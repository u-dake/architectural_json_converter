#!/usr/bin/env python3
"""
DXF->PDF変換テスト
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.engines.safe_dxf_converter import SafeDXFConverter
    from src.visualization.cad_standard_visualizer import CADStandardVisualizer
    from src.data_structures.simple_geometry import GeometryCollection
    
    print("✓ モジュールのインポート成功")
    
    # DXFファイルパス
    dxf_file = project_root / "sample_data" / "site_plan" / "01_敷地図.dxf"
    
    if not dxf_file.exists():
        print(f"✗ DXFファイルが見つかりません: {dxf_file}")
        sys.exit(1)
    
    print(f"✓ DXFファイルが存在: {dxf_file}")
    
    # 変換処理
    print("\n[1] DXF変換開始...")
    converter = SafeDXFConverter()
    geometry = converter.convert_dxf_file(str(dxf_file), include_paperspace=True)
    
    print(f"✓ 変換完了: {len(geometry.elements)} 要素")
    print(f"  unit_factor_mm: {geometry.metadata.get('unit_factor_mm', 1.0)}")
    print(f"  auto_scaled: {geometry.metadata.get('auto_scaled', False)}")
    
    # 実際の座標範囲を確認
    if hasattr(converter, '_calculate_actual_bounds'):
        bounds = converter._calculate_actual_bounds(geometry)
        if bounds:
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            print(f"  実際の座標範囲: {width:.1f} x {height:.1f} mm")
    
    # PDF出力
    print("\n[2] PDF出力開始...")
    visualizer = CADStandardVisualizer()
    
    output_dir = project_root / "test_output"
    output_dir.mkdir(exist_ok=True)
    output_pdf = output_dir / "01_敷地図_test.pdf"
    
    visualizer.visualize_to_a3_pdf(
        geometry,
        str(output_pdf),
        scale="1:100",
        dpi=300,
        show_border=True,
        title="01_敷地図"
    )
    
    if output_pdf.exists():
        print(f"✓ PDF生成成功: {output_pdf}")
        print(f"  ファイルサイズ: {output_pdf.stat().st_size:,} bytes")
    else:
        print("✗ PDF生成失敗")
        
except Exception as e:
    print(f"\n✗ エラー発生: {e}")
    import traceback
    traceback.print_exc()
