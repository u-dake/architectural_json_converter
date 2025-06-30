#!/usr/bin/env python3
"""
CAD Analyzer - 建築図面分析統合ツール

DXF図面の差分分析、単位検出、可視化を統合したコマンドラインツール
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from typing import Optional, List, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.visualize_dxf_diff import visualize_difference, find_file_pairs
from tools.debug.analyze_block_patterns_advanced import AdvancedBlockPatternAnalyzer
from tools.dxf_to_json import dxf_to_json
from src.engines.safe_dxf_converter import SafeDXFConverter


def setup_logging(verbose: bool = False):
    """ロギングの設定"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_analyze_patterns(args):
    """ブロックパターン分析コマンド"""
    print(f"ブロックパターンを分析中: {args.input_dir}")
    
    analyzer = AdvancedBlockPatternAnalyzer()
    analyzer.analyze_dxf_directory(args.input_dir)
    analyzer.print_report()
    
    output_file = args.output or 'block_patterns_advanced.json'
    analyzer.save_results(output_file)
    print(f"\n分析結果を保存しました: {output_file}")


def cmd_diff(args):
    """差分分析コマンド"""
    output_pdf = args.output or f"diff_{Path(args.site_plan).stem}_{Path(args.floor_plan).stem}.pdf"
    
    print(f"差分を分析中:")
    print(f"  敷地図: {args.site_plan}")
    print(f"  完成図: {args.floor_plan}")
    
    visualize_difference(
        args.site_plan, 
        args.floor_plan, 
        output_pdf,
        output_json=not args.no_json
    )


def cmd_batch_diff(args):
    """バッチ差分分析コマンド"""
    pairs = find_file_pairs(args.input_dir)
    
    if not pairs:
        print("対応するファイルペアが見つかりませんでした。")
        return
    
    print(f"{len(pairs)}個のファイルペアが見つかりました。")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    for i, (site, floor) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] 処理中...")
        building_num = Path(site).parent.parent.name
        output_pdf = output_dir / f"diff_building_{building_num}.pdf"
        
        try:
            visualize_difference(
                site, floor, str(output_pdf), 
                output_json=not args.no_json
            )
            success_count += 1
        except Exception as e:
            print(f"エラー: {e}")
            continue
    
    print(f"\n完了: {success_count}/{len(pairs)}個のファイルを処理しました。")


def cmd_convert(args):
    """DXF→JSON変換コマンド"""
    output_json = args.output or Path(args.dxf_file).with_suffix('.json')
    
    print(f"DXFファイルを変換中: {args.dxf_file}")
    dxf_to_json(
        args.dxf_file,
        str(output_json),
        include_structure=not args.no_structure,
        include_elements=not args.no_elements
    )


def cmd_analyze_all(args):
    """完全分析コマンド（すべての機能を実行）"""
    print("=== 完全分析を開始 ===\n")
    
    # 1. ブロックパターン分析
    if not args.skip_patterns:
        print("【ステップ1】ブロックパターン分析")
        analyzer = AdvancedBlockPatternAnalyzer()
        analyzer.analyze_dxf_directory(args.input_dir)
        analyzer.save_results('block_patterns_advanced.json')
        print("✓ ブロックパターン分析完了\n")
    
    # 2. 差分分析
    print("【ステップ2】差分分析")
    pairs = find_file_pairs(args.input_dir)
    
    if pairs:
        output_dir = Path(args.output_dir) / 'differences'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, (site, floor) in enumerate(pairs, 1):
            print(f"  [{i}/{len(pairs)}] {Path(site).parent.parent.name}")
            building_num = Path(site).parent.parent.name
            output_pdf = output_dir / f"diff_building_{building_num}.pdf"
            
            try:
                visualize_difference(
                    site, floor, str(output_pdf),
                    output_json=True
                )
            except Exception as e:
                print(f"    エラー: {e}")
        
        print("✓ 差分分析完了\n")
    
    # 3. 個別ファイルのJSON変換（サンプル）
    if not args.skip_json:
        print("【ステップ3】JSON変換（サンプル）")
        json_dir = Path(args.output_dir) / 'json_samples'
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # 各建物から1ファイルずつサンプル変換
        sample_count = 0
        for pair in pairs[:3]:  # 最初の3建物のみ
            site_file = pair[0]
            building_num = Path(site_file).parent.parent.name
            output_json = json_dir / f"building_{building_num}_site.json"
            
            try:
                dxf_to_json(site_file, str(output_json))
                sample_count += 1
            except Exception as e:
                print(f"    エラー: {e}")
        
        print(f"✓ {sample_count}個のサンプルJSON生成完了\n")
    
    print("=== 完全分析完了 ===")
    print(f"結果は {args.output_dir} に保存されています。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='CAD Analyzer - 建築図面分析統合ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # ブロックパターンを分析
  %(prog)s patterns sample_data

  # 2つのDXFファイルの差分を分析
  %(prog)s diff site.dxf floor.dxf

  # ディレクトリ内のすべてのペアを分析
  %(prog)s batch sample_data -o outputs/differences

  # DXFをJSONに変換
  %(prog)s convert drawing.dxf

  # すべての分析を実行
  %(prog)s analyze-all sample_data -o outputs
"""
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='詳細なログを表示')
    
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # patterns: ブロックパターン分析
    patterns_parser = subparsers.add_parser('patterns',
                                          help='DXFファイルのブロックパターンを分析')
    patterns_parser.add_argument('input_dir', help='DXFファイルのディレクトリ')
    patterns_parser.add_argument('-o', '--output', help='出力JSONファイル')
    
    # diff: 差分分析
    diff_parser = subparsers.add_parser('diff',
                                       help='2つのDXFファイルの差分を分析')
    diff_parser.add_argument('site_plan', help='敷地図DXFファイル')
    diff_parser.add_argument('floor_plan', help='完成図DXFファイル')
    diff_parser.add_argument('-o', '--output', help='出力PDFファイル')
    diff_parser.add_argument('--no-json', action='store_true',
                           help='JSON出力をスキップ')
    
    # batch: バッチ差分分析
    batch_parser = subparsers.add_parser('batch',
                                        help='ディレクトリ内のファイルペアを一括分析')
    batch_parser.add_argument('input_dir', help='DXFファイルのディレクトリ')
    batch_parser.add_argument('-o', '--output-dir', default='outputs',
                            help='出力ディレクトリ')
    batch_parser.add_argument('--no-json', action='store_true',
                            help='JSON出力をスキップ')
    
    # convert: DXF→JSON変換
    convert_parser = subparsers.add_parser('convert',
                                         help='DXFファイルをJSONに変換')
    convert_parser.add_argument('dxf_file', help='入力DXFファイル')
    convert_parser.add_argument('-o', '--output', help='出力JSONファイル')
    convert_parser.add_argument('--no-structure', action='store_true',
                              help='構造解析をスキップ')
    convert_parser.add_argument('--no-elements', action='store_true',
                              help='要素詳細をスキップ')
    
    # analyze-all: 完全分析
    all_parser = subparsers.add_parser('analyze-all',
                                      help='すべての分析を実行')
    all_parser.add_argument('input_dir', help='DXFファイルのディレクトリ')
    all_parser.add_argument('-o', '--output-dir', default='outputs',
                          help='出力ディレクトリ')
    all_parser.add_argument('--skip-patterns', action='store_true',
                          help='ブロックパターン分析をスキップ')
    all_parser.add_argument('--skip-json', action='store_true',
                          help='サンプルJSON生成をスキップ')
    
    args = parser.parse_args()
    
    # ロギング設定
    setup_logging(args.verbose)
    
    # コマンド実行
    if args.command == 'patterns':
        cmd_analyze_patterns(args)
    elif args.command == 'diff':
        cmd_diff(args)
    elif args.command == 'batch':
        cmd_batch_diff(args)
    elif args.command == 'convert':
        cmd_convert(args)
    elif args.command == 'analyze-all':
        cmd_analyze_all(args)
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())