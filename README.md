# 建築図面差分解析システム

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](./tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 概要
DXF・PDF形式の建築図面を解析し、以下の機能を提供するシステム：
- **DXF→PDF変換**: CAD標準（A3サイズ、縮尺指定）でのPDF出力
- **差分解析**: 敷地図と完成形図面の差分を検出し、建築要素を分類
- **可視化**: 解析結果の視覚的表示

## 主な機能
✅ **DXF→PDF変換** - スマート単位変換、A3サイズ出力  
✅ **差分解析エンジン** - 壁・開口部・設備の自動分類  
✅ **統合CLIツール** - 全機能を一つのコマンドで実行  
📋 **JSON変換** - FreeCAD互換フォーマット（今後実装予定）

## クイックスタート

```bash
# 依存関係インストール
pip install -r requirements.txt

# DXF→PDF変換（A3サイズ、1:100スケール）
python src/main.py dxf2pdf input.dxf --scale 1:100

# 差分解析（敷地図と完成形の比較）
python src/main.py diff site.dxf floor.dxf

# バッチ変換（フォルダ内の全DXFファイル）
python src/main.py batch /path/to/dxf/files/
```

## セットアップ

### 1. リポジトリクローン
```bash
git clone <repository-url>
cd architectural_json_converter
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. 動作確認
```bash
# テスト実行
pytest tests/ -v

# サンプル解析実行
python src/analyzers/dxf_analyzer.py data/sample_dxf/test.dxf
```

### 4. 開発環境設定（開発者向け）
```bash
# コードフォーマット
black src/ tests/

# 型チェック
mypy src/

# テスト（カバレッジ付き）
pytest tests/ --cov=src/ --cov-report=html
```

## プロジェクト構造
```
architectural_json_converter/
├── src/                    # メインソースコード
│   ├── analyzers/         # DXF・PDF解析モジュール
│   ├── data_structures/   # データ構造定義
│   ├── engines/           # 変換・差分解析エンジン
│   ├── visualization/     # PDF生成・可視化
│   └── main.py           # 統合CLIアプリケーション
├── tests/                 # テストコード
├── tools/debug/           # デバッグ・分析ツール
├── sample_data/           # サンプルファイル
├── output/                # 出力ディレクトリ
└── _docs/                 # 実装ドキュメント
```

## 技術的特徴

### スマート単位変換
- DXFファイルの単位系を自動検出（メートル/ミリメートル混在対応）
- A3サイズと縮尺から逆算して建築図面の妥当性をチェック
- 5m〜2kmの範囲を建築物として妥当と判定
- **NEW**: ブロックパターン学習による高精度単位推定

### CAD標準準拠
- A3サイズ（420×297mm）での出力
- 標準縮尺対応（1:50、1:100、1:200、1:500、1:1000、1:2000、1:5000）
- 図面枠・スケール表示付き

### 高精度差分解析
- Shapely使用による正確な幾何演算
- 建築要素の自動分類（壁、開口部、設備）
- 日本語レイヤー名対応

## ドキュメント
- [最新実装状況](_docs/)
- [Claude向けガイドライン](CLAUDE.md)

## 技術的な課題

### DXF単位系の混在
一部のDXFファイルでINSERT座標（メートル）とブロック内容（ミリメートル）が混在するケースがあります。[高度なブロックパターン分析](_docs/2025-06-28_advanced_block_pattern_analysis.md)により、データドリブンな単位推定を実現しました。詳細は[単位系混在分析](_docs/2025-06-28_mixed_units_analysis.md)も参照。

### 差分解析の精度
敷地図と完成図の差分解析により、新規追加された建築要素を高精度で検出・分類できます。詳細は[差分解析評価](_docs/2025-06-28_dxf_comprehensive_analysis.md)を参照。

## 使用技術
- **解析**: ezdxf (DXF), PyMuPDF (PDF)
- **数値計算**: numpy, shapely
- **可視化**: matplotlib
- **品質管理**: pytest, black, mypy
- **データ検証**: pydantic

## ライセンス
MIT License
