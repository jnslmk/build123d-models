"""Pendant lamp made from a 20 cm IKEA stainless salad bowl.

The bowl is turned over and hung from a flex through a 42 mm hole drilled at
what used to be its bottom. That leaves a 200 mm mouth pointing at the floor
with a bare lamp in it, which is the problem this model solves: a printed grille
of concentric rings on a cross drops into the mouth and is held there by eight
disc magnets pulling on the steel from the inside. Nothing is drilled, glued or
clamped to the bowl beyond the one hole it already has.

The mouth is not a plain circle: there is a bulge just inside it, 4 mm across and
standing 1 mm proud. The grille's outer band answers it with a **notch** round
its bottom -- the lowest 5.8 mm of its outer face cut back 1.3 mm, then ramped at
45 deg back onto the bowl's own sphere -- so the seat, the magnets and the wall
above it are exactly what they would be on a bowl without one, and the band
reaches all the way down to the rim plane. ``config.bead_h = 0`` takes the bulge
and the notch back off together.

    uv run show salad_bowl_lamp             # bowl and shade together
    uv run show salad_bowl_lamp.shade       # the printed part, in print pose
    uv run show salad_bowl_lamp.bowl        # the bought bowl, as measured
    uv run show salad_bowl_lamp.fit_test    # the outer band alone, to print first
    uv run export salad_bowl_lamp.shade     # the STL to print, in white PLA
    uv run check salad_bowl_lamp            # hold it to the bowl's measurements

Every view here is parametric on the website: ``PARAMS`` on each module offers
the sliders that actually reach its geometry, and ``config.Lamp.of()`` clamps
whatever comes back so no combination of them can produce a part that fails to
build.

``create()`` is the lamp: bought bowl, printed shade, in the pose they occupy in
use. Nothing about that mesh is a print job, so the website offers no STL for it
-- ``salad_bowl_lamp.shade`` is the download, and it is the only part of the
finished lamp that gets printed. ``salad_bowl_lamp.fit_test`` is its outer band
on its own, which is what to print first. See ``README.md`` for the hardware, the
print settings and the one thing worth testing before printing 141 g of filament
(whether the bowl is magnetic at all).
"""

from __future__ import annotations

from build123d import Compound, Pos

from ..lib.edges import as_part
from . import bowl as bowl_mod
from . import config, shade as shade_mod
from .bowl import create_bowl
from .config import DEFAULT, LAMP_PARAMS, Lamp
from .shade import create_shade

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True

PARAMS = LAMP_PARAMS
"""Every slider in the design, because this view holds every part of it."""


def create(**params) -> Compound:
    """Bowl and shade, assembled the way they hang.

    The bowl's rim plane is z = 0 and the shade's own origin is its underside,
    so seating it is the single translation the whole design reduces to:
    ``rim_inset`` up, into the mouth. Everything else -- the band's arc, the
    pads' radii, the tilt of the pockets -- was derived through that same offset
    on the same ``Lamp``, so if this scene looks right, the numbers agree.

    That shared object is also what keeps the sliders honest: bowl and shade are
    cut from one ``Lamp.of()``, so a dragged bowl diameter moves the seat the
    grille was built for rather than leaving the two views disagreeing.
    """
    lamp = Lamp.of(**params)
    shade = as_part(Pos(0, 0, lamp.rim_inset) * create_shade(lamp))
    shade.label = "shade (printed)"
    shade.color = shade_mod.SHADE_COLOR

    assembly = Compound(children=[create_bowl(lamp), shade])
    assembly.label = "salad bowl lamp"
    return assembly


__all__ = [
    "DEFAULT",
    "IS_ASSEMBLY",
    "PARAMS",
    "Lamp",
    "bowl_mod",
    "config",
    "create",
    "create_bowl",
    "create_shade",
    "shade_mod",
]
