"""
統一単位検出システム

DXFファイルの単位を自動検出し、適切な変換係数を提供する
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import ezdxf
from ezdxf.entities import Insert, Block
from ezdxf.document import Drawing
import numpy as np


@dataclass
class UnitDetectionResult:
    """単位検出結果"""
    unit_factor: float
    confidence: float
    detection_method: str  # "header", "pattern", "size_based", "default"
    details: Dict[str, Any]


class UnitDetector:
    """統一単位検出システム
    
    DXFファイルから単位を自動検出し、適切な変換係数を提供する。
    複数の検出方法を組み合わせて、最も信頼性の高い結果を返す。
    """
    
    def __init__(self, pattern_file: Optional[str] = None):
        """
        Args:
            pattern_file: ブロックパターン分析結果のJSONファイル
        """
        self.pattern_file = pattern_file or self._find_pattern_file()
        self.block_patterns = self._load_block_patterns()
        
        # 標準的な建築図面のサイズ範囲（mm単位）
        self.ARCHITECTURAL_SIZE_RANGE = {
            "min": 5000,      # 5m
            "max": 2000000    # 2km
        }
        
        # A3用紙と標準縮尺での有効範囲
        self.A3_VALID_SCALES = {
            "1:50": (14.85, 21.0),
            "1:100": (29.7, 42.0),
            "1:200": (59.4, 84.0),
            "1:300": (89.1, 126.0),
            "1:400": (118.8, 168.0),
            "1:500": (148.5, 210.0),
            "1:600": (178.2, 252.0),
            "1:1000": (297.0, 420.0),
            "1:1500": (445.5, 630.0),
            "1:2000": (594.0, 840.0),
            "1:2500": (742.5, 1050.0),
            "1:3000": (891.0, 1260.0),
            "1:5000": (1485.0, 2100.0)
        }
    
    def _find_pattern_file(self) -> str:
        """ブロックパターンファイルを検索"""
        # プロジェクトルートから検索
        current = Path(__file__).parent
        while current.parent != current:
            pattern_path = current / "block_patterns_advanced.json"
            if pattern_path.exists():
                return str(pattern_path)
            current = current.parent
        
        # デフォルトパス
        return "block_patterns_advanced.json"
    
    def _load_block_patterns(self) -> Dict[str, Any]:
        """ブロックパターンを読み込む"""
        if not os.path.exists(self.pattern_file):
            return {}
        
        try:
            with open(self.pattern_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('analysis_results', {})
        except Exception as e:
            print(f"ブロックパターン読み込みエラー: {e}")
            return {}
    
    def detect_from_header(self, doc: Drawing) -> Optional[float]:
        """DXFヘッダーから単位を検出
        
        Returns:
            単位変換係数（メートル→ミリメートル）、検出できない場合はNone
        """
        try:
            # $INSUNITSヘッダー変数をチェック
            insunits = doc.header.get('$INSUNITS', 0)
            
            # 単位コードから変換係数へのマッピング
            unit_factors = {
                0: None,     # 単位なし
                1: 25.4,     # インチ→mm
                2: 304.8,    # フィート→mm
                3: 1609344,  # マイル→mm
                4: 1.0,      # ミリメートル（変換不要）
                5: 10.0,     # センチメートル→mm
                6: 1000.0,   # メートル→mm
                7: 1000000,  # キロメートル→mm
                8: 25.4/1000000,    # マイクロインチ→mm
                9: 0.001,    # ミル（1/1000インチ）→mm
                10: 914.4,   # ヤード→mm
                11: 0.0000254,      # オングストローム→mm
                12: 0.000001,       # ナノメートル→mm
                13: 0.001,   # ミクロン→mm
                14: 100.0,   # デシメートル→mm
                15: 10000.0, # デカメートル→mm
                16: 100000.0,        # ヘクトメートル→mm
                17: 1000000000000.0, # ギガメートル→mm
                18: 149597870700000.0, # 天文単位→mm
                19: 9460730472580800000.0, # 光年→mm
                20: 30856775814671900000.0, # パーセク→mm
            }
            
            return unit_factors.get(insunits)
            
        except Exception:
            return None
    
    def detect_from_patterns(self, doc: Drawing, file_type: str = "unknown") -> UnitDetectionResult:
        """ブロックパターンから単位を検出
        
        Args:
            doc: DXFドキュメント
            file_type: ファイルタイプ（"敷地図", "完成図", "unknown"）
            
        Returns:
            単位検出結果
        """
        if not self.block_patterns:
            return None
        
        # ブロックを収集
        block_votes = []
        msp = doc.modelspace()
        
        for insert in msp.query('INSERT'):
            block_name = insert.dxf.name
            if block_name in self.block_patterns:
                pattern = self.block_patterns[block_name]
                
                # コンテキスト別単位を確認
                if file_type in pattern.get('context_units', {}):
                    unit = pattern['context_units'][file_type]
                else:
                    unit = pattern.get('estimated_unit', 'mm')
                
                confidence = pattern.get('confidence', 0.5)
                
                # 単位をファクターに変換
                factor = 1000.0 if unit == 'm' else 1.0
                block_votes.append((factor, confidence))
        
        if not block_votes:
            return None
        
        # 信頼度加重平均で最終的な単位を決定
        total_weight = sum(conf for _, conf in block_votes)
        if total_weight > 0:
            weighted_factor = sum(factor * conf for factor, conf in block_votes) / total_weight
            avg_confidence = total_weight / len(block_votes)
            
            # 最も近い標準的な変換係数に丸める
            if weighted_factor > 500:
                final_factor = 1000.0  # メートル
            else:
                final_factor = 1.0     # ミリメートル
            
            return UnitDetectionResult(
                unit_factor=final_factor,
                confidence=avg_confidence,
                detection_method="pattern",
                details={
                    "block_count": len(block_votes),
                    "weighted_factor": weighted_factor,
                    "file_type": file_type
                }
            )
        
        return None
    
    def detect_from_size(self, doc: Drawing) -> UnitDetectionResult:
        """図面サイズから単位を推定
        
        Returns:
            単位検出結果
        """
        try:
            # モデル空間の境界を取得
            msp = doc.modelspace()
            
            # INSERT座標から境界を計算
            insert_bounds = self._calculate_insert_bounds(msp)
            if insert_bounds:
                min_x, min_y, max_x, max_y = insert_bounds
                width = max_x - min_x
                height = max_y - min_y
                
                # 建築図面として妥当なサイズかチェック
                if self._is_valid_architectural_size(width, height, 1.0):
                    return UnitDetectionResult(
                        unit_factor=1.0,
                        confidence=0.8,
                        detection_method="size_based",
                        details={"size": (width, height), "unit": "mm"}
                    )
                elif self._is_valid_architectural_size(width * 1000, height * 1000, 1.0):
                    return UnitDetectionResult(
                        unit_factor=1000.0,
                        confidence=0.8,
                        detection_method="size_based",
                        details={"size": (width, height), "unit": "m"}
                    )
            
            # エンティティ全体から境界を計算
            entity_bounds = self._calculate_entity_bounds(doc)
            if entity_bounds:
                min_x, min_y, max_x, max_y = entity_bounds
                width = max_x - min_x
                height = max_y - min_y
                
                if self._is_valid_architectural_size(width, height, 1.0):
                    return UnitDetectionResult(
                        unit_factor=1.0,
                        confidence=0.6,
                        detection_method="size_based",
                        details={"size": (width, height), "unit": "mm", "source": "entities"}
                    )
                elif self._is_valid_architectural_size(width * 1000, height * 1000, 1.0):
                    return UnitDetectionResult(
                        unit_factor=1000.0,
                        confidence=0.6,
                        detection_method="size_based",
                        details={"size": (width, height), "unit": "m", "source": "entities"}
                    )
            
        except Exception as e:
            print(f"サイズベース検出エラー: {e}")
        
        return None
    
    def _calculate_insert_bounds(self, msp) -> Optional[Tuple[float, float, float, float]]:
        """INSERT要素から境界を計算"""
        inserts = list(msp.query('INSERT'))
        if not inserts:
            return None
        
        x_coords = [insert.dxf.insert.x for insert in inserts]
        y_coords = [insert.dxf.insert.y for insert in inserts]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def _calculate_entity_bounds(self, doc: Drawing) -> Optional[Tuple[float, float, float, float]]:
        """全エンティティから境界を計算"""
        msp = doc.modelspace()
        points = []
        
        for entity in msp:
            if entity.dxftype() == 'LINE':
                points.extend([(entity.dxf.start.x, entity.dxf.start.y),
                             (entity.dxf.end.x, entity.dxf.end.y)])
            elif entity.dxftype() == 'CIRCLE':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                points.extend([
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius)
                ])
            # 他のエンティティタイプも必要に応じて追加
        
        if not points:
            return None
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def _is_valid_architectural_size(self, width: float, height: float, factor: float) -> bool:
        """建築図面として妥当なサイズかチェック"""
        # 変換後のサイズ（mm単位）
        width_mm = width * factor
        height_mm = height * factor
        
        # 建築図面の妥当な範囲内かチェック
        size_ok = (self.ARCHITECTURAL_SIZE_RANGE["min"] <= width_mm <= self.ARCHITECTURAL_SIZE_RANGE["max"] and
                   self.ARCHITECTURAL_SIZE_RANGE["min"] <= height_mm <= self.ARCHITECTURAL_SIZE_RANGE["max"])
        
        if not size_ok:
            return False
        
        # A3用紙に収まる縮尺があるかチェック
        for scale, (max_width_m, max_height_m) in self.A3_VALID_SCALES.items():
            if (width_mm <= max_width_m * 1000 and height_mm <= max_height_m * 1000):
                return True
        
        return False
    
    def get_recommended_unit_factor(self, doc: Drawing, file_path: str = None) -> UnitDetectionResult:
        """推奨される単位変換係数を取得
        
        複数の検出方法を組み合わせて、最も信頼性の高い結果を返す。
        
        Args:
            doc: DXFドキュメント
            file_path: ファイルパス（ファイルタイプの判定用）
            
        Returns:
            単位検出結果
        """
        # ファイルタイプを判定
        file_type = "unknown"
        if file_path:
            if "site_plan" in file_path or "敷地図" in Path(file_path).name:
                file_type = "敷地図"
            elif "floor_plan" in file_path or "完成形" in Path(file_path).name:
                file_type = "完成図"
        
        results = []
        
        # 1. ヘッダーから検出
        header_factor = self.detect_from_header(doc)
        if header_factor is not None:
            results.append(UnitDetectionResult(
                unit_factor=header_factor,
                confidence=0.9,
                detection_method="header",
                details={"source": "$INSUNITS"}
            ))
        
        # 2. パターンから検出
        pattern_result = self.detect_from_patterns(doc, file_type)
        if pattern_result:
            results.append(pattern_result)
        
        # 3. サイズから検出
        size_result = self.detect_from_size(doc)
        if size_result:
            results.append(size_result)
        
        # 最も信頼度の高い結果を選択
        if results:
            best_result = max(results, key=lambda r: r.confidence)
            return best_result
        
        # デフォルト（ミリメートル）
        return UnitDetectionResult(
            unit_factor=1.0,
            confidence=0.3,
            detection_method="default",
            details={"reason": "No reliable detection method succeeded"}
        )