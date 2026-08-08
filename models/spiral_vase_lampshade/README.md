# Spiral vase lampshade — "waves"

A 200 mm vase-mode lampshade: five soft petals breathing up an ovoid body,
standing on an 83 mm collar. One shell, 0.8 mm thick, printed in a single
spiralising perimeter with no supports and no seam.

```bash
uv run show spiral_vase_lampshade
uv run export spiral_vase_lampshade    # exports/spiral_vase_lampshade.stl
uv run check spiral_vase_lampshade
```

|                     |                                              |
| ------------------- | -------------------------------------------- |
| Height              | 200 mm                                        |
| Footprint           | 156 mm across (fits a 180 mm bed)             |
| Base register       | 83 mm ⌀, 6 mm tall collar, 2.4 mm wall        |
| Mouth               | 88 mm profile ⌀, open                         |
| Shell               | 0.8 mm                                        |
| Material            | ~58 cm³ ≈ 72 g PETG                           |
| Steepest overhang   | 41.6° from vertical                           |

## Where the design comes from

The look is after **JH's ["Waves" Designer Lamp](https://www.printables.com/model/1261597-waves-designer-lamp)**
(Printables 1261597, CC-BY). That model is a whole lamp — a threaded base for
the Bambu Lab LED Lamp Kit, a shade that screws into it, and a step file for
adapting other shades to the same fitting. This is none of that. It is the
*shade*, rebuilt parametrically in build123d from the reference photographs;
none of JH's geometry was available or used, so what is reproduced here is the
look, tuned by eye against their pictures and then pinned in place by
`checks.py`.

One number does come from their published spec: **83 mm**, the bottom diameter
any shade has to present to their base. `base_dia` defaults to it and the collar
exists to hold it round and flat.

## What it fits

The collar is a plain 83 mm register — a flat-bottomed, 6 mm tall, 2.4 mm thick
ring, chamfered onto the bed. There is deliberately **no thread**: cutting one
to a profile nobody here has measured would be a fit this repo could not stand
behind. To put this on JH's base, print their `Lampshade-Attachment` and glue
this collar into it, or use the register as a locating spigot on any 83 mm
opening.

Nothing about the shade assumes that base, though. `base_dia` is a slider, so
the same design will sit on an E27 shade ring or a wooden puck at whatever
diameter it happens to be.

## Printing

Vase mode, 0.4 mm nozzle, no supports. It arrives already in print pose — collar
down — and has to be printed that way round: the mouth is the last thing to
print and there is nothing to support it upside down. Reckon on a couple of
hours: 1000 layers at 0.2 mm, each one a single ~450 mm perimeter. That is an
arithmetic estimate, not a sliced one — ask your slicer.

| Setting                     | Value                                  |
| --------------------------- | -------------------------------------- |
| Spiral vase mode            | on                                     |
| Layer height                | 0.2 mm                                 |
| External perimeter width    | **0.6 mm**                             |
| Solid bottom layers         | **30** (the first 6 mm — the collar)   |
| Infill                      | 0                                      |
| Material                    | PETG or PLA, translucent or white      |

The solid-bottom-layers count is the one that matters and the one slicers do not
work out for you: it is what turns the collar from a hoop into a foot. At other
layer heights it is `6 mm ÷ layer height` — 40 at 0.15 mm, 20 at 0.3 mm.

The shell is modelled at 0.8 mm, which is two perimeters of a 0.4 mm nozzle and
the floor below which a wall does not slice as a wall at all. Vase mode lays one
bead per layer and the *slicer's* external extrusion width decides how fat that
bead really is; 0.6 mm is the reference design's recommendation and gives a
shade that diffuses without going translucent-blotchy at the crests.

Print it in the colour you want lit, not the colour you want on the shelf: at
0.6 mm of wall, everything about this part is about what the light does on its
way out.

## Turning the knobs

Thirteen sliders on the website, all of them clamped by `Shade.of()` so no
combination can produce a part that fails to build. Four are worth understanding
before the rest; `wave.py` is the argument for each term.

- **`pinch`** (0.65) — the one to turn first. At 0 the envelope is constant and
  the shade is a plain twisted flute. Above 0.5 the envelope goes *negative* over
  part of the height, so crest and valley swap and the lobes appear to overlap
  along the bands where it passes through zero. That inversion is the whole
  petal effect.
- **`wave_depth`** (0.22) — how proud a crest stands, as a fraction of the
  *local* radius rather than a fixed depth, so the lobes stay in proportion as
  the silhouette swells and narrows. Clamped against the wall: an inward offset
  cannot be pushed further than the radius of curvature of a crest without
  crossing itself, so deep waves and many lobes are traded off against each
  other automatically.
- **`wave_cycles`** (2) and **`lobes`** (5) — how many times the depth breathes
  up the body, and how many crests go round. These two set the rhythm; almost
  everything else is proportion.
- **`twist_turns`** (0.05) — turns of the *pattern* over the full height, not
  turns divided by the lobe count. 0.05 is 18°, which is the lazy S-lean in the
  reference rather than a barber's pole.

Two numbers are deliberately **not** sliders. `FADE_IN` is what holds the body
to the collar as a true circle, so exposing it would let the site produce a
shade that no longer meets the 83 mm spec it is named for. `z_sections` and
`facets` are loft resolution, which is construction rather than design.

## Known gaps, accepted rather than hidden

- **Printability is checked but not clamped.** The sliders can reach an 84°
  overhang (a 300 mm profile on a 60 mm height will do it) and that shape still
  builds — it just does not print. `checks.py` holds *the default* to 45° and
  says so; clamping the sliders would be the model overruling a shape somebody
  explicitly asked for.
- **No base, no thread, no LED mount.** See above. This is one printed part.
- **The wall is the section's, not the surface's.** The 0.8 mm offset is taken
  in the plane of each cross-section, which is exactly what a vase-mode slicer's
  single perimeter follows. Where the silhouette leans, the wall measured
  perpendicular to the *surface* is that times the cosine of the lean — up to
  about 0.6 mm at the steepest band. That is the right model of the print and
  the wrong model of the solid, and the checks measure the former.
- **Tuned by eye.** The wave parameters were fitted against photographs, not
  against the reference geometry, which was never available. `checks.py` can
  prove the surface is the field `wave.py` describes; it cannot prove the field
  is JH's.
