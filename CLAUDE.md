# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run a model by name (shows in viewer + exports)
uv run model cube

# Build all models
uv run python main.py

# Start viewer server with Catppuccin theme (run in separate terminal)
uv run viewer
# Then open http://127.0.0.1:3939

# Lint
uv run ruff check .

# Type check
uv run ty check .
```

## Architecture

This is a collection of 3D printable models using build123d (Python CAD library).

- `models/` - Individual model files, each with a `create_*()` function and `main()` for export
- `exports/` - Generated STEP and STL files (not tracked in git)
- `main.py` - Entry point that builds and exports all models

## Model Pattern

Each model file follows this structure using **builder mode**:

```python
from build123d import BuildPart, Box, Part, export_step, export_stl
from ocp_vscode import show

def create_thing() -> Part:
    with BuildPart() as builder:
        # Build geometry here
        Box(10, 10, 10)
    return builder.part

def main() -> None:
    part = create_thing()
    show(part)
    export_step(part, "exports/thing.step")
    export_stl(part, "exports/thing.stl")
```

## build123d Style

Always use **builder mode** (`BuildPart`, `BuildSketch`, `BuildLine` context managers), not algebra mode. This provides a consistent sketch-driven CAD workflow across all models.

## Viewer Interaction

The `viewer.py` module provides programmatic control of the OCP viewer for visual feedback:

```python
from viewer import show_and_screenshot, set_camera, screenshot, view_iso, view_top

# Show object and take screenshot from specific view
path = show_and_screenshot(part, "exports/screenshot.png", view="ISO", zoom=1.0)

# Convenience functions for common views
view_iso(part, "exports/iso.png")
view_top(part, "exports/top.png")
view_front(part, "exports/front.png")

# Camera presets: ISO, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK
set_camera(view="FRONT", zoom=1.5)
```

**Requires the viewer server running:** `uv run python -m ocp_vscode`
