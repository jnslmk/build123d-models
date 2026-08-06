# build123d-models

Collection of 3D printable models built with [build123d](https://github.com/gumyr/build123d).

[![Deploy to GitHub Pages](https://github.com/jnslmk/build123d-models/actions/workflows/build.yml/badge.svg)](https://github.com/jnslmk/build123d-models/actions/workflows/build.yml)
[![GitHub Pages](https://img.shields.io/github/pages/jnslmk/build123d-models)](https://jnslmk.github.io/build123d-models/)

**Live 3D viewer:** https://jnslmk.github.io/build123d-models/

## Setup

```bash
uv sync
```

## Viewing Models

```bash
uv run show cube
```

The viewer starts in the background on first use and stays open, so subsequent
`uv run show` calls just swap the model in it.

Models are addressed by **name**, and a name is a module path under `models/`
with dots for directories:

```bash
uv run show led_profiles                      # models/led_profiles/__init__.py
uv run show led_profiles.stand                # models/led_profiles/stand.py
uv run show led_profiles.assemblies.standing  # one directory deeper
```

The same name works for `export`, `render`, `render-a4` and `check`.

## Rendering to SVG

Generate SVG projections without a viewer:

```bash
uv run render cube                    # exports/cube_iso.svg
uv run render cube --view top         # exports/cube_top.svg
uv run render cube --view front       # exports/cube_front.svg
```

Available views: `iso`, `front`, `back`, `left`, `right`, `top`, `bottom`

## Rendering DIN A4 PDF Sheets

Generate a DIN A4 PDF with top, front, left, and isometric views:

```bash
uv run render-a4 cube
uv run render-a4 door_latch exports/door_latch_views.pdf
```

## Exporting

A single model, to `exports/`:

```bash
uv run export cube                    # STL (+ per-child STLs, + GLB)
uv run export cube --step             # also STEP
```

All of them — incremental, so this only rebuilds what your change can reach, and
builds those in parallel:

```bash
uv run python main.py            # whatever is stale
uv run python main.py --list     # what that would be, and why
uv run python main.py --all      # the whole roster regardless
```

`uv run deps <path>` answers the same question on its own, if you just want to
know what a file feeds into.

## Checking

Ribs, wall gaps and fit clearances are invisible in a projection, so models
verify themselves in code. `check` runs those assertions and exits non-zero when
they fail:

```bash
uv run check led_psu_enclosure
```

## Repository Structure

```text
models/          the models — one file or one package each
models/lib/      helpers shared across models (edges, checks, fits)
exports/         generated STL / STEP / GLB / renders (untracked)
website/         the static Pyodide site
docs/plans/      design documents
tests/           unittest suite (uv run python -m unittest discover -s tests -t .)
```

A model is either a **single file** (`models/cube.py`) or a **package**
(`models/led_psu_enclosure/`) — nothing in between. Both expose a zero-arg
`create()` returning the part in its print pose, which is the only thing every
entry point needs. A package additionally carries its own `config.py`, one
module per printable part, `checks.py`, a `README.md` and a `docs/` folder, and
is the required shape as soon as a model grows a second part, a second view,
measured hardware constants, or a sibling that imports from it.

`tessellate_models.MODELS` is the single roster: `main.py`, the website and CI
all build from it, so adding a name there is the whole procedure for publishing
a model.

The full specification — the promotion rule, naming, where shared geometry goes,
how a model gets registered, and the places the tree still deviates — is in
[AGENTS.md](AGENTS.md#model-structure).

## CI/CD

<!-- Trigger rebuild: Pages reset attempt #3 -->

Every push to `main` automatically:
1. Builds all models
2. Generates SVG renders (iso, top, front views)
3. Deploys to GitHub Pages

View live at: https://jnslmk.github.io/build123d-models/

## Models

Packages — each has its own README with the full story:

| Model | Description |
|-------|-------------|
| [`drill_storage`](models/drill_storage/README.md) | Gridfinity drill holders, one per tool set (`.wood`, `.metal`, `.stone`) — a rigid ASA shell that guides, a compliant TPU cartridge that grips, and a labelled PETG cover, plus `.hex` for driver bits |
| [`led_profiles`](models/led_profiles/README.md) | Modular 24 V addressable COB linear lamp system: endcap, corner, strap, stand, feet, and three mounting scenes |
| [`led_psu_enclosure`](models/led_psu_enclosure/README.md) | Weatherproof enclosure for a 24 V LED driver stack, with sliding-shutter vents and an optional fan yoke |

Single-file models:

| Model | Description |
|-------|-------------|
| `cube` | Simple parametric cube — the minimal example |
| `door_latch` | Rounded L-shaped door latch that pivots around a screw hole |
| `slotted_plate` | Door latch plate: slot with a tapered entry ramp |
| `lens_cap` | Parametric push-on lens cap |
| `round_snap_box` | Round box with a snap-on lid that closes flush |
| `satellite_led` | Hexagonal rod with WS2811 strips, parabolic mirror and diffuser |
| `spiral_vase_lampshade` | Spiral-vase lampshade with twisted ribs and a breathing wave profile |
| `wall_bar_lamp` | Wall-mounted linear bar lamp, double-ended tube sconce |
