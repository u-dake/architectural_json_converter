# API リファレンス

## 概要

本ドキュメントは、architectural_json_converterの主要なモジュールとクラスのAPIリファレンスです。

## 主要モジュール

### src.engines.safe_dxf_converter

DXFファイルの安全な変換を行うモジュール。

#### SafeDXFConverter

```python
class SafeDXFConverter:
    """安全なDXFコンバーター"""
    
    def convert_dxf_file(self, 
                        file_path: str, 
                        include_paperspace: bool = True) -> GeometryCollection:
        """
        DXFファイルをGeometryCollectionに変換
        
        Args:
            file_path: DXFファイルパス
            include_paperspace: ペーパースペースを含めるか
            
        Returns:
            GeometryCollection: 変換されたジオメトリ
        """
```

### src.data_structures.simple_geometry

基本的なジオメトリ要素を定義するモジュール。

#### 主要クラス

- `Point`: 2D点
- `Line`: 線分
- `Circle`: 円
- `Arc`: 円弧
- `Polyline`: ポリライン
- `Text`: テキスト要素
- `GeometryCollection`: ジオメトリ要素のコレクション

### src.visualization.cad_standard_visualizer

CAD標準に準拠したPDF出力を行うモジュール。

#### CADStandardVisualizer

```python
class CADStandardVisualizer:
    """CAD標準準拠の可視化クラス"""
    
    def visualize_to_a3_pdf(self,
                           geometry: GeometryCollection,
                           output_path: str,
                           scale: str = "1:100",
                           dpi: int = 300,
                           show_border: bool = True,
                           title: Optional[str] = None):
        """
        A3サイズのPDFに出力
        
        Args:
            geometry: 描画するジオメトリ
            output_path: 出力パス
            scale: 縮尺（例: "1:100"）
            dpi: 解像度
            show_border: 図面枠を表示するか
            title: タイトル
        """
```

### src.engines.difference_engine

図面の差分解析を行うモジュール。

#### 主要関数

```python
def extract_differences(site_geometry: GeometryData, 
                       floor_geometry: GeometryData) -> DifferenceResult:
    """
    敷地図と完成形の差分を抽出
    
    Args:
        site_geometry: 敷地図のジオメトリ
        floor_geometry: 完成形のジオメトリ
        
    Returns:
        DifferenceResult: 差分解析結果
    """
```

## 使用例

### DXFファイルの読み込みと変換

```python
from src.engines.safe_dxf_converter import SafeDXFConverter
from src.visualization.cad_standard_visualizer import CADStandardVisualizer

# DXFファイルを読み込む
converter = SafeDXFConverter()
geometry = converter.convert_dxf_file("input.dxf")

# PDFに出力
visualizer = CADStandardVisualizer()
visualizer.visualize_to_a3_pdf(
    geometry,
    "output.pdf",
    scale="1:100",
    title="建築図面"
)
```

### 差分解析の実行

```python
from src.engines.safe_dxf_converter import SafeDXFConverter
from src.engines.difference_engine import extract_differences

# DXFファイルを読み込む
converter = SafeDXFConverter()
site_data = converter.convert_dxf_file("site_plan.dxf")
floor_data = converter.convert_dxf_file("floor_plan.dxf")

# 差分を解析
result = extract_differences(site_data, floor_data)

# 統計情報を取得
stats = result.get_statistics()
print(f"新規要素数: {stats['total_new_elements']}")
```

## データ構造

### GeometryCollection

```python
@dataclass
class GeometryCollection:
    elements: List[Union[Point, Line, Circle, Arc, Polyline, Text]]
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### DifferenceResult

```python
class DifferenceResult:
    site_only: GeometryData      # 敷地図のみの要素
    site_with_plan: GeometryData  # 敷地図+完成形の要素
    new_elements: List[GeometryElement]  # 新規要素
    walls: List[GeometryElement]         # 壁要素
    openings: List[GeometryElement]      # 開口部要素
    fixtures: List[GeometryElement]      # 設備要素
```

## エラーハンドリング

### 一般的な例外

- `FileNotFoundError`: DXFファイルが見つからない
- `ValueError`: 無効な縮尺指定
- `ezdxf.DXFError`: DXFファイルの読み込みエラー

### エラー処理の例

```python
try:
    geometry = converter.convert_dxf_file("input.dxf")
except FileNotFoundError:
    print("ファイルが見つかりません")
except Exception as e:
    print(f"変換エラー: {e}")
```