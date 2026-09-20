# Stella analytical inputs

Evidence gathered 2026-09-20 for the [Stella specification](stella-specification.md)
and its current [CAD contract](cad-contract.md). This is source-backed input and
illustrative arithmetic, not accepted geometry, a load rating, or physical
validation. The agreed scope is estimates/CAD only.

## Existing hanging pose and separate frames

Primary repository sources: `../assemblies/stella_octangula.py` (`BASE_SIGNS`,
`OFFSET_SIGNS`, `tetra_vertices`, `_vertex_core_frame`, placement loops),
`../stella_config.py` and `../mount_config.py`.

- The current global pose has four upper vertices: two belonging to each
  tetrahedron. Each tetrahedron contains six lamps and its own four vertex cores.
- The six apparent crossings are deliberately separated. There is no structural
  connection between the two tetrahedra in the current model; a crossing must not
  be counted as a load-transfer joint.
- A single safety attached to one tetrahedron would not retain the other if its
  primary path failed. The accepted Round 4 architecture backs up a common
  **metal collector/master link** carrying both primary bridles. It backs up
  the upper connection, not every downstream leg, printed joint or lamp;
  detailed hardware and actual safety-arrest forces are not established.

### Headroom consequence of the 45-degree bridle limit

For the existing 1500 mm lamps, the documented gland setback is about 35 mm and
cap thickness is 15.85 mm. Thus the current mathematical edge length is about
`1500 + 2 × (35 + 15.85) = 1601.7 mm`, with half-cube coordinate
`u = 1601.7 / sqrt(8) = 566.29 mm`.

The base core reference centres remain at their mathematical vertices. Only the
**offset tetrahedron** receives the additional shift `EDGE_OFFSET / 3`, currently
`30.75 / 3 = 10.25 mm` per signed coordinate. The two upper pairs are not coplanar.

| Upper core reference pair | z above assembly origin | Horizontal reach from centreline |
| --- | ---: | ---: |
| Base tetrahedron | 566.29 mm | 800.85 mm |
| Offset tetrahedron | 576.54 mm | 815.35 mm |

At 45 degrees from vertical, required vertical rise equals horizontal reach.
A pickup above the centreline therefore needs approximately **815 mm above the
higher offset-core references**, or **826 mm above the base-core references**.
For discussion, reserve about **0.82 m of bridle rise above the higher cores**;
final sling contact points and hardware still require their own allowance.
These are placement-reference calculations, not a final rigging drawing.

## Static leg-tension sensitivity

The existing source assumes twelve 0.65 kg lamps: 7.8 kg and 76.52 N at
`g = 9.81 m/s²`. It does not provide a weighed complete-assembly mass. The 10 kg
and 12 kg rows below illustrate additional mass allowances; neither is selected.

For a symmetric example, `T = m g / (n cos(theta))`, where `n` is the number of
legs actually carrying the assumed load and theta is measured from vertical.

| Assumed total mass | Four equal legs, 45° | Two loaded legs, 45° | Two loaded legs × existing 5× factor |
| --- | ---: | ---: | ---: |
| 7.8 kg | 27.05 N/leg | 54.11 N/leg | 270.53 N/leg |
| 10 kg | 34.68 N/leg | 69.37 N/leg | 346.84 N/leg |
| 12 kg | 41.62 N/leg | 83.24 N/leg | 416.20 N/leg |

The two-loaded-leg example represents unequal sharing, not a demonstrated load
case. The 5× factor is carried from the old configuration for comparison only;
the revised calculation margins and mass allowance still need to be stated.
The existing 250 N/hub target is not automatically the appropriate leg-tension,
arm-joint or safety-arrest load.

A single bridle leg applies a force of magnitude T at its attachment, with
vertical and horizontal components. That does **not** assign T to each of the
three arm joints: resolve the node and arm geometry separately. Moments require
the actual eccentricity, `M = F × e`; static leg tension alone cannot calculate
arm bending, insert peel, or shock when a slack safety engages.

## Existing connector evidence and proof limits

Source review, not a destructive test of printed parts:

- `stella_arm.py` / `stella_config.py` currently connect the saddle through a
  **20 × 4 mm plate**, two **5 mm-wide ribs**, and a **28 × 20 × 6 mm tab**.
  The tab contains a bolt hole and an edge-open cable notch. Those dimensions
  describe geometry; they do not establish an adequate section.
- `checks.py`'s `check_stella_parts` covers selected fits, fastener access,
  intersections, point samples, and two nominal load calculations:
  `250 / (10 × 5) = 5.00 MPa` for core/bolt bearing and
  `250 / (2 × 8 × 3) = 5.21 MPa` for the two keys. Both compare with an assumed
  10 MPa sustained limit. The arithmetic is not an end-to-end structural
  analysis.
- It does not cover arm bending and deflection, tab peel, layer separation,
  notched net sections, core ligaments, fastener preload, creep, fatigue,
  profile retention, or handling moments.
- Risks to evaluate include bending in the low plate, stress at rib roots,
  tear-out beside cable cuts, and joint rotation as plastic relaxes. A prettier
  render or larger screw is not evidence against breakage.

## Printed ABS: a reference, not a four-week allowable

Primary source: Polymaker's [PolyLite ABS technical data][abs]. It reports
Young's modulus about 2247 MPa in X-Y and 2081 MPa in Z, and Z tensile strength
29.7 MPa. The HTML table duplicates an X-Y tensile-strength label, so it should
not be treated as an unambiguous design specification.

Its specimen recipe is specific: 260 °C nozzle, 90 °C bed, two shells, three
upper/lower layers, 100% infill and fan off; the published page also lists
90 °C environmental temperature for the specimens. Those conditions and the
named filament are not established for the user's prints.

The manufacturer expressly limits the typical values to reference/comparison,
not design specifications. Its HDT and glass-transition values are not creep
limits. This narrow source search found **no four-week sustained-load allowable**
for the actual printed ABS joints. A thermal, layer or creep derating adopted
for the estimate must be labelled an engineering assumption, not a measured
material property or a transferred ASA allowable.

## M3 inserts: Ø4 × 5 mm user inventory

The dimensions are supplied by the user; brand, knurl/taper, dimensional
tolerances and retention data are not. Do not substitute a similarly named
catalogue insert or silently reverse diameter and length.

Primary guidance:

- [SPIROL's insert design guide][spirol] identifies M3 coarse pitch as 0.5 mm.
  Its general heat/ultrasonic depth rule, insert length plus two pitches,
  gives **6 mm minimum host-hole depth** for a 5 mm insert. This is not screw
  length; engagement, joint stack and tip clearance still need separate checks.
- SPIROL's general boss starting range is 2–3 times insert OD: 8–12 mm for this
  inventory envelope. This is general insert-host guidance, not verified FDM
  ABS capacity. The repository's fastener skill additionally requires sufficient
  radial material and a solid load path; a small free-standing boss is not made
  structural merely by meeting an OD ratio.
- [Markforged's insert guidance][markforged] gives a surrounding/below-material
  rule of thumb for its example and stresses cavity design. Its specific cavity
  dimensions are for a different insert, not a pilot recipe for this inventory.
- [AndyMark's M3 example][andymark] has a different OD/length, while [ruthex's
  compact M3 variant][ruthex] uses another dimensional combination. “M3” alone
  does not specify the external geometry or installation hole.

**No exact pilot diameter is established by these sources for the unidentified
Ø4 × 5 mm insert.** In particular, the generic repository Ø4.2 mm M3 pilot is
for a larger insert envelope and must not be copied. The pilot, mating clearance
hole and insert-face bearing area must be coordinated to avoid jacking the
insert out. If an estimated pilot is adopted later, record it as an adjustable,
unverified installation assumption rather than a manufacturer's specification.

The selected two-M3, broad-seat arrangement is not a capacity result. Its boss
roots, load sharing, prying, head bearing, preload
retention and four-week creep still need explicit analytical treatment; merely
counting two screws does not settle those questions.

[abs]: https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-abs
[spirol]: https://www.spirol.com/assets/files/ins-threaded-inserts-design-guide-us.pdf
[markforged]: https://markforged.com/resources/blog/heat-set-inserts
[andymark]: https://andymark.com/products/m3-heat-set-threaded-insert
[ruthex]: https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-made-for-voron-rx-m3x5x4-messing-gewindebuchsen-fur-3d-druck
