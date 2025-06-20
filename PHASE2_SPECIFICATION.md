# Phase 2: 差分解析エンジン + 可視化システム実装指示書

## プロジェクト概要

### Phase 2 目標
敷地図と間取り図の差分を抽出し、新規追加された建築要素（壁、開口部、設備）を自動検出する差分解析エンジンを開発する。加えて、検出結果を視覚的に確認できる可視化システムを実装する。

### 拡張された成果物
- **統一データ構造**: DXF・PDF両対応の中間表現
- **差分抽出エンジン**: 座標ベースの要素比較アルゴリズム
- **可視化システム**: matplotlib/Plotlyを使った差分の視覚的表示
- **包括的ドキュメント**: 日英対応README + セットアップガイド

## システム要件

### 技術スタック（追加）
```
matplotlib>=3.7.0     # 2D可視化
plotly>=5.15.0        # インタラクティブ可視化（推奨）
seaborn>=0.12.0       # 美しい可視化スタイル
```

### Phase 2 実装内容

## 1. 統一データ構造設計

### 1.1 GeometryData クラス
```python
# src/data_structures/geometry_data.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class ElementType(Enum):
    WALL = "wall"
    OPENING = "opening" 
    TEXT = "text"
    EQUIPMENT = "equipment"
    DIMENSION = "dimension"
    UNKNOWN = "unknown"

@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0
    
    def distance_to(self, other: 'Point') -> float:
        """他の点との距離を計算"""
        pass

@dataclass
class Line:
    start: Point
    end: Point
    layer: str
    color: Optional[int] = None
    line_type: str = "Continuous"
    
    def length(self) -> float:
        """線分の長さを計算"""
        pass
    
    def angle(self) -> float:
        """線分の角度を計算（度）"""
        pass

@dataclass
class Text:
    content: str
    position: Point
    height: float
    font: str = ""
    layer: str = "0"

@dataclass
class GeometryElement:
    element_type: ElementType
    geometry: Any  # Line, Text, etc.
    properties: Dict[str, Any]
    source_file: str
    
class GeometryData:
    """DXF・PDF両対応の統一データ構造"""
    
    def __init__(self):
        self.lines: List[Line] = []
        self.texts: List[Text] = []
        self.elements: List[GeometryElement] = []
        self.bounds: Tuple[float, float, float, float] = (0, 0, 0, 0)
        self.metadata: Dict[str, Any] = {}
    
    def add_line(self, line: Line) -> None:
        """線分を追加"""
        pass
    
    def add_text(self, text: Text) -> None:
        """テキストを追加"""
        pass
    
    def get_elements_by_type(self, element_type: ElementType) -> List[GeometryElement]:
        """指定タイプの要素を取得"""
        pass
    
    def calculate_bounds(self) -> Tuple[float, float, float, float]:
        """境界ボックスを計算"""
        pass
    
    def to_grid_coordinates(self, grid_size: float = 910.0) -> 'GeometryData':
        """910mmグリッド座標系に変換"""
        pass
```

### 1.2 変換モジュール
```python
# src/data_structures/converters.py

def dxf_to_geometry_data(dxf_analysis: Dict[str, Any]) -> GeometryData:
    """DXF解析結果をGeometryDataに変換"""
    pass

def pdf_to_geometry_data(pdf_analysis: Dict[str, Any]) -> GeometryData:
    """PDF解析結果をGeometryDataに変換"""
    pass
```

## 2. 差分解析エンジン

### 2.1 コア差分抽出
```python
# src/engines/difference_engine.py

from typing import List, Tuple
from ..data_structures.geometry_data import GeometryData, GeometryElement

class DifferenceEngine:
    """敷地図と間取り図の差分を抽出するエンジン"""
    
    def __init__(self, tolerance: float = 1.0):
        self.tolerance = tolerance  # mm単位での許容誤差
    
    def extract_differences(self, 
                          site_data: GeometryData, 
                          complete_data: GeometryData) -> GeometryData:
        """
        2つのファイルから差分を抽出
        
        Args:
            site_data: 敷地図のジオメトリデータ
            complete_data: 完成形のジオメトリデータ
            
        Returns:
            新規追加された要素のみを含むGeometryData
        """
        pass
    
    def find_new_lines(self, site_lines: List, complete_lines: List) -> List:
        """新規追加された線分を検出"""
        pass
    
    def classify_building_elements(self, diff_data: GeometryData) -> GeometryData:
        """
        差分要素を建築要素として分類
        - 壁の検出（連続する長い線分）
        - 開口部の検出（壁の切断箇所）
        - 設備の検出（ブロック、特定形状）
        """
        pass
    
    def detect_walls(self, lines: List) -> List[GeometryElement]:
        """壁を検出するアルゴリズム"""
        pass
    
    def detect_openings(self, walls: List, all_elements: List) -> List[GeometryElement]:
        """開口部を検出するアルゴリズム"""
        pass
    
    def detect_equipment(self, elements: List) -> List[GeometryElement]:
        """設備・階段等を検出するアルゴリズム"""
        pass
```

### 2.2 座標マッチングアルゴリズム
```python
# src/engines/coordinate_matcher.py

class CoordinateMatcher:
    """座標ベースの要素マッチング"""
    
    def __init__(self, tolerance: float = 1.0):
        self.tolerance = tolerance
    
    def points_are_equal(self, p1: Point, p2: Point) -> bool:
        """2点が同一かどうかを判定（許容誤差内）"""
        pass
    
    def lines_are_equal(self, l1: Line, l2: Line) -> bool:
        """2つの線分が同一かどうかを判定"""
        pass
    
    def find_matching_elements(self, elements1: List, elements2: List) -> Tuple[List, List]:
        """
        2つの要素リストから一致する要素と差分要素を抽出
        
        Returns:
            Tuple[matching_elements, unique_elements]
        """
        pass
```

## 3. 可視化システム

### 3.1 2D可視化エンジン
```python
# src/visualization/plotter.py

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class GeometryPlotter:
    """ジオメトリデータの可視化"""
    
    def __init__(self, figure_size: Tuple[int, int] = (12, 8)):
        self.figure_size = figure_size
        self.colors = {
            'site': '#2E86AB',      # 敷地図（青）
            'new_wall': '#A23B72',   # 新規壁（紫）
            'opening': '#F18F01',    # 開口部（オレンジ）
            'equipment': '#C73E1D',  # 設備（赤）
            'text': '#4A5D23'       # テキスト（緑）
        }
    
    def plot_comparison(self, 
                       site_data: GeometryData,
                       complete_data: GeometryData,
                       diff_data: GeometryData,
                       output_path: str = "comparison.png") -> None:
        """
        敷地図、完成形、差分の比較表示
        """
        pass
    
    def plot_difference_only(self, 
                           diff_data: GeometryData,
                           output_path: str = "difference.png") -> None:
        """
        差分のみを表示
        """
        pass
    
    def create_interactive_plot(self, 
                              site_data: GeometryData,
                              diff_data: GeometryData) -> go.Figure:
        """
        Plotlyを使ったインタラクティブな可視化
        """
        pass
    
    def _draw_lines(self, ax, lines: List[Line], color: str, label: str) -> None:
        """線分を描画"""
        pass
    
    def _draw_texts(self, ax, texts: List[Text], color: str) -> None:
        """テキストを描画"""
        pass
    
    def _draw_walls(self, ax, walls: List[GeometryElement]) -> None:
        """壁を強調表示"""
        pass
    
    def _draw_openings(self, ax, openings: List[GeometryElement]) -> None:
        """開口部を描画"""
        pass
```

### 3.2 可視化ユーティリティ
```python
# src/visualization/utils.py

def save_comparison_report(site_data: GeometryData,
                          complete_data: GeometryData, 
                          diff_data: GeometryData,
                          output_dir: str) -> None:
    """
    比較レポートを生成
    - 統計情報のテキストファイル
    - 可視化画像
    - HTMLレポート
    """
    pass

def create_html_report(analysis_results: Dict[str, Any], 
                      image_paths: List[str],
                      output_path: str) -> None:
    """HTMLレポートを生成"""
    pass
```

## 4. 統合・テスト

### 4.1 統合テスト
```python
# tests/integration_tests/test_phase2_integration.py

class TestPhase2Integration:
    """Phase 2統合テスト"""
    
    def test_full_difference_pipeline(self):
        """完全な差分抽出パイプラインのテスト"""
        pass
    
    def test_wall_detection_accuracy(self):
        """壁検出精度のテスト"""
        pass
    
    def test_visualization_output(self):
        """可視化出力のテスト"""
        pass
    
    def test_grid_conversion_accuracy(self):
        """910mmグリッド変換精度のテスト"""
        pass
```

### 4.2 パフォーマンステスト
```python
# tests/performance/test_performance.py

def test_large_file_processing():
    """大容量ファイルの処理性能テスト"""
    pass

def test_difference_extraction_speed():
    """差分抽出の処理速度テスト"""
    pass
```

## 5. メインアプリケーション

### 5.1 統合CLI
```python
# src/main.py

import argparse
from .analyzers.dxf_analyzer import analyze_dxf_structure
from .analyzers.pdf_analyzer import analyze_pdf_structure
from .data_structures.converters import dxf_to_geometry_data, pdf_to_geometry_data
from .engines.difference_engine import DifferenceEngine
from .visualization.plotter import GeometryPlotter

def main():
    parser = argparse.ArgumentParser(description='建築図面差分解析システム')
    parser.add_argument('site_file', help='敷地図ファイル (.dxf or .pdf)')
    parser.add_argument('complete_file', help='完成形ファイル (.dxf or .pdf)')
    parser.add_argument('--output-dir', default='output', help='出力ディレクトリ')
    parser.add_argument('--tolerance', type=float, default=1.0, help='座標許容誤差(mm)')
    parser.add_argument('--visualize', action='store_true', help='可視化を実行')
    parser.add_argument('--interactive', action='store_true', help='インタラクティブ表示')
    
    args = parser.parse_args()
    
    # ファイル解析 → データ変換 → 差分抽出 → 可視化
    print("Phase 2: 差分解析エンジン実行中...")
    
    # 実装詳細は開発チームが作成

if __name__ == "__main__":
    main()
```

## 品質要件

### 精度要件
- **座標精度**: ±1mm以内（Phase 1と同等）
- **差分検出精度**: 95%以上（手動検証との比較）
- **壁検出精度**: 90%以上
- **開口部検出精度**: 85%以上

### パフォーマンス要件
- **差分抽出処理**: < 10秒（通常サイズファイル）
- **可視化生成**: < 15秒
- **メモリ使用量**: < 500MB

### コード品質要件
- **テストカバレッジ**: 80%以上（Phase 1の50%から向上）
- **Type hints**: 100%適用
- **Docstring**: 全public関数に適用
- **Black formatter**: 適用済み

## 成果物チェックリスト

### コア機能
- [ ] `src/data_structures/geometry_data.py` - 統一データ構造
- [ ] `src/data_structures/converters.py` - DXF/PDF変換器
- [ ] `src/engines/difference_engine.py` - 差分抽出エンジン
- [ ] `src/engines/coordinate_matcher.py` - 座標マッチング
- [ ] `src/visualization/plotter.py` - 可視化エンジン
- [ ] `src/visualization/utils.py` - 可視化ユーティリティ

### テスト
- [ ] `tests/test_engines/` - エンジンテスト
- [ ] `tests/integration_tests/` - 統合テスト
- [ ] `tests/performance/` - パフォーマンステスト

### 出力例
- [ ] `output/comparison_visualization.png` - 比較可視化
- [ ] `output/difference_only.png` - 差分のみ表示
- [ ] `output/interactive_plot.html` - インタラクティブ表示
- [ ] `output/analysis_report.html` - HTMLレポート
- [ ] `output/difference_data.json` - 差分データJSON

### ドキュメント
- [ ] 日英対応README
- [ ] セットアップガイド
- [ ] 実行コマンドガイド
- [ ] API仕様書

## 開発スケジュール

### Week 1 (1/20-1/24)
- 統一データ構造の設計・実装
- DXF/PDF変換器の実装
- 基本的な差分抽出アルゴリズム

### Week 2 (1/27-1/31)
- 建築要素分類アルゴリズム
- 可視化システムの実装
- 基本テストの作成

### Week 3 (2/3-2/7)
- 統合テスト・パフォーマンステスト
- ドキュメント整備
- 最終調整・バグ修正

## 注意事項

### 座標系の統一
- DXFとPDFの座標系違いに注意
- 必ず910mmグリッドでの正規化を実装
- 回転・スケール変換への対応

### 建築要素の分類ロジック
- 壁: 連続する直線、一定以上の長さ
- 開口部: 壁の切断箇所、矩形状の空間
- 設備: ブロック参照、特定の記号パターン

### 可視化の要件
- カラーコードの統一
- 凡例の自動生成
- ズーム・パン機能（インタラクティブ）

---

**開発チーム**: この仕様に従ってPhase 2の実装を開始してください。質問があれば随時相談してください。特に建築要素の分類ロジックについては、実際の図面を見ながら調整が必要になる可能性があります。
