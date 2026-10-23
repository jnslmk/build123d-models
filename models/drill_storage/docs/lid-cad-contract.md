# Empty bin — two-part stacking lid glue interface

## References

- Context: `../README.md` and the [accepted body slice](empty-bin-cad-contract.md).
- Specification: [empty-bin-specification.md](empty-bin-specification.md), EB-2–EB-5, EB-7 and EB-8; common split-print requirements [SC-4](stackable-cover-specification.md).
- Supporting evidence: `models.lib.gridfinity` foot profile and `models.lib.gridfinity_socket` lower-foot socket/support helpers (extracted unchanged from the bin lid); `models.lib.fits.SLIDING` PETG diametral; accepted body wall/rim; [support design procedure](../../../docs/fdm-support-design.md) and [removable-support research](../../../docs/research-removable-fdm-supports.md).

## Current slice

- Name: two-part-only keyed glue interface with self-supporting undersides, accepted 2026-10-23.
- Anchor: accepted `drill_storage.bin.lid` for the accepted bin body; no downstream body redesign.
- Public print result: exactly `lid_body` and `stacking_lips`, with no one-piece alternative or support/split switches. Preserve all full/half-cell layouts and taller roofs.
- Joint scope: keyed positive location, light retention during adhesive cure and adhesive relief, self-supporting in both supplied print poses without unsupported precision mating cantilevers. Preserve snap-in closure, roof, socket fit and stacking pitch.
- Earlier shallow-rebate integration/export results do not establish verification of this underside correction; physical glue/retention acceptance is pending.

The common [joint design](stackable-cover-cad-contract.md#joint-design-for-this-slice)
removes the broad roof rebate. A flat, bed-backed body roof carries discrete
45° conical locating recesses (0.4 mm deep/radius) and 45° triangular adhesive
channels (0.2 mm wide, 0.1 mm deep). The connected lip field prints
socket-mouth-down/joint-up, carrying 0.3 mm-high tapered locating/crush cones
with 0.45 mm base radius, four per receiver plus an asymmetric fifth key.
The original split plane remains the hard seating datum. At the default
1 mm roof, the discrete 0.4 mm recesses leave at least 0.6 mm backing; the
shallow channels leave 0.9 mm. The interior roof, closure and 2.5 mm foot seat
retain their original geometry. No unsupported precision ledge or horizontal
adhesive-reservoir ceiling remains; sliced and physical behavior is unverified.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| EB-2 | Lid footprint and receiving sockets align with every full/half foot of the matching base, without exceeding the 0.5 mm grid gap. |
| EB-3 | Independently printable removable lid; default minimum is 2.5 mm socket + 1 mm solid ceiling + 3 mm locating skirt = 6.5 mm total. Configurable height grows the plate/roof while preserving skirt engagement; EB-9 retains the snap closure. |
| EB-4 | A 1 mm body wall remains viable: derive skirt width from the body cavity and a PETG sliding fit; keep a flat rim bearing on the accepted body's 0.6 mm landing. |
| EB-5 | Preserve presentation; remove the former public support Boolean. |
| EB-7 | Historical support-only revision, no longer the public printing path. |
| EB-8 / SC-3–SC-4 | Exactly two named print children with self-supporting underside joint geometry, keyed location, light cure-time retention and glue relief; retain complete roof/skirt and connected receiver walls/webs. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Foot socket depth | 2.5 mm (0.7 lower bevel + 1.8 straight) | `drill_storage.box.STACK_SOCKET_DEPTH` |
| Socket XY clearance | `fits.SLIDING`, 0.22 mm diametral | PETG sliding-fit class; calibration required |
| Lid roof above socket | 1 mm minimum | `drill_storage.box.CAP_H`, five layers at 0.2 mm |
| Plug engagement | 3 mm minimum | Three times 1 mm rim budget; lift-off locating skirt |
| Outer shell | grid span minus 0.5 mm | Existing accepted bin body |
| Fixture clearance | 3.6 mm below body rim | 3 mm skirt plus 0.6 mm service gap; accepted body's optional fixture headroom refined during lid integration |
| Historical support body | 0.8 mm ribs, 5 mm centre pitch | Superseded one-piece support revision; historical process rows below are not new-joint dimensions |
| Historical nominal roof process gap | 0.2 mm trial candidate in the superseded support-only revision | Baseline and candidate slices: OrcaSlicer 2.4.2, Centauri Carbon 0.4 mm / Generic PETG, uniform 0.2 mm first/normal layers, generated supports and brim off. Lattice ended at Z=2.4 mm; Z=2.6 mm contained only attachments inside sockets; full roof Bridge started at Z=2.8 mm with HEIGHT=0.2. This is not a slice of the current two-part joint |
| Historical perimeter process separation | 0.6 mm each side, rail 0.8 mm thick | Superseded support-only manufacturing gap, not a current mating-fit allowance |
| Historical tab necks | Two 0.4 × 0.8 mm sections per cell, measured 0.64 mm² total; gap height plus 0.02 mm roof overlap | Superseded support-only gate measured both necks; candidate slice preserved two attachment locations per socket at Z=2.6. Old four 0.6 × 0.6 mm nibs totalled 1.44 mm². Printed fracture/removal was unproven |
| Historical full-cell roof/lattice span | 36.52 / 30.8 mm; revised rail outer span 35.32 mm | Superseded support-only straight-edge band 2.86 mm; revised nominal band 0.6 mm, extending backing 2.26 mm beyond each old edge. Gate probed straight edges and all rounded corners |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Joint location, retention and adhesive relief | Current integrated CAD gates passed; printed dry-fit and cured-bond trial remain required | CAD evidence does not establish physical acceptance; old support slices cannot close this gate |
| Full/half-cell joint fit and loaded stacking | Representative minimum, shifted, multi-cell and taller lids with matching feet | Preserve foot seating/closure and stack pitch; actual fit and strength require printed evidence |

## Service and assembly constraints

1. Print both named child STLs in supplied poses. Dry-fit the keyed joint, confirm complete seating and matching upper-foot orientation, then apply PETG-compatible adhesive without fouling sockets or closure. Light retention helps during cure; it is not proof of bond strength.
2. The skirt bead still detents into the bin groove. Pull the cured lid to unsnap and access the bin.
3. Closed display scene is not a slicer part; export the base and both lid children separately.

## Required skills

`model-documentation`, `cad-iteration`, `box-closures`, `fdm-fits-and-clearances`, `build123d-geometry-ops`.

## Current verification — self-supporting underside revision, 2026-10-23

The geometry owner reports **124 passing CAD assertions** for the bin lid
integration, covering default 1×2, shifted 1.5×1.5, organized 1×1, minimum
0.5×0.5, all-half-cell and 9 mm taller-roof layouts. All supplied-pose growth
checks had zero unsupported samples. Default measured body/lip bed contact
was 3446.35 / 434.92 mm²; intentional crush overlap was 0.054192 mm³ seated,
reducing to 0.008897 mm³ after 0.02 mm withdrawal. These are CAD measurements,
not printed contact area, retention force or adhesive strength.

Restoring the former broad-rebate joint failed both body and lip underside
predicates. Both named child STLs and combined STL/GLB exported; the default
HTML view was rebuilt/opened and exact CAD sections inspected. Ruff and ty
passed. The [common verification record](stackable-cover-cad-contract.md#current-verification--self-supporting-underside-revision-2026-10-23)
owns cross-family mutation, edge-audit and artifact details.
No new slicer or physical-print evidence was produced.

## Historical verification — superseded support and planar-split implementations

These results predate the 2026-10-23 keyed joint; retained baseline evidence
does not establish that current geometry, slices or downloads have passed.

- [x] Revised support-on lid is one valid connected solid on z=0 within OCC tolerance; each full/half-cell rail/lattice body is a single bed-seated component, retained by exactly two measured 0.32 mm² necks.
- [x] Support material backs previously empty straight-edge bands and all rounded corners. The old lattice fails both sockets' coverage predicates; full-cell backing extends 2.26 mm beyond the old lattice envelope.
- [x] Geometry has positive wall separation (gate measured minimum 0.650 mm below the ceiling) and a nominal 0.2 mm roof gap away from tabs. A deliberately gap-filling third attachment fails gap, neck-count/section and location predicates; the old four-nib geometry fails neck predicates. Candidate slicing preserves one empty layer away from two surviving tabs.
- [x] Support-on contains all clean geometry and adds material only in the sockets. Bidirectional Boolean comparison against the captured baseline support-off lid has zero added and removed volume; roof, closure and fit geometry are preserved.
- [x] `uv run check drill_storage.bin` passes default 1×2, shifted 1.5×1.5, organized 1×1, minimum 0.5×0.5 and all-half-cell layouts. The lid leaf intentionally has no independent gate; the bin gate owns these predicates. `uv run ruff check .` and `uv run ty check .` pass; independent review reports no findings.
- Historical finished-lid evidence (before this support revision): default and 9 mm clean lids seated on z=0; overall heights 6.5/9 mm, socket depth 2.5 mm, skirt 3 mm. Seated skirt/body and matching upper feet had zero collision in default 1×2, shifted 1.5×1.5 and organized 1×1; 0.3 mm foot over-travel hit the floor. Oversized skirt mutation failed all three fit checks. Clean lid had no sharp/unclassifiable convex edges. These fit gates remain unchanged; old nib/lattice volume and old support checks are not evidence for the new support.
- [x] Full bin gate passed for default 1×2, shifted 1.5×1.5, 1×1, minimum half-cell, all-half-cell and taller 9 mm lid: two connected bed-seated prints, full socket depth, planar bed-adhesion faces and clean-lid equivalence at 0.01 mm³ Boolean tolerance. Bed area is not measured common glue-contact area.
- [x] Integration create/export smoke produced two valid connected bed-seated children and both independent STLs for all seven confirmed stackable leaves; three bin parameter variations also remained valid and connected. Independent review passed with the bed-area wording nit now corrected.
- Shared split-gate red proof on bin specimens: socket-down lips fail equivalence with 94.108221 mm³ missing material; body raised 0.3 mm fails pose/bed, equivalence and connectivity; body lowered 0.3 mm fails direct overlap with 223.432254 mm³ intersecting material. Positive full bin gate, ruff and ty passed.

## Historical visual review

- Historical views: `exports/drill_storage.bin.lid.html` (shaded interactive GLB), `exports/drill_storage.bin.lid_bottom.png` (socket-side hidden-line render) and the former single `exports/drill_storage.bin.lid.stl`. These were opened/rendered for the superseded revision; their paths are not evidence of current regenerated geometry or current child-STL output.
- Human review: cutting/peeling access, short-side/corner backing, full/half-cell sockets, and unchanged roof/rim/skirt.
- Offline slicing: OrcaSlicer reports success with no warnings. Inspected last support layer Z=2.4, isolated tabs at Z=2.6, and complete first roof bridges at Z=2.8. Print pose was preserved; no G-code was sent to a printer.
- Split integration browser proof: actual Chromium live-generation and repeated cache-hit child-STL downloads passed. The historical one-piece slice above does not establish split-print toolpaths or adhesive strength; a split-print slicer/physical trial remains pending.

## Acceptance gate

- Current purpose/decision signal: on 2026-10-23 the user retained the accepted bin lid as anchor and approved two-part-only printing with keyed location, light self-retention and glue relief, then required self-supporting underside joint geometry without unsupported precision mating cantilevers in both supplied poses.
- Historical support slices and shallow-rebate CAD/export results are not verification of the revised joint.
- Physical acceptance: pending dry-fit location/retention, joint seating and relief, adhesive compatibility/cured strength, matching-foot fit and loaded-stack trials.
- The old support-anchor rollout gate is historical, not a requirement to retain a one-piece mode. No body/foot/snap redesign is authorized.

## Historical planar split edge survey

Integration `sharp_convex_edges` audit; counts are body / lips.

| Leaf | Raw sharp | Allowed planar bed/interface boundary | Retained original sharp | Unclassifiable |
| --- | --- | --- | --- | --- |
| bin lid | 8 / 24 | 8 / 24 | 0 / 0 | 0 / 0 |

Allowed boundaries were selected by exact edge identity from planar bed
faces, not a positional blanket. They intentionally remain square for the
approved planar split; all other exposed convex edges are treated. This
classification is not a measurement of common bonded area or proof of
adhesive strength. No geometry edge retuning was made.
