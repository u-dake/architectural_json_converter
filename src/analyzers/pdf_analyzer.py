"""
PDF File Analyzer Module

このモジュールはベクターPDFファイルの構造を詳細に解析し、
JSON形式で構造化された情報を出力します。

開発チームへ:
1. PyMuPDF (fitz) を使用してPDFファイルを解析
2. ベクター図形（線分、曲線等）を抽出
3. テキスト情報を座標と共に記録
4. 座標系の正規化に注意
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import fitz  # PyMuPDF
from pathlib import Path
import os


def analyze_pdf_structure(filepath: str) -> Dict[str, Any]:
    """
    PDFファイルのベクター要素を詳細に解析

    Args:
        filepath: PDFファイルのパス

    Returns:
        PDFファイルの構造情報を含む辞書

    Raises:
        FileNotFoundError: ファイルが見つからない場合
        fitz.FileDataError: PDFファイルの読み込みエラー
    """
    # ファイルの存在確認
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PDFファイルが見つかりません: {filepath}")

    # ファイルサイズ取得
    file_size = os.path.getsize(filepath)

    # PDFファイル読み込み
    try:
        doc = fitz.open(filepath)
    except Exception as e:
        raise fitz.FileDataError(f"PDFファイルの読み込みエラー: {e}")

    # PDFメタデータ取得
    metadata = doc.metadata
    pdf_version = metadata.get("format", "Unknown")

    # 全体の境界情報を計算するための変数
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")

    # ベクター要素の統計情報
    vector_elements_summary = {}
    all_text_elements = []
    pages_info = []

    # 各ページを解析
    for page_num, page in enumerate(doc):
        page_info = {
            "page_number": page_num + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "rotation": page.rotation,
            "vector_elements": [],
            "text_elements": [],
        }

        # ベクター図形を抽出
        drawings = extract_drawings_from_page(page)
        for drawing in drawings:
            # 統計情報を更新
            draw_type = drawing.get("type", "unknown")
            if draw_type not in vector_elements_summary:
                vector_elements_summary[draw_type] = 0
            vector_elements_summary[draw_type] += 1

            # 境界情報を更新
            if "points" in drawing:
                for point in drawing["points"]:
                    min_x = min(min_x, point["x"])
                    min_y = min(min_y, point["y"])
                    max_x = max(max_x, point["x"])
                    max_y = max(max_y, point["y"])
            elif "rect" in drawing:
                rect = drawing["rect"]
                min_x = min(min_x, rect["x0"], rect["x1"])
                min_y = min(min_y, rect["y0"], rect["y1"])
                max_x = max(max_x, rect["x0"], rect["x1"])
                max_y = max(max_y, rect["y0"], rect["y1"])

        page_info["vector_elements"] = drawings

        # テキスト情報を抽出
        text_elements = extract_text_from_page(page)
        page_info["text_elements"] = text_elements
        all_text_elements.extend(text_elements)

        # テキストの境界情報を更新
        for text in text_elements:
            if "bbox" in text:
                bbox = text["bbox"]
                min_x = min(min_x, bbox["x0"])
                min_y = min(min_y, bbox["y0"])
                max_x = max(max_x, bbox["x1"])
                max_y = max(max_y, bbox["y1"])

        pages_info.append(page_info)

    # 境界情報が無限大の場合は0に設定
    if min_x == float("inf"):
        min_x = min_y = max_x = max_y = 0.0

    # 座標系を正規化（PDF座標系から標準座標系へ）
    # PDFは左下原点なので、必要に応じて変換

    analysis_result = {
        "file_info": {
            "filepath": filepath,
            "file_size": file_size,
            "page_count": len(doc),
            "pdf_version": pdf_version,
        },
        "metadata": metadata,
        "pages": pages_info,
        "vector_elements_summary": vector_elements_summary,
        "text_elements": all_text_elements,
        "bounds": {
            "min_x": round(min_x, 3),
            "min_y": round(min_y, 3),
            "max_x": round(max_x, 3),
            "max_y": round(max_y, 3),
            "width": round(max_x - min_x, 3),
            "height": round(max_y - min_y, 3),
        },
    }

    doc.close()
    return analysis_result


def extract_drawings_from_page(page: fitz.Page) -> List[Dict[str, Any]]:
    """
    ページからベクター図形を抽出

    Args:
        page: fitz.Pageオブジェクト

    Returns:
        ベクター図形のリスト
    """
    drawings = []

    try:
        # ページからベクター要素を取得
        paths = page.get_drawings()

        for path in paths:
            drawing = {
                "type": "path",
                "color": path.get("color", None),
                "fill": path.get("fill", None),
                "width": path.get("width", 1.0),
                "closePath": path.get("closePath", False),
                "items": [],
            }

            # パスの各セグメントを解析
            for item in path.get("items", []):
                item_type = item[0]

                if item_type == "l":  # Line
                    drawing["items"].append(
                        {
                            "type": "line",
                            "p1": {"x": item[1].x, "y": item[1].y},
                            "p2": {"x": item[2].x, "y": item[2].y},
                        }
                    )
                elif item_type == "c":  # Curve
                    drawing["items"].append(
                        {
                            "type": "curve",
                            "p1": {"x": item[1].x, "y": item[1].y},
                            "p2": {"x": item[2].x, "y": item[2].y},
                            "p3": {"x": item[3].x, "y": item[3].y},
                            "p4": {"x": item[4].x, "y": item[4].y},
                        }
                    )
                elif item_type == "re":  # Rectangle
                    drawing["items"].append(
                        {
                            "type": "rect",
                            "rect": {
                                "x0": item[1].x,
                                "y0": item[1].y,
                                "x1": item[1].x + item[2].x,
                                "y1": item[1].y + item[2].y,
                            },
                        }
                    )

            # 全体の境界ボックスを計算
            if drawing["items"]:
                points = []
                for item in drawing["items"]:
                    if item["type"] == "line":
                        points.append(item["p1"])
                        points.append(item["p2"])
                    elif item["type"] == "curve":
                        points.append(item["p1"])
                        points.append(item["p4"])
                    elif item["type"] == "rect":
                        rect = item["rect"]
                        points.append({"x": rect["x0"], "y": rect["y0"]})
                        points.append({"x": rect["x1"], "y": rect["y1"]})

                drawing["points"] = points

            drawings.append(drawing)
    except Exception as e:
        # エラーが発生した場合は空のリストを返す
        print(f"ベクター図形の抽出エラー: {e}")

    return drawings


def extract_text_from_page(page: fitz.Page) -> List[Dict[str, Any]]:
    """
    ページからテキスト情報を座標と共に抽出

    Args:
        page: fitz.Pageオブジェクト

    Returns:
        テキスト要素のリスト
    """
    text_elements = []

    try:
        # ページからテキスト情報を辞書形式で取得
        text_dict = page.get_text("dict")

        # ブロック単位でテキストを処理
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # テキストブロック
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_element = {
                            "text": span.get("text", ""),
                            "font": span.get("font", ""),
                            "size": span.get("size", 0),
                            "flags": span.get("flags", 0),
                            "color": span.get("color", 0),
                            "bbox": {
                                "x0": span["bbox"][0],
                                "y0": span["bbox"][1],
                                "x1": span["bbox"][2],
                                "y1": span["bbox"][3],
                            },
                        }

                        # 空白文字のみのテキストは除外
                        if text_element["text"].strip():
                            text_elements.append(text_element)
    except Exception as e:
        # エラーが発生した場合は空のリストを返す
        print(f"テキスト抽出エラー: {e}")

    return text_elements


def normalize_coordinates(
    elements: List[Dict[str, Any]], page_bounds: Tuple[float, float, float, float]
) -> List[Dict[str, Any]]:
    """
    座標系を正規化（PDFの座標系→標準座標系）

    Args:
        elements: 図形要素のリスト
        page_bounds: ページの境界（x0, y0, x1, y1）

    Returns:
        正規化された要素のリスト
    """
    # PDFの座標系は左下原点なので、Y座標を反転させて左上原点に変換
    page_height = page_bounds[3] - page_bounds[1]

    normalized_elements = []
    for element in elements:
        normalized = element.copy()

        # 座標を含むフィールドを変換
        if "bbox" in element:
            bbox = element["bbox"]
            normalized["bbox"] = {
                "x0": bbox["x0"],
                "y0": page_height - bbox["y1"],
                "x1": bbox["x1"],
                "y1": page_height - bbox["y0"],
            }

        if "points" in element:
            normalized["points"] = []
            for point in element["points"]:
                normalized["points"].append(
                    {"x": point["x"], "y": page_height - point["y"]}
                )

        normalized_elements.append(normalized)

    return normalized_elements


def save_analysis_to_json(analysis_result: Dict[str, Any], output_path: str) -> None:
    """
    解析結果をJSONファイルに保存

    Args:
        analysis_result: analyze_pdf_structure()の戻り値
        output_path: 出力JSONファイルのパス
    """
    # ディレクトリが存在しない場合は作成
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # JSON形式で保存（日本語対応、インデント付き）
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    print(f"解析結果を保存しました: {output_path}")


def main():
    """
    テスト用メイン関数
    開発チームは実際のPDFファイルでテストしてください
    """
    import sys

    if len(sys.argv) > 1:
        # コマンドライン引数からファイルパスを取得
        pdf_path = sys.argv[1]

        try:
            print(f"PDFファイルを解析中: {pdf_path}")
            analysis = analyze_pdf_structure(pdf_path)

            # 出力ファイル名を生成
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = f"data/pdf_analysis_{base_name}.json"

            save_analysis_to_json(analysis, output_path)

            # サマリー情報を表示
            print("\n=== 解析結果サマリー ===")
            print(f"PDFバージョン: {analysis['file_info']['pdf_version']}")
            print(f"ファイルサイズ: {analysis['file_info']['file_size']:,} bytes")
            print(f"ページ数: {analysis['file_info']['page_count']}")
            print(f"テキスト要素数: {len(analysis['text_elements'])}")
            print("\nベクター要素種別:")
            for element_type, count in sorted(
                analysis["vector_elements_summary"].items()
            ):
                print(f"  {element_type}: {count}")
            print(f"\n図面境界:")
            bounds = analysis["bounds"]
            print(f"  X: {bounds['min_x']} ~ {bounds['max_x']} (幅: {bounds['width']})")
            print(
                f"  Y: {bounds['min_y']} ~ {bounds['max_y']} (高さ: {bounds['height']})"
            )

        except FileNotFoundError as e:
            print(f"エラー: {e}")
        except Exception as e:
            print(f"予期しないエラー: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("使用方法: python pdf_analyzer.py <PDFファイルパス>")
        print("例: python pdf_analyzer.py data/sample_pdf/test.pdf")


if __name__ == "__main__":
    main()
