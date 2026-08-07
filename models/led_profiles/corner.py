"""Corner connector: joins two lamps at a fixed angle to build geometric forms.

``angle`` is the **included angle between the two tube axes** -- 60 makes an
equilateral triangle, 90 a square, 120 a hexagon. Asking for 60 and getting a
hexagon corner is the obvious mistake, so it is worth saying twice.

The corner is mechanical only. Both tubes keep their glanded endcaps and the bus
crosses on an external jumper, which is what pushes the tube ends back from the
vertex: two glands pointing at each other are cylinders whose axes intersect, so
the clearance condition is not "twice the radius" but

    a         = (GLAND_ENV_D / 2) / tan(angle / 2)      16.2 mm at 60 deg
    cap face  = a + GLAND_PROUD                         35.0 mm
    aluminium = cap face + CAP_T                        47.0 mm

and the unlit run at a 60 deg vertex is 2 x 47.0 = **94 mm**. That is the price
of staying coplanar; ``docs/design-notes.md`` S2 records what was refused to
avoid it, and ``checks.py`` reports the number so a change to the gland cannot
make it worse quietly. It was 126 mm until the gland was measured rather than
assumed -- both inputs came down (``mount_config``), and 32 mm of dark tube at
every vertex came off with them.

Shape: a V-shaped bar with a cradle at each end and an open channel down its
middle, in which the two endcaps, their glands and the jumper loop all sit. Two
numbers are not free choices:

* ``PLINTH_H`` -- the gland used to sit 6 mm *below* the tube axis, hang below
  the tube's underside and cut into a 4 mm cradle floor, which is why the
  cradles stand on a plinth at all. The drop is ``GLAND_DROP``: measuring the
  gland took it from 3.0 mm to 0.35 mm, and centring the gland on the endcap
  took it to zero. The plinth is now pure headroom and could come down if the
  corner ever needs the height back.
* ``ARM_WALL`` -- the channel has to clear the 26.1 mm cap, and a bar only as
  wide as the cradle would be left with thin side walls. The arms are widened
  until the walls carry the out-of-plane load (see ``section_modulus``).

Print pose: back face on the bed, cradles and channel opening up. That is the
LED direction, so nothing overhangs and the first layer is the whole footprint.

Edge treatments are four isolated calls at the end of ``create_corner`` rather
than one, and every one of them selects **by geometry, not off a face**: the top
face carries eight insert holes, which is precisely the case OCC will not
chamfer from (see ``models/lib/edges.py``). They are, in order, the two
trough-mouth corners per arm (filleted at ``MOUTH_FILLET``, the one radius on
this part set by the room it has rather than by the house rule), the rest of the
body's vertical corners (filleted at ``EDGE_FILLET`` -- arm ends, boss steps,
the V's inner root, the channel's ends out at the knuckle), the whole rim at
``TOP_Z`` bar those insert mouths
(chamfered -- outer silhouette, channel mouth, and both trough mouths, which is
the tube's lead-in as it drops in sideways), and the bed face's outer wire.

The channel and both troughs carry **no drains**. Every other upward-facing
pocket in this family has one (``docs/design-notes.md`` S5), so this corner is
the family's one stated exception rather than an oversight: standing water sits
in the channel with the glands and the jumper loop, and in each trough against
the aluminium. Anywhere it can rain, that is the corner's own limitation.

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
    ShapeList,
    Sketch,
    Text,
    add,
    extrude,
)

from models.lib.edges import as_part, chamfer_edge, fillet_edge

from . import config as c
from . import cradle as cr
from . import mount_config as m
from .endcap import CAP_T, CAP_W, GLAND_Z

# The gland's axis sits GLAND_Z above the tube's underside and it is
# GLAND_ENV_D across, so it hangs this far below that underside -- or, once the
# gland moved to the cap's own centre, it does not hang below at all and the
# drop clamps to zero. Derived rather than typed, so moving GLAND_Z again lands
# here instead of in a stale comment.
GLAND_DROP = max(m.GLAND_ENV_D / 2 - GLAND_Z, 0.0)  # 0.0 with GLAND_Z centred
PLINTH_H = 8.0  # > GLAND_DROP + a printable floor; see the docstring

# The channel answers to two constraints at once, and the second one is not
# obvious from the part:
#
# * it has to clear a seated cap and a fitted gland by ``CAP_CLEAR`` a side.
#   The cap wins that max() by a wide margin (26.1 against 18.71) -- kept
#   because it is the condition, not the answer, and a fatter gland takes it
#   back;
# * it has to leave the rim at ``TOP_Z`` a **land it can actually chamfer**,
#   where the channel's wall runs alongside the trough bore. Two
#   ``EDGE_CHAMFER``s meet on that land, and if it is narrower than they are
#   OCC refuses the *whole* rim chamfer -- all four arms, 76 edges, shipped
#   raw and looking identical in a projection, because ``chamfer_edge``
#   swallows the refusal by design.
#
# That second constraint is a **window, not a floor**, and both edges of it are
# measured rather than argued: a land of 1.52 mm refuses the rim chamfer, 1.72
# takes it, and past about 1.82 the body's own R2.5 vertical corners start
# refusing instead. So this cannot be made generous "to be safe" -- it sits in
# the middle of a window roughly 0.25 mm wide, and ``check_corner`` asserts it
# is still in there.
#
# Worth knowing how thin the old margin was: at a 26.0 mm tube this landed on
# 1.565 mm, 0.035 mm inside the lower edge. Correcting the tube to 26.1 was
# enough to tip it, which is how the constraint got found at all.
CAP_CLEAR = 2.0
MOUTH_LAND = 2 * m.EDGE_CHAMFER + 0.1  # 1.7, mid-window
CHANNEL_W = max(
    max(CAP_W, m.GLAND_ENV_D) + CAP_CLEAR,
    c.WIDTH + m.BORE_FIT + 2 * MOUTH_LAND,
)  # 29.57


def mouth_land() -> float:
    """Rim land between the channel's wall and the trough bore, in mm.

    What ``CHANNEL_W``'s second constraint is really about, so ``checks`` can
    assert the window rather than re-deriving it.
    """
    return CHANNEL_W / 2 - (c.WIDTH + m.BORE_FIT) / 2


# The two corners where the channel's side wall meets its end wall are the one
# pair ``EDGE_FILLET`` does not fit, and the reason is arithmetic rather than
# taste. That corner is concave, so a fillet of radius R rolls the wall inward
# by R at the end plane -- and the end plane is the trough's mouth, where the
# only room there is is the ``(CHANNEL_W - CAP_W) / 2`` = 1.0 mm the channel
# holds clear of the endcap. R2.5 therefore rolled 1.5 mm past the cap's own
# envelope (0.18 mm^3 of interference per arm, measured against a seated cap,
# not estimated) and straight through the bore's mouth outline, where it ended
# dead against the bore wall and left the unblended seam the raw-edge audit
# reported as an untraced residual near the first strap boss.
#
# Half that clearance: the corner still gets a break, and the cap keeps the
# other half. **Not a free number** -- it is the same species as
# ``mount_config.BOSS_U`` and ``feet.PAD_WALL``, a radius that has to be
# derived from the room it sits in rather than typed.
MOUTH_FILLET = (CHANNEL_W - CAP_W) / 4  # 0.5

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
        add(label, mode=Mode.SUBTRACT)

        # Edge treatments, house rule: fillet vertical, chamfer horizontal.
        # Four separate isolated calls, each re-querying the builder, because a
        # successful edge op invalidates the previous selection and a failed one
        # would otherwise take every later op with it. The trough-mouth corners
        # go first and on their own: they are the two verticals with a radius of
        # their own (MOUTH_FILLET), and running them separately also means a
        # radius OCC will not take there cannot cost the arm ends theirs.
        fillet_edge(bp, _mouth_corners(bp, angle, start), MOUTH_FILLET)
        fillet_edge(bp, _vertical_corners(bp, angle, start), m.EDGE_FILLET)
        chamfer_edge(bp, _rim_edges(bp), m.EDGE_CHAMFER)
        chamfer_edge(
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), m.EDGE_CHAMFER
        )

    part = bp.part
    part.color = CORNER_COLOR
    part.label = f"corner {angle:.0f} deg"
    return part


def _arc_radius(edge) -> float | None:
    """An edge's radius, or None if it is straight.

    ``Edge.radius`` raises on a line rather than returning None, and every
    selection below is a mix of lines and arcs.
    """
    try:
        return edge.radius
    except Exception:  # noqa: BLE001 -- "not a circle" is the answer, not an error
        return None


def _is_vertical_corner(edge) -> bool:
    """A real vertical corner of the body, as opposed to a seam inside it.

    The length test is what separates a corner of the body from the short
    verticals inside a trough's stadium and around the engraved label, both of
    which must be left alone.
    """
    return edge.length > 0.6 * TOP_Z and abs(edge.bounding_box().max.Z - TOP_Z) < 1e-6


def _mouth_corners(bp: BuildPart, angle: float, start: float) -> ShapeList:
    """The two vertical corners per arm where the channel meets the trough.

    Where the channel's side wall runs into its end wall, at the plane the
    tube's cradle begins. Selected in each arm's own frame -- ``start`` along
    the axis, ``CHANNEL_W / 2`` across it -- which is the only thing that
    separates them from the channel's other full-depth verticals: its two
    ends out at the knuckle, and the notch where the two arms' channels cross.

    They take ``MOUTH_FILLET`` rather than ``EDGE_FILLET``; see that constant
    for what the full radius did to the endcap and the bore's mouth.
    """
    out = []
    for e in bp.edges().filter_by(Axis.Z):
        if not _is_vertical_corner(e):
            continue
        ctr = e.center()
        for bearing in _axis_bearings(angle):
            a = radians(bearing)
            d = ctr.X * cos(a) + ctr.Y * sin(a)
            u = -ctr.X * sin(a) + ctr.Y * cos(a)
            if abs(d - start) < 0.05 and abs(abs(u) - CHANNEL_W / 2) < 0.05:
                out.append(e)
                break
    return ShapeList(out)


def _vertical_corners(bp: BuildPart, angle: float, start: float) -> ShapeList:
    """The body's own vertical corners: arm ends, boss steps, the V's inner
    root and the channel's end walls out at the knuckle.

    Selected by geometry rather than off a face, because the top face they all
    reach carries eight insert holes -- exactly the case where OCC refuses to
    work off a face at all.

    The trough-mouth corners are held back for ``_mouth_corners``, which gives
    them the smaller radius the endcap leaves room for. They are a
    separate call rather than a smaller radius for everything because
    ``EDGE_FILLET`` is right everywhere else -- these arms are 41 mm across,
    and this is the one corner on the part with 1 mm of room.
    """
    held_back = set(_mouth_corners(bp, angle, start))
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by(Axis.Z)
            if _is_vertical_corner(e) and e not in held_back
        ]
    )


def _rim_edges(bp: BuildPart) -> ShapeList:
    """Everything at the rim except the insert mouths.

    The rim carries the outer silhouette, the channel's mouth and both troughs'
    mouths, and all of it wants a chamfer -- the trough ones are the tube's
    lead-in as it drops in sideways. The eight insert holes are the deliberate
    exception this family already makes elsewhere: a printed lead-in removes the
    material the heat-set has to melt into (``cradle.create_cradle``), so they
    are filtered out by radius. A fillet arc left by ``_vertical_corners`` is
    ``EDGE_FILLET``, well clear of that test.
    """
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by_position(Axis.Z, TOP_Z - 0.01, TOP_Z + 0.01)
            if not _is_insert_mouth(e)
        ]
    )


def _is_insert_mouth(edge) -> bool:
    r = _arc_radius(edge)
    return r is not None and abs(r - m.INSERT_D / 2) < 0.05


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
