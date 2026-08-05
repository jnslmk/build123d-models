# AGENTS.md

## Commands

```bash
# Install dependencies
uv sync

# Show a model in the viewer (starts viewer in background if needed)
uv run show cube

# Export a model to STEP and STL (no viewer)
uv run export cube

# Render model to SVG (no viewer needed) — preferred for agent workflows
uv run render cube                    # exports/cube_iso.svg
uv run render cube --view top         # exports/cube_top.svg
uv run render cube --view front       # exports/cube_front.svg
uv run render cube out.svg --scale 2  # custom output and scale
# Views: iso (default), front, back, left, right, top, bottom

# Run a model's geometry assertions, exit non-zero on failure
uv run check cube

# Build all models
uv run python main.py

# Lint
uv run ruff check .

# Type check
uv run ty check .

# Query selection buffer (elements clicked in viewer)
uv run selection                      # JSON output + human summary
```

## Post-Update Verification

After modifying any model, always verify it visually in the viewer:

```bash
uv run show <model_name>
```

This opens the model in the 3D viewer so you can confirm geometry, orientation, and colors before considering the task complete. **Always run `uv run show <model_name>` immediately after every edit to a model — do not wait to be asked — so the user can see the change live in the viewer.** It is the last step of any model change.

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

## Design Guidelines

**Default material is PETG** unless a model states otherwise. Clearances and strain limits in the skills below are given for PETG; adjust per the table in `fdm-fits-and-clearances`. Do not design reopening snap fits in PLA.

**Print orientation**: Parts print bottom-to-top in layers. Design with Z+ as the print direction—flat base on the build plate, overhangs minimized or supported. **Always return each part already sitting in its print pose** (the orientation it lands on the bed in): the model IS the print orientation, so the exported STL drops straight into the slicer with no re-orienting. Lids/caps/covers therefore get flipped upside down before returning—e.g. a cover built closed-top-up is rotated 180° so its open mouth faces up—and the whole part is re-seated on `z=0` (`part = Rotation(180, 0, 0) * builder.part; part = Pos(0, 0, -part.bounding_box().min.Z) * part`). This is a rigid transform, so it doesn't change the physical part—only how it's laid on the bed. If a part is shown in an assembly next to others, print orientation still wins over a pretty assembly view.

**Edge design for FDM**: always add chamfers/fillets where appropriate; never ship a part with raw square edges. One-line rule: **chamfer horizontal edges, fillet vertical edges.** Enforceable, not just advised: `sharp_convex_edges()` in `models/lib/checks.py` lets a model's `checks.py` fail on any sharp edge left untreated, and legitimate exceptions must be named in its `allow` list, not merely omitted. Full rationale, the DFM sources, and the exceptions live in `build123d-geometry-ops` and `fdm-fits-and-clearances` — read those before shaping a rim, lid, hole mouth, or joint.

## build123d Gotchas

OCC edge `fillet`/`chamfer` calls are all-or-nothing and can cascade-corrupt a `BuildPart` after one failure; `Edge.center()` on a full circle is not its center (use `arc_center`). Full failure semantics, snapshot-restore isolation, and the point-sampling verification pattern live in the `build123d-geometry-ops` skill — load it before touching edge ops or writing a model's checks.

## Available Skills

- `build123d-geometry-ops` — when to trust an OCC edge fillet/chamfer versus cutting a boolean chamfer instead, and how to verify internal geometry by point-sampling a solid.
- `fdm-fits-and-clearances` — the master clearance table: named fit classes (press/snug/sliding/free), per-material adjustments, and FDM bore-undersize compensation.
- `fasteners-and-inserts` — sizing heat-set inserts, nut traps, self-tapping screws, and printed/tapped threads, plus the `bd_warehouse` fastener catalog.
- `box-closures` — picking and sizing a box lid or closure (rabbet, snap bead, screw-on, hinge, dovetail, bayonet, magnet, gasket).
- `snap-fits` — sizing a cantilever, annular, or torsional snap fit against a material's permissible strain and checking deflection/mating force.
- `part-joints` — non-lid, non-fastener joints between two printed parts: dovetails, T-slots, pins, hinges, crush ribs, telescoping collars.
- `printed-text` — sizing and placing engraved or embossed labels so a 0.4 mm nozzle can actually resolve them.
- `viewer-frontend` — the cross-repo build loop for changing the viewer's frontend (three-cad-viewer → vscode-ocp-cad-viewer → this repo).
- `viewer-inspection` — using the viewer's Element Picker and `uv run selection` to turn a click into a build123d selector.
