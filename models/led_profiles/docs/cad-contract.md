# CAD contract — Stella functional vertex core

> **Current slice:** Functional unshifted vertex core — implemented review
> candidate; geometry acceptance pending.
> **Requirement source:** [Stella specification](stella-specification.md).
> **Status:** Round 1 confirmed the continuous web-section outline, removal of
> core electrical-cable notches, two textile-cord suspension holes, and a 12 mm
> overall-height target rather than a hard ceiling. Round 2 selected the short
> closed attachment loop through both holes. On 2026-09-21 the user explicitly
> authorized geometry implementation; the resulting 20 mm core is now at the
> human acceptance gate. No dependent slice is open.

## References

- **Context:** [LED profile model language](../CONTEXT.md)
- **Specification:** [Stella redesign specification](stella-specification.md)
- **Supporting evidence:** [Stella analytical basis](stella-analytical-basis.md)
- **Re-entry and tight loop:** [Stella re-entry index](stella-cad-contract.md)

## Current slice

- **Name / public model:** Functional unshifted vertex core —
  `led_profiles.stella.core`.
- **Anchor part:** One core with three keyed arm seats and two M3 insert pockets
  per seat, a continuous smooth outer outline, and two rounded suspension holes.
- **Purpose:** Join the three branch load paths while retaining lamp service
  access and an explicitly defined primary suspension attachment.
- **Form:** Carry the existing web-section outline through the body height,
  without its three cable notches or a separate inset-buttress outline; retain
  functional seat recesses and appropriate edge treatment.
- **Height target/result:** The target is **12 mm overall (1.2 cm)**, not
  1.2 mm. The implemented result is **20 mm**. The 12 mm hardware stack
  physically accommodates a 6 mm insert well, 3 mm retained floor and 3 mm
  keyed seat, but fails the actual post-cut screens. At 19 mm the outer-seat
  short-event result is 13.748 MPa against the assumed 13.365 MPa threshold
  and one 8 mm suspension ligament reaches 13.517 MPa; 20 mm passes both.
- **Print pose:** Flat underside on `z=0`, seats/insert axes in +Z. This keeps
  branch material in the XY layer plane. The lower R2 cord mouths necessarily
  exceed a 45° overhang near the bed and require local removable support plus
  post-print smoothing/inspection; support-free contact is not claimed.
- **Deferred parts:** Separate profile arms, keepers, offset cores, physical
  fastener/suspension assemblies and the full frame. Interface and tool
  envelopes constrain this core; no dependent public part is authorized.

## Applicable specification constraints

| Requirement ID | Immediate consequence for this slice |
| --- | --- |
| `STELLA-CORE-01` | Use the uninterrupted web-section outline through the core height; size the cut sections without old depth or buttress minima. |
| `STELLA-JOINT-01` | Retain all three keyed seats and the six pockets for the user's M3 inserts; preserve bearing, host material and installation access. |
| `STELLA-PROFILE-01` | Preserve the later slim, non-invasive profile-capture boundary. |
| `STELLA-CABLE-01` | Remove the three core cable notches; retain external access for already-terminated electrical cables. |
| `STELLA-SUSPENSION-01` | Keep the four upper primary lines, two per tetrahedron, and common metal collector unchanged. |
| `STELLA-SUSPENSION-02` | Replace the single webbing slot with two rounded holes carrying a closed cord loop under their central bridge; keep its joining knot above the core and away from contact. |
| `STELLA-USE-01` | Use ABS, indoor use up to 28 days, and explicit print/temperature assumptions. |
| `STELLA-SERVICE-01` | Retain core hardware/tool access and inspectable suspension contact/termination; full lamp extraction remains deferred. |
| `STELLA-EVIDENCE-01` | Use estimates and geometry screening only; no overhead, creep, knot-capacity or safety-arrest qualification. |

## Evidence-backed inputs

These are hardware/layout inputs, not approved dimensions of the revised core.
Unrecorded manufacturing tolerances remain unknown.

| Input | Value and source | Consequence |
| --- | --- | --- |
| Profile | 26.1 × 30.5 mm, 0.5 mm wall, 1500 mm long; `../config.py` and `../README.md` | Preserve lamp/service boundaries without loading the diffuser or crushing aluminium. |
| Branch layout | Three directions at 120° in the core plane | Retain the existing three-arm layout. |
| Electrical cable | OD 6.7 mm, fixed-install bend radius 26.8 mm; `../mount_config.py` | External route and bend space, not new core slots. |
| Electrical connector | Provisional SP16 Ø21 × 45 mm family envelope; README also permits SP17 | Exact purchased variant/coupling space remains unverified; no SP17 fit claim. |
| User inserts | M3 thread, Ø4 × 5 mm outside envelope; knurl/tolerance unknown | Re-evaluate pilot, relief depth and host material; do not inherit a generic larger insert recipe. |
| Material/use | ABS, indoor use ≤28 days; `STELLA-USE-01` | Temperature, print properties and duration reductions remain explicit assumptions. |
| Suspension cord candidate | Petzl CORD / CORDELETTE 6MM, R046AA00: nominal 6 mm nylon; [manufacturer evidence](stella-analytical-basis.md#two-hole-textile-cord-attachment--definition-evidence) | Provisional engineering selection only; the implemented allowance/contact geometry is not a lamp-use approval or capacity rating. |

The prior M3 stack, iron/driver envelopes and ABS/load assumptions are recorded
in the [preceding candidate's analysis](stella-analytical-basis.md#functional-core-screen--2026-09-20).
They are references to re-evaluate, not silently retained dimensions or proof.

## Implementation definitions and remaining limits

| Definition | Implemented state | Remaining limit |
| --- | --- | --- |
| Suspension cord | Nominal 6 mm nylon Petzl CORD R046AA00 with 2 mm functional diametral handling/movement allowance, giving Ø8 holes. The cord has not been measured. | The allowance is an engineering choice, not a Petzl minimum or a fit-class result. |
| Loop and joining method | Closed route down one hole, below the bridge and up the other; the documented starting point remains a double fisherman's knot above the core. | Knot bulk, tail length, migration, equal sharing and primary-line coupling remain physical/deferred-interface work. Petzl's Prusik guidance does not qualify this application. |
| Core depth/seat proportions | 138.603 × 127 × 20 mm overall; three 28.25 × 28.25 × 3 mm seats with 0.8 mm entries. The smooth web outline continues through the structural height. | Human geometry acceptance remains pending; the 20 mm depth is a screen result, not a rated minimum. |
| Insert installation/stack | Six Ø3.7 × 6 mm blind pilots; pocket bottoms are at z=11 mm, with a checked 3 mm minimum floor witness, 3 mm radial host outside the Ø4 insert envelope, installation-iron access, and the retained M3 × 12 / 7.5 mm arm / 0.5 mm washer stack. | Pilot size, real knurl/taper, pull-out, torque-out, preload retention, screw choice and printed coupon remain unqualified. |
| Suspension contact and ligaments | Two Ø8 holes on 22 mm centres; R2 mouths; 14 mm throat bridge, 10 mm mouth bridge, 8 mm outer ligaments and 16 mm effective straight-contact height. | R2 is an engineering choice with no manufacturer minimum; abrasion, bearing/contact stress, knot/core capacity, movement and unequal contact load remain unqualified. |
| External electrical-cable access | No core notches. Each open valley retains a solid band and clears core-only radial side corridors beginning at r=45 mm for sleeved Ø7.7 cable, r=50 mm for coupled Ø21 connectors, and r=60 mm for the Ø40 hand envelope. | Exact SP16/SP17 variant, later arm interaction, complete bend path, retention and lamp extraction remain assembly proof. |
| Load/ABS estimates | Retained 12 kg unweighed frame allowance, one loaded line per frame at 45°, separate 1.5× sustained and 5× short-event screens, 40 °C/28-day assumption and documented ABS factors. Actual finished sections include both holes and all seat/pilot cuts. | No solved frame stiffness, measured print properties, four-week creep allowable, shock/safety-arrest case, fatigue or professional qualification. |

## Required skills

- `model-documentation`, `cad-iteration`: purpose, definition and geometry gates.
- `part-joints`, `fasteners-and-inserts`: retained keyed seats, insert hosts and
  hardware/tool access.
- `fdm-fits-and-clearances`: named allowances for future hole/interface sizing.
- `build123d-geometry-ops`: contact/edge treatment and actual geometry proof.

## Verifiable predicates — implemented review candidate

- [x] One valid connected solid, seated on `z=0` in the flat +Z print pose.
- [x] The smooth outline has equal feature-free interior sections through the
  body height, with no inset-buttress transition, perimeter ledge or
  electrical-cable notch.
- [x] Three keyed seats and six insert pockets retain bearing/host material,
  installation depth, and posed iron, washer, head and driver access.
- [x] Two Ø8 suspension holes admit the nominal-6 mm route, carry actual R2
  toroidal contact at all four mouths, and retain checked bridge/outer material.
- [x] Core-only external cable, connector and hand side corridors remain open;
  complete arm/assembly routing and lamp extraction remain deferred.
- [x] Actual net sections include both suspension holes and every seat/pilot
  cut under the stated load, ABS, print, temperature and duration assumptions.
- [x] The sharp-edge survey reports no unexplained sharp or unclassifiable
  edges; raw insert mouths and exact periodic seams are identity-matched,
  reasoned exceptions.

The revised predicates reject a reintroduced valley notch, a blocked suspension
hole, and a thinned insert floor at their owning gates. The 12 mm and 19 mm
height trials are also rejected by the retained physical screens.

### Implementation proof — 2026-09-21

- `uv run check led_profiles.stella.core` passes on the implemented 20 mm core.
- `uv run ruff check .` and `uv run ty check .` both pass after integration.
- A 12 mm build fails 31 section predicates; representative results are
  36.507 MPa at the outer-seat short-event section against 13.365 MPa,
  25.344 MPa for one outer suspension ligament, and 20.275 MPa for the
  mouth bridge. These are screening comparisons, not material predictions.
- At 19 mm, all three r=63 mm outer-seat sections fail at 13.748 MPa and the
  one-ligament short-event screen fails at 13.517 MPa. At 20 mm the
  corresponding values are 12.402 MPa and 12.672 MPa.
- Deliberate single-defect variants are rejected by the exact intended gates:
  a valley notch, one filled suspension bore and a floor cut leaving only
  2 mm below one insert pilot.
- Fresh review outputs are
  `exports/led_profiles.stella.core_loop-review.html`,
  `exports/led_profiles.stella.core_loop-review-sheet.png`, and the separate
  isometric, top, side, insert-floor-section and
  suspension-bridge-section PNGs sharing that filename stem.

### Historical proof — preceding 22 mm candidate

- `uv run check led_profiles.stella.core --json exports/led_profiles.stella.core.functional-check.json`:
  151 assertions passed; 15 deliberately broken cases were rejected.
- `uv run ruff check .` and `uv run ty check .` passed for that implementation.
- `exports/led_profiles.stella.core_functional-review.html` and
  `exports/led_profiles.stella.core_functional-review.png` show the old candidate
  with cable notches and one sling slot. They are not views of this amendment.
- The rejected 46 mm blank's earlier 26 assertions are likewise historical;
  neither candidate establishes dimensions or geometry acceptance for this one.

## Visual review after modelling

The fresh core-only interactive artifact and review sheet named above show the
isometric, top and side views plus the insert-floor and two-hole bridge
sections. They show the actual 20 mm result and its +8 mm departure from the
target; hidden geometry remains governed by the leaf gate rather than the
drawing. These are review outputs, not geometry acceptance.

## Acceptance gate

- **Round 1 confirmation:** The user answered **“as recommended”** to the
  revised purpose/three requirement changes, 12 mm height target, and selection
  of knot-compatible textile cord. The specification records those changes.
- **Round 2 confirmation:** The user answered **“A”**: a separate short closed
  cord loop through both holes, joined above the core, rather than stopper
  terminations bearing at the holes.
- **Definition completion:** Complete for this anchor's architecture.
  Remaining entries above are implementation sizing or explicitly unqualified
  hardware/contact assumptions, not silently open architecture choices.
- **Geometry authorization:** Explicitly granted on 2026-09-21 for this functional
  unshifted core amendment; implementation proceeded without reopening the
  accepted architecture.
- **Implementation proof:** The 20 mm review candidate, leaf gate, deliberate
  failure cases and fresh core-only views are complete.
- **Geometry acceptance:** Pending human review of this implemented core; no
  dependent slice is open.
- **After core acceptance:** One mating profile arm/arm-to-core connection.
  Keepers, offset cores and full-assembly work remain separately gated.
