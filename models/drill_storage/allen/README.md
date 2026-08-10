# drill_storage.allen

Gridfinity storage for an **eight-piece set of 50 mm hex keys** (1.5 – 8 mm),
and one of the five top-level drill_storage sets. Two-material, like the
others: a rigid black ASA base guides each key upright and holds the
cartridge, the black TPU insert grips it on a short land, and the translucent
PETG cover snaps over the collar. The sizes are engraved into the base's body
walls, largest → smallest, so the set reads as an ordered grid.

The geometry is `drill_storage.hex`'s — the ALLEN box and the BITS driver-bit
box are cut from the same `hex.base` / `hex.insert` / `hex.cover` modules, and
this package only names the ALLEN one. The clearances, the fit classes and the
argument behind the two-material split are the drill family's — see [the
family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).

```bash
uv run show drill_storage.allen                # the box, all eight keys standing
uv run export drill_storage.allen.base         # rigid, foot down, cavity up
uv run export drill_storage.allen.insert       # TPU, flat down, bores up
uv run export drill_storage.allen.cover        # translucent, pillow top down
uv run check drill_storage.allen
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| ALLEN base | `drill_storage.allen.base` | ASA, black | foot down, cavity up |
| ALLEN insert | `drill_storage.allen.insert` | TPU, black | flat bottom down, bores up |
| ALLEN cover | `drill_storage.allen.cover` | PETG, translucent | pillow top down, mouth up |

**1x1 Gridfinity** (41.5 mm, pad, body and cover alike), eight sockets in the
family's rows, the sizes engraved on the body walls largest → smallest.

**Grip**: the cartridge's lands are cut `HEX_LAND_TIGHTEN` (0.10 mm across the
flats) tighter than the family's, because a socket here is named by `HEX_AF` —
which already carries the guide's slip clearance — rather than by the shank the
family measures from. The argument, and what to do if a key still lifts the box
or now fights you, are in [`../hex/config.py`](../hex/config.py)'s *The grip*.

**Cover**: 45 mm (63 mm / 9U assembled, about 3 mm over the longest key tip).
The base is 30 mm — the family's 36 mm is for drills that need the depth. Keys
sink **21 mm** below the rim (`ALLEN_HOLE_DEPTH`), resting on the rigid guide
floor at z = 9, and stand 29 mm proud, which is how you pinch them out. The
hole was 15 mm deep before, standing the keys 35 mm proud; sinking them the
extra 6 mm buys a whole Gridfinity unit back on the cover (9U, not 10U) and
still leaves 4.6 mm of solid body between the bores and the foot.

The sibling set, `drill_storage.hex`, is the 16-piece 25 mm driver-bit box —
same boxes, shaved clearances to fit a literal 4x4 grid — see
[`hex/README.md`](hex/README.md).
