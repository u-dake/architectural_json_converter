"""
Architectural Drawing Difference Analyzer - Main CLI

建築図面差分解析システムのメインCLI
Phase 2統合アプリケーション
"""

import argparse
import sys
import os
import time
from pathlib import Path
from typing import Optional, Tuple

# 必要なモジュールをインポート
from engines.dxf_converter import convert_dxf_to_geometry_data
from engines.pdf_converter import convert_pdf_to_geometry_data
from engines.difference_engine import extract_differences, save_difference_result_to_json
from visualization.matplotlib_visualizer import ArchitecturalPlotter
from data_structures.geometry_data import DifferenceResult


class ArchitecturalAnalyzer:
    """建築図面差分解析システムのメインクラス"""
    
    def __init__(self, output_dir: str = "output", verbose: bool = True):
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.plotter = ArchitecturalPlotter()
        
        # 出力ディレクトリを作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str) -> None:
        """ログ出力"""
        if self.verbose:
            print(f"[INFO] {message}")
    
    def error(self, message: str) -> None:
        """エラー出力"""
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def load_drawing_file(self, filepath: str) -> Tuple[str, object]:
        """
        図面ファイルを読み込み、統一データ構造に変換
        
        Args:
            filepath: ファイルパス
            
        Returns:
            (ファイルタイプ, GeometryDataオブジェクト)
            
        Raises:
            ValueError: 対応していないファイル形式
            FileNotFoundError: ファイルが見つからない
        """
        filepath = str(filepath)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")
        
        file_ext = Path(filepath).suffix.lower()
        
        if file_ext == '.dxf':
            self.log(f"DXFファイルを読み込み中: {filepath}")
            geometry_data = convert_dxf_to_geometry_data(filepath)
            return 'dxf', geometry_data
            
        elif file_ext == '.pdf':
            self.log(f"PDFファイルを読み込み中: {filepath}")
            geometry_data = convert_pdf_to_geometry_data(filepath)
            return 'pdf', geometry_data
            
        else:
            raise ValueError(f"対応していないファイル形式: {file_ext}")
    
    def analyze_differences(self, site_file: str, plan_file: str,
                          tolerance: float = 0.5) -> DifferenceResult:
        """
        2つの図面ファイルの差分を解析
        
        Args:
            site_file: 敷地図ファイルパス
            plan_file: 間取り図ファイルパス
            tolerance: 類似度の閾値
            
        Returns:
            差分解析結果
        """
        start_time = time.time()
        
        # ファイル読み込み
        site_type, site_data = self.load_drawing_file(site_file)
        plan_type, plan_data = self.load_drawing_file(plan_file)
        
        self.log(f"敷地図: {len(site_data.elements)}要素 ({site_type})")
        self.log(f"間取り図: {len(plan_data.elements)}要素 ({plan_type})")
        
        # 差分解析実行
        self.log("差分解析を実行中...")
        result = extract_differences(site_data, plan_data, tolerance)
        
        # 処理時間を記録
        processing_time = time.time() - start_time
        result.analysis_metadata["processing_time"] = processing_time
        result.analysis_metadata["site_file"] = site_file
        result.analysis_metadata["plan_file"] = plan_file
        result.analysis_metadata["tolerance"] = tolerance
        
        # 結果サマリーを表示
        stats = result.get_statistics()
        self.log(f"解析完了 (処理時間: {processing_time:.2f}秒)")
        self.log(f"新規要素: {stats['total_new_elements']}個")
        self.log(f"壁: {stats['walls_detected']}個, 開口部: {stats['openings_detected']}個, 設備: {stats['fixtures_detected']}個")
        
        return result
    
    def save_results(self, result: DifferenceResult,
                    base_filename: str = "analysis_result") -> str:
        """
        解析結果をJSONファイルに保存
        
        Args:
            result: 差分解析結果
            base_filename: ベースファイル名
            
        Returns:
            保存されたファイルパス
        """
        output_path = self.output_dir / f"{base_filename}.json"
        save_difference_result_to_json(result, str(output_path))
        return str(output_path)
    
    def create_visualizations(self, result: DifferenceResult,
                            base_filename: str = "visualization") -> Tuple[str, str]:
        """
        可視化画像を生成
        
        Args:
            result: 差分解析結果
            base_filename: ベースファイル名
            
        Returns:
            (差分可視化パス, 建築要素解析パス)
        """
        self.log("可視化を生成中...")
        
        # 差分可視化
        diff_viz_path = self.output_dir / f"{base_filename}_difference.png"
        self.plotter.plot_difference_result(result, str(diff_viz_path))
        
        # 建築要素解析
        arch_analysis_path = self.output_dir / f"{base_filename}_architectural.png"
        self.plotter.plot_architectural_analysis(result, str(arch_analysis_path))
        
        return str(diff_viz_path), str(arch_analysis_path)

    def convert_dxf_to_pdf(self, dxf_file: str, output_filename: Optional[str] = None) -> dict:
        """
        単一のDXFファイルをPDFに変換

        Args:
            dxf_file: 入力DXFファイルパス
            output_filename: 出力PDFファイル名 (オプション)

        Returns:
            実行結果の辞書
        """
        start_time = time.time()
        try:
            # DXF読み込み
            file_type, geometry_data = self.load_drawing_file(dxf_file)
            if file_type != 'dxf':
                raise ValueError("入力はDXFファイルである必要があります")

            # 出力パス決定
            if output_filename:
                pdf_path = self.output_dir / "pdf" / output_filename
            else:
                pdf_path = self.output_dir / "pdf" / f"{Path(dxf_file).stem}.pdf"
            
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

            # PDF生成
            self.log(f"PDFを生成中: {pdf_path}")
            saved_path = self.plotter.save_geometry_as_pdf(geometry_data, str(pdf_path))

            processing_time = time.time() - start_time
            return {
                "success": True,
                "output_file": saved_path,
                "processing_time": processing_time
            }

        except Exception as e:
            self.error(f"変換エラー: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_complete_analysis(self, site_file: str, plan_file: str,
                            tolerance: float = 0.5,
                            enable_visualization: bool = True,
                            enable_interactive: bool = False,
                            base_filename: str = "analysis") -> dict:
        """
        完全な解析パイプラインを実行
        
        Args:
            site_file: 敷地図ファイルパス
            plan_file: 間取り図ファイルパス
            tolerance: 類似度の閾値
            enable_visualization: 可視化の有効化
            enable_interactive: インタラクティブ可視化の有効化
            base_filename: 出力ファイルのベース名
            
        Returns:
            実行結果の辞書
        """
        try:
            # 差分解析
            result = self.analyze_differences(site_file, plan_file, tolerance)
            
            # 結果保存
            json_path = self.save_results(result, base_filename)
            
            output_files = {
                "json": json_path,
                "visualizations": []
            }
            
            # 可視化生成
            if enable_visualization:
                diff_viz, arch_viz = self.create_visualizations(result, base_filename)
                output_files["visualizations"] = [diff_viz, arch_viz]
            
            # インタラクティブ可視化（将来実装）
            if enable_interactive:
                self.log("インタラクティブ可視化は将来実装予定です")
            
            # 統計情報
            stats = result.get_statistics()
            
            return {
                "success": True,
                "statistics": stats,
                "output_files": output_files,
                "processing_time": result.analysis_metadata.get("processing_time", 0)
            }
            
        except Exception as e:
            self.error(f"解析エラー: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        description="建築図面ユーティリティシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="実行するコマンド")

    # --- 解析コマンド (analyze) ---
    parser_analyze = subparsers.add_parser(
        "analyze",
        help="2つの図面ファイルを比較し、差分を解析します。",
        epilog="""使用例:
  python src/main.py analyze site.dxf plan.dxf --visualize"""
    )
    parser_analyze.add_argument("site_file", help="敷地図ファイルパス (.dxf または .pdf)")
    parser_analyze.add_argument("plan_file", help="間取り図ファイルパス (.dxf または .pdf)")
    parser_analyze.add_argument("--visualize", "-v", action="store_true", help="matplotlib による可視化を生成")
    parser_analyze.add_argument("--interactive", "-i", action="store_true", help="Plotly によるインタラクティブ可視化を生成（将来実装）")
    parser_analyze.add_argument("--output-dir", "-o", default="output", help="出力ディレクトリ (デフォルト: output)")
    parser_analyze.add_argument("--tolerance", "-t", type=float, default=0.5, help="要素マッチングの類似度閾値 (0.0-1.0, デフォルト: 0.5)")
    parser_analyze.add_argument("--quiet", "-q", action="store_true", help="詳細ログを無効化")
    parser_analyze.add_argument("--filename", "-f", default="analysis", help="出力ファイルのベース名 (デフォルト: analysis)")

    # --- 変換コマンド (convert) ---
    parser_convert = subparsers.add_parser(
        "convert",
        help="DXFファイルをPDFに変換します。",
        epilog="""使用例:
  python src/main.py convert sample_data/site_plan/01_敷地図.dxf"""
    )
    parser_convert.add_argument("dxf_file", help="入力DXFファイルパス")
    parser_convert.add_argument("--output-dir", "-o", default="output", help="出力ディレクトリ (デフォルト: output)")
    parser_convert.add_argument("--output-filename", help="出力PDFファイル名 (オプション)")
    parser_convert.add_argument("--quiet", "-q", action="store_true", help="詳細ログを無効化")
    
    return parser


def main():
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # グローバルオプション
    output_dir = args.output_dir if hasattr(args, 'output_dir') else "output"
    verbose = not args.quiet if hasattr(args, 'quiet') else True

    # 解析システム初期化
    analyzer = ArchitecturalAnalyzer(
        output_dir=output_dir,
        verbose=verbose
    )

    if args.command == "analyze":
        # --- 差分解析の実行 ---
        if verbose:
            print("🏗️  建築図面差分解析システム")
            print(f"  敷地図: {args.site_file}")
            print(f"  間取り図: {args.plan_file}")
            print(f"  出力先: {args.output_dir}")
            print("-" * 50)

        result = analyzer.run_complete_analysis(
            site_file=args.site_file,
            plan_file=args.plan_file,
            tolerance=args.tolerance,
            enable_visualization=args.visualize,
            enable_interactive=args.interactive,
            base_filename=args.filename
        )
        
        if result["success"]:
            if verbose:
                print("\n✅ 解析完了!")
                print(f"処理時間: {result['processing_time']:.2f}秒")
                
                stats = result["statistics"]
                print(f"\n📊 解析結果:")
                print(f"  新規要素: {stats['total_new_elements']}個")
                print(f"  壁: {stats['walls_detected']}個")
                print(f"  開口部: {stats['openings_detected']}個") 
                print(f"  設備: {stats['fixtures_detected']}個")
                print(f"  削除要素: {stats['removed_elements']}個")
                
                print(f"\n📁 出力ファイル:")
                print(f"  解析結果: {result['output_files']['json']}")
                for viz_file in result['output_files']['visualizations']:
                    print(f"  可視化: {viz_file}")
            sys.exit(0)

    elif args.command == "convert":
        # --- DXFからPDFへの変換実行 ---
        if verbose:
            print("🔄  DXF to PDF Converter")
            print(f"  入力ファイル: {args.dxf_file}")
            print(f"  出力ディレクトリ: {output_dir}")
            print("-" * 50)

        result = analyzer.convert_dxf_to_pdf(
            dxf_file=args.dxf_file,
            output_filename=args.output_filename
        )

        if result["success"]:
            if verbose:
                print(f"\n✅ 変換完了!")
                print(f"  処理時間: {result['processing_time']:.2f}秒")
                print(f"  出力ファイル: {result['output_file']}")
            sys.exit(0)
        else:
            print(f"\n❌ 変換失敗: {result['error']}", file=sys.stderr)
            sys.exit(1)



if __name__ == "__main__":
    main()