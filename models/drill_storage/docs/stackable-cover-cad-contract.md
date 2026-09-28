# Stackable cover — current CAD slice

## References

- Context: `../README.md`, `../box.py`, `../hex/README.md`.
- Specification: [stackable-cover-specification.md](stackable-cover-specification.md), SC-1–SC-3.
- Supporting evidence: `box.gridfinity_foot`, `box.cover_height_for`, existing cover geometry and fit constants.

## Current slice

- Name: 1×1 stackable cover family.
- Anchor part: the shared stackable PETG cover, reviewed as `drill_storage.wood.cover_stackable`; the other four labels/heights use that same receiving geometry.
- Purpose and print pose: accept an upper holder's Gridfinity foot while keeping the original cover-to-base interface; print top down, mouth up, with integral removable support under the socket.
- In scope: five stackable cover entries, one shared foot receiver and support, compatibility/clearance proof, visual review.
- Deferred interfaces: no new base, cartridge, connector, or fastener.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| SC-1 | Recess tracks the shared foot's lower bevel and straight band with a named PETG sliding fit, within the 41.5 mm envelope. |
| SC-2 | Existing public cover geometry remains unchanged; solve each new cover height with the thicker top and existing quantisation. |
| SC-3 | Integral support must span the socket's ceiling during print and be removable without obstructing the final seat. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| 1×1 outer envelope | 41.5 mm | `box.PAD` |
| Foot lower bevel / vertical band / upper bevel | 0.7 / 1.8 / 1.9 mm | `box.FOOT_C1`, `FOOT_STRAIGHT`, `FOOT_C3` |
| Foot mid-width | 37.7 mm | `box.PAD - 2 * box.FOOT_C3` |
| PETG socket clearance | `fits.SLIDING` diametral | `models.lib.fits` |
| Socket depth | 2.5 mm | lower bevel + straight band, leaving upper bevel proud |
| Minimum solid cover ceiling | 1.0 mm | `box.CAP_H` |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Breakaway support interface and removal effort | Geometry check and printed coupon for final calibration | Physical handling is unproven until printed |

## Service and assembly constraints

1. Pull out the sacrificial support before seating a second holder.
2. Stack only on the existing 1×1 foot and keep the regular cover as a support-free option.

## Required skills

`model-documentation`, `cad-iteration`, `box-closures`, `fdm-fits-and-clearances`, `build123d-geometry-ops`.

## Verifiable predicates

- [x] Foot fits inside the socket without intersection and locates radially before the body bears on the rim — `stackable_checks.check_cover` seats `gridfinity_foot()` after simulated lattice removal; collision volume zero in all five sets.
- [x] Enough cap remains under the socket and the longest tool clears it — 1 mm solid ceiling, tested against each set's tool-tip height (1.5–5.5 mm clearance across the five).
- [x] Support reaches the ceiling during printing and removes without leaving geometry across the receiving surface — one solid with four nibs; section probe and simulated removal show lattice below the floor and uninterrupted material behind it. Breakaway force requires a print.
- [x] Covers stay within the footprint, print on z=0 and preserve the snap interface — 41.5 mm bounding box, exact shared bore/bead, targeted stackable-cover gates.

## Visual review

- Views: wood stackable cover isometric, socket-down bottom projection, and live 3D artifact.
- Human review: stacking seat, support removal access, and unchanged outer silhouette.
- Artifact: `exports/drill_storage.wood.cover_stackable.html`, `exports/drill_storage.wood.cover_stackable_bottom.png`.

## Acceptance gate

- Human feedback requested on the stackable cover family after presentation.
- Acceptance signal: pending; user confirmed the variant purpose and integral support strategy, not the finished geometry.
- Next slice: any change to the base or a separately retained accessory requires a new accepted slice.
