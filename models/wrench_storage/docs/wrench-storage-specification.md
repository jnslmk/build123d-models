# Wrench-storage specification

> **Scope:** Storage of the user's six WORKZONE double-open wrenches in a
> Gridfinity bin, with an eventual separate removable stackable lid.
> **Status:** Accepted definition; bin geometry acceptance pending.
> **Authoritative for:** User-accepted design requirements for this subject.
> **Does not authorize:** Geometry, dimensions or a dependent interface outside
> the [active bin CAD contract](bin-cad-contract.md).

## Purpose

Store and retrieve the complete six-wrench set compactly on a Gridfinity
baseplate, keeping the tools upright on their narrow edges rather than laid
flat. Reduce occupied cells and unnecessary plastic without losing support or
access. A later removable lid will permit covered, stackable storage.

## Accepted requirements

| ID | Requirement | Source or rationale | Consequence |
| --- | --- | --- | --- |
| WS-01 | Store exactly the six WORKZONE double-open wrenches marked 16/17, 14/15, 12/13, 10/11, 8/9 and 6/7 mm. | User-approved purpose; the supplied photo identifies this set. | Configuration contains all six, biggest first; changing column size does not omit tools. |
| WS-02 | Wrenches stand on their narrow edges, longitudinal axes parallel. | User-approved arrangement. | Photo face outlines become longitudinal/vertical profiles; measured thickness sets transverse spacing. |
| WS-03 | Each column uses two transverse racks with individual open-top handle slots. | User-approved support scheme. | Both racks must support all tools in their column at handle-only stations and permit drop-in/lift-out use. |
| WS-04 | Minimize occupied whole Gridfinity cells; support connected stepped footprints when unequal column lengths save cells. | User-approved space-saving requirement. | Size each column for its longest wrench and connect the columns; do not fill absent cells merely to make a rectangular bounding box. |
| WS-05 | Print the bin in PETG with a lightweight base. | User-approved material and economy requirement. | Use the project's PETG free-fit baseline; preserve continuous printable load paths while hollowing unnecessary base material. |
| WS-06 | Default to six wrenches per column; allow integer values 1–6 to re-group the complete set into columns. | Approved configuration requirement. | Use consecutive biggest-first groups with a shorter final group when needed; lay out every supported value. |
| WS-07 | Provide a separate removable stackable lid eventually. | User-approved covered-storage requirement. | Keep lid requirements recorded, but defer lid, closure and stacking-interface geometry until the bin gate passes. |
| WS-08 | Treat the bin alone as the current anchor; obtain explicit human acceptance before dependent geometry. | User-approved core-first boundary. | The open bin must be reviewable without a lid; a request to continue is not acceptance. |
| WS-09 | Keep the tools accessible when the lid is removed. | Parent's reference-design clarification: open low-walled tray with exposed heads. | Derive a low body rim and only the rack heights needed for support; do not bury the closely spaced heads behind full-height bin walls. |

## Boundaries and non-claims

- Approval of this definition is not approval of the bin's current or future
  geometry. The active contract owns the pending acceptance state.
- The A4-confirmed photograph establishes approximate face silhouettes and
  envelopes, not jaw accuracy, a load rating, calibrated dimensional tolerances
  or physical fit. Small shadow fringes remain in the trace.
- Head/handle thicknesses are user measurements; no measurement tolerance was
  supplied. The model does not claim metrology-grade values.
- One column in five cells is the dimensional default candidate, not a promise
  of minimum assembled height or a tested print. The cover may be taller than
  the tray; no lid/interface dimensions are accepted here.
- Lightweight does not mean floating rack roots, disconnected solids or
  unsupported long bridges. No magnets, labels, hardware, snaps or other
  unrequested features are established by this specification.

## Open technical definitions

| Question | Why it remains open | Resolution path | Blocking effect |
| --- | --- | --- | --- |
| Exact tray/rack heights, seating height and lightweight load path | Geometry has not been built or accepted; hollow feet change where racks can root. | Derive and prove within the active bin contract, then show the anchor. | Blocks bin acceptance, not evidence/configuration delivery. |
| Actual drop-in fit and uncertainty of the photo envelope | Photo scale, tool elevation, corner selection, shadows and lens distortion remain uncalibrated. | Physical fit trial of the bin or a rack coupon against the real set; adjust technical sizing without changing intent. | Blocks a physical fit claim. |
| Removable lid and stacking details | Their owner, the bin, is not accepted. | Accept the bin first; open a dependent contract and load closure/fit skills before geometry. | Blocks all lid and mating-interface geometry now. |

## Evidence and decision records

| Record | What it supports |
| --- | --- |
| User confirmation of purpose/requirements and A4 sheet | Accepted intent and 297×210 mm photo reference; original ledger's scale-confirmation warning is historical. |
| User-supplied maximum head/handle thicknesses | Narrow-edge packing and handle-slot width, recorded in [evidence](evidence.md) and `config.WRENCHES`. |
| [Photo/evidence record](evidence.md) and original offline tracefinity ledger | Approximate six silhouettes, dimensional provenance and safe source-trace support bands. |
| [Bin CAD contract](bin-cad-contract.md) | Current anchor, evidence consequences and the explicit pending human gate. |

## Change protocol

Use the user-invoked `grill-with-docs` process to change an accepted requirement.
The active CAD contract cites requirement IDs and states slice-specific
consequences; it does not establish a second set of accepted requirements.
