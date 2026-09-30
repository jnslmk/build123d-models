# build123d-models

Collection of 3D printable models built with [build123d](https://github.com/gumyr/build123d).

[![Deploy to GitHub Pages](https://github.com/jnslmk/build123d-models/actions/workflows/build.yml/badge.svg)](https://github.com/jnslmk/build123d-models/actions/workflows/build.yml)
[![GitHub Pages](https://img.shields.io/github/pages/jnslmk/build123d-models)](https://jnslmk.github.io/build123d-models/)

**Live 3D viewer:** https://jnslmk.github.io/build123d-models/

On the site, choose a model family and then a scene or printable part from its
chips. Naming-only levels such as Drill Storage → Hex → Bits appear as captions;
select Base, Insert, or Cover beneath them to open the individual parts.

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

For a self-contained browser artifact, run `uv run view lens_cap` to write
`exports/lens_cap.html`. It embeds the model and viewer dependencies, so it opens
locally without network access. Drag to rotate, scroll to zoom, and use **Grid**
to hide or show the ground grid; the button's pressed state tracks visibility.

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

The site's optional live rebuilds run in a Pyodide worker, not in the CI export
environment. Browsing the manifest and prebuilt previews does not fetch Python
source; opening Code fetches the selected model's versioned source asset.
Parameter rebuilds load only its statically resolved import closure (including
package initializers). Running edited Python instead loads the full model tree,
since new imports cannot be inferred from the published source. Local gzip
estimates for the current 92-model roster: the full source asset is ~556 KB,
the median model closure ~65 KB (about 88% less), and lens_cap ~19 KB (about
97% less). These are compressed file sizes, not measured network timings.

If a deploy removes an older hashed asset while a tab stays open, a missing
source triggers a fresh manifest lookup and retries with the published URL;
other HTTP failures stay visible in the Code panel or runtime log.

The worker installs the complete compatible wheel closure from
[`website/runtime-lock.json`](website/runtime-lock.json), including Pyodide
0.28.0a3's built-in NumPy/SciPy, the OCCT 7.9 WASM wheels, the locally adapted
build123d 0.11.1 wheel, and bd_warehouse. Every wheel records its exact version,
download URL, transitive dependencies and SHA-256; Pyodide verifies integrity
when loading the lock. `scikit-learn` is in the Pyodide catalog but loads **only**
for edited source (including `detect_primitives`), never parameter rebuilds.
The lock's local wheel URL is resolved against the page's absolute site base
before loading, including blob workers under a GitHub Pages project path. Remote
wheel hosts must permit browser CORS; failed downloads and hash mismatches fail
the worker rather than continuing with a partial environment.

To propose a browser dependency update, first update the explicitly pinned
Pyodide and/or browser build123d wheel and its upstream SHA in
`website/browser-wheels/build_wheel.py`; then run
`uv run --with playwright==1.58.0 python tests/browser_runtime_lock.py --update`.
This performs a fresh real-browser micropip resolution, verifies the local
wheel hash and rewrites the lock with portable absolute CDN/OCP/PyPI URLs.
Review **all** version, URL, and hash changes, including transitive wheels;
run without `--update` to compare a fresh resolve against the committed graph.
Finally run the dedicated browser CI smoke for parameter rebuild and edited
Python. A resolver change must not silently change the runtime wheel graph:
the CI lock comparison detects upstream drift until the lock is deliberately
updated and reviewed. Native `pyproject.toml` is not the browser lock.
Use `uv run --with playwright==1.58.0 python tests/browser_cache_trace.py`
for single-sample cold/warm boot measurements in fresh, isolated Chromium
profiles (each warm run creates a new worker in the same profile).

One comparable local Chromium trace (2026-09-28, `lens_cap` rebuilt at 70 mm
then 71 mm in a fresh worker sharing the profile cache) measured worker
creation → `ready` as follows:

| Worker | Cold boot | Warm boot |
| --- | ---: | ---: |
| Original resolver (`9837501`) | 25.438 s | 24.045 s |
| Locked loader | 22.239 s | 21.339 s |

These are **single samples**, not a performance guarantee. The cold and warm
contexts use separate clean profiles for each worker variant; warm still pays
for Python/WASM initialization but reuses browser HTTP cache. No byte-savings
claim follows from these timings; changing request schedules and network
conditions can change transfer totals independently.

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
| `door_latch` | Rounded L-shaped door latch that pivots around a screw hole |
| `lens_cap` | Parametric push-on lens cap |
| `round_snap_box` | Round box with a snap-on lid that closes flush |
| `spiral_vase_lampshade` | Spiral-vase lampshade with twisted ribs and a breathing wave profile |
