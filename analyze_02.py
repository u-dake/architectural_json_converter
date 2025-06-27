#!/usr/bin/env python3
"""02_完成形.dxfの単位問題を分析"""
import ezdxf

dxf_file = "sample_data/floor_plan/02_完成形.dxf"
doc = ezdxf.readfile(dxf_file)

print(f"ファイル: {dxf_file}")
print(f"INSUNITS: {doc.header.get('$INSUNITS', 0)} (4=mm)")

# INSERT要素の座標範囲を確認
insert_count = 0
insert_min_x = insert_min_y = float('inf')
insert_max_x = insert_max_y = float('-inf')

for entity in doc.modelspace():
    if entity.dxftype() == 'INSERT':
        insert_count += 1
        x, y = entity.dxf.insert.x, entity.dxf.insert.y
        insert_min_x = min(insert_min_x, x)
        insert_max_x = max(insert_max_x, x)
        insert_min_y = min(insert_min_y, y)
        insert_max_y = max(insert_max_y, y)
        
        if insert_count <= 5:  # 最初の5個のINSERT要素を表示
            print(f"\nINSERT #{insert_count}: {entity.dxf.name}")
            print(f"  挿入点: ({x:.3f}, {y:.3f})")

if insert_count > 0:
    width = insert_max_x - insert_min_x
    height = insert_max_y - insert_min_y
    print(f"\nINSERT要素の座標範囲:")
    print(f"  X: {insert_min_x:.3f} ~ {insert_max_x:.3f}")
    print(f"  Y: {insert_min_y:.3f} ~ {insert_max_y:.3f}")
    print(f"  幅×高さ: {width:.3f} × {height:.3f}")
    print(f"\n単位判定:")
    if width < 10 and height < 10:
        print(f"  → メートル単位の可能性が高い（実際のサイズ: {width:.1f}m × {height:.1f}m）")
        print(f"  → mm変換すると: {width*1000:.1f}mm × {height*1000:.1f}mm")
    elif width < 1000 and height < 1000:
        print(f"  → センチメートル単位の可能性（実際のサイズ: {width/100:.1f}m × {height/100:.1f}m）")
    else:
        print(f"  → ミリメートル単位（実際のサイズ: {width/1000:.1f}m × {height/1000:.1f}m）")
else:
    print("\nINSERT要素が見つかりませんでした")
