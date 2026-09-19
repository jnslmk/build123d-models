# gled2 — stella octangula installation

The [gled](https://gitlab.com/photonenkollektiv/gled2) installation SVG for
the `led_profiles` stella octangula: twelve 1.5 m lamps as the edges of two
interpenetrating tetrahedra, drawn as a cube isometry so the star reads
without overlap. Every lamp path carries its patch in a `<desc>` — gled reads
groups, start address and pixel count straight out of the file, so loading it
is the whole setup step:

1. `gled` → `Project` → open `gled2-stella-octangula.svg`.
2. `Project` → `Output Routing`: map gled universes `0` and `1` to the
   device's output universes (see below).
3. Animate against the groups.

## Patch

| Lamp | Group | Starts at | Pixels |
|---|---|---|---|
| `b0..b5` | `base` | 0, 23, … 115 | 23 each |
| `o0..o5` | `offset` | 138, 161, … 253 | 23 each |

- `PIXELS_PER_LAMP = 23`, `CHANNELS_PER_PIXEL = 3` — the same numbers the
  star-tent spokes stream. One knob in `__init__.py`; regenerate after
  changing it.
- gled splits any lamp past 170 LEDs into the next universe by itself, so the
  single patch fills gled universe `0` (LEDs 0–169, up into lamp `o1`) and
  universe `1` (LEDs 170–275). No split logic in the file.

## Groups

- `all` — the whole star (set once on the root group).
- `base` / `offset` — each tetrahedron's six lamps.
- `v1..v4` — the base tetrahedron's corners; `v5..v8` — the offset one's.
  Every lamp belongs to its two endpoints, so a corner group lights the three
  lamps meeting there.

## Regenerate

```bash
uv run python -c "import models.gled2; models.gled2.write('<output.svg>')"
uv run check gled2
```

The projection (cube isometry), the lamp axes and the labels all derive from
`led_profiles.assemblies.stella_octangula.lamp_segments` — the CAD is the only
source of truth; nothing here re-derives geometry.
