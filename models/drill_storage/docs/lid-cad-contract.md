# Empty bin — optional separate stacking lips

## References

- Context: `../README.md` and the [accepted body slice](empty-bin-cad-contract.md).
- Specification: [empty-bin-specification.md](empty-bin-specification.md), EB-2–EB-5, EB-7 and EB-8; common split-print requirements [SC-4](stackable-cover-specification.md).
- Supporting evidence: `models.lib.gridfinity` foot profile and `drill_storage.box` stackable socket; `models.lib.fits.SLIDING` PETG diametral; accepted body wall/rim; [support design procedure](../../../docs/fdm-support-design.md) and [removable-support research](../../../docs/research-removable-fdm-supports.md).

## Current slice

- Name: optional support-free split-print bin lid.
- Anchor part: the accepted finished `drill_storage.bin.lid` for `drill_storage.bin.base`.
Purpose and print pose: preserve the snap-in closure and receivers; default socket-down/skirt-up print retains optional default-on support, while split mode prints roof-down body and glue-face-down/socket-up lips.
- In scope: optional planar socket-floor split, named two-child contract and print poses, all full/half-cell layouts and taller roofs, glue instructions and physical invariants.
Deferred interfaces: no gasket, fastener, locating pin or adhesive-gap allowance. The snap lock is now implemented (EB-9). Historical EB-7 support revision is unchanged; its physical acceptance and family rollout remain pending.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| EB-2 | Lid footprint and receiving sockets align with every full/half foot of the matching base, without exceeding the 0.5 mm grid gap. |
| EB-3 | Independently printable lift-off lid; default minimum is 2.5 mm socket + 1 mm solid ceiling + 3 mm locating skirt = 6.5 mm total. A configurable height grows the plate/roof while keeping skirt engagement at 3 mm, so optional bin fixtures cannot be fouled. |
| EB-4 | A 1 mm body wall remains viable: derive skirt width from the body cavity and a PETG sliding fit; keep a flat rim bearing on the accepted body's 0.6 mm landing. |
| EB-5 | Expose a Boolean lid support option enabled by default; leaving it off yields a clean one-piece lid. Match the other drill holders' black base/translucent PETG cover appearance in leaf exports and the scene. |
| EB-7 | Connect the existing central lattice to a gapped rounded perimeter rail following the narrowest roof/socket contour; replace four welded nibs with two accessible smaller tabs. Slicer and physical acceptance, not CAD topology, decide removal and sag success. |
| EB-8 | Split at the 2.5 mm socket-floor plane; complete roof/skirt belongs to `lid_body`, all connected receiver walls/webs to one `stacking_lips` child/STL, with unchanged ideal assembled geometry. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Foot socket depth | 2.5 mm (0.7 lower bevel + 1.8 straight) | `drill_storage.box.STACK_SOCKET_DEPTH` |
| Socket XY clearance | `fits.SLIDING`, 0.22 mm diametral | PETG sliding-fit class; calibration required |
| Lid roof above socket | 1 mm minimum | `drill_storage.box.CAP_H`, five layers at 0.2 mm |
| Plug engagement | 3 mm minimum | Three times 1 mm rim budget; lift-off locating skirt |
| Outer shell | grid span minus 0.5 mm | Existing accepted bin body |
| Fixture clearance | 3.6 mm below body rim | 3 mm skirt plus 0.6 mm service gap; accepted body's optional fixture headroom refined during lid integration |
| Existing support body | 0.8 mm ribs, 5 mm centre pitch | Existing bin source; retained to isolate attachment/edge-coverage changes |
| Nominal roof process gap | 0.2 mm retained trial candidate | Baseline and candidate slices: OrcaSlicer 2.4.2, Centauri Carbon 0.4 mm / Generic PETG, uniform 0.2 mm first/normal layers, generated supports and brim off. Lattice ends at Z=2.4 mm; Z=2.6 mm contains only attachments inside the sockets; full roof Bridge starts at Z=2.8 mm with HEIGHT=0.2. One empty layer remains away from tabs on this profile; other layer schedules require rechecking |
| Perimeter process separation | 0.6 mm each side, rail 0.8 mm thick | Proposed positive XY manufacturing gap, not a mating-fit allowance; offset the narrowest socket/roof contour including its corner radius |
| New tab necks | Two 0.4 × 0.8 mm sections per cell, measured 0.64 mm² total; gap height plus 0.02 mm roof overlap | Gate measured both necks; candidate slice preserves two attachment locations per socket at Z=2.6. Old four 0.6 × 0.6 mm nibs totalled 1.44 mm². Printed fracture/removal remains unproven |
| Default full-cell roof/old lattice span | 36.52 / 30.8 mm; revised rail outer span 35.32 mm | Baseline straight-edge band 2.86 mm; revised nominal band 0.6 mm, extending backing 2.26 mm beyond each old edge. Gate probes straight edges and all rounded corners |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Effective Z/XY gaps, tab extrusion and first roof toolpaths on other profiles | Current recorded 0.4 mm nozzle / 0.2 mm-layer PETG slice passes visual path inspection; repeat for a different profile | One profile's sliced result does not establish general printability or physical release |
| Release effort, short-side sag, residual nibs, roof damage and actual foot fit | Representative socket coupon, then full bin lid, on the target PETG printer | Physical support revision acceptance and family rollout remain blocked until trial results are accepted |

## Service and assembly constraints

1. With supports enabled, reach through each open socket to cut the two weak tabs at the straight perimeter rail midpoints, then peel the connected rail/lattice inward. Do not pry against the finished rim or skirt. Trim any roof-side tab remnants without changing the foot seat; confirm full-depth mating-foot seating before stacking. Tabs survive the recorded slice; cutting access and removal effort await physical trials. With supports disabled, use slicer support or verify the approximately 37 mm socket bridge on the target printer.
2. The skirt locates and locks: the bead on the skirt detents into the bin's groove. Pull the lid to unsnap and access the bin.
3. Closed display scene is not a slicer part; base and lid each have a separate print-pose model.

## Required skills

`model-documentation`, `cad-iteration`, `box-closures`, `fdm-fits-and-clearances`, `build123d-geometry-ops`.

## Verifiable predicates

- [x] Revised support-on lid is one valid connected solid on z=0 within OCC tolerance; each full/half-cell rail/lattice body is a single bed-seated component, retained by exactly two measured 0.32 mm² necks.
- [x] Support material backs previously empty straight-edge bands and all rounded corners. The old lattice fails both sockets' coverage predicates; full-cell backing extends 2.26 mm beyond the old lattice envelope.
- [x] Geometry has positive wall separation (gate measured minimum 0.650 mm below the ceiling) and a nominal 0.2 mm roof gap away from tabs. A deliberately gap-filling third attachment fails gap, neck-count/section and location predicates; the old four-nib geometry fails neck predicates. Candidate slicing preserves one empty layer away from two surviving tabs.
- [x] Support-on contains all clean geometry and adds material only in the sockets. Bidirectional Boolean comparison against the captured baseline support-off lid has zero added and removed volume; roof, closure and fit geometry are preserved.
- [x] `uv run check drill_storage.bin` passes default 1×2, shifted 1.5×1.5, organized 1×1, minimum 0.5×0.5 and all-half-cell layouts. The lid leaf intentionally has no independent gate; the bin gate owns these predicates. `uv run ruff check .` and `uv run ty check .` pass; independent review reports no findings.
- Historical finished-lid evidence (before this support revision): default and 9 mm clean lids seated on z=0; overall heights 6.5/9 mm, socket depth 2.5 mm, skirt 3 mm. Seated skirt/body and matching upper feet had zero collision in default 1×2, shifted 1.5×1.5 and organized 1×1; 0.3 mm foot over-travel hit the floor. Oversized skirt mutation failed all three fit checks. Clean lid had no sharp/unclassifiable convex edges. These fit gates remain unchanged; old nib/lattice volume and old support checks are not evidence for the new support.
- [x] Full bin gate passed for default 1×2, shifted 1.5×1.5, 1×1, minimum half-cell, all-half-cell and taller 9 mm lid: two connected bed-seated prints, full socket depth, planar bed-adhesion faces and clean-lid equivalence at 0.01 mm³ Boolean tolerance. Bed area is not measured common glue-contact area.
- [x] Integration create/export smoke produced two valid connected bed-seated children and both independent STLs for all seven confirmed stackable leaves; three bin parameter variations also remained valid and connected. Independent review passed with the bed-area wording nit now corrected.
- Shared split-gate red proof on bin specimens: socket-down lips fail equivalence with 94.108221 mm³ missing material; body raised 0.3 mm fails pose/bed, equivalence and connectivity; body lowered 0.3 mm fails direct overlap with 223.432254 mm³ intersecting material. Positive full bin gate, ruff and ty passed.

## Visual review

- Current views: regenerated `exports/drill_storage.bin.lid.html` (shaded interactive GLB) and `exports/drill_storage.bin.lid_bottom.png` (socket-side hidden-line render); STL is `exports/drill_storage.bin.lid.stl`. Viewer rendered without browser errors and was opened on the user's machine. The clean lid's zero Boolean difference establishes the unchanged seated silhouette.
- Human review: cutting/peeling access, short-side/corner backing, full/half-cell sockets, and unchanged roof/rim/skirt.
- Offline slicing: OrcaSlicer reports success with no warnings. Inspected last support layer Z=2.4, isolated tabs at Z=2.6, and complete first roof bridges at Z=2.8. Print pose was preserved; no G-code was sent to a printer.
- Split integration browser proof: actual Chromium live-generation and repeated cache-hit child-STL downloads passed. The historical one-piece slice above does not establish split-print toolpaths or adhesive strength; a split-print slicer/physical trial remains pending.

## Acceptance gate

- Purpose/decision signal: user explicitly confirmed the bin lid still closes the bin and receives Gridfinity feet, and approved the support-only revision on 2026-09-30.
- Acceptance signal: CAD, independent review, recorded-profile slicing and visual/export proof complete; physical trial pending. Record coupon/full-lid removal, roof sag/damage and mating-foot fit before accepting this anchor. No claim that removal difficulty or sag is physically fixed is justified yet.
- Split purpose/decision signal: user confirmed the optional separate-lips delta for this accepted lid on 2026-09-30. Ideal CAD fit remains unchanged; actual adhesive strength, flatness, alignment and bond-line height require physical print/glue acceptance. Glue edges stay square for full flat contact. See the [family print/glue instructions](../README.md#separate-printable-stacking-lips).
- Family rollout: closed until the user physically accepts this named bin-lid support anchor; this approval does not change shared `box.py` supports or other models.

## Split print edge survey

Integration `sharp_convex_edges` audit; counts are body / lips.

| Leaf | Raw sharp | Allowed planar bed/interface boundary | Retained original sharp | Unclassifiable |
| --- | --- | --- | --- | --- |
| bin lid | 8 / 24 | 8 / 24 | 0 / 0 | 0 / 0 |

Allowed boundaries were selected by exact edge identity from planar bed
faces, not a positional blanket. They intentionally remain square for the
approved planar split; all other exposed convex edges are treated. This
classification is not a measurement of common bonded area or proof of
adhesive strength. No geometry edge retuning was made.
