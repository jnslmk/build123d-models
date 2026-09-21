# CAD contract — Stella mating profile arm

> **Current slice:** One complete mating profile arm, from the accepted core-side
> key through one open profile saddle and its arm-side keeper attachment lands.
> The removable keeper is deferred to the next separately gated slice.
> **Accepted upstream anchor:** `led_profiles.stella.core`, accepted by the user
> on 2026-09-21 with “Looks good, go ahead” after review of the 20 mm candidate.
> **Status:** The core interface is frozen. The user authorized the complete-arm
> boundary and then approved a same-slice continuous-shell amendment: the
> profile-following half-round saddle itself must morph into the connector root,
> with no independently legible support member or sharp form break. The current
> implementation is an unaccepted review candidate; the keeper remains deferred.

## References

- **Context:** [LED profile model language](../CONTEXT.md)
- **Specification:** [Stella redesign specification](stella-specification.md)
- **Supporting evidence:** [Stella analytical basis](stella-analytical-basis.md)
- **Re-entry and tight loop:** [Stella re-entry index](stella-cad-contract.md)
- **Joint decision:** [ADR-0002](adr/0002-stella-seated-m3-arm-joints.md)
- **Profile boundary:** [ADR-0001](adr/0001-stella-unmodified-profiles.md)

## Accepted upstream interface

The accepted functional core is **138.603 × 127 × 20 mm** in its flat +Z print
pose. Each branch provides:

- one **28.25 × 28.25 × 3 mm** rounded keyed seat with a 0.8 mm entry;
- two M3 insert axes at local radial offsets **−9 and +9 mm** from the seat
  centre;
- an estimated **Ø3.7 × 6 mm** blind pilot for the user's unidentified
  M3, Ø4 × 5 mm insert;
- a smooth external valley with no electrical-cable notch; and
- the proved insert-installation and screw-driver envelopes recorded in the
  accepted core gate.

The arm-side nominal key is **28 × 28 mm, R2.5**. The core uses the ABS
FREE-class total clearance, so the seat—not a second arm-side allowance—owns
the fit. The provisional stack is M3 × 12 screw, Ø7 × 0.5 mm washer and
**7.5 mm arm material at each screw**, giving 4 mm nominal thread engagement.
Pilot suitability, insert retention, preload and real hardware remain
unqualified.

Core acceptance freezes these mating dimensions for this slice. Changing them
would reopen the accepted core rather than silently adjusting the arm.

## Current slice

- **Name / proposed public model:** Mating Stella profile arm —
  `led_profiles.stella.arm`.
- **Anchor part:** One complete arm from the accepted keyed core seat to one
  open profile saddle, including the arm-side keeper attachment lands but not
  the separate keeper. The user confirmed this boundary after core acceptance.
- **Purpose:** Transfer one profile member into the accepted vertex core through
  broad bearing faces and two clamping screws while preserving non-invasive
  profile support, external cable access and later lamp replacement.
- **Print pose to validate:** Profile axis horizontal, saddle mouth upward, and
  the continuous shell seated on `z=0`. Assembly transforms, not the public part,
  place the sloped arm onto the core.
- **In scope:** Arm key, two M3 clearance paths and head/washer/driver access,
  one hollow profile-derived root-to-saddle shell, one open saddle, vertically
  centered arm-side keeper attachment lands, external cable/connector
  clearance, edge treatment and arm-only checks.
- **Deferred interfaces:** The removable keeper itself, offset cores, the second
  tetrahedron, the complete electrical route, primary suspension hardware and
  full assemblies remain separately gated.

## Applicable specification constraints

| Requirement | Consequence for this slice |
| --- | --- |
| `STELLA-JOINT-01` | Match the accepted broad key and clamp with two M3 screws into the core inserts; bearing faces and shoulders, not screw shanks, carry shear and rotation. |
| `STELLA-PROFILE-01` | Support the aluminium profile without drilling it, crushing its 0.5 mm wall or loading the diffuser; use a rounded, tapered arm transition and vertically centered keeper lands beneath the future keeper rather than a block-like support. |
| `STELLA-CABLE-01` | Keep the electrical cable outside the core and preserve side-loading access for an already-terminated cable. |
| `STELLA-USE-01` | Use ABS and the indoor, at-most-28-day assumptions; do not inherit the previous ASA arm's allowables. |
| `STELLA-SERVICE-01` | Keep fasteners, cable and future keeper accessible while the surrounding structure independently supports the lamp. |
| `STELLA-EVIDENCE-01` | CAD checks and estimates may screen geometry; they do not rate the arm or qualify overhead use. |

## Evidence-backed dimensions

| Dimension | Value and status | Evidence/source | Applies to |
| --- | --- | --- | --- |
| Core-side arm key | 28 × 28 mm, R2.5; accepted mating nominal | Accepted core configuration | Arm root |
| Core seat | 28.25 × 28.25 × 3 mm, R2.625, 0.8 mm entry | Accepted core geometry and FREE-class ABS allowance | Joint fit |
| Insert axes | ±9 mm along the arm's local radial direction | Accepted core geometry | Arm clearance holes |
| Screw stack | M3 × 12, Ø7 × 0.5 washer, 7.5 mm arm stack; provisional | Accepted core screen and ISO envelopes | Joint clamp |
| Screw/driver envelopes | Ø3.25 nominal arm clearance, Ø5.5 × 3 head, Ø8 × 50 driver | Core configuration; hardware remains unmeasured | Access checks |
| Profile envelope | 26.1 × 30.5 mm with 0.5 mm wall | `../config.py` measurements | Saddle |
| Electrical cable | Ø6.7 mm; fixed-install bend radius 26.8 mm | `../mount_config.py` | External route |
| Connector/service envelopes | Ø21 × 45 mm connector family; Ø40 hand envelope | Accepted core screen; exact connector remains unverified | Side access |
| Assembly member direction | Radial component `1/sqrt(3)`, core-normal component `sqrt(2/3)` | Analytical equilibrium basis | Root-to-shell transition |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Print orientation | Validate the confirmed mouth-up pose against support demand at the sloped key and strength through the continuous shell. | Root/shell form and checks |
| Root-to-saddle shell | Size actual post-cut net sections for axial member load, core-normal reaction, handling moment and screw-head bearing by changing the shell exterior around the fixed profile cavity; do not add a separate beam, rail, rib, tower or brace. | Shell section thickness and transition envelope |
| Profile saddle | Retain measured-profile clearance and bearing support below the diffuser while making the saddle wall and transition one continuous form. | Saddle geometry |
| Keeper-side interface | Choose lands and fastener or keyed features that a later removable keeper can use without changing the accepted arm body. | Arm completion before keeper work |
| External cable path | Prove the cable, bend, connector and service approach around the accepted solid core and new arm; do not add a core notch. | Arm envelope and service access |
| Hardware reality | Measure or identify the user's inserts, screws and washers and validate the pilot with a coupon before physical use. | Physical qualification, not initial CAD |
| Material capacity | Retain conservative screen assumptions, but keep printed-ABS creep, layer strength, fatigue, preload and pull-out explicitly unqualified. | Rating and physical use |

## Service and assembly constraints

1. The arm must be removable from the core with the lamp independently
   supported; removal must not require disturbing the suspension cord.
2. Both M3 heads and the driver approach must remain accessible after the arm is
   seated, and the arm must not obstruct insert installation before assembly.
3. An already-terminated electrical cable must approach from the side without
   passing its connector through the core or a closed arm opening.
4. The future keeper must be removable without modifying the aluminium profile
   or using the diffuser as a structural reaction.

## Required skills

| Concern | Skill | Why it applies now |
| --- | --- | --- |
| Mating key and profile support | `part-joints` | The arm must reproduce the accepted key from one source and establish non-invasive mating geometry. |
| Clearance choices | `fdm-fits-and-clearances` | The key, screw and profile allowances must remain named material-adjusted fits. |
| Two-M3 joint | `fasteners-and-inserts` | Screw reach, head/washer bearing and driver access constrain the arm root. |
| Edge treatment and physical gates | `build123d-geometry-ops` | The sloped root and internal checks need isolated edge operations and point-sampled proof. |
| Human-gated dependency order | `cad-iteration` | The arm becomes the accepted anchor before the separate keeper or assembly. |

## Verifiable predicates for the authorized geometry

- [x] One valid connected arm solid in its declared +Z print pose, seated on
  `z=0`; the sloped key and root faces remain self-supporting in the mouth-up
  pose.
- [x] The nominal 28 × 28 mm key and two screw axes seat in the accepted core
  without collision or duplicated clearance.
- [x] Both screws have through clearance, washer/head bearing, Ø8 × 50 mm driver
  approach, 4 mm nominal engagement and 2 mm to the blind-well bottom.
- [x] Actual finished profile-shell sections at x=18, 26, 36, 52 and 65 mm pass
  the unchanged sustained and short-event limited-beam screens after holes and
  reliefs.
- [x] Direct point witnesses retain the hollow floor and both flanks from root
  through saddle, and sections at x=36, 52 and 65 mm are each one U-shaped face
  with no independent support island.
- [x] The shell begins inside the frozen shoulder, expands through its envelope,
  and buries the former x=14 transverse U-face; residual transverse boolean
  seams at x=14 and x=18 remain below 1 mm² each.
- [x] The measured profile envelope has two 12 mm bearing bands at the saddle
  ends, ABS SLIDING clearance and no diffuser contact.
- [x] External cable, connector and Ø40 hand corridors remain open beside one
  seated arm and the accepted core; the 26.8 mm bend radius remains an assembly
  routing constraint rather than a closed arm passage.
- [x] The stable edge survey is pinned to 48 sharp and 6 unclassifiable
  exceptions: bed and bearing datums, raw insert mouths and boolean/loft seams.

## Visual review

- **Round-2 finding:** Isometric, side and seated-core views of the first
  continuous-shell candidate showed a straight planar break where its U-shell
  ended against the separately formed shoulder/key root. That candidate is
  superseded.
- **Views produced for the corrected candidate:** None. This fix round
  explicitly excluded render/export commands.
- **Pending human judgment:** Whether the root blend now makes saddle, shell and
  connector root read as one uninterrupted form, without a separately legible
  support member or sharp transition, and whether the proportions remain slim.
- **Artifacts:** No new visual artifact for the corrected candidate.

## Acceptance gate

- **Accepted upstream core:** On 2026-09-21 the user reviewed the interactive
  artifact and five-view sheet and replied **“Looks good, go ahead.”**
- **Core proof retained:** `uv run check led_profiles.stella.core` passed before
  commit `fff2f9c`; deliberate notch, blocked-bore and thin-floor defects were
  rejected. Ruff and ty passed.
- **Boundary decision:** After core acceptance, the user selected **complete arm,
  keeper deferred**: the core-side key, two-M3 connection, transition, open
  saddle, keeper lands and external service clearances are one arm slice.
- **First implemented candidate:** 101.488 × 52.17 × 40.933 mm,
  57,909.851 mm³ in print pose. Human review rejected its block-like transition
  and low keeper lands.
- **Superseded twin-web candidate:** 101.488 × 52.17 × 40.933 mm,
  59,883.470 mm³ in print pose. Its raised keeper lands remain applicable, but
  its distinct beam/rail/rib support morphology is rejected.
- **Confirmed continuous-shell amendment:** The profile-following saddle itself
  morphs into the connector root as one hollow shell. Independent beams, rails,
  ribs, towers, braces, newly started extrusions and sharp form breaks are out.
- **Current review candidate:** 107.395 × 52.170 × 40.933 mm,
  63,467.323 mm³ in mouth-up print pose. Focused direct construction and physical
  predicate probes pass; no render, export, repository check runner, formatter,
  lint, type check or test suite was run in this implementation task.
- **Current-slice acceptance signal:** Pending human visual review and explicit
  acceptance. The geometry is not physically qualified or releasable.
- **Geometry authorization:** Explicitly granted with the boundary selection.
- **Next slice after arm acceptance:** The separate removable profile keeper.
