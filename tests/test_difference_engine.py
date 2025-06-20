"""
Test suite for difference extraction engine

差分抽出エンジンのテストスイート
テスト対象: src/engines/difference_engine.py
カバレッジ目標: 80%
"""

import pytest
import numpy as np
import tempfile
import os
import json
from unittest.mock import patch, mock_open

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_structures.geometry_data import (
    GeometryData, LineElement, CircleElement, TextElement, BlockElement,
    PolylineElement, Point2D, Style, ElementType, ArchitecturalType,
    DifferenceResult
)

from engines.difference_engine import (
    calculate_similarity_score,
    find_matching_elements,
    classify_wall_elements,
    classify_opening_elements,
    classify_fixture_elements,
    extract_differences,
    analyze_spatial_distribution,
    save_difference_result_to_json
)


class TestSimilarityCalculation:
    """類似度計算関数のテスト"""
    
    def test_different_element_types(self):
        """異なる要素タイプでの類似度計算"""
        line = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(10, 10)
        )
        circle = CircleElement(
            id="circle1",
            center=Point2D(5, 5),
            radius=3
        )
        
        score = calculate_similarity_score(line, circle)
        assert score == 0.0
    
    def test_identical_lines(self):
        """同一線分での類似度計算"""
        line1 = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(10, 10)
        )
        line2 = LineElement(
            id="line2",
            start=Point2D(0, 0),
            end=Point2D(10, 10)
        )
        
        score = calculate_similarity_score(line1, line2)
        assert score > 0.9  # 高い類似度を期待
    
    def test_overlapping_lines(self):
        """重複する線分での類似度計算"""
        line1 = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(10, 0)
        )
        line2 = LineElement(
            id="line2",
            start=Point2D(5, 0),
            end=Point2D(15, 0)
        )
        
        score = calculate_similarity_score(line1, line2)
        assert 0.3 < score < 0.8  # 部分的な類似度
    
    def test_separate_lines(self):
        """分離した線分での類似度計算"""
        line1 = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(10, 0)
        )
        line2 = LineElement(
            id="line2",
            start=Point2D(20, 20),
            end=Point2D(30, 20)
        )
        
        score = calculate_similarity_score(line1, line2)
        assert score <= 0.3  # 低い類似度（同一タイプだが空間的に分離）
    
    def test_text_elements_identical(self):
        """同一テキストでの類似度計算"""
        text1 = TextElement(
            id="text1",
            position=Point2D(0, 0),
            text="同じテキスト",
            height=5.0
        )
        text2 = TextElement(
            id="text2",
            position=Point2D(1, 1),
            text="同じテキスト",
            height=5.0
        )
        
        score = calculate_similarity_score(text1, text2)
        assert score > 0.5  # テキストが同じなので高めの類似度
    
    def test_text_elements_partial_match(self):
        """部分的に一致するテキストでの類似度計算"""
        text1 = TextElement(
            id="text1",
            position=Point2D(0, 0),
            text="部分テキスト",
            height=5.0
        )
        text2 = TextElement(
            id="text2",
            position=Point2D(0, 0),
            text="部分",
            height=5.0
        )
        
        score = calculate_similarity_score(text1, text2)
        assert 0.3 < score < 0.8  # 部分一致による中程度の類似度
    
    def test_text_elements_no_match(self):
        """テキストが一致しない場合の類似度計算"""
        text1 = TextElement(
            id="text1",
            position=Point2D(0, 0),
            text="テキスト1",
            height=5.0
        )
        text2 = TextElement(
            id="text2",
            position=Point2D(0, 0),
            text="完全に異なるテキスト",
            height=5.0
        )
        
        score = calculate_similarity_score(text1, text2)
        assert score < 0.5  # テキストが異なるので低い類似度
    
    def test_zero_area_elements(self):
        """面積ゼロの要素での類似度計算"""
        line1 = LineElement(
            id="line1",
            start=Point2D(5, 5),
            end=Point2D(5, 5)  # 点線分
        )
        line2 = LineElement(
            id="line2",
            start=Point2D(5, 5),
            end=Point2D(5, 5)  # 同じ点線分
        )
        
        score = calculate_similarity_score(line1, line2)
        assert score == 1.0  # 同じ点なので完全一致


class TestElementMatching:
    """要素マッチング関数のテスト"""
    
    def test_simple_matching(self):
        """基本的な要素マッチングテスト"""
        elements1 = [
            LineElement(id="l1", start=Point2D(0, 0), end=Point2D(10, 0)),
            LineElement(id="l2", start=Point2D(0, 10), end=Point2D(10, 10))
        ]
        elements2 = [
            LineElement(id="l3", start=Point2D(0, 0), end=Point2D(10, 0)),
            LineElement(id="l4", start=Point2D(0, 10), end=Point2D(10, 10))
        ]
        
        matches = find_matching_elements(elements1, elements2, 0.5)
        
        assert len(matches) == 2
        assert "l1" in matches
        assert "l2" in matches
    
    def test_partial_matching(self):
        """部分マッチングテスト"""
        elements1 = [
            LineElement(id="l1", start=Point2D(0, 0), end=Point2D(10, 0)),
            LineElement(id="l2", start=Point2D(0, 10), end=Point2D(10, 10)),
            LineElement(id="l3", start=Point2D(100, 100), end=Point2D(110, 100))
        ]
        elements2 = [
            LineElement(id="l4", start=Point2D(0, 0), end=Point2D(10, 0)),
            LineElement(id="l5", start=Point2D(0, 10), end=Point2D(10, 10))
        ]
        
        matches = find_matching_elements(elements1, elements2, 0.5)
        
        # 最初の2つの要素はマッチするが、3つ目はマッチしない
        assert len(matches) == 2
        assert "l3" not in matches
    
    def test_no_matches_below_threshold(self):
        """閾値以下でマッチしない場合のテスト"""
        elements1 = [
            LineElement(id="l1", start=Point2D(0, 0), end=Point2D(10, 0))
        ]
        elements2 = [
            LineElement(id="l2", start=Point2D(100, 100), end=Point2D(110, 100))
        ]
        
        matches = find_matching_elements(elements1, elements2, 0.8)
        
        assert len(matches) == 0
    
    def test_empty_lists(self):
        """空のリストでのマッチングテスト"""
        matches = find_matching_elements([], [], 0.5)
        assert len(matches) == 0
        
        elements1 = [LineElement(id="l1", start=Point2D(0, 0), end=Point2D(10, 0))]
        matches = find_matching_elements(elements1, [], 0.5)
        assert len(matches) == 0
        
        matches = find_matching_elements([], elements1, 0.5)
        assert len(matches) == 0
    
    def test_one_to_one_matching(self):
        """一対一マッチングの確認"""
        # 同じ要素を複数含むケース
        elements1 = [
            LineElement(id="l1", start=Point2D(0, 0), end=Point2D(10, 0)),
            LineElement(id="l2", start=Point2D(0, 0), end=Point2D(10, 0))
        ]
        elements2 = [
            LineElement(id="l3", start=Point2D(0, 0), end=Point2D(10, 0))
        ]
        
        matches = find_matching_elements(elements1, elements2, 0.5)
        
        # l3は一度だけマッチする
        assert len(matches) == 1
        assert "l3" in matches.values()


class TestWallClassification:
    """壁分類関数のテスト"""
    
    def test_long_line_classification(self):
        """長い線分の壁分類テスト"""
        elements = [
            LineElement(id="wall1", start=Point2D(0, 0), end=Point2D(2000, 0)),  # 2m
            LineElement(id="short1", start=Point2D(0, 10), end=Point2D(100, 10))  # 10cm
        ]
        
        walls = classify_wall_elements(elements)
        
        assert len(walls) == 1
        assert walls[0].id == "wall1"
        assert walls[0].architectural_type == ArchitecturalType.WALL
    
    def test_wall_layer_classification(self):
        """レイヤー名による壁分類テスト"""
        elements = [
            LineElement(
                id="wall1", 
                start=Point2D(0, 0), 
                end=Point2D(600, 0),  # 60cm
                style=Style(layer="WALLS")
            ),
            LineElement(
                id="wall2", 
                start=Point2D(0, 10), 
                end=Point2D(600, 10),
                style=Style(layer="W-MAIN")
            ),
            LineElement(
                id="other1", 
                start=Point2D(0, 20), 
                end=Point2D(600, 20),
                style=Style(layer="DIMENSIONS")
            )
        ]
        
        walls = classify_wall_elements(elements)
        
        assert len(walls) == 2
        wall_ids = [w.id for w in walls]
        assert "wall1" in wall_ids
        assert "wall2" in wall_ids
        assert "other1" not in wall_ids
    
    def test_polyline_wall_classification(self):
        """ポリライン壁分類テスト"""
        vertices = [
            Point2D(0, 0), Point2D(1000, 0), Point2D(1000, 500), Point2D(0, 500)
        ]
        polyline = PolylineElement(
            id="poly_wall",
            vertices=vertices
        )
        
        walls = classify_wall_elements([polyline])
        
        assert len(walls) == 1
        assert walls[0].id == "poly_wall"
        assert walls[0].architectural_type == ArchitecturalType.WALL
    
    def test_short_polyline_not_wall(self):
        """短いポリラインが壁として分類されないテスト"""
        vertices = [Point2D(0, 0), Point2D(100, 0)]  # 10cm
        polyline = PolylineElement(
            id="short_poly",
            vertices=vertices
        )
        
        walls = classify_wall_elements([polyline])
        
        assert len(walls) == 0
    
    def test_empty_elements(self):
        """空要素リストでの壁分類テスト"""
        walls = classify_wall_elements([])
        assert len(walls) == 0


class TestOpeningClassification:
    """開口部分類関数のテスト"""
    
    def test_door_layer_classification(self):
        """ドアレイヤー分類テスト"""
        elements = [
            LineElement(
                id="door1",
                start=Point2D(0, 0),
                end=Point2D(800, 0),
                style=Style(layer="DOORS")
            ),
            LineElement(
                id="door2",
                start=Point2D(0, 10),
                end=Point2D(900, 10),
                style=Style(layer="扉")
            )
        ]
        
        openings = classify_opening_elements(elements, [])
        
        assert len(openings) == 2
        assert all(o.architectural_type == ArchitecturalType.DOOR for o in openings)
    
    def test_window_layer_classification(self):
        """窓レイヤー分類テスト"""
        elements = [
            LineElement(
                id="window1",
                start=Point2D(0, 0),
                end=Point2D(1200, 0),
                style=Style(layer="WINDOWS")
            ),
            LineElement(
                id="window2",
                start=Point2D(0, 10),
                end=Point2D(1000, 10),
                style=Style(layer="サッシ")
            )
        ]
        
        openings = classify_opening_elements(elements, [])
        
        assert len(openings) == 2
        assert all(o.architectural_type == ArchitecturalType.WINDOW for o in openings)
    
    def test_opening_near_wall(self):
        """壁近くの開口部分類テスト"""
        wall = LineElement(
            id="wall1",
            start=Point2D(0, 0),
            end=Point2D(5000, 0)
        )
        
        opening_near = LineElement(
            id="opening1",
            start=Point2D(1000, 10),  # 壁から1cm
            end=Point2D(2000, 10)
        )
        
        opening_far = LineElement(
            id="opening2",
            start=Point2D(1000, 200),  # 壁から20cm
            end=Point2D(2000, 200)
        )
        
        openings = classify_opening_elements([opening_near, opening_far], [wall])
        
        # 壁に近い要素のみが開口部として分類される
        assert len(openings) == 1
        assert openings[0].id == "opening1"
        assert openings[0].architectural_type == ArchitecturalType.OPENING
    
    def test_line_length_filter(self):
        """線分長による開口部フィルタテスト"""
        wall = LineElement(id="wall1", start=Point2D(0, 0), end=Point2D(5000, 0))
        
        too_short = LineElement(
            id="short1",
            start=Point2D(1000, 10),
            end=Point2D(1050, 10)  # 5cm（短すぎ）
        )
        
        good_length = LineElement(
            id="good1",
            start=Point2D(2000, 10),
            end=Point2D(2800, 10)  # 80cm（適切）
        )
        
        too_long = LineElement(
            id="long1",
            start=Point2D(3000, 10),
            end=Point2D(6500, 10)  # 3.5m（長すぎ）
        )
        
        openings = classify_opening_elements([too_short, good_length, too_long], [wall])
        
        assert len(openings) == 1
        assert openings[0].id == "good1"


class TestFixtureClassification:
    """設備分類関数のテスト"""
    
    def test_fixture_layer_classification(self):
        """設備レイヤー分類テスト"""
        elements = [
            CircleElement(
                id="fixture1",
                center=Point2D(100, 100),
                radius=50,
                style=Style(layer="FIXTURES")
            ),
            LineElement(
                id="equipment1",
                start=Point2D(0, 0),
                end=Point2D(100, 100),
                style=Style(layer="EQUIPMENT")
            )
        ]
        
        fixtures = classify_fixture_elements(elements)
        
        assert len(fixtures) == 2
        assert all(f.architectural_type == ArchitecturalType.FIXTURE for f in fixtures)
    
    def test_circle_element_classification(self):
        """円要素の設備分類テスト"""
        circle = CircleElement(
            id="circle1",
            center=Point2D(100, 100),
            radius=30
        )
        
        fixtures = classify_fixture_elements([circle])
        
        assert len(fixtures) == 1
        assert fixtures[0].id == "circle1"
        assert fixtures[0].architectural_type == ArchitecturalType.FIXTURE
        assert fixtures[0].confidence == 0.7
    
    def test_block_element_classification(self):
        """ブロック要素の設備分類テスト"""
        from data_structures.geometry_data import BlockElement
        
        block = BlockElement(
            id="block1",
            position=Point2D(200, 200),
            block_name="TOILET"
        )
        
        fixtures = classify_fixture_elements([block])
        
        assert len(fixtures) == 1
        assert fixtures[0].id == "block1"
        assert fixtures[0].architectural_type == ArchitecturalType.FIXTURE
        assert fixtures[0].confidence == 0.8
    
    def test_non_fixture_elements(self):
        """設備以外の要素が分類されないテスト"""
        line = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(100, 100),
            style=Style(layer="WALLS")
        )
        
        fixtures = classify_fixture_elements([line])
        
        assert len(fixtures) == 0


class TestDifferenceExtraction:
    """差分抽出関数のテスト"""
    
    def test_basic_difference_extraction(self):
        """基本的な差分抽出テスト"""
        # 敷地図データ
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        site_line = LineElement(id="site1", start=Point2D(0, 0), end=Point2D(1000, 0))
        site_data.elements = [site_line]
        
        # 間取り付きデータ
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        plan_line = LineElement(id="plan1", start=Point2D(0, 0), end=Point2D(1000, 0))  # 同じ線
        new_wall = LineElement(id="new_wall", start=Point2D(0, 1000), end=Point2D(2000, 1000))  # 新しい壁
        plan_data.elements = [plan_line, new_wall]
        
        result = extract_differences(site_data, plan_data, 0.5)
        
        assert len(result.new_elements) == 1
        assert result.new_elements[0].id == "new_wall"
        assert len(result.removed_elements) == 0
    
    def test_removed_elements(self):
        """削除要素の検出テスト"""
        # 敷地図データ
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        site_line1 = LineElement(id="site1", start=Point2D(0, 0), end=Point2D(1000, 0))
        site_line2 = LineElement(id="site2", start=Point2D(0, 1000), end=Point2D(1000, 1000))
        site_data.elements = [site_line1, site_line2]
        
        # 間取り付きデータ（要素が少ない）
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        plan_line = LineElement(id="plan1", start=Point2D(0, 0), end=Point2D(1000, 0))  # site1と同じ
        plan_data.elements = [plan_line]
        
        result = extract_differences(site_data, plan_data, 0.5)
        
        assert len(result.new_elements) == 0
        assert len(result.removed_elements) == 1
        assert result.removed_elements[0].id == "site2"
    
    def test_wall_classification_in_differences(self):
        """差分内での壁分類テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        new_wall = LineElement(
            id="new_wall", 
            start=Point2D(0, 0), 
            end=Point2D(3000, 0),  # 3m の壁
            style=Style(layer="WALLS")
        )
        plan_data.elements = [new_wall]
        
        result = extract_differences(site_data, plan_data, 0.5)
        
        assert len(result.walls) == 1
        assert result.walls[0].id == "new_wall"
        assert result.walls[0].architectural_type == ArchitecturalType.WALL
    
    def test_fixture_classification_in_differences(self):
        """差分内での設備分類テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        new_fixture = CircleElement(
            id="new_fixture",
            center=Point2D(100, 100),
            radius=50
        )
        plan_data.elements = [new_fixture]
        
        result = extract_differences(site_data, plan_data, 0.5)
        
        assert len(result.fixtures) == 1
        assert result.fixtures[0].id == "new_fixture"
        assert result.fixtures[0].architectural_type == ArchitecturalType.FIXTURE
    
    def test_analysis_metadata(self):
        """解析メタデータのテスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        result = extract_differences(site_data, plan_data, 0.7)
        
        assert "similarity_threshold" in result.analysis_metadata
        assert result.analysis_metadata["similarity_threshold"] == 0.7
        assert "total_matches" in result.analysis_metadata
        assert "classification_confidence" in result.analysis_metadata


class TestSpatialDistribution:
    """空間分布解析のテスト"""
    
    def test_empty_elements(self):
        """空要素での空間分布解析"""
        result = analyze_spatial_distribution([])
        assert result == {}
    
    def test_single_element(self):
        """単一要素での空間分布解析"""
        element = LineElement(
            id="line1",
            start=Point2D(10, 20),
            end=Point2D(30, 40)
        )
        
        result = analyze_spatial_distribution([element])
        
        assert result["count"] == 1
        assert "bounding_box" in result
        assert "center_of_mass" in result
        assert "spread" in result
        
        # 境界ボックスの確認
        bbox = result["bounding_box"]
        assert bbox["min_x"] == 10
        assert bbox["min_y"] == 20
        assert bbox["max_x"] == 30
        assert bbox["max_y"] == 40
        
        # 重心の確認（線分の中点）
        center = result["center_of_mass"]
        assert center["x"] == 20  # (10 + 30) / 2
        assert center["y"] == 30  # (20 + 40) / 2
    
    def test_multiple_elements(self):
        """複数要素での空間分布解析"""
        elements = [
            LineElement(id="l1", start=Point2D(0, 0), end=Point2D(10, 10)),
            LineElement(id="l2", start=Point2D(20, 20), end=Point2D(30, 30)),
            CircleElement(id="c1", center=Point2D(50, 50), radius=5)
        ]
        
        result = analyze_spatial_distribution(elements)
        
        assert result["count"] == 3
        
        # 境界ボックスの確認
        bbox = result["bounding_box"]
        assert bbox["min_x"] == 0
        assert bbox["min_y"] == 0
        assert bbox["max_x"] == 55  # 円の右端
        assert bbox["max_y"] == 55  # 円の上端
        
        # 重心の確認
        center = result["center_of_mass"]
        # 各要素の中心点：(5,5), (25,25), (50,50)
        # 平均：(5+25+50)/3 = 26.67, (5+25+50)/3 = 26.67
        assert abs(center["x"] - 26.67) < 0.1
        assert abs(center["y"] - 26.67) < 0.1


class TestJSONSaving:
    """JSON保存機能のテスト"""
    
    def test_save_to_json(self):
        """JSON保存テスト"""
        # テスト用の差分結果を作成
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[],
            walls=[],
            openings=[],
            fixtures=[]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # ファイル保存の実行
            save_difference_result_to_json(result, temp_path)
            
            # ファイルが作成されたことを確認
            assert os.path.exists(temp_path)
            
            # ファイル内容の確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert "site_only" in data
            assert "site_with_plan" in data
            assert data["site_only"]["source_file"] == "site.dxf"
            assert data["site_with_plan"]["source_file"] == "plan.dxf"
            
        finally:
            # テンポラリファイルをクリーンアップ
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_with_directory_creation(self):
        """ディレクトリ作成付きJSON保存テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 存在しないサブディレクトリ内にファイルを保存
            output_path = os.path.join(temp_dir, "subdir", "test_result.json")
            
            save_difference_result_to_json(result, output_path)
            
            # ファイルとディレクトリが作成されたことを確認
            assert os.path.exists(output_path)
            assert os.path.isdir(os.path.dirname(output_path))
    
    @patch('builtins.print')  # print文をモックしてテスト出力を抑制
    def test_save_json_encoding(self, mock_print):
        """JSON保存時の文字エンコーディングテスト"""
        site_data = GeometryData(source_file="敷地図.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="間取り図.dxf", source_type="dxf")
        
        # 日本語テキスト要素を含む結果
        japanese_text = TextElement(
            id="text1",
            position=Point2D(0, 0),
            text="日本語テキスト",
            height=10.0
        )
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[japanese_text]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            save_difference_result_to_json(result, temp_path)
            
            # ファイルを読み直して日本語が正しく保存されているか確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 日本語ファイル名とテキストの確認
            assert data["site_only"]["source_file"] == "敷地図.dxf"
            assert data["site_with_plan"]["source_file"] == "間取り図.dxf"
            assert data["new_elements"][0]["text"] == "日本語テキスト"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestIntegrationScenarios:
    """統合シナリオのテスト"""
    
    def test_complete_difference_workflow(self):
        """完全な差分抽出ワークフローのテスト"""
        # 敷地図: 外壁のみ
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        outer_wall = LineElement(
            id="outer_wall",
            start=Point2D(0, 0),
            end=Point2D(10000, 0),  # 10m
            style=Style(layer="WALLS")
        )
        site_data.elements = [outer_wall]
        
        # 間取り図: 外壁 + 内壁 + 設備
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        # 同じ外壁
        matching_wall = LineElement(
            id="matching_wall",
            start=Point2D(0, 0),
            end=Point2D(10000, 0),
            style=Style(layer="WALLS")
        )
        
        # 新しい内壁
        inner_wall = LineElement(
            id="inner_wall",
            start=Point2D(5000, 0),
            end=Point2D(5000, 3000),  # 3m
            style=Style(layer="WALLS")
        )
        
        # ドア
        door = LineElement(
            id="door1",
            start=Point2D(2000, 0),
            end=Point2D(2800, 0),  # 80cm
            style=Style(layer="DOORS")
        )
        
        # 設備（洗面台など）
        fixture = CircleElement(
            id="sink",
            center=Point2D(1000, 1000),
            radius=300,  # 30cm
            style=Style(layer="FIXTURES")
        )
        
        plan_data.elements = [matching_wall, inner_wall, door, fixture]
        
        # 差分抽出の実行
        result = extract_differences(site_data, plan_data, 0.5)
        
        # 結果の検証
        assert len(result.new_elements) == 3  # inner_wall, door, fixture
        assert len(result.removed_elements) == 0
        
        # 建築要素分類の検証
        assert len(result.walls) == 1  # inner_wall
        assert len(result.openings) == 1  # door
        assert len(result.fixtures) == 1  # fixture
        
        # 統計情報の検証
        stats = result.get_statistics()
        assert stats["total_new_elements"] == 3
        assert stats["walls_detected"] == 1
        assert stats["openings_detected"] == 1
        assert stats["fixtures_detected"] == 1
        
        # メタデータの検証
        assert result.analysis_metadata["similarity_threshold"] == 0.5
        assert result.analysis_metadata["total_matches"] == 1  # outer_wall のマッチ
    
    def test_complex_element_matching(self):
        """複雑な要素マッチングのテスト"""
        # 似ているが微妙に異なる要素を含むケース
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        # 完全一致
        exact_match_site = LineElement(id="exact1", start=Point2D(0, 0), end=Point2D(1000, 0))
        exact_match_plan = LineElement(id="exact2", start=Point2D(0, 0), end=Point2D(1000, 0))
        
        # 部分一致（位置が少しずれている）
        partial_match_site = LineElement(id="partial1", start=Point2D(0, 1000), end=Point2D(1000, 1000))
        partial_match_plan = LineElement(id="partial2", start=Point2D(10, 1010), end=Point2D(1010, 1010))
        
        # 一致しない
        no_match_site = LineElement(id="nomatch1", start=Point2D(5000, 5000), end=Point2D(6000, 6000))
        no_match_plan = LineElement(id="nomatch2", start=Point2D(0, 5000), end=Point2D(1000, 5000))
        
        site_data.elements = [exact_match_site, partial_match_site, no_match_site]
        plan_data.elements = [exact_match_plan, partial_match_plan, no_match_plan]
        
        result = extract_differences(site_data, plan_data, 0.3)  # 低い閾値
        
        # マッチング結果の検証
        assert len(result.new_elements) == 1  # no_match_plan のみ
        assert len(result.removed_elements) == 1  # no_match_site のみ
        
        # メタデータの検証
        assert result.analysis_metadata["total_matches"] == 2  # exact と partial


if __name__ == "__main__":
    pytest.main([__file__, "-v"])