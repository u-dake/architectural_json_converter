"""
PDF to Unified Structure Converter

PDF解析結果を統一データ構造に変換するモジュール
"""

from typing import Dict, List, Any, Optional
import uuid
import numpy as np
from src.data_structures.geometry_data import (
    GeometryData, GeometryElement, Point2D, Style, Layer,
    ElementType, ArchitecturalType,
    LineElement, PolylineElement, TextElement
)
from src.analyzers.pdf_analyzer import analyze_pdf_structure


def classify_pdf_architectural_type(element: Dict[str, Any], text_content: str = "") -> ArchitecturalType:
    """
    PDF要素から建築要素タイプを推定
    
    Args:
        element: PDF解析結果の要素
        text_content: テキスト内容（テキスト要素の場合）
        
    Returns:
        推定された建築要素タイプ
    """
    if text_content:
        text_lower = text_content.lower()
        
        # テキスト内容による分類
        if any(keyword in text_lower for keyword in ["room", "部屋", "居室", "リビング", "キッチン", "寝室"]):
            return ArchitecturalType.TEXT_LABEL
        elif any(keyword in text_lower for keyword in ["mm", "m", "寸法", "距離"]):
            return ArchitecturalType.DIMENSION_LINE
        elif any(keyword in text_lower for keyword in ["扉", "ドア", "door"]):
            return ArchitecturalType.DOOR
        elif any(keyword in text_lower for keyword in ["窓", "window", "サッシ"]):
            return ArchitecturalType.WINDOW
        else:
            return ArchitecturalType.TEXT_LABEL
    
    # パスタイプの要素の場合
    element_type = element.get("type", "")
    if element_type == "path":
        items = element.get("items", [])
        
        # パスの特徴から建築要素を推定
        if len(items) > 1:
            # 複数のアイテムがある場合は複雑な形状の可能性
            line_items = [item for item in items if item.get("type") == "line"]
            rect_items = [item for item in items if item.get("type") == "rect"]
            
            if len(line_items) > 3:  # 多数の線分は壁の可能性
                return ArchitecturalType.WALL
            elif rect_items:  # 矩形は開口部や設備の可能性
                return ArchitecturalType.FIXTURE
        elif len(items) == 1:
            item = items[0]
            item_type = item.get("type", "")
            
            if item_type == "line":
                # 単一線分の長さで判定
                p1 = item.get("p1", {})
                p2 = item.get("p2", {})
                if p1 and p2:
                    length = ((p2["x"] - p1["x"])**2 + (p2["y"] - p1["y"])**2)**0.5
                    if length > 50:  # 50ポイント以上の線分は壁の可能性
                        return ArchitecturalType.WALL
            elif item_type == "rect":
                return ArchitecturalType.FIXTURE
    
    return ArchitecturalType.UNKNOWN


def convert_pdf_path_to_elements(path_data: Dict[str, Any], element_id: str) -> List[GeometryElement]:
    """
    PDFパスデータを幾何要素に変換
    
    Args:
        path_data: PDFパス情報
        element_id: 要素ID
        
    Returns:
        変換された幾何要素のリスト
    """
    elements = []
    items = path_data.get("items", [])
    
    # スタイル情報を作成
    style = Style(
        color=path_data.get("color"),
        line_width=path_data.get("width", 1.0)
    )
    
    # 建築要素タイプを推定
    arch_type = classify_pdf_architectural_type(path_data)
    
    for i, item in enumerate(items):
        item_type = item.get("type", "")
        sub_element_id = f"{element_id}_{i}"
        
        try:
            if item_type == "line":
                p1 = item.get("p1", {})
                p2 = item.get("p2", {})
                if p1 and p2:
                    element = LineElement(
                        id=sub_element_id,
                        start=Point2D(p1["x"], p1["y"]),
                        end=Point2D(p2["x"], p2["y"]),
                        style=style,
                        architectural_type=arch_type,
                        source_info=item
                    )
                    elements.append(element)
                    
            elif item_type == "rect":
                rect = item.get("rect", {})
                if rect:
                    # 矩形を4つの線分として表現
                    x0, y0 = rect["x0"], rect["y0"]
                    x1, y1 = rect["x1"], rect["y1"]
                    
                    vertices = [
                        Point2D(x0, y0),
                        Point2D(x1, y0),
                        Point2D(x1, y1),
                        Point2D(x0, y1)
                    ]
                    
                    element = PolylineElement(
                        id=sub_element_id,
                        vertices=vertices,
                        is_closed=True,
                        style=style,
                        architectural_type=arch_type,
                        source_info=item
                    )
                    elements.append(element)
                    
            elif item_type == "curve":
                # 曲線を直線で近似
                p1 = item.get("p1", {})
                p4 = item.get("p4", {})
                if p1 and p4:
                    element = LineElement(
                        id=sub_element_id,
                        start=Point2D(p1["x"], p1["y"]),
                        end=Point2D(p4["x"], p4["y"]),
                        style=style,
                        architectural_type=arch_type,
                        source_info=item
                    )
                    elements.append(element)
                    
        except (KeyError, TypeError, ValueError) as e:
            print(f"PDFパスアイテム変換エラー ({item_type}): {e}")
            continue
    
    return elements


def convert_pdf_text_element(text_data: Dict[str, Any], element_id: str) -> Optional[TextElement]:
    """
    PDFテキストデータを統一構造に変換
    
    Args:
        text_data: PDFテキスト情報
        element_id: 要素ID
        
    Returns:
        変換されたテキスト要素、または変換不可能な場合はNone
    """
    try:
        bbox = text_data.get("bbox", {})
        text = text_data.get("text", "")
        
        if not bbox or not text.strip():
            return None
        
        # テキストの位置を左下から取得
        position = Point2D(bbox["x0"], bbox["y0"])
        
        # テキストの高さを計算
        height = bbox["y1"] - bbox["y0"]
        
        # スタイル情報
        style = Style(
            color=text_data.get("color"),
            layer="TEXT"
        )
        
        # 建築要素タイプを推定
        arch_type = classify_pdf_architectural_type(text_data, text)
        
        return TextElement(
            id=element_id,
            position=position,
            text=text,
            height=height,
            font=text_data.get("font", ""),
            style=style,
            architectural_type=arch_type,
            source_info=text_data
        )
        
    except (KeyError, TypeError, ValueError) as e:
        print(f"PDFテキスト変換エラー: {e}")
        return None


def convert_pdf_to_geometry_data(pdf_filepath: str) -> GeometryData:
    """
    PDFファイルを解析して統一データ構造に変換
    
    Args:
        pdf_filepath: PDFファイルのパス
        
    Returns:
        統一データ構造のGeometryData
        
    Raises:
        FileNotFoundError: ファイルが見つからない場合
        Exception: 解析・変換エラー
    """
    # PDFファイルを解析
    analysis_result = analyze_pdf_structure(pdf_filepath)
    
    # デフォルトレイヤーを作成（PDFにはレイヤー概念がないため）
    layers = [
        Layer(name="GRAPHICS", color=0),
        Layer(name="TEXT", color=7)
    ]
    
    # 要素を変換
    elements = []
    element_counter = 0
    
    # 各ページの要素を処理
    for page_info in analysis_result.get("pages", []):
        page_num = page_info.get("page_number", 1)
        
        # ベクター要素を変換
        for vector_element in page_info.get("vector_elements", []):
            element_id = f"pdf_vector_{page_num}_{element_counter}"
            converted_elements = convert_pdf_path_to_elements(vector_element, element_id)
            elements.extend(converted_elements)
            element_counter += 1
        
        # テキスト要素を変換
        for text_element in page_info.get("text_elements", []):
            element_id = f"pdf_text_{page_num}_{element_counter}"
            converted_element = convert_pdf_text_element(text_element, element_id)
            if converted_element:
                elements.append(converted_element)
            element_counter += 1
    
    # メタデータを準備
    metadata = {
        "original_analysis": analysis_result,
        "pdf_version": analysis_result.get("file_info", {}).get("pdf_version"),
        "file_size": analysis_result.get("file_info", {}).get("file_size"),
        "page_count": analysis_result.get("file_info", {}).get("page_count"),
        "bounds": analysis_result.get("bounds"),
        "vector_elements_summary": analysis_result.get("vector_elements_summary"),
        "conversion_stats": {
            "total_pages": len(analysis_result.get("pages", [])),
            "converted_elements": len(elements),
            "text_elements": len([e for e in elements if isinstance(e, TextElement)]),
            "vector_elements": len([e for e in elements if not isinstance(e, TextElement)])
        }
    }
    
    return GeometryData(
        source_file=pdf_filepath,
        source_type="pdf",
        layers=layers,
        elements=elements,
        metadata=metadata
    )


def analyze_pdf_architectural_elements(geometry_data: GeometryData) -> Dict[str, List[GeometryElement]]:
    """
    PDF由来の要素を建築要素別に分析
    
    Args:
        geometry_data: 統一データ構造
        
    Returns:
        建築要素タイプ別の要素リスト
    """
    result = {
        "walls": [],
        "openings": [],
        "fixtures": [],
        "text_labels": [],
        "dimension_lines": [],
        "unknown": []
    }
    
    for element in geometry_data.elements:
        if element.architectural_type == ArchitecturalType.WALL:
            result["walls"].append(element)
        elif element.architectural_type in [ArchitecturalType.DOOR, ArchitecturalType.WINDOW, ArchitecturalType.OPENING]:
            result["openings"].append(element)
        elif element.architectural_type == ArchitecturalType.FIXTURE:
            result["fixtures"].append(element)
        elif element.architectural_type == ArchitecturalType.TEXT_LABEL:
            result["text_labels"].append(element)
        elif element.architectural_type == ArchitecturalType.DIMENSION_LINE:
            result["dimension_lines"].append(element)
        else:
            result["unknown"].append(element)
    
    return result


def save_geometry_data_to_json(geometry_data: GeometryData, output_path: str) -> None:
    """
    統一データ構造をJSONファイルに保存
    
    Args:
        geometry_data: 統一データ構造
        output_path: 出力ファイルパス
    """
    import json
    import os
    
    # ディレクトリが存在しない場合は作成
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Pydanticモデルの辞書化（JSON互換形式）
    data_dict = geometry_data.model_dump(mode='json')
    
    # JSON形式で保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2)
    
    print(f"統一データ構造を保存しました: {output_path}")


def main():
    """テスト用メイン関数"""
    import sys
    import os
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        
        try:
            print(f"PDFファイルを統一構造に変換中: {pdf_path}")
            geometry_data = convert_pdf_to_geometry_data(pdf_path)
            
            # 出力ファイル名を生成
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = f"data/geometry_{base_name}.json"
            
            save_geometry_data_to_json(geometry_data, output_path)
            
            # 変換結果サマリーを表示
            print("\n=== 変換結果サマリー ===")
            print(f"元ファイル: {geometry_data.source_file}")
            print(f"要素数: {len(geometry_data.elements)}")
            print(f"レイヤー数: {len(geometry_data.layers)}")
            
            # 建築要素別の統計
            arch_analysis = analyze_pdf_architectural_elements(geometry_data)
            print("\n建築要素別統計:")
            for category, elements in arch_analysis.items():
                if elements:
                    print(f"  {category}: {len(elements)}")
                    
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("使用方法: python pdf_converter.py <PDFファイルパス>")


if __name__ == "__main__":
    main()