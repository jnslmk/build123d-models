"""Three lamps and three corners, closed into a flat equilateral loop.

    uv run show led_profiles.assemblies.triangle
    uv run export led_profiles.assemblies.triangle

The view that exercises most of the family at once -- three lamps, three
corners, twelve straps -- and the only one whose geometry has to *close*
exactly, which is why the side length is derived here (``triangle_vertices``)
rather than typed in.
"""

from __future__ import annotations

from math import atan2, cos, degrees, radians, sin, sqrt

from build123d import Compound, Location, Part, Pos, Rotation

from models.lib.edges import as_part

from .. import config as c
from .. import corner as corner_mod
from .. import mount_config as m
from .. import strap as strap_mod
from ..assembly import PARAMS, parts as lamp_parts

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True

# The tube's underside, above a corner's own back face (z=0) -- see the
# CONVENTIONS note this package works under: mount_config measures z from the
# bed, a corner adds its plinth on top of that.
CORNER_TUBE_LIFT = corner_mod.PLINTH_H + m.TUBE_UNDER_Z


def triangle_vertices(
    length: float = c.LENGTH, angle: float = 60.0
) -> list[tuple[float, float]]:
    """The 3 vertex (x, y) positions of the triangle this length of tube forms.

    Not a free choice. A corner's cradle begins ``corner.cradle_start(angle)``
    from its vertex (the gland setback plus the cap thickness -- the unlit run
    corner.py's docstring prices at ~62.8 mm for a 60 deg corner), so one edge,
    a full lamp long, reaches from ``start`` past its near vertex to
    ``side - start`` short of its far one. Closing the loop needs

        side = length + 2 * start

    exactly -- not the tube length alone -- which is why this is a function
    and not a hand-typed constant.
    """
    start = corner_mod.cradle_start(angle)
    side = length + 2 * start
    circumradius = side / sqrt(3)
    return [
        (
            circumradius * cos(radians(90 + 120 * i)),
            circumradius * sin(radians(90 + 120 * i)),
        )
        for i in range(3)
    ]


def _corner_rotation(vertex: tuple[float, float]) -> float:
    """Heading that points a corner's bisector at the triangle's centroid.

    The corner's own included angle (60 deg) is exactly the triangle's
    interior angle, so aiming the bisector at the centroid lands *both* arms
    on their adjacent edges at once -- verified numerically against the edge
    bearings computed independently below, for all three vertices, to within
    floating point.
    """
    vx, vy = vertex
    return degrees(atan2(-vy, -vx)) - 90.0


def _edge_xform(vertex: tuple[float, float], bearing: float, start: float) -> Location:
    """World transform for a tube-local part, landing it on the arm that
    leaves ``vertex`` along ``bearing`` (degrees from +X)."""
    origin_x = vertex[0] + start * cos(radians(bearing))
    origin_y = vertex[1] + start * sin(radians(bearing))
    return Pos(origin_x, origin_y, CORNER_TUBE_LIFT) * Rotation(0, 0, bearing)


def _arm_straps(
    vertex: tuple[float, float], bearing: float, start: float, tag: str
) -> list[Part]:
    """Both straps on one cradle: the arm reaching out from ``vertex``."""
    xform = _edge_xform(vertex, bearing, start)
    straps: list[Part] = []
    for station in m.STRAP_STATIONS:
        tube_frame = Pos(0, 0, -m.TUBE_UNDER_Z) * strap_mod.seated(station)
        placed = as_part(xform * tube_frame)
        straps.append(strap_mod.labelled(placed, tag))
    return straps


def create_triangle(length: float = c.LENGTH) -> Compound:
    """Three lamps and three 60 deg corners, closed into a flat equilateral loop.

    Vertex positions come from ``triangle_vertices``, so the side length is
    derived from the tube length and ``corner.cradle_start(60)`` rather than
    guessed. Everything below is placed straight in the world frame from
    those vertices and the edge bearings between them -- the same approach
    ``checks._tube_clears_corner`` uses to fit a single corner. The corners'
    print pose already opens their channel along +Z, so leaving
    ``rotation_deg`` and every vertex's z at 0 is what keeps the whole loop
    coplanar with the LEDs facing out of that plane.
    """
    angle = 60.0
    start = corner_mod.cradle_start(angle)
    verts = triangle_vertices(length, angle)

    children: list[Part] = []
    for i, v in enumerate(verts):
        corner = corner_mod.seated(
            angle, position=(v[0], v[1], 0.0), rotation_deg=_corner_rotation(v)
        )
        corner.label = f"corner {i} ({angle:.0f} deg)"
        children.append(corner)

    for i in range(3):
        v_from, v_to = verts[i], verts[(i + 1) % 3]
        bearing = degrees(atan2(v_to[1] - v_from[1], v_to[0] - v_from[0]))
        xform = _edge_xform(v_from, bearing, start)

        # cable=False: the pigtails at a corner are a jumper loop inside the
        # corner's channel, not a straight run into open air -- see
        # ``assembly.parts``. The glands themselves stay, since clearing two of
        # them nose to nose is what sets this triangle's side length.
        for part in lamp_parts(length, cable=False):
            moved = as_part(xform * part)
            moved.label = f"{part.label} (lamp {i})"
            moved.color = part.color
            children.append(moved)

        children.extend(_arm_straps(v_from, bearing, start, f"edge {i} near"))
        children.extend(_arm_straps(v_to, bearing + 180.0, start, f"edge {i} far"))

    assembly = Compound(children=children)
    assembly.label = f"triangle ({length:.0f} mm lamps, {angle:.0f} deg corners)"
    return assembly


def create(length: float = c.LENGTH) -> Compound:
    """Entry point for ``uv run show led_profiles.assemblies.triangle``."""
    return create_triangle(length)


__all__ = [
    "CORNER_TUBE_LIFT",
    "IS_ASSEMBLY",
    "PARAMS",
    "create",
    "create_triangle",
    "triangle_vertices",
]
