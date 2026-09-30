# Labelled BITS CAD contract

## References

- [Public hex purpose](../README.md)
- [Accepted specification LB1–LB5](labelled-bits-specification.md)
- Dimensional sources: `hex/config.py`, `box.py`, rectangular Dremel base.

## Current slice

- **Name:** Labelled 1×2 rigid base.
- **Anchor:** `drill_storage.hex.bits_double.base`.
- **Purpose/print pose:** Guide 36 short bits; two feet at z=0, socket mouths up,
  printed in black ASA. Complete labels let the user judge the planned layout.
- **In scope:** Footprint, blind guides, readable wall labels and unchanged BITS
  retention features extended along the second Gridfinity cell.
- **Deferred dependants:** TPU cartridge, PETG cover and assembled scene. Their
  envelopes and coordinates are constraints; their solids wait for acceptance
  of this anchor under the core-first CAD policy.

## Evidence-backed dimensions

| Dimension | Value | Source |
| --- | --- | --- |
| Body | 41.5×83.5 mm | `PAD`, plus one `GRID=42` cell |
| Base/shoulder | 30 / 18 mm | Existing BITS |
| Bit insertion / rigid floor | 15 / z=15 mm | Existing BITS |
| Cavity floor | z=23.2 mm | Existing BITS |
| Guide across flats / mouth chamfer | 6.55 / 0.4 mm | Existing BITS shaved fits |
| Socket pitches | Derived from existing TPU wall and relief footprint | `bits_double/config.py` |
| Labels | Bold 4.15 mm font, 0.8 mm deep | Printed-text guidance; direct glyph probe |

The long walls carry the nearest two socket columns each. Full strings are
rotated so their length occupies the solid body's vertical band. At font 4.15,
`SL6.5` is approximately 12.397 mm long, `H` approximately 3.025 mm high and the
period approximately 0.729×0.784 mm; these were measured with build123d's actual
bold font. Each row's paired labels are offset ±1.85 mm along Y. Tool bounds and
actual cuts, rather than nominal font size, must pass the physical gate.

## Open technical definitions and assembly constraints

- No open shape choice: the accepted design extends the existing BITS box.
- Manufacturer-specific tip envelopes and physical ASA/TPU fits remain untested.
- The future cartridge must share all 36 coordinates and the existing BITS grip.
- The future cover must retain the existing short-bit clearance and eased snap.
- Foot, collar and cartridge mouth bevels remain the inherited FDM treatments.

## Required skills

`model-documentation`, `cad-iteration`, `build123d-geometry-ops`,
`printed-text`, `fdm-fits-and-clearances`, `box-closures`.

## Verifiable predicates

- [x] Valid single solid, correct 1×2 envelope and z=0 print pose.
- [x] Two correctly spaced feet with the inherited chamfer profiles.
- [x] All 36 guides open at their centers and end on the z=15 rigid floor.
- [x] Hex guide lead-ins, cavity mouth and collar top bevel exist physically.
- [x] Retention groove walls and roof survive the rectangular extension.
- [x] All 36 full labels fit, do not overlap, and remove real wall material.
- [x] Sharp-convex-edge audit has only named functional exceptions.
- [x] A guide-floor defect demonstrates a failing physical predicate.

### Exercised defect rejection

Focused checks on the exported STEP rejected all 36 blind floors after a
0.2 mm upward shift, and rejected a cut through the first guide-mouth land.
An unrelated shoulder notch produced three edges rejected by the seating
allowance. These are deliberate damaged-geometry probes, not print trials.
The true closest mouth lands are 0.105 mm across X and 1.183 mm across Y;
completed-solid samples cover a 0.1 mm strip rather than a circle approximation.

The edge survey on the exported solid found **0 unexplained sharp and
0 unclassifiable edges**. Named geometric exceptions: 24 seating-profile edges,
432 blind-hex floor/vertical corners, 18 retention receiver lips, 546 actual
glyph-cut edges and two tangent antirotation-key mouth splits.

Final fresh-geometry verification passed:
`uv run check drill_storage.hex.bits_double.base`, `uv run ruff check .` and
`uv run ty check .`. Independent geometry/spec and physical-gate source reviews
reported no remaining important findings after the gate corrections.

## Visual review and acceptance gate

- **Views:** Self-contained 3D artifact plus long-side and top projections.
- **Review:** Base proportions, literal grid, grouped Torx sockets, label
  readability and unambiguous side-wall-to-socket mapping.
- **Artifact:** `exports/drill_storage.hex.bits_double.base.html` (9.4 MiB,
  shaded GLB), opened locally. Top and right PNG projections were rendered and
  inspected; the right projection shows complete, separated bold labels.
- **Acceptance:** Pending human review of this base geometry. The user's
  “accepted, implement it” accepted LB1–LB5 and the label plan, not unshown solids.
- **Next slice:** Matching TPU cartridge after explicit anchor acceptance.
