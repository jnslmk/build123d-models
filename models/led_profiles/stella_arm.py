"""Support-free cradle arm for one stella-octangula vertex connector.

The existing cradle starts ``CRADLE_START`` from the mathematical vertex so a
finished lamp keeps its endcap and gland. A triangular flange rises from the bed
to the vertex core's plane; two M5 captive nuts open on that mating face. The
core closes the pockets and its bolts pull the arm onto the full face.

Print pose is authored directly: cradle mouth up, beam and flange on z=0.
"""

from __future__ import annotations

from math import sqrt

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Color,
    Cylinder,
    Mode,
    Part,
    Plane,
    Polygon,
    RectangleRounded,
    RegularPolygon,
    add,
    extrude,
)

from models.lib.edges import as_part, chamfer_edge

from . import cradle as cradle_mod
from . import stella_config as s

ARM_COLOR = Color(0.24, 0.27, 0.31)

# Outward radial normal of the core plane in an arm's print frame. Local +X is
# the lamp axis and +Z the diffuser direction.
CORE_NORMAL = (-sqrt(2 / 3), 0.0, 1 / sqrt(3))
INTO_ARM = (-CORE_NORMAL[0], 0.0, -CORE_NORMAL[2])
FACE_TANGENT = (1 / sqrt(3), 0.0, sqrt(2 / 3))


def _flange() -> Part:
    """Triangular flange with two captive M5 nut pockets in its sloped face."""
    with BuildPart() as bp:
        with BuildSketch(
            Plane(
                origin=(0.0, 0.0, 0.0),
                x_dir=(1.0, 0.0, 0.0),
                z_dir=(0.0, -1.0, 0.0),
            )
        ):
            Polygon(
                (0.0, 0.0),
                (s.FLANGE_RUN, 0.0),
                (s.FLANGE_RUN, s.FLANGE_H),
                align=(Align.MIN, Align.MIN),
            )
        extrude(amount=s.FLANGE_W / 2, both=True)

        # The prism is still simple here. Treating before the pockets avoids the
        # exact OCC failure mode caused by selecting edges off a perforated face.
        chamfer_edge(bp, bp.edges(), s.FLANGE_CHAMFER)

        for y in (-s.BOLT_Y, s.BOLT_Y):
            point = (
                s.BOLT_FACE_X,
                y,
                sqrt(2) * s.BOLT_FACE_X,
            )
            pocket_plane = Plane(origin=point, x_dir=(0.0, 1.0, 0.0), z_dir=INTO_ARM)
            with BuildSketch(pocket_plane):
                RegularPolygon(s.NUT_CIRCUM_R, 6, rotation=30.0)
            extrude(amount=s.NUT_DEPTH, mode=Mode.SUBTRACT)
            add(
                as_part(
                    pocket_plane.location
                    * Cylinder(
                        s.NUT_RELIEF_D / 2,
                        s.NUT_DEPTH + 5.0,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                ),
                mode=Mode.SUBTRACT,
            )
    return bp.part


def _beam() -> Part:
    """Low plate joining the flange to the cradle without entering the gland."""
    start = s.FLANGE_RUN - 2.0
    length = s.BEAM_END - start
    with BuildPart() as bp:
        with BuildSketch():
            RectangleRounded(length, s.BEAM_W, 2.0, align=(Align.MIN, Align.CENTER))
        extrude(amount=s.BEAM_T)
        chamfer_edge(bp, bp.edges().filter_by(Plane.XY), s.CORE_EDGE_CHAMFER)
    return bp.part


def create_arm() -> Part:
    """One printable arm: flange, under-gland beam and the shared cradle."""
    cradle = as_part(
        Plane(origin=(s.CRADLE_START, 0.0, 0.0)).location * cradle_mod.create_cradle()
    )
    with BuildPart() as bp:
        add(_flange())
        add(_beam())
        add(cradle)
    part = bp.part
    part.label = "stella vertex arm"
    part.color = ARM_COLOR
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stella_arm``."""
    return create_arm()


__all__ = ["CORE_NORMAL", "FACE_TANGENT", "create", "create_arm"]
