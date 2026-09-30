# Dremel three-part holder CAD contract

## References

- **Context:** `models/drill_storage/README.md`; the existing `drill_storage.base`, `insert`, and `hex.cover` patterns.
- **Specification:** [Dremel specification](dremel-specification.md), DR-1–DR-6.
- **Supporting evidence:** User-accepted 2026-09-30 inventory and spare allocation; accepted 1×2 footprint, 50 mm tool length and existing drill-holder fit/snap dimensions. Earlier uniform 2.5 mm shanks are historical.

## Current slice

- **Name:** Accepted-inventory rebore of the existing 55-position Dremel holder.
- **Anchor part:** Existing accepted ASA base and its fixed 5×11 guide layout; matching TPU insert and unchanged PETG cover.
- **Purpose and print pose:** Store the owned mixed-shank inventory with spare capacity; retain the independent base, insert and cover print poses and the closed inspection scene.
- **In scope:** Assign nominal diameter groups to existing positions and apply the family's diameter-dependent small-bore compensation to matching guide/insert bores. Preserve guide clearance, TPU grip-land and upper-relief fit rules.
- **Unchanged:** 55 coordinates, 7 mm pitch, 1×2 envelope, 50 mm tool-length capacity, floor/seat heights, insert retention, cover collar/snap, cover geometry and assembly transforms.
- **Deferred interfaces:** None; this is a rebore of the accepted parts, not a new mating-interface design. Physical trials of TPU grip, snap force and large tool-head packing remain outside CAD evidence.

## Applicable specification constraints

| Requirement | Consequence for this slice |
| --- | --- |
| DR-1 | Change only the independent Dremel variant; preserve existing sets. |
| DR-2 | Retain the 1×2 footprint and 50 mm tool below the 70 mm assembled top; replace uniform shanks with the accepted nominal diameter groups. |
| DR-3 | No copied Printables geometry. |
| DR-4 | Retain the individually printable ASA base, TPU insert and PETG cover and their seated scene. |
| DR-5 | Provide the specification's 41 owned-tool positions plus 14 spares, totaling 55; corresponding ASA/TPU bores receive the same diameter-dependent compensation before material-specific fit allowances. |
| DR-6 | Assign ascending diameter groups to the existing x-major coordinates; preserve all envelope and mating-interface dimensions. |

## Evidence-backed dimensions

| Dimension | Value | Source | Applies to |
| --- | --- | --- | --- |
| Accepted base and TPU insert | body 41.5×83.5, shoulder z=24, collar 39.2×81.2, insert top z=37.2 | user acceptances, 2026-09-28 | cover envelope |
| Cover outer/inner width | 41.5 / 39.6 mm; Y dimensions add one 42 mm grid cell | `drill_storage.box` | cover walls and bore |
| Foot-to-tool envelope | tool floor z=8 plus 50 mm length = top z=58 | user dimension and accepted base | cap clearance |
| Cover height | family `cover_height_for(50, bore_floor_z=8, cap_h=2)` = 46 mm above shoulder, assembled top z=70 (10U) | quantized family rule, 6 mm minimum headroom | cover roof |
| Snap bead | 0.38 mm radial protrusion into 39.6 mm bore at z=6 above mouth | adapted from family's 0.45 mm; nominal passage strain 2×(0.38−0.20)/39.2 ≈ 0.92% below PETG repeated 1.0% | cover retention |
| Print roof | 2 mm solid cap | 10 × 0.2 mm layers, double the 1×1 cover's 1 mm cap for the longer unsupported plate | cover top |

### Bore assignment

The inventory table in the specification owns the counts. Number the existing
positions 1–55 in x-major order: X = −14, −7, 0, 7, 14 mm, with
Y = −35, −28, −21, −14, −7, 0, 7, 14, 21, 28, 35 mm in each column.
No coordinate moves and no new bore labels are required.

| Existing position indices (inclusive) | Nominal shank diameter (mm) |
| --- | ---: |
| 1 | 1.0 |
| 2 | 1.5 |
| 3 | 2.0 |
| 4–13 | 2.35 |
| 14–38 | 2.9 |
| 39–55 | 3.1 |

`SHANK_COUNTS` records the ordered diameter/count pairs. `BORES` associates
each existing `(x, y)` with its nominal diameter; `CUT_BORES` associates
the same coordinates with `nominal + family.small_bore_comp(nominal)`.
The ASA guide adds its existing free-fit allowance to that compensated
diameter; the TPU insert applies its existing land and relief allowances.
The historic single nominal diameter and 2.65 mm land are not current
mixed-inventory bore targets.

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

- [x] All 55 original coordinates retain the six nominal diameter/count groups, including the 14 spare positions; the top render shows the unchanged 5×11 layout.
- [x] Four-direction boundary probes verify every ASA guide and matching TPU land/relief against its compensated diameter and existing fit allowance; all guide floors remain at z=8.
- [x] Updated base and insert each return one solid seated on z=0 (numerical tolerance 0.000001 mm); cover geometry and assembly transforms are unchanged.
- [x] `uv run check drill_storage.dremel` passes the inventory/bore gate, all three zero-overlap pairs, rim seat and 50 mm tool clearance. Substituting the former uniform 2.5 mm bore geometry produces 210 failed physical predicates. The throwaway red-run harness subsequently hit a list-versus-int assertion error, after recording those failures.
- [x] Base and insert rebuilt/exported through `uv run view`, their HTML views opened locally, and the base top PNG inspected. `uv run ruff check .` and `uv run ty check .` pass.

The diameter-dependent compensation retains the family's existing calibration;
these probes establish CAD dimensions, not measured printed TPU retention.

### Edge survey

`sharp_convex_edges` reports 26 sharp / 55 unclassifiable edges on the
base and 8 sharp / 110 unclassifiable edges on the print-pose insert.
This rebore retains the accepted interface geometry; it does not claim a
zero-sharp-edge audit. The unchanged sharp-edge exceptions are:

- Base outer cover-seat perimeter at z=24: four 75.5/33.5 mm lines and
  four quarter-circle edges of length 6.283 mm. Keep the flat cover landing.
- Base two 8.5 mm straight edges at z=4.4 between the Gridfinity feet:
  retain the accepted foot/body junction.
- Base cartridge receiver perimeter at each of z=31.35 and z=34.15:
  four 74.2/32.2 mm lines and four quarter-circles of length 2.985 mm per
  perimeter. Retain the accepted retention groove profile.
- Insert retention-bead perimeter at print z=6.4: four 74.2/32.2 mm lines
  and four quarter-circles of length 2.749 mm. Retain the accepted TPU bead.

The unclassifiable edges are cylindrical surface seams, not physical sharp
rims: one 20.7 mm guide seam per position, and one 3.2 mm relief seam plus
one 3.5 mm land seam per position. Bore-mouth chamfers are retained.

## Visual review

- **Views to show:** Updated base and insert in their print poses; closed scene isometric and long-side orthographic for the unchanged envelope.
- **What they let the human judge:** Diameter grouping at unchanged positions, retained proportions, component colors and upright assembled label.
- **Artifacts:** `exports/drill_storage.dremel.base.html`, `exports/drill_storage.dremel.insert.html`, their updated STL exports, and `exports/drill_storage.dremel.base_top.png`. Closed scene rebuilt at `exports/drill_storage.dremel.html`.

## Acceptance gate

- **Acceptance signal:** The user confirmed the purpose/specification update, retained 55 positions and authorized selection of the additional diameters on 2026-09-30. The approved allocation is recorded in the specification; no additional interface decision is pending.
- **CAD evidence state:** Mixed-bore inventory, radii, guide floors and seated non-interference verified on 2026-09-30. Actual tool-head packing and printed grip effort remain physical-trial questions.
- **Next slice after verification:** None; print trials still govern real-world TPU grip and snap effort/durability.

## Historical acceptance and verification

The following records are explicitly historical evidence from the earlier
uniform-2.5 mm-shank design accepted on 2026-09-28, not current-slice proof.

The base was accepted with “looks good, continue”; its 55 free guides
terminated at z=8, and its two receiver grooves and cover shoulder were
probed. The TPU insert was accepted after its 55 through-bores, then-2.65 mm
land and zero seated overlap were verified. The PETG cover was accepted
after its 2 mm roof, 50 mm tool envelope and zero seated interference with
both existing parts were verified. Its narrow-span snap-strain estimate
was 0.92%; fit force and tool-head packing remained physical-print questions.

Historical scene/release integration evidence:

- Closed scene positions were measured at base z=0..36, insert z=29.2..37.2 and cover z=24..70.
- All three seated pairwise intersections were 0 mm³; `uv run check drill_storage.dremel` passed the collision, rim-seat and 50 mm tool-clearance gate. Deliberately lowering the cover by 2 mm produced 483 mm³ overlap and demonstrated that the historical gate went red.
- All three print-pose leaves exported independently via `uv run export`; the parent declared `IS_ASSEMBLY = True` and was rendered as a scene.
- The closed isometric/right projections were recorded at `exports/drill_storage.dremel.html`, alongside individual `dremel.base`, `.insert` and `.cover` HTML views and STL exports.
