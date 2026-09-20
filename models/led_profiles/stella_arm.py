"""Support-free arm for one stella-octangula vertex connector.

A short saddle starts ``CRADLE_START`` from the mathematical vertex so the lamp
keeps its endcap and gland. Two triangular ribs print from the bed to a flat
sloped tab; one M5 clearance hole passes through that tab, and two tapered keys
enter the round core to carry shear. The open centre between the ribs leaves the
M5 nut reachable from the back.

The saddle has one low through-bolt ear and takes one separate drop-on keeper.
Print pose is authored directly: saddle mouth up, beam and ribs on z=0.
"""

from __future__ import annotations

from math import sqrt

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.lib.edges import (
    as_part,
    bottom_chamfer_tool,
    chamfer_edge,
    fillet_edge,
    top_chamfer_tool,
)

from . import cradle as cradle_mod
from . import mount_config as m
from . import stella_config as s

ARM_COLOR = Color(0.24, 0.27, 0.31)

# Outward radial normal of the core plane in an arm's print frame. Local +X is
# the lamp axis and +Z the diffuser direction.
CORE_NORMAL = (-sqrt(2 / 3), 0.0, 1 / sqrt(3))
INTO_ARM = (-CORE_NORMAL[0], 0.0, -CORE_NORMAL[2])
FACE_TANGENT = (1 / sqrt(3), 0.0, sqrt(2 / 3))


def _offset(
    point: tuple[float, float, float],
    direction: tuple[float, float, float],
    distance: float,
) -> tuple[float, float, float]:
    return (
        point[0] + direction[0] * distance,
        point[1] + direction[1] * distance,
        point[2] + direction[2] * distance,
    )


def _face_point(x: float, y: float = 0.0) -> tuple[float, float, float]:
    return x, y, sqrt(2) * x


def _rib() -> Part:
    """One edge rib supporting the sloped tab without blocking its fastener."""
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
        extrude(amount=s.RIB_W / 2, both=True)
        fillet_edge(bp, bp.edges().filter_by(Axis.Z), s.RIB_EDGE_FILLET)
        chamfer_edge(
            bp,
            [edge for edge in bp.edges() if edge not in bp.edges().filter_by(Axis.Z)],
            s.FLANGE_CHAMFER,
        )
    return bp.part


def _key(point: tuple[float, float, float]) -> Part:
    """Tapered anti-rotation key with a lead-in on every entering edge."""
    plane = Plane(origin=point, x_dir=(0.0, 1.0, 0.0), z_dir=CORE_NORMAL)
    with BuildPart() as bp:
        with BuildSketch(plane):
            RectangleRounded(s.KEY_W, s.KEY_D, min(s.TAB_CORNER_R, s.KEY_W / 3))
        with BuildSketch(plane.offset(s.KEY_PROTRUSION)):
            RectangleRounded(
                s.KEY_W - 2 * s.KEY_LEAD_IN,
                s.KEY_D - 2 * s.KEY_LEAD_IN,
                min(s.TAB_CORNER_R, s.KEY_W / 3) - s.KEY_LEAD_IN / 2,
            )
        loft(ruled=True)
    return bp.part


def _tab() -> Part:
    """Flat keyed tab with one M5 through-hole and an open rear fastener seat."""
    bolt_point = _face_point(s.BOLT_FACE_X)
    front = Plane(origin=bolt_point, x_dir=(0.0, 1.0, 0.0), z_dir=INTO_ARM)
    with BuildPart() as bp:
        with BuildSketch(front):
            RectangleRounded(s.TAB_W, s.TAB_H, s.TAB_CORNER_R)
        extrude(amount=s.TAB_T)
        for depth in (0.0, s.TAB_T):
            perimeter = []
            for edge in bp.edges():
                centre = edge.center()
                edge_depth = (
                    (centre.X - bolt_point[0]) * INTO_ARM[0]
                    + (centre.Y - bolt_point[1]) * INTO_ARM[1]
                    + (centre.Z - bolt_point[2]) * INTO_ARM[2]
                )
                if abs(edge_depth - depth) < 0.01:
                    perimeter.append(edge)
            chamfer_edge(bp, perimeter, s.FLANGE_CHAMFER)

        hole_origin = _offset(bolt_point, CORE_NORMAL, 1.0)
        hole_plane = Plane(
            origin=hole_origin,
            x_dir=(0.0, 1.0, 0.0),
            z_dir=INTO_ARM,
        )
        add(
            as_part(
                hole_plane.location
                * Cylinder(
                    s.BOLT_CLEAR_D / 2,
                    s.TAB_T + 2.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            ),
            mode=Mode.SUBTRACT,
        )

        front_mouth = Plane(
            origin=bolt_point,
            x_dir=(0.0, 1.0, 0.0),
            z_dir=INTO_ARM,
        )
        add(
            as_part(
                front_mouth.location
                * Cone(
                    s.BOLT_CLEAR_D / 2 + s.BOLT_LEAD_IN,
                    s.BOLT_CLEAR_D / 2,
                    s.BOLT_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            ),
            mode=Mode.SUBTRACT,
        )
        back_point = _offset(bolt_point, INTO_ARM, s.TAB_T)
        back_mouth = Plane(
            origin=back_point,
            x_dir=(0.0, 1.0, 0.0),
            z_dir=CORE_NORMAL,
        )
        add(
            as_part(
                back_mouth.location
                * Cone(
                    s.BOLT_CLEAR_D / 2 + s.BOLT_LEAD_IN,
                    s.BOLT_CLEAR_D / 2,
                    s.BOLT_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            ),
            mode=Mode.SUBTRACT,
        )

        for y in (-s.KEY_Y, s.KEY_Y):
            add(_key(_face_point(s.BOLT_FACE_X, y)))
    return bp.part


def _support_ribs() -> Part:
    rib = _rib()
    centre = s.TAB_W / 2 - s.RIB_W / 2
    with BuildPart() as bp:
        for y in (-centre, centre):
            add(as_part(Plane(origin=(0.0, y, 0.0)).location * rib))
    return bp.part


def _beam() -> Part:
    """Low plate joining the ribbed tab to the saddle without entering the gland."""
    start = s.FLANGE_RUN - 2.0
    length = s.BEAM_END - start
    with BuildPart() as bp:
        with BuildSketch():
            with Locations((start, 0.0)):
                RectangleRounded(
                    length,
                    s.BEAM_W,
                    2.0,
                    align=(Align.MIN, Align.CENTER),
                )
        extrude(amount=s.BEAM_T)
        chamfer_edge(bp, bp.edges().filter_by(Plane.XY), s.CORE_EDGE_CHAMFER)
    return bp.part


def _keeper_ear() -> Part:
    """Low M4 through-bolt crossbar beneath the saddle's single keeper."""
    with BuildPart() as bp:
        with BuildSketch():
            RectangleRounded(
                s.KEEPER_W,
                2 * s.KEEPER_EAR_OUT,
                s.KEEPER_EAR_CORNER_R,
            )
        extrude(amount=s.KEEPER_FOOT_T)
        add(
            bottom_chamfer_tool(
                s.KEEPER_W,
                2 * s.KEEPER_EAR_OUT,
                s.KEEPER_EAR_CORNER_R,
                0.0,
                s.KEEPER_EDGE_CHAMFER,
            ),
            mode=Mode.SUBTRACT,
        )
        add(
            top_chamfer_tool(
                s.KEEPER_W,
                2 * s.KEEPER_EAR_OUT,
                s.KEEPER_EAR_CORNER_R,
                s.KEEPER_FOOT_T,
                s.KEEPER_EDGE_CHAMFER,
            ),
            mode=Mode.SUBTRACT,
        )

        with BuildSketch(Plane.YZ.offset(-s.KEEPER_W / 2)):
            add(cradle_mod.tube_section(m.BORE_FIT))
        extrude(amount=s.KEEPER_W, mode=Mode.SUBTRACT)

        with Locations(
            (0.0, -s.KEEPER_BOLT_U, -1.0),
            (0.0, s.KEEPER_BOLT_U, -1.0),
        ):
            Cylinder(
                s.KEEPER_BOLT_CLEAR_D / 2,
                s.KEEPER_FOOT_T + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        for z, bottom_r, top_r in (
            (
                0.0,
                s.KEEPER_BOLT_CLEAR_D / 2 + s.KEEPER_BOLT_LEAD_IN,
                s.KEEPER_BOLT_CLEAR_D / 2,
            ),
            (
                s.KEEPER_FOOT_T - s.KEEPER_BOLT_LEAD_IN,
                s.KEEPER_BOLT_CLEAR_D / 2,
                s.KEEPER_BOLT_CLEAR_D / 2 + s.KEEPER_BOLT_LEAD_IN,
            ),
        ):
            with Locations(
                (0.0, -s.KEEPER_BOLT_U, z),
                (0.0, s.KEEPER_BOLT_U, z),
            ):
                Cone(
                    bottom_r,
                    top_r,
                    s.KEEPER_BOLT_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
    return bp.part


def _saddle() -> Part:
    """Short trough with one low through-bolt keeper station."""
    cradle = cradle_mod.create_cradle(
        length=s.SADDLE_LEN,
        stations=(),
        treat=False,
    )
    ear = as_part(Plane(origin=(s.KEEPER_STATION, 0.0, 0.0)).location * _keeper_ear())
    with BuildPart() as bp:
        add(cradle)
        add(ear)
        cradle_mod.treat_edges(bp)
    return bp.part


def create_arm() -> Part:
    """One printable arm: keyed tab, support ribs, beam and short saddle."""
    saddle = as_part(Plane(origin=(s.CRADLE_START, 0.0, 0.0)).location * _saddle())
    with BuildPart() as bp:
        add(_support_ribs())
        add(_tab())
        add(_beam())
        add(saddle)
    part = bp.part
    part.label = "stella vertex arm"
    part.color = ARM_COLOR
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stella_arm``."""
    return create_arm()


__all__ = ["CORE_NORMAL", "FACE_TANGENT", "INTO_ARM", "create", "create_arm"]
