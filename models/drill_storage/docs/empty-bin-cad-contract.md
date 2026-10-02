# Empty bin — generator-style body revision

## References

- Context: `../README.md`, `../box.py`.
- Specification: [empty-bin-specification.md](empty-bin-specification.md), EB-1–EB-4 and EB-6.
- Supporting evidence: `box.gridfinity_foot`, the 42 mm pitch and 7 mm height unit; the referenced generator's thin print-bed plate and interior-open foot cavities, as confirmed in the user's screenshot.

## Current slice

- Name: empty bin body.
- Anchor part: `drill_storage.bin.base`, a parametric PETG container with optional internal organization.
- Purpose and print pose: general-purpose grid-sized storage on a Gridfinity baseplate, foot-down and open upward.
- In scope: half-cell X/Y sizes and foot arrangement, wall and bottom-plate thickness, whole-unit height, interior-open feet, magnet pockets, dividers, labels and scoops; retain a lid-bearing rim.
- Existing lid interface: the removable lid, its stack socket and print support retain the approved mating envelope.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| EB-1 | Default cavity has no holes, cartridge, label or partition; existing holders are unchanged. |
| EB-2 | Full and half Gridfinity feet beneath one open container; 42 mm pitch and whole-unit vertical height. |
| EB-3 | Preserve a flat perimeter landing for the inside-plug lid. |
| EB-4 | Expose generator controls; use a 1 mm PETG default wall with at least two perimeters and a flat lid-bearing rim. |
| EB-6 | Default 1×2×5U feet have closed 1 mm bed plates, interior-open cavities and a raised cell seam; no underside ribs or mouse ears. Divider switch is on with 0×0 counts; magnets, labels and scoops are off. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| XY pitch / vertical unit | 42 / 7 mm | `drill_storage.box.GRID`, `HEIGHT_UNIT` |
| Per-cell foot | 41.5 mm envelope, 4.4 mm exterior profile; half-foot 20.5 mm | Same four outer sections as `drill_storage.box.gridfinity_foot` |
| Exterior margin | 0.25 mm on each side of the grid | `drill_storage.box.PAD` |
| Default floor / wall | 1 / 1 mm; 0 bottom override means wall thickness | Generator reference: closed foot plate, hollow open to bin interior; the former 1 mm continuous raised floor and underside ribs were replaced |
| Rim bevels and landing | 0.2 mm exterior + 0.2 mm mouth lead-in, 0.6 mm flat | Retains lid-bearing land on 1 mm wall |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Printed lid retention | Snap bead and groove geometry is implemented (EB-9); confirm PETG fit by physical print | CAD overlap proof does not establish printed retention |
| Printed baseplate fit and larger-footprint warping | Physical print calibration | Cannot claim physical fit from CAD alone |
| Optional internal fixtures over the open foot cavities | Print divided/scooped variants and assess bridging before production use | CAD verifies geometry and stacking, not unsupported first layers of dividers or scoops |

## Service and assembly constraints

1. Bin must remain open and unobstructed for loose contents.
2. Each printed part starts on z=0 in its own print pose.

## Required skills

`model-documentation`, `cad-iteration`, `fdm-fits-and-clearances`, `build123d-geometry-ops`; the existing lid interface stays as approved.

## Verifiable predicates

- [x] Default 1×2 body is one solid in foot-down pose. Each foot has a closed 1 mm print-bed plate, an interior-open void above it, and a raised seam at the cell boundary; a 2 mm bottom override thickens the plate without closing the cavity. The solid-base switch instead leaves a full raised floor.
- [x] Original body proof covered half-cell foot placement, 1–4 mm walls, magnet pockets, divider walls, label tabs and scoops; optional fixture roots remain above the foot cavities to avoid occupying the stackable lid's sockets.
- [x] Default envelope remains 41.5×83.5×21 mm. The half-grid 1.5×1.5 and organized 1×1 closed-scene checks exercise lift-off lid fit and stacked foot seating on the revised body.
- [x] Default 1 mm wall retains 0.6 mm of flat rim between two 0.2 mm lead-ins, offering a level landing for the inside-plug lid.
- [x] Edge survey: default body has 2 deliberately square foot-to-body shoulders at z=4.4 mm, preserving the Gridfinity transition; 0 other sharp convex edges and 0 unclassifiable edges. The 2×2 body has 4 such outer shoulders, and no other raw edges.

## Visual review

- Views: default body isometric and top; live default 3D artifact.
- Human review: wall proportion, new per-cell floor and closed underside, and reserved lid rim.
- Artifacts: `exports/drill_storage.bin.base.html`, `exports/drill_storage.bin.base_iso.png`, `exports/drill_storage.bin.base_top.png`.
- Lid integration refinement: optional dividers, labels, and scoops end at least 3.6 mm below the body rim, leaving the 3 mm plug skirt 0.6 mm of clearance. The body exterior envelope and mating rim remain unchanged.

## Acceptance gate

- User explicitly confirmed the body purpose and replacement of its raised floor / underside ribs with the generator-style closed plates and interior-open feet (2026-09-28).
- Visual acceptance of this body revision is pending. The already implemented lid remains a dependent interface whose envelope is unchanged; see [lid-cad-contract.md](lid-cad-contract.md).
