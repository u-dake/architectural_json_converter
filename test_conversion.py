import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import the converter
from src.engines.safe_dxf_converter import SafeDXFConverter

# Test the conversion
converter = SafeDXFConverter()
try:
    # Convert 02_完成形.dxf
    dxf_file = project_root / "sample_data" / "floor_plan" / "02_完成形.dxf"
    result = converter.convert_dxf_file(str(dxf_file))
    
    # Check the bounds
    bounds = converter._calculate_actual_bounds(result)
    if bounds:
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        print(f"02_完成形.dxf conversion result:")
        print(f"  Size: {width:.1f} x {height:.1f} mm")
        print(f"  Size in meters: {width/1000:.1f} x {height/1000:.1f} m")
        print(f"  Unit factor: {result.metadata.get('unit_factor_mm', 1.0)}")
        print(f"  Auto-scaled: {result.metadata.get('auto_scaled', False)}")
        
        if width > 100000:  # Larger than 100m
            print(f"\n⚠️  WARNING: The converted size is too large!")
            print(f"  This appears to be a building but is {width/1000:.0f}m wide")
            print(f"  This suggests incorrect unit conversion")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
