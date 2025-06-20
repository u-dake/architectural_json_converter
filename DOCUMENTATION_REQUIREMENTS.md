# ドキュメント整備要件指示書

## 概要
Phase 2実装と並行して、プロジェクトの包括的なドキュメント整備を実施する。国際的な利用を想定し、日英両言語での完全対応を実現する。

## ドキュメント整備項目

### 1. README日英対応版

#### 1.1 README.md (英語版)
```markdown
# Architectural Drawing Difference Analyzer and JSON Converter

## Overview
A comprehensive system for analyzing differences between site plans and floor plans, converting them to structured JSON data compatible with FreeCAD Python API.

## Features
- **Multi-format Support**: Analyzes both DXF and PDF files
- **Difference Detection**: Automatically identifies new architectural elements
- **Visualization**: Interactive comparison views
- **JSON Export**: FreeCAD-compatible structured data output
- **Grid System**: Japanese 910mm (half-tatami) grid standardization

## Quick Start
\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Analyze file structures (Phase 1)
python src/analyzers/dxf_analyzer.py data/site_plan.dxf
python src/analyzers/pdf_analyzer.py data/site_plan.pdf

# Extract differences and visualize (Phase 2)
python src/main.py data/site_plan.dxf data/floor_plan.dxf --visualize
\`\`\`

## Installation
[Detailed installation instructions...]

## Usage Examples
[Comprehensive usage examples...]

## API Documentation
[API reference link...]

## Contributing
[Contribution guidelines...]

## License
[License information...]
```

#### 1.2 README_ja.md (日本語版)
```markdown
# 建築図面差分解析・JSON変換システム

## 概要
敷地図と間取り図の差分を解析し、FreeCAD Python APIで利用可能な構造化JSONデータに変換する包括的システム。

## 特徴
- **マルチフォーマット対応**: DXF・PDFファイルの両方を解析
- **差分検出**: 新規建築要素の自動識別
- **可視化**: インタラクティブな比較表示
- **JSON出力**: FreeCAD互換の構造化データ出力
- **グリッド対応**: 日本建築標準910mm（半畳）グリッド

## クイックスタート
\`\`\`bash
# 依存関係のインストール
pip install -r requirements.txt

# ファイル構造解析（Phase 1）
python src/analyzers/dxf_analyzer.py data/敷地図.dxf
python src/analyzers/pdf_analyzer.py data/敷地図.pdf

# 差分抽出・可視化（Phase 2）
python src/main.py data/敷地図.dxf data/間取り図.dxf --visualize
\`\`\`

## インストール方法
[詳細なインストール手順...]

## 使用例
[包括的な使用例...]

## API仕様
[API仕様へのリンク...]

## 貢献方法
[貢献ガイドライン...]

## ライセンス
[ライセンス情報...]
```

### 2. セットアップガイド

#### 2.1 SETUP_GUIDE.md (英語)
```markdown
# Setup Guide

## System Requirements
- Python 3.8 or higher
- pip package manager
- Git (for development)

## Operating System Support
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, CentOS 7+)

## Installation Methods

### Method 1: Standard Installation
\`\`\`bash
# Clone repository
git clone https://github.com/your-org/architectural_json_converter.git
cd architectural_json_converter

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m pytest tests/ -v
\`\`\`

### Method 2: Development Installation
\`\`\`bash
# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Setup pre-commit hooks
pre-commit install

# Run development checks
black src/ tests/
mypy src/
pytest tests/ --cov=src/
\`\`\`

## Configuration
[Configuration details...]

## Troubleshooting
[Common issues and solutions...]
```

#### 2.2 SETUP_GUIDE_ja.md (日本語)
```markdown
# セットアップガイド

## システム要件
- Python 3.8以上
- pipパッケージマネージャー
- Git（開発用）

## 対応OS
- Windows 10/11
- macOS 10.15以上
- Linux (Ubuntu 18.04以上、CentOS 7以上)

## インストール方法

### 方法1: 標準インストール
\`\`\`bash
# リポジトリのクローン
git clone https://github.com/your-org/architectural_json_converter.git
cd architectural_json_converter

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# インストールの確認
python -m pytest tests/ -v
\`\`\`

### 方法2: 開発環境インストール
\`\`\`bash
# 開発用依存関係のインストール
pip install -r requirements.txt
pip install -e .

# pre-commitフックの設定
pre-commit install

# 開発環境チェック
black src/ tests/
mypy src/
pytest tests/ --cov=src/
\`\`\`

## 設定
[設定詳細...]

## トラブルシューティング
[よくある問題と解決方法...]
```

### 3. 実行コマンドガイド

#### 3.1 COMMAND_GUIDE.md (英語)
```markdown
# Command Guide

## Phase 1: File Structure Analysis

### DXF File Analysis
\`\`\`bash
# Basic analysis
python src/analyzers/dxf_analyzer.py <dxf_file_path>

# Examples
python src/analyzers/dxf_analyzer.py data/sample_dxf/site_plan.dxf
python src/analyzers/dxf_analyzer.py data/sample_dxf/floor_plan.dxf

# Output: data/dxf_analysis_<filename>.json
\`\`\`

### PDF File Analysis
\`\`\`bash
# Basic analysis
python src/analyzers/pdf_analyzer.py <pdf_file_path>

# Examples
python src/analyzers/pdf_analyzer.py data/sample_pdf/site_plan.pdf
python src/analyzers/pdf_analyzer.py data/sample_pdf/floor_plan.pdf

# Output: data/pdf_analysis_<filename>.json
\`\`\`

## Phase 2: Difference Analysis & Visualization

### Basic Difference Analysis
\`\`\`bash
# Analyze differences between two files
python src/main.py <site_file> <complete_file> [options]

# Examples
python src/main.py data/site_plan.dxf data/floor_plan.dxf
python src/main.py data/site_plan.pdf data/floor_plan.pdf
python src/main.py data/site_plan.dxf data/floor_plan.pdf  # Mixed formats
\`\`\`

### Visualization Options
\`\`\`bash
# Generate visualization
python src/main.py data/site_plan.dxf data/floor_plan.dxf --visualize

# Interactive visualization
python src/main.py data/site_plan.dxf data/floor_plan.dxf --interactive

# Custom output directory
python src/main.py data/site_plan.dxf data/floor_plan.dxf --output-dir results/

# Custom tolerance (in mm)
python src/main.py data/site_plan.dxf data/floor_plan.dxf --tolerance 0.5
\`\`\`

### Output Files
\`\`\`
output/
├── comparison_visualization.png    # Side-by-side comparison
├── difference_only.png            # New elements only
├── interactive_plot.html          # Interactive visualization
├── analysis_report.html           # Comprehensive report
└── difference_data.json           # Structured difference data
\`\`\`

## Testing Commands

### Run All Tests
\`\`\`bash
# Run complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/ --cov-report=html

# Run specific test categories
pytest tests/test_analyzers/ -v          # Phase 1 tests
pytest tests/test_engines/ -v            # Phase 2 tests
pytest tests/integration_tests/ -v       # Integration tests
\`\`\`

### Code Quality Checks
\`\`\`bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Lint code
flake8 src/ tests/

# Import sorting
isort src/ tests/
\`\`\`

## Performance Testing
\`\`\`bash
# Performance benchmarks
python tests/performance/benchmark.py

# Memory profiling
python -m memory_profiler tests/performance/memory_test.py
\`\`\`

## Common Use Cases

### 1. Quick File Analysis
\`\`\`bash
# Analyze single file
python src/analyzers/dxf_analyzer.py my_drawing.dxf
\`\`\`

### 2. Compare Two Drawings
\`\`\`bash
# Generate visual comparison
python src/main.py site.dxf plan.dxf --visualize --interactive
\`\`\`

### 3. Batch Processing
\`\`\`bash
# Process multiple file pairs
for site in data/sites/*.dxf; do
    plan="${site/sites/plans}"
    python src/main.py "$site" "$plan" --output-dir "results/$(basename "$site" .dxf)/"
done
\`\`\`

### 4. Development Workflow
\`\`\`bash
# Complete development check
black src/ tests/ && mypy src/ && pytest tests/ --cov=src/
\`\`\`
```

#### 3.2 COMMAND_GUIDE_ja.md (日本語)
```markdown
# コマンドガイド

## Phase 1: ファイル構造解析

### DXFファイル解析
\`\`\`bash
# 基本的な解析
python src/analyzers/dxf_analyzer.py <DXFファイルパス>

# 実行例
python src/analyzers/dxf_analyzer.py data/sample_dxf/敷地図.dxf
python src/analyzers/dxf_analyzer.py data/sample_dxf/間取り図.dxf

# 出力: data/dxf_analysis_<ファイル名>.json
\`\`\`

### PDFファイル解析
\`\`\`bash
# 基本的な解析
python src/analyzers/pdf_analyzer.py <PDFファイルパス>

# 実行例
python src/analyzers/pdf_analyzer.py data/sample_pdf/敷地図.pdf
python src/analyzers/pdf_analyzer.py data/sample_pdf/間取り図.pdf

# 出力: data/pdf_analysis_<ファイル名>.json
\`\`\`

## Phase 2: 差分解析・可視化

### 基本的な差分解析
\`\`\`bash
# 2つのファイルの差分を解析
python src/main.py <敷地図ファイル> <完成形ファイル> [オプション]

# 実行例
python src/main.py data/敷地図.dxf data/間取り図.dxf
python src/main.py data/敷地図.pdf data/間取り図.pdf
python src/main.py data/敷地図.dxf data/間取り図.pdf  # 混合フォーマット
\`\`\`

### 可視化オプション
\`\`\`bash
# 可視化の生成
python src/main.py data/敷地図.dxf data/間取り図.dxf --visualize

# インタラクティブ可視化
python src/main.py data/敷地図.dxf data/間取り図.dxf --interactive

# カスタム出力ディレクトリ
python src/main.py data/敷地図.dxf data/間取り図.dxf --output-dir results/

# カスタム許容誤差（mm単位）
python src/main.py data/敷地図.dxf data/間取り図.dxf --tolerance 0.5
\`\`\`

### 出力ファイル
\`\`\`
output/
├── comparison_visualization.png    # 並列比較
├── difference_only.png            # 新規要素のみ
├── interactive_plot.html          # インタラクティブ可視化
├── analysis_report.html           # 包括的レポート
└── difference_data.json           # 構造化差分データ
\`\`\`

## テストコマンド

### 全テスト実行
\`\`\`bash
# 完全テストスイート実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ --cov=src/ --cov-report=html

# 特定テストカテゴリ実行
pytest tests/test_analyzers/ -v          # Phase 1テスト
pytest tests/test_engines/ -v            # Phase 2テスト
pytest tests/integration_tests/ -v       # 統合テスト
\`\`\`

### コード品質チェック
\`\`\`bash
# コードフォーマット
black src/ tests/

# 型チェック
mypy src/

# リント
flake8 src/ tests/

# インポートソート
isort src/ tests/
\`\`\`

## パフォーマンステスト
\`\`\`bash
# パフォーマンスベンチマーク
python tests/performance/benchmark.py

# メモリプロファイリング
python -m memory_profiler tests/performance/memory_test.py
\`\`\`

## よくある使用例

### 1. クイックファイル解析
\`\`\`bash
# 単一ファイル解析
python src/analyzers/dxf_analyzer.py my_drawing.dxf
\`\`\`

### 2. 2つの図面比較
\`\`\`bash
# 視覚的比較の生成
python src/main.py 敷地図.dxf 間取り図.dxf --visualize --interactive
\`\`\`

### 3. バッチ処理
\`\`\`bash
# 複数ファイルペアの処理
for site in data/sites/*.dxf; do
    plan="${site/sites/plans}"
    python src/main.py "$site" "$plan" --output-dir "results/$(basename "$site" .dxf)/"
done
\`\`\`

### 4. 開発ワークフロー
\`\`\`bash
# 完全な開発チェック
black src/ tests/ && mypy src/ && pytest tests/ --cov=src/
\`\`\`
```

### 4. API仕様書

#### 4.1 API_REFERENCE.md
```markdown
# API Reference

## Module: analyzers

### dxf_analyzer
\`\`\`python
def analyze_dxf_structure(filepath: str) -> Dict[str, Any]:
    \"\"\"
    Analyzes DXF file structure and returns detailed information.
    
    Args:
        filepath: Path to DXF file
        
    Returns:
        Dictionary containing:
        - file_info: File metadata
        - header_info: DXF header information
        - layers: Layer definitions
        - entities_summary: Entity type statistics
        - entities_detail: Detailed entity information
        - bounds: Drawing boundaries
        
    Raises:
        FileNotFoundError: File not found
        ezdxf.DXFError: DXF parsing error
    \"\"\"
\`\`\`

### pdf_analyzer
\`\`\`python
def analyze_pdf_structure(filepath: str) -> Dict[str, Any]:
    \"\"\"
    Analyzes PDF file structure and extracts vector elements.
    
    Args:
        filepath: Path to PDF file
        
    Returns:
        Dictionary containing:
        - file_info: File metadata
        - metadata: PDF metadata
        - pages: Page-by-page analysis
        - vector_elements_summary: Vector element statistics
        - text_elements: Text elements with coordinates
        - bounds: Drawing boundaries
        
    Raises:
        FileNotFoundError: File not found
        fitz.FileDataError: PDF parsing error
    \"\"\"
\`\`\`

## Module: data_structures

### GeometryData
\`\`\`python
class GeometryData:
    \"\"\"Unified data structure for DXF and PDF geometry data.\"\"\"
    
    def __init__(self):
        self.lines: List[Line] = []
        self.texts: List[Text] = []
        self.elements: List[GeometryElement] = []
        self.bounds: Tuple[float, float, float, float] = (0, 0, 0, 0)
        self.metadata: Dict[str, Any] = {}
    
    def add_line(self, line: Line) -> None: ...
    def add_text(self, text: Text) -> None: ...
    def get_elements_by_type(self, element_type: ElementType) -> List[GeometryElement]: ...
    def calculate_bounds(self) -> Tuple[float, float, float, float]: ...
    def to_grid_coordinates(self, grid_size: float = 910.0) -> 'GeometryData': ...
\`\`\`

## Module: engines

### DifferenceEngine
\`\`\`python
class DifferenceEngine:
    \"\"\"Engine for extracting differences between site and complete drawings.\"\"\"
    
    def extract_differences(self, site_data: GeometryData, complete_data: GeometryData) -> GeometryData: ...
    def classify_building_elements(self, diff_data: GeometryData) -> GeometryData: ...
    def detect_walls(self, lines: List) -> List[GeometryElement]: ...
    def detect_openings(self, walls: List, all_elements: List) -> List[GeometryElement]: ...
\`\`\`

## Module: visualization

### GeometryPlotter
\`\`\`python
class GeometryPlotter:
    \"\"\"Visualization engine for geometry data.\"\"\"
    
    def plot_comparison(self, site_data: GeometryData, complete_data: GeometryData, diff_data: GeometryData, output_path: str) -> None: ...
    def plot_difference_only(self, diff_data: GeometryData, output_path: str) -> None: ...
    def create_interactive_plot(self, site_data: GeometryData, diff_data: GeometryData) -> go.Figure: ...
\`\`\`
```

### 5. ドキュメント品質要件

#### 5.1 言語品質基準
- **英語**: ネイティブレベルの自然な表現
- **日本語**: 技術文書として適切な敬語・専門用語
- **一貫性**: 用語集による統一された専門用語使用

#### 5.2 構造品質基準
- **階層構造**: 明確なセクション分け
- **ナビゲーション**: 目次とクロスリファレンス
- **検索性**: キーワードによる検索容易性

#### 5.3 実用性基準
- **初心者対応**: 前提知識なしでも理解可能
- **専門家対応**: 詳細な技術仕様も提供
- **トラブルシューティング**: よくある問題の解決策

## 実装要件

### ドキュメント更新の自動化
```bash
# ドキュメント生成スクリプト
scripts/
├── generate_docs.py          # API仕様の自動生成
├── update_readme.py          # README更新
├── validate_docs.py          # ドキュメント品質チェック
└── translate_docs.py         # 翻訳チェック
```

### CI/CDでのドキュメント検証
```yaml
# .github/workflows/docs.yml
- name: Validate Documentation
  run: |
    python scripts/validate_docs.py
    python scripts/check_translations.py
```

## 成果物チェックリスト

### 基本ドキュメント
- [ ] README.md (英語版)
- [ ] README_ja.md (日本語版)
- [ ] SETUP_GUIDE.md (英語版)
- [ ] SETUP_GUIDE_ja.md (日本語版)
- [ ] COMMAND_GUIDE.md (英語版)
- [ ] COMMAND_GUIDE_ja.md (日本語版)
- [ ] API_REFERENCE.md
- [ ] CONTRIBUTING.md
- [ ] LICENSE

### 補助ドキュメント
- [ ] CHANGELOG.md
- [ ] TROUBLESHOOTING.md
- [ ] EXAMPLES.md
- [ ] FAQ.md
- [ ] ARCHITECTURE.md

### メディア
- [ ] screenshots/ - スクリーンショット集
- [ ] examples/ - 使用例ファイル
- [ ] diagrams/ - システム図・フローチャート

---

**開発チーム**: Phase 2実装と並行して、このドキュメント整備要件に従って包括的なドキュメントを作成してください。特に初心者向けのセットアップガイドとコマンドガイドの品質を重視してください。
