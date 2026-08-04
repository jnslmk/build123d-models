"""Corner connector: joins two lamps at a fixed angle to build geometric forms.

``angle`` is the **included angle between the two tube axes** -- 60 makes an
equilateral triangle, 90 a square, 120 a hexagon. Asking for 60 and getting a
hexagon corner is the obvious mistake, so it is worth saying twice.

The corner is mechanical only. Both tubes keep their glanded endcaps and the bus
crosses on an external jumper, which is what pushes the tube ends back from the
vertex: two glands pointing at each other are cylinders whose axes intersect, so
the clearance condition is not "twice the radius" but

    a         = (GLAND_ENV_D / 2) / tan(angle / 2)      20.8 mm at 60 deg
    cap face  = a + GLAND_PROUD                         50.8 mm
    aluminium = cap face + CAP_T                        62.8 mm

and the unlit run at a 60 deg vertex is 2 x 62.8 = **126 mm**. That is the price
of staying coplanar; ``docs/design-notes.md`` S2 records what was refused to
avoid it, and ``checks.py`` reports the number so a change to the gland cannot
make it worse quietly.

Shape: a V-shaped bar with a cradle at each end and an open channel down its
middle, in which the two endcaps, their glands and the jumper loop all sit. Two
numbers are not free choices:

* ``PLINTH_H`` -- the gland axis is 6 mm *below* the tube axis, so a Ø24 gland
  hangs 3 mm below the tube's underside and would cut straight through a 4 mm
  cradle floor. The cradles therefore stand on a plinth.
* ``ARM_WALL`` -- the channel has to clear the 27.2 mm cap collar, and a bar
  only as wide as the cradle would be left with 2.4 mm side walls. The arms are
  widened until the walls carry the out-of-plane load (see ``section_modulus``).

Print pose: back face on the bed, cradles and channel opening up. That is the
LED direction, so nothing overhangs and the first layer is the whole footprint.

One build123d trap shapes how this file is written: **a ``BuildSketch`` opened
inside a helper function does not attach to the caller's ``BuildPart``**, and
the following ``extrude`` raises "A face or sketch must be provided". Object
creation (``Cylinder`` and friends) *does* cross a function boundary, which
makes the failure look arbitrary. So every helper here builds a standalone
``Part`` before the main builder opens, and ``create_corner`` does all the
adding and subtracting itself -- the same pattern ``endcap.py`` uses for its
thread, and for the same reason.
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
    Cylinder,
    FontStyle,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    Rotation,
    Sketch,
    Text,
    add,
    extrude,
)

from models.lib.edges import as_part, chamfer_edge

from . import cradle as cr
from . import mount_config as m
from .endcap import CAP_T, CAP_W

# The gland's axis sits GLAND_Z above the tube's underside and it is
# GLAND_ENV_D across, so it hangs this far below that underside.
GLAND_DROP = m.GLAND_ENV_D / 2 - 9.0  # 3.0 -- endcap.GLAND_Z is 9.0
PLINTH_H = 8.0  # > GLAND_DROP + a printable floor

CHANNEL_W = max(CAP_W, m.GLAND_ENV_D) + 2.0  # 29.2, clears the cap collar
ARM_WALL = 6.0
BODY_W = CHANNEL_W + 2 * ARM_WALL  # 41.2
KNUCKLE_R = BODY_W / 2

TOP_Z = PLINTH_H + m.CRADLE_DEPTH  # 28.8 -- one height throughout, no step

LABEL_H = 5.0
LABEL_DEPTH = 0.6

CORNER_COLOR = Color(0.30, 0.32, 0.36)


def cradle_start(angle: float) -> float:
    """Vertex to where the aluminium -- and so the cradle -- begins."""
    return m.gland_setback(angle) + CAP_T


def section_modulus() -> float:
    """Z of the arm's U section about the out-of-plane axis, in mm^3.

    The design load is somebody pushing a tube tip out of the form's plane:
    10 N at 1.5 m is 15 N.m, and ASA under sustained load wants <= 10 MPa.
    """
    b, h = BODY_W, TOP_Z
    bv, hv = CHANNEL_W, TOP_Z - PLINTH_H
    a_o, a_v = b * h, bv * hv
    y_o, y_v = h / 2, PLINTH_H + hv / 2
    area = a_o - a_v
    y_bar = (a_o * y_o - a_v * y_v) / area
    i = (b * h**3 / 12 + a_o * (y_o - y_bar) ** 2) - (
        bv * hv**3 / 12 + a_v * (y_v - y_bar) ** 2
    )
    return i / max(y_bar, h - y_bar)


def _axis_bearings(angle: float) -> tuple[float, float]:
    """Bearings of the two tube axes in degrees from +X, straddling +Y."""
    half = angle / 2
    return 90.0 + half, 90.0 - half


def _axis_plane(bearing: float, distance: float) -> Plane:
    """A section plane across a tube axis, ``distance`` out from the vertex.

    Built explicitly rather than by rotating ``Plane.YZ``: ``Plane.rotated``
    turns a plane about its *own* axes, which would spin the section in its own
    face instead of swinging it round to the axis. What matters is that local y
    comes out along global Z, so every cradle section can be used unchanged.
    """
    a = radians(bearing)
    return Plane(
        origin=(distance * cos(a), distance * sin(a), 0),
        x_dir=(-sin(a), cos(a), 0),
        z_dir=(cos(a), sin(a), 0),
    )


def _arm_footprint(angle: float, length: float) -> Sketch:
    """The V-bar seen from the front: two arms and a rounded knuckle."""
    with BuildSketch() as s:
        Circle(KNUCKLE_R)
        for bearing in _axis_bearings(angle):
            with Locations(Location((0, 0, 0), (0, 0, bearing))):
                with Locations((length / 2, 0)):
                    Rectangle(length, BODY_W)
    return s.sketch


def _channel_footprint(angle: float, length: float) -> Sketch:
    """The open middle channel: what the caps, glands and jumper need."""
    with BuildSketch() as s:
        Circle(CHANNEL_W / 2)
        for bearing in _axis_bearings(angle):
            with Locations(Location((0, 0, 0), (0, 0, bearing))):
                with Locations((length / 2, 0)):
                    Rectangle(length, CHANNEL_W)
    return s.sketch


def create_corner(angle: float = 60.0) -> Part:
    """One corner, in its print pose: back face on z=0, cradles opening up."""
    start = cradle_start(angle)
    arm_len = start + m.CRADLE_LEN
    # Built before the main builder opens -- see the module docstring on why a
    # helper cannot open a BuildSketch against a caller's BuildPart.
    bosses = _strap_boss_solid(angle, start)
    label = _label_solid(angle)

    with BuildPart() as bp:
        with BuildSketch():
            add(_arm_footprint(angle, arm_len))
        extrude(amount=TOP_Z)

        # The channel, from the vertex out to where each cradle begins. Its
        # floor is the plinth top, which is what keeps the glands clear.
        with BuildSketch(Plane.XY.offset(PLINTH_H)):
            add(_channel_footprint(angle, start))
        extrude(amount=TOP_Z - PLINTH_H, mode=Mode.SUBTRACT)

        for bearing in _axis_bearings(angle):
            base = _axis_plane(bearing, start)
            with BuildSketch(base):
                add(cr.tube_section(m.BORE_FIT, lift=PLINTH_H))
            extrude(amount=m.CRADLE_LEN, mode=Mode.SUBTRACT)
            # Relieved between the two end bands: the +/-1 deg of compliance a
            # closed polygon needs, since 0.5 deg is 13 mm over 1500.
            with BuildSketch(base.offset(m.BAND_LEN)):
                add(cr.tube_section(m.BORE_FIT + 2 * m.BAND_RELIEF, lift=PLINTH_H))
            extrude(amount=m.CRADLE_LEN - 2 * m.BAND_LEN, mode=Mode.SUBTRACT)
            # No "cut back above the rim" step is needed: TOP_Z *is* the rim, so
            # the body already stops there and the trough cannot wrap.

        add(bosses)
        _drill_inserts(angle, start)
        _add_drains(angle, start)
        add(label, mode=Mode.SUBTRACT)
        chamfer_edge(
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), m.EDGE_CHAMFER
        )

    part = bp.part
    part.color = CORNER_COLOR
    part.label = f"corner {angle:.0f} deg"
    return part


def _strap_boss_solid(angle: float, start: float) -> Part:
    """The strap boss pads, as a standalone solid the caller unions in."""
    with BuildPart() as bp:
        for bearing in _axis_bearings(angle):
            for station in m.STRAP_STATIONS:
                x = start + station
                with BuildSketch(_axis_plane(bearing, x - m.STRAP_W / 2)):
                    add(cr.boss_pad_section(lift=PLINTH_H))
                extrude(amount=m.STRAP_W)
    return bp.part


def _drill_inserts(angle: float, start: float) -> None:
    """Insert holes at every strap boss. Object creation *does* cross a
    function boundary, so this one can stay a helper."""
    for bearing in _axis_bearings(angle):
        a = radians(bearing)
        nx, ny = -sin(a), cos(a)  # across the axis
        for station in m.STRAP_STATIONS:
            d = start + station
            for side in (-1, 1):
                px = d * cos(a) + side * m.BOSS_U * nx
                py = d * sin(a) + side * m.BOSS_U * ny
                with Locations((px, py, TOP_Z)):
                    Cylinder(
                        m.INSERT_D / 2,
                        m.INSERT_DEPTH,
                        align=(Align.CENTER, Align.CENTER, Align.MAX),
                        mode=Mode.SUBTRACT,
                    )


def _add_drains(angle: float, start: float) -> None:
    """Drains out of the channel and both cradles -- see design-notes S5."""
    with Locations((0, 0, 0)):
        Cylinder(
            m.DRAIN_D / 2,
            PLINTH_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    for bearing in _axis_bearings(angle):
        a = radians(bearing)
        for d in (
            start * 0.55,
            start + m.CRADLE_LEN * 0.35,
            start + m.CRADLE_LEN * 0.75,
        ):
            with Locations((d * cos(a), d * sin(a), 0)):
                Cylinder(
                    m.DRAIN_D / 2,
                    TOP_Z,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )


def _label_solid(angle: float) -> Part:
    """The engraved angle, as a solid to subtract from the back face.

    60, 90 and 120 corners are indistinguishable by eye once they are in a box.
    ``font_size`` is divided by 0.72 because build123d sizes a font by its em,
    not by its cap height -- digits come out about three quarters of the number
    asked for.
    """
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            with Locations((0, -KNUCKLE_R * 0.45)):
                Text(
                    f"{angle:.0f}", font_size=LABEL_H / 0.72, font_style=FontStyle.BOLD
                )
        extrude(amount=LABEL_DEPTH)
    return bp.part


def seated(
    angle: float = 60.0,
    position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation_deg: float = 0.0,
) -> Part:
    """A corner moved from its print pose into a triangle's (or polygon's) vertex.

    House rule: the corner is authored with its vertex on the origin and the
    two arms straddling +Y (``_axis_bearings``); the assembly is what moves
    it. A vertex is just a point with a heading, so placing one is a Z
    rotation about the corner's own vertex followed by a translation to
    ``position`` -- there is no separate lift, because the corner's print
    pose already puts its back face on z=0, and z=0 *is* the floor the whole
    polygon stands on.

    A caller walking a regular polygon picks ``position`` off the vertex
    circle and sets ``rotation_deg`` so the bisector points where it needs
    to (in or out of the polygon); it is also the one placing tubes between
    corners, using ``cradle_start(angle)`` and ``_axis_bearings(angle)`` in
    *this* corner's own frame before this rotation is applied to either.
    """
    corner = create_corner(angle)
    placed = as_part(Pos(*position) * (Rotation(0, 0, rotation_deg) * corner))
    placed.color = CORNER_COLOR
    placed.label = f"corner {angle:.0f} deg (seated)"
    return placed


def create(angle: float = 60.0) -> Part:
    """Entry point for ``uv run show led_profiles.corner``."""
    return create_corner(angle)


PARAMS = [
    {
        "name": "angle",
        "label": "Included angle between tubes (deg)",
        "type": "number",
        "min": 45.0,
        "max": 150.0,
        "step": 5.0,
        "default": 60.0,
    },
]

__all__ = [
    "PARAMS",
    "cradle_start",
    "create",
    "create_corner",
    "seated",
    "section_modulus",
]
