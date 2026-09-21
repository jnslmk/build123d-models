# Stella redesign specification

> **Scope:** The next generation of Stella vertex connectors and their suspended
> use. Existing round-core production geometry remains a separate implementation.
> **Status:** Core amendment defined and implemented as a review candidate:
> Round 1's “as recommended” confirmed the outline/cable changes; Round 2's
> “A” selected a short closed cord loop through the two suspension holes.
> Implementation dimensions and proof remain in the CAD contract. Geometry
> acceptance is pending and no dependent slice is open.
> **Authoritative for:** User-accepted Stella requirements. The active
> [CAD contract](cad-contract.md) owns the current functional-core review slice.

## Purpose

Create a modular Stella frame from independently replaceable lamp profiles. Its
vertex connection must look structurally credible without turning the slim
profile capture into a bulky collar, and it must preserve service access for
already-terminated cables.

## Accepted requirements

| ID | Requirement | Source or rationale | Consequence |
| --- | --- | --- | --- |
| `STELLA-CORE-01` | Retain the organic Y with broad, smoothly blended roots. Use the smooth web-section outline throughout the body's height, apart from functional seat recesses and appropriate edge treatments; remove the distinct inset-buttress outline and any unnecessary perimeter ledge. A circular puck is not required. | User requested the web-section outline for the complete part and confirmed Round 1 “as recommended”. This supersedes the earlier thin-web/local-buttress distribution requirement. | The outline strategy is fixed; exact depth and remaining material around the functional features must still be sized. |
| `STELLA-JOINT-01` | Seat each profile arm on a broad, flat keyed core face with substantial shoulders and clamp it with two M3 screws into core-mounted Ø4 × 5 mm heat-set inserts. | User accepted the two-M3 arrangement; see [ADR-0002](adr/0002-stella-seated-m3-arm-joints.md). | Bearing faces and shoulders resist shear and rotation; screws clamp them. Capacity and dimensions remain open. |
| `STELLA-PROFILE-01` | Keep profile retention visually slim, use no drain holes, and make no permanent modification to the aluminium profiles. | User requirement; see [ADR-0001](adr/0001-stella-unmodified-profiles.md). | Retention must be non-invasive and must not load the diffuser or crush the thin wall. |
| `STELLA-CABLE-01` | Route electrical cables outside the core and omit all three core cable notches. Already-terminated profile cables must remain installable without threading their connectors through a closed small hole. | User requested removal of the three web-section cabling slots and confirmed external routing in Round 1. | Preserve external cable, connector and service clearance; the core has no dedicated electrical-cable passages. |
| `STELLA-SUSPENSION-01` | Retain the existing pose: four primary suspension lines from the four upper vertex cores, two per tetrahedron, to one common metal collector and overhead pickup. Keep each line within 45° of vertical. | User accepted the existing pose and bridle limit. | The 1.5 m layout reserves roughly 0.82 m above the highest core plus attachment allowance. |
| `STELLA-SUSPENSION-02` | Connect each primary line to its core through a short, closed textile-cord loop: down one rounded core hole, under the bridge between the holes and up the other, with the ends joined above the core away from the hole mouths. Keep the joining knot visible and accessible; do not use stopper knots bearing at the holes. Use one safety that bypasses the main upper connection and attaches to the common metal collector. | User confirmed knot-compatible textile cord in Round 1 and selected the separate closed-loop arrangement, option A, in Round 2. | The core carries the cord's contact loads, not stopper-knot seating loads. Cord and joining details belong in the contract; sizing must account for knot movement and unequal contact loading. The safety does not independently retain every downstream printed part or lamp. |
| `STELLA-USE-01` | Print Stella components in ABS for indoor installations of at most 28 days. | User requirement. | New estimates use an explicit ABS and print-orientation basis; existing ASA assumptions do not transfer automatically. |
| `STELLA-SERVICE-01` | Lift only at designated points, transport dismantled, and replace one lamp while the surrounding structure is independently supported. | User accepted the service and handling recommendations. | Tool, cable, and extraction access are design constraints for later slices. |
| `STELLA-EVIDENCE-01` | Use documented estimates and CAD screening, not physical qualification or professional review. | User bounded the design-review scope. | The redesign carries no no-breakage, creep-capacity, overhead-rating, or certification claim. |

## Boundaries and non-claims

The accepted architecture does not set section depth, arm-seat proportions,
insert pilots, screw lengths, suspension-hole or knot/tail dimensions,
external cable routing, retention force, or a validated service sequence.
It does not accept the existing round core, its M5 arm bolts, its cable
passages, or its preliminary 250 N per-hub target as redesign inputs.

Physical destructive tests, creep tests, safety-arrest tests, and professional
qualification are outside this definition. They cannot be implied by a rendered
model, an estimate, or a B-rep geometry check.

The functional-core review sizes the core-side seats and insert pockets,
two-hole suspension attachment, and remaining material together. Its scope,
12 mm height target and acceptance gate are recorded in the
[CAD contract](cad-contract.md), not as fixed dimensions here. The rejected
46 mm blank and preceding 22 mm featured candidate are historical evidence;
their calculations and checks do not establish minima or proof for the revision.

## Open technical definitions

| Question | Why it remains open | Resolution path | Blocking effect |
| --- | --- | --- | --- |
| Load cases and limits | Existing static targets do not resolve node vectors, handling moments, unequal sharing, or safety engagement. | State conservative assumptions and calculation margins. | Core section and joint sizing. |
| ABS and print basis | A four-week allowable for the actual printed joints is not established. | Record material, orientation, temperature, and creep assumptions. | Section, boss, and preload estimates. |
| Core envelope, depth and seat proportions | The continuous web-section outline is accepted, but its depth and seat proportions are not. | Size the actual net sections with the core-side joints and two suspension holes; evaluate the contract's height target rather than inheriting old minima. | Functional-core geometry and section adequacy. |
| M3 stack and insert installation | Insert envelope is known, but pilot, pocket depth, screw length, head, washer, and retention are not. | Derive the joint stack with exact hardware and installation evidence, together with core-side seat and insert-pocket sizing. | Core-side seat/pocket geometry and final arm-to-core joint. |
| Two-hole suspension attachment | Closed-loop routing is accepted; the selected cord's allowances, contact geometry, knot/tail envelope and remaining ligaments still need sizing. | Use the contract's documented cord candidate and joining method; derive the route and actual net sections without treating catalogue cord strength as an attachment rating. | Functional-core suspension geometry and primary-attachment screening. |
| External electrical-cable route | The core notches are removed, but connector choice, external bend path, protection and tool access sizing remain unresolved. | Preserve external side access at the revised core and prove complete routing with the later arm/assembly slices. | Local clearance screening now; complete routing remains unproven. |
| Non-invasive profile capture | Axial retention, thermal growth, frame closure, and crossing clearance remain unproven. | Design and assess the arm/keeper interface. | Profile retention geometry. |
| Service sequence | Service intent is accepted; the actual order and tool paths are not. | Prove access during joint, arm/keeper, and cable slices. | Assembly and replacement approval. |

## Evidence and decision records

| Record | What it supports |
| --- | --- |
| [LED profile context](../CONTEXT.md) | Physical vocabulary used by this specification. |
| [Analytical basis](stella-analytical-basis.md) | Existing pose, illustrative load sensitivity, ABS limitations, and insert-host guidance. |
| [ADR-0001](adr/0001-stella-unmodified-profiles.md) | Non-invasive profile boundary. |
| [ADR-0002](adr/0002-stella-seated-m3-arm-joints.md) | Accepted broad-seat, two-M3 joint architecture. |
| [CAD contract](cad-contract.md) | Current functional-core execution boundary, inputs, proof, and acceptance. |

## Change protocol

Use the repository `grill-with-docs` interview to add, change, or remove an
accepted requirement. The CAD contract references these IDs and records only
their current-slice consequences; it does not duplicate the specification.
