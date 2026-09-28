# Sideways drill holder: current slice

## References

- **Context:** `models/drill_storage/wood/README.md`, `models/drill_storage/metal/README.md`, `models/drill_storage/sets.py`.
- **Specification:** [`sideways-specification.md`](sideways-specification.md), SD-1–SD-10; the three-part collar, flush ASA exterior, and removable cover detent were confirmed on 2026-09-28.
- **Review direction:** The user wants to see the complete design and iterate on it, not review the ASA seat separately. The current slice therefore presents the ASA/TPU/PETG assembly together.

## Current slice

- **Name:** Complete horizontal wood and metal holders.
- **Anchor:** Each ASA guide with its front-facing cartridge seat and broad, scalloped cover collar.
- **Dependent parts:** A removable, separately printable TPU cartridge with short gripping lands and a keyed retention bead; the foot-bearing PETG cover sliding over the ASA collar.
- **Purpose and print poses:** Store every named wood/metal bit horizontally in a 1×3 / 1×4, 5U Gridfinity holder; print the ASA base and PETG cover foot-down, and the TPU cartridge flat with through-bores along Z. Upright holders remain unchanged.

## Constraints and design evidence

| Requirement | Consequence |
| --- | --- |
| SD-1–SD-3 | Frozen X/Z layouts, one rear ASA foot and two/three forward PETG feet, with all tools horizontal and a whole-5U envelope. |
| SD-4–SD-5 | The cover encloses a shallow ASA rim in its hollow mouth, not a dovetail rail or overhanging sleeve. It withdraws along +Y after lifting the whole assembly off the baseplate. |
| SD-6–SD-7 | One full-depth receiver per cell; WOOD/METAL on PETG and twelve position-map labels on the solid ASA rear face. |
| SD-8 | ASA bores use `config.GUIDE_FIT`; TPU through-bores have 3.5 mm `LAND_H` grips and `RELIEF_FIT` behind them. Hex shanks get matching hexagonal lands. |
| SD-9 | Continuous exposed ASA side and lower bed edge through the guide-to-collar transition; preserve PETG sliding clearance. |
| SD-10 | Match a PETG retention bead to an ASA groove within the short collar overlap, with enough backing to remain printable and an axial hand-release after lifting off the baseplate. |
| `box.py`, `config.py` | Grid pitch 42 mm, body width 41.5 mm, foot depth 4.4 mm, 35 mm stack pitch, 8 mm cartridge seat, 7.68 mm TPU print and named TPU/FDM fits. |

The ASA cartridge pocket leaves 1 mm nominal outer walls before its 0.2 mm entrance bevel. The TPU cartridge takes a TPU-adjusted snug fit across X/Z and 0.32 mm axial sliding clearance; one rounded bead keys it to the left side and seats in a shallow ASA dimple. The broad ASA cover collar extends 4 mm into the PETG shell, has two-perimeter nominal walls and PETG sliding clearance, and is scalloped around every shank and the step drill's head. Both cover and collar have axial entry bevels. The cover retains the long bed, all forward feet, sockets and enlarged name lettering.

The cover's 0.30 mm PETG bead is an 8 mm-wide floor catch with an axial lead-in, seated in a 0.36 mm ASA groove with 0.8 mm of backed floor behind it. Nominal engagement beyond the sliding gap is 0.19 mm; the short, scalloped collar cannot support the upright variant's full-perimeter groove. The detent is hand-removable after lifting the complete holder off its baseplate; keep it horizontal while withdrawing the cover. Print supports under the collar must be removed from the groove before assembly. Final fit, print support removal, collar durability, TPU grip and stacking strength require printed trials.

## Verifiable predicates

- [x] Wood and metal ASA guides are single solids with only a rear foot, intact rear receiver, labelled map, and open tool guides/insert seats — leaf `check` gates.
- [x] Each TPU cartridge is a valid single solid, flat on Z=0, with twelve land/relief through-bores, one keyed bead, and no overlap with its ASA seat — TPU leaf `check` gates.
- [x] PETG covers are single foot-down solids with forward feet, intact receivers, legible names and no overlap with the seated base, insert or posed bits. The backed ASA groove seats the PETG bead without collision; axial withdrawal meets its retention barrier before the cover clears the collar — cover leaf `check` gates.
- [x] Both ASA guides carry one uninterrupted outer side face from the rear radius through the cover joint, down to the foot shoulder; the seated cover remains collision-free — base and cover leaf `check` gates.
- [ ] Physical fit/retention of TPU, ASA/PETG mating, support removal, adjacent-cell stack clearance, and load-bearing lip strength — require printed parts.

## Visual review and acceptance gate

- **Show:** Iso views of the assembled and uncovered wood and metal holders, plus guide-mouth and insert-face views. Keep the rendered artifacts in `exports/` for review.
- **Ask:** Does the complete three-part holder have the desired proportions, tool access and cover-over-base behavior? Iterate this assembled design on feedback; do not treat the rendering as a print-fit result.
