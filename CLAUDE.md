# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an architectural drawing JSON conversion system that analyzes differences between site plans and floor plans, converting them to JSON format for FreeCAD Python API.

Currently in **Phase 1 development** (File Structure Analysis).

## Essential Commands

### Development Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Code formatting
black src/ tests/

# Type checking
mypy src/

# Run tests with coverage
pytest tests/ --cov=src/

# Run individual test file
pytest tests/test_analyzers/test_dxf_analyzer.py
```

## Architecture Overview

The system consists of three main phases:

1. **Phase 1: File Structure Analysis** (Current)
   - DXF file analysis using `ezdxf` library
   - PDF file analysis using `PyMuPDF` library
   - Output detailed JSON structure of each file

2. **Phase 2: Difference Analysis Engine**
   - Unified data structure for DXF/PDF
   - Extract differences between site-only and site-with-floorplan files
   - Detect walls, openings, room boundaries, fixtures

3. **Phase 3: JSON Conversion Engine**
   - Convert to FreeCAD-compatible JSON format
   - Normalize coordinates to 910mm grid system
   - Output both `points_grid` and `points_mm`

## Key Technical Requirements

- **Coordinate Precision**: ±1mm accuracy required
- **Grid System**: 910mm (half-tatami) grid standard
- **JSON Output**: Must follow the predefined schema with metadata, structure (walls, rooms, openings, fixtures)
- **Code Quality**: Type hints and docstrings mandatory, 80%+ test coverage

## Current Development Focus

When implementing `dxf_analyzer.py`:
1. Use `ezdxf.readfile()` to load DXF files
2. Extract all entity types comprehensively
3. Capture layer information with patterns like "WALL", "壁", "W-" for walls
4. Normalize coordinates with origin reference
5. Include detailed bounds information

When implementing `pdf_analyzer.py`:
1. Use `fitz.open()` to load PDF files
2. Extract vector elements using `page.get_drawings()`
3. Convert PDF coordinate system (bottom-left origin) to standard (top-left origin)
4. Extract text with coordinates for room names and dimensions
5. Handle multi-page documents appropriately

## Testing Approach

- Test files should be placed in `data/sample_dxf/` and `data/sample_pdf/`
- Each analyzer should have comprehensive unit tests
- Integration tests should verify the complete pipeline
- Use actual architectural drawings for testing when available

## Important Notes

- DXF and PDF have different coordinate systems - always normalize
- Layer naming conventions vary - implement pattern matching
- Maintain separation between site elements and floor plan elements
- Error handling must allow partial success with appropriate logging

## Implementation Documentation

After completing any implementation:
1. Create an implementation log in the `_docs/` directory
2. Use the naming format: `yyyy-mm-dd_function_name.md`
3. Document the implementation details, decisions made, and any challenges encountered

When starting work, check the `_docs/` directory for previous implementation logs to understand past decisions and context.