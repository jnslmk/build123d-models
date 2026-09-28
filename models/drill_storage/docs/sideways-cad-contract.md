# Sideways drill holder: current slice

## References

- **Context:** `models/drill_storage/wood/README.md`, `models/drill_storage/metal/README.md` and `models/drill_storage/sets.py`.
- **Specification:** [`sideways-specification.md`](sideways-specification.md), SD-1–SD-5.
- **Supporting evidence:** `sets.WOOD` and `sets.METAL` tool lengths; `box.py` Gridfinity pitch, pad, foot height and 7 mm height unit; `bin/base.py` body-envelope convention.

## Current slice

- **Name:** Foot-bearing side-opening cover.
- **Anchor part:** Shared printable PETG cover/long bed with the two wood or three metal forward Gridfinity feet; mate to the accepted ASA rear guide.
- **Purpose and print pose:** Close over the horizontal bits by sliding along −Y after the assembled holder is lifted off its baseplate; both separate parts print foot-down at z=0.
- **In scope:** A roof and front/side walls, long bit-supporting platform, forward feet, a removable rail joint to the guide, closed and open inspection scenes, and checks of the assembled fit.
- **Deferred interfaces:** A separate TPU shank grip, if prints demonstrate it is needed; no grip geometry is committed in this slice.

## Applicable specification constraints

| Source | Consequence |
| --- | --- |
| SD-1 | New entries, without rotating or changing the upright models. |
| SD-2 | Every stored drill has a horizontal long axis; the printed part remains foot-down. |
| SD-3 | Try 1×3×5U independently for each set; enlarge length to four cells and/or height to 6U only on demonstrated packing failure. |
| SD-4 | The cover pulls along the tool axes and exposes every bit; the guide/cover joint must locate and retain the cover without blocking the guide mouths. |
| SD-5 | Keep only the rear Gridfinity foot under the anchor; all forward feet and the long tool bed belong to the removable cover. Opening happens after lifting the assembled holder out of its baseplate. |

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

The wood length leaves only 2.5 mm within a 1×3 footprint after 1 mm end walls; metal's 132 mm drill requires 1×4. Both full sets fit 5U: the leaf guide gates report a 1.60 mm minimum nominal tool-envelope gap for each set, and the narrowest guide-mouth ASA wall is 0.91 mm (wood) / 0.81 mm (metal). The latter is only just above two 0.4 mm perimeters and needs a print trial. Frozen bit positions in `sideways.py` are checked against the set dimensions in `sideways_checks.py`. The cover gates check the real posed tool solids against the seated cover (no intersection for all 12 tools in either set), its continuous 5U silhouette, forward-only feet, rail/sleeve mating and collision-free 5–18 mm withdrawal. They do not establish real-world friction or grip.

The revised anchor now consists of just the rear 41.5×41.5 mm foot/pad and
rear guide, reaching 35 mm total height. `uv run check` for both leaves
confirms a single foot-down solid, an open guide for every set member and no
forward bed/foot; deliberately re-adding a forward bed makes that gate fail.
The sharp-edge surveys found **0 sharp** and **12 unclassifiable** edges per
anchor: these are periodic seams of the cylindrical bores, not measured sharp
dihedrals. The PETG cover now supports the projecting tools on its long deck; its roof and short rear tongue need slicer-generated supports during printing.

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
- [x] Revised foot-down single-cell anchor and a guide hole for every tool — both leaf geometry gates and posed-tool previews; a reintroduced forward bed fails the gate.
- [ ] Individually accessible and retained tools with side-opening cover — BRep checks establish the mating, withdrawal and no tool/cover interference; human review and physical print trial remain before accepting the slice.

## Visual review

- **Views to show:** Interactive open posed-tool scenes and closed assembled scenes for wood and metal, plus the separate foot-down PETG cover top projection.
- **What the views let the human judge:** One-foot rear guide versus the cover's forward feet, continuous bed and roof, side-opening seam, proportions and print-support burden.
- **Artifacts:** `exports/drill_storage.{wood,metal}.sideways.html`, `exports/drill_storage.{wood,metal}.sideways.preview.html`, `exports/drill_storage.{wood,metal}.sideways_iso.png`, `exports/drill_storage.wood.sideways.cover_top.png`.

## Acceptance gate

- **Human feedback requested:** Review the assembled covers and print one ASA/PETG pair to judge rail friction, roof/support removal and actual drill fit before accepting this slice or requesting a TPU grip.
- **Acceptance signal:** User confirmed the revised rear-guide anchor on 2026-09-28 and directed work on the dependent cover.
- **Next slice after acceptance:** Optional TPU grip only if needed after fit/retention review.
