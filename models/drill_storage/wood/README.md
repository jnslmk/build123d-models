# drill_storage.wood

Gridfinity storage for a **brad-point wood drill set**: eleven drills, 2 – 10 mm
(2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10), plus a 10 mm countersink on a 6.3 mm hex
shank.

The separate **1×3×5U sideways holder** has three prints: an ASA guide on the
rear foot, a removable TPU shank-gripping cartridge, and a PETG side-opening
cover carrying the long bed and two forward feet. WOOD is engraved on the cover;
the ASA back wall maps every drill size and CSK to its guide position. A short
grip land in each TPU through-bore holds the shank; the ASA bores guide freely.
The keyed TPU bead seats in a shallow ASA pocket. Print the cartridge flat,
with its relieved face on the bed and its grip lands upward.

The cover slides **over a continuous ASA collar** along the drill axes. A
ramped 0.30 mm PETG bead runs around its full mouth perimeter, including the
rounded corners, and seats in the matching ASA groove with 0.19 mm nominal
engagement and 0.17 mm radial groove relief. The collar retains its outer
dimensions with a continuous 1.16 mm wall (0.36 mm groove plus 0.8 mm backing);
the tool layout is repacked to clear it. Reprint the base, TPU cartridge and
cover together: the revised bore positions do not match the old cartridge.
This replaces the short floor catch, as confirmed on 2026-09-30. Lift the
assembled holder off its baseplate before pulling the foot-bearing cover
sideways; keep it horizontal while opening. Print the ASA
base and PETG cover foot-down, with slicer supports under the ASA rear roof and
collar overhang and the PETG long roof. Clear supports from the entire groove
and bead ring before assembly. Retention and hand-release force remain
unverified until a physical print trial.

The ASA guide's exposed side and lower bed edge stay flush across the cartridge
seat and into the cover joint; the sliding cover clearance remains inside.
Three full-depth top receivers seat another holder's feet at a 5U stacking
pitch. The 42 mm thin-lipped receivers, adjacent-cell clearance, TPU grip,
cartridge catch and cover retention still require a physical print trial.
See the [sideways-holder specification](../docs/sideways-specification.md) and
[current CAD contract](../docs/sideways-cad-contract.md). The upright parts
below remain unchanged.

```bash
uv run show drill_storage.wood            # assembled, drills standing in it
uv run export drill_storage.wood.base    # ASA
uv run export drill_storage.wood.insert   # TPU
uv run export drill_storage.wood.cover    # PETG
uv run export drill_storage.wood.cover_stackable  # PETG stacking alternative
uv run check drill_storage.wood
uv run export drill_storage.wood.sideways.base    # ASA rear guide
uv run export drill_storage.wood.sideways.insert  # TPU grip cartridge
uv run export drill_storage.wood.sideways.cover   # PETG foot-bearing cover
uv run view drill_storage.wood.sideways           # assembled inspection scene
uv run show drill_storage.wood.sideways.preview   # exposed horizontal drills
uv run check drill_storage.wood.sideways.base
uv run check drill_storage.wood.sideways.insert
uv run check drill_storage.wood.sideways.cover
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| Base | `drill_storage.wood.base` | ASA | foot down, cavity up |
| Cartridge | `drill_storage.wood.insert` | TPU | top face down, bores down |
| Cover | `drill_storage.wood.cover` | PETG | pillow top down, mouth up |

**Cover: 109 mm**, for a 133 mm (19U) assembled envelope. The 121 mm 10 mm drill
picks it and clears the cap by about 3 mm; a longer drill would cost a whole
Gridfinity unit.

**Stackable cover: 113.4 mm** (137.4 mm = 19U + 4.4 mm assembled).
Its experimental 42 mm-wide lip seats the whole 4.4 mm of the unchanged
1×1 foot for a 19U stacking pitch, retaining the snap and drill clearance.
Print mouth-up with the built-in lattice under the socket, then break it out
and remove the four nibs before stacking. The lip mouth's ~0.14 mm nominal
wall and zero nominal gap to an adjacent 42 mm cell require a printed fit
and durability trial. The smooth 109 mm cover remains the support-free,
41.5 mm-wide option; see the
[stackable-cover specification](../docs/stackable-cover-specification.md).

The countersink is packed by its 10 mm head — which stands above the tray rather
than dropping into it — and bored as a hex socket for its 6.3 mm shank. It swaps
places with the 10 mm drill so it lands at a row edge rather than in the centre
slot; the two footprints are within 0.2 mm, so the trade costs no wall.

Sizes, lengths and the cover label are `sets.WOOD`. The clearances, the geometry
and the argument behind both are shared with the other two variants — see
[the family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).

**Check the small drills against your own bits.** The grip land sits at world
z 29.2 – 32.7. On the brad-point lengths this set assumes, every size grips plain
shank with room to spare; on stubby jobber lengths the 2 mm would be gripped
partly on its *flutes*, whose hardened spurs broach a grip feature away
permanently. The table is in the design notes.
