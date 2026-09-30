# Dremel three-part holder CAD contract

## References

- **Context:** `models/drill_storage/README.md`.
- **Specification:** [Dremel specification](dremel-specification.md), DR-1–DR-10; common split-print requirements [SC-4](stackable-cover-specification.md).
- **Acceptance signal:** The user confirmed 8U stacking pitch and the lower-floor repack, then approved optional separate lips for all seven stackable lids on 2026-09-30.

## Current slice

- **Name:** Approved optional separate stacking lips.
- **Anchor:** The accepted 8U stackable PETG cover.
- **In scope:** Optional socket-floor split into two named support-free print-pose children; keep both receivers and their connecting web in one lip STL, document planar glue usage and verify ideal assembled equivalence.
- **Unchanged:** Accepted six-column base/insert, diameter counts and calibrated fits, 8U stacking pitch, 2 mm roof, feet, cartridge retention, flat shoulder z=24, label/snap, smooth cover and parent scene. The lower-floor evidence below is historical verification, not split-print proof.

## Evidence-backed dimensions

| Dimension | Accepted value |
| --- | --- |
| Floor and tool tip | z=3; 50 mm tool reaches z=53 |
| Layout | X=−15,−9,−3,+3,+9,+15; Y=−35,−28,−21,−14,−7,+7,+14,+21,+28,+35; first 55 x-major positions |
| Stack pitch and overall top | 56 mm (8U); z=60.4 |
| Stackable print height | 36.4 mm above the z=24 seat |
| Socket depth and roof | 4.4 mm; 2 mm roof, underside z=54 |
| Tool headroom | 1 mm nominal in the stackable cover |
| Smooth cover | Unchanged 46 mm print height, assembled top z=70; 15 mm headroom on the lower floor |
| Materials | ASA base, TPU insert, PETG covers |

## Verifiable predicates

- [x] All 55 closed floor disks have solid backing at z=0.02, 1.5 and 2.98.
- [x] Every guide and matching cartridge land/relief retains the accepted radius.
- [x] Base and insert are one valid solid at z=0.
- [x] Stackable cover builds as one valid solid, supported and clean, at z=0.
- [x] An upper base seats at 56 mm without interference; 0.3 mm over-insertion meets the socket floors.
- [x] All 55 nominal tool envelopes plus 0.9 mm headroom clear the stackable cover, with solid roof above.
- [x] Seated cover clears both base and cartridge; smooth scene still clears all parts.
- [x] Both support lattices, 0.2 mm release gaps and 2 mm roofs remain present.
- [x] Exported parts and local views rebuilt; lint/type checks passed.
- [x] Full Dremel leaf gate passed: valid connected prints on z=0, 4.4 mm socket-up lips, planar bed-adhesion faces and separate preview footprints. Bed area is not common glued-contact area: the retained body pillow fillet narrows planar overlap.
- [x] Independent reassembly equals the clean one-piece cover at 0.01 mm³ Boolean tolerance, retaining both sockets, 2 mm roof, labels/snap and 8U pitch, with zero body/lips overlap.
- [x] Integration create/export smoke succeeded for all seven confirmed leaves, including Dremel's two receivers in one valid connected lip child: both named children and independent STLs rest on z=0. Independent review passed with bed-area wording clarified.
- [x] Actual Chromium live-generation and repeated cache-hit child-STL download smoke passed; this establishes the export/UI path, not sliced printability or bonded strength.
- Shared gate mutation proof on representative bin specimens: socket-down lips fail equivalence (94.108221 mm³ missing); body raised 0.3 mm fails pose/bed, equivalence and connectivity; body lowered 0.3 mm fails direct overlap (223.432254 mm³). Positive Dremel gate, ruff and ty passed.

## Prior feasibility proof

The old layout's five Y=0 guides broke into the inter-foot gap at a z=3 floor;
the trial failed ten floor predicates. A z=6 floor stayed closed but collided
with all 55 tool paths under an 8U roof. The accepted repack passed full-floor
disk probes at z=0.02, 1.5 and 2.98 as one valid base solid.

## Physical trial boundary and acceptance

User accepted the layout and height decision, not printed performance.
Six-millimetre horizontal pitch reduces tool-head packing clearance; trial
actual tools, the 1 mm headroom, floor strength, TPU grip and snap effort.
The existing approximately 0.14 mm receiver mouth walls remain an accepted
experimental print-trial exception. Remove both support lattices and attachment
nibs before stacking; verify foot fit, neighbouring cells and loaded strength.
Reprint both the base and TPU insert: the previous 5×11 insert is incompatible.
Current CAD integration passed the assembly and stackable-cover physical gates.
Restoring the old z=8 floor caused 110 stackable tool/roof failures, proving the
clearance gate rejects the old geometry. Measured top/pitch/roof/tip are
60.4 / 56 / 54 / 53 mm. Base, insert and stackable HTML views were rebuilt and
opened locally; the shorter cover's right PNG was inspected. The smooth parent
scene was rebuilt with the repacked base/insert. The user accepted the visual
result with “commit and push” on 2026-09-30; physical print trials remain pending.

The user approved the optional split-print delta on 2026-09-30. Print the body
roof-down and the one-piece lip field glue-face-down/socket-up, without socket
supports. Dry-align its centred 0.25 mm per-side overhang before gluing; see
[family instructions](../README.md#separate-printable-stacking-lips).
Adhesive compatibility, cured strength, printed flatness, actual bond-line
height and loaded-stack durability remain physically unverified. New interface
perimeter edges intentionally remain square; only the overlapping planar regions
are bonded, not the whole bed-face area. This option does not assert acceptance
of the existing experimental thin walls.

## Current edge survey

The base has 26 sharp / 55 unclassifiable edges: eight cover-seat perimeter
edges retain the flat shoulder, two foot/body junctions preserve the foot
interface, and sixteen cartridge-receiver perimeters retain bead engagement.
The insert has eight sharp / 110 unclassifiable edges: the eight retention-bead
perimeter edges are functional. Unclassifiable edges are cylindrical seams,
not a claim of no sharp edges.

The clean stackable cover has 78 sharp / zero unclassifiable edges: 46 shallow
letter edges preserve readable engraving, sixteen snap edges preserve detent
engagement, eight receiver mouth edges preserve the experimental thin wall,
and eight receiver/body transitions preserve the flat shoulder. The reused
support lattices are sacrificial and excluded from the clean-cover survey.

### Split print edge survey

Integration `sharp_convex_edges` audit; counts are body / lips.

| Leaf | Raw sharp | Allowed planar bed/interface boundary | Retained original sharp | Unclassifiable |
| --- | --- | --- | --- | --- |
| Dremel stackable cover | 62 / 32 | 0 / 24 | 62 / 8 | 0 / 0 |

Allowed boundary edges were matched by exact identity from planar bed faces,
not a loose positional rule. Lip bed/interface edges intentionally remain
square for the approved planar split; the body's retained pillow fillet
leaves no sharp bed-boundary edges. The 62 original body edges comprise
16 snap-bead ring edges preserving detent engagement and 46 engraved glyph
edges preserving readable lettering. Eight retained lip-mouth edges preserve
the accepted experimental ~0.14 mm receiver profile. No edge retuning was
made; this audit and bed area do not establish common bonded area or strength.

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
