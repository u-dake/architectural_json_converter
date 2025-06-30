# 使用ガイド

## 概要

本システムは建築図面（DXF形式）の変換・解析・差分視覚化を行うツールセットです。

## 主な機能

### 1. DXF→PDF変換

DXFファイルをCAD標準（A3サイズ）のPDFに変換します。

```bash
python src/main.py dxf2pdf <input_dxf> [options]
```

**オプション:**
- `--scale`: 出力縮尺（デフォルト: 1:100）
- `-o, --output`: 出力ファイルパス

**例:**
```bash
# 単一ファイルの変換
python src/main.py dxf2pdf sample_data/buildings/01/site_plan/01_敷地図.dxf --scale 1:100

# 出力先を指定
python src/main.py dxf2pdf input.dxf -o output.pdf --scale 1:50
```

### 2. 差分解析・視覚化

敷地図と完成形図面の差分を解析し、PDFで視覚化します。

```bash
python tools/visualize_dxf_diff.py diff <site_plan> <floor_plan> [options]
```

**オプション:**
- `-o, --output`: 出力PDFファイル名

**例:**
```bash
# 2つのDXFファイルの差分を視覚化
python tools/visualize_dxf_diff.py diff \
    sample_data/buildings/01/site_plan/01_敷地図.dxf \
    sample_data/buildings/01/floor_plan/01_完成形.dxf \
    -o diff_01.pdf
```

### 3. バッチ処理

#### DXFの一括変換
```bash
python src/main.py batch <input_directory> [options]
```

**オプション:**
- `-o, --output-dir`: 出力ディレクトリ
- `-s, --scale`: 出力縮尺（デフォルト: 1:50）

#### 差分の一括解析
```bash
python tools/visualize_dxf_diff.py batch <input_directory> [options]
```

**オプション:**
- `-o, --output-dir`: 出力ディレクトリ（デフォルト: outputs）

**例:**
```bash
# sample_data内の全建物の差分を一括解析
python tools/visualize_dxf_diff.py batch sample_data/

# 出力ディレクトリを指定
python tools/visualize_dxf_diff.py batch sample_data/ -o results/
```

## サンプルデータ構造

```
sample_data/
└── buildings/
    ├── 01/
    │   ├── site_plan/01_敷地図.dxf    # 敷地図
    │   └── floor_plan/01_完成形.dxf   # 完成形
    ├── 02/
    │   ├── site_plan/02_敷地図.dxf
    │   └── floor_plan/02_完成形.dxf
    ...
    └── 10/
        ├── site_plan/10_敷地図.dxf
        └── floor_plan/10_完成形.dxf
```

## 出力形式

### PDF出力の特徴
- **A3サイズ（420×297mm）**での出力
- **標準縮尺**対応（1:50, 1:100, 1:200, 1:500, 1:1000）
- **図面枠**と**スケール表示**付き
- **単位自動変換**（メートル/ミリメートル混在に対応）

### 差分視覚化の表示内容
1. **サイトプラン**（敷地図）のみ
2. **フロアプラン**（完成形）のみ
3. **重ね合わせ表示**（青：サイト、赤：フロア）
4. **差分強調表示**（新規要素を強調）

## トラブルシューティング

### DXFファイルが正しく読み込まれない場合
- ファイルの文字エンコーディングを確認（UTF-8推奨）
- DXFバージョンを確認（AutoCAD 2000以降推奨）

### 要素が表示されない場合
- ブロック参照が正しく展開されているか確認
- レイヤーが非表示になっていないか確認
- 単位設定（INSUNITS）を確認

### メモリ不足エラーが発生する場合
- 大きなDXFファイルの場合、バッチ処理ではなく個別処理を推奨
- 不要なレイヤーやブロックを削除してファイルサイズを削減

## 高度な使用方法

### デバッグツールの使用

```bash
# DXFファイルの詳細解析
python tools/debug/analyze_dxf_detail.py <dxf_file>

# ブロックパターンの解析
python tools/debug/analyze_block_patterns.py <directory>

# 単位問題の調査
python tools/debug/analyze_unit_problem.py <dxf_file>
```

### カスタマイズ

`src/engines/safe_dxf_converter.py`の設定を調整することで、変換動作をカスタマイズできます：

- 単位変換の閾値
- ブロック展開の深さ
- 要素フィルタリング