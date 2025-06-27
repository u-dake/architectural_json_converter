#!/usr/bin/env python3
"""
バッチ単位系分析ツール
全DXFファイルの単位系混在状況を一括チェック

Created: 2025-06-28
Purpose: DXFファイル包括的調査タスク
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import ezdxf
from ezdxf.entities import Insert

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.engines.safe_dxf_converter import SafeDXFConverter


@dataclass
class UnitAnalysisResult:
    """単位系分析結果"""
    filename: str
    file_type: str  # "敷地図" or "完成図"
    
    # ヘッダー情報
    insunits_code: int
    insunits_name: str
    
    # INSERT座標情報
    insert_count: int
    insert_min_x: float
    insert_max_x: float
    insert_min_y: float
    insert_max_y: float
    insert_width: float
    insert_height: float
    
    # ブロック内座標情報
    block_elements_count: int
    block_min_x: float
    block_max_x: float
    block_min_y: float
    block_max_y: float
    block_width: float
    block_height: float
    
    # 推定単位系
    estimated_insert_unit: str  # "mm", "m", "unknown"
    estimated_block_unit: str   # "mm", "m", "unknown"
    unit_consistency: str       # "consistent", "mixed", "unknown"
    
    # 建築図面としての妥当性
    size_validation: str        # "valid", "too_small", "too_large"
    recommended_scale: str
    
    # 変換情報
    auto_conversion_applied: bool
    conversion_factor: float
    final_size_mm: Tuple[float, float]
    
    # 警告・エラー
    warnings: List[str]
    errors: List[str]


class BatchUnitAnalyzer:
    """バッチ単位系分析器"""
    
    def __init__(self):
        self.converter = SafeDXFConverter()
        self.setup_logging()
        
        # INSUNITS コード → 名前のマッピング
        self.insunits_map = {
            0: "Unknown",
            1: "Inch", 
            2: "Foot",
            3: "Mile",
            4: "Millimeter",
            5: "Centimeter", 
            6: "Meter",
            7: "Kilometer"
        }
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_file(self, file_path: str) -> UnitAnalysisResult:
        """単一ファイルの分析"""
        filename = Path(file_path).name
        file_type = "敷地図" if filename.endswith("1.dxf") else "完成図"
        
        warnings = []
        errors = []
        
        try:
            # DXFファイル読み込み
            doc = ezdxf.readfile(file_path)
            
            # ヘッダー情報取得
            insunits_code = getattr(doc, 'units', 0)
            insunits_name = self.insunits_map.get(insunits_code, f"Unknown({insunits_code})")
            
            # INSERT要素の分析
            insert_data = self._analyze_insert_elements(doc)
            
            # ブロック内要素の分析
            block_data = self._analyze_block_elements(doc)
            
            # 単位系の推定
            unit_analysis = self._estimate_unit_systems(insert_data, block_data)
            
            # 建築図面としての妥当性チェック
            validation = self._validate_architectural_drawing(
                insert_data["width"], insert_data["height"], 
                block_data["width"], block_data["height"]
            )
            
            # SafeDXFConverterでの変換テスト
            conversion_info = self._test_conversion(file_path)
            
            return UnitAnalysisResult(
                filename=filename,
                file_type=file_type,
                insunits_code=insunits_code,
                insunits_name=insunits_name,
                insert_count=insert_data["count"],
                insert_min_x=insert_data["min_x"],
                insert_max_x=insert_data["max_x"],
                insert_min_y=insert_data["min_y"],
                insert_max_y=insert_data["max_y"],
                insert_width=insert_data["width"],
                insert_height=insert_data["height"],
                block_elements_count=block_data["count"],
                block_min_x=block_data["min_x"],
                block_max_x=block_data["max_x"],
                block_min_y=block_data["min_y"],
                block_max_y=block_data["max_y"],
                block_width=block_data["width"],
                block_height=block_data["height"],
                estimated_insert_unit=unit_analysis["insert_unit"],
                estimated_block_unit=unit_analysis["block_unit"],
                unit_consistency=unit_analysis["consistency"],
                size_validation=validation["status"],
                recommended_scale=validation["scale"],
                auto_conversion_applied=conversion_info["applied"],
                conversion_factor=conversion_info["factor"],
                final_size_mm=conversion_info["final_size"],
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            self.logger.error(f"Error analyzing {filename}: {e}")
            
            # エラー時のデフォルト値
            return UnitAnalysisResult(
                filename=filename,
                file_type=file_type,
                insunits_code=0,
                insunits_name="Error",
                insert_count=0,
                insert_min_x=0, insert_max_x=0, insert_min_y=0, insert_max_y=0,
                insert_width=0, insert_height=0,
                block_elements_count=0,
                block_min_x=0, block_max_x=0, block_min_y=0, block_max_y=0,
                block_width=0, block_height=0,
                estimated_insert_unit="unknown",
                estimated_block_unit="unknown",
                unit_consistency="unknown",
                size_validation="error",
                recommended_scale="unknown",
                auto_conversion_applied=False,
                conversion_factor=1.0,
                final_size_mm=(0, 0),
                warnings=warnings,
                errors=errors
            )
    
    def _analyze_insert_elements(self, doc) -> Dict[str, Any]:
        """INSERT要素の分析"""
        modelspace = doc.modelspace()
        insert_coords = []
        
        for entity in modelspace:
            if entity.dxftype() == 'INSERT':
                x, y = entity.dxf.insert.x, entity.dxf.insert.y
                insert_coords.append((x, y))
        
        if not insert_coords:
            return {
                "count": 0,
                "min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0,
                "width": 0, "height": 0
            }
        
        xs, ys = zip(*insert_coords)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        return {
            "count": len(insert_coords),
            "min_x": min_x, "max_x": max_x,
            "min_y": min_y, "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y
        }
    
    def _analyze_block_elements(self, doc) -> Dict[str, Any]:
        """ブロック内要素の分析"""
        all_coords = []
        element_count = 0
        
        # 全ブロック定義を走査
        for block in doc.blocks:
            if not block.name.startswith("*"):  # システムブロックを除外
                for entity in block:
                    element_count += 1
                    # 要素タイプに応じて座標を取得
                    coords = self._extract_entity_coordinates(entity)
                    all_coords.extend(coords)
        
        if not all_coords:
            return {
                "count": 0,
                "min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0,
                "width": 0, "height": 0
            }
        
        xs, ys = zip(*all_coords)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        return {
            "count": element_count,
            "min_x": min_x, "max_x": max_x,
            "min_y": min_y, "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y
        }
    
    def _extract_entity_coordinates(self, entity) -> List[Tuple[float, float]]:
        """エンティティから座標を抽出"""
        coords = []
        entity_type = entity.dxftype()
        
        try:
            if entity_type == "LINE":
                coords.append((entity.dxf.start.x, entity.dxf.start.y))
                coords.append((entity.dxf.end.x, entity.dxf.end.y))
            elif entity_type == "CIRCLE":
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                coords.extend([
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius)
                ])
            elif entity_type == "ARC":
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                coords.extend([
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius)
                ])
            elif entity_type == "LWPOLYLINE":
                for point in entity:
                    coords.append((point[0], point[1]))
            elif entity_type == "POLYLINE":
                for vertex in entity.vertices:
                    coords.append((vertex.dxf.location.x, vertex.dxf.location.y))
            elif entity_type in ["TEXT", "MTEXT"]:
                coords.append((entity.dxf.insert.x, entity.dxf.insert.y))
        except Exception:
            pass  # 座標取得に失敗した場合はスキップ
        
        return coords
    
    def _estimate_unit_systems(self, insert_data: Dict, block_data: Dict) -> Dict[str, str]:
        """単位系の推定"""
        insert_unit = "unknown"
        block_unit = "unknown"
        
        # INSERT座標の単位推定
        if insert_data["width"] > 0:
            if 50 < insert_data["width"] < 2000:  # 50m〜2km範囲
                insert_unit = "m"
            elif 50000 < insert_data["width"] < 2000000:  # 50,000mm〜2,000,000mm
                insert_unit = "mm"
        
        # ブロック内座標の単位推定
        if block_data["width"] > 0:
            if 50 < block_data["width"] < 2000:  # 50m〜2km範囲
                block_unit = "m"
            elif 50000 < block_data["width"] < 2000000:  # 50,000mm〜2,000,000mm
                block_unit = "mm"
            elif 50 < block_data["width"] < 2000:  # 重複チェック（小さめの値はmm可能性）
                if block_data["width"] < 100:
                    block_unit = "mm"
        
        # 一貫性の判定
        if insert_unit == "unknown" or block_unit == "unknown":
            consistency = "unknown"
        elif insert_unit == block_unit:
            consistency = "consistent"
        else:
            consistency = "mixed"
        
        return {
            "insert_unit": insert_unit,
            "block_unit": block_unit,
            "consistency": consistency
        }
    
    def _validate_architectural_drawing(self, insert_w: float, insert_h: float, 
                                      block_w: float, block_h: float) -> Dict[str, str]:
        """建築図面としての妥当性チェック"""
        
        # 推定される実際のサイズ（メートル換算）
        sizes_to_check = []
        
        # INSERT座標ベース
        if insert_w > 0 and insert_h > 0:
            if insert_w < 10:  # 10未満ならmm可能性
                sizes_to_check.append((insert_w * 1000, insert_h * 1000))  # mm→mm変換
            else:
                sizes_to_check.append((insert_w, insert_h))  # m想定
        
        # ブロック座標ベース
        if block_w > 0 and block_h > 0:
            if block_w < 10:  # 10未満ならmm可能性
                sizes_to_check.append((block_w * 1000, block_h * 1000))
            else:
                sizes_to_check.append((block_w, block_h))
        
        # 建築図面としての妥当性をチェック
        for width_m, height_m in sizes_to_check:
            if 5 <= width_m <= 2000 and 5 <= height_m <= 2000:
                # 推奨スケールを決定
                if width_m <= 40 and height_m <= 30:
                    scale = "1:100"
                elif width_m <= 80 and height_m <= 60:
                    scale = "1:200"
                elif width_m <= 200 and height_m <= 150:
                    scale = "1:500"
                elif width_m <= 400 and height_m <= 300:
                    scale = "1:1000"
                elif width_m <= 800 and height_m <= 600:
                    scale = "1:2000"
                else:
                    scale = "1:5000"
                
                return {"status": "valid", "scale": scale}
        
        # サイズが小さすぎる場合
        max_size = max([max(w, h) for w, h in sizes_to_check] or [0])
        if max_size < 5:
            return {"status": "too_small", "scale": "unknown"}
        
        # サイズが大きすぎる場合
        if max_size > 2000:
            return {"status": "too_large", "scale": "1:5000+"}
        
        return {"status": "unknown", "scale": "unknown"}
    
    def _test_conversion(self, file_path: str) -> Dict[str, Any]:
        """SafeDXFConverterでの変換テスト"""
        try:
            # 変換実行
            collection = self.converter.convert_dxf_file(file_path)
            
            # 変換情報を取得
            applied = collection.metadata.get("auto_scaled", False)
            factor = collection.metadata.get("unit_factor_mm", 1.0)
            
            # 最終サイズを計算
            bounds = self.converter._calculate_actual_bounds(collection)
            if bounds:
                final_width = bounds[2] - bounds[0]
                final_height = bounds[3] - bounds[1]
                final_size = (final_width, final_height)
            else:
                final_size = (0, 0)
            
            return {
                "applied": applied,
                "factor": factor,
                "final_size": final_size
            }
            
        except Exception as e:
            self.logger.error(f"Conversion test failed for {file_path}: {e}")
            return {
                "applied": False,
                "factor": 1.0,
                "final_size": (0, 0)
            }
    
    def analyze_batch(self, dxf_dir: str) -> List[UnitAnalysisResult]:
        """バッチ分析の実行"""
        dxf_path = Path(dxf_dir)
        if not dxf_path.exists():
            raise FileNotFoundError(f"Directory not found: {dxf_dir}")
        
        # DXFファイルを取得してソート
        dxf_files = sorted(dxf_path.glob("*.dxf"))
        
        self.logger.info(f"Found {len(dxf_files)} DXF files to analyze")
        
        results = []
        for dxf_file in dxf_files:
            self.logger.info(f"Analyzing: {dxf_file.name}")
            result = self.analyze_file(str(dxf_file))
            results.append(result)
        
        return results
    
    def save_results(self, results: List[UnitAnalysisResult], output_file: str):
        """結果をJSONファイルに保存"""
        output_data = {
            "analysis_metadata": {
                "total_files": len(results),
                "timestamp": str(Path().cwd()),
                "analyzer_version": "1.0"
            },
            "results": [asdict(result) for result in results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Results saved to: {output_file}")
    
    def print_summary(self, results: List[UnitAnalysisResult]):
        """分析結果のサマリーを出力"""
        print("\n" + "="*80)
        print("DXF UNIT ANALYSIS SUMMARY")
        print("="*80)
        
        # 基本統計
        total_files = len(results)
        site_files = len([r for r in results if r.file_type == "敷地図"])
        floor_files = len([r for r in results if r.file_type == "完成図"])
        
        print(f"Total files analyzed: {total_files}")
        print(f"Site plans (敷地図): {site_files}")
        print(f"Floor plans (完成図): {floor_files}")
        
        # INSUNITS分布
        print(f"\nINSUNITS Distribution:")
        insunits_count = {}
        for result in results:
            insunits_count[result.insunits_name] = insunits_count.get(result.insunits_name, 0) + 1
        
        for insunit, count in sorted(insunits_count.items()):
            print(f"  {insunit}: {count} files")
        
        # 単位系一貫性
        print(f"\nUnit Consistency:")
        consistency_count = {}
        for result in results:
            consistency_count[result.unit_consistency] = consistency_count.get(result.unit_consistency, 0) + 1
        
        for consistency, count in sorted(consistency_count.items()):
            print(f"  {consistency}: {count} files")
        
        # サイズ妥当性
        print(f"\nSize Validation:")
        validation_count = {}
        for result in results:
            validation_count[result.size_validation] = validation_count.get(result.size_validation, 0) + 1
        
        for validation, count in sorted(validation_count.items()):
            print(f"  {validation}: {count} files")
        
        # 自動変換適用状況
        auto_converted = len([r for r in results if r.auto_conversion_applied])
        print(f"\nAuto conversion applied: {auto_converted}/{total_files} files")
        
        # エラー・警告
        files_with_errors = len([r for r in results if r.errors])
        files_with_warnings = len([r for r in results if r.warnings])
        
        print(f"\nFiles with errors: {files_with_errors}")
        print(f"Files with warnings: {files_with_warnings}")
        
        print("="*80)


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DXF Batch Unit Analysis Tool')
    parser.add_argument('dxf_dir', help='Directory containing DXF files')
    parser.add_argument('-o', '--output', default='batch_unit_analysis.json',
                       help='Output JSON file (default: batch_unit_analysis.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = BatchUnitAnalyzer()
    
    try:
        # バッチ分析実行
        results = analyzer.analyze_batch(args.dxf_dir)
        
        # 結果保存
        analyzer.save_results(results, args.output)
        
        # サマリー表示
        analyzer.print_summary(results)
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()