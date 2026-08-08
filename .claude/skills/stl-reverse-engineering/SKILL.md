---
name: stl-reverse-engineering
description: >-
  Turns an STL or other triangle mesh into parametric build123d source in this
  repo. Analyses a mesh to find its extrusion axis, extracts the dominant
  cross-section, maps the model into feature zones, generates builder-mode
  build123d code, and grades the reconstruction against the original by
  intersection-over-union. Classifies through-holes, blind holes, counterbores,
  countersinks and their grid, radial or linear patterns in mesh_zones.py, and
  ships a reproducible eval harness under eval/ that pins the round-trip accuracy
  claims to real script output rather than prose. Use when a downloaded, scanned
  or exported mesh must become editable CAD, when a model needs to be resized or
  refitted but only an STL exists, when an existing STL must be measured or its
  structure understood, when reconstructing a part from a mesh, or when checking
  how closely a rebuilt part matches the mesh it came from. Keywords - STL, mesh,
  reverse engineer, reconstruct, remodel, import STL, mesh to CAD, mesh to
  build123d, parametric from mesh, triangle mesh, 3MF, OBJ, PLY, IoU, accuracy,
  Thingiverse, Printables, downloaded model, scan, hole feature, counterbore,
  countersink, hole pattern, eval harness. Load BEFORE running `mesh_analyze.py`,
  `mesh_zones.py` or `mesh_compare.py`, or before writing build123d code from a
  mesh — the swept/actual pre-check decides whether reconstruction is even the
  right move before any code is generated. TRIGGER: about to import or
  reconstruct an STL/3MF/OBJ/PLY, measure an existing mesh's structure or hole
  features, grade a rebuilt part's IoU against its source mesh, or run the eval
  harness after changing the pipeline.
---

# STL reverse engineering

Turning a triangle mesh back into parametric build123d source. A mesh carries no
semantics — no primitives, no operations, no dimensions — so reconstruction means
measuring the geometry and re-expressing it as code.

## Setup

The tooling needs a dependency group that is deliberately **not** installed by
default, so CI and the site build never touch it:

```bash
uv sync --group mesh
```

Every command below uses `uv run --group mesh`. `.github/workflows/build.yml`
runs plain `uv sync --frozen`, which skips this group — nothing here can break a
model build or a deploy.

## Do not reach for OCC

`build123d.import_stl()` returns a single invalid `Face` with the triangulation
attached and no topology. **Sectioning it segfaults the interpreter** (measured:
exit 139 on every STL tried, including a 12-triangle cube).

The workable OCC route — read triangles with `RWStl`, build a face each, sew,
make a solid — works but does not scale:

| STL | triangles | sew | one section |
|---|---|---|---|
| `cube.stl` | 12 | 0.00 s | 0.01 s |
| `door_latch.stl` | 1,552 | 0.51 s | 0.51 s |
| `led_profiles.stand.stl` | 34,714 | **47.3 s** | **6.71 s** |

Axis detection alone takes 64 slices × 3 axes. In trimesh that is **0.129 s**; in
OCC it is roughly 7 minutes of sectioning on top of a 47 s sew. Mesh analysis
happens in trimesh/shapely. build123d is the **output** side only.

## The workflow

### 1. Analyse

```bash
uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_analyze.py \
    model.stl --out analysis/
```

Reports triangle count, watertightness, both candidate extrusion axes, and
`swept/actual`. Writes `analysis/analysis.json` and `analysis/reconstructed.py`.

**Read `swept/actual` before anything else.** It is the profile area × extrusion
length over the mesh's real volume, and it predicts the result before you spend
anything:

- **0.97–1.03** — a real extrusion. `reconstructed.py` is close to final.
- **> 1.3** — not an extrusion. Do not touch the generated file; go to step 2.

### 2. Decompose (only when step 1 says it is not an extrusion)

```bash
uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_zones.py \
    model.stl --out analysis/
```

Slices all three axes coarse-then-fine and collapses them into typed zones —
`solid`, `solid_with_holes`, `shell_or_channel`, `multi_body` — each with the
build123d operation that rebuilds it. It flags zones whose width drifts, which
is a taper or fillet rather than a straight extrude.

Build one zone at a time. The axis with the fewest zones is usually the one to
decompose along.

### 3. Grade

```bash
uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_compare.py \
    model.stl rebuilt.stl
```

Exact IoU via manifold3d booleans (milliseconds), falling back to Monte-Carlo
sampling when a mesh is too dirty for a boolean. **Exits non-zero below 95%**, so
it can gate a loop.

IoU is the number that matters — not volume, not bounding box. A part can match
both and still be the wrong shape.

## The rules that cost the most when broken

1. **Never add a feature you have not seen in slice data.** Renders produce
   phantom geometry — a shadow reads as a pyramid, a curved wall edge reads as a
   cylinder. If it is not a contour in the slice data, it does not exist.
2. **Volume and bbox can both match a wrong shape.** Use IoU.
3. **When the stability axis and the thinnest axis disagree**, and the model has
   diagonal features, take the thinnest axis.
4. **Build the whole solid, then subtract.** All additive work first, every
   `Mode.SUBTRACT` last.
5. **Past ~200 profile points, stop adding vertices.** Curves need `Circle()`,
   not a finer polygon.

Full detail, the per-geometry technique table, and the tolerance/accuracy
measurements are in `references/reconstruction-guide.md`. Read it before any
reconstruction that is not a plain extrusion.

## Closing the loop

Steps 2 and 3 are a decomposition and a numeric gate, which is everything a
builder/critic loop needs — but nothing above says to *run* one, and doing it by
hand one zone at a time is the slow way through a multi-zone part.

Fan out instead: one subagent per zone from `mesh_zones.py`, each with a
separate critic subagent that sees the zone's slice contours and its
`mesh_compare.py` output but **not** the builder's reasoning. Loop a zone until
its gate passes; cap it at three rounds, because a zone that has not converged
by then is blocked on information the mesh does not contain, and the useful
result is saying which.

Two rules make this work rather than burn tokens:

1. **The bar is the exit code, never an opinion.** `mesh_compare.py` already
   exits non-zero below 95%. A critic that reports "looks close" has reported
   nothing. This is the one thing to get right if you are adapting a loop
   pattern from elsewhere — see `photo-reverse-engineering`'s
   `references/gauntlet-loop.md` for where that framing comes from and what it
   costs to copy an aesthetic bar verbatim.
2. **Do not start with the loop.** `swept/actual` is already this rule in
   numeric form: above 1.3, no number of critic rounds will turn the generated
   extrusion into the right part, and the loop will spend hours refining a shape
   that was never close. Decompose first, then loop per zone.

An IoU gate has the same blind spot a visual one does, and it is worth naming:
`mesh_compare.py` grades a *solid*, so it does see internal voids — but the
zone-level slice contours a critic reads do not distinguish a blind pocket from
a through hole at the same diameter. Point-sample the rebuilt solid
(`is_solid_at`, per `build123d-geometry-ops`) rather than trusting a contour.

## Round-trip validation

Export a model this repo already has, reconstruct it blind, compare to the
original. Measured:

| Model | swept/actual | Predicted | IoU |
|---|---|---|---|
| `cube` | 1.000 | clean extrusion | **100.00%** |
| `door_latch` | 0.997 | clean extrusion | **99.60%** |
| `led_profiles.stand` | 2.137 | not an extrusion | **38.91%** |

The stand is a correct *negative*: the tool predicted failure before generating
code, and `mesh_compare.py` returned "wrong shape — do not iterate". A tool that
reported 38.91% as a success would be worse than no tool.

## A reconstruction is not yet a model

The generated file is a starting point. A 200-point literal polygon is not
parametric — it cannot be resized and it satisfies nothing in `AGENTS.md`.

Before it belongs in `models/`: replace polygon runs with named parametric
geometry, pull hardware dimensions into constants checked against
`fdm-fits-and-clearances` (the mesh encodes the *original* designer's clearances,
not ours), re-apply edge treatments as real operations rather than inherited
faceting, put the part in print pose on `z=0`, and give it checks.

Reconstructed models are also the one case where the mesh's own dimensions are
untrustworthy input: they already include the source designer's tolerances,
shrinkage compensation and printer quirks. Re-derive fits from
`fdm-fits-and-clearances` instead of copying them.

`photo-reverse-engineering` ends at the same place from a weaker input. If only
photos exist, go there; if both exist, start here, because a mesh has real
dimensions and a photo does not.

## Attribution

The analysis approach — stability-scored axis detection, coarse-then-fine
adaptive slicing, the zone taxonomy, the accuracy targets and the
feature-hallucination warnings — is adapted from
[andreahaku/openscad_claude_skill](https://github.com/andreahaku/openscad_claude_skill),
MIT licensed. Its output targeted OpenSCAD; the code generation, the plane
handling, the `swept/actual` pre-check and the IoU grading here are this repo's.

Note for anyone reading that repo: its `SKILL.md` documents an
`openscad-auto-reconstruct.py` at length. That file is not in the repository.
