# drill_storage.wood

Gridfinity storage for a **brad-point wood drill set**: eleven drills, 2 – 10 mm
(2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10), plus a 10 mm countersink on a 6.3 mm hex
shank.

```bash
uv run show drill_storage.wood            # assembled, drills standing in it
uv run export drill_storage.wood.base    # ASA
uv run export drill_storage.wood.insert   # TPU
uv run export drill_storage.wood.cover    # PETG
uv run export drill_storage.wood.cover_stackable  # PETG stacking alternative
uv run check drill_storage.wood
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| Base | `drill_storage.wood.base` | ASA | foot down, cavity up |
| Cartridge | `drill_storage.wood.insert` | TPU | top face down, bores down |
| Cover | `drill_storage.wood.cover` | PETG | pillow top down, mouth up |

**Cover: 109 mm**, for a 133 mm (19U) assembled envelope. The 121 mm 10 mm drill
picks it and clears the cap by about 3 mm; a longer drill would cost a whole
Gridfinity unit.

**Stackable cover: 109 mm** (19U assembled). Same snap fit and tool clearance,
with a 2.5 mm-deep seat for another 1×1 foot on top. Print mouth-up with the
built-in lattice under the socket, then break it out before stacking. The
smooth cover above remains the support-free option; see the
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
