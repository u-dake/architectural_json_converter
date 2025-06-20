"""
Test suite for Phase 2 integration

Phase 2統合テストスイート
エンドツーエンドテスト、全コンポーネントの統合テスト
カバレッジ目標: 80%
"""

import pytest
import tempfile
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_structures.geometry_data import (
    GeometryData, LineElement, CircleElement, TextElement, BlockElement,
    Point2D, Style, ElementType, ArchitecturalType, DifferenceResult
)

from engines.dxf_converter import convert_dxf_to_geometry_data
from engines.pdf_converter import convert_pdf_to_geometry_data
from engines.difference_engine import extract_differences, save_difference_result_to_json
from visualization.matplotlib_visualizer import ArchitecturalPlotter
from main import ArchitecturalAnalyzer


class TestDataStructureIntegration:
    """データ構造統合テスト"""
    
    def test_geometry_data_serialization_roundtrip(self):
        """GeometryData シリアライゼーション往復テスト"""
        # 複雑なGeometryDataを作成
        geo_data = GeometryData(
            source_file="integration_test.dxf",
            source_type="dxf",
            metadata={"test": "integration"}
        )
        
        # 様々な要素を追加
        line = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(1000, 1000),
            architectural_type=ArchitecturalType.WALL,
            style=Style(color=255, layer="WALLS")
        )
        
        circle = CircleElement(
            id="circle1",
            center=Point2D(500, 500),
            radius=100,
            architectural_type=ArchitecturalType.FIXTURE
        )
        
        text = TextElement(
            id="text1",
            position=Point2D(100, 100),
            text="統合テスト",
            height=20,
            architectural_type=ArchitecturalType.TEXT_LABEL
        )
        
        geo_data.elements = [line, circle, text]
        
        # JSON形式でシリアライズ
        json_data = geo_data.model_dump(mode='json')
        
        # デシリアライズ
        restored_data = GeometryData.model_validate(json_data)
        
        # データの一致を確認
        assert restored_data.source_file == geo_data.source_file
        assert restored_data.source_type == geo_data.source_type
        assert len(restored_data.elements) == len(geo_data.elements)
        assert restored_data.elements[0].id == "line1"
        assert restored_data.elements[1].id == "circle1"
        assert restored_data.elements[2].id == "text1"
    
    def test_difference_result_serialization_roundtrip(self):
        """DifferenceResult シリアライゼーション往復テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        new_wall = LineElement(
            id="new_wall",
            start=Point2D(0, 1000),
            end=Point2D(2000, 1000),
            architectural_type=ArchitecturalType.WALL
        )
        
        new_fixture = CircleElement(
            id="new_fixture",
            center=Point2D(1000, 500),
            radius=200,
            architectural_type=ArchitecturalType.FIXTURE
        )
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[new_wall, new_fixture],
            walls=[new_wall],
            fixtures=[new_fixture],
            analysis_metadata={
                "processing_time": 1.5,
                "similarity_threshold": 0.5
            }
        )
        
        # JSON往復テスト
        json_data = result.model_dump(mode='json')
        restored_result = DifferenceResult.model_validate(json_data)
        
        # データの一致を確認
        assert len(restored_result.new_elements) == 2
        assert len(restored_result.walls) == 1
        assert len(restored_result.fixtures) == 1
        assert restored_result.analysis_metadata["processing_time"] == 1.5


class TestConverterIntegration:
    """コンバーター統合テスト"""
    
    def create_mock_dxf_file(self, filepath: str):
        """モックDXFファイルを作成"""
        # 実際のDXFファイルは複雑なので、convert_dxf_to_geometry_dataをモック
        mock_geo_data = GeometryData(
            source_file=filepath,
            source_type="dxf"
        )
        
        # テスト用要素を追加
        line = LineElement(
            id="mock_line1",
            start=Point2D(0, 0),
            end=Point2D(1000, 0),
            style=Style(layer="WALLS")
        )
        mock_geo_data.elements = [line]
        return mock_geo_data
    
    def create_mock_pdf_file(self, filepath: str):
        """モックPDFファイルを作成"""
        mock_geo_data = GeometryData(
            source_file=filepath,
            source_type="pdf"
        )
        
        # PDFから抽出されたテキスト要素
        text = TextElement(
            id="mock_text1",
            position=Point2D(100, 100),
            text="PDF図面",
            height=12
        )
        mock_geo_data.elements = [text]
        return mock_geo_data
    
    @patch('engines.dxf_converter.convert_dxf_to_geometry_data')
    def test_dxf_converter_integration(self, mock_converter):
        """DXFコンバーター統合テスト"""
        test_file = "test.dxf"
        mock_data = self.create_mock_dxf_file(test_file)
        mock_converter.return_value = mock_data
        
        result = convert_dxf_to_geometry_data(test_file)
        
        assert result.source_file == test_file
        assert result.source_type == "dxf"
        assert len(result.elements) > 0
        mock_converter.assert_called_once_with(test_file)
    
    @patch('engines.pdf_converter.convert_pdf_to_geometry_data')
    def test_pdf_converter_integration(self, mock_converter):
        """PDFコンバーター統合テスト"""
        test_file = "test.pdf"
        mock_data = self.create_mock_pdf_file(test_file)
        mock_converter.return_value = mock_data
        
        result = convert_pdf_to_geometry_data(test_file)
        
        assert result.source_file == test_file
        assert result.source_type == "pdf"
        assert len(result.elements) > 0
        mock_converter.assert_called_once_with(test_file)


class TestDifferenceEngineIntegration:
    """差分エンジン統合テスト"""
    
    def test_complete_difference_pipeline(self):
        """完全な差分パイプラインテスト"""
        # 敷地図データ
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        
        # 既存の外壁
        outer_wall1 = LineElement(
            id="outer1",
            start=Point2D(0, 0),
            end=Point2D(10000, 0),
            style=Style(layer="WALLS")
        )
        outer_wall2 = LineElement(
            id="outer2",
            start=Point2D(10000, 0),
            end=Point2D(10000, 8000),
            style=Style(layer="WALLS")
        )
        
        site_data.elements = [outer_wall1, outer_wall2]
        
        # 間取り図データ
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        # 同じ外壁（マッチするはず）
        matching_wall1 = LineElement(
            id="match1",
            start=Point2D(0, 0),
            end=Point2D(10000, 0),
            style=Style(layer="WALLS")
        )
        matching_wall2 = LineElement(
            id="match2",
            start=Point2D(10000, 0),
            end=Point2D(10000, 8000),
            style=Style(layer="WALLS")
        )
        
        # 新しい内壁
        inner_wall1 = LineElement(
            id="inner1",
            start=Point2D(5000, 0),
            end=Point2D(5000, 8000),
            style=Style(layer="WALLS")
        )
        inner_wall2 = LineElement(
            id="inner2",
            start=Point2D(0, 4000),
            end=Point2D(10000, 4000),
            style=Style(layer="WALLS")
        )
        
        # ドア
        door = LineElement(
            id="door1",
            start=Point2D(2000, 0),
            end=Point2D(2800, 0),
            style=Style(layer="DOORS")
        )
        
        # 窓
        window = LineElement(
            id="window1",
            start=Point2D(7000, 0),
            end=Point2D(8200, 0),
            style=Style(layer="WINDOWS")
        )
        
        # 設備
        toilet = CircleElement(
            id="toilet",
            center=Point2D(1000, 1000),
            radius=400,
            style=Style(layer="FIXTURES")
        )
        
        sink = BlockElement(
            id="sink",
            position=Point2D(8000, 6000),
            block_name="SINK_SYMBOL",
            style=Style(layer="FIXTURES")
        )
        
        plan_data.elements = [
            matching_wall1, matching_wall2,
            inner_wall1, inner_wall2,
            door, window, toilet, sink
        ]
        
        # 差分抽出実行
        start_time = time.time()
        result = extract_differences(site_data, plan_data, similarity_threshold=0.6)
        processing_time = time.time() - start_time
        
        result.analysis_metadata["processing_time"] = processing_time
        
        # 結果検証
        assert len(result.new_elements) == 6  # inner_wall1, inner_wall2, door, window, toilet, sink
        assert len(result.removed_elements) == 0  # 削除要素なし
        
        # 建築要素分類検証
        assert len(result.walls) >= 2  # 内壁2つ以上
        assert len(result.openings) >= 2  # ドア・窓
        assert len(result.fixtures) >= 2  # トイレ・洗面台
        
        # 統計情報検証
        stats = result.get_statistics()
        assert stats["total_new_elements"] == 6
        assert stats["walls_detected"] >= 2
        assert stats["openings_detected"] >= 2
        assert stats["fixtures_detected"] >= 2
        
        # メタデータ検証
        assert "processing_time" in result.analysis_metadata
        assert "similarity_threshold" in result.analysis_metadata
        assert result.analysis_metadata["similarity_threshold"] == 0.6
    
    def test_json_save_and_load_integration(self):
        """JSON保存・読み込み統合テスト"""
        # テスト用差分結果作成
        site_data = GeometryData(source_file="test_site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="test_plan.dxf", source_type="dxf")
        
        new_element = LineElement(
            id="new1",
            start=Point2D(100, 100),
            end=Point2D(200, 200),
            architectural_type=ArchitecturalType.WALL
        )
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[new_element],
            walls=[new_element],
            analysis_metadata={"test": "integration"}
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # JSON保存
            save_difference_result_to_json(result, temp_path)
            
            # ファイル存在確認
            assert os.path.exists(temp_path)
            
            # JSON読み込み・検証
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # データ構造確認
            assert "site_only" in loaded_data
            assert "site_with_plan" in loaded_data
            assert "new_elements" in loaded_data
            assert "walls" in loaded_data
            assert "analysis_metadata" in loaded_data
            
            # DifferenceResultオブジェクト復元
            restored_result = DifferenceResult.model_validate(loaded_data)
            
            assert len(restored_result.new_elements) == 1
            assert len(restored_result.walls) == 1
            assert restored_result.analysis_metadata["test"] == "integration"
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestVisualizationIntegration:
    """可視化統合テスト"""
    
    def create_test_difference_result(self):
        """テスト用差分結果を作成"""
        site_data = GeometryData(source_file="integration_site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="integration_plan.dxf", source_type="dxf")
        
        # 新規要素（建築要素別）
        wall = LineElement(
            id="integration_wall",
            start=Point2D(0, 1000),
            end=Point2D(3000, 1000),
            architectural_type=ArchitecturalType.WALL
        )
        
        door = LineElement(
            id="integration_door",
            start=Point2D(1000, 1000),
            end=Point2D(1800, 1000),
            architectural_type=ArchitecturalType.DOOR
        )
        
        fixture = CircleElement(
            id="integration_fixture",
            center=Point2D(2000, 2000),
            radius=300,
            architectural_type=ArchitecturalType.FIXTURE
        )
        
        text = TextElement(
            id="integration_text",
            position=Point2D(500, 500),
            text="統合テスト",
            height=100,
            architectural_type=ArchitecturalType.TEXT_LABEL
        )
        
        return DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[wall, door, fixture, text],
            walls=[wall],
            openings=[door],
            fixtures=[fixture],
            analysis_metadata={
                "processing_time": 2.5,
                "similarity_threshold": 0.7,
                "classification_confidence": {
                    "walls": 0.95,
                    "openings": 0.85,
                    "fixtures": 0.90
                }
            }
        )
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_complete_visualization_pipeline(self, mock_close, mock_savefig):
        """完全な可視化パイプラインテスト"""
        result = self.create_test_difference_result()
        plotter = ArchitecturalPlotter(figsize=(20, 16), dpi=200)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 差分可視化
            diff_path = os.path.join(temp_dir, "integration_diff.png")
            result_path1 = plotter.plot_difference_result(result, diff_path)
            
            assert result_path1 == diff_path
            
            # 建築要素解析可視化
            arch_path = os.path.join(temp_dir, "integration_arch.png")
            result_path2 = plotter.plot_architectural_analysis(result, arch_path)
            
            assert result_path2 == arch_path
            
            # 保存関数が呼ばれたことを確認
            assert mock_savefig.call_count == 2
            assert mock_close.call_count == 2
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_visualization_with_edge_cases(self, mock_close, mock_savefig):
        """エッジケースでの可視化テスト"""
        # 空の差分結果
        site_data = GeometryData(source_file="empty_site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="empty_plan.dxf", source_type="dxf")
        
        empty_result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[],
            walls=[],
            openings=[],
            fixtures=[]
        )
        
        plotter = ArchitecturalPlotter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 空の結果でも可視化が正常動作することを確認
            diff_path = os.path.join(temp_dir, "empty_diff.png")
            arch_path = os.path.join(temp_dir, "empty_arch.png")
            
            plotter.plot_difference_result(empty_result, diff_path)
            plotter.plot_architectural_analysis(empty_result, arch_path)
            
            assert mock_savefig.call_count == 2
            assert mock_close.call_count == 2


class TestMainApplicationIntegration:
    """メインアプリケーション統合テスト"""
    
    @patch('engines.dxf_converter.convert_dxf_to_geometry_data')
    @patch('engines.pdf_converter.convert_pdf_to_geometry_data')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_architectural_analyzer_complete_workflow(
        self, mock_close, mock_savefig, mock_pdf_converter, mock_dxf_converter
    ):
        """ArchitecturalAnalyzerの完全ワークフローテスト"""
        
        # モックデータの準備
        site_data = GeometryData(source_file="integration_site.dxf", source_type="dxf")
        site_line = LineElement(
            id="site_existing",
            start=Point2D(0, 0),
            end=Point2D(5000, 0)
        )
        site_data.elements = [site_line]
        
        plan_data = GeometryData(source_file="integration_plan.dxf", source_type="dxf")
        plan_line = LineElement(
            id="plan_existing",
            start=Point2D(0, 0),
            end=Point2D(5000, 0)
        )
        new_wall = LineElement(
            id="plan_new_wall",
            start=Point2D(0, 2000),
            end=Point2D(5000, 2000),
            style=Style(layer="WALLS")
        )
        new_fixture = CircleElement(
            id="plan_new_fixture",
            center=Point2D(2500, 1000),
            radius=200,
            style=Style(layer="FIXTURES")
        )
        plan_data.elements = [plan_line, new_wall, new_fixture]
        
        # モック設定
        mock_dxf_converter.return_value = site_data
        mock_pdf_converter.return_value = plan_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ArchitecturalAnalyzer(output_dir=temp_dir, verbose=False)
            
            # 完全解析の実行
            result = analyzer.run_complete_analysis(
                site_file="test_site.dxf",
                plan_file="test_plan.pdf",  # 異なるファイル形式
                tolerance=0.6,
                enable_visualization=True,
                enable_interactive=False,
                base_filename="integration_test"
            )
            
            # 結果検証
            assert result["success"] is True
            assert "statistics" in result
            assert "output_files" in result
            assert "processing_time" in result
            
            # 統計情報検証
            stats = result["statistics"]
            assert stats["total_new_elements"] == 2  # new_wall, new_fixture
            assert stats["walls_detected"] >= 1
            assert stats["fixtures_detected"] >= 1
            
            # 出力ファイル検証
            output_files = result["output_files"]
            assert "json" in output_files
            assert "visualizations" in output_files
            assert len(output_files["visualizations"]) == 2  # diff + arch
            
            # コンバーターが呼ばれたことを確認
            mock_dxf_converter.assert_called_once_with("test_site.dxf")
            mock_pdf_converter.assert_called_once_with("test_plan.pdf")
            
            # 可視化が実行されたことを確認
            assert mock_savefig.call_count == 2
    
    def test_architectural_analyzer_error_handling(self):
        """ArchitecturalAnalyzerのエラーハンドリングテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ArchitecturalAnalyzer(output_dir=temp_dir, verbose=False)
            
            # 存在しないファイルでのテスト
            result = analyzer.run_complete_analysis(
                site_file="nonexistent_site.dxf",
                plan_file="nonexistent_plan.dxf"
            )
            
            # エラーが適切に処理されることを確認
            assert result["success"] is False
            assert "error" in result
    
    @patch('engines.dxf_converter.convert_dxf_to_geometry_data')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_architectural_analyzer_file_type_detection(
        self, mock_close, mock_savefig, mock_dxf_converter
    ):
        """ファイルタイプ自動検出テスト"""
        
        # テストデータ
        test_data = GeometryData(source_file="test.dxf", source_type="dxf")
        test_line = LineElement(id="test", start=Point2D(0, 0), end=Point2D(100, 100))
        test_data.elements = [test_line]
        
        mock_dxf_converter.return_value = test_data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ArchitecturalAnalyzer(output_dir=temp_dir, verbose=False)
            
            # DXFファイルの検出テスト
            site_type, site_data = analyzer.load_drawing_file("test.dxf")
            assert site_type == "dxf"
            assert isinstance(site_data, GeometryData)
            
            mock_dxf_converter.assert_called_with("test.dxf")
    
    def test_architectural_analyzer_unsupported_file_type(self):
        """サポートされていないファイルタイプのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ArchitecturalAnalyzer(output_dir=temp_dir, verbose=False)
            
            # サポートされていないファイル形式
            with pytest.raises(ValueError):
                analyzer.load_drawing_file("test.dwg")
    
    def test_architectural_analyzer_file_not_found(self):
        """ファイルが見つからない場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ArchitecturalAnalyzer(output_dir=temp_dir, verbose=False)
            
            # 存在しないファイル
            with pytest.raises(FileNotFoundError):
                analyzer.load_drawing_file("nonexistent.dxf")


class TestFullSystemIntegration:
    """フルシステム統合テスト"""
    
    @patch('main.ArchitecturalAnalyzer.load_drawing_file')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_end_to_end_cli_simulation(
        self, mock_close, mock_savefig, mock_load_file
    ):
        """エンドツーエンドCLIシミュレーションテスト"""
        
        # 完全なテストシナリオ
        site_data = GeometryData(source_file="e2e_site.dxf", source_type="dxf")
        
        # 敷地の境界線
        boundary_lines = [
            LineElement(id="bound1", start=Point2D(0, 0), end=Point2D(12000, 0)),
            LineElement(id="bound2", start=Point2D(12000, 0), end=Point2D(12000, 9000)),
            LineElement(id="bound3", start=Point2D(12000, 9000), end=Point2D(0, 9000)),
            LineElement(id="bound4", start=Point2D(0, 9000), end=Point2D(0, 0))
        ]
        site_data.elements = boundary_lines
        
        plan_data = GeometryData(source_file="e2e_plan.dxf", source_type="dxf")
        
        # 同じ境界線（マッチするべき）
        matching_boundaries = [
            LineElement(id="match1", start=Point2D(0, 0), end=Point2D(12000, 0)),
            LineElement(id="match2", start=Point2D(12000, 0), end=Point2D(12000, 9000)),
            LineElement(id="match3", start=Point2D(12000, 9000), end=Point2D(0, 9000)),
            LineElement(id="match4", start=Point2D(0, 9000), end=Point2D(0, 0))
        ]
        
        # 建物の新しい要素
        new_elements = [
            # 外壁
            LineElement(
                id="wall_ext1", start=Point2D(2000, 2000), end=Point2D(10000, 2000),
                architectural_type=ArchitecturalType.WALL, style=Style(layer="WALLS")
            ),
            LineElement(
                id="wall_ext2", start=Point2D(10000, 2000), end=Point2D(10000, 7000),
                architectural_type=ArchitecturalType.WALL, style=Style(layer="WALLS")
            ),
            LineElement(
                id="wall_ext3", start=Point2D(10000, 7000), end=Point2D(2000, 7000),
                architectural_type=ArchitecturalType.WALL, style=Style(layer="WALLS")
            ),
            LineElement(
                id="wall_ext4", start=Point2D(2000, 7000), end=Point2D(2000, 2000),
                architectural_type=ArchitecturalType.WALL, style=Style(layer="WALLS")
            ),
            
            # 内壁
            LineElement(
                id="wall_int1", start=Point2D(6000, 2000), end=Point2D(6000, 7000),
                architectural_type=ArchitecturalType.WALL, style=Style(layer="WALLS")
            ),
            LineElement(
                id="wall_int2", start=Point2D(2000, 4500), end=Point2D(10000, 4500),
                architectural_type=ArchitecturalType.WALL, style=Style(layer="WALLS")
            ),
            
            # ドア
            LineElement(
                id="door_main", start=Point2D(5000, 2000), end=Point2D(5800, 2000),
                architectural_type=ArchitecturalType.DOOR, style=Style(layer="DOORS")
            ),
            LineElement(
                id="door_room1", start=Point2D(6000, 3200), end=Point2D(6000, 4000),
                architectural_type=ArchitecturalType.DOOR, style=Style(layer="DOORS")
            ),
            
            # 窓
            LineElement(
                id="window1", start=Point2D(3000, 2000), end=Point2D(4000, 2000),
                architectural_type=ArchitecturalType.WINDOW, style=Style(layer="WINDOWS")
            ),
            LineElement(
                id="window2", start=Point2D(7000, 2000), end=Point2D(8000, 2000),
                architectural_type=ArchitecturalType.WINDOW, style=Style(layer="WINDOWS")
            ),
            LineElement(
                id="window3", start=Point2D(10000, 3000), end=Point2D(10000, 4000),
                architectural_type=ArchitecturalType.WINDOW, style=Style(layer="WINDOWS")
            ),
            
            # 設備
            CircleElement(
                id="toilet", center=Point2D(3000, 6000), radius=400,
                architectural_type=ArchitecturalType.FIXTURE, style=Style(layer="FIXTURES")
            ),
            CircleElement(
                id="sink", center=Point2D(8000, 6000), radius=300,
                architectural_type=ArchitecturalType.FIXTURE, style=Style(layer="FIXTURES")
            ),
            BlockElement(
                id="kitchen", position=Point2D(8000, 3000), block_name="KITCHEN_UNIT",
                architectural_type=ArchitecturalType.FIXTURE, style=Style(layer="FIXTURES")
            ),
            
            # ラベル
            TextElement(
                id="label_living", position=Point2D(4000, 3000), text="リビング", height=200,
                architectural_type=ArchitecturalType.TEXT_LABEL
            ),
            TextElement(
                id="label_bedroom", position=Point2D(8000, 3000), text="寝室", height=200,
                architectural_type=ArchitecturalType.TEXT_LABEL
            )
        ]
        
        plan_data.elements = matching_boundaries + new_elements
        
        # load_drawing_fileのモック設定
        def mock_load_side_effect(filepath):
            if "site" in filepath:
                return ("dxf", site_data)
            elif "plan" in filepath:
                return ("dxf", plan_data)
            else:
                raise FileNotFoundError(f"File not found: {filepath}")
        
        mock_load_file.side_effect = mock_load_side_effect
        
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = ArchitecturalAnalyzer(output_dir=temp_dir, verbose=True)
            
            # フル解析実行
            start_time = time.time()
            result = analyzer.run_complete_analysis(
                site_file="e2e_site.dxf",
                plan_file="e2e_plan.dxf",
                tolerance=0.5,
                enable_visualization=True,
                enable_interactive=False,
                base_filename="e2e_test"
            )
            execution_time = time.time() - start_time
            
            # 実行成功確認
            assert result["success"] is True
            
            # 統計検証
            stats = result["statistics"]
            assert stats["total_new_elements"] == len(new_elements)
            assert stats["walls_detected"] >= 6  # 外壁4 + 内壁2
            assert stats["openings_detected"] >= 5  # ドア2 + 窓3
            assert stats["fixtures_detected"] >= 3  # トイレ、洗面台、キッチン
            
            # パフォーマンス検証
            assert result["processing_time"] < 10.0  # 10秒以内
            assert execution_time < 15.0  # 全体で15秒以内
            
            # 出力ファイル検証
            output_files = result["output_files"]
            assert os.path.exists(output_files["json"])
            assert len(output_files["visualizations"]) == 2
            
            # JSON結果の検証
            with open(output_files["json"], 'r', encoding='utf-8') as f:
                json_result = json.load(f)
            
            assert "new_elements" in json_result
            assert "walls" in json_result
            assert "openings" in json_result
            assert "fixtures" in json_result
            assert "analysis_metadata" in json_result
            
            # メタデータの検証
            metadata = json_result["analysis_metadata"]
            assert "processing_time" in metadata
            assert "similarity_threshold" in metadata
            assert metadata["similarity_threshold"] == 0.5
            
            print(f"E2Eテスト完了: {stats['total_new_elements']}個の新規要素検出")
            print(f"処理時間: {result['processing_time']:.2f}秒")
            print(f"壁: {stats['walls_detected']}個, 開口部: {stats['openings_detected']}個, 設備: {stats['fixtures_detected']}個")


class TestPerformanceIntegration:
    """パフォーマンス統合テスト"""
    
    def test_large_dataset_performance(self):
        """大規模データセットのパフォーマンステスト"""
        # 大量の要素を含むテストデータ作成
        site_data = GeometryData(source_file="large_site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="large_plan.dxf", source_type="dxf")
        
        # 1000個の線分要素を作成
        site_elements = []
        plan_elements = []
        
        for i in range(1000):
            # 敷地図要素
            site_line = LineElement(
                id=f"site_line_{i}",
                start=Point2D(i * 10, 0),
                end=Point2D(i * 10 + 5, 5)
            )
            site_elements.append(site_line)
            
            # 間取り図要素（50%は同じ、50%は新規）
            if i < 500:
                # マッチする要素
                plan_line = LineElement(
                    id=f"plan_line_{i}",
                    start=Point2D(i * 10, 0),
                    end=Point2D(i * 10 + 5, 5)
                )
            else:
                # 新規要素
                plan_line = LineElement(
                    id=f"plan_new_{i}",
                    start=Point2D(i * 10, 100),
                    end=Point2D(i * 10 + 5, 105),
                    architectural_type=ArchitecturalType.WALL
                )
            plan_elements.append(plan_line)
        
        site_data.elements = site_elements
        plan_data.elements = plan_elements
        
        # パフォーマンステスト実行
        start_time = time.time()
        result = extract_differences(site_data, plan_data, similarity_threshold=0.7)
        processing_time = time.time() - start_time
        
        # パフォーマンス検証
        assert processing_time < 30.0  # 30秒以内で完了
        assert len(result.new_elements) == 500  # 新規要素500個
        
        print(f"大規模データセットテスト: {len(site_data.elements) + len(plan_data.elements)}要素, 処理時間: {processing_time:.2f}秒")
    
    def test_memory_usage_integration(self):
        """メモリ使用量統合テスト"""
        import gc
        import sys
        
        # メモリ使用量を監視しながらテスト実行
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # 中規模のテストデータでメモリリークをチェック
        for iteration in range(10):
            site_data = GeometryData(source_file=f"memory_test_site_{iteration}.dxf", source_type="dxf")
            plan_data = GeometryData(source_file=f"memory_test_plan_{iteration}.dxf", source_type="dxf")
            
            # 100個の要素を作成
            elements = []
            for i in range(100):
                element = LineElement(
                    id=f"mem_test_{iteration}_{i}",
                    start=Point2D(i, i),
                    end=Point2D(i + 10, i + 10)
                )
                elements.append(element)
            
            site_data.elements = elements[:50]
            plan_data.elements = elements[25:]  # 25個重複、25個新規
            
            # 差分抽出実行
            result = extract_differences(site_data, plan_data)
            
            # 明示的にオブジェクトを削除
            del site_data, plan_data, result, elements
            gc.collect()
        
        # メモリリークチェック
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # オブジェクト数の増加が合理的な範囲内であることを確認
        assert object_growth < 10000, f"Potential memory leak: {object_growth} objects created"
        
        print(f"メモリテスト完了: オブジェクト増加数 {object_growth}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])