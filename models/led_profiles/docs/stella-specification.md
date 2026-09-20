# Stella redesign specification

> **Scope:** The next generation of Stella vertex connectors and their suspended
> use. Existing round-core production geometry remains a separate implementation.
> **Status:** Accepted design definition on 2026-09-20. No redesigned production
> part or dependent interface has been accepted.
> **Authoritative for:** User-accepted Stella requirements. The active
> [CAD contract](cad-contract.md) owns only the current core-sizing slice.

## Purpose

Create a modular Stella frame from independently replaceable lamp profiles. Its
vertex connection must look structurally credible without turning the slim
profile capture into a bulky collar, and it must preserve service access for
already-terminated cables.

## Accepted requirements

| ID | Requirement | Source or rationale | Consequence |
| --- | --- | --- | --- |
| `STELLA-CORE-01` | Use concept C: a buttressed organic Y with broad, smoothly blended roots and structural depth along each branch. A circular puck is not required. | User accepted the concept after the form review. | The silhouette strategy is fixed; sketch dimensions are not. |
| `STELLA-JOINT-01` | Seat each profile arm on a broad, flat keyed core face with substantial shoulders and clamp it with two M3 screws into core-mounted Ø4 × 5 mm heat-set inserts. | User accepted the two-M3 arrangement; see [ADR-0002](adr/0002-stella-seated-m3-arm-joints.md). | Bearing faces and shoulders resist shear and rotation; screws clamp them. Capacity and dimensions remain open. |
| `STELLA-PROFILE-01` | Keep profile retention visually slim, use no drain holes, and make no permanent modification to the aluminium profiles. | User requirement; see [ADR-0001](adr/0001-stella-unmodified-profiles.md). | Retention must be non-invasive and must not load the diffuser or crush the thin wall. |
| `STELLA-CABLE-01` | Already-terminated profile cables load from the side rather than through a closed small hole. | User requirement. | The eventual route needs an edge-open loading path and preserves cable, tool, and structural clearance. |
| `STELLA-SUSPENSION-01` | Retain the existing pose: four primary suspension lines from the four upper vertex cores, two per tetrahedron, to one common metal collector and overhead pickup. Keep each line within 45° of vertical. | User accepted the existing pose and bridle limit. | The 1.5 m layout reserves roughly 0.82 m above the highest core plus attachment allowance. |
| `STELLA-SUSPENSION-02` | Connect each primary line through a short, closed sewn webbing loop passing through a broad, rounded core opening. This loop is the primary attachment. Use one safety that bypasses the main upper connection and attaches to the common metal collector. | User accepted the recommended sling and safety architecture. | The safety does not independently retain every downstream printed part or lamp. |
| `STELLA-USE-01` | Print Stella components in ABS for indoor installations of at most 28 days. | User requirement. | New estimates use an explicit ABS and print-orientation basis; existing ASA assumptions do not transfer automatically. |
| `STELLA-SERVICE-01` | Lift only at designated points, transport dismantled, and replace one lamp while the surrounding structure is independently supported. | User accepted the service and handling recommendations. | Tool, cable, and extraction access are design constraints for later slices. |
| `STELLA-EVIDENCE-01` | Use documented estimates and CAD screening, not physical qualification or professional review. | User bounded the design-review scope. | The redesign carries no no-breakage, creep-capacity, overhead-rating, or certification claim. |

## Boundaries and non-claims

The accepted architecture does not set section depths, arm-seat proportions,
insert pilots, screw lengths, sling-opening dimensions, cable routing, retention
force, or a validated service sequence. It does not accept the existing round
core, its M5 arm bolts, its cable passages, or its preliminary 250 N per-hub
target as redesign inputs.

Physical destructive tests, creep tests, safety-arrest tests, and professional
qualification are outside this definition. They cannot be implied by a rendered
model, an estimate, or a B-rep geometry check.

## Open technical definitions

| Question | Why it remains open | Resolution path | Blocking effect |
| --- | --- | --- | --- |
| Load cases and limits | Existing static targets do not resolve node vectors, handling moments, unequal sharing, or safety engagement. | State conservative assumptions and calculation margins. | Core section and joint sizing. |
| ABS and print basis | A four-week allowable for the actual printed joints is not established. | Record material, orientation, temperature, and creep assumptions. | Section, boss, and preload estimates. |
| Core envelope and seat proportions | The organic-Y architecture is accepted, but its sizes are not. | Size around load assumptions and reservations; review the core alone. | Production core geometry. |
| M3 stack and insert installation | Insert envelope is known, but pilot, screw length, head, washer, and retention are not. | Derive the joint stack with exact hardware and installation evidence. | Final arm-to-core joint. |
| Sling opening | The loop architecture is accepted, but webbing and contact dimensions are not. | Select the sling hardware, then derive opening and ligament requirements. | Core central reservation. |
| Side-load cable route | Connector choice, bend path, protection, and access are unresolved. | Validate swept cable and service envelopes in its later slice. | Core reservation and cable geometry. |
| Non-invasive profile capture | Axial retention, thermal growth, frame closure, and crossing clearance remain unproven. | Design and assess the arm/keeper interface. | Profile retention geometry. |
| Service sequence | Service intent is accepted; the actual order and tool paths are not. | Prove access during joint, arm/keeper, and cable slices. | Assembly and replacement approval. |

## Evidence and decision records

| Record | What it supports |
| --- | --- |
| [LED profile context](../CONTEXT.md) | Physical vocabulary used by this specification. |
| [Analytical basis](stella-analytical-basis.md) | Existing pose, illustrative load sensitivity, ABS limitations, and insert-host guidance. |
| [ADR-0001](adr/0001-stella-unmodified-profiles.md) | Non-invasive profile boundary. |
| [ADR-0002](adr/0002-stella-seated-m3-arm-joints.md) | Accepted broad-seat, two-M3 joint architecture. |
| [CAD contract](cad-contract.md) | Current core-only execution boundary, inputs, proof, and acceptance. |

## Change protocol

Use the repository `grill-with-docs` interview to add, change, or remove an
accepted requirement. The CAD contract references these IDs and records only
their current-slice consequences; it does not duplicate the specification.
