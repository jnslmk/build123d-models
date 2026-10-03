# Wrench bin CAD contract

## References

- **Context:** [Family README](../README.md). No new glossary is needed; the
  specification and evidence record define the working terms directly.
- **Specification:** [Accepted wrench-storage specification](wrench-storage-specification.md).
- **Supporting evidence:** [Photo normalization, thickness ledger and interfaces](evidence.md),
  `config.py`, `profiles.py` and the unchanged original
  [`exports/wrench_analysis/ledger.json`](../../../exports/wrench_analysis/ledger.json).

## Current slice

- **Name:** Open on-edge wrench bin.
- **Anchor part:** The bin alone, including its lightweight Gridfinity base,
  low surrounding walls and two slotted transverse racks per column.
- **Purpose and print pose:** Hold all six tools upright and individually
  retrievable. Print the bin base-down, bed face at `z=0`, racks/slots open
  upward; print pose takes precedence over presentation pose.
- **In scope:** Integer 1–6 wrenches-per-column grouping; minimum-cell default;
  connected stepped footprints for unequal column lengths; supported lightweight
  base; finished exposed edges; an open tool preview that communicates seating
  and access without pretending to be a measured replica.
- **Deferred interfaces:** All lid solids, skirts, snaps, receivers, mating
  grooves and stacking-interface geometry. Only a future **3 mm vertical
  headroom envelope above the highest seated tool** is reserved. The tray wall
  is not required to reach that height: the later removable cover may be taller
  than the tray. No closure type or interface geometry is chosen now.

## Applicable specification constraints

| Requirement ID or source | Consequence for this slice |
| --- | --- |
| WS-01, WS-02 | Retain all six labels and measured thicknesses; common longitudinal axes, face profiles vertical. |
| WS-03 | Exactly two rack bands per column; use only the source-backed common handle stations and full-band underside bounds. |
| WS-04, WS-06 | Default is one six-tool column; alternate grouping preserves the complete set. Keep only occupied cells and join columns at their common end. |
| WS-05 | Hollow unnecessary base material without leaving racks over an unsupported cavity. Maintain continuous load paths to the print bed. |
| WS-07, WS-08 | No dependent interface until explicit bin acceptance; 3 mm cover headroom is an envelope constraint only. |
| WS-09 | Expose the heads above a low tray rim for retrieval; derive wall/rack heights from support and access, not from covered-storage height. |

## Evidence-backed dimensions

| Dimension | Value and tolerance | Evidence/source | Applies to |
| --- | --- | --- | --- |
| Six photo lengths / face head widths | 203.80/37.60, 188.41/33.34, 172.47/29.13, 152.52/25.29, 136.87/20.53, 123.01/15.78 mm; physical uncertainty unquantified | A4-confirmed offline tracefinity ledger; see evidence record for aligned bounds | Longitudinal/vertical tool envelopes, not fits |
| Head / handle thicknesses | 6.1/4.4, 5.8/4.15, 5.5/3.65, 4.8/3.3, 4.3/3.2, 3.9/2.8 mm; supplied measurement tolerance unknown | User maximum measurements, biggest first | Transverse tool placement and slot widths |
| Gridfinity pitch / total external setback | 42.0 / 0.5 mm | Existing project Gridfinity primitives | Whole-cell footprint budget |
| Wall / lightweight bed plate | 1.0 / 1.0 mm PETG; foot-cavity XY offset is `WALL * sqrt(2)` to retain 1 mm normal thickness on 45° shoulders | `config.WALL`, `layout.BED_THICKNESS`, built-solid physical gate | Wall minimum and supported base construction |
| Tool gaps / added slot width | `fits.FREE`, currently 0.4 mm total, PETG baseline | `fdm-fits-and-clearances`; `config.TOOL_GAP`, `config.SLOT_CLEARANCE` | Drop-in head spacing and handle slots |
| Photo end reserve | 1.0 mm at each end; functional allowance, not a fit or calibrated error bar | `config.PHOTO_END_ALLOWANCE` | Longitudinal envelope |
| Support stations / rack thickness | 50.0 and 85.0 mm from common photographed end / 2.0 mm longitudinal band | Unsimplified normalized profiles; `HANDLE_STATIONS`, `HANDLE_BAND_WIDTH`, `RACK_THICKNESS` | Handle-only support |
| Slot floor bounds | `seat_z + HANDLE_SPANS[label][station_index][0] - 0.2 mm` | Full-band trace minima rounded down, plus `layout.SLOT_FLOOR_RESERVE`; a functional photo/noise reserve, not a measured contact tolerance | Tool/rack non-overlap across the full rack band |
| Future cover headroom | 3.0 mm above full seated tool envelope; functional reserve | `config.FUTURE_LID_HEADROOM` | Constraint only; not body-rim height |
| Verified default footprint | 1×5 cells: outer 41.5×209.5 mm; 39.5×207.5 mm straight inner span | Actual exported bin bounds and passing corner/wall-clearance gate | Minimum whole-cell default footprint |
| Open tray / maximum rack height | 14.0 / 19.079 mm above the bed | Actual bin bounds, low-rim predicate and section renders | Exposed heads and print pose |
| Seated photo-envelope datum / top | 5.4 / 43.011 mm above the bed | `layout.SEAT_Z`, aligned photo contours and actual preview | Nominal illustrative pose, not a measured contact solution |
| Three-per-column stepped alternative | Connected 1×5 + 1×4 cells; 83.5×209.5 mm outer bounds, nine occupied cells | Actual exported stepped bin, connectivity and containment gates | Omit the unused end cell rather than enclosing a rectangle |

Use the larger of each `Wrench` photo dimension and `PROFILE_EXTENTS` for the
corresponding envelope. Profile alignment slightly changes those bounds; it
must not silently change the user-recorded dimensional ledger.

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Photo accuracy and real slot fit | Print a rack coupon or fit the real tools in the bin; preserve provenance when adjusting technical dimensions. | Blocks a physical fit guarantee; thicknesses alone cannot validate the photographed underside. |
| Lid and stacking definition | Human accepts this named bin, then open the dependent contract and load closure/fit skills. Any change to accepted intent returns to user-invoked `grill-with-docs`. | Blocks all lid/mating-interface geometry now. |

## Service and assembly constraints

1. Tools drop into open-top slots and lift out individually, without moving a
   neighbour or disassembling the racks. Head gaps use total PETG free clearance.
2. The same photographed top end is aligned across tools and columns. Do not
   reverse a wrench while still using the common support facts.
3. Rack slot floors use the minimum underside over their **whole** longitudinal
   thickness. Rack thickness must match the evidence's 2 mm band; a wider rack
   requires new raw-trace bounds. Simplified preview data is not the source of
   contact heights.
4. All base/rack/wall regions join into one printable connected bin. Hollow
   foot cavities stay open above their bed plates; root racks to those plates
   rather than spanning a long empty cavity at the nominal cavity-floor level.
5. The bin must remain useful and reviewable with no lid present. Do not add
   side-specific locating lips or hidden dependent features for a hypothetical
   cover. Reserve the cover envelope without burying the tool heads.

## Required skills

| Concern | Skill | Why it applies now |
| --- | --- | --- |
| Purpose and accepted intent | `model-documentation` | The README/specification gate has been approved; this contract does not authorize a dependent slice. |
| Anchor and acceptance sequencing | `cad-iteration` | The bin owns later lid interfaces and must be judged first. |
| Photo provenance and limits | `photo-reverse-engineering` | Face outlines are approximate source-backed silhouettes, not fit measurements. |
| Tool gaps and handle slots | `fdm-fits-and-clearances` | Free-fit PETG values are total allowances, not guessed per-side gaps. |
| Edge treatment, joins and physical gates | `build123d-geometry-ops` | Geometry must prove wall/rack continuity, cavity roots and clearance; preview appearance is insufficient. |

Closure, snap, joint and hardware skills remain downstream unless a subsequent
accepted slice actually needs them.

## Verifiable predicates

The centralized `uv run check wrench_storage --json
exports/wrench_analysis/bin-checks.json` gate passes for settings 6 and 3:
the default five-cell bin and nine-cell stepped alternative. The layout suite
also covers every integer setting 1–6 and rejects invalid/boundary inputs.
These are CAD/photo-envelope results, not a printed-fit guarantee.

- [x] **Complete grouping:** For every integer setting 1–6, all six labels occur
  exactly once, in consecutive biggest-first groups. — **Physical proof:**
  Targeted layout assertions and correspondence of tool placement to the bin.
- [x] **Minimum default occupied footprint:** Six tools fit within the five
  occupied cells, including walls/end reserves; fewer cells fail the envelope
  lower bound. — **Physical proof:** Layout/envelope assertions and point/section
  checks of tool-to-wall/corner clearance in the actual bin.
- [x] **Connected stepped alternatives:** Occupancy omits the absent end cells
  without disconnecting the body or base. — **Physical proof:** Layout adjacency,
  occupied-cell counts and actual solid connectivity, including step joints.
- [x] **Handle-only, non-overlapping racks:** Two racks per column have measured
  handle thickness plus total free clearance; notch floors clear the underside
  across their full 2 mm bands. — **Physical proof:** Source-band facts plus
  built-solid intersections/sections and tool clearance samples.
- [x] **Supported lightweight load path:** Bed plates, rack roots and walls are
  connected; no long floating rack underside spans an open foot cavity. —
  **Physical proof:** Section/point sampling down to the bed plates, solid
  connectivity and print-pose review of bridge/overhang spans.
- [x] **Accessible open bin, CAD envelope:** Low walls and only necessary rack
  height leave heads exposed and permit individual vertical removal. —
  **Physical proof:** Actual open preview and exact continuous removal sweeps
  against the bin and every neighbour. Real-tool seating/removal remains a
  separate, unverified printed trial.
- [x] **Future envelope without interface:** The recorded future ceiling is
  46.011 mm, reserving 3 mm above the nominal photo-envelope top. —
  **Evidence only:** Derived layout value and absence of lid/mating geometry.
  This is not a physical gate or lid-compatibility proof.
- [x] **Print-ready anchor:** Base seated on `z=0`, minimum 1 mm walls maintained,
  exposed edges finished, one valid connected printable part. — **Physical
  proof:** Geometry gate and sections, not a visual-only claim.

## Visual review

- **Views to show:** Bin-only isometric; open tool-preview isometric; top view of
  the default and one stepped grouping; transverse rack section and longitudinal
  section showing rack roots down to lightweight bed plates.
- **What the views let the human judge:** Compactness, upright tool proportions,
  exposed heads, retrieval access, stepped footprint, support locations and
  print pose. Hidden clearance/continuity still requires physical predicates.
- **Artifacts:** `exports/wrench_storage.base.stl` is the printable default bin.
  `exports/wrench_storage.preview.html` shows the open bin with coloured
  photo-qualified wrench envelopes; `exports/wrench_storage.stepped.html`
  shows the three-per-column parameter snapshot. Views and sections are in
  `exports/wrench_analysis/`: `bin_iso.png`, `bin_top.png`, `open_preview.png`,
  `stepped_top.png`, `rack_section.png`, and `root_section.png`. The actual
  standalone preview was inspected in Chromium with no browser errors.
  The raw traced overlay remains measurement evidence, not bin acceptance.
- **Verification:** The physical gate passes including a filled-notch negative
  control that makes the slot-clearance predicate fail. Ruff and ty pass;
  the repository suite passes 114 tests with one skip. All 17 extracted shared
  foot/cavity comparisons lose less than `1e-5 mm³` of either original or new
  solid relative to their common volume. Continuous sweep construction retains the exact
  swept set and unions its faces once; the focused first-wrench sweep completed
  in 6.39 s after the original incremental union exceeded 94 s.

## Acceptance gate

- **Human feedback requested:** Review and explicitly accept the named **open
  on-edge wrench bin**, including its accessible head exposure, upright seating,
  support scheme, lightweight print pose and footprint. A printed fit result is
  needed before claiming physical fit.
- **Acceptance signal:** **Pending.** The user approved purpose/requirements,
  A4 paper and the bin-only anchor; that is not bin-geometry acceptance. Record
  the exact explicit acceptance or instruction clearly approving this slice.
- **Next slice after acceptance:** The separate removable stackable lid and its
  actual dependent mating/stacking interface, under a new current-slice contract.
