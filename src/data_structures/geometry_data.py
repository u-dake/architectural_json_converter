"""
Unified Geometry Data Structures

このモジュールはDXF・PDF両対応の統一データ構造を定義します。
Phase 2の差分解析エンジンで使用される中間表現データです。
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import numpy as np
from shapely.geometry import Point, LineString, Polygon

# 前方参照のための型定義
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # 循環インポートを避けるため、TYPE_CHECKINGでのみインポート
    pass


class ElementType(Enum):
    """要素タイプの定義"""
    LINE = "line"
    ARC = "arc"
    CIRCLE = "circle"
    POLYLINE = "polyline"
    TEXT = "text"
    BLOCK = "block"
    DIMENSION = "dimension"
    HATCH = "hatch"


class ArchitecturalType(Enum):
    """建築要素タイプの定義"""
    WALL = "wall"
    OPENING = "opening"
    DOOR = "door"
    WINDOW = "window"
    FIXTURE = "fixture"
    DIMENSION_LINE = "dimension_line"
    TEXT_LABEL = "text_label"
    UNKNOWN = "unknown"


@dataclass
class Point2D:
    """2D座標点"""
    x: float
    y: float
    
    def to_numpy(self) -> np.ndarray:
        """numpy配列に変換"""
        return np.array([self.x, self.y])
    
    def to_shapely(self) -> Point:
        """Shapelyポイントに変換"""
        return Point(self.x, self.y)
    
    def distance_to(self, other: 'Point2D') -> float:
        """他の点との距離を計算"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __add__(self, other: 'Point2D') -> 'Point2D':
        return Point2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point2D') -> 'Point2D':
        return Point2D(self.x - other.x, self.y - other.y)


@dataclass
class BoundingBox:
    """境界ボックス"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Point2D:
        return Point2D(
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2
        )
    
    def contains(self, point: Point2D) -> bool:
        """点が境界内にあるかチェック"""
        return (self.min_x <= point.x <= self.max_x and 
                self.min_y <= point.y <= self.max_y)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """他の境界ボックスと交差するかチェック"""
        return not (self.max_x < other.min_x or self.min_x > other.max_x or
                   self.max_y < other.min_y or self.min_y > other.max_y)


@dataclass
class Style:
    """描画スタイル情報"""
    color: Optional[int] = None
    line_width: float = 1.0
    line_type: str = "CONTINUOUS"
    layer: str = "0"


class GeometryElement(BaseModel):
    """幾何要素の基底クラス"""
    id: str
    element_type: ElementType
    architectural_type: ArchitecturalType = ArchitecturalType.UNKNOWN
    style: Style = Field(default_factory=Style)
    source_info: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0  # 分類の信頼度 (0.0-1.0)
    
    class Config:
        use_enum_values = True
    
    def get_bounding_box(self) -> BoundingBox:
        """境界ボックスを取得（サブクラスで実装）"""
        raise NotImplementedError
    
    def to_shapely(self) -> Union[Point, LineString, Polygon]:
        """Shapely図形に変換（サブクラスで実装）"""
        raise NotImplementedError


class LineElement(GeometryElement):
    """線分要素"""
    element_type: ElementType = ElementType.LINE
    start: Point2D
    end: Point2D
    
    def get_bounding_box(self) -> BoundingBox:
        return BoundingBox(
            min(self.start.x, self.end.x),
            min(self.start.y, self.end.y),
            max(self.start.x, self.end.x),
            max(self.start.y, self.end.y)
        )
    
    def to_shapely(self) -> LineString:
        return LineString([self.start.to_shapely(), self.end.to_shapely()])
    
    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)
    
    @property
    def angle(self) -> float:
        """線分の角度（ラジアン）"""
        return np.arctan2(self.end.y - self.start.y, self.end.x - self.start.x)


class CircleElement(GeometryElement):
    """円要素"""
    element_type: ElementType = ElementType.CIRCLE
    center: Point2D
    radius: float
    
    def get_bounding_box(self) -> BoundingBox:
        return BoundingBox(
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.center.x + self.radius,
            self.center.y + self.radius
        )
    
    def to_shapely(self) -> Point:
        # Shapelyでは円はバッファ付きポイントとして表現
        return self.center.to_shapely().buffer(self.radius)


class ArcElement(GeometryElement):
    """円弧要素"""
    element_type: ElementType = ElementType.ARC
    center: Point2D
    radius: float
    start_angle: float  # ラジアン
    end_angle: float    # ラジアン
    
    def get_bounding_box(self) -> BoundingBox:
        # 簡易的に円全体の境界ボックスを返す
        return BoundingBox(
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.center.x + self.radius,
            self.center.y + self.radius
        )
    
    def to_shapely(self) -> LineString:
        # 円弧を線分で近似
        angles = np.linspace(self.start_angle, self.end_angle, 20)
        points = [(self.center.x + self.radius * np.cos(a),
                  self.center.y + self.radius * np.sin(a)) for a in angles]
        return LineString(points)


class PolylineElement(GeometryElement):
    """ポリライン要素"""
    element_type: ElementType = ElementType.POLYLINE
    vertices: List[Point2D]
    is_closed: bool = False
    
    def get_bounding_box(self) -> BoundingBox:
        if not self.vertices:
            return BoundingBox(0, 0, 0, 0)
        
        x_coords = [v.x for v in self.vertices]
        y_coords = [v.y for v in self.vertices]
        return BoundingBox(
            min(x_coords), min(y_coords),
            max(x_coords), max(y_coords)
        )
    
    def to_shapely(self) -> Union[LineString, Polygon]:
        if len(self.vertices) < 2:
            return LineString([])
        
        points = [v.to_shapely() for v in self.vertices]
        if self.is_closed and len(points) >= 3:
            return Polygon(points)
        else:
            return LineString(points)


class TextElement(GeometryElement):
    """テキスト要素"""
    element_type: ElementType = ElementType.TEXT
    position: Point2D
    text: str
    height: float
    rotation: float = 0.0  # ラジアン
    font: str = ""
    
    def get_bounding_box(self) -> BoundingBox:
        # 簡易的な境界ボックス（実際のテキスト幅は計算が複雑）
        estimated_width = len(self.text) * self.height * 0.6
        return BoundingBox(
            self.position.x,
            self.position.y,
            self.position.x + estimated_width,
            self.position.y + self.height
        )
    
    def to_shapely(self) -> Point:
        return self.position.to_shapely()


class BlockElement(GeometryElement):
    """ブロック要素（INSERT）"""
    element_type: ElementType = ElementType.BLOCK
    position: Point2D
    block_name: str
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    
    def get_bounding_box(self) -> BoundingBox:
        # ブロックの実際のサイズは不明なので、位置のみ
        return BoundingBox(
            self.position.x, self.position.y,
            self.position.x, self.position.y
        )
    
    def to_shapely(self) -> Point:
        return self.position.to_shapely()


@dataclass
class Layer:
    """レイヤー情報"""
    name: str
    color: int = 7  # デフォルト白
    line_type: str = "CONTINUOUS"
    is_visible: bool = True
    is_locked: bool = False
    is_frozen: bool = False


class GeometryData(BaseModel):
    """統一幾何データ構造"""
    source_file: str
    source_type: str  # "dxf" or "pdf"
    layers: List[Layer] = Field(default_factory=list)
    elements: List[Any] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
    
    def get_elements_by_type(self, element_type: ElementType) -> List[GeometryElement]:
        """要素タイプで要素をフィルタ"""
        return [e for e in self.elements if e.element_type == element_type]
    
    def get_elements_by_architectural_type(self, arch_type: ArchitecturalType) -> List[GeometryElement]:
        """建築要素タイプで要素をフィルタ"""
        # use_enum_values=True のため、文字列比較と enum 比較の両方をサポート
        return [e for e in self.elements if (
            e.architectural_type == arch_type or 
            e.architectural_type == arch_type.value
        )]
    
    def get_elements_by_layer(self, layer_name: str) -> List[GeometryElement]:
        """レイヤーで要素をフィルタ"""
        return [e for e in self.elements if e.style.layer == layer_name]
    
    def get_bounding_box(self) -> BoundingBox:
        """全要素の境界ボックスを計算"""
        if not self.elements:
            return BoundingBox(0, 0, 0, 0)
        
        boxes = [e.get_bounding_box() for e in self.elements]
        return BoundingBox(
            min(b.min_x for b in boxes),
            min(b.min_y for b in boxes),
            max(b.max_x for b in boxes),
            max(b.max_y for b in boxes)
        )
    
    def add_element(self, element: GeometryElement) -> None:
        """要素を追加"""
        self.elements.append(element)
    
    def remove_element(self, element_id: str) -> bool:
        """要素を削除"""
        original_length = len(self.elements)
        self.elements = [e for e in self.elements if e.id != element_id]
        return len(self.elements) < original_length


class DifferenceResult(BaseModel):
    """差分解析結果"""
    site_only: Any  # GeometryData対応
    site_with_plan: Any  # GeometryData対応
    new_elements: List[Any] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    removed_elements: List[Any] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    modified_elements: List[Tuple[Any, Any]] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    
    # 建築要素別の分類結果
    walls: List[Any] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    openings: List[Any] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    fixtures: List[Any] = Field(default_factory=list)  # GeometryElementのサブクラス対応
    
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
    
    def get_statistics(self) -> Dict[str, int]:
        """統計情報を取得"""
        return {
            "total_new_elements": len(self.new_elements),
            "walls_detected": len(self.walls),
            "openings_detected": len(self.openings),
            "fixtures_detected": len(self.fixtures),
            "removed_elements": len(self.removed_elements),
            "modified_elements": len(self.modified_elements)
        }


# ユーティリティ関数

def create_line_from_points(start: Tuple[float, float], end: Tuple[float, float], 
                           element_id: str = "", layer: str = "0") -> LineElement:
    """座標タプルから線分要素を作成"""
    return LineElement(
        id=element_id,
        start=Point2D(start[0], start[1]),
        end=Point2D(end[0], end[1]),
        style=Style(layer=layer)
    )


def create_text_element(position: Tuple[float, float], text: str, height: float,
                       element_id: str = "", layer: str = "0") -> TextElement:
    """テキスト要素を作成"""
    return TextElement(
        id=element_id,
        position=Point2D(position[0], position[1]),
        text=text,
        height=height,
        style=Style(layer=layer)
    )


def normalize_to_910mm_grid(point: Point2D, grid_size: float = 910.0) -> Point2D:
    """910mmグリッドに正規化"""
    return Point2D(
        round(point.x / grid_size) * grid_size,
        round(point.y / grid_size) * grid_size
    )