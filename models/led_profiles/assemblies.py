"""Assembly views: how the mounting family actually holds a lamp.

Three scenes, each a labelled, coloured ``Compound``. Every mount here is
placed with the family's own ``seated()`` helpers -- ``endcap.seated``,
``strap.seated``, ``feet.seated``, ``corner.seated``, ``stand.seated`` /
``seated_legs`` -- nothing here re-derives a transform those already own. The
one genuinely new placement is the triangle's vertex geometry (see
``triangle_vertices``) and the stand's tube-to-vertical rotation (see
``_to_socket``).

``strap.py`` never sets a colour on the part it returns (nothing else in the
family assembles it loose enough to need one), so this module supplies one --
the same ASA grey every other mount in the family already uses.
"""

from __future__ import annotations

from math import atan2, cos, degrees, radians, sin, sqrt

from build123d import Color, Compound, Location, Part, Pos, Rotation

from models.lib.edges import as_part

from . import config as c
from . import corner as corner_mod
from . import feet as feet_mod
from . import mount_config as m
from . import stand as stand_mod
from . import strap as strap_mod
from .assembly import parts as lamp_parts
from .endcap import CAP_T

STRAP_COLOR = Color(0.30, 0.32, 0.36)  # matches CORNER_COLOR / STAND_COLOR / FOOT_COLOR


def _labelled_strap(placed: Part, tag: str) -> Part:
    """A strap already moved into place, labelled and coloured.

    ``Location * Part`` (what every ``xform * strap`` placement in this module
    is) drops both, so this is the one place that puts them back rather than
    repeating the two lines at every call site.
    """
    placed.label = f"strap ({tag})"
    placed.color = STRAP_COLOR
    return placed


# --------------------------------------------------------------- suspended

# Airy/Bessel points: the two-point support that levels a simply-supported
# beam's ends with its own midspan sag -- the standard way to rest or hang a
# long, floppy thing (an optical flat, a surveyor's staff) without visible
# droop at the tips.
BESSEL_FRACTION = 0.2203


def bessel_points(length: float = c.LENGTH) -> tuple[float, float]:
    """The two support x's along the tube -- where the eye bolts actually hang."""
    span = BESSEL_FRACTION * length
    return span, length - span


def _foot_and_straps(support_x: float, tag: str) -> list[Part]:
    """An eye foot centred on ``support_x``, plus its two straps.

    ``feet.seated``/``strap.seated`` both take the cradle's *near end*, but
    the actual hang point -- the eye-bolt holes -- sits at the cradle's own
    mid (``mount_config.CRADLE_LEN / 2``), so the near end is back-solved from
    the support point rather than the other way round.
    """
    near_end = support_x - m.CRADLE_LEN / 2
    parts: list[Part] = [feet_mod.seated(near_end)]
    for station in m.STRAP_STATIONS:
        strap = as_part(
            Pos(0, 0, -m.TUBE_UNDER_Z) * strap_mod.seated(near_end + station)
        )
        parts.append(_labelled_strap(strap, tag))
    return parts


def create_suspended(length: float = c.LENGTH) -> Compound:
    """One lamp hung from two eye feet at the Bessel points, straps fitted."""
    x1, x2 = bessel_points(length)
    children = [
        *lamp_parts(length),
        *_foot_and_straps(x1, "near"),
        *_foot_and_straps(x2, "far"),
    ]
    assembly = Compound(children=children)
    assembly.label = f"suspended lamp ({length:.0f} mm, Bessel points)"
    return assembly


# ----------------------------------------------------------------- standing

# Rotates a tube-local part (config's own convention: x along the tube from
# its near end, y = u, z = height from the underside, centred at HEIGHT / 2)
# so the tube's length axis becomes vertical. Verified against unit vectors:
# local +X -> global +Z, local +Y -> global +X, local +Z -> global +Y.
STAND_UPRIGHT = Rotation(0, -90, 0) * Rotation(-90, 0, 0)


def _to_socket(part: Part) -> Part:
    """A tube-local part onto the stand's vertical socket.

    x (0 at the aluminium's near end) becomes global Z, landing on
    ``stand.SEAT_Z + CAP_T`` -- exactly where the hub's own tube bore starts
    (``stand.create_stand_hub``), so x=-CAP_T (an endcap's outer face) lands
    on ``SEAT_Z`` itself: the seat. y and z (height, centred on HEIGHT / 2)
    become global X and Y, which is what puts the tube's own axis on the
    hub's vertical axis -- see ``stand.SINK``.
    """
    return as_part(
        Pos(0, -c.HEIGHT / 2, stand_mod.SEAT_Z + CAP_T) * (STAND_UPRIGHT * part)
    )


def _mount_to_socket(part: Part) -> Part:
    """A mount-local part (bed frame, see ``mount_config``) onto the same socket."""
    return _to_socket(as_part(Pos(0, 0, -m.TUBE_UNDER_Z) * part))


def create_standing(length: float = c.LENGTH) -> Compound:
    """One lamp standing vertically in the tripod hub, legs deployed.

    The lamp is rotated onto the hub's vertical socket axis by ``_to_socket``;
    the offset baked into that transform is what lands the lower endcap's
    outer face exactly on the hub's seat, not merely somewhere in the bore.
    Straps go on at all three of the stand's own strap stations
    (``stand.STATIONS``, which are global heights -- back-solved to the
    tube-local x that ``strap.seated`` wants).
    """
    hub = stand_mod.seated()
    legs = stand_mod.seated_legs()

    lamp: list[Part] = []
    for part in lamp_parts(length):
        moved = _to_socket(part)
        moved.label = part.label
        moved.color = part.color
        lamp.append(moved)

    straps: list[Part] = []
    for i, z in enumerate(stand_mod.STATIONS):
        local_station = z - (stand_mod.SEAT_Z + CAP_T)
        moved = _mount_to_socket(strap_mod.seated(local_station))
        straps.append(_labelled_strap(moved, f"station {i}"))

    assembly = Compound(children=[hub, *legs, *lamp, *straps])
    assembly.label = f"standing lamp ({length:.0f} mm, tripod stand)"
    return assembly


# ---------------------------------------------------------------- triangle

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
        straps.append(_labelled_strap(placed, tag))
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

        for part in lamp_parts(length):
            moved = as_part(xform * part)
            moved.label = f"{part.label} (lamp {i})"
            moved.color = part.color
            children.append(moved)

        children.extend(_arm_straps(v_from, bearing, start, f"edge {i} near"))
        children.extend(_arm_straps(v_to, bearing + 180.0, start, f"edge {i} far"))

    assembly = Compound(children=children)
    assembly.label = f"triangle ({length:.0f} mm lamps, {angle:.0f} deg corners)"
    return assembly


def create() -> Compound:
    """Entry point for ``uv run show led_profiles.assemblies``.

    Returns the triangle: the one view that exercises every part in the
    family at once (three lamps, three corners, twelve straps) and the one
    whose geometry has to close exactly, which makes it the most informative
    single picture of how the family fits together.
    """
    return create_triangle()


__all__ = [
    "bessel_points",
    "create",
    "create_standing",
    "create_suspended",
    "create_triangle",
    "triangle_vertices",
]
