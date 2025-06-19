# 建築図面JSON変換システム開発指示書

## プロジェクト概要

### プロジェクト名
Architectural Drawing Difference Analyzer and JSON Converter

### 目的
敷地図ファイルと間取り図ファイルの差分を解析し、FreeCAD Python APIで利用可能なJSON形式で出力するシステムを開発する。

### 背景
- 顧客（セールス担当者）が敷地図をアップロードするだけで自動的に間取り図を生成するシステムの基盤
- diffusionモデルではなく、構造化データ（JSON）ベースでの間取り生成を採用
- 910mmグリッド（日本建築標準）での正確な寸法管理が必要

## 技術要件

### 対応ファイル形式
- **DXF**: AutoCAD Drawing Exchange Format
- **PDF**: ベクターデータを含むPDFファイル

### 出力形式
- **JSON**: FreeCAD Python APIで直接利用可能な構造化データ

### 技術制約
- 精度: mm単位での寸法精度を保証
- グリッド: 910mm（半畳）グリッドベースでの計算
- 拡張性: 将来的な他フォーマット対応を考慮した設計

## システム要件

### Phase 1: ファイル構造解析
**マイルストーン**: 実際のDXF・PDFファイルの内部構造をJSONで可視化

#### 1.1 DXF解析モジュール
```python
# 期待される機能
def analyze_dxf_structure(filepath: str) -> dict:
    """
    DXFファイルの全構造を詳細に解析
    - ヘッダー情報
    - レイヤー構造
    - エンティティ詳細（線分、円、ブロック等）
    - 座標情報
    """
    pass
```

**使用ライブラリ**: `ezdxf`
**出力**: `dxf_analysis_[filename].json`

#### 1.2 PDF解析モジュール
```python
# 期待される機能
def analyze_pdf_structure(filepath: str) -> dict:
    """
    PDFファイルのベクター要素を詳細に解析
    - ページ情報
    - 図形要素（線分、曲線等）
    - テキスト情報
    - 座標系
    """
    pass
```

**使用ライブラリ**: `PyMuPDF (fitz)` または `pdfplumber`
**出力**: `pdf_analysis_[filename].json`

### Phase 2: 差分解析エンジン
**マイルストーン**: 2つのファイル（敷地図のみ vs 間取り付き）の差分抽出

#### 2.1 統一データ構造設計
```python
class GeometryData:
    """
    DXF・PDF両対応の中間データ構造
    Phase 1の結果を踏まえて設計
    """
    lines: List[Line]
    texts: List[Text]
    blocks: List[Block]
    layers: List[Layer]
    metadata: Dict
```

#### 2.2 差分抽出アルゴリズム
```python
def extract_differences(site_only: GeometryData, 
                       site_with_plan: GeometryData) -> dict:
    """
    2つのファイルから新規追加要素を抽出
    - 壁の検出
    - 開口部の検出
    - 部屋境界の検出
    - 設備・階段等の検出
    """
    pass
```

### Phase 3: JSON変換エンジン
**マイルストーン**: FreeCAD互換JSONの出力

#### 3.1 JSON スキーマ準拠
既存の設計されたJSONスキーマに従う：
```json
{
  "metadata": {
    "grid_info": {"module_mm": 910},
    "source": "dxf_pdf_diff_analysis"
  },
  "structure": {
    "walls": [...],
    "rooms": [...],
    "openings": [...],
    "fixtures": [...]
  }
}
```

#### 3.2 座標正規化
- 910mmグリッドへの座標変換
- `points_grid` と `points_mm` の両方を出力

## 開発フェーズと成果物

### Phase 1 (Week 1-2)
**成果物**:
- `dxf_analyzer.py` - DXF解析モジュール
- `pdf_analyzer.py` - PDF解析モジュール
- サンプルファイルの解析結果JSON
- `requirements.txt` - 依存関係

### Phase 2 (Week 3-4)
**成果物**:
- `geometry_data.py` - 統一データ構造
- `difference_engine.py` - 差分抽出エンジン
- `test_difference_detection.py` - テストケース

### Phase 3 (Week 5-6)
**成果物**:
- `json_converter.py` - JSON変換エンジン
- `main.py` - メインアプリケーション
- `integration_tests.py` - 統合テスト
- `README.md` - 使用方法説明

## テストデータ
プロジェクト管理者が以下を提供：
- 敷地図のみDXF
- 敷地図のみPDF
- 間取り付きDXF
- 間取り付きPDF

## 品質要件

### コード品質
- Type hints必須
- Docstring必須
- Unit test coverage > 80%
- Black formatter適用

### 精度要件
- 座標精度: ±1mm以内
- グリッド変換精度: 完全一致
- JSON schema準拠: 100%

### パフォーマンス要件
- DXF解析: < 10秒 (通常サイズファイル)
- PDF解析: < 15秒 (通常サイズファイル)
- 差分抽出: < 5秒
- JSON変換: < 3秒

## 技術スタック

### 必須ライブラリ
```
ezdxf>=1.1.0          # DXF処理
PyMuPDF>=1.23.0       # PDF処理
numpy>=1.24.0         # 数値計算
pydantic>=2.0.0       # データ検証
pytest>=7.0.0         # テスト
black>=23.0.0         # フォーマッター
```

### 推奨ライブラリ
```
matplotlib>=3.7.0     # 可視化・デバッグ用
shapely>=2.0.0        # 幾何学計算
```

## プロジェクト構造
```
architectural_json_converter/
├── src/
│   ├── analyzers/
│   │   ├── dxf_analyzer.py
│   │   └── pdf_analyzer.py
│   ├── data_structures/
│   │   └── geometry_data.py
│   ├── engines/
│   │   ├── difference_engine.py
│   │   └── json_converter.py
│   └── main.py
├── tests/
│   ├── test_analyzers/
│   ├── test_engines/
│   └── integration_tests/
├── data/
│   ├── sample_dxf/
│   └── sample_pdf/
├── docs/
│   └── api_documentation.md
├── requirements.txt
├── README.md
└── PROJECT_SPECIFICATION.md
```

## 重要な注意事項

### 座標系の統一
- DXFとPDFでは座標系が異なる可能性
- 必ず原点基準で正規化すること

### レイヤー・要素の分類
- 壁: "WALL", "壁", "W-" などのレイヤー名パターン
- 寸法: "DIM", "寸法", "D-" などのパターン
- テキスト: 部屋名、注釈の適切な分離

### エラーハンドリング
- ファイル破損への対応
- 非対応フォーマットの適切なエラーメッセージ
- 部分的な解析失敗時の継続処理

## 報告・レビュー体制

### 週次報告
毎週金曜日に以下を報告：
- 進捗状況
- 技術課題・解決策
- 次週の計画
- サンプル出力（あれば）

### コードレビュー
- 各Phase完了時にプルリクエスト
- プロジェクト管理者による要件確認
- 品質チェック・テスト結果確認

---

**開発開始承認後、即座にPhase 1から着手してください。**
**質問・不明点は遠慮なく確認してください。**
