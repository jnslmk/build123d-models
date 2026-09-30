# Removable same-material FDM supports

**Accessed:** 2026-09-30  
**Scope:** source-backed design principles and proposed print experiments for PETG stackable drill-storage lids with modelled breakaway supports. This note does not change geometry or an accepted CAD contract.

## Bottom line

- **Separate support coverage from attachment strength.** A roof needs short, well-anchored extrusion spans, including its edges; that does not require welding the support to it. Same-material supports need a separation gap, whereas zero-gap advice for dedicated support filament does not apply to PETG-on-PETG. [P1] [B1]
- **Use sparse structure below a controlled top interface, not automatically a dense full-height grid.** Denser interfaces improve roof backing but trade away removability. Larger spacing improves release only until unsupported spans begin to sag. [P1] [O1]
- **There is no universal PETG gap, rib pitch or breakaway-neck size.** Gap, extrusion width, layer height, bridge flow, cooling, material and actual sliced paths must be considered together. Prusa explicitly identifies PETG's poor bridging and difficult support removal. [P2] [P3]

For the repository's actionable design/verification procedure, see [removable FDM support design](fdm-support-design.md). Existing fit/overhang guidance is not a substitute for checking the release interface and every roof-edge path.

## Current evidence: stackable drill-storage lid

**User-reported print failures:** the PETG supports are very hard to remove, and the roof sags near the unsupported short sides. These observations are ground truth; neither the cause nor a successful replacement has yet been proven by a controlled print comparison.

The bin lid's [`_support()`](../models/drill_storage/bin/lid.py) and the separate shared cover [`add_stacking_support()`](../models/drill_storage/box.py) both use the gap, pitch, rib and nib dimensions below, but their footprint calculations differ:

| Feature | Current construction | Consequence to investigate, not a proven sole cause |
|---|---|---|
| Vertical gap | **0.2 mm** below the socket ceiling | A CAD distance, not proof of one empty printed layer or easy release. |
| Lattice | **0.8 mm** ribs on **5 mm** pitch in both directions | **4.2 mm** clear openings; an intersecting grid rather than an independently tuned dense top interface. |
| Attachment | Four **0.6 × 0.6 mm** nibs per socket, spanning the gap and overlapping the roof by **0.02 mm** | Total nominal neck section **1.44 mm²**; these are intentional same-material welds, not gap-separated contact points. The small overlap is not the neck's fracture area. |
| Coverage | Default bin: **30.8 mm** lattice envelope. Shared covers: **30.8 mm** across outer rib widths, with **31.6 mm** rib lengths. | Both are centre-limited; the shared cover's longer rib-end envelope must not be mistaken for the bin footprint or continuous perimeter backing. |

These dimensions come from the model sources, not an online recommendation. Parent inspection of the **default bin lid** measured a **36.52 mm** straight ceiling width and **30.8 mm** lattice span: a **2.86 mm** unsupported band at each straight edge. Point probes confirm nib penetration into the roof and an empty short-side band below it. These measurements do not describe every shared-cover variant. Actual fusion across the nominal gap, nib fracture behaviour and sliced bridge direction remain unmeasured. The existing [`lid CAD contract`](../models/drill_storage/docs/lid-cad-contract.md) and accepted purpose take precedence; geometry changes require the model-documentation decision/confirmation step first.

## Source-backed principles

1. **Z clearance is a release/surface-quality trade-off.** Bambu documents easier removal but poorer interface quality with larger top Z distance, and warns against zero distance for the same interface/body filament. Its approximately **0.2 mm** suggestion is contextual, not a guarantee. Prusa separately says **50–75% of layer height** can work for its generated supports. These are not interchangeable universal CAD values: generated supports can use independent layer heights to follow the gap. [B1: “Top Z distance & Support/object XY distance”] [P1: “Top contact Z distance,” “Synchronize with object layers”]
2. **XY clearance matters independently.** Prusa states that increasing XY separation reduces support contact area and makes removal easier and fusion less likely. Moving all support inward also removes backing from roof edges, so lateral release clearance and supported footprint must be tuned separately. The latter is a design inference, not a prescribed perimeter offset. [P1: “XY separation between an object and its support”]
3. **Contact density and strength are separate knobs.** Bambu reports that closer tree nodes improve overhang quality but increase removal difficulty, and larger branches increase strength and removal difficulty. Orca likewise distinguishes tip diameter, branch density and a thicker base for stability. These support concentrating strength below smaller contacts; they do **not** establish a safe dimensions table for welded PETG nibs. A narrow, accessible sacrificial neck is a proposed CAD adaptation, requiring fracture/roof-damage testing. [B1: “Tree Support-Only Options”] [O2]
4. **Dense top backing is not the same as dense support everywhere.** Prusa recommends a denser interface over a more widely spaced base. It warns that excessive base spacing causes the interface's own bridges to sag. Orca documents that more interface layers give flatter support but can be harder to peel; zero interface spacing means a solid interface. Thus neither “always sparse” nor “always solid” answers both release and sagging. [P1: “Pattern spacing,” “Top interface layers”] [O1: “Interface layers,” “Interface spacing”]
5. **Trace the actual first roof paths, especially the perimeter.** Bambu explains that a bridge works because both extrusion ends are supported, while a cantilever supported at only one end needs support. Prusa recommends subdividing long bridges with support islands and calibrating bridge flow/speed. Orca allows automatic or overridden bridge direction; support-pattern rotation is a separate setting. A central lattice or a small average opening does not prove that every roof-edge path has backing. [B1: “Max bridge Length,” “Cantilevers”] [P3] [O3] [O1: “Pattern angle”]
6. **PETG needs material-specific calibration.** Prusa describes high tenacity and good layer adhesion alongside poor bridges and difficult support removal. Cooling improves detail and limits oozing, whereas higher temperature and less cooling favour layer bonding/strength. Tune bridge behaviour on representative coupons rather than globally weakening the functional lid to release its supports. [P2: “Description,” “Temperature settings and cooling”] [P3]

## Proposed experiments, not accepted geometry or universal settings

Use a **representative single-socket roof coupon retaining the roof edge, socket wall, print pose and removal access** after the purpose/design decision is confirmed. Keep filament, nozzle, layer heights, temperatures, fan, speeds and flow fixed initially; record them. Keep an unchanged reference from the reported print; do not require another failed full-lid print merely to confirm the complaint.

| Experiment | Controlled comparison | Observation that decides the next change |
|---|---|---|
| Welds versus gap | Compare the four current fused nibs with gap-only backing. Where a connected export is an accepted requirement, separately compare accessible reduced necks sized against the actual extrusion width. | Where separation occurs, tool access, release effort, retained nibs and roof tearing. Gap-only or single-bead necks are hypotheses, not proven replacements. |
| Vertical release | Start from **0.2 mm**; compare the next one and two **slicer-realizable** larger gaps. For uniform **0.2 mm** layers, **0.4/0.6 mm** are possible coupon candidates, not recommendations. | Confirm different effective gaps in sliced layers; reject easier release if roof sag or socket interference worsens. Do this without welded nibs dominating the comparison. |
| Edge coverage and XY gap | Hold top gap, rib pitch and attachment strategy constant; extend backing beneath the failed short-side roof regions while retaining clearance from socket walls. Compare two positive side clearances that remain distinct in the actual sliced paths. | First roof perimeter and infill path anchoring, short-side sag and unintended side fusion. A smaller wall clearance is not automatically better. |
| Sparse versus denser top | Compare current **5 mm** pitch/**0.8 mm** ribs with, for example, **3 mm** pitch at the top only, over the same sparse body, gap and footprint. Also inspect a slicer-generated interface reference using the existing support-off option. | Roof flatness versus contact scars, peeling effort and support fragmentation. The **3 mm** pitch is only a proposed experimental starting value. |
| Bridge direction | Inspect the first roof layer, then compare directions that cross the ribs and keep the failed edge paths short and anchored. Change direction separately from support density. | Actual unsupported path lengths and edge quality; rotating the object may not rotate bridge fill when absolute direction settings apply. [O3] |

Before printing a candidate, inspect **actual layer paths**: thin necks may vanish or become wider toolpaths, fused CAD contacts remain model material, and ordinary support settings do not automatically impose a release gap on modelled ribs. This is a workflow inference from the distinction between supplied model geometry and generated supports, not a slicer setting guarantee.

Record removal method/time (and force if measured), roof damage and residual support, maximum short-side sag, and whether the cleaned socket accepts its mating foot to full depth. A successful coupon must improve removal **and** preserve roof/socket function; verify the selected result on the full lid before claiming the design fixed. No such candidate print has been performed for this research note.

## Sources

All originals below were accessed 2026-09-30. Prusa and Bambu pages required browser rendering to read the article bodies; search snippets were not used as final evidence. Slicer documentation describes generated supports; adaptations to modelled support geometry are explicitly identified above.

- **[P1] Prusa — “Support material.”** Official Knowledge Base. <https://help.prusa3d.com/article/support-material_1698>
- **[P2] Prusa — “PETG.”** Official material guide. <https://help.prusa3d.com/article/petg_2059>
- **[P3] Prusa — “Poor bridging.”** Official print-quality guidance. <https://help.prusa3d.com/article/poor-bridging_1802>
- **[B1] Bambu Lab — “Support.”** Official Bambu Studio wiki. <https://wiki.bambulab.com/en/software/bambu-studio/support>
- **[O1] OrcaSlicer — “Support Advanced.”** Project-maintained official GitHub wiki. <https://github.com/OrcaSlicer/OrcaSlicer/wiki/support_settings_advanced>
- **[O2] OrcaSlicer — “Tree Support.”** Project-maintained official GitHub wiki. <https://github.com/OrcaSlicer/OrcaSlicer/wiki/support_settings_tree>
- **[O3] OrcaSlicer — “Strength Advanced,” bridge infill direction and model alignment.** Project-maintained official GitHub wiki. <https://github.com/OrcaSlicer/OrcaSlicer/wiki/strength_settings_advanced>
