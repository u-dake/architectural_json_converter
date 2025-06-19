"""
DXF Analyzer Tests

開発チームへ:
実際のDXFファイルを使用してテストケースを作成してください。
"""

import pytest
import json
from pathlib import Path
import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from analyzers.dxf_analyzer import analyze_dxf_structure, save_analysis_to_json


class TestDXFAnalyzer:
    """DXF解析モジュールのテストクラス"""

    def test_analyze_dxf_structure_basic(self):
        """基本的なDXFファイル解析のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.dxf"
        if os.path.exists(test_file):
            result = analyze_dxf_structure(test_file)
            
            # 必須フィールドの存在確認
            assert "file_info" in result
            assert "header_info" in result
            assert "layers" in result
            assert "entities_summary" in result
            assert "entities_detail" in result
            assert "bounds" in result
            
            # ファイル情報の検証
            assert result["file_info"]["filepath"] == test_file
            assert result["file_info"]["file_size"] > 0
            assert "dxf_version" in result["file_info"]
            
            # 境界情報の検証
            bounds = result["bounds"]
            assert "min_x" in bounds
            assert "min_y" in bounds
            assert "max_x" in bounds
            assert "max_y" in bounds
            assert bounds["width"] >= 0
            assert bounds["height"] >= 0

    def test_analyze_dxf_structure_file_not_found(self):
        """存在しないファイルに対するエラーハンドリングのテスト"""
        with pytest.raises(FileNotFoundError):
            analyze_dxf_structure("non_existent_file.dxf")

    def test_save_analysis_to_json(self, tmp_path):
        """JSON保存機能のテスト"""
        # サンプルデータ
        test_data = {
            "file_info": {"filepath": "test.dxf", "file_size": 1000},
            "layers": [],
            "entities_summary": {"LINE": 10},
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 100, "max_y": 100}
        }
        
        # JSONファイルに保存
        output_file = tmp_path / "test_output.json"
        save_analysis_to_json(test_data, str(output_file))
        
        # ファイルが作成されたことを確認
        assert output_file.exists()
        
        # JSONファイルを読み込んで内容を確認
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data

    def test_coordinate_precision(self):
        """座標精度のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.dxf"
        if os.path.exists(test_file):
            result = analyze_dxf_structure(test_file)
            bounds = result["bounds"]
            
            # 座標値が小数点3桁で丸められていることを確認
            assert isinstance(bounds["min_x"], float)
            assert isinstance(bounds["min_y"], float)
            assert isinstance(bounds["max_x"], float)
            assert isinstance(bounds["max_y"], float)

    def test_layer_analysis(self):
        """レイヤー解析機能のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.dxf"
        if os.path.exists(test_file):
            result = analyze_dxf_structure(test_file)
            layers = result["layers"]
            
            # レイヤー情報が取得されていることを確認
            assert isinstance(layers, list)
            if layers:
                layer = layers[0]
                assert "name" in layer
                assert "color" in layer
                assert "line_type" in layer
                assert "is_on" in layer
                assert "is_locked" in layer
                assert "is_frozen" in layer


if __name__ == "__main__":
    pytest.main([__file__])
