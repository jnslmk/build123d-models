# Empty bin — current bin-lid support revision anchor

## References

- Context: `../README.md` and the [accepted body slice](empty-bin-cad-contract.md).
- Specification: [empty-bin-specification.md](empty-bin-specification.md), EB-2–EB-5 and EB-7.
- Supporting evidence: `drill_storage.box` foot profile and stackable socket; `models.lib.fits.SLIDING` PETG diametral; accepted body wall/rim; [support design procedure](../../../docs/fdm-support-design.md) and [removable-support research](../../../docs/research-removable-fdm-supports.md).

## Current slice

- Name: bin-lid sacrificial attachment and short-side backing revision.
- Anchor part: `drill_storage.bin.lid` for the accepted `drill_storage.bin.base`.
- Purpose and print pose: unchanged lift-off bin cover receiving Gridfinity feet; print socket-down with skirt upward. Sacrificial socket support remains optional and on by default.
- In scope: only sacrificial support geometry and its physical gate/removal instructions, including full/half-cell sockets. Finished lid, roof thickness, closure interfaces, fits, public parameters and clean assembly scene are unchanged.
- Deferred interfaces: no snap lock, gasket, fastener or other model changes. Family/shared-cover support rollout waits for physical acceptance of this bin-lid anchor.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| EB-2 | Lid footprint and receiving sockets align with every full/half foot of the matching base, without exceeding the 0.5 mm grid gap. |
| EB-3 | Independently printable lift-off lid; default minimum is 2.5 mm socket + 1 mm solid ceiling + 3 mm locating skirt = 6.5 mm total. A configurable height grows the plate/roof while keeping skirt engagement at 3 mm, so optional bin fixtures cannot be fouled. |
| EB-4 | A 1 mm body wall remains viable: derive skirt width from the body cavity and a PETG sliding fit; keep a flat rim bearing on the accepted body's 0.6 mm landing. |
| EB-5 | Expose a Boolean lid support option enabled by default; leaving it off yields a clean one-piece lid. Match the other drill holders' black base/translucent PETG cover appearance in leaf exports and the scene. |
| EB-7 | Connect the existing central lattice to a gapped rounded perimeter rail following the narrowest roof/socket contour; replace four welded nibs with two accessible smaller tabs. Slicer and physical acceptance, not CAD topology, decide removal and sag success. |

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
2. The skirt locates but does not lock: lift lid by hand to access bin.
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

## Visual review

- Current views: regenerated `exports/drill_storage.bin.lid.html` (shaded interactive GLB) and `exports/drill_storage.bin.lid_bottom.png` (socket-side hidden-line render); STL is `exports/drill_storage.bin.lid.stl`. Viewer rendered without browser errors and was opened on the user's machine. The clean lid's zero Boolean difference establishes the unchanged seated silhouette.
- Human review: cutting/peeling access, short-side/corner backing, full/half-cell sockets, and unchanged roof/rim/skirt.
- Offline slicing: OrcaSlicer reports success with no warnings. Inspected last support layer Z=2.4, isolated tabs at Z=2.6, and complete first roof bridges at Z=2.8. Print pose was preserved; no G-code was sent to a printer.

## Acceptance gate

- Purpose/decision signal: user explicitly confirmed the bin lid still closes the bin and receives Gridfinity feet, and approved the support-only revision on 2026-09-30.
- Acceptance signal: CAD, independent review, recorded-profile slicing and visual/export proof complete; physical trial pending. Record coupon/full-lid removal, roof sag/damage and mating-foot fit before accepting this anchor. No claim that removal difficulty or sag is physically fixed is justified yet.
- Family rollout: closed until the user physically accepts this named bin-lid support anchor; this approval does not change shared `box.py` supports or other models.
