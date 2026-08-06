# drill_storage.metal

Gridfinity storage for an **HSS twist drill set**: ten drills on jobber lengths,
1 – 10 mm (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10), plus an M6 hex-shank tap and a
4 – 20 mm step drill on a 6.3 mm hex shank.

```bash
uv run show drill_storage.metal            # assembled, drills standing in it
uv run export drill_storage.metal.shell    # ASA
uv run export drill_storage.metal.insert   # TPU
uv run export drill_storage.metal.cover    # PETG
uv run check drill_storage.metal
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| Shell | `drill_storage.metal.shell` | ASA | foot down, cavity up |
| Cartridge | `drill_storage.metal.insert` | TPU | flat bottom down, bores up |
| Cover | `drill_storage.metal.cover` | PETG | pillow top down, mouth up |

**Cover: 123 mm**, for a 147 mm (21U) assembled envelope. The 132 mm 10 mm twist
drill is the longest tool in the whole package, so this is the family's default
cover height.

The tap drops into a hex socket for its 10 mm across-flats shank and is legended
`TAP` on the walls rather than a bare size, since it is not a drill. The step
drill gets the same treatment, legended `STEP`.

## The step drill, and why this tray has no rows

The other two sets are laid out in tidy rows by `box.pack_rows`. This one is not,
and the step drill is the reason.

Its socket is 6.3 mm, but its **body is 20 mm**, and the body is what the layout
has to reserve room for — it stands above the tray among the other bits. A row is
32.68 mm of usable span; the step drill and the tap alone want 20 + 1.1 + 11.9 =
33.0 of it. So the packer gives the step drill a row to itself, that row then
spends 20 mm of the *vertical* budget as well, and everything underneath is
crushed. Reordering does not help, and neither does dropping the small drills:
what does not fit is the tap's own 11.9 mm, not the number of holes.

Dropping the rows does fit — comfortably. `freepack.pack_free` solves the same
two constraints without the row structure, and all twelve land with a **1.75 mm
worst wall** (1.50 required) and a **1.54 mm worst gap** (1.10 required), against
the 1.27 mm the row layout managed before the step drill existed. Irregular is
not a compromise here; it is the better packing.

Its coordinates are frozen in `sets.FREE_LAYOUT` rather than re-solved on every
import. Regenerate with:

```bash
uv run python -m models.drill_storage.freepack
```

What makes them trustworthy is `checks.py`, which re-derives every wall and every
gap from the frozen numbers and fails if one is short.

### It hangs, it does not stand

Every other tool here bottoms out on the shell's ASA floor. The step drill's hex
shank is 25 mm and the socket is 31.2 mm deep, so it cannot — it stops when the
underside of its 20 mm step lands on the cartridge's top face, shank dangling.

That is the better of the two anyway. Hanging, the shank spans the grip land
completely; standing on the floor a 25 mm shank would top out 1.7 mm into it and
be held by half a land. `HexTool.seat_z` works out which of the two a tool does
from its own shank length, and `checks.py` asserts the land engagement either
way.

Nothing about the cover changes: the tip reaches 87 mm where the 132 mm twist
drill reaches 138, so the 123 mm cover is still sized by the drill.

### If you have the 3 – 12 mm one instead

Swap `head_d=20.0, d_min=4.0` for `head_d=12.0, d_min=3.0, step=1.0` in
`sets.METAL`. A 12 mm footprint fits the row packer, so you can also drop the
`layout=FREE_LAYOUT` line and let `pack_rows` have it back. Both step drills at
once do not fit in any arrangement.

## The two smallest bores

1 mm and 1.5 mm are the smallest holes in the package, and they sit at the edge
of what a 0.4 mm nozzle resolves in TPU: the 1 mm land is 0.95 mm across, barely
two extrusions wide. `checks.py` asserts that floor rather than assuming it.

They print and they grip, but expect to open the smallest one with the drill
itself the first time. If a bore closes up entirely, drop that size from
`sets.METAL` — do **not** open every land to rescue one, which trades the grip on
nine bores for the tenth.

Sizes, lengths and the cover label are `sets.METAL`. The clearances, the geometry
and the argument behind both are shared with the other two variants — see
[the family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).
