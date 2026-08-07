"""The bought bowl, as a mock -- the thing the shade has to fit.

    uv run show salad_bowl_lamp.bowl

**Not a print job.** This is a 20 cm stainless salad bowl with a hole drilled
through its bottom for a lampholder, reconstructed from three measurements so
the shade has something to be checked against; ``IS_ASSEMBLY`` keeps the website
from offering an STL of it. Deliberately not vendor CAD, for the same reason
``led_psu_enclosure/mocks.py`` gives: a fit check needs the surface the part
meets and nothing else.

It is returned **inverted -- rim plane at z = 0, dome above, hole at the top**,
which is the pose it has as a lamp rather than the pose it has as a bowl. That
is the whole point of the model: upright it is crockery, and none of the
geometry the shade cares about is where the shade expects it.

The shape is a spherical cap, which is forced by the measurements rather than
assumed -- see ``config``. Two places knowingly depart from the real bowl, both
in directions that cannot flatter the fit:

* **The rim is modelled as a plain rounded edge**, not the rolled or hemmed lip
  a spun bowl actually has. That is exactly why the shade starts
  ``config.RIM_INSET`` above the rim instead of flush with it: at 3 mm up, what
  the real bowl does with its last millimetre or two stops mattering.
* **Wall thickness is nominal.** The shade fits the *inside* sphere, so if the
  steel is thicker than 0.8 mm the shade seats a little shallower, and if it is
  thinner, a little deeper. The seat is a taper; that is the failure mode it is
  chosen for.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    Color,
    Cylinder,
    Locations,
    Mode,
    Part,
    Pos,
    Rotation,
    Sphere,
)

from ..lib.edges import as_part, fillet_edge
from . import config as c

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True

STEEL = Color(0.78, 0.80, 0.83)


def create_bowl() -> Part:
    """The bowl in lamp pose: rim plane on z = 0, dome up, hole at the apex."""
    rim_from_centre = c.BOWL_H - c.BOWL_R  # negative: the rim is below the centre

    with BuildPart() as bowl:
        Sphere(c.BOWL_R)
        Sphere(c.BOWL_R_IN, mode=Mode.SUBTRACT)
        # Keep the cap below the rim plane; the sphere is still centred on the
        # origin here, so the rim sits at a negative z. Note the ``Locations``:
        # a ``Cylinder`` is a ``BasePartObject`` and joins the builder the
        # instant it is constructed, so ``Cylinder(...).locate(...)`` subtracts
        # it from the origin and *then* moves the useless return value. That
        # cuts this bowl at its equator and leaves a 100 mm deep hemisphere
        # that still looks plausible -- see the build123d-geometry-ops skill.
        with Locations((0, 0, rim_from_centre)):
            Cylinder(
                radius=c.BOWL_R + 1,
                height=2 * c.BOWL_R,  # clears the far pole; R + 1 leaves a cap behind
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # Round the cut rim over, on a decreasing ladder: 0.4 mm is half the
        # wall and OCC will not fillet an annulus to its own half-width. A
        # failure here costs nothing but a squarer mock, and fillet_edge
        # restores the builder rather than poisoning it.
        rim = bowl.edges().filter_by_position(
            Axis.Z, rim_from_centre - 0.01, rim_from_centre + 0.01
        )
        for radius in (0.35, 0.25, 0.15):
            if fillet_edge(bowl, rim, radius):
                break
        # The lampholder hole, drilled through the bottom pole.
        with Locations((0, 0, -c.BOWL_R)):
            Cylinder(
                radius=c.BOWL_HOLE_D / 2,
                height=4 * c.BOWL_WALL,
                mode=Mode.SUBTRACT,
            )

    # Turn it over: the rim plane becomes z = 0 and the dome goes up.
    part = as_part(Rotation(180, 0, 0) * bowl.part)
    part = as_part(Pos(0, 0, -part.bounding_box().min.Z) * part)
    part.label = "bowl (bought)"
    part.color = STEEL
    return part


def create() -> Part:
    """Entry point for ``uv run show salad_bowl_lamp.bowl``."""
    return create_bowl()


__all__ = ["IS_ASSEMBLY", "STEEL", "create", "create_bowl"]
