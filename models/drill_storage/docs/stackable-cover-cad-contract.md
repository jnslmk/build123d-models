# Stackable cover — current CAD slice

## References

- Context: `../README.md`, `../box.py`, `../hex/README.md`.
- Specification: [stackable-cover-specification.md](stackable-cover-specification.md), revised SC-1–SC-3.
- Supporting evidence: `box.gridfinity_foot`, `box.cover_height_for`, existing cover geometry and fit constants.

## Current slice

- Name: 1×1 stackable cover family.
- Anchor part: the shared stackable PETG cover, reviewed as `drill_storage.wood.cover_stackable`; the other four labels/heights use that same receiving geometry.
- Purpose and print pose: accept an upper holder's Gridfinity foot while keeping the original cover-to-base interface; print top down, mouth up, with optional integral removable support under the socket (enabled by default).
- In scope: five stackable cover entries, one shared foot receiver and optional support, compatibility/clearance proof, visual review.
- Deferred interfaces: no new base, cartridge, connector, or fastener.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| SC-1 | Full 4.4 mm foot profile enters a 4.4 mm-deep socket; lip sits at 7U + 4.4 mm and next foot's body seats at 7U. Only stackable lip widens from 41.5 to 42 mm. |
| SC-2 | Original bases and smooth covers retain their envelope and snap joints; the lip mouth's sub-perimeter wall is a user-accepted experimental exception, not proven printable. |
| SC-3 | Integral support spans the deeper socket floor in print pose when enabled and can be removed for stacking; disabling support yields the unchanged cover/socket without sacrificial geometry. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Original 1×1 pad, body and smooth cover | 41.5 mm | `box.PAD`, unchanged |
| Stackable lip envelope | 42 mm, +0.25 mm per side | Gridfinity draft drawing; user-authorized exception at the lip only |
| Foot lower bevel / straight band / upper bevel | 0.7 / 1.8 / 1.9 mm | `box.FOOT_C1`, `FOOT_STRAIGHT`, `FOOT_C3` |
| Full foot seat and added lip height | 4.4 mm | `box.BASE_H`; drawing's 2U = 14 + 4.4 mm |
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

- [ ] Full foot seats to the socket floor without overlap, and the assembled stack pitch equals a whole 7 mm multiple — targeted `stackable_checks.check_cover` geometric gate; physical fit still pending.
- [ ] Solid cap and tool-tip clearance remain under the full-depth socket — five targeted cover gates.
- [ ] Default support bridges the deeper socket floor in print pose and exposes the seat when removed; disabling it leaves the cover/socket unchanged — geometry gate, physical breakaway and unsupported bridge pending.
- [ ] Only stackable lip reaches 42 mm; original smooth cover/base remain 41.5 mm, with snap interface unchanged — geometry gate and parent validation pending.

## Visual review

- Views: stackable-cover isometric, socket-down projection, side section revealing the entire 4.4 mm foot/lip engagement, and neighbouring-holder view for the 42 mm lip.
- Human review: thin lip, full foot seat, support removal access and unchanged original cover/base silhouettes.
- Prior 2.5 mm-seat artifacts (`exports/drill_storage.wood.cover_stackable.html` and `_bottom.png`) are superseded; regenerate views after physical gates.

## Acceptance gate

- Human confirmation: draft-spec thin 42 mm lip accepted as an experiment, despite the ~0.14 mm nominal wall and lost neighbouring-cell tolerance.
- Physical acceptance signal: pending printed fit, support removal, durability and adjacent-cell trial.
- Next slice: any alteration to the original base, foot, snap, or a separately retained accessory requires a new accepted slice.
