#!/usr/bin/env python3
"""
DXF単位問題の詳細分析
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
    
    doc = ezdxf.readfile(str(dxf_file))
    
    # INSERT要素の詳細確認
    print("\n[INSERT要素の詳細]")
    for entity in doc.modelspace():
        if entity.dxftype() == "INSERT":
            print(f"\nINSERT: {entity.dxf.name}")
            print(f"  挿入点: ({entity.dxf.insert.x:.1f}, {entity.dxf.insert.y:.1f})")
            
            # ブロック定義の内容確認
            block = doc.blocks.get(entity.dxf.name)
            if block:
                # ブロック内の最初のLINE要素を確認
                for b_entity in block:
                    if b_entity.dxftype() == "LINE":
                        print(f"  最初のLINE要素:")
                        print(f"    開始: ({b_entity.dxf.start.x:.3f}, {b_entity.dxf.start.y:.3f})")
                        print(f"    終了: ({b_entity.dxf.end.x:.3f}, {b_entity.dxf.end.y:.3f})")
                        length = ((b_entity.dxf.end.x - b_entity.dxf.start.x)**2 + 
                                 (b_entity.dxf.end.y - b_entity.dxf.start.y)**2)**0.5
                        print(f"    長さ: {length:.3f} 単位")
                        
                        # 建築的に意味のある長さか判定
                        if 0.9 < length < 1.1:
                            print(f"    → 1m（100cm）の可能性")
                        elif 9 < length < 11:
                            print(f"    → 10m（1000cm）の可能性")
                        elif 90 < length < 110:
                            print(f"    → 100m（10000cm）の可能性あり（ただし建築的には大きすぎ）")
                        elif 900 < length < 1100:
                            print(f"    → 1000m = 1km（非現実的）")
                        break
    
    # SafeDXFConverterでの変換テスト（自動スケーリングなし）
    print("\n[自動スケーリングなしでの変換テスト]")
    converter = SafeDXFConverter()
    converter.unit_factor = 1.0  # 強制的に1.0に設定
    
    # 実際には変換メソッドを一部実行
    doc = ezdxf.readfile(str(dxf_file))
    print(f"  INSUNITS: {doc.header.get('$INSUNITS', 0)} (4=mm)")
    
    # ブロック内の実際のサイズを確認
    for block_name in ["FcPack%d0", "FcPack%d1"]:
        block = doc.blocks.get(block_name)
        if block:
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for entity in block:
                if entity.dxftype() == "LINE":
                    min_x = min(min_x, entity.dxf.start.x, entity.dxf.end.x)
                    max_x = max(max_x, entity.dxf.start.x, entity.dxf.end.x)
                    min_y = min(min_y, entity.dxf.start.y, entity.dxf.end.y)
                    max_y = max(max_y, entity.dxf.start.y, entity.dxf.end.y)
            
            if min_x != float('inf'):
                width = max_x - min_x
                height = max_y - min_y
                print(f"\n  ブロック {block_name}:")
                print(f"    サイズ: {width:.1f} x {height:.1f} 単位")
                
                # もしこれがcmなら、建築的なサイズは？
                print(f"    もしcm単位なら: {width*10:.0f}mm x {height*10:.0f}mm = {width/100:.1f}m x {height/100:.1f}m")
                print(f"    もしmm単位なら: {width:.0f}mm x {height:.0f}mm = {width/1000:.1f}m x {height/1000:.1f}m")
