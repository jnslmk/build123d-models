# Reconstruction guide

Adapted from [andreahaku/openscad_claude_skill](https://github.com/andreahaku/openscad_claude_skill)
(MIT). The failure modes and the accuracy targets are theirs, learned from real
reconstructions. The build123d mapping, the ordering rule and the measured
numbers below are this repo's.

## The five rules

### Rule 1 — Analyse before you write a single line

Run `mesh_analyze.py` first, always. It answers three questions in one shot: is
the mesh watertight, which axis is the extrusion direction, and is this even an
extruded part. Writing geometry before that is guessing.

### Rule 2 — Never add a feature you have not seen in slice data

This is the most expensive mistake and it comes from reading renders. From their
notes: a "cylinder" that was really a rounded slot floor, a "pyramid" that was a
shadow in the render and did not exist at all.

**If a feature does not show up as a separate contour in the slice data, it does
not exist.** `mesh_zones.py` prints the contour and hole count for every band of
the model. That is the evidence. A render is not.

### Rule 3 — Volume and bounding box can both match a wrong shape

A reconstruction can hit the bounding box to 0.000 mm and still be 70% wrong.
`mesh_compare.py` reports IoU (intersection over union) precisely because volume
and bbox do not catch a shape error — a part with the right amount of material
in the wrong places passes both.

It prints an explicit warning when volume matches within 1% but IoU is under 90%,
because that combination almost always means the profile went on the wrong axis.

### Rule 4 — Choose the extrusion axis by geometry, not only by the score

`mesh_analyze.py` reports two candidates and tells you when they disagree:

- **stability axis** — the axis whose cross-section changes least along it
- **thinnest axis** — the smallest of the three extents

| Model | Use | Why |
|---|---|---|
| Flat bracket or plate | Thinnest axis | The profile in the wide plane carries all the detail |
| Diagonal or angled arm | **Thinnest axis** | Diagonals live in the plane of the two longest axes; slicing across them gives staircase artifacts |
| Clean extrusion (stability < 0.1) | Stability axis | The profiles are genuinely identical, so the score is trustworthy |
| Rotationally symmetric | Neither — use `revolve()` | Reconstruct from a half-profile, not a stack of slices |
| No good axis (stability > 0.3) | Decompose first | Run `mesh_zones.py` and rebuild zone by zone |

When they disagree and the model has diagonal features, the thinnest axis wins.

### Rule 5 — Build the whole solid, then subtract

Add all material first, subtract every cut last:

```python
with BuildPart() as builder:
    # 1. every additive feature
    ...
    # 2. then every Mode.SUBTRACT
    ...
```

The source skill made this rule absolute because OpenSCAD's `difference()` only
applies to its immediate children, so material added afterwards silently covers
holes already cut. **build123d does not have that bug** — `Mode.SUBTRACT` is
applied against the whole builder state at the point of the call.

The rule still holds here, for a weaker but real reason: a subtraction that runs
before the material it was meant to cut exists is a silent no-op, and it leaves
no error behind. Keeping all cuts last makes that impossible by construction.

## Reading the pre-check

`mesh_analyze.py` reports `swept/actual` — the profile area times the extrusion
length, over the mesh's real volume. It costs nothing and it predicts the
outcome before any code is generated:

| swept/actual | Meaning |
|---|---|
| 0.97 – 1.03 | A genuine extrusion. Expect IoU > 99%. |
| 1.03 – 1.3 | Mostly extruded with material removed along the axis. Reconstruct, then subtract the difference. |
| > 1.3 | Not an extrusion. Do not iterate on the generated file — run `mesh_zones.py` and decompose. |
| < 0.97 | The profile missed part of the model. Usually a multi-body slice where only the largest contour was taken. |

Measured on this repo (round-trip: export a known model to STL, reconstruct
blind, compare against the original):

| Model | swept/actual | Predicted | Actual IoU |
|---|---|---|---|
| `cube` | 1.000 | clean | **100.00%** |
| `door_latch` | 0.997 | clean | **99.60%** |
| `led_profiles.stand` | 2.137 | not an extrusion | **38.91%** |

The pre-check is quantitatively predictive, not just directional: it warned
2.137× on the stand and the measured volume error was 2.14×.

## Accuracy targets

| Level | IoU | What it means |
|---|---|---|
| Excellent | > 98% | Production quality |
| Good | > 95% | Functional, ready for a test print |
| Draft | > 85% | Structure is right, details are not |
| Wrong | < 85% | Re-analyse. Do not iterate — you will polish a wrong shape. |

`mesh_compare.py` exits non-zero below 95% so it can gate a loop.

## Simplification tolerance

`--simplify` is the Douglas-Peucker tolerance in mm and it is the main quality
dial. From the source skill's measurements:

| Tolerance | Points | Accuracy |
|---|---|---|
| 0.3 mm | ~50 | 52% — curves collapse to flats |
| 0.05 mm | ~150 | 75% |
| 0.02 mm | ~230 | 75% — diminishing returns |

**Past ~200 points a polygon profile stops improving.** Curved features need
parametric primitives, not more polygon vertices. If the profile is mostly
circular, read the radius off the slice data and write `Circle(r)` by hand
instead of shipping a 230-point polygon.

## Technique per geometry

| Geometry | Approach | Expected |
|---|---|---|
| Flat, angular (brackets, plates) | Profile + `extrude()` | 90–96% |
| Diagonal features | Profile on the **thinnest** axis + `extrude()` | 85–92% |
| Cylindrical features | Parametric `Circle()` / `Rectangle()` — never a polygon | 85–95% |
| Rotationally symmetric | Half-profile + `revolve()` | 95%+ |
| Smooth convex transitions | `loft()` between boundary profiles | 85–90% |
| Concave (channels, hooks, U-forks) | `extrude()` a representative profile | — |
| Complex organic | Keep the mesh; do not reconstruct | — |

**`loft()` only between convex profiles.** Like OpenSCAD's `hull()`, it bridges
across concavities and fills in every channel, clip and fork. For a concave
profile, extrude a representative section instead.

## Where reconstruction stops

The output of these scripts is a **starting point, not a model**. A polygon with
200 literal coordinates is not parametric — it cannot be resized, and it fails
every convention in `AGENTS.md`. Before it counts as a model in this repo:

1. Replace polygon runs with named parametric geometry (`Circle`, `Rectangle`,
   `RectangleRounded`, `revolve`).
2. Pull measured hardware dimensions into named constants, and check them
   against `fdm-fits-and-clearances` rather than trusting the mesh — the STL
   encodes the original designer's clearances, which may not match our material
   or printer.
3. Add the edge treatments the house rule requires (chamfer horizontal, fillet
   vertical). A reconstructed mesh usually has these baked into the polygon as
   faceted noise; delete them and re-apply them as real operations.
4. Put the part in print pose and re-seat it on `z=0`.
5. Give it a `checks.py` or `check()` that asserts the dimensions that matter.

A reconstruction that skips step 1 is a mesh in a `.py` file.
