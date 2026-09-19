"""Flat vertex core for the modular stella-octangula connector.

Six M5 clearance holes clamp three cradle arms to the top face; their captive
nuts live in the arms. The rounded eye accepts a 10 mm soft sling. The core
prints flat, so its layers carry sling load in-plane rather than in peel.
"""

from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    SlotOverall,
    add,
    extrude,
    loft,
    make_hull,
)

from models.lib.edges import as_part, chamfer_edge

from . import stella_config as s

CORE_COLOR = Color(0.17, 0.20, 0.24)


def bolt_centers(offset: float) -> list[tuple[float, float]]:
    """Six bolt axes: a tangential pair for each of the three cradle arms."""
    radius = s.core_hole_radius(offset)
    points: list[tuple[float, float]] = []
    for angle in (0.0, 120.0, 240.0):
        ca, sa = cos(radians(angle)), sin(radians(angle))
        for x, y in ((-s.BOLT_Y, -radius), (s.BOLT_Y, -radius)):
            points.append((x * ca - y * sa, x * sa + y * ca))
    return points


def eye_center(offset: float) -> tuple[float, float]:
    """Centre of the sling lobe in the gap between two arm flanges."""
    radius = s.core_hole_radius(offset)
    distance = radius + s.CORE_PAD_R + s.EYE_R - s.EYE_NECK_OVERLAP
    angle = radians(-30.0)  # between arm flanges, not underneath one
    return (distance * cos(angle), distance * sin(angle))


def _outline(offset: float):
    """Convex rounded plate around all bolt pads and the single sling eye."""
    with BuildSketch() as seeds:
        with Locations(*bolt_centers(offset)):
            Circle(s.CORE_PAD_R)
        with Locations(eye_center(offset)):
            Circle(s.EYE_R)
    with BuildSketch() as outline:
        add(make_hull(seeds.sketch.edges()))
    return outline.sketch


def _slot_lead_in(z: float, top: bool) -> Part:
    """Boolean obround lead-in matching the sling slot's own cross-section."""
    wide_w = s.SLING_SLOT_W + 2 * s.CORE_EDGE_CHAMFER
    wide_h = s.SLING_SLOT_H + 2 * s.CORE_EDGE_CHAMFER
    z_wide = z if not top else z + s.CORE_EDGE_CHAMFER
    z_narrow = z + s.CORE_EDGE_CHAMFER if not top else z
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_wide)):
            SlotOverall(wide_w, wide_h)
        with BuildSketch(Plane.XY.offset(z_narrow)):
            SlotOverall(s.SLING_SLOT_W, s.SLING_SLOT_H)
        loft(ruled=True)
    return tool.part


def create_core(offset: float = 0.0) -> Part:
    """One core; ``offset`` is the tetrahedron's outward crossing layer."""
    centres = bolt_centers(offset)
    eye = eye_center(offset)
    with BuildPart() as bp:
        with BuildSketch():
            add(_outline(offset))
        extrude(amount=s.CORE_T)

        # Treat the simple outer plate before holes reach either face.
        chamfer_edge(
            bp,
            bp.edges().filter_by_position(Axis.Z, s.CORE_T - 0.01, s.CORE_T + 0.01),
            s.CORE_EDGE_CHAMFER,
        )
        chamfer_edge(
            bp,
            bp.edges().filter_by_position(Axis.Z, -0.01, 0.01),
            s.CORE_EDGE_CHAMFER,
        )

        with Locations(*[(x, y, -1.0) for x, y in centres]):
            Cylinder(
                s.BOLT_CLEAR_D / 2,
                s.CORE_T + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        for z, bottom_r, top_r in (
            (0.0, s.BOLT_CLEAR_D / 2 + s.BOLT_LEAD_IN, s.BOLT_CLEAR_D / 2),
            (
                s.CORE_T - s.BOLT_LEAD_IN,
                s.BOLT_CLEAR_D / 2,
                s.BOLT_CLEAR_D / 2 + s.BOLT_LEAD_IN,
            ),
        ):
            with Locations(*[(x, y, z) for x, y in centres]):
                Cone(
                    bottom_r,
                    top_r,
                    s.BOLT_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

        with BuildSketch(Plane.XY.offset(-1.0)):
            with Locations(eye):
                SlotOverall(s.SLING_SLOT_W, s.SLING_SLOT_H)
        extrude(amount=s.CORE_T + 2.0, mode=Mode.SUBTRACT)
        add(
            as_part(Pos(eye[0], eye[1], 0.0) * _slot_lead_in(0.0, top=False)),
            mode=Mode.SUBTRACT,
        )
        add(
            as_part(
                Pos(eye[0], eye[1], 0.0)
                * _slot_lead_in(s.CORE_T - s.CORE_EDGE_CHAMFER, top=True)
            ),
            mode=Mode.SUBTRACT,
        )

    part = bp.part
    part.label = "stella vertex core"
    part.color = CORE_COLOR
    return part


def create() -> Part:
    """The four cores for the unshifted tetrahedron."""
    return create_core(0.0)


__all__ = ["bolt_centers", "create", "create_core", "eye_center"]
