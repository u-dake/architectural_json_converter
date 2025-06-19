# 建築図面JSON変換システム

## 概要
敷地図と間取り図の差分を解析し、FreeCAD Python API用のJSONを生成するシステム

## 開発状況
🚧 **現在Phase 1開発中** 🚧

## セットアップ

### 1. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 2. 開発環境設定
```bash
# コードフォーマット
black src/ tests/

# 型チェック
mypy src/

# テスト実行
pytest tests/ --cov=src/
```

## プロジェクト構造
```
architectural_json_converter/
├── src/                    # メインソースコード
│   ├── analyzers/         # DXF・PDF解析モジュール
│   ├── data_structures/   # データ構造定義
│   ├── engines/           # 差分抽出・JSON変換
│   └── main.py           # メインアプリケーション
├── tests/                 # テストコード
├── data/                  # サンプルデータ
└── docs/                  # ドキュメント
```

## Phase 1: ファイル構造解析（進行中）

### 目標
- DXFファイルの内部構造をJSONで出力
- PDFファイルの内部構造をJSONで出力

### 成果物
- [ ] `src/analyzers/dxf_analyzer.py`
- [ ] `src/analyzers/pdf_analyzer.py`
- [ ] サンプル解析結果JSON
- [x] `requirements.txt`

## 開発ガイドライン

### コード品質
- Type hints必須
- Docstring必須
- Black formatter適用
- Unit test coverage > 80%

### 精度要件
- 座標精度: ±1mm以内
- 910mmグリッド対応

## 詳細仕様
完全な仕様は [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md) を参照

---
**開発チームへ**: Phase 1の `dxf_analyzer.py` から開発開始してください
