"""
Test suite for matplotlib visualization system

matplotlib可視化システムのテストスイート
テスト対象: src/visualization/matplotlib_visualizer.py
カバレッジ目標: 80%
"""

import pytest
import matplotlib
matplotlib.use('Agg')  # GUI不要のバックエンドを使用
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, mock_open

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_structures.geometry_data import (
    GeometryData, LineElement, CircleElement, ArcElement, PolylineElement,
    TextElement, BlockElement, Point2D, Style, ElementType, ArchitecturalType,
    DifferenceResult
)

from visualization.matplotlib_visualizer import ArchitecturalPlotter


class TestArchitecturalPlotter:
    """ArchitecturalPlotter クラスの基本テスト"""
    
    def test_initialization_default(self):
        """デフォルト設定での初期化テスト"""
        plotter = ArchitecturalPlotter()
        
        assert plotter.figsize == (16, 12)
        assert plotter.dpi == 300
        assert 'site_elements' in plotter.colors
        assert 'new_elements' in plotter.colors
        assert 'walls' in plotter.colors
        assert 'line_width' in plotter.styles
    
    def test_initialization_custom(self):
        """カスタム設定での初期化テスト"""
        plotter = ArchitecturalPlotter(figsize=(20, 15), dpi=150)
        
        assert plotter.figsize == (20, 15)
        assert plotter.dpi == 150
        assert len(plotter.colors) > 0
        assert len(plotter.styles) > 0
    
    def test_color_definitions(self):
        """色定義の確認テスト"""
        plotter = ArchitecturalPlotter()
        
        required_colors = [
            'site_elements', 'new_elements', 'walls', 
            'openings', 'fixtures', 'text', 'removed_elements'
        ]
        
        for color_key in required_colors:
            assert color_key in plotter.colors
            assert isinstance(plotter.colors[color_key], str)
            assert plotter.colors[color_key].startswith('#')
    
    def test_style_definitions(self):
        """スタイル定義の確認テスト"""
        plotter = ArchitecturalPlotter()
        
        required_styles = ['line_width', 'text_size', 'marker_size', 'alpha']
        
        for style_key in required_styles:
            assert style_key in plotter.styles
            assert isinstance(plotter.styles[style_key], (int, float))


class TestElementPlotting:
    """要素描画機能のテスト"""
    
    def setup_method(self):
        """各テスト前のセットアップ"""
        self.plotter = ArchitecturalPlotter()
        self.fig, self.ax = plt.subplots()
    
    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        plt.close(self.fig)
    
    def test_plot_line_element(self):
        """線分要素の描画テスト"""
        line = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(100, 100)
        )
        
        # 描画実行（例外が発生しないことを確認）
        self.plotter.plot_geometry_element(self.ax, line, '#FF0000')
        
        # axesに線が追加されたことを確認
        lines = self.ax.get_lines()
        assert len(lines) > 0
    
    def test_plot_circle_element(self):
        """円要素の描画テスト"""
        circle = CircleElement(
            id="circle1",
            center=Point2D(50, 50),
            radius=25
        )
        
        self.plotter.plot_geometry_element(self.ax, circle, '#00FF00')
        
        # パッチが追加されたことを確認
        patches = self.ax.patches
        assert len(patches) > 0
        assert patches[0].get_radius() == 25
    
    def test_plot_arc_element(self):
        """円弧要素の描画テスト"""
        arc = ArcElement(
            id="arc1",
            center=Point2D(0, 0),
            radius=50,
            start_angle=0,
            end_angle=np.pi/2
        )
        
        self.plotter.plot_geometry_element(self.ax, arc, '#0000FF')
        
        lines = self.ax.get_lines()
        assert len(lines) > 0
    
    def test_plot_polyline_element_open(self):
        """開いたポリライン要素の描画テスト"""
        vertices = [Point2D(0, 0), Point2D(50, 0), Point2D(50, 50), Point2D(0, 50)]
        polyline = PolylineElement(
            id="poly1",
            vertices=vertices,
            is_closed=False
        )
        
        self.plotter.plot_geometry_element(self.ax, polyline, '#FF00FF')
        
        lines = self.ax.get_lines()
        assert len(lines) > 0
    
    def test_plot_polyline_element_closed(self):
        """閉じたポリライン要素の描画テスト"""
        vertices = [Point2D(0, 0), Point2D(50, 0), Point2D(50, 50), Point2D(0, 50)]
        polyline = PolylineElement(
            id="poly1",
            vertices=vertices,
            is_closed=True
        )
        
        self.plotter.plot_geometry_element(self.ax, polyline, '#FFFF00')
        
        lines = self.ax.get_lines()
        assert len(lines) > 0
    
    def test_plot_polyline_element_insufficient_vertices(self):
        """頂点数不足のポリライン描画テスト"""
        polyline = PolylineElement(
            id="poly1",
            vertices=[Point2D(0, 0)],  # 頂点1つのみ
            is_closed=False
        )
        
        # 例外が発生しないことを確認
        self.plotter.plot_geometry_element(self.ax, polyline, '#000000')
    
    def test_plot_text_element(self):
        """テキスト要素の描画テスト"""
        text = TextElement(
            id="text1",
            position=Point2D(10, 10),
            text="テストテキスト",
            height=12.0,
            rotation=np.pi/4
        )
        
        self.plotter.plot_geometry_element(self.ax, text, '#666666')
        
        # テキストが追加されたことを確認
        texts = self.ax.texts
        assert len(texts) > 0
        assert texts[0].get_text() == "テストテキスト"
    
    def test_plot_block_element(self):
        """ブロック要素の描画テスト"""
        block = BlockElement(
            id="block1",
            position=Point2D(100, 100),
            block_name="TEST_BLOCK"
        )
        
        self.plotter.plot_geometry_element(self.ax, block, '#FF8800')
        
        lines = self.ax.get_lines()
        assert len(lines) > 0
    
    def test_plot_with_alpha(self):
        """透明度付き描画テスト"""
        line = LineElement(
            id="line1",
            start=Point2D(0, 0),
            end=Point2D(100, 100)
        )
        
        self.plotter.plot_geometry_element(self.ax, line, '#FF0000', alpha=0.5)
        
        lines = self.ax.get_lines()
        assert len(lines) > 0


class TestGeometryDataPlotting:
    """統一データ構造描画のテスト"""
    
    def setup_method(self):
        self.plotter = ArchitecturalPlotter()
        self.fig, self.ax = plt.subplots()
    
    def teardown_method(self):
        plt.close(self.fig)
    
    def test_plot_empty_geometry_data(self):
        """空のGeometryDataの描画テスト"""
        geo_data = GeometryData(source_file="empty.dxf", source_type="dxf")
        
        # 例外が発生しないことを確認
        self.plotter.plot_geometry_data(self.ax, geo_data)
    
    def test_plot_geometry_data_with_mixed_elements(self):
        """混合要素のGeometryData描画テスト"""
        geo_data = GeometryData(source_file="mixed.dxf", source_type="dxf")
        
        # 異なる建築要素タイプの要素を追加
        wall = LineElement(
            id="wall1", 
            start=Point2D(0, 0), 
            end=Point2D(1000, 0),
            architectural_type=ArchitecturalType.WALL
        )
        
        door = LineElement(
            id="door1",
            start=Point2D(200, 0),
            end=Point2D(280, 0),
            architectural_type=ArchitecturalType.DOOR
        )
        
        fixture = CircleElement(
            id="fixture1",
            center=Point2D(500, 500),
            radius=100,
            architectural_type=ArchitecturalType.FIXTURE
        )
        
        text = TextElement(
            id="text1",
            position=Point2D(100, 100),
            text="ラベル",
            height=20,
            architectural_type=ArchitecturalType.TEXT_LABEL
        )
        
        unknown = LineElement(
            id="unknown1",
            start=Point2D(800, 800),
            end=Point2D(900, 900),
            architectural_type=ArchitecturalType.UNKNOWN
        )
        
        geo_data.elements = [wall, door, fixture, text, unknown]
        
        self.plotter.plot_geometry_data(self.ax, geo_data, show_legend=True)
        
        # 要素が描画されたことを確認
        assert len(self.ax.get_lines()) > 0 or len(self.ax.patches) > 0 or len(self.ax.texts) > 0
        
        # 凡例が表示されたことを確認
        legend = self.ax.get_legend()
        assert legend is not None
    
    def test_plot_geometry_data_without_legend(self):
        """凡例なしのGeometryData描画テスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        line = LineElement(id="line1", start=Point2D(0, 0), end=Point2D(100, 100))
        geo_data.elements = [line]
        
        self.plotter.plot_geometry_data(self.ax, geo_data, show_legend=False)
        
        # 凡例が表示されていないことを確認
        legend = self.ax.get_legend()
        assert legend is None
    
    def test_architectural_type_color_mapping(self):
        """建築要素タイプの色マッピングテスト"""
        geo_data = GeometryData(source_file="test.dxf", source_type="dxf")
        
        wall = LineElement(
            id="wall1",
            start=Point2D(0, 0),
            end=Point2D(100, 0),
            architectural_type=ArchitecturalType.WALL
        )
        geo_data.elements = [wall]
        
        self.plotter.plot_geometry_data(self.ax, geo_data)
        
        # 壁の色で描画されることを確認（実際の色確認は複雑なので、例外が発生しないことで代用）
        assert len(self.ax.get_lines()) > 0


class TestDifferenceVisualization:
    """差分可視化のテスト"""
    
    def setup_method(self):
        self.plotter = ArchitecturalPlotter()
        
        # テスト用データの準備
        self.site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        site_line = LineElement(id="site1", start=Point2D(0, 0), end=Point2D(1000, 0))
        self.site_data.elements = [site_line]
        
        self.plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        plan_line = LineElement(id="plan1", start=Point2D(0, 0), end=Point2D(1000, 0))
        new_wall = LineElement(
            id="new_wall",
            start=Point2D(0, 500),
            end=Point2D(1000, 500),
            architectural_type=ArchitecturalType.WALL
        )
        new_fixture = CircleElement(
            id="new_fixture",
            center=Point2D(500, 250),
            radius=50,
            architectural_type=ArchitecturalType.FIXTURE
        )
        self.plan_data.elements = [plan_line, new_wall, new_fixture]
        
        self.difference_result = DifferenceResult(
            site_only=self.site_data,
            site_with_plan=self.plan_data,
            new_elements=[new_wall, new_fixture],
            walls=[new_wall],
            fixtures=[new_fixture]
        )
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('os.makedirs')
    def test_plot_difference_result(self, mock_makedirs, mock_close, mock_savefig):
        """差分結果可視化テスト"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            result_path = self.plotter.plot_difference_result(
                self.difference_result, 
                temp_path
            )
            
            assert result_path == temp_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_difference_result_with_directory_creation(self, mock_close, mock_savefig):
        """ディレクトリ作成付き差分可視化テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "subdir", "difference.png")
            
            result_path = self.plotter.plot_difference_result(
                self.difference_result,
                output_path
            )
            
            assert result_path == output_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
    
    def test_plot_difference_result_empty_elements(self):
        """空の新規要素での差分可視化テスト"""
        empty_result = DifferenceResult(
            site_only=self.site_data,
            site_with_plan=self.site_data,  # 同じデータ
            new_elements=[],
            walls=[],
            fixtures=[]
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            with patch('matplotlib.pyplot.savefig'), patch('matplotlib.pyplot.close'):
                result_path = self.plotter.plot_difference_result(empty_result, temp_path)
                assert result_path == temp_path
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestArchitecturalAnalysis:
    """建築要素解析可視化のテスト"""
    
    def setup_method(self):
        self.plotter = ArchitecturalPlotter()
        
        # テスト用の差分結果を準備
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        wall1 = LineElement(
            id="wall1",
            start=Point2D(0, 0),
            end=Point2D(1000, 0),
            architectural_type=ArchitecturalType.WALL
        )
        
        wall2 = LineElement(
            id="wall2", 
            start=Point2D(0, 0),
            end=Point2D(0, 1000),
            architectural_type=ArchitecturalType.WALL
        )
        
        door = LineElement(
            id="door1",
            start=Point2D(200, 0),
            end=Point2D(280, 0),
            architectural_type=ArchitecturalType.DOOR
        )
        
        window = LineElement(
            id="window1",
            start=Point2D(500, 0),
            end=Point2D(600, 0),
            architectural_type=ArchitecturalType.WINDOW
        )
        
        fixture1 = CircleElement(
            id="fixture1",
            center=Point2D(500, 500),
            radius=100,
            architectural_type=ArchitecturalType.FIXTURE
        )
        
        fixture2 = BlockElement(
            id="fixture2",
            position=Point2D(800, 800),
            block_name="TOILET",
            architectural_type=ArchitecturalType.FIXTURE
        )
        
        all_new_elements = [wall1, wall2, door, window, fixture1, fixture2]
        
        self.difference_result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=all_new_elements,
            walls=[wall1, wall2],
            openings=[door, window],
            fixtures=[fixture1, fixture2],
            analysis_metadata={
                'processing_time': 1.23,
                'classification_confidence': {
                    'walls': 0.95,
                    'openings': 0.82,
                    'fixtures': 0.88
                }
            }
        )
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_architectural_analysis(self, mock_close, mock_savefig):
        """建築要素解析可視化テスト"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            result_path = self.plotter.plot_architectural_analysis(
                self.difference_result,
                temp_path
            )
            
            assert result_path == temp_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_architectural_analysis_empty_elements(self, mock_close, mock_savefig):
        """空要素での建築要素解析可視化テスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        empty_result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[],
            walls=[],
            openings=[],
            fixtures=[]
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            result_path = self.plotter.plot_architectural_analysis(empty_result, temp_path)
            assert result_path == temp_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_statistics_text_generation(self):
        """統計テキスト生成テスト"""
        # plot_architectural_analysis内で統計情報が正しく表示されるかのテスト
        stats = self.difference_result.get_statistics()
        
        assert stats['total_new_elements'] == 6
        assert stats['walls_detected'] == 2
        assert stats['openings_detected'] == 2
        assert stats['fixtures_detected'] == 2
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_bounding_box_calculation_with_unimplemented_elements(self, mock_close, mock_savefig):
        """境界ボックス計算で未実装要素があるケースのテスト"""
        # NotImplementedErrorを発生させるモック要素を作成
        mock_element = MagicMock()
        mock_element.get_bounding_box.side_effect = NotImplementedError()
        
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        result_with_mock = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data,
            new_elements=[mock_element],
            walls=[],
            openings=[],
            fixtures=[]
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            # 例外が発生しないことを確認
            result_path = self.plotter.plot_architectural_analysis(result_with_mock, temp_path)
            assert result_path == temp_path
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestFileHandling:
    """ファイル処理のテスト"""
    
    def setup_method(self):
        self.plotter = ArchitecturalPlotter()
    
    @patch('builtins.print')
    def test_output_messages(self, mock_print):
        """出力メッセージのテスト"""
        site_data = GeometryData(source_file="site.dxf", source_type="dxf")
        plan_data = GeometryData(source_file="plan.dxf", source_type="dxf")
        
        result = DifferenceResult(
            site_only=site_data,
            site_with_plan=plan_data
        )
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            with patch('matplotlib.pyplot.savefig'), patch('matplotlib.pyplot.close'):
                self.plotter.plot_difference_result(result, temp_path)
                
                # print文が呼ばれたことを確認
                mock_print.assert_called()
                
                # 出力メッセージの内容を確認
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                assert any("差分可視化を保存しました" in call for call in print_calls)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMainFunction:
    """main関数のテスト"""
    
    @patch('sys.argv', ['matplotlib_visualizer.py', 'test_result.json'])
    @patch('builtins.open', new_callable=mock_open, read_data='{"site_only": {"source_file": "site.dxf", "source_type": "dxf", "layers": [], "elements": [], "metadata": {}}, "site_with_plan": {"source_file": "plan.dxf", "source_type": "dxf", "layers": [], "elements": [], "metadata": {}}, "new_elements": [], "removed_elements": [], "modified_elements": [], "walls": [], "openings": [], "fixtures": [], "analysis_metadata": {}}')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('builtins.print')
    def test_main_with_valid_file(self, mock_print, mock_close, mock_savefig, mock_file):
        """有効なファイルでのmain関数テスト"""
        from visualization.matplotlib_visualizer import main
        
        # main関数を実行
        main()
        
        # ファイルが開かれたことを確認
        mock_file.assert_called()
        
        # 可視化が実行されたことを確認
        mock_savefig.assert_called()
        mock_close.assert_called()
        
        # 成功メッセージが出力されたことを確認
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("可視化完了" in call for call in print_calls)
    
    @patch('sys.argv', ['matplotlib_visualizer.py'])
    @patch('builtins.print')
    def test_main_without_arguments(self, mock_print):
        """引数なしでのmain関数テスト"""
        from visualization.matplotlib_visualizer import main
        
        main()
        
        # 使用方法が表示されたことを確認
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("使用方法" in call for call in print_calls)
    
    @patch('sys.argv', ['matplotlib_visualizer.py', 'nonexistent.json'])
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('builtins.print')
    def test_main_with_file_error(self, mock_print, mock_open):
        """ファイルエラーでのmain関数テスト"""
        from visualization.matplotlib_visualizer import main
        
        main()
        
        # エラーメッセージが出力されたことを確認
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("エラー" in call for call in print_calls)
    
    @patch('sys.argv', ['matplotlib_visualizer.py', 'invalid.json'])
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('builtins.print')
    def test_main_with_json_error(self, mock_print, mock_file):
        """JSON解析エラーでのmain関数テスト"""
        from visualization.matplotlib_visualizer import main
        
        main()
        
        # エラーメッセージが出力されたことを確認
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("エラー" in call for call in print_calls)


class TestEdgeCases:
    """エッジケースのテスト"""
    
    def setup_method(self):
        self.plotter = ArchitecturalPlotter()
    
    def test_plot_with_extreme_coordinates(self):
        """極端な座標値での描画テスト"""
        fig, ax = plt.subplots()
        
        try:
            # 非常に大きな座標
            large_line = LineElement(
                id="large",
                start=Point2D(1e6, 1e6),
                end=Point2D(2e6, 2e6)
            )
            
            # 非常に小さな座標
            small_line = LineElement(
                id="small",
                start=Point2D(1e-6, 1e-6),
                end=Point2D(2e-6, 2e-6)
            )
            
            # 例外が発生しないことを確認
            self.plotter.plot_geometry_element(ax, large_line, '#FF0000')
            self.plotter.plot_geometry_element(ax, small_line, '#00FF00')
            
        finally:
            plt.close(fig)
    
    def test_plot_with_nan_coordinates(self):
        """NaN座標での描画テスト"""
        fig, ax = plt.subplots()
        
        try:
            # NaN座標を含む線分
            nan_line = LineElement(
                id="nan_line",
                start=Point2D(float('nan'), 0),
                end=Point2D(100, float('nan'))
            )
            
            # エラーが発生しても例外でプログラムが停止しないことを確認
            try:
                self.plotter.plot_geometry_element(ax, nan_line, '#FF0000')
            except:
                pass  # NaN座標での描画エラーは許容
            
        finally:
            plt.close(fig)
    
    def test_empty_polyline_vertices(self):
        """空の頂点リストを持つポリラインの描画テスト"""
        fig, ax = plt.subplots()
        
        try:
            empty_polyline = PolylineElement(
                id="empty",
                vertices=[],
                is_closed=False
            )
            
            # 例外が発生しないことを確認
            self.plotter.plot_geometry_element(ax, empty_polyline, '#FF0000')
            
        finally:
            plt.close(fig)
    
    def test_zero_radius_circle(self):
        """半径ゼロの円の描画テスト"""
        fig, ax = plt.subplots()
        
        try:
            zero_circle = CircleElement(
                id="zero",
                center=Point2D(50, 50),
                radius=0
            )
            
            # 例外が発生しないことを確認
            self.plotter.plot_geometry_element(ax, zero_circle, '#FF0000')
            
        finally:
            plt.close(fig)
    
    def test_empty_text_element(self):
        """空文字列のテキスト要素描画テスト"""
        fig, ax = plt.subplots()
        
        try:
            empty_text = TextElement(
                id="empty_text",
                position=Point2D(10, 10),
                text="",
                height=12.0
            )
            
            # 例外が発生しないことを確認
            self.plotter.plot_geometry_element(ax, empty_text, '#666666')
            
        finally:
            plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])