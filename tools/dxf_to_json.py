#!/usr/bin/env python3
"""
DXF→JSON変換ツール

DXFファイルの内容をJSON形式で出力する
"""

import sys
import os
from pathlib import Path
import json
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engines.safe_dxf_converter import SafeDXFConverter
from src.analyzers.dxf_analyzer import analyze_dxf_structure


def convert_element_to_dict(element) -> Dict[str, Any]:
    """ジオメトリ要素を辞書形式に変換"""
    element_dict = {
        "type": element.__class__.__name__,
    }
    
    # レイヤー情報
    if hasattr(element, 'layer'):
        element_dict["layer"] = element.layer
    
    # 要素タイプ別の詳細情報
    if hasattr(element, 'start') and hasattr(element, 'end'):
        # Line
        element_dict["start"] = {"x": element.start.x, "y": element.start.y}
        element_dict["end"] = {"x": element.end.x, "y": element.end.y}
    
    elif hasattr(element, 'center') and hasattr(element, 'radius'):
        # Circle or Arc
        element_dict["center"] = {"x": element.center.x, "y": element.center.y}
        element_dict["radius"] = element.radius
        if hasattr(element, 'start_angle'):
            element_dict["start_angle"] = element.start_angle
            element_dict["end_angle"] = element.end_angle
    
    elif hasattr(element, 'points'):
        # Polyline
        element_dict["points"] = [{"x": p.x, "y": p.y} for p in element.points]
        if hasattr(element, 'closed'):
            element_dict["closed"] = element.closed
    
    elif hasattr(element, 'position') and hasattr(element, 'content'):
        # Text
        element_dict["position"] = {"x": element.position.x, "y": element.position.y}
        element_dict["content"] = element.content
        if hasattr(element, 'height'):
            element_dict["height"] = element.height
        if hasattr(element, 'rotation'):
            element_dict["rotation"] = element.rotation
    
    return element_dict


def dxf_to_json(dxf_file: str, output_json: str = None, include_structure: bool = True, include_elements: bool = True):
    """DXFファイルをJSONに変換
    
    Args:
        dxf_file: 入力DXFファイル
        output_json: 出力JSONファイル（省略時は自動生成）
        include_structure: DXF構造解析を含めるか
        include_elements: 個別要素の詳細を含めるか
    """
    print(f"DXFファイルを読み込み中: {dxf_file}")
    
    # 出力ファイル名の生成
    if output_json is None:
        output_json = Path(dxf_file).with_suffix('.json')
    
    # 基本情報
    data = {
        "file_info": {
            "source_file": str(Path(dxf_file).absolute()),
            "file_name": Path(dxf_file).name,
            "file_size": os.path.getsize(dxf_file),
            "conversion_type": "dxf_to_json"
        }
    }
    
    # DXF構造解析（詳細情報）
    if include_structure:
        try:
            print("DXF構造を解析中...")
            structure = analyze_dxf_structure(dxf_file)
            data["dxf_structure"] = structure
        except Exception as e:
            print(f"警告: DXF構造解析でエラー: {e}")
            data["dxf_structure"] = {"error": str(e)}
    
    # SafeDXFConverterで要素を抽出
    if include_elements:
        try:
            print("ジオメトリ要素を抽出中...")
            converter = SafeDXFConverter()
            geometry = converter.convert_dxf_file(dxf_file, include_paperspace=True)
            
            # ジオメトリ情報
            data["geometry"] = {
                "element_count": len(geometry.elements),
                "metadata": geometry.metadata,
                "elements": []
            }
            
            # 要素の詳細（大きなファイルの場合は制限）
            max_elements = 10000  # 最大要素数
            element_count = min(len(geometry.elements), max_elements)
            
            for i, element in enumerate(geometry.elements[:element_count]):
                element_dict = convert_element_to_dict(element)
                element_dict["index"] = i
                data["geometry"]["elements"].append(element_dict)
            
            if len(geometry.elements) > max_elements:
                data["geometry"]["truncated"] = True
                data["geometry"]["truncated_message"] = f"要素数が多いため、最初の{max_elements}個のみを出力しました"
            
            print(f"  抽出された要素数: {len(geometry.elements)}")
            
        except Exception as e:
            print(f"警告: ジオメトリ抽出でエラー: {e}")
            data["geometry"] = {"error": str(e)}
    
    # JSONファイルに保存
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSONファイルを生成しました: {output_json}")
    
    # サマリー表示
    if "dxf_structure" in data and "bounds" in data["dxf_structure"]:
        bounds = data["dxf_structure"]["bounds"]
        print(f"\n図面境界:")
        print(f"  X: {bounds['min_x']:.2f} ~ {bounds['max_x']:.2f} (幅: {bounds['width']:.2f}mm)")
        print(f"  Y: {bounds['min_y']:.2f} ~ {bounds['max_y']:.2f} (高さ: {bounds['height']:.2f}mm)")
    
    if "geometry" in data and "element_count" in data["geometry"]:
        print(f"\n要素数: {data['geometry']['element_count']}")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DXFファイルをJSON形式に変換')
    parser.add_argument('dxf_file', help='入力DXFファイル')
    parser.add_argument('-o', '--output', help='出力JSONファイル（省略時は同名.json）')
    parser.add_argument('--no-structure', action='store_true', 
                       help='DXF構造解析をスキップ')
    parser.add_argument('--no-elements', action='store_true',
                       help='要素詳細の出力をスキップ')
    
    args = parser.parse_args()
    
    dxf_to_json(
        args.dxf_file,
        args.output,
        include_structure=not args.no_structure,
        include_elements=not args.no_elements
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())