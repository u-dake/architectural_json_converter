#!/usr/bin/env python3
"""
DXFブロック内容の詳細解析
"""
import sys
from pathlib import Path
import ezdxf

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# DXFファイルのパス
dxf_file = project_root / "sample_data" / "site_plan" / "01_敷地図.dxf"

print(f"ファイル: {dxf_file.name}")
print('='*60)

doc = ezdxf.readfile(str(dxf_file))

# ブロック定義の詳細解析
for block in doc.blocks:
    if not block.name.startswith("*"):
        print(f"\nブロック: {block.name}")
        print("-"*40)
        
        # ブロック内の要素範囲を計算
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        element_types = {}
        
        for entity in block:
            etype = entity.dxftype()
            element_types[etype] = element_types.get(etype, 0) + 1
            
            try:
                if etype == "LINE":
                    min_x = min(min_x, entity.dxf.start.x, entity.dxf.end.x)
                    max_x = max(max_x, entity.dxf.start.x, entity.dxf.end.x)
                    min_y = min(min_y, entity.dxf.start.y, entity.dxf.end.y)
                    max_y = max(max_y, entity.dxf.start.y, entity.dxf.end.y)
                elif etype == "CIRCLE":
                    c = entity.dxf.center
                    r = entity.dxf.radius
                    min_x = min(min_x, c.x - r)
                    max_x = max(max_x, c.x + r)
                    min_y = min(min_y, c.y - r)
                    max_y = max(max_y, c.y + r)
                elif etype == "ARC":
                    c = entity.dxf.center
                    r = entity.dxf.radius
                    min_x = min(min_x, c.x - r)
                    max_x = max(max_x, c.x + r)
                    min_y = min(min_y, c.y - r)
                    max_y = max(max_y, c.y + r)
                elif etype in ("LWPOLYLINE", "POLYLINE"):
                    if etype == "LWPOLYLINE":
                        for v in entity.vertices():
                            min_x = min(min_x, v[0])
                            max_x = max(max_x, v[0])
                            min_y = min(min_y, v[1])
                            max_y = max(max_y, v[1])
                    else:
                        for v in entity.vertices:
                            loc = v.dxf.location
                            min_x = min(min_x, loc.x)
                            max_x = max(max_x, loc.x)
                            min_y = min(min_y, loc.y)
                            max_y = max(max_y, loc.y)
            except:
                pass
        
        print(f"  要素数: {len(list(block))}")
        print(f"  要素タイプ: {dict(sorted(element_types.items()))}")
        
        if min_x != float('inf'):
            width = max_x - min_x
            height = max_y - min_y
            print(f"  座標範囲: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")
            print(f"  サイズ: {width:.1f} x {height:.1f}")
            
            # サンプル要素を表示
            print("\n  最初の5要素:")
            for i, entity in enumerate(block):
                if i >= 5:
                    break
                if entity.dxftype() == "LINE":
                    print(f"    LINE: ({entity.dxf.start.x:.1f}, {entity.dxf.start.y:.1f}) -> ({entity.dxf.end.x:.1f}, {entity.dxf.end.y:.1f})")
                elif entity.dxftype() == "CIRCLE":
                    print(f"    CIRCLE: center=({entity.dxf.center.x:.1f}, {entity.dxf.center.y:.1f}), r={entity.dxf.radius:.1f}")

# モデル空間のINSERT要素を確認
print("\n\nモデル空間のINSERT要素:")
print("="*60)
for entity in doc.modelspace():
    if entity.dxftype() == "INSERT":
        print(f"\nINSERT: {entity.dxf.name}")
        print(f"  挿入点: ({entity.dxf.insert.x:.1f}, {entity.dxf.insert.y:.1f})")
        print(f"  スケール: X={entity.dxf.xscale}, Y={entity.dxf.yscale}")
        print(f"  回転: {entity.dxf.rotation}°")
