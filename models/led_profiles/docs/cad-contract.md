# CAD contract — Stella mating profile arm

> **Current slice:** One unshifted mating profile arm and its arm-to-core
> connection — definition boundary pending confirmation.
> **Accepted upstream anchor:** `led_profiles.stella.core`, accepted by the user
> on 2026-09-21 with “Looks good, go ahead” after review of the 20 mm candidate.
> **Status:** The core implementation and its interface are frozen for dependent
> work. This contract proposes the next anchor; no arm geometry exists yet.

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
  the separate keeper. This boundary is the proposal awaiting confirmation.
- **Purpose:** Transfer one profile member into the accepted vertex core through
  broad bearing faces and two clamping screws while preserving non-invasive
  profile support, external cable access and later lamp replacement.
- **Proposed print pose:** Profile axis horizontal, saddle mouth upward, and the
  structural beam/ribs seated on `z=0`. Assembly transforms, not the public
  part, place the sloped arm onto the core.
- **In scope after confirmation:** Arm key, two M3 clearance paths and
  head/washer/driver access, structural transition and ribs, one open saddle,
  the arm-side half of the future keeper joint, external cable/connector
  clearance, edge treatment and arm-only checks.
- **Deferred interfaces:** The removable keeper itself, offset cores, the second
  tetrahedron, the complete electrical route, primary suspension hardware and
  full assemblies remain separately gated.

## Applicable specification constraints

| Requirement | Consequence for this slice |
| --- | --- |
| `STELLA-JOINT-01` | Match the accepted broad key and clamp with two M3 screws into the core inserts; bearing faces and shoulders, not screw shanks, carry shear and rotation. |
| `STELLA-PROFILE-01` | Support the aluminium profile without drilling it, crushing its 0.5 mm wall or loading the diffuser. |
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
| Assembly member direction | Radial component `1/sqrt(3)`, core-normal component `sqrt(2/3)` | Analytical equilibrium basis | Root-to-beam transition |

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Slice boundary | Confirm a complete arm with arm-side keeper lands while the separate keeper remains deferred, rather than a root-only coupon or combined arm/keeper slice. | Geometry authorization |
| Print orientation | Compare the proposed mouth-up pose against support demand at the sloped key and strength across the root transition. | Root/rib form and checks |
| Root-to-beam structure | Size actual post-cut net sections for axial member load, core-normal reaction, handling moment and screw-head bearing; avoid copying the previous M5 arm. | Arm thickness, ribs and transition |
| Profile saddle | Derive clearance and bearing support from the measured profile while keeping load off the diffuser and avoiding wall crush. | Saddle geometry |
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

## Verifiable predicates after geometry authorization

- [ ] One valid connected arm solid in its declared +Z print pose, seated on
  `z=0`, with no avoidable support demand.
- [ ] The nominal 28 × 28 mm key and two screw axes seat in the accepted core
  without collision or duplicated clearance.
- [ ] Both screws have through clearance, washer/head bearing, driver approach,
  nominal engagement and no bottoming.
- [ ] Actual root/beam sections pass the documented sustained and short-event
  screens after every hole and relief is cut.
- [ ] The measured profile envelope has supported bearing surfaces and clearance
  without diffuser contact or thin-wall interference.
- [ ] External cable, bend, connector and hand/tool corridors remain open beside
  one seated arm and the accepted core.
- [ ] Edge survey contains only intentional seams; functional lead-ins and
  exposed print edges are treated.

## Visual review

- **Views to show:** Arm-only isometric, top, side and profile-end views; one arm
  seated in one accepted core branch; root fastener section; root/rib section;
  saddle/profile section; external cable/service corridor.
- **What the views let the human judge:** Root bulk, transition into the beam,
  relationship to the accepted organic core, profile support, future keeper
  lands, cable access and print orientation.
- **Artifact:** To be named when the boundary above is confirmed and geometry is
  implemented.

## Acceptance gate

- **Accepted upstream core:** On 2026-09-21 the user reviewed the interactive
  artifact and five-view sheet and replied **“Looks good, go ahead.”**
- **Core proof retained:** `uv run check led_profiles.stella.core` passed before
  commit `fff2f9c`; deliberate notch, blocked-bore and thin-floor defects were
  rejected. Ruff and ty passed.
- **Human feedback requested now:** Confirm whether this slice should deliver a
  complete arm through its open profile saddle and arm-side keeper lands, with
  the removable keeper itself still deferred.
- **Current-slice acceptance signal:** Pending explicit boundary confirmation.
- **Geometry authorization:** Pending that confirmation; no arm source or public
  registration exists yet.
- **Next slice after arm acceptance:** The separate removable profile keeper.
