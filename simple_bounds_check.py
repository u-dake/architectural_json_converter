#!/usr/bin/env python3
"""
Simple DXF bounds analysis without complex imports
"""

import ezdxf
from collections import defaultdict


def analyze_dxf_bounds(dxf_file):
    """DXFファイルの座標範囲を分析"""
    print(f"=== DXF Bounds Analysis: {dxf_file} ===")
    
    doc = ezdxf.readfile(dxf_file)
    
    # 全要素の座標範囲を取得
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    element_count = 0
    
    def process_entity(entity):
        nonlocal min_x, min_y, max_x, max_y, element_count
        element_count += 1
        
        try:
            if entity.dxftype() == "LINE":
                min_x = min(min_x, entity.dxf.start.x, entity.dxf.end.x)
                max_x = max(max_x, entity.dxf.start.x, entity.dxf.end.x)
                min_y = min(min_y, entity.dxf.start.y, entity.dxf.end.y)
                max_y = max(max_y, entity.dxf.start.y, entity.dxf.end.y)
            elif entity.dxftype() == "CIRCLE":
                cx, cy, r = entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius
                min_x = min(min_x, cx - r)
                max_x = max(max_x, cx + r)
                min_y = min(min_y, cy - r)
                max_y = max(max_y, cy + r)
            elif entity.dxftype() == "ARC":
                cx, cy, r = entity.dxf.center.x, entity.dxf.center.y, entity.dxf.radius
                min_x = min(min_x, cx - r)
                max_x = max(max_x, cx + r)
                min_y = min(min_y, cy - r)
                max_y = max(max_y, cy + r)
            elif entity.dxftype() in ["TEXT", "MTEXT"]:
                if entity.dxftype() == "TEXT":
                    pos = entity.dxf.insert
                else:
                    pos = entity.dxf.insert
                min_x = min(min_x, pos.x)
                max_x = max(max_x, pos.x)
                min_y = min(min_y, pos.y)
                max_y = max(max_y, pos.y)
            elif entity.dxftype() == "INSERT":
                # ブロック参照 - ブロック内の要素も展開
                block = doc.blocks.get(entity.dxf.name)
                if block:
                    insert_point = entity.dxf.insert
                    x_scale = entity.dxf.xscale
                    y_scale = entity.dxf.yscale
                    
                    for block_entity in block:
                        # 簡易的な変換を適用
                        if block_entity.dxftype() == "LINE":
                            sx = block_entity.dxf.start.x * x_scale + insert_point.x
                            sy = block_entity.dxf.start.y * y_scale + insert_point.y
                            ex = block_entity.dxf.end.x * x_scale + insert_point.x
                            ey = block_entity.dxf.end.y * y_scale + insert_point.y
                            
                            min_x = min(min_x, sx, ex)
                            max_x = max(max_x, sx, ex)
                            min_y = min(min_y, sy, ey)
                            max_y = max(max_y, sy, ey)
                        elif block_entity.dxftype() == "CIRCLE":
                            cx = block_entity.dxf.center.x * x_scale + insert_point.x
                            cy = block_entity.dxf.center.y * y_scale + insert_point.y
                            r = block_entity.dxf.radius * max(x_scale, y_scale)
                            min_x = min(min_x, cx - r)
                            max_x = max(max_x, cx + r)
                            min_y = min(min_y, cy - r)
                            max_y = max(max_y, cy + r)
                        elif block_entity.dxftype() == "ARC":
                            cx = block_entity.dxf.center.x * x_scale + insert_point.x
                            cy = block_entity.dxf.center.y * y_scale + insert_point.y
                            r = block_entity.dxf.radius * max(x_scale, y_scale)
                            min_x = min(min_x, cx - r)
                            max_x = max(max_x, cx + r)
                            min_y = min(min_y, cy - r)
                            max_y = max(max_y, cy + r)
        except:
            pass
    
    # モデル空間の要素を処理
    for entity in doc.modelspace():
        process_entity(entity)
    
    # ペーパー空間の要素も処理
    for layout in doc.layouts:
        if layout.is_any_paperspace:
            for entity in layout:
                if entity.dxftype() != "VIEWPORT":
                    process_entity(entity)
    
    if min_x == float('inf'):
        print("No drawable elements found")
        return
    
    width = max_x - min_x
    height = max_y - min_y
    
    print(f"Elements processed: {element_count}")
    print(f"Drawing bounds:")
    print(f"  X: {min_x:.2f} to {max_x:.2f} (width: {width:.2f})")
    print(f"  Y: {min_y:.2f} to {max_y:.2f} (height: {height:.2f})")
    print(f"  Units: {doc.units} (1=無単位, 4=mm, 6=m)")
    
    # スケール分析
    print(f"\n=== Scale Analysis ===")
    
    # A3横サイズ (420mm x 297mm)
    a3_width_mm = 420
    a3_height_mm = 297
    
    # 図面単位がmmと仮定
    drawing_width_mm = width
    drawing_height_mm = height
    
    print(f"Drawing size (assuming mm): {drawing_width_mm:.2f} x {drawing_height_mm:.2f} mm")
    print(f"A3 paper size: {a3_width_mm} x {a3_height_mm} mm")
    
    # 1/100スケールで必要なページサイズ
    required_width_mm = drawing_width_mm / 100
    required_height_mm = drawing_height_mm / 100
    
    print(f"Required page size at 1/100 scale: {required_width_mm:.2f} x {required_height_mm:.2f} mm")
    
    if required_width_mm <= a3_width_mm and required_height_mm <= a3_height_mm:
        print("✓ Drawing fits in A3 at 1/100 scale")
    else:
        print("✗ Drawing too large for A3 at 1/100 scale")
        scale_needed = max(required_width_mm / a3_width_mm, required_height_mm / a3_height_mm)
        actual_scale = int(100 * scale_needed)
        print(f"Suggested scale: 1/{actual_scale}")
    
    # PDFページサイズの計算
    mm_to_pts = 2.834645669  # 1mm = 2.834645669 points
    
    print(f"\n=== PDF Page Size (points) ===")
    print(f"A3 size: {a3_width_mm * mm_to_pts:.2f} x {a3_height_mm * mm_to_pts:.2f} pts")
    print(f"Content at 1/100: {required_width_mm * mm_to_pts:.2f} x {required_height_mm * mm_to_pts:.2f} pts")


if __name__ == "__main__":
    files = [
        "sample_data/site_plan/01_敷地図.dxf",
        "sample_data/floor_plan/02_完成形.dxf"
    ]
    
    for file in files:
        analyze_dxf_bounds(file)
        print("-" * 60)