# Joint clearance reference

One section per joint type: the number to start from, what it fails like, and where
the number comes from. Every figure is diametral or per-face as marked — mixing the
two is the single commonest sizing error, so read the column heading.

Material-specific adjustment (PLA vs PETG vs ABS), hole-shrink compensation and the
reasoning behind FDM's dimensional behaviour are **not** repeated here. They live in
the `fdm-fits-and-clearances` skill.

## Contents

- [Quick table](#quick-table)
- [Dovetail](#dovetail)
- [T-slot and tongue-and-groove](#t-slot-and-tongue-and-groove)
- [Pin-and-socket and dowels](#pin-and-socket-and-dowels)
- [Crush ribs](#crush-ribs)
- [Print-in-place hinge (knuckle)](#print-in-place-hinge-knuckle)
- [Mortise-and-tenon](#mortise-and-tenon)
- [Cross-dowel / barrel nut](#cross-dowel--barrel-nut)
- [Magnet pocket](#magnet-pocket)
- [Bearing pocket](#bearing-pocket)
- [Scaling with part size](#scaling-with-part-size)
- [Minimum printable features](#minimum-printable-features)
- [Sources](#sources)

## Quick table

| Joint | Clearance | Basis | Source |
| --- | --- | --- | --- |
| Dovetail | 0.2–0.3 mm per face snug / 0.4–0.5 mm free (0.25 author's default) | per face | [Siraya][sy] (general FDM gap); rest is author's estimate |
| T-slot / tongue-and-groove | 0.2–0.5 mm per side; 0.1–0.15 tight | per side | [Siraya][sy] (general gap); tight figure is author's estimate |
| Pin, snug | 0.1–0.2 mm | diametral | [Creative3DP][c3], [Hydra][hr] |
| Pin, free rotation | 0.3–0.4 mm | diametral | [Creative3DP][c3], [UAVMODEL][uv] |
| Pin, press fit | −0.1 to −0.2 mm | diametral | [Creative3DP][c3] |
| Crush ribs | 3–4 ribs, 0.2 mm proud, ~2° slope | radial | rib count [Creative3DP][c3]; 0.2 mm + slope [AON3D][an] |
| Hinge, around pin | 0.3 mm | radial | author's estimate (see note) |
| Hinge, knuckle faces | 0.2 mm | per face | author's estimate (see note) |
| Mortise-and-tenon | 0.2–0.3 mm (desktop FDM) | per wall | author's estimate; [Formlabs][fl] confirms FDM tenon stepping |
| Cross-dowel bore | nut OD + 0.2–0.3 mm | diametral | author's estimate, no source discusses barrel nuts directly |
| Magnet pocket | Ø +0.2–0.3 mm, depth = thickness | diametral | author's estimate, generalised from [Creative3DP][c3]'s press-fit ladder |
| Bearing pocket | −0.05…0.10 mm per side | per side | [Creative3DP][c3] |

## Dovetail

A dovetail is a sliding joint, so it inherits Siraya's general FDM gap guidance:
**0.2–0.3 mm per face for a snug hand-assembled fit, 0.4–0.5 mm for a free
sliding one** ([Siraya][sy] states this as general FDM design guidance, not
specifically about dovetails). **This skill's default is 0.25 mm per face** —
the midpoint of that band. That default, and every other specific number in this
section except the two explicitly marked otherwise, is the **author's estimate**:
searches of Formlabs, Siraya, Markforged, Creative3DP, AON3D and Hydra Research
turned up no page that publishes a dovetail-specific clearance or flank angle, so
none is cited as if it did.

- **Flank taper: 10–15°** (author's estimate). A shallower angle stops resisting
  pull-out; a steeper one wastes cross-section for no extra grip. No source
  found for this specific range — treat it as a reasonable starting point to
  verify on a printed coupon, not a verified figure.
- **A single dovetail should stay under roughly 50–60 mm wide** (author's
  estimate, following from the size-scaling rule below: thermal contraction
  along the slide axis grows with width while a fixed per-face clearance does
  not, so a wide dovetail eventually binds partway in). Split into two shorter
  dovetails rather than widening one.
- **Sub-6 mm dovetails may need hammering** even at nominal clearance (author's
  estimate): the absolute error is unchanged but it is now a large fraction of
  the feature, and the tail is too stiff to relieve itself. Below that size, use
  a pin instead.
- Optionally add a **1–2° taper along the length** so the joint slides freely for
  most of its travel and only tightens at the end — this figure **is** stated by
  [Siraya][sy]. This is rule 3 from `SKILL.md` — the taper makes the joint
  tolerant of the exact clearance.
- Lead-in at the entry mouth is mandatory; a dovetail with a square entry corner
  is the classic split-on-first-assembly failure.

## T-slot and tongue-and-groove

**0.2–0.5 mm per side, material-dependent** — the same general FDM gap guidance
as the dovetail above (0.2–0.3 mm snug, 0.4–0.5 mm free-sliding, [Siraya][sy]).
For a deliberately tight, rarely-moved fit, **0.1–0.15 mm per side** is the
author's estimate, interpolated below [Creative3DP][c3]'s "close running"
(+0.15 mm) rung — no source states this range for a T-slot specifically.

- **Print the slide axis in XY.** A rail whose length runs up Z is a stack of
  disks joined only by layer adhesion, and side load on the tongue peels it. This
  is the dominant failure mode and no clearance fixes it.
- The groove is the part that shrinks; the tongue is the part that is easy to
  measure. Size the clearance onto the groove.
- Long slides accumulate the size penalty — see
  [Scaling with part size](#scaling-with-part-size).
- Chamfer the tongue's leading end and the groove mouth, both.

## Pin-and-socket and dowels

Diametral, on the *hole*:

| Intent | Clearance | Note |
| --- | --- | --- |
| Snug locating fit | +0.1 to +0.2 mm | assembles by hand, no play |
| Free rotation | +0.3 to +0.4 mm | pivot, not a bearing |
| Press fit | −0.1 to −0.2 mm | permanent; prefer crush ribs instead |

Source: [Creative3DP][c3]'s FDM fit ladder (−0.10 press, +0.05 snug, +0.15 close
running, +0.35 free), widened to the ranges above to cover uncalibrated printers.

- **Print holes with the axis vertical.** [Protolabs Network][pl] confirms FDM
  often prints undersized vertical-axis holes (the nozzle drags the perimeter
  inward), which at least stays round; a horizontal hole needs internal bridging
  or support to print at all, and holding it round is harder still (author's
  extension of that point — the source does not itself compare hole shape
  between the two orientations).
- **45° chamfer or 0.5 mm radius lead-in on both the pin and the hole.** Not one
  or the other — both, so neither part has to be the one that is on-axis.
- **Pins under 5 mm Ø are unreliable** and should carry a fillet at the base
  regardless; if the pin is structural, model a hole and use an off-the-shelf
  metal dowel instead ([Protolabs Network][pl]).
- **Posts: keep height < 5× diameter.** Taller and the post shears along a layer
  line at the base, which is where the bending moment is highest and the bond is
  the only thing resisting it.
- A dowel through *two* printed holes wants the free-rotation number in one of
  them and the press number in the other, not the same fit in both — otherwise
  the joint is over-constrained and one hole splits.

## Crush ribs

**3–4 ribs standing ~0.2 mm proud of the bore wall, with roughly a 2° slope up
the rib**, giving a transition or press fit without a plain interference fit.

- **This is the preferred way to press-fit anything in FDM.** The ribs absorb
  dimensional error: only the rib tips contact, so bore variation moves the crush
  depth rather than moving the joint between "rattles" and "cracked". It is "far
  easier (and more forgiving) than trying to get the entire mating surface exactly
  right" ([Hackaday][hd]).
- **[AON3D][an] states both the transition-fit recipe directly**: "slope the
  inner or outer diameter by ~2°, creating slight clearance on one end, and add
  0.2 mm vertical crush ribs around the circumference" (and, separately, a
  press-fit version with no taper, for one-time assembly only). **The specific
  rib count (three or four) is [Creative3DP][c3]'s** — AON3D's own page states
  the 0.2 mm protrusion and the ~2° slope but does not itself give a rib count.
- **Crush ribs are effectively single-use.** They deform plastically on insertion;
  repeated assembly loses the grip. If the joint must come apart and back together,
  use compliant ribs sized for elastic deflection instead (see below).
- **Same principle as this repo's ribbed bores**, generalised from tool grip to
  press fits. `models/drill_storage` used `RIB_COUNT = 3` beads
  whose contact edge sits `RIB_GRIP = 0.22` mm (diametral) inside the tool, and
  its design notes (`models/drill_storage/docs/design-notes.md`) explain why an
  elastic rib and a crushable bump are different animals: the earlier bumps could only be crushed, not
  deflected, so no single interference number covered the size range. Details in
  `bores-and-ribs.md`.
- Under load or heat, crushed ribs have far less contact area than a full press
  fit — do not use them to retain something that carries a real radial load hot
  ([Hackaday][hd], comments).

## Print-in-place hinge (knuckle)

The four figures below are the **author's estimates**, not independently
published numbers — no source found breaks a knuckle hinge down into
around-the-pin vs. between-faces clearance specifically. They are consistent
with (sit inside) the general rotating-joint clearances in the per-material
table further down, which **is** a real published table ([UAVMODEL][uv]).

- **0.3 mm around the pin** (radial).
- **0.2 mm between knuckle faces** (per face, axially).
- **Pin length ≥ 1.5× pin diameter**, so the knuckle cannot cock and bind.
- **A 5 mm pin at 0.2 mm layer height is a good starting point** — big enough that
  0.3 mm of clearance is a modest fraction of it, small enough to stay stiff.

Per-material rotating clearance, from [UAVMODEL][uv]'s matrix:

| Material | Rotating | Sliding | Snap-fit |
| --- | --- | --- | --- |
| PLA | 0.50 mm | 0.30 mm | 0.20 mm |
| PETG | 0.60 mm | 0.40 mm | 0.25 mm |
| ABS / ASA | 0.40 mm | 0.25 mm | 0.15 mm |
| ASA, enclosed chamber | 0.35 mm | 0.20 mm | — |
| TPU 95A | 0.80 mm | 0.50 mm | 0.30 mm |

PETG needs the most because it oozes and bridges gaps aggressively when molten;
ABS needs the least because it shrinks away from itself as it cools and creates
some of its own gap ([UAVMODEL][uv]).

A print-in-place hinge is either free on the first flex or fused forever. Print a
single-knuckle coupon before committing a hinge to a large part.

## Mortise-and-tenon

**0.2–0.3 mm per wall on desktop FDM** (author's estimate — no source found
publishes a desktop-FDM-specific mortise-and-tenon clearance; it is sized to sit
in the same band as this reference's other snug-sliding fits).

Markforged publishes **0.08 mm per wall (0.16 mm diametral)** for a consistent
sliding fit on the Mark Two ([Markforged joinery][mj]: "a .08mm gap between each
wall (.16mm diametrically) is enough to allow two pieces to consistently achieve
a sliding fit" — the live page blocks automated fetches, confirmed instead via
its [Wayback Machine
archive](https://web.archive.org/web/20250628040449/https://markforged.com/resources/blog/joinery-onyx))
— **do not port that number.** It is an industrial machine printing Onyx
(chopped-carbon nylon) with far lower dimensional variation than a desktop FFF
printer running PLA or PETG. Quoting it here produces a joint that will not go
together. (The Composites Design Guide was also checked as a possible
co-source for this figure; its content could not be retrieved this session —
its portal page renders no text and its PDF didn't yield a matching passage —
so it is not cited for this specific number.)

- FDM shows visible stepping on the tenon's angled faces; the tenon usually needs
  a light clean-up pass, or design it with flat-to-the-bed faces
  ([Formlabs][fl]).
- Fillet the internal corner where the tenon meets its shoulder — that corner is a
  crack initiator and it is exactly where the joint is loaded.
- Lead-in chamfer on the mortise mouth and on the tenon's leading edges.

## Cross-dowel / barrel nut

**Bore = nut OD + 0.2–0.3 mm** (diametral, author's estimate — no source found
discusses cross-dowels or barrel nuts specifically; this places the bore in
[Creative3DP][c3]'s general "close running" to "free/loose" band, +0.15 to
+0.35 mm, since the dowel needs to rotate rather than just locate). The dowel
must rotate freely in its bore so the bolt can find the thread; a tight bore
turns assembly into a fight.

- If the barrel nut is itself printed, **print it in PETG with its axis parallel
  to the bed.** Standing it on end puts the thread's hoop load directly across
  layer boundaries and it splits on the first turn.
- Chamfer the bore mouth so the dowel drops in, and chamfer the bolt's cross-hole.
- The bolt hole through the mating part wants a clearance fit, not a thread — this
  joint is otherwise the `fasteners-and-inserts` skill's territory.

## Magnet pocket

**Ø + 0.2–0.3 mm, depth = magnet thickness**, for a press fit that seats flush.
This is the **author's estimate**: [Creative3DP][c3] lists magnets among the use
cases for its −0.10 mm-diametral press-fit rung, but does not publish a magnet
pocket dimension or a worked example — no source found does. The figure above
generalises the same fit ladder to a slightly looser (+0.2–0.3 mm) allowance
because a magnet, unlike a bearing race, tolerates a bit of play without losing
function.

Illustrative calculation only (not a published measurement): a 6 × 3 mm disc
magnet at that allowance would want roughly a 6.2–6.3 mm diameter × 3.0 mm deep
pocket — the diameter gets the allowance, the depth stays at the magnet's own
3.0 mm thickness, per the "not more" rule right below.

- **Depth = the magnet's thickness, not more.** A deeper pocket lets the magnet
  sit proud-or-sunk unpredictably and kills the holding force, which falls off
  fast with any air gap.
- Cap the pocket with a thin printed layer (0.4–0.8 mm) rather than leaving the
  magnet exposed — it keeps the magnet in without glue and protects the face.
- **Check polarity before you close the pocket.** A magnet glued in backwards is a
  reprint.
- Lead-in chamfer at the mouth, as with everything else; a magnet is brittle and
  will chip on a square corner.

## Bearing pocket

**Nominal OD −0.05 to −0.10 mm per side**, plus a **0.5 mm × 45° lead-in
chamfer** ([Creative3DP][c3]).

Worked example: a **608 bearing (22 mm OD)** → a **~21.95 mm** pocket in PLA.

- The interference is per side and small on purpose. A bearing pressed into an
  over-tight plastic bore pinches its outer race and the bearing stops turning
  freely — the symptom is a joint that got *stiffer* after assembly.
- PETG tolerates up to about 0.10 mm per side; PLA prefers the 0.05–0.10 mm band
  ([Creative3DP][c3]).
- Support the bearing on a shoulder rather than pressing it to a blind floor, so
  the press load goes into the outer race only.
- If the pocket must be reusable, use compliant ribs rather than a bore
  interference.

## Scaling with part size

- **Add ~+0.05 mm of clearance per 100 mm of part dimension** for thermal
  contraction. This is why a 30 mm dovetail at 0.25 mm works and the same
  clearance on a 150 mm one binds.
- **Small features tolerate tighter fits than large ones — but this page's own
  numbers are SLA/SLS, not FDM.** [Formlabs][fl] gives 0.2 mm (< 20 mm²) / 0.4 mm
  (> 20 mm²) under an explicit "SLA / SLS Minimum Assembly Tolerance" heading,
  and states plainly that FDM needs *more* clearance than SLA/SLS "because the
  FDM printer has more dimensional variability" — its own FDM figure is ~0.5 mm,
  not size-split at all. Use the SLA/SLS split only to see the *shape* of the
  size effect (roughly 2× for a large feature); for an actual FDM number, scale
  0.5 mm the same way, or use this reference's per-joint clearances above, which
  are already FDM-sourced.
- Apply both size adjustments together. They pull in opposite directions and a
  mid-size joint often lands back where it started — which is fine; the point
  is to know why.

## Minimum printable features

0.4 mm nozzle. Sources disagree by roughly 2×, so both columns are given.

| Feature | Absolute floor | Recommended |
| --- | --- | --- |
| Hole Ø, vertical axis (Z) | 1.0 mm | 2.0 mm ([Hydra][hr]) |
| Hole Ø, horizontal axis (XY) | 1.5 mm | 2.0 mm ([Hydra][hr]) |
| Post / pin Ø | 1.6 mm = 4× extrusion width | 3.0 mm |
| Wall thickness | 0.4 mm (1 perimeter) | 0.9 mm ([Hydra][hr]) |
| Unsupported bridge | — | < 5 mm ([Protolabs Network][pl]) |

Below the floor the feature does not exist after slicing: a gap under ~0.3 mm
merges into solid, and a post under one extrusion width is skipped entirely.

## Sources

[fl]: https://formlabs.com/blog/how-to-3d-print-interlocking-joints/
[pl]: https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
[hr]: https://www.hydraresearch3d.com/design-rules
[mg]: https://support.markforged.com/portal/s/article/Composites-Design-Guide-1
[mj]: https://markforged.com/resources/blog/joinery-onyx
[c3]: https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/
[an]: https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/
[uv]: https://blog.uavmodel.com/3d-printer-print-in-place-mechanism-design-clearance-tolerances-hinge-geometry-and-joint-guidelines-2026/
[hd]: https://hackaday.com/2020/10/15/adding-crush-ribs-to-3d-printed-parts-for-a-better-press-fit/
[sy]: https://siraya.tech/blogs/news/3d-print-joints

- [Formlabs — How to 3D print interlocking parts and assemblies][fl]
- [Protolabs Network — How to design parts for FDM 3D printing][pl]
- [Hydra Research — Design rules and best practices for FFF][hr]
- [Markforged — Composites design guide][mg] — listed for completeness; its
  content could not be retrieved this session (portal renders no text, PDF
  extraction found no matching passage), so it is not cited as the source of
  any specific figure in this document
- [Markforged — 3D printed joinery: simplifying assembly][mj] — the 0.08 mm
  figure is confirmed via this page's Wayback Machine archive (see Mortise-and-
  tenon above)
- [Creative3DP — Press-fit tolerances for 3D printing][c3]
- [AON3D — Engineering fits: how to design for 3D printed assemblies][an]
- [UAVMODEL — Print-in-place mechanism design: clearance tolerances, hinge geometry and joint guidelines][uv]
- [Hackaday — Adding crush ribs to 3D printed parts for a better press fit][hd]
- [Siraya Tech — 3D print joints guide][sy]
