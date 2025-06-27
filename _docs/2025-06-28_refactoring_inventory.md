# プロジェクト整理・リファクタリング調査報告書

作成日: 2025-06-28
作成者: Claude

## 1. 機能インベントリマップ

### 1.1 コアモジュール構成

```
architectural_json_converter/
├── src/
│   ├── analyzers/        # Phase 1: ファイル解析
│   │   ├── dxf_analyzer.py     [ACTIVE] DXF構造解析・JSON出力
│   │   └── pdf_analyzer.py     [ACTIVE] PDF構造解析・JSON出力
│   ├── engines/          # Phase 2: データ変換・差分解析
│   │   ├── safe_dxf_converter.py  [ACTIVE] DXF→幾何変換（Matrix44回避）
│   │   ├── dxf_converter.py       [ACTIVE] DXF→統一データ構造
│   │   ├── pdf_converter.py       [ACTIVE] PDF→統一データ構造
│   │   └── difference_engine.py   [ACTIVE] 差分解析・建築要素分類
│   ├── visualization/    # 可視化・PDF出力
│   │   ├── cad_standard_visualizer.py [ACTIVE] A3/CADスケール準拠PDF
│   │   ├── safe_pdf_visualizer.py     [ACTIVE] エラー回避PDF生成
│   │   ├── matplotlib_visualizer.py   [ACTIVE] 差分結果可視化
│   │   └── layout_util.py             [ACTIVE] レイアウト計算
│   ├── data_structures/  # データ構造定義
│   │   ├── geometry_data.py    [ACTIVE] Pydanticベース統一構造
│   │   └── simple_geometry.py  [ACTIVE] 軽量幾何データ構造
│   ├── main.py          [ACTIVE] 統合CLIアプリケーション
│   └── main_legacy.py   [LEGACY] 旧CLIアプリケーション
├── tests/               # テストファイル群
├── analyze_*.py         [DEBUG] デバッグ・解析ツール群
└── test_*.py           [DEBUG] 手動テストスクリプト群
```

### 1.2 機能フロー

1. **DXF→PDF変換フロー（現在の主要機能）**
   ```
   DXFファイル → safe_dxf_converter → GeometryCollection → cad_standard_visualizer → PDF
   ```
   - 単位自動検出（mm/cm）
   - A3サイズ固定、CADスケール（1:100等）準拠
   - Matrix44エラー回避

2. **差分解析フロー（Phase 2機能）**
   ```
   敷地図・完成形図面 → dxf/pdf_converter → GeometryData → difference_engine → 差分結果
   ```
   - 建築要素分類（壁、開口部、設備）
   - Shapelyによる幾何演算

## 2. ファイル分類結果

### ACTIVE（現在使用中）
- `src/` 配下のほぼ全てのモジュール
- `tests/` 配下のテストファイル
- `requirements.txt`, `README.md`, `CLAUDE.md`

### LEGACY（廃止予定）
- `src/main_legacy.py` - main.pyに機能統合済み
- `250618_図面セット/` - テスト済み図面（削除可能）

### DEBUG（デバッグ用）
- `analyze_dxf_bounds.py` - DXF境界確認
- `analyze_dxf_detail.py` - DXF詳細解析
- `analyze_blocks.py` - ブロック解析
- `analyze_unit_problem.py` - 単位問題診断
- `simple_bounds_check.py` - 境界チェック
- `test_conversion.py` - 変換テスト
- `test_both_files.py` - 複数ファイルテスト

### DELETE（削除対象）
- `output/`, `test_output/`, `test_output_fixed/`, `output_test/`, `output_final/`, `debug_output/` - 出力ディレクトリ群
- `.pytest_cache/`, `__pycache__/` - キャッシュディレクトリ

## 3. 現在の問題点

1. **ディレクトリ構造の散乱**
   - ルートレベルに多数のデバッグスクリプト
   - 複数の出力ディレクトリ（6個）
   - テストファイルの配置が不統一

2. **機能の重複**
   - `safe_pdf_visualizer.py`と`cad_standard_visualizer.py`の役割分担が不明確
   - `main.py`と`main_legacy.py`の並存

3. **スケール問題の複雑さ**
   - `layout_util.py`の`compute_fit_scale`が動的スケール調整を行う
   - CAD標準スケール（1:100）との競合
   - 単位係数（mm/cm）の扱いが複数箇所に分散

## 4. リファクタリング提案

### 4.1 ディレクトリ整理
```bash
# 1. 出力ディレクトリの統合
mkdir -p output
rm -rf test_output test_output_fixed output_test output_final debug_output

# 2. デバッグツールの移動
mkdir -p tools/debug
mv analyze_*.py tools/debug/
mv test_*.py tools/debug/

# 3. レガシーファイルの移動
mkdir -p legacy
mv src/main_legacy.py legacy/
```

### 4.2 コード整理

1. **Visualizerの統合**
   - `safe_pdf_visualizer.py`を削除
   - `cad_standard_visualizer.py`に安全機能を統合

2. **スケール処理の一元化**
   - `layout_util.py`を削除または制限
   - CAD標準スケールを優先する設定を追加

3. **main.pyの改善**
   - コマンド体系の整理
   - ヘルプメッセージの充実

### 4.3 優先順位

1. **高優先度**
   - ディレクトリ整理（即実行可能）
   - main_legacy.pyの削除
   - テストの整理

2. **中優先度**
   - Visualizerの統合
   - スケール処理の改善

3. **低優先度**
   - Phase 3（JSON変換）の設計
   - ドキュメントの充実

## 5. 次のステップ

1. このインベントリを基にリファクタリング実行計画を作成
2. ユーザーの承認を得てから実行
3. スケール問題の根本解決に着手

## 6. 成果物

- 本調査報告書
- 機能インベントリマップ（表形式）
- リファクタリング提案