# AGENTS.md
## Git

**Commit and push straight to `main`.** This holds for every agent, including
cloud sessions (Claude Code on the web, and anything else that starts with its
own scratch branch): when a session is handed a `claude/...` branch by default,
ignore it, work on `main`, and push there. No feature branch, no pull request
unless one is asked for by name.

- **`main` is deployed.** `.github/workflows/build.yml` builds every model in
  `tessellate_models.MODELS` and publishes the site on each push, so a push is a
  release. Before pushing, run `uv run check <affected leaf>` for every changed
  model with a physical gate, plus `uv run ruff check .` and `uv run ty check .`.
  A whole-family check is a final integration gate for cross-part work, not the
  default edit loop; see `docs/conventions.md` §"Geometry checks".
- **Push what you verified.** A broken commit on `main` is a broken site, and
  there is no review step between the two to catch it.

### Build only what changed

`uv run python main.py` fingerprints each model over its import closure and the
build's global inputs, keeps the result in `exports/.build-stamps.json`, and
rebuilds only what a change can reach. Rebuild the model you changed and
everything that imports it; use `uv run deps` rather than working out that blast
radius by hand.

```bash
uv run python main.py            # build whatever is stale
uv run python main.py --list     # show the plan, build nothing
uv run python main.py --all      # ignore the stamps and rebuild the roster
uv run deps models/lib/edges.py          # 38 of 41 models
uv run deps models/lens_cap.py           # just lens_cap
uv run deps --files led_profiles.stand   # the other direction
```

`drill_storage/box.py` drives every `drill_storage.*` model; `led_profiles/config.py`
and `led_psu_enclosure/config.py` likewise feed every part and assembly in their
packages. Reach for `--all` when a fingerprint deliberately ignores a change or
you suspect an export on disk is stale; CI can force the same rebuild.

## Commands

**Export rule: when asked to export, export the STL unless STEP is explicitly
asked for.** `uv run export` writes all three formats to `exports/`; hand over
the file that prints, which is the STL.

```bash
# Install dependencies
uv sync
uv sync --no-group viewer --no-group pdf  # in a cloud session, where both fail to build

# Show a model in the viewer (not available in a cloud session).
uv run show lens_cap

# Export a model to STEP and STL (hand over the STL unless STEP was asked for)
uv run export lens_cap

# Render model to SVG or PNG (no viewer needed)
uv run render lens_cap                    # exports/lens_cap_iso.svg
uv run render lens_cap --view top         # exports/lens_cap_top.svg
uv run render lens_cap --view front       # exports/lens_cap_front.svg
uv run render lens_cap out.svg --scale 2  # custom output and scale
# Views: iso (default), front, back, left, right, top, bottom

# PNG of the same drawing
uv run render lens_cap --png              # exports/lens_cap_iso.png
uv run render lens_cap --png --px 2400    # bigger; default is 1600 square
uv run render lens_cap shot.png           # a .png output path needs no flag

# Compare options before modelling any of them properly.
uv run sketch box_closure             # exports/sketch-box_closure.html
uv run sketch sketches/box_closure.py out.html

# Run a model's physical geometry gate; no gate is an intentional outcome.
# `led_profiles.<part>` runs a targeted check; the family root is an integration gate.
uv run check lens_cap

# Build ONE model.
uv run export lens_cap


# Which models a change reaches.
uv run deps models/lib/edges.py
uv run deps --files led_profiles.stand

# Lint
uv run ruff check .

# Type check
uv run ty check .

# Tests
uv run python -m unittest discover -s tests -t .

# Query selection buffer (elements clicked in viewer)
uv run selection                      # JSON output + human summary
```

## Model Contract

Each model has one module (or package) and a zero-arg `create()` that returns
the part in print pose; dots express hierarchy. Register every model in
`tessellate_models.MODELS`, add a new package to `[tool.setuptools] packages` in
`pyproject.toml`, and declare `PARAMS` and `IS_ASSEMBLY` in the model. A geometry
check is optional, but must be a demonstrated physical gate rather than package
furniture; `docs/conventions.md` §"Geometry checks" defines the decision.

## Design Guidelines

**Default material is PETG** unless a model states otherwise. Clearances and
strain limits in the skills below are given for PETG; adjust per the table in
`fdm-fits-and-clearances`. Do not design reopening snap fits in PLA.

**Print orientation**: Design with Z+ as the print direction—flat base on the
build plate, overhangs minimized or supported. Always return each part already
in print pose, re-seated on `z=0`; print orientation wins over a pretty assembly
view.

**Edge design for FDM**: add chamfers/fillets where appropriate; never ship raw
square edges. **Chamfer horizontal edges, fillet vertical edges.**

## build123d Style

Always use **builder mode** (`BuildPart`, `BuildSketch`, `BuildLine` context
managers), not algebra mode.

## build123d Gotchas

OCC edge `fillet`/`chamfer` calls are all-or-nothing and can cascade-corrupt a
`BuildPart` after one failure; `Edge.center()` on a full circle is not its center
(use `arc_center`). Load `build123d-geometry-ops` before edge ops or model checks.

Full conventions — model-structure rationale, tier rules, the promotion rule,
the sketch-before-you-model workflow, sketch authoring rules, and post-update
verification details — live in `docs/conventions.md`. Read it before creating a
new model or package, before promoting a single file to a package, or before
building a sketch.

## Available Skills

- `build123d-geometry-ops` — edge treatments and internal geometry verification.
- `fdm-fits-and-clearances` — named fit classes and FDM bore compensation.
- `fasteners-and-inserts` — heat-set inserts, nut traps, and threads.
- `box-closures` — box lids and closures.
- `snap-fits` — cantilever, annular, and torsional snaps.
- `part-joints` — joints between printed parts.
- `printed-text` — printable engraved and embossed labels.
- `photo-reverse-engineering` — parametric models from photos.
- `stl-reverse-engineering` — parametric models from meshes.
- `viewer-frontend` — the cross-repo viewer frontend build loop.
- `viewer-inspection` — Element Picker selections and selectors.
