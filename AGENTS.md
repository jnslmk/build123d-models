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

- `models/` - The models themselves, one module or one package each (see **Model Structure**)
- `models/lib/` - Helpers shared *across* models: `edges`, `checks`, `fits`
- `exports/` - Generated STL / STEP / GLB / render assets (not tracked in git)
- `tessellate_models.py` - `MODELS`, the one roster the website, CI and `main.py` read
- `main.py` - Builds and exports every model in `MODELS`
- `show.py` / `export_model.py` / `check.py` / `render_svg.py` - the `uv run` entry points
- `website.py` - Builds the static site bundle from `MODELS`

Every entry point addresses a model by **name**, and a name is a *module path under
`models`* with dots for directories: `cube` is `models/cube.py`,
`led_profiles.stand` is `models/led_profiles/stand.py`,
`led_profiles.assemblies.standing` is nested one deeper. They all do the same
thing — import `models.<name>` and call its zero-arg `create()`. Nothing else is
needed to make a model showable, exportable, renderable and downloadable.

## Model Structure

A model is either **one file** or **one package**. There is no third shape, and
which one a model gets is decided by the promotion rule below, not by taste.

### Tier 1 — single-file model

```text
models/<name>.py
```

For a model that is one part, built in one file, that nothing else imports. Keep
it a single file for exactly as long as all of that stays true.

### Tier 2 — model package

```text
models/<name>/
  __init__.py      # headline create(), IS_ASSEMBLY, re-exports, the docstring people read first
  config.py        # measured + derived numbers. No geometry.
  <part>.py        # one printed part per module, each with its own create()
  assemblies/      # scenes, one module each, each IS_ASSEMBLY = True
  printable.py     # print layout for the slicer, when the headline view is a scene
  checks.py        # geometry assertions, with a main() that owns the exit code
  README.md        # what it is, what hardware it fits, how to print it
  docs/            # design-notes.md, part-data.md, assets/ (datasheets, SVGs)
```

Not every package needs every entry — `config.py`, `assemblies/`, `printable.py`
and `docs/` appear when the model earns them. `__init__.py`, `README.md` and
`checks.py` are the floor.

### The promotion rule

Promote a single file to a package as soon as **any one** of these becomes true.
Do not wait for the second one:

1. **A sibling wants to import from it.** One model reaching into another
   model's module is the signal that they are one family sharing one library.
2. **It grows a second showable view or a second printable part.** Each of them
   needs its own module to be addressable by name.
3. **It needs measured hardware constants.** Those belong in a `config.py` next
   to the geometry that consumes them, not scattered as module-level literals.
4. **It earns geometry assertions or written design notes.** `checks.py`,
   `README.md` and `docs/` are package furniture.

The promotion is mechanical: `models/<name>.py` becomes
`models/<name>/__init__.py`, the shared numbers move to `config.py`, each part
moves to its own module, and the roster names gain a dot. The website resolves a
package name to its `__init__.py` automatically (`website._source_path`), so the
Code panel keeps working.

### Rules that hold in both tiers

- **`create()` is the contract.** Zero-arg (or all-defaulted), returns a `Part`
  or `Compound` **already in print pose**. Every entry point calls exactly this.
  Named builders (`create_endcap()`, `create_print_layout()`) are welcome
  alongside it, but `create()` is what the tooling binds to.
- **One model, one module.** If a view cannot be reached as
  `models.<something>`, it is not a model — it cannot be shown, exported,
  rendered or put on the site. Splitting a second scene into its own module
  costs nothing and buys it a name.
- **Never encode hierarchy in underscores.** A part of `drill_storage` is
  `drill_storage.wood`, not `drill_storage_wood`; its assembled view is
  `drill_storage.assemblies.wood`, not `drill_storage_wood_assembly`. Dots are
  the hierarchy; underscores are only for multi-word single names.
- **No private cross-module imports.** `from models.other_model import _helper`
  means the two are one family: make it a package and make the helper public in
  a shared module.
- **Shared geometry goes down, not sideways.** Shared within one family →
  a module in that package (`led_profiles.cradle`). Shared across families →
  `models/lib/`, and only once it is genuinely needed twice.
- **Declare what the model is.** `PARAMS` (list of dicts) makes it parametric on
  the website; `IS_ASSEMBLY = True` marks a scene that is not a print job, so no
  STL/STEP download is offered. Both live in the model, never in a list
  elsewhere that would drift.
- **Verify in code.** A package gets `checks.py` with a `main()`; a single-file
  model gets a module-level `check()`. `uv run check <name>` finds either.
- **No `main()` in a model.** Building and exporting is `main.py`'s and
  `export_model.py`'s job, and a `main()` that re-implements the export paths
  drifts from them. `uv run show/export/render/check <name>` is the interface.
- **Docs live with the model.** A package: `README.md` plus `docs/`. A
  single-file model: the module docstring, which should say what it is, what it
  fits and how it prints.

### Registering a model

Add the name to **`tessellate_models.MODELS`**. That is the whole procedure —
`main.py` builds straight from that list, the website reads it, CI reads it, so
there is no second place to keep in sync and no way for them to disagree.

Only modules with a zero-arg `create()` belong there. The shared pieces a part is
built from (`drill_storage.box`, `led_profiles.cradle`, `led_psu_enclosure.config`,
`models/lib`) are not models. A new package also has to be added to
`[tool.setuptools] packages` in `pyproject.toml` — subpackages are not implied by
their parent, so a missing line ships a wheel without that model.

### Known deviations

Nothing to copy here — these are gaps, and closing one is welcome work:

- No single-file model has a `check()`, so `uv run check <flat-model>` prints
  "no checks defined" for all of them.
- `drill_storage` and `drill_fit_tester` have no `checks.py` yet, though
  `checks.py` is meant to be package floor. `led_profiles` and
  `led_psu_enclosure` are the two that carry real ones — read those for the
  shape a `checks.py` should take.

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
