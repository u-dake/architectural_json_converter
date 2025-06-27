# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an architectural drawing processing system with the following capabilities:
- **DXF→PDF Conversion**: Convert DXF files to PDF with CAD standard formatting (A3 size, specified scales)
- **Smart Unit Detection**: Automatically detect and correct unit issues in DXF files (meter/millimeter)
- **Difference Analysis**: Compare site plans and floor plans to detect architectural changes
- **Visualization**: Generate high-quality PDF outputs with proper scaling

The project has evolved from its original three-phase plan to focus on practical DXF→PDF conversion with smart unit handling.

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

The system is organized into the following components:

1. **Analyzers** (`src/analyzers/`)
   - `dxf_analyzer.py`: Extract and analyze DXF file structure
   - `pdf_analyzer.py`: Extract and analyze PDF file content

2. **Conversion Engines** (`src/engines/`)
   - `safe_dxf_converter.py`: Smart DXF→PDF conversion with unit detection
   - `difference_engine.py`: Compare and analyze differences between drawings

3. **Visualization** (`src/visualization/`)
   - `cad_standard_visualizer.py`: Generate CAD-standard PDF outputs (A3 size, proper scales)
   - `matplotlib_visualizer.py`: Create visual analysis outputs

4. **Main Application** (`src/main.py`)
   - Unified CLI for all operations
   - Commands: `dxf2pdf`, `diff`, `batch`

## Key Technical Requirements

- **Coordinate Precision**: ±1mm accuracy required
- **Grid System**: 910mm (half-tatami) grid standard
- **JSON Output**: Must follow the predefined schema with metadata, structure (walls, rooms, openings, fixtures)
- **Code Quality**: Type hints and docstrings mandatory, 80%+ test coverage

## Current Development Focus

### DXF→PDF Conversion
1. **Smart Unit Detection**:
   - Validate drawing size against architectural standards (5m-2km range)
   - Check A3 paper compatibility with standard scales (1:50 to 1:5000)
   - Automatically apply meter→mm conversion when needed

2. **Mixed Unit Handling**:
   - INSERT coordinates may be in meters while block content is in millimeters
   - Trust INSERT coordinates for overall building size
   - See `_docs/2025-06-28_mixed_units_analysis.md` for detailed analysis

3. **CAD Standard Output**:
   - A3 size (420×297mm) paper format
   - Proper scale notation and drawing frame
   - Support for standard architectural scales

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