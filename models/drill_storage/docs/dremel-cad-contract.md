# Dremel holder CAD contract

## References

- **Context:** `models/drill_storage/README.md`; Gridfinity dimensions in `models/drill_storage/box.py`.
- **Specification:** [Dremel specification](dremel-specification.md), DR-1–DR-3.
- **Supporting evidence:** User dimensions (1×2 cells, 2.5 mm shank, up to 50 mm tool length); Printables reference is visual inspiration only.

## Current slice

- **Name:** Upright Dremel rack.
- **Anchor part:** Single printable PETG holder.
- **Purpose and print pose:** Tools stand shank-down in blind bores; two Gridfinity feet land on z=0, bores open upward.
- **In scope:** One contiguous rounded body with a regular array of upright tool positions and standard feet.
- **Deferred interfaces:** No cover, mating closure or insert is specified; do not build them in this slice.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| DR-1 | New package and roster entry; existing models unchanged. |
| DR-2 | 42×84 mm cell pitch, 41.5×83.5 mm outside envelope; 2.5 mm nominal shanks, 50 mm total tool length. |
| DR-3 | No inferred lid or copied reference geometry. |

## Evidence-backed dimensions

| Dimension | Value | Source | Applies to |
| --- | --- | --- | --- |
| Grid pitch / pad | 42 / 41.5 mm | `drill_storage.box.GRID/PAD` | body and feet |
| Foot height | 4.4 mm | `drill_storage.box.BASE_H` | underside |
| Nominal shank | 2.5 mm | user | bores |
| Tool length | at most 50 mm | user | exposed tool clearance |
| Bore allowance | `fits.FREE` (0.4 mm diametral, PETG) | FDM fits skill | drop-in bores |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Actual 2.5 mm shank tolerance and printer hole accuracy | Trial print and adjust fit if needed | Does not block reviewable anchor; cannot claim tested physical grip. |

## Service and assembly constraints

1. Tools lift vertically without friction retention; they are not enclosed or held for transport.
2. Keep the bores blind, with a solid floor, and leave space between mouths for fingers and varying head diameters; larger heads may require alternate slots.

## Required skills

| Concern | Skill | Why |
| --- | --- | --- |
| Printed bores | `fdm-fits-and-clearances` | Diametral clearance in PETG. |
| Edge treatment and geometry proof | `build123d-geometry-ops` | Bore lead-ins, top perimeter and solid checks. |

## Verifiable predicates

- [x] One connected solid with two feet, flat on z=0, within 41.5×83.5 mm. Measured on `create()`; both foot interiors solid, gap between feet empty at z=1.
- [x] All 55 bores open from the top and end at z=8, above the bottom face. Point samples at every bore mouth and beneath every floor passed; an upright 50 mm shaft in a bore extends above the open top (physical tool-head clearance is not proven).
- [x] Bore centers stay inside the body, with material between neighboring bores. Point samples adjacent to all 55 bore walls passed.

Edge survey: 2 sharp 8.5 mm edges on the underside bridge where the two
standard feet meet the body (x=±20.75, y=0, z=4.4); these retain the flat
Gridfinity foot junction and are not hand-contact edges. The 55 unclassifiable
edges are periodic seam edges inside the cylindrical bores, not exposed
corners. The top perimeter and every bore mouth are chamfered.

## Visual review

- **Views to show:** Isometric and top orthographic.
- **What they let the human judge:** Number and spacing of positions, proportions, foot arrangement and open-top presentation.
- **Artifact:** `exports/drill_storage.dremel.html`, `exports/drill_storage.dremel_iso.png`, `exports/drill_storage.dremel_top.png`.

## Acceptance gate

- **Human feedback requested:** Is this upright single-piece layout the desired Dremel holder?
- **Acceptance signal:** Pending explicit acceptance of this anchor.
- **Next slice after acceptance:** Only if a cover or a different retention interface is requested and accepted.
