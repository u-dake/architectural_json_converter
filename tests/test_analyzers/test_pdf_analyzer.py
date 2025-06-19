"""
PDF Analyzer Tests

PDFファイル解析モジュールのテストケース
"""

import pytest
import json
from pathlib import Path
import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from analyzers.pdf_analyzer import analyze_pdf_structure, save_analysis_to_json


class TestPDFAnalyzer:
    """PDF解析モジュールのテストクラス"""

    def test_analyze_pdf_structure_basic(self):
        """基本的なPDFファイル解析のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.pdf"
        if os.path.exists(test_file):
            result = analyze_pdf_structure(test_file)
            
            # 必須フィールドの存在確認
            assert "file_info" in result
            assert "metadata" in result
            assert "pages" in result
            assert "vector_elements_summary" in result
            assert "text_elements" in result
            assert "bounds" in result
            
            # ファイル情報の検証
            assert result["file_info"]["filepath"] == test_file
            assert result["file_info"]["file_size"] > 0
            assert result["file_info"]["page_count"] > 0
            assert "pdf_version" in result["file_info"]
            
            # 境界情報の検証
            bounds = result["bounds"]
            assert "min_x" in bounds
            assert "min_y" in bounds
            assert "max_x" in bounds
            assert "max_y" in bounds
            assert bounds["width"] >= 0
            assert bounds["height"] >= 0

    def test_analyze_pdf_structure_file_not_found(self):
        """存在しないファイルに対するエラーハンドリングのテスト"""
        with pytest.raises(FileNotFoundError):
            analyze_pdf_structure("non_existent_file.pdf")

    def test_save_analysis_to_json(self, tmp_path):
        """JSON保存機能のテスト"""
        # サンプルデータ
        test_data = {
            "file_info": {"filepath": "test.pdf", "file_size": 1000, "page_count": 1},
            "metadata": {},
            "pages": [],
            "vector_elements_summary": {"path": 10},
            "text_elements": [],
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

    def test_page_analysis(self):
        """ページ解析機能のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.pdf"
        if os.path.exists(test_file):
            result = analyze_pdf_structure(test_file)
            pages = result["pages"]
            
            # ページ情報が取得されていることを確認
            assert isinstance(pages, list)
            assert len(pages) > 0
            
            page = pages[0]
            assert "page_number" in page
            assert "width" in page
            assert "height" in page
            assert "vector_elements" in page
            assert "text_elements" in page

    def test_vector_elements_extraction(self):
        """ベクター要素抽出機能のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.pdf"
        if os.path.exists(test_file):
            result = analyze_pdf_structure(test_file)
            
            # ベクター要素の統計情報を確認
            assert "vector_elements_summary" in result
            assert isinstance(result["vector_elements_summary"], dict)
            
            # ベクター要素が抽出されていることを確認
            if result["pages"]:
                page = result["pages"][0]
                assert "vector_elements" in page
                assert isinstance(page["vector_elements"], list)

    def test_text_extraction(self):
        """テキスト抽出機能のテスト"""
        # 実際のテストファイルを使用
        test_file = "250618_図面セット/01_敷地図.pdf"
        if os.path.exists(test_file):
            result = analyze_pdf_structure(test_file)
            
            # テキスト要素が抽出されていることを確認
            assert "text_elements" in result
            assert isinstance(result["text_elements"], list)
            
            # テキスト要素の構造を確認
            if result["text_elements"]:
                text = result["text_elements"][0]
                assert "text" in text
                assert "bbox" in text
                assert "font" in text
                assert "size" in text


if __name__ == "__main__":
    pytest.main([__file__])