"""The outer band on its own -- print this first, before the whole shade.

    uv run show salad_bowl_lamp.fit_test
    uv run export salad_bowl_lamp.fit_test

The shade is 137 g and two hours of a 200 mm bed, and everything that can go
wrong with it goes wrong at the band: whether a taper seat cut for *your* bowl
actually beds where it was meant to, whether your discs drop into a 6.3 mm
pocket, and whether eight of them hold the weight. This is that band and nothing
else -- the same ``create_band()`` the shade is built from, so it cannot drift
from the part it is a test of -- at a bit over a quarter of the filament
(38 g against 137 g).

**It is the whole ring, not a sample of it, and that is the point.** A segment
tells you the pocket size and the magnet grip, both of which are honest, and
then lies about the fit, because a 2.6 mm arc of PLA flexes far more than the
50 mm of diameter error it would take to matter. A closed ring cannot: it either
drops in and stops where the seat says, or it does not.

What to look for, with the bowl upside down on a table:

* **Where it stops.** The band should come to rest with its underside about 3 mm
  above the rim (``RIM_INSET``) and sit there without rocking. Deeper means the
  print came out small, shallower means large -- a taper seat converts a
  diameter error into a depth error at about 2.7:1, so 2 mm of depth is only
  0.7 mm of diameter, and the shade will still look right. Only worry if it
  drops past the rim or stands proud of it.
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

from .shade import SHADE_COLOR, create_band


def create() -> Part:
    """The band, in print pose -- the shade's seat with the grille left off."""
    part = create_band()
    part.label = "band fit test"
    part.color = SHADE_COLOR
    return part


__all__ = ["create"]
