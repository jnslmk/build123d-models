# drill_storage.stone

Gridfinity storage for a **carbide-tipped masonry set**: seven bits, 3 – 10 mm
(3, 4, 5, 6, 7, 8, 10). No hex tool — a masonry set is drills, and the room is
better spent on the 10 mm.

```bash
uv run show drill_storage.stone            # assembled, bits standing in it
uv run export drill_storage.stone.shell    # ASA
uv run export drill_storage.stone.insert   # TPU
uv run export drill_storage.stone.cover    # PETG
uv run check drill_storage.stone
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| Shell | `drill_storage.stone.shell` | ASA | foot down, cavity up |
| Cartridge | `drill_storage.stone.insert` | TPU | top face down, bores down |
| Cover | `drill_storage.stone.cover` | PETG | pillow top down, mouth up |

**Cover: 137 mm**, for a 161 mm (23U) assembled envelope — tied with the metal
set for the tallest of the three, despite the shortest drill list, because a
10 mm masonry bit runs 150 mm (and the metal set's 10 mm twist drill does too).

## Every bore is cut 0.20 mm under its printed size

This is the one thing that makes the stone set more than a different drill list.
A masonry bit's carbide tip is brazed across the top and stands proud of the
shank on every side — that is what lets the bit cut a hole its own shank passes
freely through. Bore to the printed size and the land grips 0.20 mm of air.

So `sets.STONE` carries a `shank_allowance` of 0.20 mm, and every bore — ASA
guide and TPU land alike — is cut to `nominal − allowance`. The engraved legend
still reads the nominal size, because that is what the bit is sold as. It costs
nothing: bits go in shank-first and the tip never enters the tray.

**Measure your own set before printing.** 0.20 mm is typical over this size
range, not universal. A caliper on the shank of the 6 mm bit settles it, and one
number covers the set.

## Why it stops at 10 mm

Masonry bits above 10 mm are commonly sold with a *reduced* shank — a 12 mm bit
on a 10 mm shank, to fit a 10 mm chuck. That is a different allowance for every
size rather than one for the set, and a 12 mm legend over a 10 mm bore is a label
that lies. Add one only with its own entry.

Sizes, lengths and the cover label are `sets.STONE`. The clearances, the geometry
and the argument behind both are shared with the other two variants — see
[the family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).
