# Stella redesign specification

> **Scope:** The next generation of Stella vertex connectors and their suspended
> use. Existing round-core production geometry remains a separate implementation.
> **Status:** The functional core amendment was accepted on 2026-09-21 after
> review of the implemented 20 mm candidate. Round 1's “as recommended”
> confirmed the outline/cable changes; Round 2's “A” selected a short closed
> cord loop through the two suspension holes. The authorized next slice is one
> complete mating profile arm through its open saddle and arm-side keeper lands;
> the removable keeper remains separately gated.
> **Authoritative for:** User-accepted Stella requirements. The active
> [CAD contract](cad-contract.md) owns the profile-arm implementation slice.

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
| `STELLA-PROFILE-01` | Keep profile retention visually slim, use no drain holes, and make no permanent modification to the aluminium profiles. Shape the arm transition as a rounded, tapered continuation of the profile rather than a rectangular block, and center the keeper fastener lands vertically beneath the future keeper. | User requirement; see [ADR-0001](adr/0001-stella-unmodified-profiles.md). The user confirmed the arm-shape amendment after reviewing the first complete-arm candidate. | Retention must be non-invasive, must not load the diffuser or crush the thin wall, and should reserve flat material only where bearing, fastening, or print support requires it. |
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
| Load cases and limits | Existing static targets do not resolve node vectors, handling moments, unequal sharing, or safety engagement. | State conservative assumptions and calculation margins. | Arm/joint sizing and later assembly proof. |
| ABS and print basis | A four-week allowable for the actual printed joints is not established. | Record material, orientation, temperature, and creep assumptions. | Arm sections, bosses and preload estimates. |
| M3 stack and insert installation | The accepted core uses a provisional M3 × 12 / 7.5 mm arm / 0.5 mm washer stack and an estimated insert pilot; physical hardware remains unidentified. | Match the accepted interface, prove arm-side access and reach, then validate the real insert/pilot with a coupon. | Final arm-to-core joint and physical qualification. |
| Suspension qualification | The accepted core fixes the two-hole geometry, but cord contact, knot/tail behaviour, movement, abrasion and capacity remain unqualified. | Retain the accepted geometry and resolve physical rigging outside the arm slice. | Physical suspended use, not arm CAD. |
| External electrical-cable route | The core has no notches, but connector choice, protection and the complete arm-side bend/service path remain unresolved. | Prove side access around the accepted core and arm, then complete routing in assembly. | Arm envelope and later assembly proof. |
| Arm and keeper boundary | The authorized arm slice includes the accepted core-side key, two-M3 connection, structural transition and beam, one open profile saddle, arm-side keeper lands and external service clearances. The removable keeper is deferred to the next separately gated slice. | Implement and review the complete arm before defining keeper geometry. | Arm geometry is authorized; keeper geometry remains blocked pending arm acceptance. |
| Non-invasive profile capture | Axial retention, thermal growth, frame closure, and crossing clearance remain unproven. | Design and assess the arm/keeper interface without drilling or crushing the profile. | Profile retention geometry. |
| Service sequence | Service intent is accepted; the actual order and tool paths are not. | Prove access during joint, arm/keeper, and cable slices. | Assembly and replacement approval. |

## Evidence and decision records

| Record | What it supports |
| --- | --- |
| [LED profile context](../CONTEXT.md) | Physical vocabulary used by this specification. |
| [Analytical basis](stella-analytical-basis.md) | Existing pose, illustrative load sensitivity, ABS limitations, and insert-host guidance. |
| [ADR-0001](adr/0001-stella-unmodified-profiles.md) | Non-invasive profile boundary. |
| [ADR-0002](adr/0002-stella-seated-m3-arm-joints.md) | Accepted broad-seat, two-M3 joint architecture. |
| [CAD contract](cad-contract.md) | Accepted core interface and current mating-profile-arm definition boundary. |

## Change protocol

Use the repository `grill-with-docs` interview to add, change, or remove an
accepted requirement. The CAD contract references these IDs and records only
their current-slice consequences; it does not duplicate the specification.
