"""Pendant lamp made from a 20 cm IKEA stainless salad bowl.

The bowl is turned over and hung from a flex through a 42 mm hole drilled at
what used to be its bottom. That leaves a 200 mm mouth pointing at the floor
with a bare lamp in it, which is the problem this model solves: a printed grille
of concentric rings on a cross drops into the mouth and is held there by eight
disc magnets pulling on the steel from the inside. Nothing is drilled, glued or
clamped to the bowl beyond the one hole it already has.

    uv run show salad_bowl_lamp             # bowl and shade together
    uv run show salad_bowl_lamp.shade       # the printed part, in print pose
    uv run show salad_bowl_lamp.bowl        # the bought bowl, as measured
    uv run export salad_bowl_lamp.shade     # the STL to print, in white PLA
    uv run check salad_bowl_lamp            # hold it to the bowl's measurements

``create()`` is the lamp: bought bowl, printed shade, in the pose they occupy in
use. Nothing about that mesh is a print job, so the website offers no STL for it
-- ``salad_bowl_lamp.shade`` is the download, and it is the only printed part
here. See ``README.md`` for the hardware, the print settings and the one thing
worth testing before printing 175 g of filament (whether the bowl is magnetic at
all).
"""

from __future__ import annotations

from build123d import Compound, Pos

from ..lib.edges import as_part
from . import bowl as bowl_mod
from . import config, shade as shade_mod
from .bowl import create_bowl
from .config import bowl_inner_radius
from .shade import create_shade

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True


def create() -> Compound:
    """Bowl and shade, assembled the way they hang.

    The bowl's rim plane is z = 0 and the shade's own origin is its underside,
    so seating it is the single translation the whole design reduces to:
    ``RIM_INSET`` up, into the mouth. Everything else -- the band's arc, the
    pads' radii, the tilt of the pockets -- was derived through that same offset
    in ``config``, so if this scene looks right, the numbers agree.
    """
    shade = as_part(Pos(0, 0, config.RIM_INSET) * create_shade())
    shade.label = "shade (printed)"
    shade.color = shade_mod.SHADE_COLOR

    assembly = Compound(children=[create_bowl(), shade])
    assembly.label = "salad bowl lamp"
    return assembly


__all__ = [
    "IS_ASSEMBLY",
    "bowl_inner_radius",
    "bowl_mod",
    "config",
    "create",
    "create_bowl",
    "create_shade",
    "shade_mod",
]
