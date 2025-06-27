#!/usr/bin/env python3
"""
DXFファイルの詳細解析
"""
import sys
from pathlib import Path
import ezdxf

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.engines.safe_dxf_converter import SafeDXFConverter

# DXFファイルのパス
dxf_files = [
    project_root / "sample_data" / "site_plan" / "01_敷地図.dxf",
    project_root / "sample_data" / "floor_plan" / "02_完成形.dxf"
]

for dxf_file in dxf_files:
    print(f"\n{'='*60}")
    print(f"ファイル: {dxf_file.name}")
    print('='*60)
    
    try:
        # DXFファイルを読み込み
        doc = ezdxf.readfile(str(dxf_file))
        
        # ヘッダー情報
        print("\n[ヘッダー情報]")
        extmin = doc.header.get("$EXTMIN")
        extmax = doc.header.get("$EXTMAX")
        limmin = doc.header.get("$LIMMIN")
        limmax = doc.header.get("$LIMMAX")
        insunits = doc.header.get("$INSUNITS", 0)
        
        print(f"  $EXTMIN: {extmin}")
        print(f"  $EXTMAX: {extmax}")
        if extmin and extmax:
            width = extmax[0] - extmin[0]
            height = extmax[1] - extmin[1]
            print(f"  → ヘッダー範囲: {width:.1f} x {height:.1f} 単位")
            
        print(f"  $LIMMIN: {limmin}")
        print(f"  $LIMMAX: {limmax}")
        print(f"  $INSUNITS: {insunits} ({['不明','インチ','フィート','マイル','mm','cm','m','km'][insunits] if insunits < 8 else '不明'})")
        
        # モデル空間の要素数
        print("\n[モデル空間]")
        modelspace = doc.modelspace()
        elements = list(modelspace)
        print(f"  要素数: {len(elements)}")
        
        # 要素タイプ別統計
        element_types = {}
        for e in elements:
            etype = e.dxftype()
            element_types[etype] = element_types.get(etype, 0) + 1
        
        print("  要素タイプ:")
        for etype, count in sorted(element_types.items()):
            print(f"    {etype}: {count}")
            
        # ブロック定義
        print("\n[ブロック定義]")
        blocks = [b for b in doc.blocks if not b.name.startswith("*")]
        print(f"  ブロック数: {len(blocks)}")
        for block in blocks[:5]:  # 最初の5個のみ表示
            print(f"    {block.name}: {len(list(block))} 要素")
        if len(blocks) > 5:
            print(f"    ... 他 {len(blocks)-5} ブロック")
            
        # SafeDXFConverterで変換してみる
        print("\n[SafeDXFConverter解析]")
        converter = SafeDXFConverter()
        
        # ヘッダーから範囲取得
        header_bounds = converter._get_drawing_extents_from_header(doc)
        if header_bounds:
            print(f"  ヘッダーから取得した範囲: {header_bounds[2]-header_bounds[0]:.1f} x {header_bounds[3]-header_bounds[1]:.1f}")
            
        # 実際のモデル空間の範囲を推定
        raw_width = converter._estimate_raw_width(doc)
        raw_height = converter._estimate_raw_height(doc)
        print(f"  モデル空間の推定範囲: {raw_width:.1f} x {raw_height:.1f}")
        
        # ペーパー空間判定
        is_paper = converter._is_paper_space_coordinates(raw_width, raw_height)
        print(f"  ペーパー空間座標と判定: {is_paper}")
        
        # 単位係数
        unit_factor = converter._detect_unit_factor(doc)
        print(f"  単位係数 (→mm): {unit_factor}")
        
        # 実際に変換してみる
        print("\n[変換後の情報]")
        geometry = converter.convert_dxf_file(str(dxf_file), include_paperspace=True)
        print(f"  変換された要素数: {len(geometry.elements)}")
        print(f"  メタデータ:")
        for key, value in geometry.metadata.items():
            print(f"    {key}: {value}")
            
        # 実際の座標範囲
        actual_bounds = converter._calculate_actual_bounds(geometry)
        if actual_bounds:
            width = actual_bounds[2] - actual_bounds[0]
            height = actual_bounds[3] - actual_bounds[1]
            print(f"  実際の座標範囲: {width:.1f} x {height:.1f} mm")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
