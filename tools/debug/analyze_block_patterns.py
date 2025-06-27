#!/usr/bin/env python3
"""
ブロック単位パターン分析ツール
10セットのDXFファイルからブロック名と単位のパターンを学習

Created: 2025-06-28
Purpose: ブロック名ごとの単位パターンを分析・学習
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import statistics
import ezdxf

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class BlockPatternAnalyzer:
    """ブロック単位パターン分析器"""
    
    def __init__(self):
        self.block_patterns = defaultdict(lambda: {
            "occurrences": [],
            "sizes": [],
            "file_types": [],
            "estimated_unit": None,
            "confidence": 0.0
        })
        
    def analyze_dxf_directory(self, dxf_dir: str):
        """DXFディレクトリを分析"""
        dxf_path = Path(dxf_dir)
        dxf_files = sorted(dxf_path.glob("*.dxf"))
        
        print(f"分析対象: {len(dxf_files)} ファイル\n")
        
        # 各ファイルを分析
        for dxf_file in dxf_files:
            self._analyze_file(dxf_file)
        
        # パターンを集計
        self._aggregate_patterns()
        
    def _analyze_file(self, file_path: Path):
        """単一ファイルの分析"""
        try:
            doc = ezdxf.readfile(str(file_path))
            file_type = "敷地図" if file_path.name.endswith("1.dxf") else "完成図"
            
            # ブロック定義を分析
            for block in doc.blocks:
                if block.name.startswith("*"):  # システムブロックを除外
                    continue
                    
                # ブロックのバウンディングボックスを計算
                bbox = self._calculate_block_bbox(block)
                if bbox:
                    min_x, min_y, max_x, max_y = bbox
                    width = max_x - min_x
                    height = max_y - min_y
                    
                    # パターンデータに追加
                    self.block_patterns[block.name]["occurrences"].append(file_path.name)
                    self.block_patterns[block.name]["sizes"].append((width, height))
                    self.block_patterns[block.name]["file_types"].append(file_type)
                    
        except Exception as e:
            print(f"エラー: {file_path.name} - {e}")
    
    def _calculate_block_bbox(self, block) -> Optional[Tuple[float, float, float, float]]:
        """ブロックのバウンディングボックスを計算"""
        points = []
        
        for entity in block:
            try:
                if entity.dxftype() == "LINE":
                    points.extend([(entity.dxf.start.x, entity.dxf.start.y),
                                 (entity.dxf.end.x, entity.dxf.end.y)])
                elif entity.dxftype() == "CIRCLE":
                    center = (entity.dxf.center.x, entity.dxf.center.y)
                    radius = entity.dxf.radius
                    points.extend([
                        (center[0] - radius, center[1] - radius),
                        (center[0] + radius, center[1] + radius)
                    ])
                elif entity.dxftype() == "ARC":
                    center = (entity.dxf.center.x, entity.dxf.center.y)
                    radius = entity.dxf.radius
                    points.extend([
                        (center[0] - radius, center[1] - radius),
                        (center[0] + radius, center[1] + radius)
                    ])
                elif entity.dxftype() == "LWPOLYLINE":
                    for point in entity:
                        points.append((point[0], point[1]))
            except:
                continue
        
        if not points:
            return None
            
        xs, ys = zip(*points)
        return min(xs), min(ys), max(xs), max(ys)
    
    def _estimate_unit(self, sizes: List[Tuple[float, float]]) -> Tuple[str, float]:
        """サイズリストから単位を推定"""
        if not sizes:
            return "unknown", 0.0
            
        # 各サイズの最大寸法を取得
        max_dims = [max(w, h) for w, h in sizes]
        avg_size = statistics.mean(max_dims)
        
        # 単位推定ロジック
        if 0.5 <= avg_size < 10:
            # 0.5-10: メートル（小さな部屋〜建物）
            return "m", 0.9
        elif 10 <= avg_size < 50:
            # 10-50: メートル（建物〜敷地）
            return "m", 0.8
        elif 50 <= avg_size < 500:
            # 50-500: 曖昧な範囲
            if avg_size < 100:
                return "m", 0.6  # 50-100mの建物もありうる
            else:
                return "mm", 0.7  # 100-500mmの部品
        elif 500 <= avg_size < 50000:
            # 500-50000: ミリメートル（0.5m-50m）
            return "mm", 0.9
        elif 50 <= avg_size < 300:
            # 50-300: メートル（大規模施設）
            return "m", 0.85
        else:
            return "unknown", 0.3
    
    def _aggregate_patterns(self):
        """パターンを集計して単位を推定"""
        for block_name, data in self.block_patterns.items():
            if data["sizes"]:
                # 単位を推定
                unit, confidence = self._estimate_unit(data["sizes"])
                data["estimated_unit"] = unit
                data["confidence"] = confidence
                
                # 統計情報を追加
                widths = [w for w, h in data["sizes"]]
                heights = [h for w, h in data["sizes"]]
                
                data["stats"] = {
                    "count": len(data["sizes"]),
                    "avg_width": statistics.mean(widths),
                    "avg_height": statistics.mean(heights),
                    "std_width": statistics.stdev(widths) if len(widths) > 1 else 0,
                    "std_height": statistics.stdev(heights) if len(heights) > 1 else 0,
                    "min_width": min(widths),
                    "max_width": max(widths),
                    "min_height": min(heights),
                    "max_height": max(heights),
                }
    
    def generate_pattern_rules(self) -> Dict[str, str]:
        """パターンルールを生成"""
        rules = {}
        
        # パターンをグループ化
        patterns_by_prefix = defaultdict(list)
        
        for block_name, data in self.block_patterns.items():
            if data["estimated_unit"] and data["confidence"] > 0.7:
                # プレフィックスを抽出
                prefix = self._extract_prefix(block_name)
                patterns_by_prefix[prefix].append({
                    "name": block_name,
                    "unit": data["estimated_unit"],
                    "confidence": data["confidence"]
                })
        
        # プレフィックスごとに最も信頼度の高い単位を選択
        for prefix, patterns in patterns_by_prefix.items():
            # 単位ごとの信頼度を集計
            unit_scores = defaultdict(float)
            for p in patterns:
                unit_scores[p["unit"]] += p["confidence"]
            
            # 最も信頼度の高い単位を選択
            best_unit = max(unit_scores.items(), key=lambda x: x[1])
            rules[f"{prefix}*"] = best_unit[0]
        
        return rules
    
    def _extract_prefix(self, block_name: str) -> str:
        """ブロック名からプレフィックスを抽出"""
        # 数字や記号で区切られた最初の部分を取得
        match = re.match(r'^([A-Za-z_]+)', block_name)
        if match:
            return match.group(1)
        
        # %や数字の前まで
        match = re.match(r'^([^%\d]+)', block_name)
        if match:
            return match.group(1)
            
        return block_name
    
    def save_results(self, output_file: str):
        """結果を保存"""
        output_data = {
            "block_patterns": dict(self.block_patterns),
            "pattern_rules": self.generate_pattern_rules(),
            "summary": self._generate_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n結果を保存: {output_file}")
    
    def _generate_summary(self) -> Dict:
        """サマリー情報を生成"""
        total_blocks = len(self.block_patterns)
        unit_counts = defaultdict(int)
        high_confidence = 0
        
        for data in self.block_patterns.values():
            if data["estimated_unit"]:
                unit_counts[data["estimated_unit"]] += 1
                if data["confidence"] > 0.8:
                    high_confidence += 1
        
        return {
            "total_unique_blocks": total_blocks,
            "unit_distribution": dict(unit_counts),
            "high_confidence_blocks": high_confidence,
            "confidence_threshold": 0.8
        }
    
    def print_report(self):
        """分析レポートを出力"""
        print("\n" + "="*80)
        print("ブロック単位パターン分析レポート")
        print("="*80)
        
        # パターンルール
        rules = self.generate_pattern_rules()
        print(f"\n検出されたパターンルール（{len(rules)}個）:")
        for pattern, unit in sorted(rules.items()):
            print(f"  {pattern:<20} → {unit}")
        
        # 信頼度の高いブロック
        print(f"\n信頼度の高いブロック（信頼度 > 0.8）:")
        high_conf_blocks = [(name, data) for name, data in self.block_patterns.items() 
                           if data["confidence"] > 0.8]
        
        for name, data in sorted(high_conf_blocks, key=lambda x: x[1]["confidence"], reverse=True)[:10]:
            stats = data.get("stats", {})
            print(f"\n  {name}:")
            print(f"    推定単位: {data['estimated_unit']}")
            print(f"    信頼度: {data['confidence']:.2f}")
            print(f"    出現回数: {stats.get('count', 0)}")
            print(f"    平均サイズ: {stats.get('avg_width', 0):.1f} × {stats.get('avg_height', 0):.1f}")
        
        # サマリー
        summary = self._generate_summary()
        print(f"\n総括:")
        print(f"  ユニークブロック数: {summary['total_unique_blocks']}")
        print(f"  単位分布: {summary['unit_distribution']}")
        print(f"  高信頼度ブロック: {summary['high_confidence_blocks']}")
        
        print("="*80)


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DXF Block Pattern Analyzer')
    parser.add_argument('dxf_dir', help='Directory containing DXF files')
    parser.add_argument('-o', '--output', default='block_patterns.json',
                       help='Output JSON file')
    
    args = parser.parse_args()
    
    analyzer = BlockPatternAnalyzer()
    analyzer.analyze_dxf_directory(args.dxf_dir)
    analyzer.print_report()
    analyzer.save_results(args.output)


if __name__ == "__main__":
    main()
