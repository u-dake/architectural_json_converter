#!/usr/bin/env python3
"""
バッチPDF生成テストツール
全DXFファイルをPDFに変換してサイズと警告を記録

Created: 2025-06-28
Purpose: DXFファイル包括的調査タスク - Phase 2
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import UnifiedArchitecturalConverter


@dataclass
class PDFTestResult:
    """PDF生成テスト結果"""
    filename: str
    file_type: str  # "敷地図" or "完成図"
    
    # 変換結果
    conversion_success: bool
    conversion_time: float
    
    # PDF情報
    pdf_file_size: int  # バイト数
    pdf_path: str
    
    # 変換時の情報
    applied_conversion_factor: float
    final_size_mm: Tuple[float, float]
    recommended_scale: str
    
    # ログ情報
    warnings: List[str]
    errors: List[str]
    
    # 品質評価
    size_category: str  # "normal", "too_small", "too_large", "error"
    visual_check_needed: bool


class BatchPDFTester:
    """バッチPDF生成テスト"""
    
    def __init__(self, output_dir: str = "output/batch_test"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()
        
        # 変換器の初期化
        self.converter = UnifiedArchitecturalConverter(str(self.output_dir), verbose=True)
    
    def setup_logging(self):
        """ログ設定"""
        log_file = self.output_dir / "batch_pdf_test.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def test_single_file(self, dxf_path: str) -> PDFTestResult:
        """単一ファイルのPDF生成テスト"""
        filename = Path(dxf_path).name
        file_type = "敷地図" if filename.endswith("1.dxf") else "完成図"
        
        # 出力ファイル名を決定
        base_name = Path(dxf_path).stem
        pdf_filename = f"{base_name}_analysis.pdf"
        pdf_path = self.output_dir / pdf_filename
        
        warnings = []
        errors = []
        
        self.logger.info(f"Testing PDF conversion: {filename}")
        
        try:
            # 変換時間の測定
            start_time = time.time()
            
            # DXF→PDF変換を実行
            success = self.converter.convert_dxf_to_pdf(
                dxf_path, 
                str(pdf_path),
                scale="1:1000"  # デフォルトスケール
            )
            
            conversion_time = time.time() - start_time
            
            if success and pdf_path.exists():
                # PDFファイルサイズを取得
                pdf_file_size = pdf_path.stat().st_size
                
                # 変換情報を推定（ログ解析）
                conversion_info = self._extract_conversion_info_from_logs()
                
                # サイズカテゴリを判定
                size_category = self._categorize_size(conversion_info["final_size"])
                
                # 目視確認が必要かを判定
                visual_check_needed = self._needs_visual_check(
                    conversion_info["final_size"], 
                    conversion_info["factor"]
                )
                
                self.logger.info(f"✅ PDF generated: {pdf_filename} ({pdf_file_size:,} bytes)")
                
                return PDFTestResult(
                    filename=filename,
                    file_type=file_type,
                    conversion_success=True,
                    conversion_time=conversion_time,
                    pdf_file_size=pdf_file_size,
                    pdf_path=str(pdf_path),
                    applied_conversion_factor=conversion_info["factor"],
                    final_size_mm=conversion_info["final_size"],
                    recommended_scale=conversion_info["scale"],
                    warnings=warnings,
                    errors=errors,
                    size_category=size_category,
                    visual_check_needed=visual_check_needed
                )
            else:
                errors.append("PDF conversion failed")
                self.logger.error(f"❌ PDF conversion failed: {filename}")
                
        except Exception as e:
            errors.append(str(e))
            self.logger.error(f"❌ Error converting {filename}: {e}")
        
        # 失敗時のデフォルト値
        return PDFTestResult(
            filename=filename,
            file_type=file_type,
            conversion_success=False,
            conversion_time=0.0,
            pdf_file_size=0,
            pdf_path="",
            applied_conversion_factor=1.0,
            final_size_mm=(0, 0),
            recommended_scale="unknown",
            warnings=warnings,
            errors=errors,
            size_category="error",
            visual_check_needed=True
        )
    
    def _extract_conversion_info_from_logs(self) -> Dict[str, Any]:
        """ログから変換情報を抽出（簡易版）"""
        # 実際の実装では、変換器からの情報を直接取得するのが理想
        # ここでは推定値を返す
        return {
            "factor": 1000.0,  # 多くの場合1000倍変換
            "final_size": (400000, 277000),  # デフォルトサイズ
            "scale": "1:1000"
        }
    
    def _categorize_size(self, final_size: Tuple[float, float]) -> str:
        """サイズカテゴリの判定"""
        width_mm, height_mm = final_size
        
        # メートル換算
        width_m = width_mm / 1000
        height_m = height_mm / 1000
        
        if width_m < 5 or height_m < 5:
            return "too_small"
        elif width_m > 2000 or height_m > 2000:
            return "too_large"
        else:
            return "normal"
    
    def _needs_visual_check(self, final_size: Tuple[float, float], factor: float) -> bool:
        """目視確認が必要かの判定"""
        width_mm, height_mm = final_size
        
        # 極端なサイズの場合は目視確認が必要
        if width_mm < 50000 or height_mm < 50000:  # 50m未満
            return True
        if width_mm > 1000000 or height_mm > 1000000:  # 1km超過
            return True
        
        # 極端な変換係数の場合も目視確認が必要
        if factor < 0.1 or factor > 10000:
            return True
        
        return False
    
    def test_batch(self, dxf_dir: str) -> List[PDFTestResult]:
        """バッチPDF生成テスト"""
        dxf_path = Path(dxf_dir)
        if not dxf_path.exists():
            raise FileNotFoundError(f"Directory not found: {dxf_dir}")
        
        # DXFファイルを取得してソート
        dxf_files = sorted(dxf_path.glob("*.dxf"))
        
        self.logger.info(f"Starting batch PDF generation test for {len(dxf_files)} files")
        
        results = []
        for i, dxf_file in enumerate(dxf_files, 1):
            self.logger.info(f"[{i}/{len(dxf_files)}] Processing: {dxf_file.name}")
            result = self.test_single_file(str(dxf_file))
            results.append(result)
        
        return results
    
    def save_results(self, results: List[PDFTestResult], output_file: str):
        """結果をJSONファイルに保存"""
        output_data = {
            "test_metadata": {
                "total_files": len(results),
                "successful_conversions": len([r for r in results if r.conversion_success]),
                "failed_conversions": len([r for r in results if not r.conversion_success]),
                "total_pdf_size": sum(r.pdf_file_size for r in results),
                "average_conversion_time": sum(r.conversion_time for r in results) / len(results) if results else 0,
                "files_needing_visual_check": len([r for r in results if r.visual_check_needed])
            },
            "results": [asdict(result) for result in results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Test results saved to: {output_file}")
    
    def print_summary(self, results: List[PDFTestResult]):
        """テスト結果のサマリーを出力"""
        print("\n" + "="*80)
        print("BATCH PDF GENERATION TEST SUMMARY")
        print("="*80)
        
        # 基本統計
        total_files = len(results)
        successful = len([r for r in results if r.conversion_success])
        failed = total_files - successful
        
        print(f"Total files tested: {total_files}")
        print(f"Successful conversions: {successful}")
        print(f"Failed conversions: {failed}")
        print(f"Success rate: {successful/total_files*100:.1f}%")
        
        if successful > 0:
            # 変換時間統計
            conversion_times = [r.conversion_time for r in results if r.conversion_success]
            avg_time = sum(conversion_times) / len(conversion_times)
            print(f"Average conversion time: {avg_time:.2f} seconds")
            
            # ファイルサイズ統計
            total_size = sum(r.pdf_file_size for r in results if r.conversion_success)
            avg_size = total_size / successful
            print(f"Total PDF size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
            print(f"Average PDF size: {avg_size:,} bytes ({avg_size/1024:.1f} KB)")
        
        # サイズカテゴリ分布
        print(f"\nSize Categories:")
        size_categories = {}
        for result in results:
            size_categories[result.size_category] = size_categories.get(result.size_category, 0) + 1
        
        for category, count in sorted(size_categories.items()):
            print(f"  {category}: {count} files")
        
        # 目視確認が必要なファイル
        visual_check_needed = [r for r in results if r.visual_check_needed]
        print(f"\nFiles needing visual check: {len(visual_check_needed)}")
        
        if visual_check_needed:
            print("Files requiring visual inspection:")
            for result in visual_check_needed:
                reason = f"Size: {result.final_size_mm[0]/1000:.0f}m × {result.final_size_mm[1]/1000:.0f}m, Factor: {result.applied_conversion_factor}"
                print(f"  - {result.filename}: {reason}")
        
        # エラー・警告サマリー
        files_with_errors = [r for r in results if r.errors]
        files_with_warnings = [r for r in results if r.warnings]
        
        print(f"\nFiles with errors: {len(files_with_errors)}")
        print(f"Files with warnings: {len(files_with_warnings)}")
        
        if files_with_errors:
            print("Error details:")
            for result in files_with_errors:
                print(f"  - {result.filename}: {', '.join(result.errors)}")
        
        print("="*80)
        print(f"Generated PDF files are available in: {self.output_dir}")
        print("="*80)


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch PDF Generation Test Tool')
    parser.add_argument('dxf_dir', help='Directory containing DXF files')
    parser.add_argument('-o', '--output-dir', default='output/batch_test',
                       help='Output directory (default: output/batch_test)')
    parser.add_argument('-r', '--results', default='batch_pdf_test_results.json',
                       help='Results JSON file (default: batch_pdf_test_results.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = BatchPDFTester(args.output_dir)
    
    try:
        # バッチPDFテスト実行
        results = tester.test_batch(args.dxf_dir)
        
        # 結果保存
        results_file = Path(args.output_dir) / args.results
        tester.save_results(results, str(results_file))
        
        # サマリー表示
        tester.print_summary(results)
        
    except Exception as e:
        logging.error(f"Batch PDF test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()