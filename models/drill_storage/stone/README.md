# drill_storage.stone

Gridfinity storage for a **carbide-tipped masonry set**: eight bits, 3 – 12 mm
(3, 4, 5, 6, 7, 8, 10, 12). No hex tool — a masonry set is drills, and the room
is better spent on the 12 mm.

```bash
uv run show drill_storage.stone            # assembled, bits standing in it
uv run export drill_storage.stone.base    # ASA
uv run export drill_storage.stone.insert   # TPU
uv run export drill_storage.stone.cover    # PETG
uv run check drill_storage.stone
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| Base | `drill_storage.stone.base` | ASA | foot down, cavity up |
| Cartridge | `drill_storage.stone.insert` | TPU | top face down, bores down |
| Cover | `drill_storage.stone.cover` | PETG | pillow top down, mouth up |

**Cover: 137 mm**, for a 161 mm (23U) assembled envelope — the tallest of the
three, despite the shortest drill list, because a 12 mm masonry bit runs 150 mm.

## Bores are cut to the shank, which is ground below nominal

This is the one thing that makes the stone set more than a different drill list.
A masonry bit's carbide tip is brazed across the top and stands proud of the
shank on every side — that is what lets the bit cut a hole its own shank passes
freely through. And this set's shanks are *ground down*: a reduced-shank set,
where every shank is the next-lower standard size (12 mm bit on a ~10 mm shank,
10 mm on 8, 8 mm on 6.3, 6 mm on 5, 5 mm on 4, 4 mm on 3.15). Bore to the
printed size and the land would grip air.

So every drill in `sets.STONE` carries its own measured `shank`, and every bore
— ASA guide and TPU land alike — is cut to that shank. The engraved legend still
reads the nominal size, because that is what the bit is sold as. It costs
nothing: bits go in shank-first and the tip never enters the tray.

**The shanks are measured where the caliper has been** (12, 10, 6, 5, 4 mm) and
extrapolated on the next-lower-standard rule for the rest (8, 7, 3 mm). Check
those three against your own bits before printing: bore to a shank that is
wider than modelled and the bit will not seat; one that is narrower rattles.

Sizes, lengths and the cover label are `sets.STONE`. The clearances, the geometry
and the argument behind both are shared with the other two variants — see
[the family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).
