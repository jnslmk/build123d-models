# Sideways drill holder: current slice

## References

- **Context:** `models/drill_storage/wood/README.md`, `models/drill_storage/metal/README.md`, `models/drill_storage/sets.py`.
- **Specification:** [`sideways-specification.md`](sideways-specification.md), SD-1–SD-10; the three-part collar and flush ASA exterior were confirmed on 2026-09-28. The SD-10 replacement of the floor catch with a continuous full-perimeter detent was confirmed on 2026-09-30.
- **Review direction:** The user wants to see the complete design and iterate on it, not review the ASA seat separately. The current slice therefore presents the ASA/TPU/PETG assembly together.

## Current slice

- **Name:** Complete horizontal wood and metal holders.
- **Anchor:** Each ASA guide with its front-facing cartridge seat and continuous, unscalloped cover collar.
- **Dependent parts:** A removable, separately printable TPU cartridge with short gripping lands and a keyed retention bead; the foot-bearing PETG cover sliding over the ASA collar.
- **Purpose and print poses:** Store every named wood/metal bit horizontally in a 1×3 / 1×4, 5U Gridfinity holder; print the ASA base and PETG cover foot-down, and the TPU cartridge flat with through-bores along Z. Upright holders remain unchanged.

## Constraints and design evidence

| Requirement | Consequence |
| --- | --- |
| SD-1–SD-3 | Repack shared X/Z layouts for the continuous collar: wood positions shift slightly; metal requires rearranging several tools. Preserve every tool, 1.4 mm tool gaps and at least 0.11 mm clearance above the 1.6 mm raised bed. Keep one rear ASA foot and two/three forward PETG feet, horizontal tools and a whole-5U envelope. |
| SD-4–SD-5 | The cover encloses a shallow ASA rim in its hollow mouth, not a dovetail rail or overhanging sleeve. It withdraws along +Y after lifting the whole assembly off the baseplate. |
| SD-6–SD-7 | One full-depth receiver per cell; WOOD/METAL on PETG and twelve position-map labels on the solid ASA rear face. |
| SD-8 | ASA bores use `config.GUIDE_FIT`; TPU through-bores have 3.5 mm `LAND_H` grips and `RELIEF_FIT` behind them. Hex shanks get matching hexagonal lands. |
| SD-9 | Continuous exposed ASA side and lower bed edge through the guide-to-collar transition; preserve PETG sliding clearance. |
| SD-10 | Continuous ramped PETG bead and matching ASA groove around every flat and rounded corner within the short collar overlap; retain the collar's outer dimensions and a continuous 1.16 mm wall with 0.8 mm backing behind the 0.36 mm groove. Groove depth leaves 0.17 mm radial relief beyond the bead's 0.19 mm nominal engagement. Axial hand-release after lifting off the baseplate remains a physical acceptance requirement. |
| `box.py`, `config.py` | Grid pitch 42 mm, body width 41.5 mm, foot depth 4.4 mm, 35 mm stack pitch, 8 mm cartridge seat, 7.68 mm TPU print and named TPU/FDM fits. |

The ASA cartridge pocket leaves 1 mm nominal outer walls before its 0.2 mm entrance bevel. The TPU cartridge takes a TPU-adjusted snug fit across X/Z and 0.32 mm axial sliding clearance; one rounded bead keys it to the left side and seats in a shallow ASA dimple. The ASA cover collar extends 4 mm into the PETG shell with PETG sliding clearance. Its unchanged outer rounded rectangle is 39.28 mm wide, spans Z=6.11–33.89 mm and has 1.0 mm corner radii. Its continuous inner rounded rectangle is 36.96 mm wide (X=±18.48 mm), spans Z=7.27–32.73 mm and has 0.2 mm corner radii. There are no shank or step-head scallops. Minimally repacked tool coordinates are shared through `layout_for`; collar clearance uses each tool's actual envelope over Y=39–46 mm. STEP's widest 20 mm shoulder is before the collar; its maximum diameter within that axial band is 16 mm. The global full-body tool gaps remain at least 1.4 mm. Both cover and collar retain axial entry bevels. The cover retains the long bed, all forward feet, sockets and enlarged name lettering. TPU grip/bore profiles are retained, with positions following the revised shared layout; upright geometry remains unchanged.

The cover's 0.30 mm PETG bead and matching 0.36 mm ASA groove form continuous rounded-rectangle rings across all flats and corners, replacing the 8 mm-wide floor catch. The collar wall is 1.16 mm with 0.8 mm backing behind the groove. Nominal engagement beyond the sliding gap is 0.19 mm, leaving 0.17 mm radial groove relief. The axial detent center is `GRID + 2.5` mm, with a 1.1 mm lead ramp, 0.5 mm back ramp and 0.15 mm flat. Intended operation is hand removal after lifting the complete holder off its baseplate; keep it horizontal while withdrawing the cover. Clear slicer supports from the full ASA groove and PETG bead ring, including corners, before assembly. Circular hoop-strain or snap-force calculations are not force predictions for this rectangular, foot-down-printed ring: the flats, corners, local bending and print anisotropy differ. CAD clearance cannot establish hand force; final fit, retention/release force, support removal, collar durability, TPU grip and stacking strength require physical printed trials.

The continuous inner collar mouth has a 0.2 mm bevel; together with the outer
0.3 mm lead-in it leaves a 0.66 mm free rim. Reprint all three sideways parts
together because the shared bore positions have changed. Small rear-face map
offsets separate decimal labels without shifting the actual guide bores.

## Verifiable predicates

- [x] Wood and metal ASA guides are single solids with only a rear foot, intact rear receiver, labelled map, and open tool guides/insert seats; every tool clears the continuous inner collar — base and cover leaf gates.
- [x] Each TPU cartridge is a valid single solid, flat on Z=0, with twelve land/relief through-bores, one keyed bead, and no overlap with its ASA seat — TPU leaf gates at the revised shared positions.
- [x] PETG covers are single foot-down solids with forward feet, intact receivers, legible names and no overlap with the seated base, insert or posed bits. The continuous backed ASA groove seats the full PETG bead ring without collision, including rounded corners; axial withdrawal meets its retention barrier before the cover clears the collar — cover leaf gates.
- [x] Both ASA guides carry one uninterrupted outer side face from the rear radius through the cover joint, down to the foot shoulder; the seated cover remains collision-free — base and cover leaf gates.
- [ ] Physical fit/retention of TPU, ASA/PETG mating, full-perimeter support removal, hand-release force, adjacent-cell stack clearance, and load-bearing lip strength — require printed parts.

Integration evidence, 2026-09-30: all six wood/metal sideways base, insert and
cover leaf gates pass; repository Ruff and ty checks pass. The full-loop gate
samples 148 perimeter locations with three backing depths and rejects the old
floor-catch solids. The inner-mouth bevel predicate also rejects the old collar.
Metal STEP's shoulder now clears the raised bed (Z=6.23 mm versus the 6.0 mm bed);
the earlier 8.02 mm³ shoulder/floor overlap is absent in the final posed-tool gate.
Both holders retain a 1.41 mm minimum full-body tool gap.

Edge survey at the default 2 mm threshold reports wood base 86 sharp / 12
unclassifiable, wood cover 59 / 2, metal base 92 / 12, and metal cover 84 / 3.
No allow-list predicates were supplied and this is not a clean-edge certificate.
Existing square stacking/mating profiles, blind guide seats, engraving edges and
concealed shell transitions remain outside this detent revision. The new exposed
collar-mouth edges have no sharp survey hits; their bevel is physically sampled.

Updated closed and uncovered GLB inspection artifacts were built for both sets.
The closed wood and metal artifacts were opened locally; the cover-mouth and
guide-mouth PNG views were inspected. Physical retention and hand force remain
unverified until printing; this evidence is CAD verification, not user acceptance.

## Visual review and acceptance gate

- **Show:** Iso views of the assembled and uncovered wood and metal holders, plus guide-mouth and insert-face views. Keep the rendered artifacts in `exports/` for review.
- **Ask:** Does the complete three-part holder have the desired proportions, tool access and cover-over-base behavior? Iterate this assembled design on feedback; do not treat the rendering as a print-fit result.
