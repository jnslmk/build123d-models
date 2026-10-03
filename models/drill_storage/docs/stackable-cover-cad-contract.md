# Stackable cover — current CAD slice

## References

- Context: `../README.md`, `../box.py`, `../hex/README.md`.
- Specification: [stackable-cover-specification.md](stackable-cover-specification.md), revised SC-1–SC-4.
- Supporting evidence: `models.lib.gridfinity.gridfinity_foot`, `box.cover_height_for`, existing cover geometry and fit constants.

## Current slice

- Name: approved optional separate stacking lips for the 1×1 stackable cover family.
- Anchor part: the existing accepted stackable PETG cover, reviewed as `drill_storage.wood.cover_stackable`; the other four labels/heights use that same receiving geometry.
- Purpose and print pose: preserve the existing receiver and closure; one-piece socket-down/mouth-up remains the default, while split mode prints the roof-down body and glue-face-down/socket-up lips.
- In scope: Boolean split option, support-free socket-floor split, named child print poses, preserved closure/labels/receiver, glue instructions and targeted geometry gates.
- Deferred interfaces: no new base, cartridge, connector, alignment pin, fastener or adhesive-gap feature.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| SC-1 | Full 4.4 mm foot profile enters a 4.4 mm-deep socket; lip sits at 7U + 4.4 mm and next foot's body seats at 7U. Only stackable lip widens from 41.5 to 42 mm. |
| SC-2 | Original bases and smooth covers retain their envelope and snap joints; the lip mouth's sub-perimeter wall is a user-accepted experimental exception, not proven printable. |
| SC-3 | Integral support spans the deeper socket floor in print pose when enabled and can be removed for stacking; disabling support yields the unchanged cover/socket without sacrificial geometry. |
| SC-4 | Two named children `lid_body` and `stacking_lips`, both on z=0 and separated only for preview; split at the socket floor and omit all sacrificial material. Ideal assembled geometry equals the clean one-piece lid. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Original 1×1 pad, body and smooth cover | 41.5 mm | `models.lib.gridfinity.PAD`, unchanged |
| Stackable lip envelope | 42 mm, +0.25 mm per side | Gridfinity draft drawing; user-authorized exception at the lip only |
| Foot lower bevel / straight band / upper bevel | 0.7 / 1.8 / 1.9 mm | `models.lib.gridfinity.FOOT_C1`, `FOOT_STRAIGHT`, `FOOT_C3` |
| Full foot seat and added lip height | 4.4 mm | `models.lib.gridfinity.BASE_H`; drawing's 2U = 14 + 4.4 mm |
| PETG socket clearance | `fits.SLIDING`, 0.22 mm diametral | `models.lib.fits` |
| Narrowest nominal lip wall | (42 − 41.5 − 0.22)/2 = 0.14 mm | Full-width foot shoulder and user-accepted thin-lip exception |
| Minimum solid cover ceiling | 1.0 mm | `box.CAP_H` |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Will a 0.14 mm nominal lip wall survive PETG slicing, first-layer spread and repeated stacking? | Inspect slicer toolpath and print a fit/durability coupon with the actual machine | Cannot call this physically printable or load-bearing before testing |
| Will nominally 42 mm lips coexist in adjacent cells without touching? | Print and measure neighbouring holders in the intended grid | No tolerance budget remains inside 42 mm pitch |
| Breakaway support interface and removal effort | Cut the four nibs on a physical print and verify socket remains intact | Handling is unproven until printed |

## Service and assembly constraints

1. Pull out the sacrificial support before seating a second holder.
2. Stack only on the existing 1×1 foot and keep the regular cover as a support-free option.

## Required skills

`model-documentation`, `cad-iteration`, `box-closures`, `fdm-fits-and-clearances`, `build123d-geometry-ops`.

## Verifiable predicates

- [x] Full foot seats to the socket floor without overlap, and the assembled stack pitch equals a whole 7 mm multiple — all five targeted cover gates passed; physical fit still pending.
- [x] Solid cap and tool-tip clearance remain under the full-depth socket — all five targeted cover gates passed.
- [x] Default support bridges the deeper socket floor in print pose and exposes the seat when removed — geometry gates passed; physical breakaway and unsupported bridge remain unverified.
- [x] Only stackable lip reaches 42 mm; original body retains 41.5 mm and snap interface — targeted gates passed.
- [x] Split children are valid connected solids on z=0; lips point socket-up and retain the complete 4.4 mm height, with substantial planar bed-adhesion faces — all five split gates passed. Bed area is not measured common glue-contact area.
- [x] Independent reassembly retains clean one-piece labels, closure and socket, with no overlapping material and a connected no-gap assembly — all five split gates passed at 0.01 mm³ Boolean tolerance.
- [x] Integration create/export smoke succeeded for all seven confirmed leaves: each yields two named valid connected children and independent STLs on z=0, including three bin parameter variations. Independent review passed; its bed-area wording nit was corrected.
- Shared split-gate red proof on representative bin specimens: reversing the lips to socket-down produced 94.108221 mm³ missing material and failed equivalence; lifting the body 0.3 mm failed pose/bed, equivalence and connectivity; lowering it 0.3 mm failed direct body/lips overlap at 223.432254 mm³. All five positive family gates, Dremel and the full bin gate passed. Ruff and ty passed.

## Visual review

- Views: stackable-cover isometric, socket-down projection, side section revealing the entire 4.4 mm foot/lip engagement, and neighbouring-holder view for the 42 mm lip.
- Human review: thin lip, full foot seat, support removal access and unchanged original cover/base silhouettes.
- Prior 2.5 mm-seat artifacts (`exports/drill_storage.wood.cover_stackable.html` and `_bottom.png`) are superseded; regenerate views after physical gates.
- Integration browser proof: actual Chromium live-generation and repeated cache-hit child-STL downloads passed. This is export/UI evidence, not slicing or physical glue acceptance.

## Acceptance gate

- Human confirmation: draft-spec thin 42 mm lip accepted as an experiment, despite the ~0.14 mm nominal wall and lost neighbouring-cell tolerance.
- Physical acceptance signal: pending printed fit, support removal, durability and adjacent-cell trial.
- Split-option purpose/decision signal: user confirmed all seven upright/bin/Dremel stackable lids on 2026-09-30, explicitly excluding sideways holders; planar glue split is approved.
- Split print/glue acceptance: create/export smoke, desktop/mobile visual inspection, live/cache browser downloads, mutation rejection proof and positive geometry gates complete. Adhesive compatibility/strength, actual flatness and bond-line thickness remain physically unverified. New square interface edges preserve the planar joint; bed-face area does not establish bonded contact area or load capacity, and existing receiver/snap/text exceptions remain unchanged.
- Next slice: any alteration to the original base, foot, snap, or a separately retained accessory requires a new accepted slice.

## Split print edge survey

Integration `sharp_convex_edges` audit; counts are body / lips. Every child
had zero unclassifiable edges. Allowed boundaries were matched by exact edge
identity from planar bed faces, not a loose positional exception.

| Leaf | Raw sharp | Allowed planar bed/interface boundary | Retained original sharp |
| --- | --- | --- | --- |
| wood | 8 / 24 | 8 / 16 | 0 / 8 |
| metal | 36 / 24 | 8 / 16 | 28 / 8 |
| stone | 33 / 24 | 8 / 16 | 25 / 8 |
| allen | 8 / 24 | 8 / 16 | 0 / 8 |
| hex.bits | 30 / 24 | 8 / 16 | 22 / 8 |

Planar bed/interface boundaries intentionally remain square to preserve the
approved planar split. Retained body edges are the original engraved glyph
mouths (metal 28, stone 25, BITS 22). The eight retained lip edges on each
tool cover preserve the accepted experimental ~0.14 mm receiver-mouth profile;
chamfering them would alter it. No edge retuning was made. Bed-face area and
edge exceptions do not prove common bonded area or adhesive strength.
