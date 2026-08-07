# Salad-bowl pendant lamp

A 20 cm stainless IKEA salad bowl, turned over and hung from a flex through a
42 mm hole drilled in what used to be its bottom, plus one printed part: a
grille of concentric rings on a cross that drops into the 200 mm mouth and is
held there by eight disc magnets. Nothing is drilled, glued or clamped to the
bowl beyond the hole it already has, and the grille comes out by pulling on it.

```bash
uv run show salad_bowl_lamp             # bowl and shade together
uv run show salad_bowl_lamp.shade       # the printed part, in print pose
uv run export salad_bowl_lamp.shade     # the STL to print
uv run check salad_bowl_lamp            # hold it to the bowl's measurements
```

## Before you print 170 g of filament: is your bowl magnetic?

**Test it with a fridge magnet.** Stainless steel comes in two families and only
one of them holds a magnet. Deep-drawn kitchenware is usually 18/10 austenitic,
which is nominally *non*-magnetic; forming work-hardens it and often leaves it
weakly magnetic, so bowls of the same model vary. If a fridge magnet will not
stay on the inside of the mouth, this shade has nothing to hang from and the
mounting has to change (a steel band bonded inside the rim, or three printed
hooks over the lip) before anything gets printed.

If a magnet does hold, check it holds *near the rim*, on the inside, which is
where these eight will be.

## Hardware

| Item | Qty | Note |
| --- | --- | --- |
| Ø20 cm stainless salad bowl, 9.5 cm deep | 1 | with a 42 mm hole drilled at the apex |
| Ø8 × 3 mm disc magnet, N42 or similar | 8 | `config.MAGNET_D` / `MAGNET_T` if yours differ |
| Cyanoacrylate or 5-minute epoxy | — | to retain the magnets |
| E27 lampholder, flex, ceiling rose | 1 | not modelled |

**Polarity does not matter.** Every magnet here pulls on steel, not on another
magnet, so there is no way to fit one the wrong way round -- unusual enough among
magnet closures to be worth saying.

## Printing

White PLA, 0.4 mm nozzle, 0.2 mm layers. **No supports and no rafts**; a brim is
worth it, because the first layer is 3 mm-wide rings and 200 mm across, and a
lifted corner on the outer band is a lifted seat.

The part comes out of `create()` already in print pose and the pose is not
negotiable: the band narrows as it rises, so every layer is inside the one below
it and nothing overhangs. Turning it over or laying it down gives up both.

It is about **170 g and several hours** -- 3 mm × 20 mm of wall, five rings and
a cross, at 200 mm diameter. Print it in one piece; there is no seam that would
survive being split.

Perimeters matter more than infill here. At 3 mm wall the part is perimeters all
the way through, so set 4-5 of them and let infill be whatever is left.

## Fitting

1. Glue the eight magnets into the pockets around the outer band, flush with the
   surface. The pockets are teardrop-shaped -- round at the bottom, pointed at
   the top -- so they print without a sagging bridge; a round magnet still drops
   straight in. They are cut 0.3 mm oversize on the diameter (`fits.FREE` for
   PLA) precisely so the magnet is never forced: sintered magnet chips rather
   than deforms, and the glue is what retains it.
2. Turn the bowl over, hang it, and push the shade up into the mouth until it
   stops. It is a taper seat, so it stops by itself, roughly 3 mm above the rim.
3. If it sits noticeably deeper or shallower than that, the print is running
   under or over size. Nothing is wrong with it -- the seat is a 10.5 deg cone
   and it simply beds where the diameters agree.

## What decides the geometry

The bowl is a **spherical cap**, and that is forced rather than assumed: exactly
one sphere passes through a 200 mm rim circle and touches a plane 95 mm below
it, at R = 100.13 mm. Everything else follows from the inside of that sphere:

- the band's outer face is the bowl's inner sphere, with **no clearance at all**
  -- a taper seat cannot jam, and it puts the magnets on steel instead of near it;
- the eight magnet pockets are bored along that sphere's own radii, so each
  magnet's face is tangent to the steel rather than merely close to it;
- the shade starts 3 mm above the rim (`RIM_INSET`), clear of whatever a spun
  rim does with its last millimetre or two of rolled lip;
- five rings, evenly spaced, 3 mm thick and 20 mm tall, with two full-diameter
  cross arms of the same section. The ring diameters are derived from the gap,
  not typed in -- change `RING_COUNT` or `EYE_D` and the rest re-spaces itself.

## The one thing this model does not know: your bulb

The grille sits across the mouth with a **45 mm eye** in the middle
(`config.EYE_D`), sized to pass an E27 lampholder shell. The bowl is only 95 mm
deep, so a full-size A60 bulb hanging from a holder at the apex reaches *below*
the rim and will foul the rings.

Either use a lamp that stays inside the dome -- a golfball or short globe on a
holder mounted high -- or open `EYE_D` until the bulb passes through it, keeping
in mind that the eye is also the one direction you can look straight at the
filament from. Nothing else in the model needs to change; the rings re-space
themselves around whatever `EYE_D` becomes.

## Files

| File | What is in it |
| --- | --- |
| `config.py` | every measured and derived number, and the arguments for them |
| `bowl.py` | the bought bowl, as a mock, in lamp pose |
| `shade.py` | the printed grille |
| `checks.py` | the geometry assertions `uv run check` runs |
