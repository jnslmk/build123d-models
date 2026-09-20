# CAD contract — Stella core sizing

> **Current slice:** Unshifted Stella vertex core body.
> **Requirement source:** [Stella specification](stella-specification.md).
> **Status:** Definition accepted; dimensional sizing and production geometry are
> pending. Existing round-core geometry is not evidence for this slice.

## References

- **Context:** [LED profile model language](../CONTEXT.md)
- **Specification:** [Stella redesign specification](stella-specification.md)
- **Supporting evidence:** [Stella analytical basis](stella-analytical-basis.md)
- **Re-entry and tight loop:** [Stella re-entry index](stella-cad-contract.md)

## Current slice

- **Name:** Stella core body — unshifted tetrahedron.
- **Anchor part:** The vertex core body receiving three separate profile arms.
- **Purpose and print pose:** Join three branch load paths in a compact coherent
  body. The accepted production print orientation must be selected for layer
  strength and re-seat the part on `z=0`; concept-sheet presentation pose is not
  that decision.
- **In scope:** Size and review the core silhouette, material distribution,
  structural reservations, print pose, and core-only predicates.
- **Deferred interfaces:** Arm mating geometry, screws/inserts/nuts, profile
  keepers, cable cuts, suspension hardware, and the offset core constrain this
  body only. No dependent geometry is authorized in this slice.

## Applicable specification constraints

| Requirement | Consequence for this slice |
| --- | --- |
| `STELLA-CORE-01` | Build a buttressed organic-Y core; retain broad blended roots rather than a circular puck or slender profile-capture collar. |
| `STELLA-JOINT-01` | Reserve three broad, flat arm seats with structural continuity around the eventual two-M3 insert regions; do not size or model their mating geometry yet. |
| `STELLA-PROFILE-01` | Respect a slim, non-invasive profile-capture boundary while keeping the core roots structurally substantial. |
| `STELLA-CABLE-01` | Reserve a plausible side-loading cable path without cutting or modelling the final route. |
| `STELLA-SUSPENSION-01` | Preserve the four-upper-core bridle architecture and its clearance consequences. |
| `STELLA-SUSPENSION-02` | Reserve material for a rounded primary-sling opening; no final webbing geometry or safety hardware belongs in this slice. |
| `STELLA-USE-01` | Size against explicit ABS, orientation, temperature, and duration assumptions rather than historical ASA inputs. |
| `STELLA-SERVICE-01` | Preserve future lamp, cable, fastener, and tool access; final service steps are deferred. |
| `STELLA-EVIDENCE-01` | Present assumptions and limits as estimates, never as an overhead rating or no-breakage proof. |

## Evidence-backed inputs

These are source-backed inputs, not approved dimensions for the redesigned core.
Unknown manufacturing tolerances remain unknown.

| Input | Value and tolerance | Evidence/source | Applies to |
| --- | --- | --- | --- |
| Profile envelope / wall | 26.1 × 30.5 mm / 0.5 mm; tolerance not recorded | `../config.py`; `../README.md` profile table | Reserve the lamp envelope; avoid denting aluminium or loading the diffuser. |
| Lamp length | 1500 mm full stick; cut tolerance not established | `../config.py`; `../README.md` | Leverage, closure tolerance, and handling. |
| Branch directions | Three directions at 120° in the core plane | Existing `../stella_core.py` and assembly layout | Comparison basis, not new attachment geometry. |
| Cable | Nominal OD 6.7 mm; fixed-install bend radius 26.8 mm | `../mount_config.py`; `design-notes.md` §2 | Side loading and cable reservation. |
| Cable connector | Current SP16 envelope Ø21 × 45 mm; README also permits SP17 | `../mount_config.py`; `../README.md` | Exact selected hardware and coupling clearance remain open. |
| Existing core / arm | Cores about Ø99 / Ø149 × 10 mm; saddle 36 mm; keeper band 10 mm | Current README | Comparison only, never a redesign minimum. |
| Existing hardware | M5 × 25 arm-to-core; two M4 × 16 per keeper | `../stella_config.py`; current README | Existing implementation only. |
| Existing load basis | 0.65 kg per lamp × 12 = 7.8 kg; about 76.52 N static weight; preliminary 250 N per hub | `../stella_config.py`; analytical basis | Assumed lamp mass, not a weighed redesign load case. |
| User M3 inserts | M3 thread; Ø4 mm outer diameter; 5 mm length; knurl/tolerance unknown | User inventory; analytical basis | Envelope is known; generic larger-insert pilot guidance does not apply. |

## Current technical definitions

A resolution that changes an accepted requirement returns to `grill-with-docs`
and the specification. The following are engineering definitions for this slice
or later dependent slices, not reopened architecture.

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Load cases and limits | State mass allowance, bridle angles, unequal sharing, handling moments, and calculation margin. | Core section and joint sizing. |
| ABS and print basis | Establish print orientation, temperature, and creep derating assumptions. | Core sections, bosses, and preload estimate. |
| Core envelope and depths | Derive around the selected architecture and reservations, then present the core alone. | Production anchor review. |
| M3 stack and insert installation | Select exact screw/head/washer/pilot details from the eventual joint stack. | Final joint and core seat dimensions. |
| Sling opening | Choose actual webbing, then derive opening, contact, and ligament dimensions. | Core central reservation. |
| Side-load cable route | Reserve the route now; prove bend, access, and edge protection later. | Core reservation and cable slice. |
| Profile capture and service | Validate retention, thermal growth, frame closure, tool access, and extraction in later slices. | Arm/keeper and cable approvals. |

## Required eventual service constraints

This sequence is a later proof target, not an approved procedure:

1. Install inserts or captive hardware while the loose core is accessible.
2. Support the frame independently during assembly or service.
3. Bring each terminated cable into its edge-open route while locating an arm.
4. Seat and fasten arms with head, driver, and any nut access available.
5. Capture each profile without loading the diffuser or crushing its wall.
6. Support the affected structure, remove the relevant hardware, and extract one
   lamp without dismantling neighbouring vertices or cutting its cable connector.

## Required skills

| Concern | Skill | Why it applies now |
| --- | --- | --- |
| Slice boundary | `cad-iteration` | Anchor-only work and explicit acceptance. |
| Requirement changes | User-invoked `grill-with-docs` | Owns the glossary, specification, and any earned ADR. |
| Reversible form discussion | Sketch workflow | Compare shape before making production geometry. |
| Core proof | `build123d-geometry-ops` | Governs reliable edge operations and physical predicates. |
| Later arm joint | `fasteners-and-inserts`, `part-joints` | Governs hardware and mating geometry after this slice. |
| Later cable route | `fdm-fits-and-clearances` | Governs clearances after cable geometry is in scope. |

## Verifiable predicates

- [x] The selected architecture and its evidence limits are recorded in the
  specification — **proof:** [Stella specification](stella-specification.md).
- [ ] The production core is a complete solid in its selected print pose and
  re-seated on `z=0` — **proof:** targeted solid and placement checks.
- [ ] Each branch root, future arm-seat envelope, cable reservation, and sling
  reservation retains a documented structural load path — **proof:** section
  measurements and named geometry predicates after sizing.
- [ ] Estimates name ABS, orientation, temperature, load-sharing, and uncertainty
  assumptions — **proof:** calculation record linked from this contract.

No rendered concept, calculation, or B-rep check qualifies the redesign for
overhead use or proves no-breakage, creep capacity, or safety-arrest behavior.

## Visual review

- **Views to show:** Isometric, top, and right views of the sized unshifted core.
- **What the views let the human judge:** Organic-Y silhouette, branch depth,
  material distribution, access-space reservations, and print pose. They do not
  approve arm, screw, sling, cable, or assembly geometry.
- **Artifact or render:** Produce after the sized core exists, following the
  post-update verification workflow.

## Acceptance gate

- **Specification acceptance:** The user accepted the Stella definition on
  2026-09-20; this did not accept production geometry.
- **Human feedback requested:** Accept or refine the sized, unshifted core body
  alone against this contract.
- **Acceptance signal:** Pending — record the exact explicit acceptance or
  instruction clearly approving this named slice.
- **Next slice after acceptance:** One arm-to-core connection carrying the agreed
  two-M3 architecture. Arm/keeper, cable, offset-core, and assembly work remain
  separate slices.
