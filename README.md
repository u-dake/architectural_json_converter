# 建築図面JSON変換システム

## 概要
敷地図と間取り図の差分を解析し、FreeCAD Python API用のJSONを生成するシステム

## 開発状況
✅ **Phase 1 完了** - ファイル構造解析システム実装済み  
🚧 **Phase 2 開発中** - 差分解析エンジン + 可視化システム

## 機能
- **マルチフォーマット対応**: DXF・PDFファイルの両方を解析
- **差分検出**: 敷地図と間取り図の新規追加要素を自動識別
- **可視化**: インタラクティブな比較表示（Phase 2）
- **JSON出力**: FreeCAD互換の構造化データ出力（Phase 3予定）
- **グリッド対応**: 日本建築標準910mm（半畳）グリッド

## クイックスタート

### Phase 1: ファイル構造解析
```bash
# 依存関係インストール
pip install -r requirements.txt

# DXFファイル解析
python src/analyzers/dxf_analyzer.py data/sample.dxf

# PDFファイル解析
python src/analyzers/pdf_analyzer.py data/sample.pdf
```

### Phase 2: 差分解析・可視化（開発中）
```bash
# 2つの図面の差分を解析・可視化
python src/main.py data/敷地図.dxf data/間取り図.dxf --visualize --interactive
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
│   ├── analyzers/         # DXF・PDF解析モジュール（Phase 1完了）
│   ├── data_structures/   # 統一データ構造（Phase 2）
│   ├── engines/           # 差分抽出エンジン（Phase 2）
│   ├── visualization/     # 可視化システム（Phase 2）
│   └── main.py           # メインアプリケーション（Phase 2）
├── tests/                 # テストコード
├── data/                  # サンプル・解析結果データ
├── output/                # 生成される可視化・レポート
└── docs/                  # ドキュメント
```

## 開発フェーズ

### ✅ Phase 1: ファイル構造解析（完了）
- **成果物**: DXF・PDF解析モジュール、基本テストスイート
- **品質**: テストカバレッジ50%、実図面での動作確認済み
- **解析結果**: 敷地図56エンティティ → 完成形68エンティティ（差分検出成功）

### 🚧 Phase 2: 差分解析エンジン + 可視化（開発中）
- **目標**: 建築要素の自動分類・可視化システム
- **期間**: 3週間（1/20-2/7）
- **成果物**: 統一データ構造、差分抽出エンジン、可視化システム、包括的ドキュメント

### 📋 Phase 3: JSON変換エンジン（予定）
- **目標**: FreeCAD Python API互換JSON出力
- **成果物**: 910mmグリッド対応、間取り生成パイプライン

## ドキュメント
- [Phase 1実装ログ](_docs/2025-01-19_phase1_file_analyzers.md)
- [Phase 2実装仕様](PHASE2_SPECIFICATION.md)
- [Phase 2進捗チェックリスト](PHASE2_CHECKLIST.md)
- [ドキュメント整備要件](DOCUMENTATION_REQUIREMENTS.md)
- [プロジェクト全体仕様](PROJECT_SPECIFICATION.md)

## 開発ガイドライン

### コード品質
- Type hints必須
- Docstring必須
- Black formatter適用
- Unit test coverage > 80%（Phase 2目標）

### 精度要件
- 座標精度: ±1mm以内
- 910mmグリッド対応
- 差分検出精度: 95%以上

### パフォーマンス要件
- DXF解析: < 10秒
- PDF解析: < 15秒
- 差分抽出: < 10秒
- 可視化生成: < 15秒

## 使用技術
- **解析**: ezdxf (DXF), PyMuPDF (PDF)
- **数値計算**: numpy, shapely
- **可視化**: matplotlib, plotly, seaborn
- **品質管理**: pytest, black, mypy, flake8
- **データ検証**: pydantic

## 貢献方法
1. このリポジトリをフォーク
2. 機能ブランチを作成
3. 変更をコミット
4. テストが通ることを確認
5. プルリクエストを作成

## ライセンス
[ライセンス情報を記載]

---
**開発チーム**: Phase 2実装中！詳細は [PHASE2_CHECKLIST.md](PHASE2_CHECKLIST.md) を参照してください。
