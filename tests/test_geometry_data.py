"""
Test suite for geometry data structures

統一データ構造のテストスイート
テスト対象: src/data_structures/geometry_data.py
カバレッジ目標: 80%
"""

import pytest
import numpy as np
from unittest.mock import patch
from pydantic import ValidationError
from shapely.geometry import Point, LineString, Polygon

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_structures.geometry_data import (
    # Enums
    ElementType, ArchitecturalType,
    # Basic structures
    Point2D, BoundingBox, Style, Layer,
    # Geometry elements
    GeometryElement, LineElement, CircleElement, ArcElement,
    PolylineElement, TextElement, BlockElement,
    # Main classes
    GeometryData, DifferenceResult,
    # Utility functions
    create_line_from_points, create_text_element, normalize_to_910mm_grid
)


class TestPoint2D:
    """Point2D クラスのテスト"""
    
    def test_creation(self):
        """Point2D作成テスト"""
        point = Point2D(10.5, 20.3)
        assert point.x == 10.5
        assert point.y == 20.3
    
    def test_to_numpy(self):
        """numpy配列変換テスト"""
        point = Point2D(5.0, 10.0)
        arr = point.to_numpy()
        np.testing.assert_array_equal(arr, np.array([5.0, 10.0]))
    
    def test_to_shapely(self):
        """Shapely Point変換テスト"""
        point = Point2D(3.0, 4.0)
        shapely_point = point.to_shapely()
        assert isinstance(shapely_point, Point)
        assert shapely_point.x == 3.0
        assert shapely_point.y == 4.0
    
    def test_distance_to(self):
        """距離計算テスト"""
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(3.0, 4.0)
        distance = p1.distance_to(p2)
        assert abs(distance - 5.0) < 1e-10
    
    def test_addition(self):
        """点の加算テスト"""
        p1 = Point2D(1.0, 2.0)
        p2 = Point2D(3.0, 4.0)
        result = p1 + p2
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_subtraction(self):
        """点の減算テスト"""
        p1 = Point2D(5.0, 8.0)
        p2 = Point2D(2.0, 3.0)
        result = p1 - p2
        assert result.x == 3.0
        assert result.y == 5.0


class TestBoundingBox:
    """BoundingBox クラスのテスト"""
    
    def test_creation(self):
        """BoundingBox作成テスト"""
        bbox = BoundingBox(0.0, 5.0, 10.0, 15.0)
        assert bbox.min_x == 0.0
        assert bbox.min_y == 5.0
        assert bbox.max_x == 10.0
        assert bbox.max_y == 15.0
    
    def test_properties(self):
        """プロパティテスト"""
        bbox = BoundingBox(0.0, 0.0, 10.0, 5.0)
        assert bbox.width == 10.0
        assert bbox.height == 5.0
        
        center = bbox.center
        assert center.x == 5.0
        assert center.y == 2.5
    
    def test_contains(self):
        """点包含テスト"""
        bbox = BoundingBox(0.0, 0.0, 10.0, 10.0)
        
        # 内部の点
        assert bbox.contains(Point2D(5.0, 5.0))
        # 境界上の点
        assert bbox.contains(Point2D(0.0, 0.0))
        assert bbox.contains(Point2D(10.0, 10.0))
        # 外部の点
        assert not bbox.contains(Point2D(-1.0, 5.0))
        assert not bbox.contains(Point2D(11.0, 5.0))
    
    def test_intersects(self):
        """境界ボックス交差テスト"""
        bbox1 = BoundingBox(0.0, 0.0, 10.0, 10.0)
        
        # 重複する場合
        bbox2 = BoundingBox(5.0, 5.0, 15.0, 15.0)
        assert bbox1.intersects(bbox2)
        
        # 接する場合
        bbox3 = BoundingBox(10.0, 0.0, 20.0, 10.0)
        assert bbox1.intersects(bbox3)
        
        # 分離している場合
        bbox4 = BoundingBox(20.0, 20.0, 30.0, 30.0)
        assert not bbox1.intersects(bbox4)


class TestStyle:
    """Style クラスのテスト"""
    
    def test_default_creation(self):
        """デフォルト値での作成テスト"""
        style = Style()
        assert style.color is None
        assert style.line_width == 1.0
        assert style.line_type == "CONTINUOUS"
        assert style.layer == "0"
    
    def test_custom_creation(self):
        """カスタム値での作成テスト"""
        style = Style(color=255, line_width=2.5, line_type="DASHED", layer="WALLS")
        assert style.color == 255
        assert style.line_width == 2.5
        assert style.line_type == "DASHED"
        assert style.layer == "WALLS"


class TestEnums:
    """Enum クラスのテスト"""
    
    def test_element_type_enum(self):
        """ElementType Enumテスト"""
        assert ElementType.LINE.value == "line"
        assert ElementType.CIRCLE.value == "circle"
        assert ElementType.TEXT.value == "text"
        assert len(ElementType) == 8
    
    def test_architectural_type_enum(self):
        """ArchitecturalType Enumテスト"""
        assert ArchitecturalType.WALL.value == "wall"
        assert ArchitecturalType.DOOR.value == "door"
        assert ArchitecturalType.UNKNOWN.value == "unknown"
        assert len(ArchitecturalType) == 8


class TestLineElement:
    """LineElement クラスのテスト"""
    
    def test_creation(self):
        """LineElement作成テスト"""
        line = LineElement(
            id="line1",
            start=Point2D(0.0, 0.0),
            end=Point2D(10.0, 10.0)
        )
        assert line.id == "line1"
        assert line.element_type == ElementType.LINE
        assert line.start.x == 0.0
        assert line.end.y == 10.0
    
    def test_bounding_box(self):
        """境界ボックス計算テスト"""
        line = LineElement(
            id="line1",
            start=Point2D(2.0, 8.0),
            end=Point2D(10.0, 3.0)
        )
        bbox = line.get_bounding_box()
        assert bbox.min_x == 2.0
        assert bbox.min_y == 3.0
        assert bbox.max_x == 10.0
        assert bbox.max_y == 8.0
    
    def test_to_shapely(self):
        """Shapely変換テスト"""
        line = LineElement(
            id="line1",
            start=Point2D(0.0, 0.0),
            end=Point2D(5.0, 5.0)
        )
        shapely_line = line.to_shapely()
        assert isinstance(shapely_line, LineString)
        coords = list(shapely_line.coords)
        assert coords[0] == (0.0, 0.0)
        assert coords[1] == (5.0, 5.0)
    
    def test_properties(self):
        """プロパティテスト"""
        line = LineElement(
            id="line1",
            start=Point2D(0.0, 0.0),
            end=Point2D(3.0, 4.0)
        )
        assert abs(line.length - 5.0) < 1e-10
        
        # 45度の線分
        line_45 = LineElement(
            id="line2",
            start=Point2D(0.0, 0.0),
            end=Point2D(1.0, 1.0)
        )
        assert abs(line_45.angle - np.pi/4) < 1e-10


class TestCircleElement:
    """CircleElement クラスのテスト"""
    
    def test_creation(self):
        """CircleElement作成テスト"""
        circle = CircleElement(
            id="circle1",
            center=Point2D(5.0, 5.0),
            radius=3.0
        )
        assert circle.id == "circle1"
        assert circle.element_type == ElementType.CIRCLE
        assert circle.center.x == 5.0
        assert circle.radius == 3.0
    
    def test_bounding_box(self):
        """境界ボックス計算テスト"""
        circle = CircleElement(
            id="circle1",
            center=Point2D(10.0, 15.0),
            radius=5.0
        )
        bbox = circle.get_bounding_box()
        assert bbox.min_x == 5.0
        assert bbox.min_y == 10.0
        assert bbox.max_x == 15.0
        assert bbox.max_y == 20.0
    
    def test_to_shapely(self):
        """Shapely変換テスト"""
        circle = CircleElement(
            id="circle1",
            center=Point2D(0.0, 0.0),
            radius=1.0
        )
        shapely_circle = circle.to_shapely()
        # バッファ付きポイントとして表現される
        assert abs(shapely_circle.area - np.pi) < 0.1


class TestArcElement:
    """ArcElement クラスのテスト"""
    
    def test_creation(self):
        """ArcElement作成テスト"""
        arc = ArcElement(
            id="arc1",
            center=Point2D(0.0, 0.0),
            radius=5.0,
            start_angle=0.0,
            end_angle=np.pi/2
        )
        assert arc.id == "arc1"
        assert arc.element_type == ElementType.ARC
        assert arc.radius == 5.0
        assert arc.start_angle == 0.0
        assert arc.end_angle == np.pi/2
    
    def test_to_shapely(self):
        """Shapely変換テスト（線分近似）"""
        arc = ArcElement(
            id="arc1",
            center=Point2D(0.0, 0.0),
            radius=1.0,
            start_angle=0.0,
            end_angle=np.pi/2
        )
        shapely_line = arc.to_shapely()
        assert isinstance(shapely_line, LineString)
        assert len(list(shapely_line.coords)) == 20


class TestPolylineElement:
    """PolylineElement クラスのテスト"""
    
    def test_creation(self):
        """PolylineElement作成テスト"""
        vertices = [Point2D(0, 0), Point2D(10, 0), Point2D(10, 10), Point2D(0, 10)]
        polyline = PolylineElement(
            id="poly1",
            vertices=vertices,
            is_closed=True
        )
        assert polyline.id == "poly1"
        assert polyline.element_type == ElementType.POLYLINE
        assert len(polyline.vertices) == 4
        assert polyline.is_closed
    
    def test_bounding_box(self):
        """境界ボックス計算テスト"""
        vertices = [Point2D(1, 3), Point2D(8, 1), Point2D(5, 9)]
        polyline = PolylineElement(
            id="poly1",
            vertices=vertices
        )
        bbox = polyline.get_bounding_box()
        assert bbox.min_x == 1
        assert bbox.min_y == 1
        assert bbox.max_x == 8
        assert bbox.max_y == 9
    
    def test_bounding_box_empty(self):
        """空の頂点リストでの境界ボックステスト"""
        polyline = PolylineElement(
            id="poly1",
            vertices=[]
        )
        bbox = polyline.get_bounding_box()
        assert bbox.min_x == 0
        assert bbox.max_x == 0
    
    def test_to_shapely_closed(self):
        """閉じたポリライン（ポリゴン）のShapely変換テスト"""
        vertices = [Point2D(0, 0), Point2D(5, 0), Point2D(5, 5), Point2D(0, 5)]
        polyline = PolylineElement(
            id="poly1",
            vertices=vertices,
            is_closed=True
        )
        shapely_geom = polyline.to_shapely()
        assert isinstance(shapely_geom, Polygon)
    
    def test_to_shapely_open(self):
        """開いたポリライン（ラインストリング）のShapely変換テスト"""
        vertices = [Point2D(0, 0), Point2D(5, 0), Point2D(5, 5)]
        polyline = PolylineElement(
            id="poly1",
            vertices=vertices,
            is_closed=False
        )
        shapely_geom = polyline.to_shapely()
        assert isinstance(shapely_geom, LineString)
    
    def test_to_shapely_insufficient_vertices(self):
        """頂点数不足でのShapely変換テスト"""
        polyline = PolylineElement(
            id="poly1",
            vertices=[Point2D(0, 0)]
        )
        shapely_geom = polyline.to_shapely()
        assert isinstance(shapely_geom, LineString)
        assert shapely_geom.is_empty


class TestTextElement:
    """TextElement クラスのテスト"""
    
    def test_creation(self):
        """TextElement作成テスト"""
        text = TextElement(
            id="text1",
            position=Point2D(10.0, 20.0),
            text="サンプルテキスト",
            height=5.0,
            rotation=np.pi/4,
            font="Arial"
        )
        assert text.id == "text1"
        assert text.element_type == ElementType.TEXT
        assert text.text == "サンプルテキスト"
        assert text.height == 5.0
        assert text.rotation == np.pi/4
    
    def test_bounding_box(self):
        """境界ボックス計算テスト"""
        text = TextElement(
            id="text1",
            position=Point2D(0.0, 0.0),
            text="Hello",
            height=10.0
        )
        bbox = text.get_bounding_box()
        # テキスト幅の簡易推定: len(text) * height * 0.6
        expected_width = 5 * 10.0 * 0.6
        assert bbox.min_x == 0.0
        assert bbox.min_y == 0.0
        assert bbox.max_x == expected_width
        assert bbox.max_y == 10.0
    
    def test_to_shapely(self):
        """Shapely変換テスト"""
        text = TextElement(
            id="text1",
            position=Point2D(5.0, 10.0),
            text="Test",
            height=2.0
        )
        shapely_point = text.to_shapely()
        assert isinstance(shapely_point, Point)
        assert shapely_point.x == 5.0
        assert shapely_point.y == 10.0


class TestBlockElement:
    """BlockElement クラスのテスト"""
    
    def test_creation(self):
        """BlockElement作成テスト"""
        block = BlockElement(
            id="block1",
            position=Point2D(15.0, 25.0),
            block_name="DOOR_SYMBOL",
            scale_x=2.0,
            scale_y=1.5,
            rotation=np.pi/2
        )
        assert block.id == "block1"
        assert block.element_type == ElementType.BLOCK
        assert block.block_name == "DOOR_SYMBOL"
        assert block.scale_x == 2.0
        assert block.rotation == np.pi/2
    
    def test_bounding_box(self):
        """境界ボックス計算テスト（位置のみ）"""
        block = BlockElement(
            id="block1",
            position=Point2D(10.0, 20.0),
            block_name="TEST_BLOCK"
        )
        bbox = block.get_bounding_box()
        assert bbox.min_x == 10.0
        assert bbox.min_y == 20.0
        assert bbox.max_x == 10.0
        assert bbox.max_y == 20.0


class TestLayer:
    """Layer クラスのテスト"""
    
    def test_default_creation(self):
        """デフォルト値での作成テスト"""
        layer = Layer(name="TEST_LAYER")
        assert layer.name == "TEST_LAYER"
        assert layer.color == 7
        assert layer.line_type == "CONTINUOUS"
        assert layer.is_visible
        assert not layer.is_locked
        assert not layer.is_frozen
    
    def test_custom_creation(self):
        """カスタム値での作成テスト"""
        layer = Layer(
            name="WALLS",
            color=255,
            line_type="DASHED",
            is_visible=False,
            is_locked=True,
            is_frozen=True
        )
        assert layer.name == "WALLS"
        assert layer.color == 255
        assert layer.line_type == "DASHED"
        assert not layer.is_visible
        assert layer.is_locked
        assert layer.is_frozen


class TestGeometryData:
    """GeometryData クラスのテスト"""
    
    def test_creation(self):
        """GeometryData作成テスト"""
        geo_data = GeometryData(
            source_file="test.dxf",
            source_type="dxf"
        )
        assert geo_data.source_file == "test.dxf"
        assert geo_data.source_type == "dxf"
        assert len(geo_data.layers) == 0
        assert len(geo_data.elements) == 0
    
    def test_filter_by_type(self):
        """要素タイプフィルタテスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        
        # テスト要素追加
        line = LineElement(id="line1", start=Point2D(0, 0), end=Point2D(10, 10))
        circle = CircleElement(id="circle1", center=Point2D(5, 5), radius=3)
        text = TextElement(id="text1", position=Point2D(0, 0), text="Test", height=2)
        
        geo_data.elements = [line, circle, text]
        
        lines = geo_data.get_elements_by_type(ElementType.LINE)
        circles = geo_data.get_elements_by_type(ElementType.CIRCLE)
        
        assert len(lines) == 1
        assert len(circles) == 1
        assert lines[0].id == "line1"
        assert circles[0].id == "circle1"
    
    def test_filter_by_architectural_type(self):
        """建築要素タイプフィルタテスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        
        line1 = LineElement(id="wall1", start=Point2D(0, 0), end=Point2D(10, 0),
                           architectural_type=ArchitecturalType.WALL)
        line2 = LineElement(id="door1", start=Point2D(2, 0), end=Point2D(4, 0),
                           architectural_type=ArchitecturalType.DOOR)
        
        geo_data.elements = [line1, line2]
        
        walls = geo_data.get_elements_by_architectural_type(ArchitecturalType.WALL)
        doors = geo_data.get_elements_by_architectural_type(ArchitecturalType.DOOR)
        
        assert len(walls) == 1
        assert len(doors) == 1
        assert walls[0].id == "wall1"
        assert doors[0].id == "door1"
    
    def test_filter_by_layer(self):
        """レイヤーフィルタテスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        
        line1 = LineElement(id="line1", start=Point2D(0, 0), end=Point2D(10, 0),
                           style=Style(layer="WALLS"))
        line2 = LineElement(id="line2", start=Point2D(0, 0), end=Point2D(0, 10),
                           style=Style(layer="DIMENSIONS"))
        
        geo_data.elements = [line1, line2]
        
        wall_elements = geo_data.get_elements_by_layer("WALLS")
        dim_elements = geo_data.get_elements_by_layer("DIMENSIONS")
        
        assert len(wall_elements) == 1
        assert len(dim_elements) == 1
        assert wall_elements[0].id == "line1"
        assert dim_elements[0].id == "line2"
    
    def test_bounding_box(self):
        """全体境界ボックス計算テスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        
        line = LineElement(id="line1", start=Point2D(0, 0), end=Point2D(10, 5))
        circle = CircleElement(id="circle1", center=Point2D(15, 10), radius=3)
        
        geo_data.elements = [line, circle]
        
        bbox = geo_data.get_bounding_box()
        assert bbox.min_x == 0
        assert bbox.min_y == 0
        assert bbox.max_x == 18  # circle center(15) + radius(3)
        assert bbox.max_y == 13  # circle center(10) + radius(3)
    
    def test_bounding_box_empty(self):
        """空の要素リストでの境界ボックステスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        bbox = geo_data.get_bounding_box()
        assert bbox.min_x == 0
        assert bbox.max_x == 0
    
    def test_add_element(self):
        """要素追加テスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        line = LineElement(id="line1", start=Point2D(0, 0), end=Point2D(10, 10))
        
        geo_data.add_element(line)
        assert len(geo_data.elements) == 1
        assert geo_data.elements[0].id == "line1"
    
    def test_remove_element(self):
        """要素削除テスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        
        line1 = LineElement(id="line1", start=Point2D(0, 0), end=Point2D(10, 10))
        line2 = LineElement(id="line2", start=Point2D(5, 5), end=Point2D(15, 15))
        
        geo_data.elements = [line1, line2]
        
        # 存在する要素の削除
        result = geo_data.remove_element("line1")
        assert result is True
        assert len(geo_data.elements) == 1
        assert geo_data.elements[0].id == "line2"
        
        # 存在しない要素の削除
        result = geo_data.remove_element("nonexistent")
        assert result is False
        assert len(geo_data.elements) == 1


class TestDifferenceResult:
    """DifferenceResult クラスのテスト"""
    
    def test_creation(self):
        """DifferenceResult作成テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data
        )
        
        assert result.site_only.source_file == "site.dxf"
        assert result.site_with_plan.source_file == "plan.dxf"
        assert len(result.new_elements) == 0
        assert len(result.walls) == 0
    
    def test_statistics(self):
        """統計情報取得テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        # テスト要素作成
        new_line = LineElement(id="new1", start=Point2D(0, 0), end=Point2D(10, 10))
        wall = LineElement(id="wall1", start=Point2D(0, 0), end=Point2D(10, 0),
                          architectural_type=ArchitecturalType.WALL)
        fixture = CircleElement(id="fixture1", center=Point2D(5, 5), radius=1,
                               architectural_type=ArchitecturalType.FIXTURE)
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[new_line],
            walls=[wall],
            fixtures=[fixture]
        )
        
        stats = result.get_statistics()
        assert stats["total_new_elements"] == 1
        assert stats["walls_detected"] == 1
        assert stats["fixtures_detected"] == 1
        assert stats["openings_detected"] == 0
        assert stats["removed_elements"] == 0
        assert stats["modified_elements"] == 0


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_create_line_from_points(self):
        """create_line_from_points関数テスト"""
        line = create_line_from_points(
            start=(0.0, 0.0),
            end=(10.0, 5.0),
            element_id="test_line",
            layer="TEST_LAYER"
        )
        
        assert isinstance(line, LineElement)
        assert line.id == "test_line"
        assert line.start.x == 0.0
        assert line.start.y == 0.0
        assert line.end.x == 10.0
        assert line.end.y == 5.0
        assert line.style.layer == "TEST_LAYER"
    
    def test_create_text_element(self):
        """create_text_element関数テスト"""
        text = create_text_element(
            position=(5.0, 10.0),
            text="テストテキスト",
            height=12.0,
            element_id="test_text",
            layer="TEXT_LAYER"
        )
        
        assert isinstance(text, TextElement)
        assert text.id == "test_text"
        assert text.position.x == 5.0
        assert text.position.y == 10.0
        assert text.text == "テストテキスト"
        assert text.height == 12.0
        assert text.style.layer == "TEXT_LAYER"
    
    def test_normalize_to_910mm_grid(self):
        """normalize_to_910mm_grid関数テスト"""
        # 標準的な910mmグリッド
        point1 = Point2D(450.0, 300.0)  # 910/2, 910/3に近い
        normalized1 = normalize_to_910mm_grid(point1)
        assert normalized1.x == 0.0  # round(450/910) * 910 = 0
        assert normalized1.y == 0.0  # round(300/910) * 910 = 0
        
        # より正確なグリッド点
        point2 = Point2D(910.0, 1820.0)  # 1グリッド, 2グリッド
        normalized2 = normalize_to_910mm_grid(point2)
        assert normalized2.x == 910.0
        assert normalized2.y == 1820.0
        
        # カスタムグリッドサイズ
        point3 = Point2D(150.0, 250.0)
        normalized3 = normalize_to_910mm_grid(point3, grid_size=100.0)
        assert normalized3.x == 200.0  # round(150/100) * 100 = round(1.5) * 100 = 2 * 100 = 200
        assert normalized3.y == 200.0  # round(250/100) * 100 = round(2.5) * 100 = 2 * 100 = 200 (偶数丸め)


class TestPydanticIntegration:
    """Pydanticとの統合テスト"""
    
    def test_json_serialization(self):
        """JSON シリアライゼーションテスト"""
        line = LineElement(
            id="test_line",
            start=Point2D(0.0, 0.0),
            end=Point2D(10.0, 10.0),
            architectural_type=ArchitecturalType.WALL
        )
        
        # JSON形式でのダンプ
        json_data = line.model_dump(mode='json')
        
        assert json_data["id"] == "test_line"
        assert json_data["element_type"] == "line"
        assert json_data["architectural_type"] == "wall"
        assert "start" in json_data
        assert "end" in json_data
    
    def test_validation_error(self):
        """バリデーションエラーテスト"""
        with pytest.raises(ValidationError):
            # 必須フィールドが不足
            LineElement(id="test")
    
    def test_geometry_data_serialization(self):
        """GeometryData シリアライゼーションテスト"""
        geo_data = GeometryData(
            source_file="test.dxf",
            source_type="dxf"
        )
        
        line = LineElement(
            id="line1",
            start=Point2D(0.0, 0.0),
            end=Point2D(10.0, 10.0)
        )
        geo_data.add_element(line)
        
        json_data = geo_data.model_dump(mode='json')
        
        assert json_data["source_file"] == "test.dxf"
        assert json_data["source_type"] == "dxf"
        assert len(json_data["elements"]) == 1
        assert json_data["elements"][0]["id"] == "line1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])