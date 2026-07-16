# AGENTS.md

## Commands

```bash
# Install dependencies
uv sync

# Show a model in the viewer (starts viewer in background if needed)
uv run show cube

# Export a model to STEP and STL (no viewer)
uv run export cube

# Render model to SVG (no viewer needed)
uv run render cube                    # exports/cube_iso.svg
uv run render cube --view top         # exports/cube_top.svg
uv run render cube --view front       # exports/cube_front.svg
uv run render cube out.svg --scale 2  # custom output and scale

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

## SVG Rendering (Headless)

Use `uv run render` to generate SVG projections without a viewer server:

```bash
uv run render <model> [output.svg] [--view VIEW] [--scale SCALE] [--no-hidden]
```

Views: `iso` (default), `front`, `back`, `left`, `right`, `top`, `bottom`

This is the preferred method for agent workflows since it requires no running server.

## Viewer

The `show` command automatically starts the pywebview viewer in the background if not already running.

## Element Picker

The viewer includes an Element Picker tool for interactive geometry selection:

1. Click the crosshairs button in the toolbar (or activate Picker tool)
2. Click on faces/edges/vertices in the 3D view
3. Overlay shows: element type, geometry info, and build123d selector
4. Selector auto-copies to clipboard
5. Click again to deselect (toggle behavior)
6. Press Escape to clear all selections

**For AI agents:** Use `uv run selection` to retrieve selected elements as JSON with suggested selectors.

## Viewer Development

This project uses a local development setup with three related repositories:

- `build123d-models/` - This repo (Python CAD models)
- `vscode-ocp-cad-viewer/` - Python backend + VS Code extension
- `three-cad-viewer/` - JavaScript frontend (Three.js viewer)

### Frontend Build Workflow

When modifying the viewer frontend (e.g., adding tools, changing UI):

```bash
# 1. Make changes in three-cad-viewer
cd ~/git-projects/three-cad-viewer
# ... edit src/cad_tools/, src/viewer.js, etc.

# 2. Build the frontend bundle
npm run build

# 3. Copy built files to vscode-ocp-cad-viewer
cp dist/three-cad-viewer.esm.js ~/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/js/
cp dist/three-cad-viewer.css ~/git-projects/vscode-ocp-cad-viewer/ocp_vscode/static/css/

# 4. Test with a model from this repo
cd ~/git-projects/build123d-models
uv run show cube
```

The JS/CSS files in vscode-ocp-cad-viewer are gitignored (they're built artifacts). Changes to the frontend require commits in three-cad-viewer, not vscode-ocp-cad-viewer.

## Design Guidelines

**Print orientation**: Parts print bottom-to-top in layers. Design with Z+ as the print direction—flat base on the build plate, overhangs minimized or supported.

**Edge design for FDM**: Use chamfers (45°) on horizontal edges, fillets on vertical edges. This accounts for how layers stack—chamfers print cleanly on horizontal surfaces while fillets work better on vertical walls.

**Holes & tool inserts (drill holders, bit trays, etc.)**:

- **Never cut a bore at exactly the nominal diameter.** FDM prints small vertical holes ~0.1–0.3 mm *undersized* (the nozzle drags the inner perimeter inward), so a nominal bore ends up a press fit. Add a diametral clearance (~0.4–0.5 mm for an easy drop-in tool fit; wood/brad-point bits want the looser end because their spurs cut over the shank). Expose it as a constant, not a magic number.
- **Prefer ribbed bores for a robust, variation-tolerant grip.** Cut the bore a little wider (a valley), then add 3 rounded internal ribs so the tool rides on three line-contacts instead of a full-circle wall. This drops in cleanly and keeps a light, even grip regardless of layer scarring or bore shrinkage. See `models/drill_storage_gridfinity.py::create_base(ribbed=True)` (`RIB_COUNT`/`RIB_RELIEF`/`RIB_TOP_GAP`). Stop the ribs a few mm below the mouth so the opening stays a clean circle for the lead-in.
- **Always add a lead-in at every hole mouth** so bits self-guide. A fillet (rounded) or chamfer both work; fillet doubles as a print-friendly funnel.
- **Ribbed/wider bores need more room.** Keep walls between neighbouring bores ≥ ~0.8–1.2 mm (2–3 perimeters at a 0.4 mm nozzle); re-space a tight layout rather than letting bores merge (a <~0.3 mm gap won't slice as a wall).

**Telescoping / mating parts**: mating faces must have the *same* geometry — flat-on-flat or chamfer-on-chamfer. A straight rim landing on a chamfered shoulder only makes a thin line contact and wobbles. Also watch for one part being slightly wider than the other (e.g. a 42 mm cover over a 41.5 mm Gridfinity body): chamfer the wider part's mating edge so it seats flush instead of overhanging.

## build123d Gotchas

- **`Edge.center()` on a full circle returns a point *on* the curve, not the centre.** When selecting a circular hole mouth by position, use `edge.arc_center` (guard with try/except for non-circular edges, which raise `ValueError`). Line edges (e.g. hex sockets) can use `.center()` (midpoint).
- **`fillet`/`chamfer` are all-or-nothing over the edge set you pass.** One edge that can't take the radius (e.g. beside a thin wall) fails the whole call. Wrap in `try/except` and, if it matters, retry with a decreasing radius ladder so each feature still gets the largest fillet that fits.
- **Selecting edges then filleting in a loop:** each fillet changes the topology and invalidates stale edge references. Select/fillet **per feature** and **re-query the live edges** (`base.edges()...`) each pass rather than reusing a list captured up front.
- **Verify internal geometry in code**, not just the viewer. Ribs, wall gaps, and fit clearances aren't visible in a projection — point-sample the solid with `OCP.BRepClass3d.BRepClass3d_SolidClassifier` (`.Perform(gp_Pnt, tol)` → `TopAbs_IN`) to confirm ribs exist, walls are solid, and mouths widened.
