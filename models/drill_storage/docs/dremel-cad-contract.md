# Dremel three-part holder CAD contract

## References

- **Context:** `models/drill_storage/README.md`; the existing `drill_storage.base`, `insert`, and `hex.cover` patterns.
- **Specification:** [Dremel specification](dremel-specification.md), DR-1–DR-4.
- **Supporting evidence:** User-specified 1×2 footprint, 2.5 mm shank, 50 mm tool length; existing drill-holder fit and snap dimensions.

## Current slice

- **Name:** Closed Dremel inspection scene and release integration.
- **Anchor part:** Accepted ASA base, TPU insert and PETG cover as a positioned three-part scene; no new print geometry.
- **Purpose and print pose:** Show closed use-pose fit while each registered leaf still returns its own print pose.
- **In scope:** Assembly transforms, component colors and independent print/export entries; integration proof and public documentation.
- **Deferred interfaces:** None. Physical trials of TPU grip, snap force and large tool-head packing remain outside CAD evidence.

## Applicable specification constraints

| Requirement | Consequence for this slice |
| --- | --- |
| DR-1 | Assemble only the independent Dremel variant; preserve existing sets. |
| DR-2 | 1×2 footprint, 50 mm tool below a 70 mm assembled top. |
| DR-3 | No copied Printables geometry. |
| DR-4 | Base, insert and cover are individually printable and shown seated in the scene. |

## Evidence-backed dimensions

| Dimension | Value | Source | Applies to |
| --- | --- | --- | --- |
| Accepted base and TPU insert | body 41.5×83.5, shoulder z=24, collar 39.2×81.2, insert top z=37.2 | user acceptances, 2026-09-28 | cover envelope |
| Cover outer/inner width | 41.5 / 39.6 mm; Y dimensions add one 42 mm grid cell | `drill_storage.box` | cover walls and bore |
| Foot-to-tool envelope | tool floor z=8 plus 50 mm length = top z=58 | user dimension and accepted base | cap clearance |
| Cover height | family `cover_height_for(50, bore_floor_z=8, cap_h=2)` = 46 mm above shoulder, assembled top z=70 (10U) | quantized family rule, 6 mm minimum headroom | cover roof |
| Snap bead | 0.38 mm radial protrusion into 39.6 mm bore at z=6 above mouth | adapted from family's 0.45 mm; nominal passage strain 2×(0.38−0.20)/39.2 ≈ 0.92% below PETG repeated 1.0% | cover retention |
| Print roof | 2 mm solid cap | 10 × 0.2 mm layers, double the 1×1 cover's 1 mm cap for the longer unsupported plate | cover top |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Long rectangular snap stiffness | Model-fit proof and physical print trial | Geometric clearance and strain estimate can be checked; force and fatigue cannot. |
| Variable Dremel head diameters | Trial actual tools against the 7 mm layout | The cover can enclose 50 mm length, but 55 large tool heads may not all fit at once. |

## Service and assembly constraints

1. Do not export the mixed-material scene as one printable STL; export base, insert and cover separately.
2. Close the cover over the seated insert with its engraved label upright.

## Required skills

| Concern | Skill | Why it applies |
| --- | --- | --- |
| Grip/guide clearances | `fdm-fits-and-clearances`, `part-joints` | Distinct rigid guide and compliant insert. |
| Cover snap | `box-closures`, `snap-fits` | Long rectangular collar may be stiffer than the 1×1 precedent. |
| Edge treatment and proof | `build123d-geometry-ops` | Bore mouths, cavity, and print-pose validation. |

## Verifiable predicates

- [x] Closed scene positions: base z=0..36, insert z=29.2..37.2 and cover z=24..70, measured in the scene smoke run.
- [x] All three seated pairwise intersections are 0 mm³; `uv run check drill_storage.dremel` passed the collision, rim seat and 50 mm tool-clearance gate. Deliberately lowering the cover by 2 mm produced 483 mm³ overlap and demonstrated that the gate goes red.
- [x] All three print-pose leaves exported independently via `uv run export`; the parent declares `IS_ASSEMBLY = True` and was rendered as a scene.

## Visual review

- **Views to show:** Closed scene isometric and long-side orthographic, alongside accepted individual-part HTML views.
- **What they let the human judge:** Proportions, component colors and upright assembled label.
- **Artifact:** `exports/drill_storage.dremel.html`, isometric and right projections; individual `dremel.base`, `.insert` and `.cover` HTML views and STL exports.

## Acceptance gate

- **Human feedback requested:** Inspect the finished scene and the three print-pose leaf views.
- **Acceptance signal:** The PETG cover was explicitly accepted on 2026-09-28; integration may proceed.
- **Next slice after acceptance:** None.

## Accepted earlier slices

The base was accepted with “looks good, continue”; its 55 free guides terminate
at z=8, and its two receiver grooves and cover shoulder were probed. The TPU
insert was accepted after its 55 through-bores, 2.65 mm land and zero seated
overlap were verified. The PETG cover was accepted after its 2 mm roof, 50 mm
tool envelope and zero seated interference with both existing parts were
verified. Its narrow-span snap-strain estimate is 0.92%, but fit force and
tool-head packing remain physical-print questions.
