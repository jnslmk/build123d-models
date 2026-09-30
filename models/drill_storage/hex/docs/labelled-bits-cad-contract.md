# Labelled BITS CAD contract

## References

- [Public hex purpose](../README.md)
- [Accepted specification LB1–LB5](labelled-bits-specification.md)
- Dimensional sources: `hex/config.py`, `box.py`, rectangular Dremel base.

## Accepted base slice

- **Name:** Labelled 1×2 rigid base (accepted).
- **Anchor:** `drill_storage.hex.bits_double.base`.
- **Purpose/print pose:** Guide 36 short bits; two feet at z=0, socket mouths up,
  printed in black ASA. Complete labels let the user judge the planned layout.
- **In scope:** Footprint, blind guides, readable wall labels and unchanged BITS
  retention features extended along the second Gridfinity cell.
- **Dependants at the base gate:** TPU cartridge, PETG cover and assembled scene
  were deferred until the base was accepted.

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
- **Acceptance:** User replied “confirmed” to the request to confirm the base
  geometry and side-wall label placement before the matching parts are built.

## Current slice: matching TPU cartridge

- **Anchor:** `drill_storage.hex.bits_double.insert`.
- **Purpose/print pose:** Grip the same 36 short bits on the existing BITS
  short TPU lands; flat bottom at z=0, sockets up, as the original hex insert.
- **In scope:** Rectangular cartridge, through sockets, outward retention bead,
  +X antirotation key, edge treatments and fit against the accepted base.
- **Deferred dependants:** PETG cover and assembled scene wait for cartridge
  acceptance. This is the next anchor named by the accepted base contract.
- **Accepted-decision delta:** None; LB1–LB5 remain unchanged.

### Cartridge dimensions and evidence

| Dimension | Value/source | Consequence |
| --- | --- | --- |
| Cartridge body | 35.68×77.68 mm, `config.CART_X/Y` | Same per-side slip as BITS, extended by one cell |
| Height / assembled bottom | 8 / z=23.2 mm, existing BITS | Top remains z=31.2, 1.2 mm proud of base |
| Socket locations | All 36 `config.SOCKETS` coordinates | Guide and land axes cannot drift |
| Hex land and relief | Existing `HEX_AF`, `HEX_LAND_FIT`, `RELIEF_FIT` | No new grip calibration |
| Mouth | Existing BITS 0.2 mm hex lead-in | Retains inherited tight packing |
| Retention / key | Existing BITS sections and public key helper | Receiver belongs to the accepted base |

### Cartridge service constraints and technical definitions

- The rigid base remains unchanged; bits pass through TPU to its blind floors.
- The outward bead must fit the existing rectangular receiver without unwanted
  rigid-body overlap; the key must prevent incorrect cartridge orientation.
- No open design choice. TPU print fit and manufacturer tip envelopes remain
  untested physically, as stated in the specification.
- Required skills: `model-documentation`, `cad-iteration`,
  `build123d-geometry-ops`, `fdm-fits-and-clearances`, `part-joints`.

### Cartridge verifiable predicates

- [x] Valid single solid, full rectangular body and z=0 print pose.
- [x] Every socket has the actual inherited land, relief and hex lead-ins.
- [x] Physical outer walls and between-socket lands survive the cuts.
- [x] Seated cartridge clears the accepted rigid base and registers all guides.
- [x] Actual retention and key geometry fit their accepted receiver.
- [x] Edge audit has only named functional exceptions in both survey buckets.
- [x] A filled-socket mutation is rejected by the socket predicate.

### Cartridge exercised evidence

The socket predicate passed 226 assertions on the exported cartridge. Filling
the first socket with a full-height 4.2 mm-radius cylinder produced ten failures,
including the through-hole and actual section-opening checks.

The first seated-fit gate rejected a **0.022794 mm³ rigid overlap**: an external
0.01 mm offset at the bead's ramp roots projected into the base just below the
receiver. The bead's external roots were restored to the original BITS zero
reach, retaining only the independently buried inner boundary for a robust fuse.
This is a correction to inherited geometry, not a new fit or design decision.

Measured completed-solid sections retain 36 separate openings: grip neighbour
land 1.0205 mm, upper relief land 0.5933 mm, top mouth land 0.1935 mm. The top
outer wall is 0.6002 mm after charging both the socket-mouth and outer-rim bevels.

The final fresh-geometry gate passed with **0.000000 mm³ seated overlap**,
6.0923 mm³ overlap in the reversed keyed orientation and 80.1611 mm³
withdrawal overlap demonstrating the receiver's mechanical catch.
The edge audit found **0 unexplained sharp and 0 unclassifiable edges**.
Functional exceptions match exact hex vertex curves, actual narrow retention
datum faces, edges of the unchanged public key geometry and measured tangent
key seams; ramps and mouth rims remain audited.

`uv run check drill_storage.hex.bits_double.insert`, `uv run ruff check .` and
`uv run ty check .` passed. Source reviews of geometry/spec and physical gates
reported no remaining important findings after the bead-root correction.

### Cartridge visual review and acceptance gate

- **Views:** Self-contained cartridge artifact and top/side projection as needed.
- **Review:** Literal grid, proportions, accessible mouths, keyed insertion and
  print pose. A view does not prove the hidden grip geometry.
- **Evidence/artifact:** `exports/drill_storage.hex.bits_double.insert.html`
  (2.0 MiB, shaded GLB), plus the refreshed and inspected isometric PNG.
  Local automatic opening via `xdg-open` timed out; the artifact and render are
  available directly. The STL is in print pose, land-side down.
- **Acceptance:** Pending explicit human acceptance of the cartridge anchor.
- **Next slice:** Matching PETG cover after cartridge acceptance.
