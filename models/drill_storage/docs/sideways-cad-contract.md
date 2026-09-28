# Sideways drill holder: current slice

## References

- **Context:** `models/drill_storage/wood/README.md`, `models/drill_storage/metal/README.md` and `models/drill_storage/sets.py`.
- **Specification:** [`sideways-specification.md`](sideways-specification.md), SD-1–SD-7.
- **Supporting evidence:** `sets.WOOD` and `sets.METAL` tool lengths; `box.py` Gridfinity pitch, pad, foot height and 7 mm height unit; `bin/base.py` body-envelope convention.

## Current slice

- **Name:** Sideways cover set name and base tool-size map.
- **Anchor part:** The ASA rear guide's labelled back wall; the already accepted PETG cover retains its set-name lettering.
- **Purpose and print pose:** Let a person identify every horizontal bit in the 1×3 / 1×4 holder, while both halves stay foot-down and stack at the same 5U pitch.
- **In scope:** One legible label per guide, including the countersink/tap/step identifiers; remove the base set name, preserve the cover label, sockets, mating and printable walls.
- **Deferred interfaces:** A separate TPU shank grip, if prints demonstrate it is needed; no grip geometry is committed in this slice.

## Applicable specification constraints

| Source | Consequence |
| --- | --- |
| SD-1 | New entries, without rotating or changing the upright models. |
| SD-2 | Every stored drill has a horizontal long axis; the printed part remains foot-down. |
| SD-3 | Try 1×3×5U independently for each set; enlarge length to four cells and/or height to 6U only on demonstrated packing failure. |
| SD-4 | The cover pulls along the tool axes and exposes every bit; the guide/cover joint must locate and retain the cover without blocking the guide mouths. |
| SD-5 | Keep only the rear Gridfinity foot under the anchor; all forward feet and the long tool bed belong to the removable cover. Opening happens after lifting the assembled holder out of its baseplate. |
| SD-6 | Rear receiver belongs to the guide; all other receivers belong to the cover. The 4.4 mm raised lips must align on a 42 mm grid, retain the roof beneath the sockets, and seat matching feet without collision. |
| SD-7 | Keep only WOOD / METAL on the cover. Project each guide's size or tool identifier onto the opposite, solid ASA rear wall as a compact position map; clamp labels inside its rounded corners, avoid overlapping glyphs, and preserve the 2 mm back wall. |

## Evidence-backed dimensions

| Dimension | Value | Source | Applies to |
| --- | --- | --- | --- |
| Grid pitch; body pad width | 42 mm; 41.5 mm in a single cell | `box.GRID`, `box.PAD` | Both |
| Three/four-cell body length | 125.5 / 167.5 mm | `bin/base.py` envelope formula | Both |
| Wood longest drill | 121 mm | `sets.WOOD` 10 mm brad-point | Wood |
| Metal longest drill | 132 mm | `sets.METAL` 10 mm twist drill | Metal |
| Height target/alternate; foot | 35 / 42 mm; 4.4 mm foot | `box.HEIGHT_UNIT`, `box.BASE_H` | Both |
| Step-drill maximum diameter | 20 mm | `sets.METAL` | Metal |
| Cover wall/roof; guide/cover seam | 1.0 / 1.0 mm PETG; 0.22 mm axial | `sideways_cover.py`, `fits.SLIDING` | Both |
| Rail/sleeve | Centre x=4 mm; ASA rail y=rear+26–40 mm, PETG tongue y=rear+23.5–43.5 mm; `fits.SNUG` groove | `sideways.py`, `sideways_cover.py` | Both |
| Full stacking seat; outer lip | 4.4 mm deep; 42 mm wide; socket floor z=35 mm | `box.py` shared stack profile, `sideways.stacking_receiver` | Every cell |
| Cover label / base tool map | 12 mm nominal bold cover name (~9 mm actual, 0.5 mm PETG recess); unchanged 4.2 mm nominal bold base glyphs (≥3 mm actual), 0.8 mm ASA recess leaving 1.2 mm back wall | `sideways.engrave_set_name`, `sideways.tool_map_glyphs` | Both |

The wood length leaves only 2.5 mm within a 1×3 footprint after 1 mm end walls; metal's 132 mm drill requires 1×4. Both full sets fit 5U below the raised sockets: the leaf guide gates report a 1.60 mm minimum nominal tool-envelope gap for each set, and the narrowest guide-mouth ASA wall is 0.91 mm (wood) / 0.81 mm (metal). The latter is only just above two 0.4 mm perimeters and needs a print trial. Frozen bit positions in `sideways.py` are checked against the set dimensions in `sideways_checks.py`.

The rear guide's 1 mm roof and two side walls extend to the first cell boundary above the open tools and the low rail. Its socket belongs to the ASA half; the PETG roof begins just beyond that boundary and has one receiver per forward foot. All sockets have the existing full-foot profile and their intact 5U roofs form their floors. The raised 42 mm lips are an intentional thin-wall exception: chamfering their upper rim would erase the nominal 0.14 mm mouth wall. Other sharp edges at the new ASA roof seam and forward sleeve are closure/support boundaries; the new engraved glyph mouths remain square to retain legibility. The ASA roof extension and PETG long roof need slicer supports in print pose.

The leaf gates confirm one solid per half in foot-down pose, a full foot seating at every cell without overlap, an open guide for every set member, and no forward foot under the ASA half. Cover gates confirm that posed tool solids do not intersect the seated cover, that the rail/sleeve mate without overlap, and that 5–18 mm withdrawal is unobstructed. The ASA base's 12 labels map the projected guide centres onto its solid rear face, clamped off the rounded corners; the metal 1.5 label moves 1.3 mm inward to clear the 6 label. Per-character geometry probes confirm recessed ink, solid backing and separate printable footprints. Rendered exterior front views show all tool names; the PETG side still reads WOOD / METAL. These gates do not establish physical fit, stack loading strength, or actual printed lettering quality.

## Open technical definitions

| Question | Resolution path | Blocking effect |
| --- | --- | --- |
| Side-access architecture | Implemented with a low ASA rail and PETG friction-fit sleeve below the tools. The cover owns every forward foot and must slide off +Y after the holder is lifted out of the baseplate. There is no positive latch. | Physical print required to verify easy reopening and adequate frictional retention. |
| Actual tool length/diameter deviations and printable clearances | Use `sets.py` nominal dimensions and named FDM fits for geometry; validate physically on prints. | Physical-fit caveat, not a reason to redefine the accepted set. |

## Service and assembly constraints

1. All original set members, including CSK / TAP / STEP, must remain accessible without disturbing or damaging another tool.
2. The 20 mm metal step drill must not foul neighbouring bits or the holder wall.
3. Lifting the assembled holder off the baseplate before sliding the foot-bearing cover is mandatory; no lateral travel is possible while the cover's feet remain engaged.

## Required skills

| Concern | Skill | Why |
| --- | --- | --- |
| Print fit and clearance | `fdm-fits-and-clearances` | Bit supports and mating parts require sized clearance. |
| Edge treatments and proof | `build123d-geometry-ops` | Print edges and physical geometry checks. |
| Dependent interfaces | `cad-iteration` | Accept the supporting body before designing its dependants. |

## Verifiable predicates

- [x] Complete nominal tool envelopes fit inside each 5U cross-section without mutual overlap — physical layout gate; wood 1×3, metal 1×4.
- [x] One rear foot and every guide bore, with no forward foot on the ASA half — both leaf gates.
- [x] Full-depth seats in all three/four top cells with solid floors and matching-foot nonintersection at a 5U stack pitch — both base and cover leaf gates; print trial pending for strength and adjacent-cell fit.
- [x] Cover says WOOD / METAL in enlarged ≥8 mm actual-height glyphs and ASA base maps all 12 tool sizes/identifiers at the rear face — rendered cover and both base exterior views; gates verify every glyph face is recessed with solid backing and each label stays within its printable face. Physical print legibility pending.
- [ ] Individually accessible and retained tools with side-opening cover — BRep checks establish mating, withdrawal and no tool/cover interference; human review and physical print trial remain before accepting the slice.

## Visual review

- **Views to show:** Enlarged WOOD/METAL cover lettering and the unchanged wood and metal ASA back-wall maps seen from outside.
- **What the views let the human judge:** Cover name size versus the available side wall and unchanged size-map readability.
- **Artifacts:** `exports/drill_storage.{wood,metal}.sideways.cover_right.png`, `exports/drill_storage.{wood,metal}.sideways.base_front.png`, `exports/drill_storage.{wood,metal}.sideways.html`.

## Acceptance gate

- **Human feedback requested:** Review the rear-face map and set-name cover; print one ASA/PETG pair to judge lettering, roof/support removal, lip strength, adjacent-cell fit, rail friction and actual drill fit before accepting this slice.
- **Acceptance signal:** User accepted doubling the cover's nominal lettering size without changing SD-7's purpose or the base size map on 2026-09-28; SD-6 stacking and previous rear-guide anchor acceptance remain.
- **Next slice after acceptance:** Optional TPU grip only if needed after fit/retention review.
