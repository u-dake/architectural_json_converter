#!/usr/bin/env python3
"""
Unified Architectural Drawing Converter & Analyzer

建築図面変換・差分解析統合システム
- DXF → PDF変換
- PDF → JSON変換  
- 図面差分解析
- 可視化出力
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engines.safe_dxf_converter import SafeDXFConverter
from src.visualization.cad_standard_visualizer import CADStandardVisualizer

# 従来機能のインポート（利用可能な場合）
try:
    from engines.pdf_converter import convert_pdf_to_geometry_data
    from engines.difference_engine import extract_differences, save_difference_result_to_json
    from visualization.matplotlib_visualizer import ArchitecturalPlotter
    LEGACY_FEATURES_AVAILABLE = True
except ImportError:
    LEGACY_FEATURES_AVAILABLE = False


class UnifiedArchitecturalConverter:
    """統合建築図面変換・解析システム"""

    def __init__(self, output_dir: str = "output", verbose: bool = True):
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.setup_logging()
        
        # 出力ディレクトリの作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "pdf").mkdir(exist_ok=True)
        (self.output_dir / "json").mkdir(exist_ok=True)
        (self.output_dir / "analysis").mkdir(exist_ok=True)

    def setup_logging(self):
        """ログ設定"""
        log_level = logging.INFO if self.verbose else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.output_dir / 'conversion.log')
            ]
        )

    def convert_dxf_to_pdf(self, input_file: str, output_file: Optional[str] = None, scale: str = "1:100") -> bool:
        """DXFファイルをPDFに変換
        
        Args:
            input_file: 入力DXFファイルパス
            output_file: 出力PDFファイルパス（省略時は自動生成）
            
        Returns:
            変換成功の場合True
        """
        if not self.validate_input_file(input_file, '.dxf'):
            return False

        if output_file is None:
            base_name = Path(input_file).stem
            output_file = self.output_dir / "pdf" / f"{base_name}.pdf"

        try:
            logging.info(f"Converting DXF to PDF: {input_file} -> {output_file}")
            
            # DXFファイルを変換
            converter = SafeDXFConverter()
            geometry = converter.convert_dxf_file(input_file, include_paperspace=True)
            
            if not geometry.elements:
                logging.warning("No geometry elements found in DXF file")
                return False
            
            logging.info(f"Converted {len(geometry.elements)} elements")
            
            # 要素タイプ別の統計
            self.log_element_statistics(geometry)
            
            # A3、1/100スケールのPDFに変換
            visualizer = CADStandardVisualizer()
            
            # ファイル名からタイトルを生成
            title = Path(input_file).stem
            
            visualizer.visualize_to_a3_pdf(
                geometry,
                str(output_file),
                scale=scale,
                dpi=300,
                show_border=True,
                title=title
            )
            
            # 出力ファイルの検証
            output_path = Path(output_file)
            if output_path.exists() and output_path.stat().st_size > 0:
                logging.info(f"DXF to PDF conversion completed: {output_file}")
                return True
            else:
                logging.error("Output PDF was not created properly")
                return False
                
        except Exception as e:
            logging.error(f"Error in DXF to PDF conversion: {e}")
            return False

    def convert_pdf_to_json(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """PDFファイルをJSONに変換（従来機能）
        
        Args:
            input_file: 入力PDFファイルパス
            output_file: 出力JSONファイルパス（省略時は自動生成）
            
        Returns:
            変換成功の場合True
        """
        if not LEGACY_FEATURES_AVAILABLE:
            logging.error("Legacy PDF conversion features not available")
            return False

        if not self.validate_input_file(input_file, '.pdf'):
            return False

        if output_file is None:
            base_name = Path(input_file).stem
            output_file = self.output_dir / "json" / f"{base_name}.json"

        try:
            logging.info(f"Converting PDF to JSON: {input_file} -> {output_file}")
            
            # PDFを解析してJSON変換
            geometry_data = convert_pdf_to_geometry_data(input_file)
            
            # JSONファイルに保存
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(geometry_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"PDF to JSON conversion completed: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error in PDF to JSON conversion: {e}")
            return False

    def analyze_differences(self, site_file: str, floor_file: str, output_file: Optional[str] = None) -> bool:
        """図面差分解析（従来機能）
        
        Args:
            site_file: 敷地図ファイルパス
            floor_file: 完成形図面ファイルパス
            output_file: 出力JSONファイルパス（省略時は自動生成）
            
        Returns:
            解析成功の場合True
        """
        if not LEGACY_FEATURES_AVAILABLE:
            logging.error("Legacy difference analysis features not available")
            return False

        for file_path in [site_file, floor_file]:
            if not Path(file_path).exists():
                logging.error(f"Input file not found: {file_path}")
                return False

        if output_file is None:
            output_file = self.output_dir / "analysis" / "difference_analysis.json"

        try:
            logging.info(f"Analyzing differences: {site_file} vs {floor_file}")
            
            # 差分解析の実行
            differences = extract_differences(site_file, floor_file)
            
            # 結果をJSONファイルに保存
            save_difference_result_to_json(differences, str(output_file))
            
            logging.info(f"Difference analysis completed: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error in difference analysis: {e}")
            return False

    def batch_convert_dxf(self, input_dir: str, pattern: str = "*.dxf", scale: str = "1:100") -> List[str]:
        """DXFファイルの一括変換
        
        Args:
            input_dir: 入力ディレクトリ
            pattern: ファイルパターン
            
        Returns:
            変換されたPDFファイルのリスト
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            logging.error(f"Input directory not found: {input_dir}")
            return []

        dxf_files = list(input_path.glob(pattern))
        converted_files = []

        logging.info(f"Found {len(dxf_files)} DXF files for batch conversion")

        for dxf_file in dxf_files:
            output_file = self.output_dir / "pdf" / f"{dxf_file.stem}.pdf"
            if self.convert_dxf_to_pdf(str(dxf_file), str(output_file), scale):
                converted_files.append(str(output_file))

        logging.info(f"Batch conversion completed: {len(converted_files)}/{len(dxf_files)} files")
        return converted_files

    def validate_input_file(self, file_path: str, expected_ext: str) -> bool:
        """入力ファイルの検証"""
        path = Path(file_path)
        
        if not path.exists():
            logging.error(f"Input file not found: {file_path}")
            return False
        
        if not file_path.lower().endswith(expected_ext):
            logging.error(f"Input file is not a {expected_ext} file: {file_path}")
            return False
        
        try:
            file_size = path.stat().st_size
            if file_size == 0:
                logging.error(f"Input file is empty: {file_path}")
                return False
            logging.info(f"Input file size: {file_size:,} bytes")
        except OSError as e:
            logging.error(f"Cannot access input file: {e}")
            return False
        
        return True

    def log_element_statistics(self, geometry):
        """要素統計のログ出力"""
        element_types = {}
        for element in geometry.elements:
            element_type = type(element).__name__
            element_types[element_type] = element_types.get(element_type, 0) + 1
        
        logging.info("Element types:")
        for elem_type, count in sorted(element_types.items()):
            logging.info(f"  {elem_type}: {count}")


def create_parser():
    """コマンドライン引数パーサーの作成"""
    parser = argparse.ArgumentParser(
        description='Unified Architectural Drawing Converter & Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # DXF to PDF conversion
  python main_unified.py dxf2pdf input.dxf

  # PDF to JSON conversion  
  python main_unified.py pdf2json input.pdf

  # Difference analysis
  python main_unified.py diff site.dxf floor.dxf

  # Batch DXF conversion
  python main_unified.py batch /path/to/dxf/files/
        """
    )
    
    parser.add_argument(
        'command',
        choices=['dxf2pdf', 'pdf2json', 'diff', 'batch'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='Input file(s) or directory'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file or directory'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.dxf',
        help='File pattern for batch processing (default: *.dxf)'
    )
    
    parser.add_argument(
        '--scale',
        default='1:100',
        help='Drawing scale for PDF output (default: 1:100)'
    )
    
    return parser


def main():
    """メイン処理"""
    parser = create_parser()
    args = parser.parse_args()

    # コンバーターの初期化
    converter = UnifiedArchitecturalConverter(
        output_dir=args.output_dir,
        verbose=args.verbose
    )

    success = False

    try:
        if args.command == 'dxf2pdf':
            if len(args.files) != 1:
                print("Error: dxf2pdf requires exactly one input file")
                return 1
            success = converter.convert_dxf_to_pdf(args.files[0], args.output, args.scale)

        elif args.command == 'pdf2json':
            if len(args.files) != 1:
                print("Error: pdf2json requires exactly one input file")
                return 1
            success = converter.convert_pdf_to_json(args.files[0], args.output)

        elif args.command == 'diff':
            if len(args.files) != 2:
                print("Error: diff requires exactly two input files")
                return 1
            success = converter.analyze_differences(args.files[0], args.files[1], args.output)

        elif args.command == 'batch':
            if len(args.files) != 1:
                print("Error: batch requires exactly one input directory")
                return 1
            converted_files = converter.batch_convert_dxf(args.files[0], args.pattern, args.scale)
            success = len(converted_files) > 0

        else:
            print(f"Error: Unknown command '{args.command}'")
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())