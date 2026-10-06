# Wrench lid CAD contract

## References

- Context and purpose: [family README](../README.md).
- Accepted intent: [wrench-storage specification](wrench-storage-specification.md), WS-01–09.
- Accepted owner: [bin contract](bin-cad-contract.md). On 2026-10-03 the user selected **“Accept the 1×5 bin”** and approved proceeding with its matching removable stackable lid.
- Photo/measurement limits: [evidence](evidence.md).
- Manufacturing baseline: [removable FDM support design](../../../docs/fdm-support-design.md).

## Current slice

- **Anchor:** The separate PETG lift-off lid for the accepted compact 1×5 bin; preserve the bin geometry.
- **Purpose:** Enclose all six upright wrenches and receive matching Gridfinity feet for stacking, while retaining the compact footprint and unobstructed tool retrieval when removed.
- **In scope:** Locating skirt, flat rim seating, tool/rack clearance, lower-foot stacking sockets, minimal whole-7-mm stack pitch, one-piece print pose, removable socket supports, and a closed inspection scene. Reuse the existing stepped-layout parameter rather than changing the default.
- **Out of scope:** Snaps, magnets, labels, seals, fasteners, glue assembly, tool changes, and any claim of calibrated physical fit or stack load capacity.

## Technical sizing and service constraints

| Definition | Source / consequence |
| --- | --- |
| Default grouping / footprint | Six tools in the user-accepted 1×5 bin; exported lid footprint 41.5×209.5 mm. Optional grouping stays optional. |
| Cover envelope | At least the recorded 3 mm above the full photo-qualified tool/rack envelope. |
| Body / roof | 1 mm PETG baseline; preserve actual minimum sections rather than only nominal constants. |
| Closure | Unretained lift-off locating skirt, `fits.SLIDING` PETG baseline: 0.22 mm total XY clearance, 0.11 mm per side. Flat-on-flat rim landing and entering lead-in; not friction retention or a seal. |
| Skirt | 1.2 mm straight wall, 3 mm locating engagement; provide printable transitions to the 1 mm body without a floating skirt or unsupported wide ledge. The unchanged bin rim remains at 14 mm. |
| Rack passages | The accepted racks reach the bin's outside footprint and rise above its rim. Local open-bottom lid/skirt passages use 0.11 mm allowance per side and reach at most use-pose `z=21.099 mm`. Each cap retreats 1.91 mm per X side and 0.2 mm per Y side; its endpoint is the higher of clear rack top plus 1.91 mm and shoulder finish plus 0.2 mm (minimum `z=15.51 mm`). Low-column caps therefore retreat into the actual body cavity rather than ending in the 1.31 mm shoulder transition. Default 6/3 caps are unchanged. The merged common-end passage is 32.62 mm wide at use-pose `y=[−19.75, −18.33] mm` below the shoulder. Keep the bin and outside footprint unchanged; retain flat seating and the 1.2 mm skirt/3 mm engagement elsewhere. Withdraw the loaded lid straight upward, not tilted sideways across the racks/tools. |
| Stacking | Receive the foot's 0.7 mm lower bevel and 1.8 mm straight band, 2.5 mm total. The upper 1.9 mm bevel stays above the receiver; this avoids copying the older experimental 0.14 mm full-foot lip. |
| Stack datum | Receiver floor is the smallest whole multiple of 7 mm at or above `max(tool_top, rack_top) + 3 mm headroom + 1 mm roof`. Default export measurements give floor 49 mm, interior ceiling 48 mm and socket mouth 51.5 mm in canonical use coordinates, relative to the bin's print-bed datum `z=0`. The interior bin floor is at `z=5.4 mm`; these are not distances above that floor. A successful export does not establish the physical-gate predicates below. |
| Print pose | Socket mouths on the bed, cover mouth/skirt upward; transform separately for closed use pose. Default exported print height is 40.5 mm. |
| Socket support | Reuse `models.lib.gridfinity_socket.socket_tool(cell_w, cell_d, depth)` and `socket_support(cell_w, cell_d, depth)` in origin-centred socket-down print coordinates, at 2.5 mm depth. Preserve the shared lower-foot tool and bed-seated edge-rail/lattice process baseline unchanged. Keep roof process gap and only the declared small roof tabs; no accidental side welds. |
| Process limits | Nominal PETG / 0.4 mm extrusion / 0.2 mm layer baseline. Effective sliced roof gap, neck survival, roof sag and physical removal require printer-profile and printed-coupon calibration; CAD alone cannot establish them. |
| Cleaning / use | Print bin and lid separately without glue assembly. Remove every sacrificial socket support and residual attachment nib without damaging the receiver roof or locating surfaces before stacking. No removable supports belong in closed use state. |

These definitions implement WS-07 within the WS-08 gate now satisfied by the
accepted bin. They do not revise the durable WS-01–09 intent or authorize a bin
geometry change. Real-tool fit, roof sag, removal force and load rating are not
established by either the photo or this sizing table.

## Public interfaces and inspection scene

- `wrench_storage` and `wrench_storage.base` remain the same printable bin.
  The open `wrench_storage.preview` contract is unchanged.
- `lid.create(wrenches_per_column=6, support=True) -> Part` returns the one-piece
  lid in socket-down print pose. `support=False` removes only sacrificial
  receiver material and preserves that pose and finished geometry.
- `lid.seated(wrenches_per_column=6) -> Part` returns the cleaned canonical use
  pose, with no sacrificial supports. It owns the print-to-use transform.
- `lid.PARAMS` includes the shared grouping control and a print-only Boolean
  `support`; `lid.IS_ASSEMBLY = False`. `lid.check() -> Report` owns the
  centralized physical gate for this slice.
- `closed.create(wrenches_per_column=6) -> Compound` consumes
  `preview.create(...)` unchanged and adds exactly one `lid.seated(...)`.
  Bin/tool XY/Z, child labels and tool colours are preserved; only the lid is
  translucent for review. `closed.IS_ASSEMBLY = True` and
  `closed.PARAMS = config.PARAMS`: there is no support control in cleaned use
  state. This is not a slicer layout or a measured-tool replica.
- Use the same grouping value for both printable parts. Default grouping is the
  accepted compact 1×5; stepped regrouping is optional, not a workaround or a
  prerequisite for the default.

## Scoped slicing instructions and evidence

Integration slicing used **OrcaSlicer 2.4.2**, the user's **Centauri Carbon
0.4 mm**, **Jayo PETG** and **0.20 mm standard** profiles. Only inheritance was
flattened for the slice; the original profiles were not changed. Layer phasing
matters because these modelled supports are ordinary geometry, not
slicer-generated supports whose gap can be changed with a support setting.

| First layer / later layers | Last lattice layer Z | Support-core gap layers Z | First roof bridge layer Z | Effective roof separation |
| --- | --- | --- | --- | --- |
| Standard 0.20 / 0.20 mm | 2.20 mm | 2.40 and 2.60 mm | 2.80 mm | 0.40 mm, despite the nominal 0.20 mm CAD process gap |
| Lid-only 0.21 / 0.20 mm | 2.21 mm | 2.41 mm | 2.61 mm | 0.20 mm |

For this scoped 0.4 mm setup, use **0.21 mm first layer on the lid only**, then
**0.20 mm layers**; retain the bin's own print settings. The phase-adjusted slice
has both intentional attachment necks surviving in **every one of the five
cells** (10 total); the gap core contains only their extrusion paths and beads.
The standard slice also retains 10 weak necks but leaves two gap layers.
The bounded deposition audit covers the **entire lattice/edge-rail core**,
not an unmeasured assurance about every region of the whole footprint.

The regenerated explicit-corner STL slice estimates **40.15 g / 1 h 20 min 58 s**.
The hash-bound numerical record is
[`exports/wrench_analysis/lid-sliced-gap-proof.json`](../../../exports/wrench_analysis/lid-sliced-gap-proof.json);
[`lid-sliced-gap.svg`](../../../exports/wrench_analysis/lid-sliced-gap.svg) shows
actual deposition at Z=2.21, 2.41 and 2.61 mm and was visually inspected.
All core toolpaths at Z=2.41 lie within the nominal tab regions; bead envelopes
use the actual dynamic extrusion widths. Each cell has about 0.000429 mm² of
bead area beyond its nominal tab rectangles, not a second support lattice.
No arbitrary XY allowance was introduced. This
phase-adjusted first layer is a recommendation for the cited slice, **not a
universal or calibrated printer default**. Neck survival and measured sliced
separation do not establish real support release, roof sag, printed mating fit
or stack load capacity; those still require physical coupons and the lid.

## Verifiable predicates

- [ ] One valid connected clean lid and supported print; both start at z=0.
- [ ] The seated lid lands flat on the actual bin rim with the intended locating gap and no bin/rack collision.
- [ ] Every photo-qualified tool clears the closed lid, including corners, with at least the required cover envelope.
- [ ] Real Gridfinity feet enter every cleared receiver without collision, bear on an intact roof, and stack at a whole-7-mm datum.
- [ ] Roof and receiver walls retain printable sections; no absent stepped cells are filled.
- [ ] Support-off preserves finished geometry; support-on adds only removable receiver material.
- [ ] Supports reach the bed, retain their roof/XY release gaps away from named tabs, have accessible attachment necks, and cover socket edges as well as centres.
- [ ] Every actual rack-cutter terminal face opens into the finished cavity, including the low solo-6/7 column; a restored old short cap fails that same physical overlap predicate.
- [ ] Relevant intentionally broken roof, support, loaded-removal and short-cap specimens fail the same physical predicates.
- [ ] Actual STL exports, closed view, socket/roof section and support-removal view are inspected.

## Proof and visual evidence

The unchecked predicates above remain the lid's physical integration gate.
Runtime export/view succeeded and the scoped slicing results above were recorded
by integration, but neither substitutes for the physical gate.
`uv run check wrench_storage.lid` failed in the independent section/corner
reference proof. Preserve that failure; no unchecked predicate is marked passed.

On 2026-10-04 the user selected **“Rework corner construction”**: replace only
the rack/end-passage corner fillets with explicit rounded cutter geometry,
retaining the same nominal 0.2 mm rounding and fit/stacking envelopes. The
six-wrench storage purpose and WS-01–09 requirements are unchanged; the accepted
bin remains frozen. This is a new construction slice, not another relaxation of
the failed reference proof. Corner allowances must come from declared cutter
geometry applied to independently built stock, never from the tested lid or an
unvalidated before/after fillet subtraction. Preserve full roof/wall/cavity,
support-release, loaded-removal, grouping and negative-control gates.

The explicit cutter uses a radius-sized corner square minus its tangent circle
over the complete original upright edge. Each end contracts to an independently
classified air apex over 0.4 mm Z travel; apex offsets are 0.2 mm in X/Y.
Tools stay within original XY ±0.2 mm and endpoint Z ±0.4 mm. Their untrimmed
volume is independently checked against `(1 − π/4) r² (edge_length + 4r/3)`;
stock-clipped losses define only the declared corner allowance. Concave or
ambiguous designated corners fail explicitly rather than being omitted.
Required and forbidden stock use additive, precision-qualified per-solid
volume at the unchanged tolerance. Complete sections/roof/receivers/caps for
groupings 6/3/5 and restored-corner/old-short-cap controls passed focused runtime;
the full CLI physical gate is still required.

Confirm zero-argument parts/scenes and print-only Boolean metadata through the
normal registry/dependency tests; exercise clean and supported consumer parts
for every grouping 1–6 without changing the accepted bin. Full physical gates
cover default 6, stepped 3 and low solo-column 5; the remaining groupings also
receive actual complete-roof and absent-cell smoke.

Integration has generated the printable lid and closed review view. Record the
actual export/view paths and inspected socket/roof sections and support-removal
view here together with the completed physical gate. The section evidence must
expose the floor/ceiling datum, actual roof and receiver-wall sections, flat rim
landing, locating gap and support release paths; a transparent closed preview
alone does not prove those hidden details. Final section/SVG inspection and the
completed physical-gate outcomes are not yet recorded here.

## Acceptance gate

- **Current evidence:** The bin's CAD evidence and explicit acceptance are recorded in its contract. Earlier lid runtime export/view passed; default dimensions and bounded Orca deposition evidence are recorded above. The previous fillet-based corner proof failed and its fifth repair ended blocked. The user has now approved explicit rounded cutter construction; implementation and complete physical verification are pending. No previous predicate is promoted to passed, and existing exports remain inspection artifacts until rebuilt and verified.
- **Human review:** Present the actual closed 1×5 model and printable lid with the bin unchanged. Ask for feedback on the lid, not another approval of the already accepted bin.
- **Limits:** Printed tool fit, printer-specific support removal/sag and stack load capacity remain unverified unless separately demonstrated.
- **Dependent work:** None is authorized beyond this bin-and-lid deliverable.
