# Spiral vase lampshade — "waves"

A 186 mm vase-mode lampshade: six soft petals breathing up an ovoid body,
pinching away to nothing at half height and coming back inverted, standing on an
83 mm collar. One shell, 0.8 mm thick, printed in a single spiralising perimeter
with no supports and no seam.

```bash
uv run show spiral_vase_lampshade
uv run export spiral_vase_lampshade    # exports/spiral_vase_lampshade.stl
uv run check spiral_vase_lampshade
```

|                     |                                              |
| ------------------- | -------------------------------------------- |
| Height              | 185.8 mm                                      |
| Footprint           | 149 mm across (fits a 180 mm bed)             |
| Base register       | 83 mm ⌀, 6.5 mm tall collar, 2.4 mm wall      |
| Profile             | 85 mm base → 115.5 mm widest → 84 mm mouth    |
| Lobes               | 6, up to 0.44 of the local radius deep        |
| Shell               | 0.8 mm                                        |
| Material            | ~98 cm³ ≈ 124 g PETG                          |
| Steepest overhang   | 50.8° from vertical (budget 56.3°)            |

## Where the design comes from

After **JH's ["Waves" Designer Lamp](https://www.printables.com/model/1261597-waves-designer-lamp)**
(Printables 1261597, CC-BY). That model is a whole lamp — a threaded base for the
Bambu Lab LED Lamp Kit, a shade that screws into it, and a step file for adapting
other shades to the same fitting. This is the *shade*, rebuilt parametrically.

### Measured, not guessed

This model was first built from JH's photographs, and every wave parameter in it
was wrong. The reference STL was then downloaded and reverse-engineered per the
`stl-reverse-engineering` skill, and the difference is worth recording because it
is what a photograph cannot tell you:

| | from photos | from the mesh |
| --- | --- | --- |
| lobes | 5 | **6** |
| wave depth | 0.22 × R | **0.44 × R** |
| height | 200 mm | **185.8 mm** |
| profile base / widest / mouth | 83 / 136 / 88 | **85 / 115.5 / 84** |
| twist | 0.05 turns | **0.19 turns** |
| envelope at the collar | antinode | **node** |

Every one of those is now a measurement. The method: `mesh_analyze.py` reported
1,239,958 triangles, not watertight, and a swept/actual around 34 — nowhere near
an extrusion, so no generated profile was used. `mesh_zones.py` on Z found
exactly two zones, a 3.5 mm threaded collar and one continuous 176 mm shell,
which is the structure this package already had. The surface itself was then
measured directly: 300 slices × 512 angles, the axis solved for by minimising the
first angular harmonic (it came out at the origin to within 1e-7), and each
section Fourier-decomposed. n = 6 carries four times the angular energy of
anything else; the silhouette is a least-squares fit of `wave.silhouette` to the
mean radius of 279 body slices, tracking it to 0.95 mm rms.

### How close it gets

Graded against the reference mesh, rotation and z-offset removed (both are rigid
transforms, so neither is a difference in shape):

| | outer-envelope IoU | radial rms | radial mean error |
| --- | --- | --- | --- |
| tuned from photographs | 63.8% | 15.0 mm | 12.5 mm |
| **measured from the mesh** | **86.8%** | **5.5 mm** | **3.8 mm** |

against a reference whose own radius runs 30–79 mm. Measuring cut the error by a
factor of 2.7.

That is an *envelope* IoU, computed in closed form from the radial fields of 160
aligned slices, and not `mesh_compare.py`'s number. The reference STL is not
watertight, which disables that script's manifold boolean and makes its sampling
fallback unreliable by its own warning; both solids are star-shaped about the
same axis, so `min(r1,r2)² / max(r1,r2)²` summed over the field is exact and
needs no repair. The hollow is excluded, deliberately — it is a 0.8 mm offset of
the outer surface in both, so it would only dilute the thing being measured.

### What it is not

86.8% is not 95%, and it will not get there by tuning, because the gap is
structural rather than a matter of parameters. The reference's ridge line rotates
at a rate that **changes with height** — about 53°/height where the lobes are
deep, 110° where they pinch. A single twisting carrier rotates at one rate by
construction, so no setting of `twist_turns` can produce that; the signature is
two wave trains beating against each other, and fitting one gets the n=6
coefficient to about 10% where this module's single carrier leaves 4.45 mm rms
over the whole field. The reference was very likely lofted through hand-placed
profiles rather than generated from a formula at all.

So: the closest member of a parametric family, holding six measured parameters —
not the same surface. A genuinely exact copy would be a loft through the 300
measured sections, which is a data table rather than a model: not resizable, not
checkable, and JH's geometry redistributed rather than reinterpreted. That trade
was made deliberately, and this is the side of it this repo wants.

The one number that is neither measured nor fitted is **83 mm**, the bottom
diameter from JH's published spec that any shade has to present to their base.

## What it fits

The collar is a plain 83 mm register — a flat-bottomed, 6.5 mm tall, 2.4 mm thick
ring, chamfered onto the bed. There is deliberately **no thread**: the reference's
threaded attachment is a separate downloadable part, and cutting a thread to
match it is a fit this repo has not verified. To put this on JH's base, print
their `Lampshade-Attachment` and glue this collar into it, or use the register as
a locating spigot on any 83 mm opening.

Nothing about the shade assumes that base. `base_dia` is a slider, so the same
design will sit on an E27 shade ring or a wooden puck at whatever diameter it is.

## Printing

Vase mode, 0.4 mm nozzle, no supports. It arrives already in print pose — collar
down — and has to be printed that way round: the mouth is the last thing to print
and there is nothing to support it upside down. Reckon on a couple of hours: 930
layers at 0.2 mm, each a single perimeter of around 500 mm. That is an arithmetic
estimate, not a sliced one.

| Setting                     | Value                                  |
| --------------------------- | -------------------------------------- |
| Spiral vase mode            | on                                     |
| Layer height                | 0.2 mm                                 |
| External perimeter width    | **0.6 mm**                             |
| Solid bottom layers         | **33** (the first 6.5 mm — the collar) |
| Infill                      | 0                                      |
| Material                    | PETG or PLA, translucent or white      |

The solid-bottom-layers count is the one that matters and the one slicers do not
work out for you: it is what turns the collar from a hoop into a foot. At other
layer heights it is `6.5 mm ÷ layer height`.

Those two settings also set the overhang limit, which is arithmetic rather than
the usual 45° rule of thumb. Vase mode lays one bead per layer and each bead is
held by sitting partly on the one below, so the limit is where the wall's
sideways step in a layer reaches half the bead: `atan(0.6 / 2 / 0.2)` = 56.3°.
The shade's steepest point is 50.8°. Change either setting and `MAX_OVERHANG`
moves with it.

Print it in the colour you want lit, not the colour you want on the shelf: at
0.6 mm of wall, everything about this part is about what the light does on its
way out.

## Turning the knobs

Fourteen sliders on the website, all clamped by `Shade.of()` so no combination
can produce a part that fails to build. Four are worth understanding first;
`wave.py` is the argument for each term.

- **`pinch`** (1.0) — the one to turn first. At 0 the envelope is constant and
  the shade is a plain twisted flute. At 1 the lobes pinch away to *nothing* at
  each node and come back with crest and valley swapped. The reference is at the
  stop, and that inversion is the whole petal effect.
- **`env_phase`** (−π/2) — where up the body those nodes fall. It exists because
  the reference has a node exactly at the collar and another at half height;
  with the phase pinned at 0 the envelope is forced to an antinode at the bottom
  and no other slider can move it.
- **`wave_depth`** (0.44) — how proud a crest stands, as a fraction of the
  *local* radius rather than a fixed depth, so lobes stay in proportion as the
  silhouette swells. Clamped against the wall: an inward offset cannot be pushed
  past a crest's radius of curvature without crossing itself, so depth and lobe
  count trade off automatically.
- **`lobes`** (6) and **`wave_cycles`** (1) — crests round the section, and times
  the depth breathes up the body. These two set the rhythm.

Two numbers are deliberately **not** sliders. `FADE_IN` is what holds the body to
the collar as a true circle, so exposing it would let the site produce a shade
that no longer meets the 83 mm spec. `z_sections` and `facets` are loft
resolution, which is construction rather than design.

## Known gaps, accepted rather than hidden

- **It is an approximation, by 4.45 mm rms.** See "What it is not" above. The
  checks can prove the surface is the field `wave.py` describes; they cannot
  prove the field is JH's, because it is not.
- **Printability is checked but not clamped.** The sliders can reach an 84°
  overhang (a 300 mm profile on a 60 mm height will do it) and that shape still
  builds — it just does not print. `checks.py` holds *the default* to 56.3° and
  says so; clamping the sliders would be the model overruling a shape somebody
  explicitly asked for.
- **No base, no thread, no LED mount.** This is one printed part.
- **The wall is the section's, not the surface's.** The 0.8 mm offset is taken in
  the plane of each cross-section, which is exactly what a vase-mode slicer's
  single perimeter follows. Where the silhouette leans, the wall measured
  perpendicular to the *surface* is that times the cosine of the lean — down to
  about 0.5 mm at the steepest band. That is the right model of the print and the
  wrong model of the solid, and the checks measure the former.
