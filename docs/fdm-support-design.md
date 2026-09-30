# Removable FDM support design

Read this before designing built-in breakaway supports, changing a support interface, or investigating supported-roof sagging. Default material is PETG; use the actual nozzle, extrusion width, layer schedule and slicer profile for calibration. This procedure covers modelled same-material supports, not permanent structural ribs.

Source evidence and the drill-storage print feedback are recorded in [removable-support research](research-removable-fdm-supports.md). Printer-specific results outrank proposed dimensions. `fdm-fits-and-clearances` remains the authority for mating fits; support release gaps are manufacturing clearances, not diametral fits.

## 1. Separate roof support from attachment

Record print pose, first roof-layer height, roof outline, bridge direction, removal opening, and the functional surfaces that must survive removal. Distinguish:

- **Support body:** stable on the bed and stiff enough to carry the roof.
- **Release interface:** a real air gap below the roof, with enough contact coverage to limit sag.
- **Retention tabs:** optional intentional welds that keep the support attached to the exported part. Their weakest neck controls removal, not the support body's rib thickness.

Inspect every support-to-part contact, including wall intersections and first-layer brim paths. A ceiling gap does not make a support removable if welded tabs or side contacts bypass it. A single CAD solid is not proof of good support design; separate bed-seated support shells are valid when the export and slicer preserve them.

Completion: identify all intentional attachments and every possible accidental fusion path. Load `model-documentation` and obtain its purpose/decision confirmation before changing public geometry or contracts.

## 2. Budget the actual sliced release interface

Specify vertical separation as a named **support process gap**, with material and intended layer schedule in its comment. Inspect the last support extrusion and first roof extrusion in the sliced toolpath: nominal CAD distance is not necessarily the printed distance, particularly with adaptive layers or a roof height between layer planes.

For difficult removal, reduce deliberate bonded area or weaken accessible tab necks before thinning the entire support body. Calibrate a larger vertical gap separately: increasing it can improve release but worsen roof sag. Keep XY clearance from the socket walls throughout their changing section, with enough margin for extrusion width and first-layer expansion.

Prefer accessible sacrificial tabs on a substantial, non-functional area. Keep them away from thin lips, snap features and critical seating surfaces; provide a tool approach and a peeling path that does not lever against the finished rim. If no safe attachment exists, use disconnected bed-seated supports or slicer supports rather than welding a support to a fragile wall. Record any unavoidable residual nib and how it is removed without altering the fit.

Completion: sliced roof gap remains open outside the declared tabs; all tabs survive slicing, and their necks and removal access are explicit. Sub-line-width CAD necks that disappear in the slicer are not a solution.

## 3. Cover the roof edges as well as its centre

Derive the support field from the roof/socket contour at the relevant height, including half cells, corners and each socket in a multi-cell lid. A centred grid rounded down to a fixed pitch leaves a perimeter strip that can be wider than its interior openings suggest.

Measure the largest unsupported distance along the **actual first roof toolpaths**, including:

- spacing between ribs;
- each rib end to the roof boundary;
- short-side strips and rounded corners;
- spans created by the selected bridge direction.

Add removable edge-following rails or cross-ribs under the failing short-side bands, retaining the calibrated XY and Z gaps. Bring useful support coverage toward the edges rather than simply adding more ribs in the centre. Tune near-roof contact spacing independently from lower support density when a sparse body cannot produce an acceptable ceiling. A dense, continuously bonded roof interface increases removal effort; additional coverage should retain its release gap.

Completion: every roof region has a measured unsupported span within a printer-proven bridge budget. Inspect both principal directions; a small axis-aligned cell opening alone is insufficient evidence.

## 4. Verify geometry, slicing and physical removal separately

**CAD gate:** compare support-on and support-off variants; disabling support must leave the finished part unchanged. Check print pose, stable support islands, air gaps away from tabs, intended necks, absence of side-wall contact, and coverage in the reported failing region. Include full/half cells and multi-socket variants where supported. Demonstrate relevant predicates reject an intentionally bad gap, tab or missing edge rail.

**Slicer gate:** examine the last support layer and first roof layers using the intended profile. Confirm extrusion survives on narrow necks, effective Z/XY separation, bridge direction and anchoring, perimeter coverage, bed stability, and removal access. Modelled supports are sliced as ordinary model geometry: changing slicer support-gap settings does not rewrite their CAD gap or welded tabs. Record slicer/profile/layer schedule with the result.

**Print gate:** use a small roof-and-support coupon reproducing socket depth, roof thickness, edge contour and peeling access. Change one variable at a time: release gap, tab neck/area, then edge coverage. Compare removal effort, tool required, roof sag, surface damage/residual nibs, and fit with the actual mating foot. Choose the loosest interface that still meets the roof and fit requirements, then validate the full lid before extending it across a family.

Completion: CAD evidence may justify an export, but support removal and sag remain **unverified physically** until a printed coupon and representative lid pass. Do not mark them accepted from volume, solid count, or a render alone.

## Failure-directed iteration

| Observation | Inspect first | Targeted change |
| --- | --- | --- |
| Support is hard to remove | Welded tabs, effective Z gap, side/brim fusion | Reduce accessible attachment neck/area; calibrate more separation only if roof quality permits |
| Roof sags near a short side | Edge band and first roof toolpath, not centre density | Extend gapped edge coverage or add edge cross-ribs |
| Support collapses or detaches during printing | Bed anchoring, body stiffness, neck paths | Stabilise the support body while retaining its weak release interface |
| Socket or lip is damaged during removal | Peel direction, tab location, tool clearance | Move attachment to a substantial non-functional area or use unconnected supports |

Keep reusable rules here, source evidence in the linked research note, and accepted model-specific dimensions/results in that model's contract. Do not promote coupon starting values into universal PETG defaults.
