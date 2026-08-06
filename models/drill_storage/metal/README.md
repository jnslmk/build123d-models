# drill_storage.metal

Gridfinity storage for an **HSS twist drill set**: ten drills on jobber lengths,
1 – 10 mm (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10), plus an M6 hex-shank tap.

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
`TAP` on the walls rather than a bare size, since it is not a drill.

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
