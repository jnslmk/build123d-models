---
name: photo-reverse-engineering
description: >-
  Turns photographs of a physical object into a parametric build123d model in
  this repo. Establishes scale from a reference in frame, corrects camera
  perspective with a four-point homography, records every dimension in an
  evidence ledger that separates measured numbers from assumed ones, and grades
  the model's silhouette against the photo from named views. Adapts the
  "gauntlet loop" builder/critic fan-out to CAD by replacing its aesthetic bar
  with a numeric one, and ships an eval harness whose required negatives prove
  what a visual critic cannot see. Use when a part must be modelled from photos,
  a snapshot, a screenshot or a product listing rather than from calipers or a
  mesh; when an object needs measuring from an image; when a photo's scale,
  perspective or lens distortion must be corrected before a dimension is read
  off it; when checking how closely a model matches a reference image; or when
  running a builder-and-critic loop over a CAD model. Keywords - photo,
  photograph, image, picture, snapshot, reverse engineer from photo, measure
  from photo, scale reference, homography, perspective correction, rectify,
  silhouette, IoU, reference image, gauntlet loop, critic, subagent loop,
  evidence ledger, product listing, screenshot. Load BEFORE reading a dimension
  off an image or starting a builder/critic loop on a model -- the scale and
  provenance rules decide whether any number from the photo may be used at all,
  and the silhouette gate is provably blind to internal geometry. TRIGGER: about
  to measure an object in a photo, set up a critic loop that judges a model
  visually, correct a photo's perspective, or write a model dimension whose only
  source is an image.
---

# Photo reverse engineering

Rebuilding a physical object as parametric build123d source when the input is
photographs. A photo carries no scale, no depth and no interior, so most of this
skill is about knowing which numbers you are entitled to take from it -- and
being explicit about the rest.

## Setup

Two packages, in a dependency group that is deliberately **not** installed by
default:

```bash
uv sync --group photo
```

Both are already in the tree as transitive dependencies of the OCP stack, so
this costs an install nothing; the group exists so the scripts import something
this project asked for. `.github/workflows/build.yml` runs plain `uv sync
--frozen`, which skips it. Nothing here can break a model build or a deploy.

## The one rule that everything else follows from

**A photo can tell you a shape. It cannot tell you a fit.**

`scale_error_2pct` in this skill's eval is the whole argument in one number: a
part rasterised 2% too large scores **96.12% IoU** against the truth, sailing
past a 95% gate. On a 50 mm part that is 1 mm of error — enough to turn a press
fit into a rattle, while every visual check reports success.

So the ledger splits into two kinds of number and they are never mixed:

| | Source | May set |
|---|---|---|
| **Shape** | the photo | proportion, feature placement, profile, count |
| **Fit** | calipers, a datasheet, a standard | anything that mates with hardware |

If a mating dimension has no source but the photo, it is an **assumption**, it
gets written down as one, and the part gets a printed fit test before it gets a
final print. `photo_measure.py` enforces the split mechanically: it prints each
measurement's error bar next to the finest fit class in `models/lib/fits.py`
that error bar could legitimately set. For a typical phone photo the answer is
`none`.

## The workflow

### 1. Get photos that can be measured

Before any tooling. In order of how much error each one removes:

1. **Put a scale reference in frame, coplanar with the feature you are
   measuring.** Calipers open to a known span, a steel rule, a printed sheet of
   known size. A coin works and is worse — you inherit its tolerance.
2. **Shoot square-on**, one photo per principal face, camera centred on the
   face and as far back as focus allows. Distance is what suppresses
   perspective; zoom in rather than stepping closer.
3. **Plain, contrasting background.** This is what makes automatic silhouette
   extraction possible at all in step 4.
4. **One oblique photo as well**, for reading features the square-on views
   flatten away.

A photo with no scale reference is not evidence, and no amount of processing
turns it into evidence. Ask for a re-shoot or a single caliper reading before
spending anything else.

### 2. Rectify and measure

```bash
uv run --group photo python .claude/skills/photo-reverse-engineering/scripts/photo_measure.py \
    spec.json --out analysis/
```

`--example` prints a spec to start from. Given the four image corners of a
planar rectangle of known size, it solves the homography, warps the photo
square-on, fixes px_per_mm exactly, and turns point pairs into millimetres with
error bars. Output is `analysis/ledger.json` plus `rectified.png`.

The four corners are the one input worth being fussy about: their error
propagates into *every* measurement, unlike endpoint error, which is per
measurement.

The `error_mm` for a known 40 mm segment recovered through a synthetic oblique
shot is **0.000 mm** (`rectify_roundtrip` in the eval), so the maths adds
nothing to your error budget. All of the error is in where you put the corners.

### 3. Build the model, ledger first

Write `config.py` before geometry, one constant per ledger entry, each carrying
its provenance in a comment — `measured`, `datasheet`, or `ASSUMED`. A model
built from photos should be greppable for `ASSUMED`, and every hit should be
either resolved or deliberately accepted before it prints.

Everything in `AGENTS.md` still applies: builder mode, print pose on `z=0`,
chamfer horizontal edges and fillet vertical ones, `checks.py` with real
assertions. A model from photos is not a special category of model.

### 4. Grade the silhouette

```bash
uv run --group photo python .claude/skills/photo-reverse-engineering/scripts/silhouette_match.py \
    my_model --view front --reference refs/front.png --px-per-mm 8
```

Renders the model's outline from a named view (the same view names as `uv run
render`), aligns it to the reference by translation only, and reports IoU, the
width and height ratios, and a residual image — model-only in red,
reference-only in blue. Exits non-zero below `--pass-iou` (default 0.95), so it
can gate a loop.

**Read the ratios first, then the IoU.** The ratios are what catch a scale
error; the IoU is what catches a wrong shape. The tool prints an explicit
`model is 3.1% too small in width` line whenever a ratio drifts past 1%, because
that is the failure the IoU will not show you.

Automatic silhouette extraction is a global threshold, which is correct only
against a plain contrasting background. Anywhere else, cut the mask by hand and
pass that: a bad segmentation produces a confident wrong number, which is worse
than no number.

## The gauntlet loop, and what it costs to copy it verbatim

The builder/critic fan-out this skill's step 4 feeds comes from Matt Shumer's
"gauntlet loop", by way of [this
walkthrough](https://www.youtube.com/watch?v=BNjzXcEXmg4). The prompt is three
parts, and the structure is the useful bit:

1. **Task** — what to build.
2. **Build method** — break it into the smallest pieces, fan out one subagent
   per piece, and give each one a *separate* critic subagent that checks its
   work.
3. **The bar** — the standard that decides when to stop.

Parts 1 and 2 port to CAD unchanged, and they port well: `checks.py`, per-view
silhouette matching and per-part geometry assertions are all natural per-piece
critic jobs, and a model package's parts are already the decomposition.

**Part 3 does not port, and copying it is the failure mode.** The original bar
is "do not stop until each subagent is utterly wowed compared to Call of Duty".
An aesthetic bar judged by the thing being graded is unfalsifiable, and in this
repo it is also unnecessary — there are real gates already:

| Aesthetic bar | Numeric bar to use instead |
|---|---|
| "looks like the photo" | `silhouette_match.py` exit code, **and** width/height ratios within 1% |
| "the wall looks thick enough" | `checks.py`, `is_solid_at` point sampling |
| "the edges look finished" | `sharp_convex_edges()` with a named `allow` list |
| "it should fit" | a printed fit test — no software gate substitutes |

Two more things the source gets right and that survive translation:

- **The critic must be blind to the builder's reasoning.** It sees the artifact
  and the reference, not the argument for why the artifact is fine. A critic
  handed the builder's justification ratifies it.
- **Do not start with the loop.** The walkthrough's own strongest point: it
  polished a landing page to a high finish that was off-brief, because the loop
  optimises toward whatever it was pointed at. In CAD the equivalent is
  beautifully refining a part that is 2% out of scale — which, per the table
  below, every visual gate will pass. Land the ledger and a correct-scale
  skeleton first; run the loop on top of that.

And one that does not survive at all: the loop is blind to everything a
silhouette cannot see. `hidden_cavity` in the eval scores **100.00% IoU from
three orthogonal views** on two parts differing by **25% in volume**. No number
of critic rounds finds that. Internal geometry is verified in code or not at
all.

## What the tools were measured to do

Real output from `eval/run_eval.py` on this machine, 2026-08-08:

| scenario | measured | meaning |
|---|---|---|
| `self_match` | IoU **100.00%**, ratio 1.0000 | the rasteriser and aligner are self-consistent |
| `scale_error_2pct` | IoU **96.12%**, width ratio 0.9794 | a 2% scale error **passes** a 95% IoU gate; the ratio catches it |
| `hidden_cavity` | IoU **100.00%**, volume ratio 0.7500 | 25% of the material gone, no silhouette changed |
| `rectify_roundtrip` | error **0.000 mm**, fill 99.79% | the homography costs nothing; your corner clicks cost everything |

`scale_error_2pct`'s measured 0.96124 matches the closed form for a uniformly
scaled convex outline, 1/1.02² = 0.96117, to four decimals — the rasteriser is
doing real geometry, not approximating it.

The last two rows are **required negatives**: they must keep scoring *well* for
the warnings above to stay true. An eval that only checked accuracy would never
look at them.

## A reconstruction is not yet a model

Same endgame as `stl-reverse-engineering`, and the same rule: numbers taken from
a source you did not design carry that designer's tolerances, their printer's
quirks and their material's shrinkage. A photo adds its own camera to that list.
Re-derive every fit from `fdm-fits-and-clearances` rather than inheriting it,
put the part in print pose on `z=0`, give it real checks, and only then does it
belong in `models/`.

## Related

- `stl-reverse-engineering` — the same endgame from a mesh instead. If both a
  photo and a mesh exist, start there: a mesh has real dimensions.
- `fdm-fits-and-clearances` — where every mating dimension must come from.
- `build123d-geometry-ops` — `is_solid_at` point sampling, which is how you
  check the things a silhouette cannot see.
