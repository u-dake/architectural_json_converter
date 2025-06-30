#!/usr/bin/env python3
"""
改良版DXF差分視覚化ツール

SafeDXFConverterを使用してDXFファイルを正しく読み込み、差分を視覚化する
"""

import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import re
from typing import List, Tuple, Dict, Any
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engines.safe_dxf_converter import SafeDXFConverter
from src.data_structures.simple_geometry import (
    Point, Line, Circle, Arc, Polyline, Text, GeometryCollection
)
from src.visualization.geometry_plotter import GeometryPlotter, PlotStyle


# 共通プロッターのインスタンスを作成
plotter = GeometryPlotter()


def find_file_pairs(directory: str) -> List[Tuple[str, str]]:
    """ディレクトリから対応するファイルペアを検出"""
    pairs = []
    
    # 新しいディレクトリ構造に対応
    buildings_dir = Path(directory) / 'buildings'
    if buildings_dir.exists():
        for building_dir in sorted(buildings_dir.iterdir()):
            if building_dir.is_dir():
                site_plan_dir = building_dir / 'site_plan'
                floor_plan_dir = building_dir / 'floor_plan'
                
                if site_plan_dir.exists() and floor_plan_dir.exists():
                    site_files = list(site_plan_dir.glob('*.dxf'))
                    floor_files = list(floor_plan_dir.glob('*.dxf'))
                    
                    if site_files and floor_files:
                        pairs.append((str(site_files[0]), str(floor_files[0])))
    
    return sorted(pairs)


def get_geometry_bounds(geometry: GeometryCollection) -> Tuple[float, float, float, float]:
    """GeometryCollectionの境界を計算"""
    xlim, ylim = plotter.calculate_bounds(geometry, margin_ratio=0.0)
    return xlim[0], ylim[0], xlim[1], ylim[1]


def visualize_difference(site_file: str, floor_file: str, output_pdf: str, output_json: bool = True):
    """2つのDXFファイルの差分を視覚化
    
    Args:
        site_file: サイトプランのDXFファイル
        floor_file: フロアプランのDXFファイル
        output_pdf: 出力PDFファイルパス
        output_json: JSON形式でも出力するか（デフォルト: True）
    """
    print(f"サイトプラン: {site_file}")
    print(f"フロアプラン: {floor_file}")
    
    # SafeDXFConverterを使用してDXFファイルを読み込む
    converter = SafeDXFConverter()
    
    try:
        # サイトプランを読み込む
        site_geometry = converter.convert_dxf_file(site_file, include_paperspace=True)
        print(f"  サイト要素数: {len(site_geometry.elements)}")
        
        # フロアプランを読み込む
        floor_geometry = converter.convert_dxf_file(floor_file, include_paperspace=True)
        print(f"  フロア要素数: {len(floor_geometry.elements)}")
    except Exception as e:
        print(f"エラー: DXFファイルの読み込みに失敗しました: {e}")
        return
    
    # 両方のジオメトリから境界を計算
    site_bounds = get_geometry_bounds(site_geometry)
    floor_bounds = get_geometry_bounds(floor_geometry)
    
    # 統合境界を計算
    min_x = min(site_bounds[0], floor_bounds[0])
    min_y = min(site_bounds[1], floor_bounds[1])
    max_x = max(site_bounds[2], floor_bounds[2])
    max_y = max(site_bounds[3], floor_bounds[3])
    
    # マージンを追加
    width = max_x - min_x
    height = max_y - min_y
    margin = max(width, height) * 0.05
    
    xlim = (min_x - margin, max_x + margin)
    ylim = (min_y - margin, max_y + margin)
    
    # PDF作成
    with PdfPages(output_pdf) as pdf:
        # 4つのビューを作成
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 共通の軸設定
        for ax in [ax1, ax2, ax3, ax4]:
            plotter.setup_axis(ax, xlim, ylim)
        
        # 1. サイトプランのみ
        ax1.set_title('サイトプラン（敷地図）', fontsize=14, fontweight='bold')
        plotter.plot_collection(ax1, site_geometry, PlotStyle(color='blue', alpha=0.8))
        
        # 2. フロアプランのみ
        ax2.set_title('フロアプラン（完成形）', fontsize=14, fontweight='bold')
        plotter.plot_collection(ax2, floor_geometry, PlotStyle(color='red', alpha=0.8))
        
        # 3. 重ね合わせ
        ax3.set_title('重ね合わせ表示', fontsize=14, fontweight='bold')
        plotter.plot_collection(ax3, site_geometry, PlotStyle(color='blue', alpha=0.5))
        plotter.plot_collection(ax3, floor_geometry, PlotStyle(color='red', alpha=0.5))
        
        # 凡例を追加
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='blue', lw=2, label='サイトプラン'),
            Line2D([0], [0], color='red', lw=2, label='フロアプラン')
        ]
        ax3.legend(handles=legend_elements, loc='upper right')
        
        # 4. 差分強調表示
        ax4.set_title('差分強調表示', fontsize=14, fontweight='bold')
        # サイトを薄く表示
        plotter.plot_collection(ax4, site_geometry, PlotStyle(color='lightblue', alpha=0.3))
        # フロアプランの新規要素を強調
        plotter.plot_collection(ax4, floor_geometry, PlotStyle(color='darkred', alpha=1.0))
        
        # 統計情報を追加
        info_text = f"サイト要素数: {len(site_geometry.elements)}\n"
        info_text += f"フロア要素数: {len(floor_geometry.elements)}\n"
        info_text += f"描画範囲: {width:.1f} × {height:.1f} mm"
        ax4.text(0.02, 0.98, info_text, transform=ax4.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 全体タイトル
        building_num = Path(site_file).parent.parent.name
        fig.suptitle(f'建物 {building_num} - DXF差分解析', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    print(f"PDFを生成しました: {output_pdf}")
    
    # JSON形式でも出力
    if output_json:
        import json
        
        # JSONファイル名を生成
        json_path = Path(output_pdf).with_suffix('.json')
        
        # データを辞書形式に変換
        data = {
            "analysis_type": "dxf_difference",
            "files": {
                "site_plan": site_file,
                "floor_plan": floor_file
            },
            "site_geometry": {
                "element_count": len(site_geometry.elements),
                "bounds": {
                    "min_x": site_bounds[0],
                    "min_y": site_bounds[1],
                    "max_x": site_bounds[2],
                    "max_y": site_bounds[3]
                },
                "elements": []  # 要素の詳細（オプション）
            },
            "floor_geometry": {
                "element_count": len(floor_geometry.elements),
                "bounds": {
                    "min_x": floor_bounds[0],
                    "min_y": floor_bounds[1],
                    "max_x": floor_bounds[2],
                    "max_y": floor_bounds[3]
                },
                "elements": []  # 要素の詳細（オプション）
            },
            "statistics": {
                "site_elements": len(site_geometry.elements),
                "floor_elements": len(floor_geometry.elements),
                "difference": len(floor_geometry.elements) - len(site_geometry.elements),
                "drawing_width": width,
                "drawing_height": height
            }
        }
        
        # 要素の詳細を追加（サイズが大きくなりすぎないよう制限）
        max_elements_detail = 100  # 詳細を記録する最大要素数
        
        # サイトプランの要素詳細
        for i, element in enumerate(site_geometry.elements[:max_elements_detail]):
            element_data = {
                "type": element.__class__.__name__,
                "index": i
            }
            if hasattr(element, 'layer'):
                element_data["layer"] = element.layer
            data["site_geometry"]["elements"].append(element_data)
        
        # フロアプランの要素詳細
        for i, element in enumerate(floor_geometry.elements[:max_elements_detail]):
            element_data = {
                "type": element.__class__.__name__,
                "index": i
            }
            if hasattr(element, 'layer'):
                element_data["layer"] = element.layer
            data["floor_geometry"]["elements"].append(element_data)
        
        # JSONファイルに保存
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"JSONデータを生成しました: {json_path}")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='改良版DXFファイルの差分視覚化')
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    # diffコマンド
    diff_parser = subparsers.add_parser('diff', help='2つのDXFファイルの差分を視覚化')
    diff_parser.add_argument('site_file', help='サイトプランのDXFファイル')
    diff_parser.add_argument('floor_file', help='フロアプランのDXFファイル')
    diff_parser.add_argument('-o', '--output', help='出力PDFファイル名')
    diff_parser.add_argument('--no-json', action='store_true', help='JSON出力をスキップ')
    
    # batchコマンド
    batch_parser = subparsers.add_parser('batch', help='ディレクトリ内のファイルペアを一括処理')
    batch_parser.add_argument('directory', help='DXFファイルのディレクトリ')
    batch_parser.add_argument('-o', '--output-dir', default='outputs', help='出力ディレクトリ')
    batch_parser.add_argument('--no-json', action='store_true', help='JSON出力をスキップ')
    
    args = parser.parse_args()
    
    if args.command == 'diff':
        # 単一ペアの処理
        output_pdf = args.output
        if not output_pdf:
            site_name = Path(args.site_file).stem
            floor_name = Path(args.floor_file).stem
            output_pdf = f"diff_{site_name}_{floor_name}.pdf"
        
        visualize_difference(args.site_file, args.floor_file, output_pdf, output_json=not args.no_json)
    
    elif args.command == 'batch':
        # バッチ処理
        pairs = find_file_pairs(args.directory)
        
        if not pairs:
            print("対応するファイルペアが見つかりませんでした。")
            return 1
        
        print(f"\n{len(pairs)}個のファイルペアが見つかりました:")
        for site, floor in pairs:
            print(f"  - {Path(site).name} <-> {Path(floor).name}")
        
        # 出力ディレクトリ作成
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n処理を開始します...")
        success_count = 0
        for i, (site, floor) in enumerate(pairs, 1):
            print(f"\n[{i}/{len(pairs)}] 処理中...")
            building_num = Path(site).parent.parent.name
            output_pdf = output_dir / f"diff_building_{building_num}.pdf"
            
            try:
                visualize_difference(site, floor, str(output_pdf), output_json=not args.no_json)
                success_count += 1
            except Exception as e:
                print(f"エラー: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n完了しました。{success_count}/{len(pairs)}個のファイルを処理しました。")
        print(f"結果は {output_dir} に保存されています。")
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())