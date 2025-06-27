#!/usr/bin/env python3
"""
DXF図面の座標範囲とスケール分析
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.engines.safe_dxf_converter import SafeDXFConverter


def analyze_bounds(dxf_file):
    """DXFファイルの座標範囲を分析"""
    print(f"=== DXF Bounds Analysis: {dxf_file} ===")
    
    converter = SafeDXFConverter()
    geometry = converter.convert_dxf_file(dxf_file, include_paperspace=True)
    
    if not geometry.elements:
        print("No elements found")
        return
    
    # 境界計算
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for element in geometry.elements:
        if hasattr(element, 'start') and hasattr(element, 'end'):  # Line
            min_x = min(min_x, element.start.x, element.end.x)
            max_x = max(max_x, element.start.x, element.end.x)
            min_y = min(min_y, element.start.y, element.end.y)
            max_y = max(max_y, element.start.y, element.end.y)
        elif hasattr(element, 'center') and hasattr(element, 'radius'):  # Circle/Arc
            min_x = min(min_x, element.center.x - element.radius)
            max_x = max(max_x, element.center.x + element.radius)
            min_y = min(min_y, element.center.y - element.radius)
            max_y = max(max_y, element.center.y + element.radius)
        elif hasattr(element, 'points'):  # Polyline
            for point in element.points:
                min_x = min(min_x, point.x)
                max_x = max(max_x, point.x)
                min_y = min(min_y, point.y)
                max_y = max(max_y, point.y)
        elif hasattr(element, 'position'):  # Text
            min_x = min(min_x, element.position.x)
            max_x = max(max_x, element.position.x)
            min_y = min(min_y, element.position.y)
            max_y = max(max_y, element.position.y)
    
    width = max_x - min_x
    height = max_y - min_y
    
    print(f"Elements: {len(geometry.elements)}")
    print(f"X range: {min_x:.2f} to {max_x:.2f} (width: {width:.2f})")
    print(f"Y range: {min_y:.2f} to {max_y:.2f} (height: {height:.2f})")
    print(f"Drawing units: mm (assuming)")
    
    # スケール計算
    print(f"\n=== Scale Analysis ===")
    
    # A3横サイズ (420mm x 297mm)
    a3_width_mm = 420
    a3_height_mm = 297
    
    # 1/100スケールでの表示可能サイズ
    max_drawing_width_mm = a3_width_mm * 100  # 42000mm = 42m
    max_drawing_height_mm = a3_height_mm * 100  # 29700mm = 29.7m
    
    print(f"A3 paper size: {a3_width_mm}mm x {a3_height_mm}mm")
    print(f"1/100 scale max drawing size: {max_drawing_width_mm}mm x {max_drawing_height_mm}mm")
    print(f"Current drawing size: {width:.2f}mm x {height:.2f}mm")
    
    # フィット確認
    if width <= max_drawing_width_mm and height <= max_drawing_height_mm:
        print("✓ Drawing fits in A3 at 1/100 scale")
    else:
        print("✗ Drawing is too large for A3 at 1/100 scale")
        scale_x_needed = width / max_drawing_width_mm
        scale_y_needed = height / max_drawing_height_mm
        min_scale = max(scale_x_needed, scale_y_needed)
        print(f"Minimum scale needed: 1/{int(100/min_scale)}")
    
    # 1/100スケールでのPDFサイズ（ポイント単位）
    # 1mm = 2.834645669 points
    mm_to_points = 2.834645669
    pdf_width_pts = width / 100 * mm_to_points
    pdf_height_pts = height / 100 * mm_to_points
    
    print(f"\n=== PDF Output at 1/100 Scale ===")
    print(f"Content size in PDF: {pdf_width_pts:.2f} x {pdf_height_pts:.2f} pts")
    print(f"A3 page size: {a3_width_mm * mm_to_points:.2f} x {a3_height_mm * mm_to_points:.2f} pts")


if __name__ == "__main__":
    files = [
        "sample_data/site_plan/01_敷地図.dxf",
        "sample_data/floor_plan/02_完成形.dxf"
    ]
    
    for file in files:
        analyze_bounds(file)
        print()