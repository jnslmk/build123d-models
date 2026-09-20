"""Round vertex core for the modular stella-octangula connector.

Three M5 through-bolts clamp three arm tabs to one circular plate. Two shallow
keys per arm sit in free-fit pockets and carry in-plane shear, so a single bolt
can clamp each arm without also having to locate it. The central 20 x 10 mm slot
accepts a soft sling. The core prints flat, so both the sling and key loads stay
in the layer plane.
"""

from __future__ import annotations

from math import cos, radians, sin

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
    RectangleRounded,
    SlotOverall,
    add,
    extrude,
    loft,
)

from models.lib.edges import chamfer_edge

from . import stella_config as s

CORE_COLOR = Color(0.17, 0.20, 0.24)


def _rotated_point(tangent: float, radial: float, angle: float) -> tuple[float, float]:
    """Map one arm's tangential/radial core-plane coordinates into XY."""
    ca, sa = cos(radians(angle)), sin(radians(angle))
    x, y = tangent, -radial
    return x * ca - y * sa, x * sa + y * ca


def bolt_centers(offset: float) -> list[tuple[float, float]]:
    """Three bolt axes, one on the centreline of each arm tab."""
    radius = s.core_hole_radius(offset)
    return [_rotated_point(0.0, radius, angle) for angle in (0.0, 120.0, 240.0)]


def key_centers(offset: float) -> list[tuple[float, float, float]]:
    """Two anti-rotation key pockets flanking every bolt axis."""
    radius = s.core_hole_radius(offset)
    points: list[tuple[float, float, float]] = []
    for angle in (0.0, 120.0, 240.0):
        for tangent in (-s.KEY_Y, s.KEY_Y):
            x, y = _rotated_point(tangent, radius, angle)
            points.append((x, y, angle))
    return points


def eye_center(offset: float) -> tuple[float, float]:
    """The sling slot stays at the centre of either round core."""
    del offset
    return 0.0, 0.0


def _slot_lead_in(z: float, top: bool) -> Part:
    """Boolean obround lead-in matching the sling slot's cross-section."""
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


def _key_mouth_tool(x: float, y: float, angle: float) -> Part:
    """Taper the key pocket's mating-face mouth without changing bearing walls."""
    pocket_w = s.KEY_W + s.KEY_FIT
    pocket_d = s.KEY_D + s.KEY_FIT
    corner = min(s.TAB_CORNER_R, pocket_w / 3, pocket_d / 3)
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(-0.01)):
            with Locations((x, y)):
                RectangleRounded(
                    pocket_w + 2 * s.KEY_LEAD_IN,
                    pocket_d + 2 * s.KEY_LEAD_IN,
                    corner + s.KEY_LEAD_IN,
                    rotation=angle,
                )
        with BuildSketch(Plane.XY.offset(s.KEY_LEAD_IN)):
            with Locations((x, y)):
                RectangleRounded(
                    pocket_w,
                    pocket_d,
                    corner,
                    rotation=angle,
                )
        loft(ruled=True)
    return tool.part


def create_core(offset: float = 0.0) -> Part:
    """One circular core; ``offset`` selects the outward crossing layer."""
    centres = bolt_centers(offset)
    radius = s.core_outline_radius(offset)
    pocket_depth = s.KEY_PROTRUSION + s.KEY_DEPTH_RELIEF

    with BuildPart() as bp:
        Cylinder(radius, s.CORE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Treat the simple circular plate before holes and key pockets reach it.
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

        pocket_w = s.KEY_W + s.KEY_FIT
        pocket_d = s.KEY_D + s.KEY_FIT
        corner = min(s.TAB_CORNER_R, pocket_w / 3, pocket_d / 3)
        for x, y, angle in key_centers(offset):
            with BuildSketch():
                with Locations((x, y)):
                    RectangleRounded(
                        pocket_w,
                        pocket_d,
                        corner,
                        rotation=angle,
                    )
            extrude(amount=pocket_depth, mode=Mode.SUBTRACT)
            add(_key_mouth_tool(x, y, angle), mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(-1.0)):
            SlotOverall(s.SLING_SLOT_W, s.SLING_SLOT_H)
        extrude(amount=s.CORE_T + 2.0, mode=Mode.SUBTRACT)
        add(_slot_lead_in(0.0, top=False), mode=Mode.SUBTRACT)
        add(
            _slot_lead_in(s.CORE_T - s.CORE_EDGE_CHAMFER, top=True),
            mode=Mode.SUBTRACT,
        )

    part = bp.part
    part.label = "stella vertex core"
    part.color = CORE_COLOR
    return part


def create() -> Part:
    """The four cores for the unshifted tetrahedron."""
    return create_core(0.0)


__all__ = ["bolt_centers", "create", "create_core", "eye_center", "key_centers"]
