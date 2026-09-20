"""Slim drop-on keeper for one Stella arm saddle.

One 10 mm band replaces the two shared 18 mm straps used by the other mounts.
Its straight legs pass outside the saddle walls at a FREE-class ASA gap, land on
the arm's low crossbar, and take two M4 through-bolts with exposed nuts beneath.
The arch clears both aluminium and diffuser; it captures the profile without
clamping its 0.5 mm wall.

Print pose: feet on the bed, arch up. Assembly is a straight vertical drop.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Color,
    Cone,
    Cylinder,
    Line,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Rotation,
    add,
    extrude,
    sweep,
)

from models.lib.edges import as_part, chamfer_edge

from . import config as c
from . import stella_config as s

KEEPER_COLOR = Color(0.30, 0.32, 0.36)
BORE_HALF_W = (c.WIDTH + s.KEEPER_INNER_CLEAR) / 2


def _rounded_prism(
    width: float,
    depth: float,
    height: float,
    radius: float,
    *,
    z0: float = 0.0,
    treat_ends: bool = False,
) -> Part:
    """Rounded rectangular prism, optionally chamfered at its exposed ends."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(z0)):
            RectangleRounded(width, depth, radius)
        extrude(amount=height)
        if treat_ends:
            for z in (z0, z0 + height):
                chamfer_edge(
                    bp,
                    bp.edges().filter_by_position(Axis.Z, z - 0.01, z + 0.01),
                    s.KEEPER_EDGE_CHAMFER,
                )
    return bp.part


def _band() -> Part:
    """Rounded arch whose raw end faces are buried in the shoulder blocks."""
    centre_r = BORE_HALF_W + s.KEEPER_LEG_T / 2
    shoulder_z = s.KEEPER_AXIS_Z + (c.HEIGHT - c.WIDTH) / 2
    end_z = s.KEEPER_LAND_Z + s.KEEPER_FUSION_OVERLAP

    with BuildLine(Plane.XZ) as path:
        Line((-centre_r, end_z), (-centre_r, shoulder_z))
        CenterArc((0.0, shoulder_z), centre_r, 180.0, -180.0)
        Line((centre_r, shoulder_z), (centre_r, end_z))

    start = Plane(
        origin=(-centre_r, 0.0, end_z),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, 0.0, 1.0),
    )
    with BuildPart() as bp:
        with BuildSketch(start):
            RectangleRounded(
                s.KEEPER_LEG_T,
                s.KEEPER_W - 2 * s.KEEPER_EDGE_CHAMFER,
                0.75,
            )
        sweep(path=path.wire())
    # OCC orients this XZ-plane sweep inward; normalize it before a later
    # builder union interprets the band as a cutting solid.
    part = bp.part
    return Part(part.wrapped.Reversed()) if part.volume < 0 else part


def _foot() -> Part:
    """One rounded bolt foot with top and bed edges chamfered."""
    return _rounded_prism(
        s.KEEPER_EAR_OUT - s.KEEPER_LEG_INNER_U,
        s.KEEPER_W,
        s.KEEPER_FOOT_T,
        s.KEEPER_EAR_CORNER_R,
        treat_ends=True,
    )


def _leg() -> Part:
    """Straight outside leg; both end faces disappear inside adjoining solids."""
    return _rounded_prism(
        s.KEEPER_LEG_T,
        s.KEEPER_W,
        s.KEEPER_LAND_Z,
        0.75,
        z0=s.KEEPER_FOOT_T / 2,
    )


def _shoulder() -> Part:
    """Treated bridge from an outside leg to the narrower profile arch."""
    inner = BORE_HALF_W - s.KEEPER_FUSION_OVERLAP
    return _rounded_prism(
        s.KEEPER_LEG_OUTER_U - inner,
        s.KEEPER_W,
        s.KEEPER_FOOT_T,
        1.0,
        z0=s.KEEPER_LAND_Z,
        treat_ends=True,
    )


def create_keeper() -> Part:
    """One printable keeper in bed-ready pose."""
    foot = _foot()
    leg = _leg()
    shoulder = _shoulder()
    foot_u = (s.KEEPER_EAR_OUT + s.KEEPER_LEG_INNER_U) / 2
    shoulder_inner = BORE_HALF_W - s.KEEPER_FUSION_OVERLAP
    shoulder_u = (s.KEEPER_LEG_OUTER_U + shoulder_inner) / 2
    with BuildPart() as bp:
        for side in (-1.0, 1.0):
            add(as_part(Pos(side * foot_u, 0.0, 0.0) * foot))
            add(as_part(Pos(side * s.KEEPER_LEG_CENTER_U, 0.0, 0.0) * leg))
            add(as_part(Pos(side * shoulder_u, 0.0, 0.0) * shoulder))
        add(_band())

        with Locations(
            (-s.KEEPER_BOLT_U, 0.0, -1.0),
            (s.KEEPER_BOLT_U, 0.0, -1.0),
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
                (-s.KEEPER_BOLT_U, 0.0, z),
                (s.KEEPER_BOLT_U, 0.0, z),
            ):
                Cone(
                    bottom_r,
                    top_r,
                    s.KEEPER_BOLT_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    part = bp.part
    part.label = "stella keeper"
    part.color = KEEPER_COLOR
    return part


def seated(x: float = 0.0) -> Part:
    """Move a keeper onto its arm saddle at axial station ``x``."""
    placed = as_part(
        Pos(x, 0.0, s.KEEPER_FOOT_T) * (Rotation(0, 0, 90) * create_keeper())
    )
    placed.label = "stella keeper"
    placed.color = KEEPER_COLOR
    return placed


def labelled(placed: Part, tag: str) -> Part:
    """Restore label and colour after an assembly transform."""
    placed.label = f"stella keeper ({tag})"
    placed.color = KEEPER_COLOR
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stella_keeper``."""
    return create_keeper()


__all__ = ["create", "create_keeper", "labelled", "seated"]
