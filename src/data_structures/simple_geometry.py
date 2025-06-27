"""
Simple Geometry Data Structures

シンプルな幾何データ構造の定義
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict


@dataclass
class Point:
    """2D点"""
    x: float
    y: float
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return abs(self.x - other.x) < 1e-6 and abs(self.y - other.y) < 1e-6


@dataclass
class Line:
    """線分"""
    start: Point
    end: Point
    layer: str = "0"
    color: Optional[int] = None
    
    @property
    def length(self):
        import math
        return math.sqrt((self.end.x - self.start.x)**2 + (self.end.y - self.start.y)**2)


@dataclass
class Circle:
    """円"""
    center: Point
    radius: float
    layer: str = "0"
    color: Optional[int] = None


@dataclass
class Arc:
    """円弧"""
    center: Point
    radius: float
    start_angle: float  # 度単位
    end_angle: float    # 度単位
    layer: str = "0"
    color: Optional[int] = None


@dataclass
class Polyline:
    """ポリライン"""
    points: List[Point]
    closed: bool = False
    layer: str = "0"
    color: Optional[int] = None


@dataclass
class Text:
    """テキスト"""
    position: Point
    content: str
    height: float
    rotation: float = 0.0  # 度単位
    layer: str = "0"
    color: Optional[int] = None


class GeometryCollection:
    """幾何要素のコレクション"""
    
    def __init__(self):
        self.elements: List[Any] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_element(self, element: Any):
        """要素を追加"""
        self.elements.append(element)
    
    def add_elements(self, elements: List[Any]):
        """複数の要素を追加"""
        self.elements.extend(elements)
    
    def clear(self):
        """すべての要素をクリア"""
        self.elements.clear()
    
    def __len__(self):
        return len(self.elements)
    
    def __iter__(self):
        return iter(self.elements)