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
assumed -- see ``config``. On top of the cap sits the one feature of the real
bowl that the shade cannot be designed without: **the bead round the inside of
the mouth**, where the lip is rolled. It is 4 mm wide and stands 1 mm proud of
the sphere with rounded transitions at both ends, and it is modelled here rather
than idealised away because it, not the rim, is the narrowest circle in the bowl.
``bead_h = 0`` takes it back off for a bowl that does not have one.

Two places still knowingly depart from the real bowl, both in directions that
cannot flatter the fit:

* **The rim's own edge is modelled as a plain rounded corner**, and the bead is a
  ring on the inside face rather than a section through a genuinely rolled hem.
  What the fit needs from a rolled lip is how far into the mouth it reaches;
  where the steel doubles back behind it changes nothing the shade can touch.
* **Wall thickness is nominal.** The shade fits the *inside* sphere, so if the
  steel is thicker than 0.8 mm the shade seats a little shallower, and if it is
  thinner, a little deeper. The seat is a taper; that is the failure mode it is
  chosen for.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Color,
    Cylinder,
    Line,
    Locations,
    Mode,
    Part,
    Plane,
    Sphere,
    Spline,
    ThreePointArc,
    add,
    make_face,
    revolve,
)

from ..lib.edges import as_part, fillet_edge, reseat_on_bed
from .config import BOWL_PARAMS, DEFAULT, Lamp

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True

PARAMS = BOWL_PARAMS
"""The bowl's own four numbers. The grille's sliders are not offered here:
nothing about the shade changes this mock, and a slider that does nothing is
worse than no slider."""

STEEL = Color(0.78, 0.80, 0.83)

BEAD_BURY = 0.5
"""How far into the steel the bead's blank reaches, as a fraction of the wall.

The bead's profile is a lune between the sphere and itself, and a lune whose
outer edge sat *on* the sphere would hand the fuse two coincident faces to
reconcile -- the failure mode this repo already documents in ``shade.py``. Buried
half a wall deep instead, the fuse is a plain overlap, and the surplus is inside
steel that the shade never touches.
"""


def _bead(lamp: Lamp) -> Part:
    """The rolled lip's bead: a ring standing proud of the inside of the mouth.

    Built in lamp coordinates (rim plane at z = 0, depth measured up into the
    dome), because that is where it is fused on, and sampled from
    ``bead_protrusion`` rather than drawn from arcs so the profile cannot drift
    from the number ``bead_throat_radius`` -- and therefore the whole band -- is
    derived from. Both curves end on the sphere, where the protrusion is zero, so
    the ring blends into the bowl's inside instead of stepping off it.
    """
    steps = 24
    depths = [lamp.bead_depth + i * lamp.bead_w / steps for i in range(steps + 1)]
    back = lamp.bowl_wall * BEAD_BURY
    with BuildPart() as bead:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Spline(*[(lamp.bowl_clear_radius(d), d) for d in depths])
                ThreePointArc(
                    (lamp.bowl_inner_radius(depths[-1]) + back, depths[-1]),
                    (lamp.bowl_inner_radius(depths[len(depths) // 2]) + back,
                     depths[len(depths) // 2]),
                    (lamp.bowl_inner_radius(depths[0]) + back, depths[0]),
                )
                for d in (depths[0], depths[-1]):
                    Line(
                        (lamp.bowl_clear_radius(d), d),
                        (lamp.bowl_inner_radius(d) + back, d),
                    )
            make_face()
        revolve(axis=Axis.Z)
    return bead.part


def create_bowl(lamp: Lamp = DEFAULT) -> Part:
    """The bowl in lamp pose: rim plane on z = 0, dome up, hole at the apex."""
    rim_from_centre = lamp.bowl_h - lamp.bowl_r  # negative: the rim is below the centre

    with BuildPart() as bowl:
        Sphere(lamp.bowl_r)
        Sphere(lamp.bowl_r_in, mode=Mode.SUBTRACT)
        # Keep the cap below the rim plane; the sphere is still centred on the
        # origin here, so the rim sits at a negative z. Note the ``Locations``:
        # a ``Cylinder`` is a ``BasePartObject`` and joins the builder the
        # instant it is constructed, so ``Cylinder(...).locate(...)`` subtracts
        # it from the origin and *then* moves the useless return value. That
        # cuts this bowl at its equator and leaves a 100 mm deep hemisphere
        # that still looks plausible -- see the build123d-geometry-ops skill.
        with Locations((0, 0, rim_from_centre)):
            Cylinder(
                radius=lamp.bowl_r + 1,
                height=2
                * lamp.bowl_r,  # clears the far pole; R + 1 leaves a cap behind
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # Round the cut rim over, on a decreasing ladder: half the wall is the
        # most OCC will fillet an annulus to, and it often refuses even that. A
        # failure here costs nothing but a squarer mock, and fillet_edge
        # restores the builder rather than poisoning it.
        rim = bowl.edges().filter_by_position(
            Axis.Z, rim_from_centre - 0.01, rim_from_centre + 0.01
        )
        for fraction in (0.45, 0.3, 0.2):
            if fillet_edge(bowl, rim, lamp.bowl_wall * fraction):
                break
        # The lampholder hole, drilled through the bottom pole.
        with Locations((0, 0, -lamp.bowl_r)):
            Cylinder(
                radius=lamp.bowl_hole_d / 2,
                height=4 * lamp.bowl_wall,
                mode=Mode.SUBTRACT,
            )

    # Turn it over: the rim plane becomes z = 0 and the dome goes up. The bead
    # goes on afterwards, in that pose, for two reasons -- it is measured from
    # the rim plane, and adding it first would put a second ring of edges at the
    # rim height the fillet above selects on.
    part = reseat_on_bed(bowl.part, flip=True)
    if lamp.bead_h > 0 and lamp.bead_w > 0:
        with BuildPart() as beaded:
            add(part)
            add(_bead(lamp))
        part = as_part(beaded.part)
    part.label = "bowl (bought)"
    part.color = STEEL
    return part


def create(**params) -> Part:
    """Entry point for ``uv run show salad_bowl_lamp.bowl`` and the website."""
    return create_bowl(Lamp.of(**params))


__all__ = ["IS_ASSEMBLY", "PARAMS", "STEEL", "create", "create_bowl"]
