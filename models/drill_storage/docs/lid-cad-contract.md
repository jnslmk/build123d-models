# Empty bin — current removable-lid slice

## References

- Context: `../README.md` and the [accepted body slice](empty-bin-cad-contract.md).
- Specification: [empty-bin-specification.md](empty-bin-specification.md), EB-2–EB-4.
- Supporting evidence: `drill_storage.box` foot profile and stackable socket; `models.lib.fits.SLIDING` PETG diametral; accepted body wall/rim.

## Current slice

- Name: removable stackable lid.
- Anchor part: `drill_storage.bin.lid` for the accepted `drill_storage.bin.base`.
- Purpose and print pose: lift-off cover locating within the body cavity, with Gridfinity-foot seats on its exposed top; print socket-down with skirt upward. Socket lattice is removable and optional (on by default).
- In scope: parametric X/Y including half-cell foot orientation, wall thickness, physical lid height in mm, support toggle, black body and translucent cover colors on print parts and the closed scene.
- Deferred interfaces: no snap lock, gasket, or fastener. Printed retention or sealing are not implied by a lift-off lid.

## Applicable specification constraints

| Requirement | Consequence |
| --- | --- |
| EB-2 | Lid footprint and receiving sockets align with every full/half foot of the matching base, without exceeding the 0.5 mm grid gap. |
| EB-3 | Independently printable lift-off lid; default minimum is 2.5 mm socket + 1 mm solid ceiling + 3 mm locating skirt = 6.5 mm total. A configurable height grows the plate/roof while keeping skirt engagement at 3 mm, so optional bin fixtures cannot be fouled. |
| EB-4 | A 1 mm body wall remains viable: derive skirt width from the body cavity and a PETG sliding fit; keep a flat rim bearing on the accepted body's 0.6 mm landing. |
| EB-5 | Expose a Boolean lid support option enabled by default; leaving it off yields a clean one-piece lid. Match the other drill holders' black base/translucent PETG cover appearance in leaf exports and the scene. |

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Foot socket depth | 2.5 mm (0.7 lower bevel + 1.8 straight) | `drill_storage.box.STACK_SOCKET_DEPTH` |
| Socket XY clearance | `fits.SLIDING`, 0.22 mm diametral | PETG sliding-fit class; calibration required |
| Lid roof above socket | 1 mm minimum | `drill_storage.box.CAP_H`, five layers at 0.2 mm |
| Plug engagement | 3 mm minimum | Three times 1 mm rim budget; lift-off locating skirt |
| Outer shell | grid span minus 0.5 mm | Existing accepted bin body |
| Fixture clearance | 3.6 mm below body rim | 3 mm skirt plus 0.6 mm service gap; accepted body's optional fixture headroom refined during lid integration |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Release effort, support removal, and actual foot fit | Printed coupon/calibration on PETG printer | Do not claim tested retention or exact printed tolerance |

## Service and assembly constraints

1. When supports are enabled, peel each sacrificial lattice from its seat before stacking; with supports disabled, use slicer support or verify the 37 mm socket ceiling bridge on the target printer.
2. The skirt locates but does not lock: lift lid by hand to access bin.
3. Closed display scene is not a slicer part; base and lid each have a separate print-pose model.

## Required skills

`model-documentation`, `cad-iteration`, `box-closures`, `fdm-fits-and-clearances`, `build123d-geometry-ops`.

## Verifiable predicates

- [x] Default and 9 mm lids are each one connected solid and seated on z=0 in print pose; the built-in 5 mm lattice is linked to the socket ceiling by four 0.6 mm nibs per cell and absent in the clean assembly scene.
- [x] Seated skirt and body are disjoint: zero collision volume in default 1×2, shifted half-grid 1.5×1.5, and organized 1×1 with dividers, labels and scoops. The face lands on the body rim; the plug slides within the cavity.
- [x] Actual matching upper bin foot clears every socket in those three cases (zero collision), while forcing it 0.3 mm deeper overlaps the socket floor by 77–218 mm³. Socket/support point probes find a removable lattice below a solid roof.
- [x] Lid overall print height measured 6.5 mm default and 9 mm enlarged. Socket depth remains 2.5 mm, skirt 3 mm; additional height goes into the roof.
- [x] Physical gate was shown to reject an intentionally oversized skirt (`PLUG_FIT = -0.5`): all three skirt/body interface checks failed. Finished lid without the sacrificial support has zero sharp or unclassifiable convex edges; the supported print has sacrificial lattice edges that leave with it.
- [x] Supported and unsupported lid variants each have one solid on z=0; `clean - supported` has zero volume and the optional lattices add 1443.14 mm³ in the default 1×2. Leaf part colors match the family's black and translucent PETG cover, and the closed scene visibly shows both. `uv run check drill_storage.bin` passes.

## Visual review

- Views: printable lid isometric and bottom/socket; seated bin scene isometric and interactive; accepted body available separately.
- Human review: thin 6.5 mm default lid, underside support removal, locating skirt, full/half-grid sockets, and uninterrupted outer silhouette.
- Artifacts: `exports/drill_storage.bin.lid.html`, `exports/drill_storage.bin.lid_iso.png`, `exports/drill_storage.bin.lid_bottom.png`, `exports/drill_storage.bin.html`, `exports/drill_storage.bin_iso.png`.

## Acceptance gate

- Human feedback requested on the finished lid after proof and views.
- Acceptance signal: pending; user approved the bin body and instructed implementing its dependent lid, not accepting this lid geometry.
