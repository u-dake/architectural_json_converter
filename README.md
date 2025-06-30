# Architectural CAD Analyzer

建築図面（DXF）の差分分析、単位検出、可視化を統合したツール

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](./tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 概要

このシステムは、建築CADファイル（DXF形式）を分析し、以下の機能を提供します：

- 🔍 **差分分析**: 敷地図と完成図の違いを視覚的に表示
- 📊 **単位検出**: ブロックごとの単位（mm/m）を自動検出
- 📄 **多形式出力**: PDF（視覚化）とJSON（構造化データ）での出力
- 🤖 **LLM対応**: 構造化されたJSONデータでAIへの情報提供が可能

## クイックスタート

### 統合ツールの使用

```bash
# すべての分析を実行
./cad_analyzer.py analyze-all sample_data -o outputs

# 個別の差分分析
./cad_analyzer.py diff sample_data/buildings/01/site_plan/01_敷地図.dxf \
                       sample_data/buildings/01/floor_plan/01_完成形.dxf

# バッチ処理
./cad_analyzer.py batch sample_data -o outputs/differences
```

## 主要機能

### 1. DXF差分分析

2つのDXFファイル（敷地図と完成図）を比較し、4パネルのPDFを生成：
- サイトプランのみ
- フロアプランのみ
- 重ね合わせ表示
- 差分強調表示

```bash
./cad_analyzer.py diff site.dxf floor.dxf -o diff.pdf
```

### 2. ブロックパターン分析

DXFファイル内のブロックを分析し、単位を自動検出：

```bash
./cad_analyzer.py patterns sample_data -o block_patterns.json
```

出力例：
```json
{
  "FcPack%d2": {
    "estimated_unit": "mm",
    "confidence": 0.95,
    "is_fixed_size": true,
    "sizes": [[400.0, 277.0]]
  }
}
```

### 3. DXF→JSON変換

DXFファイルの構造をJSON形式で出力：

```bash
./cad_analyzer.py convert drawing.dxf -o structure.json
```

## システムアーキテクチャ

```
architectural_json_converter/
├── cad_analyzer.py         # 統合コマンドラインツール
├── src/
│   ├── analyzers/          # 解析モジュール
│   │   ├── dxf_analyzer.py    # DXF構造解析
│   │   └── unit_detector.py   # 統合単位検出システム
│   ├── engines/            # 変換エンジン
│   │   ├── safe_dxf_converter.py  # スマート単位変換
│   │   └── difference_engine.py   # 差分抽出
│   ├── data_structures/    # データ構造
│   │   └── simple_geometry.py     # ジオメトリ定義
│   └── visualization/      # 可視化
│       └── geometry_plotter.py    # 共通描画機能
├── tools/                  # 個別ツール
│   ├── visualize_dxf_diff.py     # 差分視覚化
│   └── dxf_to_json.py            # JSON変換
└── sample_data/           # サンプルデータ
    └── buildings/         # 10棟の建物データ
```

## 技術的特徴

### スマート単位検出

3つの検出方法を組み合わせた高精度な単位判定：
1. **ヘッダー検出**: DXFファイルの$INSUNITS変数
2. **パターン検出**: `block_patterns_advanced.json`による学習済みパターン
3. **サイズ検出**: 建築図面として妥当なサイズからの推定

### 混合単位問題への対応

- INSERT座標（ブロック配置）とブロック内容で異なる単位を使用するケースに対応
- コンテキスト（敷地図/完成図）に応じた単位判定

## インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 実行権限の付与
chmod +x cad_analyzer.py
```

## 必要なライブラリ

- `ezdxf`: DXFファイルの読み書き
- `matplotlib`: PDF生成と可視化
- `numpy`: 数値計算
- `shapely`: 幾何学的操作（オプション）

## 使用例

### 完全分析の実行

```bash
./cad_analyzer.py analyze-all sample_data -o outputs
```

これにより以下が生成されます：
- `outputs/differences/`: 各建物の差分PDF/JSON
- `outputs/json_samples/`: サンプルJSON変換
- `block_patterns_advanced.json`: ブロックパターン分析結果

### 特定の建物の分析

```bash
# 建物01の差分を分析
./cad_analyzer.py diff \
  sample_data/buildings/01/site_plan/01_敷地図.dxf \
  sample_data/buildings/01/floor_plan/01_完成形.dxf \
  -o building01_diff.pdf
```

## 開発者向け情報

### テスト実行

```bash
pytest tests/
```

### コード品質

```bash
# フォーマット
black src/ tests/

# 型チェック
mypy src/
```

## ドキュメント

詳細な実装については以下を参照：
- `_docs/2025-06-28_mixed_units_analysis.md`: 混合単位問題の詳細
- `_docs/2025-06-28_advanced_block_pattern_analysis.md`: ブロックパターン分析
- `CLAUDE.md`: Claude Code向けのプロジェクトガイド

## ライセンス

MIT License