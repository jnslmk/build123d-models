# Empty bin — accepted body slice

## References

- Context: `../README.md`, `../box.py`.
- Specification: [empty-bin-specification.md](empty-bin-specification.md), EB-1–EB-3.
- Supporting evidence: `box.gridfinity_foot`, the 42 mm pitch and 7 mm height unit; the adjacent `gridfinity-bins` repository is a proportions reference, not imported source.

## Current slice

- Name: empty bin body.
- Anchor part: `drill_storage.bin.base`, a parametric PETG container with optional internal organization.
- Purpose and print pose: general-purpose grid-sized storage on a Gridfinity baseplate, foot-down and open upward.
- In scope: half-cell X/Y sizes and foot arrangement, wall thickness, whole-unit height, hollow feet, magnet pockets, dividers, labels and scoops; retain a lid-bearing rim.
- Deferred interfaces: removable lid, its retention, stack socket and print support; these must fit within the existing footprint and leave the bin accessible.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| EB-1 | Default cavity has no holes, cartridge, label or divider; existing holders are unchanged. |
| EB-2 | Full and half Gridfinity feet beneath one open container; 42 mm pitch and whole-unit vertical height. |
| EB-3 | Preserve a flat perimeter landing for a future inside-plug lid; no dependent lid geometry before acceptance. |
| EB-4 | Expose each linked generator control; use a 1 mm PETG default wall, with at least two perimeters and a flat lid-bearing rim. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| XY pitch / vertical unit | 42 / 7 mm | `drill_storage.box.GRID`, `HEIGHT_UNIT` |
| Per-cell foot | 41.5 mm envelope, 4.4 mm profile; half-foot 20.5 mm | Same four sections and bevel dimensions as `drill_storage.box.gridfinity_foot` |
| Exterior margin | 0.25 mm on each side of the grid | `drill_storage.box.PAD` |
| Default floor / wall | 1 / 1 mm above foot | PETG two-perimeter minimum; 0.2 mm reserve beyond 0.8 mm |
| Rim bevels and landing | 0.2 mm exterior + 0.2 mm mouth lead-in, 0.6 mm flat | Retains lid-bearing land on 1 mm wall |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Lid retention and minimum lid height | Test inside-plug lid against accepted 1 mm rim in dependent slice | No lid geometry in this slice |
| Printed baseplate fit and larger-footprint warping | Physical print calibration | Cannot claim physical fit from CAD alone |

## Service and assembly constraints

1. Bin must remain open and unobstructed for loose contents.
2. Each printed part starts on z=0 in its own print pose.

## Required skills

`model-documentation`, `cad-iteration`, `fdm-fits-and-clearances`, `build123d-geometry-ops`; `box-closures` applies to the deferred lid interface.

## Verifiable predicates

- [x] One connected solid in foot-down print pose with an open cavity and solid floor: tested default, half-cell, half-grid, divided, magnet-pocketed and thick-wall variants; OCC point probes find default floor material at z=4.8 and cavity air at z=8.
- [x] Grid-sized and half-grid bodies retain pitch, 0.5 mm grid gap and 7 mm height units: 1×1×2U measured 41.5×41.5×14 mm; 1.5×1.5×3U 62.5×62.5×21 mm; 2×2×4U 83.5×83.5×28 mm, all single solids.
- [x] Every exposed option reaches geometry: toggling half-foot side changes material at (10, 0, 1); hollow/solid feet, 1–4 mm walls, magnet pockets, divider walls, tab placement/lightened ribs and scoops exercised. Current OCC probes: label at (0, 12, 16.8), scoop at (0, -18, 8), divider at (0, 0, 17.1), magnet void at (13, 13, 1).
- [x] Default 1 mm wall retains 0.6 mm of flat rim between two 0.2 mm lead-ins, offering a level landing for an inside-plug lid. This is a geometric allowance, not a printed lid-fit claim.
- Edge survey on default 1×2: 0 unclassifiable edges and 50 sharp edges. Two are 8.5 mm foot-to-body shoulder segments at z=4.4, deliberately square to preserve the Gridfinity foot transition; the other 48 are bottom/inner edges of the hollow foot's cruciform print-bed ribs. These ribs need flat bed contact and positive junctions to support the thin floor, not a decorative fillet; none are exposed in the storage cavity. The top outside and cavity mouth are chamfered.

## Visual review

- Views: default body isometric and top; a configured 2×2 divided bin with magnets, right-aligned labels and scoops in isometric; live default 3D artifact.
- Human review: wall proportion, open cavity, underside foot bracing, optional fixtures, and reserved lid rim.
- Artifacts: `exports/drill_storage.bin.base.html`, `exports/drill_storage.bin.base_iso.png`, `exports/drill_storage.bin.base_top.png`, `exports/drill_storage.bin.base_options.png`.
- Lid integration refinement after body acceptance: optional dividers, labels, and scoops now end at least 3.6 mm below the body rim, leaving the 3 mm plug skirt 0.6 mm of clearance. The empty default body envelope and foot geometry are unchanged; `uv run check drill_storage.bin` exercises the populated closed assembly.

## Acceptance gate

- Human feedback requested: accept or revise the empty bin body before adding its lid.
- Acceptance signal: user confirmed the revised bin body and instructed implementation of its lid (2026-09-28).
- Next slice: removable stackable lid; see [lid-cad-contract.md](lid-cad-contract.md).
