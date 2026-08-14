"""The outer band on its own -- print this first, before the whole shade.

    uv run show salad_bowl_lamp.fit_test
    uv run export salad_bowl_lamp.fit_test

The shade is 141 g and two hours of a 200 mm bed, and everything that can go
wrong with it goes wrong at the band: whether its notch really gets past the
bulge in your bowl's mouth, whether the seat then beds where it was meant to,
whether your discs drop into a 5.3 mm pocket, and whether eight of them hold the
weight. This is that band and nothing else -- the same ``create_band()``
the shade is built from, so it cannot drift from the part it is a test of -- at a
bit over a quarter of the filament (36 g against 141 g).

It takes the same sliders the band is cut from (``PARAMS``), so a bowl that is
not this bowl gets a test print for *its* seat rather than for this one.

**It is the whole ring, not a sample of it, and that is the point.** A segment
tells you the pocket size and the magnet grip, both of which are honest, and
then lies about the fit, because a 2.4 mm arc of PLA flexes far more than the
50 mm of diameter error it would take to matter. A closed ring cannot: it either
drops in and stops where the seat says, or it does not.

What to look for, with the bowl upside down on a table:

* **Whether it goes in.** Tilt it slightly to bring the notch past the bulge; it
  should not have to be forced. If it will not go, either the bulge is taller
  than the 1 mm this is cut for -- measure it and put the number in ``bead_h``
  rather than sanding the print -- or it runs all the way round the mouth, in
  which case no notch helps and the band has to be cut smaller instead.
* **Where it stops.** The band should come to rest with its underside about
  level with the rim (``RIM_INSET`` is 0) and sit there without rocking.
  Deeper means the print came out small, shallower means large -- a taper seat
  converts a diameter error into a depth error at about 2.5:1, so 2 mm of depth
  is only about 0.8 mm of diameter, and the shade will still look right. Only
  worry if it drops well past the rim or stands proud of it.
* **The magnets.** Fit one dry, without glue. It should drop in and sit flush or
  a hair below the surface, never proud -- proud means the pocket is shallow and
  the disc, not the plastic, sets the seat.
* **The hold.** With all eight in, the ring should stay put when you turn the
  bowl over and take some knocks. If it slides, the shade will too: the ring is
  a quarter of the shade's weight but carries all eight magnets, so this test is
  the *optimistic* one, and failing it means going up in magnet size before
  printing the real thing.

Print it exactly as the shade prints: same orientation (it is already in it),
same layer height, a brim, no supports.
"""

from __future__ import annotations

from build123d import Part

from .config import SEAT_PARAMS, Lamp
from .shade import SHADE_COLOR, create_band

PARAMS = SEAT_PARAMS
"""The sliders that reach the band: the bowl it seats in, the band itself and
the magnets. Ring count and eye diameter are not offered, because the part
this builds has neither."""


def create(**params) -> Part:
    """The band, in print pose -- the shade's seat with the grille left off."""
    part = create_band(Lamp.of(**params))
    part.label = "band fit test"
    part.color = SHADE_COLOR
    return part


__all__ = ["PARAMS", "create"]
