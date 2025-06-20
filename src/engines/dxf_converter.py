"""
DXF to Unified Structure Converter

DXF解析結果を統一データ構造に変換するモジュール
"""

from typing import Dict, List, Any, Optional
import uuid
import os
from data_structures.geometry_data import (
    GeometryData, GeometryElement, Point2D, Style, Layer,
    ElementType, ArchitecturalType,
    LineElement, CircleElement, ArcElement, PolylineElement,
    TextElement, BlockElement
)
from analyzers.dxf_analyzer import analyze_dxf_structure


def classify_architectural_type(element: Dict[str, Any], layer_name: str) -> ArchitecturalType:
    """
    エンティティとレイヤー情報から建築要素タイプを推定
    
    Args:
        element: DXF解析結果のエンティティ
        layer_name: レイヤー名
        
    Returns:
        推定された建築要素タイプ
    """
    layer_lower = layer_name.lower()
    element_type = element.get("type", "").lower()
    
    # レイヤー名による分類
    if any(wall_pattern in layer_lower for wall_pattern in ["wall", "壁", "w-", "w_"]):
        return ArchitecturalType.WALL
    elif any(dim_pattern in layer_lower for dim_pattern in ["dim", "寸法", "d-", "d_"]):
        return ArchitecturalType.DIMENSION_LINE
    elif any(door_pattern in layer_lower for door_pattern in ["door", "扉", "ドア"]):
        return ArchitecturalType.DOOR
    elif any(window_pattern in layer_lower for window_pattern in ["window", "窓", "サッシ"]):
        return ArchitecturalType.WINDOW
    elif any(fixture_pattern in layer_lower for fixture_pattern in ["fixture", "設備", "fix"]):
        return ArchitecturalType.FIXTURE
    
    # エンティティタイプによる分類
    if element_type in ["text", "mtext"]:
        return ArchitecturalType.TEXT_LABEL
    elif element_type == "dimension":
        return ArchitecturalType.DIMENSION_LINE
    elif element_type == "line":
        # 線分の長さや角度で分類を試行
        if "length" in element:
            length = element["length"]
            if length > 500:  # 500mm以上の線分は壁の可能性
                return ArchitecturalType.WALL
    
    return ArchitecturalType.UNKNOWN


def convert_dxf_layer(layer_info: Dict[str, Any]) -> Layer:
    """DXFレイヤー情報を統一構造に変換"""
    return Layer(
        name=layer_info["name"],
        color=layer_info.get("color", 7),
        line_type=layer_info.get("line_type", "CONTINUOUS"),
        is_visible=layer_info.get("is_on", True),
        is_locked=layer_info.get("is_locked", False),
        is_frozen=layer_info.get("is_frozen", False)
    )


def convert_dxf_element(element: Dict[str, Any]) -> Optional[GeometryElement]:
    """
    DXFエンティティを統一構造の幾何要素に変換
    
    Args:
        element: DXF解析結果のエンティティ
        
    Returns:
        変換された幾何要素、または変換不可能な場合はNone
    """
    element_type = element.get("type", "").upper()
    element_id = str(uuid.uuid4())
    layer_name = element.get("layer", "0")
    
    # スタイル情報を作成
    style = Style(
        color=element.get("color"),
        layer=layer_name
    )
    
    # 建築要素タイプを推定
    arch_type = classify_architectural_type(element, layer_name)
    
    # 共通パラメータ
    common_params = {
        "id": element_id,
        "style": style,
        "architectural_type": arch_type,
        "source_info": element
    }
    
    try:
        if element_type == "LINE":
            start_data = element.get("start", {})
            end_data = element.get("end", {})
            return LineElement(
                start=Point2D(start_data["x"], start_data["y"]),
                end=Point2D(end_data["x"], end_data["y"]),
                **common_params
            )
            
        elif element_type == "CIRCLE":
            center_data = element.get("center", {})
            radius = element.get("radius", 0)
            return CircleElement(
                center=Point2D(center_data["x"], center_data["y"]),
                radius=radius,
                **common_params
            )
            
        elif element_type == "ARC":
            center_data = element.get("center", {})
            radius = element.get("radius", 0)
            start_angle = element.get("start_angle", 0)
            end_angle = element.get("end_angle", 0)
            return ArcElement(
                center=Point2D(center_data["x"], center_data["y"]),
                radius=radius,
                start_angle=start_angle,
                end_angle=end_angle,
                **common_params
            )
            
        elif element_type in ["POLYLINE", "LWPOLYLINE"]:
            vertices_data = element.get("vertices", [])
            vertices = [Point2D(v["x"], v["y"]) for v in vertices_data]
            is_closed = element.get("is_closed", False)
            return PolylineElement(
                vertices=vertices,
                is_closed=is_closed,
                **common_params
            )
            
        elif element_type in ["TEXT", "MTEXT"]:
            insert_data = element.get("insert", {})
            text = element.get("text", "")
            height = element.get("height", element.get("char_height", 0))
            rotation = element.get("rotation", 0)
            return TextElement(
                position=Point2D(insert_data["x"], insert_data["y"]),
                text=text,
                height=height,
                rotation=rotation,
                **common_params
            )
            
        elif element_type == "INSERT":
            insert_data = element.get("insert", {})
            block_name = element.get("block_name", "")
            scale_x = element.get("xscale", 1.0)
            scale_y = element.get("yscale", 1.0)
            rotation = element.get("rotation", 0)
            return BlockElement(
                position=Point2D(insert_data["x"], insert_data["y"]),
                block_name=block_name,
                scale_x=scale_x,
                scale_y=scale_y,
                rotation=rotation,
                **common_params
            )
            
        else:
            # 未対応のエンティティタイプ
            return None
            
    except (KeyError, TypeError, ValueError) as e:
        print(f"エンティティ変換エラー ({element_type}): {e}")
        return None


def convert_dxf_to_geometry_data(dxf_filepath: str) -> GeometryData:
    """
    DXFファイルを解析して統一データ構造に変換
    
    Args:
        dxf_filepath: DXFファイルのパス
        
    Returns:
        統一データ構造のGeometryData
        
    Raises:
        FileNotFoundError: ファイルが見つからない場合
        Exception: 解析・変換エラー
    """
    # DXFファイルを解析
    analysis_result = analyze_dxf_structure(dxf_filepath)
    
    # レイヤー情報を変換
    layers = []
    for layer_info in analysis_result.get("layers", []):
        layers.append(convert_dxf_layer(layer_info))
    
    # エンティティを変換
    elements = []
    for element_data in analysis_result.get("entities_detail", []):
        converted_element = convert_dxf_element(element_data)
        if converted_element:
            elements.append(converted_element)
    
    # メタデータを準備
    metadata = {
        "original_analysis": analysis_result,
        "dxf_version": analysis_result.get("file_info", {}).get("dxf_version"),
        "file_size": analysis_result.get("file_info", {}).get("file_size"),
        "bounds": analysis_result.get("bounds"),
        "entities_summary": analysis_result.get("entities_summary"),
        "conversion_stats": {
            "original_entities": len(analysis_result.get("entities_detail", [])),
            "converted_elements": len(elements),
            "layers": len(layers)
        }
    }
    
    return GeometryData(
        source_file=dxf_filepath,
        source_type="dxf",
        layers=layers,
        elements=elements,
        metadata=metadata
    )


def analyze_dxf_architectural_elements(geometry_data: GeometryData) -> Dict[str, List[GeometryElement]]:
    """
    DXF由来の要素を建築要素別に分析
    
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
    
    if len(sys.argv) > 1:
        dxf_path = sys.argv[1]
        
        try:
            print(f"DXFファイルを統一構造に変換中: {dxf_path}")
            geometry_data = convert_dxf_to_geometry_data(dxf_path)
            
            # 出力ファイル名を生成
            base_name = os.path.splitext(os.path.basename(dxf_path))[0]
            output_path = f"data/geometry_{base_name}.json"
            
            save_geometry_data_to_json(geometry_data, output_path)
            
            # 変換結果サマリーを表示
            print("\n=== 変換結果サマリー ===")
            print(f"元ファイル: {geometry_data.source_file}")
            print(f"要素数: {len(geometry_data.elements)}")
            print(f"レイヤー数: {len(geometry_data.layers)}")
            
            # 建築要素別の統計
            arch_analysis = analyze_dxf_architectural_elements(geometry_data)
            print("\n建築要素別統計:")
            for category, elements in arch_analysis.items():
                if elements:
                    print(f"  {category}: {len(elements)}")
                    
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("使用方法: python dxf_converter.py <DXFファイルパス>")


if __name__ == "__main__":
    main()