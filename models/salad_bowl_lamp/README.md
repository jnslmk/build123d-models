# Salad-bowl pendant lamp

A 20 cm stainless IKEA salad bowl, turned over and hung from a flex through a
42 mm hole drilled in what used to be its bottom, plus one printed part: a
grille of concentric rings on a cross that drops into the 200 mm mouth and is
held there by eight disc magnets. Nothing is drilled, glued or clamped to the
bowl beyond the hole it already has, and the grille comes out by pulling on it.

```bash
uv run show salad_bowl_lamp             # bowl and shade together
uv run show salad_bowl_lamp.shade       # the printed part, in print pose
uv run export salad_bowl_lamp.fit_test  # the STL to print FIRST -- see below
uv run export salad_bowl_lamp.shade     # the STL to print
uv run check salad_bowl_lamp            # hold it to the bowl's measurements
```

## Before you print 126 g of filament: is your bowl magnetic?

**Test it with a fridge magnet.** Stainless steel comes in two families and only
one of them holds a magnet. Deep-drawn kitchenware is usually 18/10 austenitic,
which is nominally *non*-magnetic; forming work-hardens it and often leaves it
weakly magnetic, so bowls of the same model vary. If a fridge magnet will not
stay on the inside of the mouth, this shade has nothing to hang from and the
mounting has to change (a steel band bonded inside the rim, or three printed
hooks over the lip) before anything gets printed.

If a magnet does hold, check it holds *near the rim*, on the inside, which is
where these eight will be.

## Then print the fit test

`salad_bowl_lamp.fit_test` is the outer band on its own -- the same
`create_band()` the shade is built from, so it cannot drift from it -- at 36 g
instead of 126 g. It answers the three things that a drawing cannot: where the
taper seat comes to rest in *your* bowl, whether your discs drop into the
pockets, and whether eight of them hold at all. It is the whole ring rather than
a segment on purpose: a 2.4 mm arc of PLA flexes far more than any diameter
error worth catching, so a segment would tell you what you want to hear. Its own
docstring says what to look for.

## Hardware

| Item | Qty | Note |
| --- | --- | --- |
| Ø20 cm stainless salad bowl, 9.5 cm deep | 1 | with a 42 mm hole drilled at the apex |
| Ø6 × 2 mm disc magnet, N42 or similar | 8 | sliders, or `Lamp.magnet_d` / `magnet_t` |
| Cyanoacrylate or 5-minute epoxy | — | to retain the magnets |
| E27 lampholder, flex, ceiling rose | 1 | not modelled |

**Polarity does not matter.** Every magnet here pulls on steel, not on another
magnet, so there is no way to fit one the wrong way round -- unusual enough among
magnet closures to be worth saying.

Note what the load actually is. The band is a taper, so the shade's weight hangs
in **shear** across eight magnet faces, not in tension pulling them off; what
carries it is friction under the magnets' own clamping force. That is the good
direction for a joint like this, and it is also why an air gap is fatal: nothing
about it works if the discs stand off the steel by even a few tenths.

## Printing

White PLA, 0.4 mm nozzle, 0.2 mm layers. **No supports and no rafts**; a brim is
worth it, because the first layer is 2.4 mm-wide rings and 200 mm across, and a
lifted corner on the outer band is a lifted seat.

The part comes out of `create()` already in print pose and the pose is not
negotiable: the band narrows as it rises, so every layer is inside the one below
it and nothing overhangs. Turning it over or laying it down gives up both.

It is about **126 g and several hours** -- 2.4 mm × 20 mm of wall, five rings and
four arms, at 200 mm diameter. Print it in one piece; there is no seam that would
survive being split.

Perimeters matter more than infill here. At a 2.4 mm wall the part is perimeters
all the way through, so set 4 of them (0.3 mm lines) or 3 (0.4 mm) and let infill
be whatever is left. The one place that number matters structurally is behind
the magnets: a 2 mm pocket in a 2.4 mm wall leaves **0.4 mm** of backing, which
is a single line at a 0.4 mm nozzle. That is the floor, and the model treats it
as one -- `MIN_BACKING`, which the wall slider is clamped against rather than the
pocket. It is enough because the magnet is pulled *outward* onto the steel in
service and glued besides, so the backing only has to keep the disc in its hole
on the way to the bowl. If your slicer would rather bridge that 0.4 mm than
print it, take the wall to 2.8 and get two lines.

## Fitting

1. Glue the eight magnets into the pockets around the outer band, flush with the
   surface. The pockets are teardrop-shaped -- round at the bottom, pointed at
   the top -- so they print without a sagging bridge; a round magnet still drops
   straight in. They are cut 0.3 mm oversize on the diameter (`fits.FREE` for
   PLA) precisely so the magnet is never forced: a sintered magnet chips rather
   than deforms, and the glue is what retains it.
2. Turn the bowl over, hang it, and push the shade up into the mouth until it
   stops. It is a taper seat, so it stops by itself, roughly 3 mm above the rim.
3. If it sits noticeably deeper or shallower than that, the print is running
   under or over size. Nothing is wrong with it -- the seat is a 10.5 deg cone
   and it simply beds where the diameters agree, converting a diameter error into
   about 2.7× as much depth error. 2 mm of depth is 0.7 mm of diameter.

## What decides the geometry

The bowl is a **spherical cap**, and that is forced rather than assumed: exactly
one sphere passes through a 200 mm rim circle and touches a plane 95 mm below
it, at R = 100.13 mm. Everything else follows from the inside of that sphere:

- the band's outer face is the bowl's inner sphere, with **no clearance at all**
  -- a taper seat cannot jam, and it puts the magnets on steel instead of near it;
- the band's *inner* face is that same sphere 2.4 mm smaller, struck from the
  same centre. So the band is an even wall measured along a pocket's own axis,
  its inside is as plain as its outside -- no bosses, no pads, nothing standing
  proud where a hand goes to lift the shade out -- and a pocket bored on that
  axis meets the back face square instead of skewed;
- the eight magnet pockets are bored along that sphere's own radii, so each
  magnet's face is tangent to the steel rather than merely close to it;
- the shade starts 3 mm above the rim (`RIM_INSET`), clear of whatever a spun
  rim does with its last millimetre or two of rolled lip;
- five rings, evenly spaced 16.1 mm apart, 2.4 mm thick and 20 mm tall. The ring
  diameters are derived from the gap, not typed in -- change `RING_COUNT` or
  `EYE_D` and the rest re-spaces itself;
- **the cross stops at the innermost circle** rather than crossing it. Four arms
  hang off the hub, each ending half a millimetre inside the hub's wall where the
  fuse swallows it (`ARM_EMBED`), so the eye stays a clean circle and the middle
  of the shade is the one place you can see the lamp from.

## Sliders

Every view is parametric on the website, and each offers only the numbers that
reach its own geometry — the bowl gets its four, the fit test the nine that cut
a band, the shade those plus the ring count and eye, the assembled lamp all of
them. `config.Lamp` holds them; `Lamp.of()` is the door they come in through.

`of()` **clamps rather than rejects**, because a slider that can produce a part
that fails to build is a bug in the model, not in the person dragging it. Where
two inputs fight, the one that moves is the one whose being wrong is safe: a wall
too thin for its magnet grows to fit it, and a magnet never shrinks into a pocket
it does not fill. The dependency order is fixed — wall, then how much dome the
band may occupy, then ring spacing, then the eye, then the magnets — and the
limits it enforces are the geometric ones: `MIN_GAP` of air between rings,
`MIN_BACKING` behind every magnet, a bowl no deeper than a hemisphere (past that
the rim stops being the widest circle and nothing can be got in through it), a
teardrop peak that clears the band's top edge, and enough seat circumference for
the pockets asked for.

`checks.py` drags every slider to both stops and past them, then *builds* what
comes back — clamping that quietly stopped clamping shows up as a broken solid,
not as a bad number.

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
| `fit_test.py` | the outer band alone, to print before the grille |
| `checks.py` | the geometry assertions `uv run check` runs, including the slider sweep |
