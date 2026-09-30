# Dremel three-part holder CAD contract

## References

- **Context:** `models/drill_storage/README.md`; the existing `drill_storage.base`, `insert`, and `hex.cover` patterns.
- **Specification:** [Dremel specification](dremel-specification.md), DR-1–DR-7.
- **Supporting evidence:** User-accepted 2026-09-30 inventory and spare allocation; accepted 1×2 footprint, 50 mm tool length and existing drill-holder fit/snap dimensions. Earlier uniform 2.5 mm shanks are historical.

## Current slice

- **Name:** Separate stackable Dremel cover option.
- **Anchor part:** `drill_storage.dremel.cover_stackable`, a separately printable PETG cover; the accepted ASA base and TPU insert are fixed mating references.
- **Purpose and print pose:** Retain labelled snap closure while receiving two full-depth Gridfinity feet at a 10U stack pitch. Print socket-down, open mouth up.
- **In scope:** Two 4.4 mm sockets centred at X=0, Y=±21 mm; 42×84 mm top lip; 2 mm roof below the sockets; default-on `support` boolean reusing the family's removable breakaway lattices.
- **Unchanged:** ASA base, TPU insert, 55-position inventory rebore, smooth cover, label and snap interfaces. The parent closed scene continues to use the smooth cover.
- **Deferred interfaces:** No new dependent parts. Printed foot fit, thin-wall survival, loaded-stack strength and neighbouring-cell clearance remain experimental physical-trial questions.

## Applicable specification constraints

| Requirement | Consequence for this slice |
| --- | --- |
| DR-1 | Change only the independent Dremel variant; preserve existing sets. |
| DR-2 | Retain the 1×2 footprint and clearance for 50 mm tools; the stackable option raises the top to z=74.4 without changing the tool floor. |
| DR-3 | No copied Printables geometry. |
| DR-4 | Retain the individually printable ASA base, TPU insert and PETG cover and their seated scene. |
| DR-5 | Preserve the specification's accepted 41 owned tools and 14 spare positions; no guide/insert changes. |
| DR-6 | Preserve the existing x-major bore positions, envelopes and mating interfaces. |
| DR-7 | Add only the separate stackable cover, with full-depth sockets, preserved roof, default-on removable supports and experimental thin-wall print-trial boundary. |

## Evidence-backed dimensions

| Dimension | Value | Source | Applies to |
| --- | --- | --- | --- |
| Accepted base and TPU insert | body 41.5×83.5, shoulder z=24, collar 39.2×81.2, insert top z=37.2 | user acceptances, 2026-09-28 | cover envelope |
| Cover outer/inner width | 41.5 / 39.6 mm; Y dimensions add one 42 mm grid cell | `drill_storage.box` | cover walls and bore |
| Foot-to-tool envelope | tool floor z=8 plus 50 mm length = top z=58 | user dimension and accepted base | cap clearance |
| Cover height | family `cover_height_for(50, bore_floor_z=8, cap_h=2)` = 46 mm above shoulder, assembled top z=70 (10U) | quantized family rule, 6 mm minimum headroom | cover roof |
| Snap bead | 0.38 mm radial protrusion into 39.6 mm bore at z=6 above mouth | adapted from family's 0.45 mm; nominal passage strain 2×(0.38−0.20)/39.2 ≈ 0.92% below PETG repeated 1.0% | cover retention |
| Print roof | 2 mm solid cap | 10 × 0.2 mm layers, double the 1×1 cover's 1 mm cap for the longer unsupported plate | cover top |
| Stackable receiver | two full-depth 4.4 mm sockets at X=0, Y=−21/+21 mm | user-confirmed stackable option, 2026-09-30 | upper holder feet |
| Stackable top and pitch | assembled top z=74.4; full foot seating yields 70 mm (10U) pitch | user-confirmed stackable option, 2026-09-30 | stack datum |
| Stackable lip and roof | top lip 42×84 mm; 2 mm solid roof remains below socket floors | user-confirmed stackable option, 2026-09-30 | cover top |
| Receiver mouth walls | approximately 0.14 mm nominal | accepted experimental exception, consistent with family stackable covers | print trial, not a validated printable wall |

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
| Experimental receiver mouth walls | Inspect slicer toolpaths and print PETG trial | CAD fit does not prove the ~0.14 mm mouth walls print or survive handling. |
| Foot fit, loaded stack and adjacent cells | Remove supports; trial mating feet and neighbouring holders | No loaded-stack or print-tolerance claim before physical trials. |

## Service and assembly constraints

1. Do not export the mixed-material scene as one printable STL; export base, insert and cover separately.
2. Close the cover over the seated insert with its engraved label upright.
3. Export `.cover_stackable` independently; the parent scene deliberately retains `.cover`.
4. With `support=True` (default), remove both breakaway lattices and all attachment nibs before inserting feet. Disable support only for slicer supports or a verified unsupported bridge.
5. Inspect sliced thin-wall toolpaths and printed fit/durability before loading a stack.

## Required skills

| Concern | Skill | Why it applies |
| --- | --- | --- |
| Grip/guide clearances | `fdm-fits-and-clearances`, `part-joints` | Distinct rigid guide and compliant insert. |
| Cover snap | `box-closures`, `snap-fits` | Long rectangular collar may be stiffer than the 1×1 precedent. |
| Edge treatment and proof | `build123d-geometry-ops` | Bore mouths, cavity, and print-pose validation. |

## Verifiable predicates

- [x] The separate PETG leaf builds as one valid solid at z=0 in socket-down print pose, with supports enabled and disabled.
- [x] Both 4.4 mm receivers align with the existing feet at Y=±21 mm: the real upper ASA base seats at 70 mm pitch without interference; lowering it by 0.3 mm meets the socket floors.
- [x] Measured lip 42×84 mm and print height 50.4 mm give assembled top z=74.4; probes verify the preserved 2 mm roof beneath each socket.
- [x] The smooth cover geometry supplies the unchanged label and snap; seated base and TPU insert have zero interference, and both cells retain at least 6 mm clearance above 50 mm tools.
- [x] Both default-on support lattices are present with a 0.2 mm release gap; disabling support leaves both receivers open.
- [x] The smooth cover, ASA base, TPU insert and smooth-cover parent scene are unchanged.
- [x] `uv run check drill_storage.dremel.cover_stackable`, repository Ruff and ty checks passed; the view artifact built and was opened locally. The socket-fit and clean-socket predicates failed against the initial misplaced-cut geometry before passing after correction.

The clean-cover `sharp_convex_edges` survey found **78 sharp edges and zero
unclassifiable edges**. Intentional exceptions: 46 unchanged shallow engraved
letter edges preserve the accepted label; 16 unchanged snap-profile edges
preserve detent engagement; eight receiver mouth-perimeter edges retain the
experimental 0.14 mm wall rather than chamfering it away; eight receiver/base
transition edges preserve the flat shoulder and unchanged cover envelope.
The reused breakaway lattice is sacrificial, not a handled finished surface.
Printed grip, snap effort, thin-wall survival and stack durability are not
established by CAD predicates.

## Visual review

- **Views to show:** Stackable cover in print pose with supports enabled and disabled; socket/top view and a side or section-like view showing roof and receiver depth.
- **What they let the human judge:** Two-cell receiver alignment, widened lip, retained label/snap, support removal access and thin mouth walls.
- **Artifacts:** `exports/drill_storage.dremel.cover_stackable.html` (shaded, supports enabled, opened locally); `_iso.png` (support-enabled print pose); `_clean_bottom.png` (both exposed sockets, no supports); `_clean_right.png` (side view with hidden receiver/roof lines), all using the same `drill_storage.dremel.cover_stackable` filename prefix.

## Acceptance gate

- **Acceptance signal:** The user confirmed the separate stackable option, retained smooth scene/base/insert, 10U pitch, full-depth sockets and experimental mouth-wall exception on 2026-09-30.
- **CAD evidence state:** Stackable geometry predicates passed; the user accepted the visual result with “great, commit and push” on 2026-09-30. Physical print trials remain pending. Earlier smooth-cover and inventory evidence below remains historical.
- **Next slice after verification:** No dependent geometry requested; physical print trials remain necessary before loading a stack.

## Historical acceptance and verification

### Accepted inventory rebore, 2026-09-30

The user confirmed the purpose/specification update, retained 55 positions and
authorized additional-diameter selection. The accepted allocation is recorded
in DR-5 and DR-6; no new interface was introduced.

- All 55 original coordinates retained the six nominal diameter/count groups and 14 spares; the top render showed the unchanged 5×11 layout.
- Four-direction probes verified every ASA guide and matching TPU land/relief against its compensated diameter and existing fit allowance; all floors remained z=8.
- Base and insert each returned one solid seated on z=0 within 0.000001 mm; cover geometry and assembly transforms were unchanged.
- `uv run check drill_storage.dremel` passed the inventory/bore gate, three zero-overlap pairs, rim seat and 50 mm tool clearance. Substituting former uniform 2.5 mm bores produced 210 failed physical predicates; the throwaway red-run harness subsequently hit a list-versus-int assertion error after recording those failures.
- Base and insert were rebuilt/exported through `uv run view`, their HTML views opened locally and the base top PNG inspected. `uv run ruff check .` and `uv run ty check .` passed.
- Artifacts were `exports/drill_storage.dremel.base.html`, `exports/drill_storage.dremel.insert.html`, updated STL exports and `exports/drill_storage.dremel.base_top.png`; the closed scene was rebuilt at `exports/drill_storage.dremel.html`.

The compensation retained the family's calibration; these probes established
CAD dimensions, not measured printed TPU retention or tool-head packing.

Historical edge survey: `sharp_convex_edges` reported 26 sharp / 55
unclassifiable edges on the base and 8 sharp / 110 unclassifiable edges on
the print-pose insert. It did not claim a zero-sharp-edge audit. Retained
exceptions were the base cover-seat perimeter at z=24 (four 75.5/33.5 mm
lines and four 6.283 mm quarter-circle edges); two 8.5 mm foot/body-junction
edges at z=4.4; cartridge receiver perimeters at z=31.35 and 34.15
(four 74.2/32.2 mm lines and four 2.985 mm quarter-circles each); and insert
bead perimeter at print z=6.4 (four 74.2/32.2 mm lines and four 2.749 mm
quarter-circles). Unclassifiable edges were cylindrical seams: one 20.7 mm
guide seam, one 3.2 mm relief seam and one 3.5 mm land seam per position.
Bore-mouth chamfers were retained.

### Earlier uniform-bore acceptance, 2026-09-28

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
