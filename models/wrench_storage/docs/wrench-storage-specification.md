# Wrench-storage specification

> **Scope:** Storage of the user's six WORKZONE double-open wrenches in
> Gridfinity bins: the accepted low tray with separate removable stackable lid,
> an explicit lidless open tray, and a tall lidless stackable bin.
> **Status:** Accepted compact 1×5 bin and additional lidless-variant intent;
> matching lid and lidless tall-bin geometry have separate review gates.
> **Authoritative for:** User-accepted design requirements for this subject.
> **Does not authorize:** Geometry or dimensions outside the
> [accepted bin CAD contract](bin-cad-contract.md),
> [active lid CAD contract](lid-cad-contract.md) and
> [lidless CAD contract](lidless-cad-contract.md).

## Purpose

Store and retrieve the complete six-wrench set compactly on a Gridfinity
baseplate, keeping the tools upright on their narrow edges rather than laid
flat. Reduce occupied cells and unnecessary plastic without losing support or
access. The separate removable lid permits covered, stackable storage.
The lidless open variant preserves the accepted low tray and support racks.
The lidless stackable variant raises surrounding walls above every seated
wrench and adds a rim that locates the next bin, without a separate cover.
Its own lower base/feet and continuous body follow the `gridfinity-bins`
reference; it does not inherit the frozen low tray's exterior.

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
| WS-09 | Keep tools accessible above low walls in the accepted tray and explicit lidless open variant. | Parent's reference-design clarification: open low-walled tray with exposed heads; scope confirmed 2026-10-06. | Retain the low body rim and support-only rack heights in `base`/`open`; this low-wall constraint does not apply to the tall lidless variant. |
| WS-10 | Provide an explicit lidless open version retaining the accepted low tray walls and support racks. | User confirmed both variants' purpose and decision delta on 2026-10-06. | Publish `wrench_storage.open` by reusing the accepted base geometry; do not alter the existing bin or lid. |
| WS-11 | Provide a lidless stackable version with walls above all seated wrench tops and a rim locating the next bin. | User confirmed both variants' purpose and decision delta on 2026-10-06. | Publish `wrench_storage.stackable` as a tall open-mouth bin; preserve the six-tool grouping, lightweight PETG base and stepped footprints, without requiring a cover. |
| WS-12 | Implement the tall stackable bin's own base/feet and continuous walls like the reference `gridfinity-bins`, with rounded walls from the foot/body transition and a continuous stepped/chamfered locating rim rather than per-cell receivers. | User selected **“Match walls and continuous rim”**, then explicitly confirmed the replacement on 2026-10-06: **“The new agent said the spec is the same. Implement the wall and base like the references gridfinity bins at /home/jonas/git-projects/cad-and-3d/gridfinity-bins”**. | Replace inherited low-tray exterior and feet inside `wrench_storage.stackable`; do not preserve every frozen low-tray solid in this tall part. Use the actual cleaned reference base and one continuous occupied-outline body, including stepped groupings. Preserve all six tool poses, rack slots/seats, grouping and lightweight PETG load paths. Retain functional rim-access adaptations with explicit dimensions and actual mating-foot proof, not an exact-standard-lip claim. Public low `base`/family root/`open` and separate lid remain unchanged. |

## Boundaries and non-claims

- Acceptance of the definition alone did not approve geometry. The user
  subsequently selected **“Accept the 1×5 bin”** on 2026-10-03, satisfying
  WS-08's bin gate and opening the matching lid slice under its own contract.
  WS-01–08 remain unchanged; WS-09 is scoped to the low tray by the
  2026-10-06 confirmation, which adds WS-10–11 without revising the accepted
  base or existing lid geometry.
  The subsequent **“Match walls and continuous rim”** selection adds WS-12;
  the latest explicit wall-and-base instruction confirms its replacement delta,
  superseding inherited-low-tray constraints inside the tall part only. It does
  not accept the replacement geometry or alter public low parts.
- The A4-confirmed photograph establishes approximate face silhouettes and
  envelopes, not jaw accuracy, a load rating, calibrated dimensional tolerances
  or physical fit. Small shadow fringes remain in the trace.
- Head/handle thicknesses are user measurements; no measurement tolerance was
  supplied. The model does not claim metrology-grade values.
- One column in five cells is the accepted compact default with CAD/photo-envelope
  evidence in the bin contract, not a tested print or a promise of minimum
  assembled height. Optional stepped groupings are not needed to make that
  default work. Lid/interface sizing is technical implementation detail in the
  active lid contract, not an additional accepted requirement here.
- Lightweight does not mean floating rack roots, disconnected solids or
  unsupported long bridges. No magnets, labels, hardware, snaps or other
  unrequested features are established by this specification.

## Open technical definitions

| Question | Why it remains open | Resolution path | Blocking effect |
| --- | --- | --- | --- |
| Printed bin/tool fit and uncertainty of the photo envelope | Photo scale, tool elevation, corner selection, shadows and lens distortion remain uncalibrated despite the recorded CAD clearance proof. | Physical fit trial of the accepted bin or a rack coupon against the real set; adjust technical sizing without changing intent. | Blocks a physical fit claim, not the approved lid slice. |
| Printed lid fit, roof sag and support removal | CAD dimensions and modelled release gaps do not establish sliced extrusion paths or real PETG behaviour. | Use the active lid contract for CAD proof, then inspect the intended slicer profile and print representative fit/support coupons. | Blocks claims of calibrated mating fit, successful support removal or stack load capacity. |
| Printed tall-bin stacking fit and load capacity | A locating rim and CAD separation do not establish PETG fit, deflection or stability under load. | Use the lidless contract for CAD proof and visual review, then trial real printed bins. | Blocks physical stacking/load claims, not lidless CAD implementation. |

## Evidence and decision records

| Record | What it supports |
| --- | --- |
| User confirmation of purpose/requirements and A4 sheet | Accepted intent and 297×210 mm photo reference; original ledger's scale-confirmation warning is historical. |
| User-supplied maximum head/handle thicknesses | Narrow-edge packing and handle-slot width, recorded in [evidence](evidence.md) and `config.WRENCHES`. |
| [Photo/evidence record](evidence.md) and original offline tracefinity ledger | Approximate six silhouettes, dimensional provenance and safe source-trace support bands. |
| [Bin CAD contract](bin-cad-contract.md) | Frozen compact anchor, completed CAD/photo-envelope proof and explicit human acceptance. |
| User selection **“Accept the 1×5 bin”**, 2026-10-03 | Acceptance of the compact default and permission to proceed with its matching removable stackable lid; no requirement for stepped regrouping. |
| [Lid CAD contract](lid-cad-contract.md) | Active dependent slice, reversible technical sizing, centralized proof predicates and lid review/acceptance state. |
| User confirmation **“Confirm both variants”**, 2026-10-06 | Approves the lidless open reuse and tall lidless stackable purpose/delta, including WS-09 scope and WS-10–11; not visual acceptance or a printed-fit result. |
| User selection **“Match walls and continuous rim”**, 2026-10-06 | Confirms unchanged purpose and WS-12 exterior alignment for `stackable` only; permits technical clearance/stacking dimensions to change, not the accepted low tray or lid. |
| User instruction **“The new agent said the spec is the same. Implement the wall and base like the references gridfinity bins at /home/jonas/git-projects/cad-and-3d/gridfinity-bins”**, 2026-10-06 | Confirms WS-12 purpose/delta: replace the tall part's inherited low base/exterior with actual reference-style feet and continuous walls; public low parts and lid remain frozen. No renewed approval question is pending. |
| [Lidless CAD contract](lidless-cad-contract.md) | Tall-bin anchor, accepted open-bin reuse, current CAD predicates and pending human visual acceptance. |

## Change protocol

Use the user-invoked `grill-with-docs` process to change an accepted requirement.
The active CAD contract cites requirement IDs and states slice-specific
consequences; it does not establish a second set of accepted requirements.
