# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive architectural CAD analysis system that provides:
- **DXF Difference Analysis**: Compare site plans and floor plans to visualize architectural changes
- **Smart Unit Detection**: Automatically detect units (mm/m) per block using pattern analysis
- **Multi-format Output**: Generate both PDF (visual) and JSON (structured data) outputs
- **LLM Integration**: Structured JSON output suitable for AI/LLM consumption

The system has evolved into a unified tool (`cad_analyzer.py`) that integrates all functionality.

## Essential Commands

### Quick Start with Unified Tool
```bash
# Complete analysis of all sample data
./cad_analyzer.py analyze-all sample_data -o outputs

# Analyze specific building differences
./cad_analyzer.py diff sample_data/buildings/01/site_plan/01_敷地図.dxf \
                      sample_data/buildings/01/floor_plan/01_完成形.dxf

# Analyze block patterns for unit detection
./cad_analyzer.py patterns sample_data

# Convert DXF to JSON
./cad_analyzer.py convert drawing.dxf
```

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

The system now has a modular architecture with a unified entry point:

1. **Unified Tool** (`cad_analyzer.py`)
   - Single entry point for all functionality
   - Commands: `analyze-all`, `diff`, `batch`, `patterns`, `convert`

2. **Analyzers** (`src/analyzers/`)
   - `dxf_analyzer.py`: Extract and analyze DXF file structure
   - `unit_detector.py`: Unified unit detection system using 3 methods

3. **Conversion Engines** (`src/engines/`)
   - `safe_dxf_converter.py`: Smart DXF conversion with unit detection
   - `difference_engine.py`: Compare and analyze differences between drawings

4. **Visualization** (`src/visualization/`)
   - `geometry_plotter.py`: Shared geometry plotting functionality
   - `cad_standard_visualizer.py`: Generate CAD-standard PDF outputs

5. **Tools** (`tools/`)
   - `visualize_dxf_diff.py`: Specialized difference visualization
   - `dxf_to_json.py`: DXF to JSON conversion
   - `debug/analyze_block_patterns_advanced.py`: Pattern analysis

## Key Technical Features

### Unified Unit Detection System
The new `UnitDetector` class combines three detection methods:
1. **Header Detection**: Reads DXF $INSUNITS variable (90% confidence)
2. **Pattern Detection**: Uses `block_patterns_advanced.json` (variable confidence)
3. **Size Detection**: Validates against architectural standards (60-80% confidence)

### Mixed Unit Handling
- INSERT coordinates may use different units than block content
- Context-aware detection (site plan vs floor plan)
- See `_docs/2025-06-28_mixed_units_analysis.md` for details

### Block Pattern Analysis
- Machine learning-like approach to unit estimation
- Fixed-size block detection (e.g., FcPack%d2: 400×277mm)
- Confidence scoring for reliability
- Pattern dictionary: `block_patterns_advanced.json`

## Current Status

### ✅ Completed
- Unified command-line tool
- Smart unit detection with pattern analysis
- DXF difference visualization (PDF + JSON)
- Block pattern analysis system
- Common geometry plotter for code reuse

### 🔄 Ongoing Improvements
- Performance optimization for large files
- Additional architectural element recognition
- Enhanced JSON schema for LLM consumption

## Testing Approach

- Sample files in `sample_data/buildings/01-10/`
- Each building has `site_plan/` and `floor_plan/` subdirectories
- Run `./cad_analyzer.py analyze-all sample_data` for comprehensive testing

## Important Notes

- Always use `SafeDXFConverter` for block reference expansion
- Unit detection results include confidence scores
- JSON output includes unit detection metadata
- PDF output uses matplotlib with Japanese font warnings (can be ignored)

## Implementation Documentation

Key documents in `_docs/`:
- `2025-06-28_mixed_units_analysis.md`: Mixed unit problem analysis
- `2025-06-28_advanced_block_pattern_analysis.md`: Pattern-based unit detection
- `2025-06-27_safe_dxf_converter.md`: Safe DXF converter implementation

When implementing new features:
1. Update relevant documentation in `_docs/`
2. Add tests in `tests/`
3. Update this file if architecture changes