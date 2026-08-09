# Fits, clearances and dimensional reality

Every number on this page carries the URL it came from. Where published sources
disagree — and on fits they disagree by up to 4× — both positions are stated, followed by
the value this repo actually uses and why.

All clearances are **diametral** (total gap between the two parts) in millimetres, unless
a row says otherwise.

## Contents

- [The fit ladder](#the-fit-ladder)
  - [The industrial-numbers trap](#the-industrial-numbers-trap)
  - [Naming collisions between sources](#naming-collisions-between-sources)
- [Per-material clearance](#per-material-clearance)
  - [Mapping to `for_material`](#mapping-to-for_material)
  - [Where sources disagree on ABS](#where-sources-disagree-on-abs)
  - [Over-extrusion](#over-extrusion)
- [Dimensional reality](#dimensional-reality)
  - [Achievable tolerance](#achievable-tolerance)
  - [ISO 286 grades](#iso-286-grades)
  - [Hole and shaft compensation](#hole-and-shaft-compensation)
  - [Shrinkage by material](#shrinkage-by-material)
- [Minimum printable features](#minimum-printable-features)
  - [Holes and posts](#holes-and-posts)
  - [Walls](#walls)
  - [Overhang, bridging, elephant's foot](#overhang-bridging-elephants-foot)
- [Scaling rules](#scaling-rules)
- [Sources](#sources)

## The fit ladder

Diametral clearance for desktop FDM. Positive is clearance, negative is interference.

| Fit | Markforged (industrial) | Prusa MK4/XL (UF) | Creative3DP (desktop) | Safe default | `models.lib.fits` |
|---|---|---|---|---|---|
| Press / interference | 0.00 – 0.05 | — | −0.10 | **−0.10** | `PRESS = -0.10` |
| Snug / locating | 0.05 – 0.10 | 0.15 – 0.20 | +0.05 | **+0.10** | `SNUG = 0.10` |
| Close running / sliding | 0.10 – 0.20 | 0.20 – 0.25 | +0.15 | **+0.20 – 0.25** | `SLIDING = 0.22` |
| Free / loose | — | 0.30 – 0.40 | +0.35 | **+0.40** | `FREE = 0.40` |

Sources, column by column:

- **Markforged** — [Composites Design Guide](https://support.markforged.com/hc/en-us/articles/360001308239-Composites-Design-Guide),
  §"Tolerancing and clearances", v1.4 p. 8. Verbatim: press fit `0.00 mm – 0.05 mm`,
  close fit `0.05 mm – 0.10 mm`, free fit `0.10 mm – 0.20 mm`. The guide states the
  dimensions are diametral.
- **Prusa MK4/XL** — [University of Florida, Marston Makerspace](https://makerspace.uflib.ufl.edu/services/3dprocess/recommended-software-for-3d-printing/designing-for-3d-printing-tolerances-on-the-mk4-and-xl/).
  Verbatim: `0.15–0.20 mm` snug / alignment ("locating features"), `0.20–0.25 mm`
  standard sliding ("tabs, rails, enclosures"), `0.30–0.40 mm` loose ("covers and
  adjustable components"). Print-in-place mechanisms want the top of those ranges.
- **Creative3DP** — [Press-Fit Tolerances for 3D Printing](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/).
  Verbatim: press/interference `−0.10 mm`, snug/transition `+0.05 mm`, close running
  `+0.15 mm`, free/loose `+0.35 mm`.

The safe-default column tracks the *desktop* sources, rounding toward the looser of the
two where they differ. `SLIDING = 0.22` sits inside the 0.20–0.25 band; `SNUG = 0.10`
splits Creative3DP's 0.05 and UF's 0.15–0.20 and is deliberately the tightest fit this
repo will design without a test coupon.

### The industrial-numbers trap

**State this loudly, because it is the single biggest cause of a fit that welds solid.**

Markforged's numbers are for a closed-loop industrial machine printing Onyx with a
controlled chamber. On a desktop FDM printer the error budget is *larger than the
clearance itself*:

- holes print ~0.24 mm undersize, shafts ~0.10 mm oversize (below);
- practical positional tolerance is ±0.2 mm (below);
- over-extrusion alone eats 0.1–0.2 mm.

Add those up and a Markforged "free fit" of 0.10–0.20 mm is consumed before the parts
touch. Ported to desktop FDM it is a press fit at best and unassemblable at worst.
Industrial figures are a lower bound on what is *physically possible*, never a value to
type into a model.

### Naming collisions between sources

The same words mean different bands in different guides. Two to watch:

- Markforged calls `0.10–0.20 mm` a **free fit** ("slide and/or rotate easily"). Every
  desktop source calls that band a **close running** fit and reserves *free/loose* for
  0.30–0.40. This page uses the desktop meaning.
- Creative3DP's hole calculator calls a hole whose **axis is perpendicular to the bed**
  (a bore drilled down into the top face) a *horizontal hole*, and a hole whose axis lies
  *in* the bed plane a *vertical hole* — the opposite of ordinary usage
  ([Hole Tolerance Calculator](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)).
  To avoid the ambiguity entirely, this page says **axis-Z** (bored down, prints round,
  undersize) and **axis-XY** (bridged, sags to a D).

## Per-material clearance

Working clearances by material and by what the joint has to do:

| Material | Sliding | Rotating | Snap-fit |
|---|---|---|---|
| PLA | 0.30 | 0.50 | 0.20 |
| **PETG (repo baseline)** | **0.40** | **0.60** | **0.25** |
| ABS / ASA, open frame | 0.25 | 0.40 | 0.15 |
| ASA, enclosed chamber | 0.20 | 0.35 | 0.15 |
| TPU 95A | 0.50 | 0.80 | 0.30 |

**Read the column headings carefully.** *Sliding* here means a hand-operated slide with
visible clearance — closer to `fits.FREE` than to `fits.SLIDING`. The fit ladder's
`SLIDING`/close-running class is a *located* running fit with no perceptible play, which
is a tighter thing. Do not mix a row from this table with a class from the ladder without
deciding which behaviour you actually want.

Corroboration for the shape of this table:

- PETG needs more room than PLA: PETG's "slightly tacky surface eats ~0.05 mm of any
  running clearance"
  ([Creative3DP](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/)).
  That PETG also runs slightly oversize compared to PLA is a house observation, not a
  cited figure — no source fetched during authoring states it in those terms.
- TPU is the loosest row: TPU "requires double the interference" for press fits plus
  "0.5–0.8 mm total clearance for moving fits"
  ([Creative3DP](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/)) —
  which is exactly the 0.50 / 0.80 pair above.
- Rotating ≈ sliding + 0.2: an independent per-material table gives sliding 0.15–0.25
  (PLA) / 0.2–0.3 (PETG) against free rotation 0.4–0.6 (PLA) / 0.5–0.7 (PETG)
  ([3DPrintCalcs](https://3dprintcalcs.uk/reference/common-tolerances/) — **note: that
  page states its clearances are per side, so the total diametral gap is double the
  quoted figures; the ratio between the sliding and rotating columns, which is what this
  bullet borrows, is unaffected by the 2× scale**).
- An enclosed chamber tightens the ABS/ASA row because it removes most of the differential
  cooling that makes those materials arrive undersize and warped
  ([Creative3DP shrinkage figures](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)).

**Unverified as an exact table.** No single published source states these fifteen cells
verbatim; they are this repo's synthesis of the sources above, and the deltas between
rows are what `models/lib/fits.py::_MATERIAL_OFFSET` implements. Treat the *relative*
ordering as well supported and any individual cell as ±0.05.

### Mapping to `for_material`

`for_material` applies the delta of the **sliding** column relative to PETG:

| Material | Sliding column | Δ from PETG | `_MATERIAL_OFFSET` key |
|---|---|---|---|
| PLA | 0.30 | −0.10 | `"pla": -0.10` |
| PETG | 0.40 | 0.00 | `"petg": 0.0` |
| ABS / ASA, open frame | 0.25 | −0.15 | `"abs": -0.15`, `"asa": -0.15` |
| TPU 95A | 0.50 | +0.10 | `"tpu": 0.10` |

**Gap to know about:** the table has a separate *ASA, enclosed chamber* row at 0.20, but
`fits.py` has only one `"asa"` key at `−0.15`. Printing ASA in a heated chamber (the
K2 Plus can do this) therefore wants a further **−0.05 mm by hand**, with a comment saying
so. Do not silently reuse the open-frame constant.

### Where sources disagree on ABS

- **This table** puts ABS/ASA *tighter* than PETG (−0.15), on the reasoning that ABS
  shrinks most on cooling and so arrives undersize already — the shrink has spent part of
  the clearance for you.
- **3DPrintCalcs** puts ABS at the *same* clearance as PETG and both looser than PLA
  (press 0.05–0.15, snug 0.1–0.2, sliding 0.2–0.3, loose 0.3–0.5 for both)
  ([common tolerances](https://3dprintcalcs.uk/reference/common-tolerances/)). That page
  states its figures are **per side** (total diametral gap = 2× the listed value); the
  ruling below only needs the *relationship* "ABS ≈ PETG", which holds at either scale.

Both can be right, because they are measuring different things: whether the slicer's
shrinkage compensation is switched on. With a compensated ABS profile the part comes out
on-size and behaves like PETG; without one it comes out small and needs less designed
clearance.

**Safe default: use the `−0.15` offset only on an uncompensated profile.** If the slicer
profile already applies shrinkage compensation, treat ABS/ASA as PETG (offset `0.0`) and
say so in the comment. When in doubt, the looser choice fails gracefully (a rattle) and
the tighter one fails hard (an unassemblable part).

### Over-extrusion

Over-extrusion narrows every hole from the inside: "extrusion overshoot on inside curves"
causes "a tiny pile-up of material on the inside surface, narrowing the hole by
0.1–0.2 mm", and the recommended fix when press fits feel impossible is to "reduce [flow
rate] by 2–3%"
([Creative3DP](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)).

That is the whole of a snug fit and half of a sliding one. **A flow multiplier above
~105% eats 0.1–0.15 mm of every clearance in the model** — the 105% threshold is this
repo's working rule of thumb, not a sourced figure, but the 0.1–0.2 mm magnitude is.

Practical consequence: calibrate flow before blaming the CAD, and never tune a fit by
changing the model while the flow multiplier is unknown.

## Dimensional reality

### Achievable tolerance

| Quantity | Value | Source |
|---|---|---|
| Practical FDM tolerance | **±0.2 mm** (or ±0.2% on larger parts) | [Roc 3D Printing](https://roc3dprinting.com/blog/tolerances) |
| XY vs Z, independent measurement | horizontal ±0.1–0.3 mm, vertical ±0.05–0.2 mm | [3DPrintCalcs](https://3dprintcalcs.uk/reference/common-tolerances/) |
| FDM vs SLA/SLS, for context | FDM ±0.2 mm/±0.2% against SLA ±0.1 mm/±0.1% (both under ~100 mm) | [Roc 3D Printing](https://roc3dprinting.com/blog/tolerances) |
| FDM vs SLA/SLS, for context (assembly clearance) | FDM 0.5 mm against 0.2 mm for SLA/SLS | [Formlabs](https://formlabs.com/blog/how-to-3d-print-interlocking-joints/) |

**Correction:** an earlier draft of this row set carried a "calibrated machine, small
parts, XY: ±0.1 mm" line attributed to Roc 3D Printing. Re-checked against the live page:
every ±0.1 mm figure there is stated for **SLA**, not FDM — the page never claims a
calibrated FDM machine hits ±0.1 mm, on small parts or otherwise. No other source fetched
during authoring (Hydra, Protolabs, Markforged) gives a tighter-than-±0.2 mm figure for
FDM either. The row is removed rather than re-sourced. **±0.2 mm is therefore the only
FDM achievability figure this page asserts** — there is no sourced "tight/calibrated"
tier below it. If a specific printer is measured to do better, record that measurement in
`references/printers.md` against that printer, not here.

Formlabs' 0.5 mm is a service-bureau guarantee across arbitrary geometry, not a figure
specific to a calibrated desktop machine; **±0.2 mm is the one FDM figure this page
stands behind and the one to design against.** There is no sourced tighter tier for a
"calibrated" or "small parts" case — do not design to ±0.1 mm on FDM without a printed
and measured test coupon from the specific machine, and if one exists, record it in
`references/printers.md` rather than generalising it here.

### ISO 286 grades

FDM lands around **IT11–IT14** on the ISO 286 tolerance-grade scale — coarse by machining
standards, where a reamed hole is IT7. The MDPI study *Accuracy of FDM PLA Polymer 3D
Printing Technology Based on Tolerance Fields* investigates grades IT9 through IT14 for
FDM PLA and presents a CAD + calibration procedure for hitting the tighter end
([Processes 11(10):2810](https://www.mdpi.com/2227-9717/11/10/2810)).

**Partly unverified**: the paper's full text was not reachable during authoring (HTTP
403), so the IT9–IT14 span is taken from its abstract. The practical reading — *do not
promise a fit that needs better than IT11 without calibrating and measuring* — is what
matters here and is consistent with the ±0.2 mm figure above.

### Hole and shaft compensation

| Feature | Behaviour | Compensation | Source |
|---|---|---|---|
| Axis-Z bore (drilled down) | prints undersize; **−0.24 mm** measured on a 5 mm hole, PLA, 0.4 mm nozzle | add the fit class on top of nominal | [Creative3DP](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/) |
| External diameter / shaft | prints oversize, **+0.10 mm** (roughly half the hole error) | subtract if the shaft is also printed | [Creative3DP](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/) |
| Axis-XY bore (bridged) | unsupported crown sags, hole goes oval / D-shaped | **+0.1–0.2 mm**, or reorient so the axis is along Z | [Creative3DP](https://tools.creative3dp.com/tools/hole-tolerance-calculator/) |
| Critical axis-Z bore | any compensation is a guess at this precision | print undersize and drill to size | [Protolabs Network](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/) |

A corroborating measurement: a 5.0 mm hole typically yields 4.7–4.9 mm and a 5.0 mm shaft
5.1–5.2 mm ([Roc 3D Printing](https://roc3dprinting.com/blog/tolerances)) — the same
0.1–0.3 mm undersize and ~0.1–0.2 mm oversize.

### Shrinkage by material

Linear shrinkage on cooling, as a percentage of the dimension:

| Material | This repo | Alternative published figure | Note |
|---|---|---|---|
| PLA | **0.3%** | 0.2–0.5% | "almost negligible for hardware fits" |
| PLA-CF | **0.2%** | 0.2–0.4% (CF grades generally) | fibre restrains the polymer |
| PETG | **0.4%** | 0.4% | agrees |
| ABS / ASA | **0.7%** | ABS 0.8%, ASA 0.5% | "noticeable on parts >20 mm" |
| PC | **0.7%** | 0.6% | see conflict note |
| PA (nylon) | **1.5%** | PA12 1.4%, PA6 1.5% | "dramatic, needs aggressive compensation" |
| TPU 95A | — | 0.8% | not used for fits in this repo |

- This-repo column and all quoted phrases:
  [Creative3DP Hole Tolerance Calculator](https://tools.creative3dp.com/tools/hole-tolerance-calculator/),
  which gives PLA 0.3%, PETG 0.4%, ABS/ASA 0.7%, PA 1.5%, and PLA-CF/PA-CF 0.2–0.4%.
- Alternative column:
  [GrandpaCAD Material Shrinkage Calculator](https://grandpacad.com/en/tools/material-shrinkage-calculator),
  which splits ABS 0.8% from ASA 0.5%, gives PC 0.6%, PA12 1.4% / PA6 1.5%, TPU 95A 0.8%.

**Conflicts and rulings:**

- **ABS vs ASA.** Creative3DP lumps them at 0.7%; GrandpaCAD separates them (ABS 0.8%,
  ASA 0.5%). *Safe default: 0.7% for both.* It is between the two for ABS and
  conservative for ASA, and the difference (0.2%) is 0.2 mm over 100 mm — below the
  ±0.2 mm tolerance floor for anything hand-sized, so the split only matters on large
  parts. On a part over ~150 mm, use the separated figures.
- **PC.** 0.7% vs 0.6%. *Safe default: 0.7%*, the pessimistic one — PC warps badly and
  under-compensating a warped part is the worse failure.
- **PLA-CF.** 0.2% is the bottom of the quoted 0.2–0.4% CF range. *Safe default: 0.2%* for
  fits (it under-compensates, leaving the part slightly large, which loosens a clearance
  rather than tightening it), but use 0.3% if scaling a whole part to size.

Shrinkage figures vary with print temperature, cooling rate, enclosure, geometry and
filament brand — both sources say so explicitly. They are for scaling a *large* dimension,
not for setting a fit: at 5 mm, PLA shrinks 0.015 mm ("invisible") while nylon shrinks
0.075 mm ("meaningful")
([Creative3DP](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)).

## Minimum printable features

The extrusion-based minimums below come from Markforged's
[Composites Design Guide](https://support.markforged.com/hc/en-us/articles/360001308239-Composites-Design-Guide)
(v1.4, Quick Reference Sheet). Unlike its *fit* table, these are limits set by bead
geometry and layer stacking, which transfer to any extrusion process — a 0.4 mm desktop
nozzle is in the same regime.

### Holes and posts

| Feature | Value | Note |
|---|---|---|
| Minimum hole Ø, axis-Z surface | **1.0 mm** | Markforged: `Z: 1.0 mm (0.039")` |
| Minimum hole Ø, axis-XY surface | **1.5 mm** | Markforged: `XY: 1.5 mm (0.059")` — bridged, less precise |
| Minimum post Ø, XY | **1.6 mm** | Markforged: `XY: 1.6 mm (0.063")` |
| Minimum post Ø, Z | **2.0 mm** | Markforged: `Z: 2.0 mm (0.079")` |
| Post height | **H < 5D** | "Avoid printing posts with heights (H) more than five times their diameter (D)" — taller posts shear along layer lines |
| Minimum part dimension | X 1.6 / Y 1.6 / Z 0.8 mm | set by the minimum roof, floor and shell counts |

**Conflict on minimum hole diameter.** Hydra Research's FFF design rules give
`> ø2 mm` as the minimum hole, twice Markforged's figure
([Hydra Research](https://www.hydraresearch3d.com/design-rules)).
*Safe default: 2 mm for any hole that must be round and to size; 1.0–1.5 mm only for a
hole that merely has to exist (a vent, a pilot, a wire pass).* Markforged's limit is what
a good machine can resolve; Hydra's is what a desktop machine can be relied on to resolve.

Markforged also notes posts should have **filleted interfacing edges** to reduce stress
concentration — the same rule as `AGENTS.md`'s "fillet internal corners for strength".

### Walls

| Case | Value | Source |
|---|---|---|
| Absolute minimum | **0.8 mm** (2 perimeters at 0.4 mm) | house rule; matches Markforged's 0.8 mm minimum Z dimension |
| Load-bearing | **1.2 mm** (3 perimeters) | house rule |
| Functional / structural | **1.5 mm** | house rule |
| Published minimum | **> 0.9 mm** ("2 times extrusion line width") | [Hydra Research](https://www.hydraresearch3d.com/design-rules) |

Hydra's 0.9 mm assumes a 0.45 mm extrusion width; at a nominal 0.4 mm width the same rule
gives 0.8 mm. The two agree — they differ only in the assumed line width. **Slice at your
actual extrusion width and take 2× that as the floor.**

A wall thinner than 2 perimeters has no infill between its skins and behaves like a single
bead. `AGENTS.md` applies the same 0.8 mm floor to the lip of a rabbet joint and to the
web between neighbouring bores.

### Overhang, bridging, elephant's foot

| Rule | Values published | Safe default |
|---|---|---|
| Maximum unsupported overhang from vertical | Protolabs Network: **45°** · Hydra Research: `< 50°` (up to 70° on modern machines) · Markforged: `θ: 40°` to horizontal, with supports generated below 45° | **45°** |
| Maximum unsupported bridge | Hydra Research: `< 10 mm` · Protolabs Network: sag "always present unless the bridge is less than 5 mm" | **~10 mm** to print at all, **5 mm** for a surface you care about |
| Elephant's-foot relief | Hydra Research: `~0.3 mm` base chamfer (initial layer height + layer height) · Protolabs Network: "a 45° chamfer or radius on all edges touching the build plate" | **0.2–0.5 mm 45° chamfer**, plus **−0.1 to −0.2 mm** slicer XY compensation on the first layer |

The 45° overhang figure is the one to design to: it is what Protolabs Network states
plainly ([design for FDM](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)),
it is where Markforged's slicer starts generating supports, and it is inside Hydra's 50°.
The 40° and 70° figures are the edges of the envelope, not targets.

**Spiral vase mode is the documented exception, and 45° is too tight for it.**
That figure is for a perimeter that has to bridge from the wall below it. A
spiralising single perimeter never bridges: it lays one continuous bead whose
support is the bead directly beneath it, so the limit is set by how far the wall
steps sideways in one layer against how wide that bead is —
`tan(angle) × layer_height` against `extrusion_width`. Requiring half the bead to
land on its predecessor gives

```
max_overhang = atan(extrusion_width / 2 / layer_height)
```

which is **56.3°** at the usual vase-mode pair of 0.6 mm width and 0.2 mm layers,
and moves with either setting. Design a vase-mode part to 45° and you are leaving
a third of the envelope unused.

**This one is a house derivation, not a sourced figure** — no vendor above
addresses spiralised single-wall printing. What corroborates it is a measurement:
JH's "Waves" Designer Lamp (Printables 1261597), a widely printed vase-mode
design, leans **50.8°** at its steepest — over the 45° rule, under this bound.
`models/spiral_vase_lampshade/config.py` derives `MAX_OVERHANG` from the two
slicer settings rather than hard-coding either number.

**Elephant's-foot values are partly unverified.** The 0.3 mm chamfer and the 45°
chamfer/radius rule are sourced above; the specific `−0.1 to −0.2 mm` slicer elephant-foot
compensation is a house figure and the 0.2–0.5 mm chamfer band is `AGENTS.md`'s
(which specifies 0.5–1.0 mm for the house 45° chamfer — the wider 0.5–1.0 band is a
*styling* choice, 0.2–0.5 mm is the minimum that does the foot-relief job).

Both mechanisms are wanted: the chamfer gives the squished first layers somewhere to bulge
into, and the slicer compensation shrinks the first layer's outline. Doing only the
compensation leaves a raw square bottom edge, which `AGENTS.md` forbids anyway.

## Scaling rules

**Large parts need more clearance.** Add **+0.05 mm of clearance per 100 mm of part size**
to absorb thermal contraction across the span. *Unverified as a published figure* — it is
this repo's rule of thumb. Its justification is the tolerance spec: FDM holds "±0.2 mm or
±0.2%" ([Roc 3D Printing](https://roc3dprinting.com/blog/tolerances)), so the *tolerance*
band alone grows by 0.2 mm per 100 mm; +0.05 mm of extra designed clearance covers the
fraction of that which is systematic contraction rather than random error. On a 200 mm
part in ABS the effect is much larger — "0.5–1.0 mm shorter than designed" (same source) —
and belongs in slicer shrinkage compensation, not in the fit.

**Small features tolerate tighter fits.** Formlabs splits its assembly clearance at a
feature area of 20 mm²: "features less than 20 mm²: 0.2 mm", "features greater than
20 mm²: 0.4 mm"
([Formlabs](https://formlabs.com/blog/how-to-3d-print-interlocking-joints/)). Those are
SLA/SLS figures, so on FDM read them as a *ratio* rather than absolutes — a small feature
takes roughly **half** the clearance of a large one, because there is less length over
which error can accumulate.

Applied to this repo's ladder: a 6 mm locating boss can run at `fits.SNUG`; a 60 mm lid
skirt of the same nominal fit class should be at `fits.SLIDING` or looser.

**Both rules point the same way**: clearance is not a property of the joint alone, it is a
property of the joint *and the distance over which the two parts have to agree*.

## Sources

- Markforged — [Composites Design Guide](https://support.markforged.com/hc/en-us/articles/360001308239-Composites-Design-Guide)
  ([PDF, v1.4](https://static.markforged.com/downloads/CompositesDesignGuide.pdf))
- University of Florida, Marston Makerspace — [Designing for 3D Printing Tolerances on the MK4 and XL](https://makerspace.uflib.ufl.edu/services/3dprocess/recommended-software-for-3d-printing/designing-for-3d-printing-tolerances-on-the-mk4-and-xl/)
- Creative3DP — [Press-Fit Tolerances for 3D Printing](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/)
  and [Hole Tolerance Calculator](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)
- Protolabs Network (Hubs) — [How to design parts for FDM 3D printing](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
- Hydra Research — [FFF design rules](https://www.hydraresearch3d.com/design-rules)
- Xometry — [FDM design tips](https://xometry.pro/en/articles/fdm-design-tips/)
  (cited by `AGENTS.md`; returned HTTP 403 during authoring, so nothing on this page is
  sourced solely to it)
- Formlabs — [How to 3D print interlocking joints](https://formlabs.com/blog/how-to-3d-print-interlocking-joints/)
- MDPI *Processes* 11(10):2810 — [Accuracy of FDM PLA Polymer 3D Printing Technology Based on Tolerance Fields](https://www.mdpi.com/2227-9717/11/10/2810)
- 3DPrintCalcs — [Common tolerances reference](https://3dprintcalcs.uk/reference/common-tolerances/)
- GrandpaCAD — [Material Shrinkage Calculator](https://grandpacad.com/en/tools/material-shrinkage-calculator)
- Roc 3D Printing — [3D printing tolerances: what ±0.2 mm really means](https://roc3dprinting.com/blog/tolerances)
