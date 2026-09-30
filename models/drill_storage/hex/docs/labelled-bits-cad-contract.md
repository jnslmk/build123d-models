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

## Accepted cartridge slice

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
- **Acceptance:** User replied "confirmed" to the request to confirm the cartridge
  geometry before proceeding to the matching PETG cover.
- **Next slice:** Matching PETG cover; no accepted-design-decision delta.

## Accepted cover slice

- **Anchor:** `drill_storage.hex.bits_double.cover`.
- **Purpose / print pose:** Close the accepted 36-bit holder with a translucent
  PETG snap cover, pillow-top down at z=0 and open mouth up.
- **In scope:** Existing BITS cover extended by one Gridfinity cell, with its
  eased snap, pillow top, internal ceiling fillet and long-side engraved "BITS" label.
- **Deferred interface:** Assembled scene until this cover's acceptance.
- **Applicable specification:** LB1, LB2, LB5 and LB6. Socket assignment and both
  accepted anchors remain unchanged.

### Cover dimensions and constraints

| Dimension | Value | Source / consequence |
| --- | --- | --- |
| Outer footprint | 41.5 × 83.5 mm | Flush with the accepted base; one-cell extension |
| Cover height | 24 mm | Existing 25 mm BITS cover |
| Assembled height | 42 mm / 6U | Mouth seats at z=18 mm |
| Ceiling / bit tips | z=41 / 40 mm | 1 mm short-bit headroom |
| Flat wall / cap | 0.95 / 1.0 mm | Existing BITS cover sections |
| Snap reach | 0.35 mm radial | Existing eased BITS detent |
| Collar slip | 0.4 mm diametral | Family cover fit, not reselected |
| Label | "BITS" across long +X wall, 0.5 mm engraving | User's long-side request; accepted 0.45 mm backing |

No open shape decision. Fit and manufacturing tolerances remain physically
untested; geometric fit does not claim an opening force or a print trial.
Required skills: `model-documentation`, `cad-iteration`, `box-closures`,
`snap-fits`, `fdm-fits-and-clearances`, `printed-text` and
`build123d-geometry-ops`.

### Cover verification and acceptance gate

- [X] Valid single solid, complete rectangular envelope and z=0 print pose.
- [X] Cap, pillow, ceiling fillet, walls and mouth lead-ins survive the cuts.
- [X] Actual seated cover clears the accepted base and cartridge.
- [X] Detent fits its receiver and mechanically catches on withdrawal.
- [X] All 36 short-bit tips have the required ceiling clearance.
- [X] Engraving removes material without piercing the inherited backing.
- [X] Sharp and unclassifiable edge audits have only named functional exceptions.
- [X] A deliberately altered cover fails a relevant physical predicate.

### Cover exercised evidence

The focused shell gate passed 19 assertions on the completed cover. Removing
the top 1.01 mm with a full-envelope slab caused five failures, including the
missing-cap predicate, the measured thickness and both pillow-fillet probes.
The isometric print-pose projection was rendered and inspected. The
self-contained shaded GLB artifact was opened in Chromium and visually
inspected, with no browser errors.

The integrated `uv run check drill_storage.hex.bits_double.cover` passed:
zero seated overlap with both accepted anchors, 18.57985 mm³ withdrawal
interference and 0.15000 mm measured engagement on both axes. The inherited
short-span snap-sizing estimate is 0.765%; this is not a local-strain bound
or opening-force prediction. All 36 bit-tip positions retain 1.00000 mm
vertical clearance. A conservative 8 mm AF circumscribed tip envelope retains
at least 2.39294 mm wall clearance; it is not manufacturer-specific geometry.
The actual glyphs are at least 9.268 mm high, with no remaining engraving-tool
material or missing blind backing. Both convex-edge audit buckets passed with
zero unexplained edges.

Review exposed two false passes and both were reproduced before repair:
an "STIB" inscription passed all six former label predicates, and a public
print-pose cover with its detent removed passed all 71 former gate assertions.
The gate now checks the actual public printable solid through a fixed
inverse pose and compares independently placed BITS glyphs in reading order,
including their oriented boundary curves and counters. The healthy lettering
passes; "STIB" fails the ordered-ink predicate; the detent-removed print fails
seven relevant ramp, retention, engagement and snap-sizing predicates.
Near-coincident OCC glyph common booleans were replaced by bidirectional
curve membership after the healthy B falsely returned an empty intersection.

The config-dependent accepted base and insert leaf gates passed again.
`uv run ruff check .` and `uv run ty check .` passed after the review fixes.
The final fresh-geometry cover leaf gate passed with all predicates applied
to the public printable solid. Independent geometry/spec and gate/standards
source reviews reported no remaining important findings after the corrections.

### Long-side label revision

User feedback: "Print the cover label on the long side." This changes only
the identification plane to the long +X wall, reading along +Y. Height, fits,
cap, shell, text, engraving depth and backing remain unchanged. LB6 records
this accepted-decision delta. The cover remains the current reviewable anchor;
the assembled scene is still deferred.

The revised cover leaf gate passed with zero seated interference, unchanged
detent geometry and 1 mm short-bit headroom. All six focused label predicates
passed; moving the label back to the short wall was rejected by the long-wall
envelope, independently positioned ink and backing predicates. The glyphs
are at least 9.477 mm high, with unchanged 0.5 mm depth and 0.45 mm backing.
The refreshed STL, shaded HTML preview and isometric PNG were exported; the
PNG and browser preview were visually inspected. Ruff and type checks passed.

- **Views:** Self-contained cover artifact and isometric print-pose projection.
- **Review:** Proportions, accessible mouth, pillow, label and print pose.
- **Evidence/artifact:** `exports/drill_storage.hex.bits_double.cover.html`
  (2.7 MiB, shaded GLB), inspected alongside
  `exports/drill_storage.hex.bits_double.cover_iso.png`. The STL is pillow-down.
- **Acceptance:** User replied "confirmed" to the request to confirm the revised
  long-side label placement.
- **Next slice:** Assembled labelled 1×2 BITS scene; no geometry-decision delta.

## Current slice: assembled labelled 1×2 BITS holder

- **Anchor:** `drill_storage.hex.bits_double`.
- **Purpose / pose:** Display the accepted ASA base, TPU insert, PETG cover
  and 36 representative short-bit shanks in their closed use pose.
- **In scope:** Scene placement and registration only. Printable leaves keep
  their accepted geometry and bed poses.
- **Applicable specification:** LB1–LB6.
- **Dimensions:** Base foot at z=0; insert bottom at z=23.2 mm; cover mouth
  at z=18 mm; bit bottoms/tops at z=15/40 mm; closed envelope
  41.5 × 83.5 × 42 mm, from the accepted parts and existing BITS length.
- **Service constraint:** Export the three printable leaves separately; the
  assembly mixes materials and includes steel tool representations.
- **Technical definition:** As in the original BITS scene, each tool is a
  representative ¼-inch hex shank, not manufacturer-specific tip geometry.
- **Open decisions:** None; this scene cannot change an accepted interface.
- **Required skills:** `model-documentation`, `cad-iteration` and
  `build123d-geometry-ops`.

### Assembly verification and review

- [X] Actual assembled envelope and all three part placements match the accepted fit.
- [X] All 36 positioned shanks stand on the rigid guide floor and clear the ceiling.
- [X] The scene's actual cover has zero seated interference with base and cartridge.
- [X] Refreshed 3D artifact visually shows the assembled holder and long-side label.

The cover leaf gate already owns the physical snap and hidden-wall predicates.
Scene placement is exercised directly; no duplicate assembly gate is added.

The base, insert and cover leaf physical gates all passed after assembly
integration. Ruff and type checks passed; no printable geometry changed.

- **Evidence / artifact:** `exports/drill_storage.hex.bits_double.html`
  (12.5 MiB, shaded GLB). A throwaway smoke wrapper exercised the actual scene
  builder through the artifact CLI: 41.5 × 83.5 × 42 mm bounds, 36 distinct
  shanks at z=15–40 mm, all standing on blind ASA floors with 1 mm ceiling
  clearance. Actual scene cover/base and cover/insert common volumes were zero.
  Chromium visual review showed the closed holder, all shanks through the
  translucent cover and the upright long-side BITS label.
- **Viewer limitation:** Clicking the artifact's Grid button raised the existing
  `__omp_shell` reference error from `view_artifact.py`'s shell expression.
  Geometry renders; the unrelated artifact-shell code remains unchanged.
- **Acceptance:** Pending human review of the assembled holder.
- **Next slice:** None defined.
