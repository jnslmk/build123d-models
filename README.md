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
uv run show lens_cap
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
uv run render lens_cap                    # exports/lens_cap_iso.svg
uv run render lens_cap --view top         # exports/lens_cap_top.svg
uv run render lens_cap --view front       # exports/lens_cap_front.svg
```

Available views: `iso`, `front`, `back`, `left`, `right`, `top`, `bottom`

## Rendering DIN A4 PDF Sheets

Generate a DIN A4 PDF with top, front, left, and isometric views:

```bash
uv run render-a4 lens_cap
uv run render-a4 door_latch exports/door_latch_views.pdf
```

## Exporting

A single model, to `exports/`:

```bash
uv run export lens_cap                    # STL (+ per-child STLs, + GLB)
uv run export lens_cap --step             # also STEP
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

A model is either a **single file** (`models/lens_cap.py`) or a **package**
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

Every push to `main` automatically:
1. Builds all models
2. Generates SVG renders (iso, top, front views)
3. Publishes the site to the root of the `gh-pages` branch

View live at: https://jnslmk.github.io/build123d-models/

**Every pull request gets its own copy of that site**, published to
`https://jnslmk.github.io/build123d-models/pr-<number>/` and linked from a
comment on the PR. It is rebuilt on each push to the branch and deleted when
the PR closes ([`pr-preview-cleanup.yml`](.github/workflows/pr-preview-cleanup.yml)),
so a change to a model can be looked at on the real site before it is merged.
Pull requests from forks get no preview: their token is read-only by design.

Both the production site and the previews are directories on one branch,
because GitHub Pages serves exactly one source per repository. That is why the
repository's **Settings → Pages → Source** must be *Deploy from a branch →
`gh-pages` / `(root)`*, and not "GitHub Actions" — with the Actions source,
`main` would publish fine and every preview would be pushed to a branch nobody
serves. [`.github/scripts/publish-pages.sh`](.github/scripts/publish-pages.sh)
is the one thing that writes that branch, for all three of deploy, preview and
cleanup.

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
| `door_latch` | Rounded L-shaped door latch that pivots around a screw hole |
| `lens_cap` | Parametric push-on lens cap |
| `round_snap_box` | Round box with a snap-on lid that closes flush |
| `spiral_vase_lampshade` | Spiral-vase lampshade with twisted ribs and a breathing wave profile |
