"""Folding tripod hub: stands one lamp vertically, Astera AX1-STD style.

Three bought flat bars bolt to the underside of a printed hub and swing about
their M6 pivots, so they spread into a tripod and nest together for packing.
There is no ballast. The stability number is small and the doc states it
plainly rather than hiding behind a tip *angle*:

    m     = tube 0.45 + hub ~0.2 + 3 legs x 0.118        ~1.0 kg
    r_eff = leg reach x cos 60 deg  (a tripod tips about
            the line joining two legs, at half its reach)  ~134 mm
    F_tip = m g r / h                                      ~0.9 N

**About 90 g of push at the top topples it.** That is what this class of stand
is; it gets sandbagged in use. ``checks.py`` recomputes it from the real part
volume, so a change cannot quietly make it worse.

**Open defect: the cable does not fit.** The well clears the gland and only the
gland, and it does so by exactly 2 mm however big the gland is: ``WELL_H`` is
``GLAND_PROUD + 2``, so what the hub leaves in line with the gland's axis --
``SEAT_Z - FLANGE_T``, which is ``WELL_H`` -- is always the gland plus two
millimetres. ``CABLE_BEND_R`` is 26.8. So the cable leaves the nose pointing at
the flange with 2 mm to turn in, and the slot it is meant to leave by is at
right angles and 3.35 mm *above* the nose. Measuring the gland shrank the well
(30 mm of protrusion became 18.8) and changed nothing about this: the shortfall
is ``CABLE_STUB - 2``, 28 mm, and it is independent of the fitting.
``checks.check_stand_gland_cable`` fails on exactly that, and
``uv run show led_profiles.assemblies.standing`` shows the stub running out
through the flange. ``docs/design-notes.md`` section 10 has the four ways out.
Nothing below is written as though this were solved.

Three things the endcap forces on the geometry:

* The gland points straight down and stands ``GLAND_PROUD`` proud of the cap,
  so the hub needs a well that deep before the cap can land on anything.
* **The gland axis is 6 mm off the tube axis** (``GLAND_Z`` 9.0 against a tube
  centre at 15.0), so that well is offset, not concentric. A concentric one
  does not clear it, and it is the easiest thing here to get wrong.
* The cap collar is 27.2 x 31.2, wider than the tube, so the cradle's bore is
  opened out over the collar's height.

Print pose: standing on the flange, cradle channel vertical and opening
sideways. The cradle is a prism extruded straight up, so it is overhang-free by
construction, and the pivot counterbores open upward.

Edge treatments follow the house rule -- fillet vertical, chamfer horizontal --
but this is the one mount in the family whose print pose *is* its assembly pose
(see ``seated``), so "vertical" here means the bed's normal, global Z, not the
tube's axis. Two consequences worth stating, because they invert what the other
mounts do:

* The socket's mouth opens sideways (+Y) and its lips are therefore *vertical*
  edges -- they get fillets, where the corner's and the cradle's mouths are
  horizontal rims and get chamfers.
* The tube drops in from **above**, so the rim at ``TOP_Z`` is both a horizontal
  edge and the tube's lead-in. That chamfer is the one that has to be there.

Downward-facing horizontal edges only ever get a chamfer, never a fillet: at 45
degrees a chamfer is self-supporting, where a fillet leaves the bed at 90.
Every selection is made **by geometry** -- position, length, arc radius -- and
never off a face, because the socket's mouth faces carry the heat-set insert
holes, which is exactly what OCC refuses to work off. The insert mouths
themselves stay raw, the same deliberate exception the rest of the family makes:
a printed lead-in removes the material the heat-set has to melt into.
"""

from __future__ import annotations

from math import cos, hypot, radians, sin, sqrt

from build123d import (
    Align,
    Axis,
    Box,
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
    Rectangle,
    Rotation,
    ShapeList,
    Wedge,
    add,
    extrude,
    loft,
    mirror,
)

from models.lib.edges import as_part, chamfer_edge, fillet_edge

from . import config as c
from . import cradle as cr
from . import gland as gl
from . import mount_config as m
from .endcap import CAP_H, CAP_T, CAP_W

# The cradle section is drawn with the tube's underside a wall above zero; drop
# it so the tube's axis lands on the hub's own axis, where the mass wants it.
SINK = -m.TUBE_AXIS_Z

FLANGE_D = 90.0
FLANGE_T = 12.0
PIVOT_R = 30.0
PIVOT_CLEAR_D = 6.6  # M6 through-bolt into the leg, nyloc underneath
PIVOT_CBORE_D = 11.5
PIVOT_CBORE_H = 6.0
LEG_COUNT = 3

# Bought legs: flat bar, hole one end. Reach drives the whole tip-force sum.
LEG_W = 20.0
LEG_T = 3.0
LEG_LEN = 250.0
LEG_HOLE_INSET = 12.0
LEG_DENSITY = 7.85e-3  # g/mm^3, steel

# The well is cut for the *cable*, not for the gland. Sizing it at
# ``GLAND_PROUD + 2`` cleared the fitting and left the cable two millimetres --
# whatever the gland measured, since ``SEAT_Z - FLANGE_T`` reduces to ``WELL_H``
# -- and the cable needs ``gland.free_length()`` in line before it can be
# considered turned. Taking the well to that number is what closes the defect
# design notes §10 recorded: it costs 28 mm of pedestal and ~44 g, and the mass
# lands at the base, so ``tip_force`` goes *up* (0.840 -> 0.879 N) rather than
# down. The cable then meets the barrel wall inside the slot's mouth on a
# ~32 mm radius, against a 26.8 mm minimum -- see ``checks.check_stand_gland_cable``.
WELL_H = gl.free_length()
WELL_D = m.GLAND_ENV_D + 2.0
GLAND_OFFSET = 9.0 - c.HEIGHT / 2  # -6.0: the gland axis, relative to the tube's

PEDESTAL_D = 48.0
SEAT_Z = FLANGE_T + WELL_H
SOCKET_DEPTH = 100.0
TOP_Z = SEAT_Z + CAP_T + SOCKET_DEPTH

CABLE_SLOT_W = m.CABLE_OD + 2.0

# The socket's own stadium, in plan. Written out here rather than re-derived at
# every selector, because every edge below is picked by where it sits relative
# to one of these two outlines.
SOCKET_HALF_W = (c.WIDTH + m.BORE_FIT) / 2 + m.CRADLE_WALL  # 17.035
SOCKET_HALF_H = (c.HEIGHT + m.BORE_FIT) / 2 + m.CRADLE_WALL  # 19.035
MOUTH_Y = m.CRADLE_DEPTH + SINK  # 1.8 -- the plane the socket is cut off at

# The cap collar is wider than the tube, so the bore is opened out over CAP_T.
# Hoisted out of ``create_stand_hub`` because the selectors have to know where
# that wider bore's wall is: a fillet at its root would unseat the endcap, which
# has only 0.5 mm a side to play with.
COLLAR_CLEAR = max(CAP_W - c.WIDTH, CAP_H - c.HEIGHT) + 1.0  # 2.2
COLLAR_HALF_W = (c.WIDTH + COLLAR_CLEAR) / 2  # 14.1
COLLAR_HALF_H = (c.HEIGHT + COLLAR_CLEAR) / 2  # 16.1

# The mouth lips take a smaller radius than everything else. EDGE_FILLET is
# sized for the corner's 41 mm arms; a lip is only CRADLE_WALL wide, and over
# the collar band it is narrower still -- SOCKET_HALF_W - COLLAR_HALF_W = 2.94
# mm -- so R2.5 would leave 0.44 mm of wall there, under what a 0.4 nozzle
# should be asked to print. Six tenths of it leaves 1.44 mm, three perimeters,
# and still takes the sharp corner off a 112 mm edge somebody has to carry.
LIP_FILLET = 0.6 * m.EDGE_FILLET  # 1.5

# The boss pads' underside is the one real overhang in this family: printed
# standing on its flange (the module docstring), each pad's flat underside
# hangs off the socket wall with nothing below it, six times. An 0.8 mm edge
# chamfer breaks the corner but does not change the fact that the pad starts
# in mid-air -- fixing it needs the underside to *grow out of the wall*, and
# that takes two changes together:
#
# * ``PAD_BASE_V`` shortens the pad's own reach into the socket. The old
#   value, ``cr.back_z(SINK)``, ran the pad to the stadium's rounded back tip
#   -- correct for every *other* mount, where this same axis is print-vertical
#   and reaching it means reaching the bed, but here it is the socket's own
#   depth axis. Nothing needs that reach: the insert only goes in as far as
#   ``MOUTH_Y - INSERT_DEPTH`` (-7.2), and past v=-10 or so the socket wall's
#   own half-width has already shrunk *below* the pad's inboard edge (see
#   ``GUSSET_SUPPORT_U``), so the old pad was not a 12 mm cantilever there --
#   it was a slab floating over open air for its entire depth, unconnected to
#   the wall at all. Confirmed by point-sampling the pre-fix part, not assumed.
# * A 45 deg wedge (``_boss_gusset``) then carries the shortened pad's
#   underside back to wall that is actually there. Its inboard edge sits at
#   ``GUSSET_SUPPORT_U``, the wall's *real* half-width at v=PAD_BASE_V --
#   never the flank's full ``SOCKET_HALF_W``, which would overshoot past
#   material that has already curved away by that depth.
PAD_BASE_V = -9.0
_GUSSET_ARC = SOCKET_HALF_H - SOCKET_HALF_W  # 2.0 -- see _stadium_dist
GUSSET_SUPPORT_U = sqrt(
    SOCKET_HALF_W**2 - (abs(PAD_BASE_V) - _GUSSET_ARC) ** 2
)  # 15.53
GUSSET_RUN = m.BOSS_U + m.BOSS_OD / 2 - GUSSET_SUPPORT_U  # 13.68 -- rise = run, 45 deg

STAND_COLOR = Color(0.30, 0.32, 0.36)
LEG_COLOR = Color(
    0.62, 0.64, 0.67
)  # a distinct metallic grey -- reads as steel, not printed ASA

STATIONS = (SEAT_Z + CAP_T + 15.0, SEAT_Z + CAP_T + 55.0, SEAT_Z + CAP_T + 90.0)


def leg_reach() -> float:
    """Pivot centre to leg tip, i.e. the tripod's radius."""
    return PIVOT_R + LEG_LEN - LEG_HOLE_INSET


def leg_mass() -> float:
    """One bought leg, in grams."""
    return LEG_W * LEG_T * LEG_LEN * LEG_DENSITY


def tip_force(hub_mass_g: float, tube_mass_g: float = 450.0) -> float:
    """Horizontal push at the top of the tube that tips the stand, in newtons.

    A tripod tips about the line joining two adjacent legs, which is at
    ``reach * cos(60 deg)`` -- half the reach. Quoting the full reach, or a tip
    angle, flatters it by a factor of two.
    """
    mass_kg = (hub_mass_g + tube_mass_g + LEG_COUNT * leg_mass()) / 1000.0
    r_eff = leg_reach() * cos(radians(60.0)) / 1000.0
    return mass_kg * 9.81 * r_eff / (c.LENGTH / 1000.0)


def _pivot_positions() -> list[tuple[float, float]]:
    return [
        (PIVOT_R * cos(radians(90 + 120 * i)), PIVOT_R * sin(radians(90 + 120 * i)))
        for i in range(LEG_COUNT)
    ]


def _boss_gusset(z_bot: float, side: float) -> Part:
    """A 45 deg wedge that carries one boss pad's underside back to the wall.

    ``Wedge`` is an OCC primitive (``Solid.make_wedge``), built directly rather
    than by fillet/chamfer or by lofting between two sketches -- it cannot fail
    the way an edge op can (gotchas S1/S5), which matters here because the
    whole pad underside needs support, not just an edge to break.

    Built axis-aligned -- local X the ramp's horizontal reach (u), local Y its
    rise, local Z the socket's depth (v), constant along the ramp -- then
    ``rotation=(90, 0, 0)`` turns local Y onto global Z (the print-vertical
    rise) and local Z onto global -Y, the same axis swap
    ``_drill_strap_inserts`` uses for its cylinders. The near face is a
    hairline sliver at u=``GUSSET_SUPPORT_U`` -- wall that is actually there
    for the whole depth this ramp covers (see the constant's own comment) --
    and the far face grows to u=``GUSSET_SUPPORT_U + GUSSET_RUN``, exactly the
    pad's own outboard edge, over a rise of the same ``GUSSET_RUN``. The
    hairline sliver means the ramp's true run is ``GUSSET_RUN`` less the
    0.05 mm ``xsize``, not ``GUSSET_RUN`` itself, so the slope is not exactly
    45 deg -- measured off the built solid it is ~45.1 deg, very slightly
    steeper than 45. That is the safe direction (it clears the self-supporting
    threshold with a hair to spare rather than sitting exactly on it) and
    0.05 mm out of a ~13.7 mm run is well inside the margin ``check_stand_gusset``
    checks against, so it is left as a hairline rather than a true zero-width
    edge. The far face flush-merges with the pad's underside with no seam.
    Built for the +u side and mirrored for -u, since a mirror about the YZ
    plane flips u without touching the depth or the rise.
    """
    depth = MOUTH_Y - PAD_BASE_V
    with BuildPart() as gusset:
        Wedge(
            xsize=0.05,
            ysize=GUSSET_RUN,
            zsize=depth,
            xmin=0.0,
            zmin=0.0,
            xmax=GUSSET_RUN,
            zmax=depth,
            rotation=(90, 0, 0),
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
    placed = as_part(Pos(GUSSET_SUPPORT_U, MOUTH_Y, z_bot - GUSSET_RUN) * gusset.part)
    return placed if side > 0 else as_part(mirror(placed, about=Plane.YZ))


def _cable_mouth_flare() -> Part:
    """The cable slot's outer mouth, flared as a boolean tool.

    Where the slot breaks out of the pedestal it leaves four raw edges and the
    cable turns through all of them: two vertical corners on the barrel and two
    horizontal, the notch's own floor and ceiling arcs. Only the vertical pair
    used to be treated (an R``EDGE_FILLET`` fillet); the raw-edge audit found
    the other two, and **OCC will not chamfer them** -- at ``EDGE_CHAMFER`` and
    at every length down to 0.2, one at a time or all four at once, always
    "Failed creating a chamfer". That is the case ``models/lib/edges.py`` says
    to stop asking about and cut as a boolean instead.

    So the whole mouth is lofted: nominal ``CABLE_SLOT_W`` one
    ``EDGE_CHAMFER`` inside the barrel's deepest point, opening at 45 deg in
    both x and z on the way out. All four edges get the same break, which the
    fillet could never give the horizontal pair, and the mouth ends up a funnel
    rather than a slot with two rounded corners. Three things about the shape
    are load-bearing, all three found by building the alternatives:

    * **45 deg, not steeper.** Flaring x by ``EDGE_FILLET`` over the same
      ``EDGE_CHAMFER`` of depth gives a wider, gentler mouth for the cable --
      and leaves a 108 deg step down each side where the taper meets the slot
      wall, which is a sharp edge by the audit's own measure. Equal reach in
      both axes keeps every transition at 135 deg.
    * **The fillet cannot stay.** Filleting first and flaring after leaves the
      notch's arcs uncovered out at the corners the fillet widened; flaring
      first and filleting after is refused by OCC at every radius from 2.5 down
      to 1.0. The flare replaces it rather than joining it.
    * **The tool is clipped at the flange's top face**, below.

    Printed standing on the flange, the flared ceiling is also a 45 deg
    overhang where the flat one was a bridge.
    """
    w = CABLE_SLOT_W
    ch = m.EDGE_CHAMFER
    mid_z = FLANGE_T + 1.0 + w / 2
    taper_end = PEDESTAL_D / 2 - ch  # 23.2, as a +Y offset for Plane.XZ
    start = PEDESTAL_D / 2 + 2.0  # 26.0 -- clear of the barrel at every x
    with BuildPart() as tool:
        # 45 deg: the section grows by exactly what the plane has moved out.
        grow = start - taper_end
        with BuildSketch(Plane.XZ.offset(start)):
            with Locations((0, mid_z)):
                Rectangle(w + 2 * grow, w + 2 * grow)
        with BuildSketch(Plane.XZ.offset(taper_end)):
            with Locations((0, mid_z)):
                Rectangle(w, w)
        loft(ruled=True)
        # Nothing of this tool may reach below the flange's top face. The flare
        # is still opening where it leaves the pedestal's barrel, and the
        # flange is 90 mm across: two millimetres further out the tool is
        # 5.6 mm taller than the slot and would gouge a notch out of the flange
        # top behind the mouth. Inside the barrel the flare's own floor never
        # gets within 0.2 mm of this plane, so the clip costs the mouth nothing.
        with Locations((0, -PEDESTAL_D, FLANGE_T)):
            Box(
                4 * PEDESTAL_D,
                4 * PEDESTAL_D,
                4 * PEDESTAL_D,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
    return tool.part


def create_stand_hub() -> Part:
    """The hub, in its print pose: flange on z=0, socket opening +Y."""
    with BuildPart() as bp:
        with BuildSketch():
            Circle(FLANGE_D / 2)
        extrude(amount=FLANGE_T)

        with BuildSketch(Plane.XY.offset(FLANGE_T)):
            Circle(PEDESTAL_D / 2)
        extrude(amount=WELL_H)

        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            add(cr.body_section(lift=SINK, floor=None))
        extrude(amount=TOP_Z - SEAT_Z)

        # Bore for the tube, and a wider one over the endcap collar's height.
        with BuildSketch(Plane.XY.offset(SEAT_Z + CAP_T)):
            add(cr.tube_section(m.BORE_FIT, lift=SINK))
        extrude(amount=TOP_Z - SEAT_Z - CAP_T, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            add(cr.tube_section(COLLAR_CLEAR, lift=SINK))
        extrude(amount=CAP_T, mode=Mode.SUBTRACT)

        # The gland well -- offset, because the gland axis is not the tube's.
        with Locations((0, GLAND_OFFSET, FLANGE_T)):
            Cylinder(
                WELL_D / 2,
                WELL_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Cable out of the back of the well, and a drain under it. Cut as a box
        # rather than an extruded sketch: Plane.XZ faces -Y, so offsetting it
        # walks the sketch out past the part instead of through it. Its mouth
        # is flared afterwards, once the edge ops are done -- see
        # ``_cable_mouth_flare``.
        with Locations((0, -PEDESTAL_D / 2, FLANGE_T + 1)):
            Box(
                CABLE_SLOT_W,
                PEDESTAL_D,
                CABLE_SLOT_W,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        add(_cable_mouth_flare(), mode=Mode.SUBTRACT)
        with Locations((0, GLAND_OFFSET, 0)):
            Cylinder(
                m.DRAIN_D / 2,
                FLANGE_T,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Leg pivots: bolt down through the flange into the leg, nyloc beneath.
        with Locations(*[(x, y, 0) for x, y in _pivot_positions()]):
            Cylinder(
                PIVOT_CLEAR_D / 2,
                FLANGE_T,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations(*[(x, y, FLANGE_T) for x, y in _pivot_positions()]):
            Cylinder(
                PIVOT_CBORE_D / 2,
                PIVOT_CBORE_H,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )

        # Strap bosses up the socket, then a gusset under each one to carry its
        # underside back to the wall (see PAD_BASE_V/GUSSET_* above), then the
        # inserts.
        for z in STATIONS:
            with BuildSketch(Plane.XY.offset(z - m.STRAP_W / 2)):
                add(cr.boss_pad_section(lift=SINK, base=PAD_BASE_V))
            extrude(amount=m.STRAP_W)
            for side in (-1.0, 1.0):
                add(_boss_gusset(z - m.STRAP_W / 2, side))
        _drill_strap_inserts()
        _add_lead_ins()

        # Edge treatments. Every one is its own isolated call and re-queries the
        # builder, because a successful edge op invalidates the previous
        # selection (gotchas S4) and a failed one would otherwise take every
        # later op down with it (gotchas S1). Verticals first, then horizontals,
        # so a rim chamfer runs onto a finished fillet rather than the reverse.
        fillet_edge(bp, _boss_corners(bp), m.EDGE_FILLET)
        fillet_edge(bp, _lip_corners(bp), LIP_FILLET)
        # The cable slot's *inner* end. The mains cable is the one thing in
        # this family that bears on a printed edge rather than on another
        # printed part, and the notch it turns through was treated on two of
        # its six edges. These are the pair where the slot cuts into the offset
        # gland well; the outer mouth's four are the flare at the end of this
        # function. CABLE_BEND_R is already 4x CABLE_OD for the same reason --
        # a cable on a fixed outdoor installation still works against whatever
        # it touches every time the lamp cycles hot and cold.
        fillet_edge(bp, _cable_well_corners(bp), m.EDGE_FILLET)
        # The socket cantilevers 112 mm off the pedestal, so its root is the one
        # blend on the part that is structural rather than cosmetic. Only the
        # *outer* root: the collar bore's root is excluded by _socket_root,
        # because filling it would lift the endcap off its seat.
        fillet_edge(bp, _socket_root(bp), m.EDGE_FILLET)
        # The rim is the tube's lead-in, since here the tube drops in from
        # above rather than sideways. Everything at TOP_Z, unfiltered: unlike
        # the corner's rim this one carries no insert mouths to exclude -- the
        # stand's inserts go into the mouth lips' *vertical* faces, the topmost
        # of them 10 mm below the rim.
        chamfer_edge(bp, _at_z(bp, TOP_Z), m.EDGE_CHAMFER)
        chamfer_edge(bp, _boss_crowns(bp), m.EDGE_CHAMFER)
        chamfer_edge(bp, _boss_undersides(bp), m.EDGE_CHAMFER)
        chamfer_edge(bp, _ring(bp, SEAT_Z, PEDESTAL_D / 2), m.EDGE_CHAMFER)
        chamfer_edge(bp, _ring(bp, FLANGE_T, FLANGE_D / 2), m.EDGE_CHAMFER)
        chamfer_edge(
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), m.EDGE_CHAMFER
        )

    part = bp.part
    part.color = STAND_COLOR
    part.label = "stand hub"
    return part


# ------------------------------------------------------------ edge selection


def _stadium_dist(x: float, y: float, half_w: float, half_h: float) -> float:
    """Signed distance in plan from (x, y) to a tube stadium's outline.

    Negative inside. Every section of this socket is a ``SlotOverall`` centred
    on the tube axis -- which ``SINK`` puts on the hub's own axis -- so it is
    two arcs of radius ``half_w`` centred at y = +/-(half_h - half_w), joined by
    flanks at x = +/-half_w. One function answers "is this edge on the socket
    wall, on the collar bore, or out on a boss pad", which is the whole of the
    selection problem here and needs no face to answer.
    """
    arc = half_h - half_w
    if abs(y) <= arc:
        return abs(x) - half_w
    return hypot(x, abs(y) - arc) - half_w


def _socket_dist(x: float, y: float) -> float:
    return _stadium_dist(x, y, SOCKET_HALF_W, SOCKET_HALF_H)


def _collar_dist(x: float, y: float) -> float:
    return _stadium_dist(x, y, COLLAR_HALF_W, COLLAR_HALF_H)


def _arc_radius(edge) -> float | None:
    """An edge's radius, or None if it is straight.

    ``Edge.radius`` raises on a line rather than returning None, and every
    selection below is a mix of lines and arcs.
    """
    try:
        return edge.radius
    except Exception:  # noqa: BLE001 -- "not a circle" is the answer, not an error
        return None


def _at_z(bp: BuildPart, z: float) -> ShapeList:
    """Every edge lying in the plane ``z``.

    A degenerate min == max band on ``filter_by_position`` turns into exact
    float equality against a centre that carries kernel rounding, so give it a
    real tolerance (gotchas S4).
    """
    return bp.edges().filter_by_position(Axis.Z, z - 0.01, z + 0.01)


def _ring(bp: BuildPart, z: float, radius: float) -> ShapeList:
    """The one circular edge of ``radius`` at height ``z``.

    Used for the flange's and the pedestal's top rims. Picked by radius rather
    than off the face above them, because both of those faces carry holes --
    three M6 counterbores on the flange, the whole socket footprint and the
    gland well on the pedestal.
    """
    return ShapeList(
        [
            e
            for e in _at_z(bp, z)
            if (r := _arc_radius(e)) is not None and abs(r - radius) < 0.05
        ]
    )


def _boss_corners(bp: BuildPart) -> ShapeList:
    """The strap bosses' free vertical corners.

    The pads stand off the socket wall, so their outboard corners are the only
    sharp verticals on the upper half of the part. ``_socket_dist`` separates
    them from the pad's own root, where it meets the socket's arc -- that one is
    concave and is left alone, since a blend there is a gusset rather than a
    broken edge and would mix concave with convex in one all-or-nothing call.
    The height test drops every cylinder seam lower down (the pedestal's, the
    flange's, the counterbores'), which are seams in a single face and not
    corners at all.
    """
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by(Axis.Z)
            if e.bounding_box().min.Z > SEAT_Z
            and _socket_dist(e.center().X, e.center().Y) > 0.5
        ]
    )


def _lip_corners(bp: BuildPart) -> ShapeList:
    """The outer vertical corners of the socket's two mouth lips.

    These are what the corner connector never has: its mouth is a horizontal
    rim, this one is a pair of 112 mm vertical edges. Selected as "on the socket
    wall, at the mouth plane", which excludes the tangency seams at
    y = -(SOCKET_HALF_H - SOCKET_HALF_W) where the stadium's flank meets its
    arc -- those are smooth, and a fillet on a tangent edge is meaningless.
    """
    out = []
    for e in bp.edges().filter_by(Axis.Z):
        ctr = e.center()
        if abs(ctr.Y - MOUTH_Y) > 0.05:
            continue
        if abs(_socket_dist(ctr.X, ctr.Y)) > 0.1:
            continue
        out.append(e)
    return ShapeList(out)


def _cable_well_corners(bp: BuildPart) -> ShapeList:
    """The vertical ridges where the cable slot cuts into the gland well.

    The slot is a box and the well is a cylinder **offset from the socket axis
    by ``GLAND_OFFSET``**, so the two flat side walls meet the well's barrel on
    a pair of vertical lines that are *not* symmetric about the slot's own
    centre -- picked here by the one thing they do share, sitting on the well's
    own radius from the well's own centre, at the slot's height.

    Same reason as ``_cable_mouth_flare``: the cable turns out of the well into
    the slot right here, so these are the first edges it bears against on its
    way out. They were missed until the raw-edge audit found them. The two
    *horizontal* edges of this same crossing are still raw -- see
    ``check_stand_edges`` for what a flare would cost at this end.
    """
    z_lo = FLANGE_T + 1.0
    z_hi = z_lo + CABLE_SLOT_W
    out = []
    for e in bp.edges().filter_by(Axis.Z):
        ctr = e.center()
        bb = e.bounding_box()
        if abs(hypot(ctr.X, ctr.Y - GLAND_OFFSET) - WELL_D / 2) > 0.05:
            continue
        if abs(bb.min.Z - z_lo) > 0.05 or abs(bb.max.Z - z_hi) > 0.05:
            continue
        out.append(e)
    return ShapeList(out)


def _socket_root(bp: BuildPart) -> ShapeList:
    """Where the socket wall's *outer* footprint lands on the pedestal top.

    Everything at ``SEAT_Z`` bar three things:

    * the pedestal's own rim, which is convex and gets a chamfer instead;
    * the gland well's mouth, which at this height is a ceiling over the well,
      not a root -- its arc sits inside the socket's own footprint and so looks
      like a root edge to any position test. It used to come within 0.03 mm of
      the socket's back wall on the assumed Ø24 gland; on the measured one
      (``WELL_D / 2 + 6.0`` = 16.36 against ``SOCKET_HALF_H`` 19.04) it clears
      by 2.7 mm, which changes the margin and not the need to exclude it;
    * anything inside the collar bore. That bore clears the cap collar by 0.5 mm
      a side and its seat is already only ~0.6 mm wide at the narrowest, so a
      fillet at its root would stop the cap seating altogether.
    """
    out = []
    for e in _at_z(bp, SEAT_Z):
        r = _arc_radius(e)
        if r is not None and abs(r - WELL_D / 2) < 0.05:
            continue
        if r is not None and abs(r - PEDESTAL_D / 2) < 0.05:
            continue
        ctr = e.center()
        if _collar_dist(ctr.X, ctr.Y) < 0.1:
            continue
        out.append(e)
    return ShapeList(out)


def _boss_pad_outline(bp: BuildPart, z: float) -> ShapeList:
    """A boss pad's free outline at height ``z``, top or bottom.

    Only the stretch standing clear of the socket: where the pad runs back into
    the wall the edge is concave, and a chamfer there would be cutting a notch
    into the ligament that carries the strap bolt's load.
    """
    return ShapeList(
        [e for e in _at_z(bp, z) if _socket_dist(e.center().X, e.center().Y) > 0.5]
    )


def _boss_crowns(bp: BuildPart) -> ShapeList:
    """Every boss pad's upward-facing outline."""
    out: list = []
    for z in STATIONS:
        out.extend(_boss_pad_outline(bp, z + m.STRAP_W / 2))
    return ShapeList(out)


def _boss_undersides(bp: BuildPart) -> ShapeList:
    """Every boss pad's downward-facing outline that the gusset does not cover.

    The pad's real overhang is fixed by ``_boss_gusset``, not here -- this is
    what is left over after it: a short seam at the pad's own outboard-bottom
    corner, where the gusset's far face and the pad's own rectangle meet. Still
    worth an 0.8 mm break rather than a knife edge, but it is no longer the
    line standing between this part and a floating underside.
    """
    out: list = []
    for z in STATIONS:
        out.extend(_boss_pad_outline(bp, z - m.STRAP_W / 2))
    return ShapeList(out)


def _gusset_faces(part: Part) -> ShapeList:
    """The six 45 deg gusset ramps' sloped faces -- one per boss pad, per side.

    Selected by geometric properties, never by index (gotchas S9/S10), and by
    more than one of them -- confirmed necessary, not just belt-and-braces, by
    running this selector against the pre-fix part (no gusset at all) and
    watching each weaker version still find something:

    * normal has no v (global Y) component *and* is tilted -- neither
      vertical nor horizontal. Y=0 alone is not enough: the socket wall's own
      lip, between boss stations, is a flat vertical face whose normal is
      also pure X, and the position window below does not exclude it either
      (it is close enough to a gusset's own footprint to fall inside).
    * large enough: adding the tilt test still is not enough on its own,
      because ``_boss_undersides`` chamfers the pad's pre-fix outline at the
      same 45 deg every edge chamfer in this file uses, just 0.8 mm wide --
      geometrically identical in angle to a real ramp, wrong by two orders of
      magnitude in area. ``min_area`` is set generously below the real ramp's
      area (run x sqrt(2) x the gusset's own v-depth) and comfortably above
      an 0.8 mm chamfer bevel's.

    The position window then tells the six ramps apart from each other: it is
    derived from the same GUSSET_SUPPORT_U/RUN the ramp itself is built from,
    not eyeballed, and nearest-match breaks any tie inside it.
    """
    mid_u = GUSSET_SUPPORT_U + GUSSET_RUN / 2
    half_window = GUSSET_RUN / 2 + 0.5
    min_area = 0.5 * GUSSET_RUN * sqrt(2) * (MOUTH_Y - PAD_BASE_V)
    out = []
    for z in STATIONS:
        z_bot = z - m.STRAP_W / 2
        mid_z = z_bot - GUSSET_RUN / 2
        for side in (-1.0, 1.0):
            target_u = side * mid_u
            candidates = []
            for f in part.faces():  # ty: ignore[invalid-argument-type]
                c = f.center()
                if (
                    abs(c.X - target_u) >= half_window
                    or abs(c.Z - mid_z) >= half_window
                ):
                    continue
                if f.area < min_area:
                    continue
                n = f.normal_at(c)
                if abs(n.Y) < 1e-6 and 0.3 < abs(n.Z) < 0.95:
                    candidates.append(f)
            if candidates:
                out.append(
                    min(
                        candidates,
                        key=lambda f: (f.center().X - target_u) ** 2
                        + (f.center().Z - mid_z) ** 2,
                    )
                )
    return ShapeList(out)


def _add_lead_ins() -> None:
    """Boolean cone lead-ins at every bore mouth that is not a heat-set insert.

    Cones rather than edge chamfers for the reason ``corner._add_drains`` gives:
    these mouths share their faces with other features -- three counterbores and
    the pedestal on the bed face, the drain in the well floor -- and that is the
    case OCC is least willing to chamfer from. The bed-face ones double as
    elephant's-foot relief.

    Two mouths are deliberately left raw:

    * the **insert holes**, the family-wide exception -- a printed lead-in
      removes the material the heat-set has to melt into;
    * the **counterbore mouths**, meaning their *rims* at ``FLANGE_T``.
      ``PIVOT_R - PIVOT_CBORE_D / 2`` is 24.25, which is 0.25 mm outside the
      pedestal's 48 mm diameter, so a cone at that mouth would undercut the
      pedestal's own base. The bore already clears an M6 head by 0.75 mm a side
      and needs no help finding it. Their *floors*, six millimetres down and
      nowhere near the pedestal wall, do get a cone -- see below.

    Same arithmetic is why the flange/pedestal root carries no fillet: any blend
    there would hang out over a counterbore mouth and foul the bolt head.
    """
    ch = m.EDGE_CHAMFER
    mouths = [(x, y, PIVOT_CLEAR_D) for x, y in _pivot_positions()]
    mouths.append((0.0, GLAND_OFFSET, m.DRAIN_D))
    for x, y, d in mouths:
        with Locations((x, y, 0)):
            Cone(
                bottom_radius=d / 2 + ch,
                top_radius=d / 2,
                height=ch,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    # A funnel at the drain's upper mouth, so the well actually empties into it.
    # The well floor is flat, so a plain cone conforms to it (``cradle
    # .drain_funnel`` is the same cut where the floor is the trough's own arc).
    with Locations((0, GLAND_OFFSET, FLANGE_T - ch)):
        Cone(
            bottom_radius=m.DRAIN_D / 2,
            top_radius=m.DRAIN_D / 2 + ch,
            height=ch,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    # And the pivot counterbores' floors, where each one steps down to the
    # narrower clearance hole. That shoulder is where an M6 head lands, so it
    # is not a handling edge -- but it is a square internal corner at a layer
    # line directly under the fastener that carries the whole tripod's load,
    # which is the worst place on this part for a stress riser. Broken by
    # BOLT_LEAD_IN and no more: the flat left between the cone and the
    # counterbore wall is the head's own bearing seat.
    lead = m.BOLT_LEAD_IN
    for x, y in _pivot_positions():
        with Locations((x, y, FLANGE_T - PIVOT_CBORE_H - lead)):
            Cone(
                bottom_radius=PIVOT_CLEAR_D / 2,
                top_radius=PIVOT_CLEAR_D / 2 + lead,
                height=lead,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )


def _drill_strap_inserts() -> None:
    """Insert holes at each strap station up the socket.

    ``rotation=(90, 0, 0)`` turns the cylinder's axis onto -Y, so ``Align.MIN``
    is what drives it *into* the boss from the mouth face; ``MAX`` would drill
    outward into the air and cut nothing.
    """
    for z in STATIONS:
        for side in (-1, 1):
            with Locations((side * m.BOSS_U, MOUTH_Y, z)):
                Cylinder(
                    m.INSERT_D / 2,
                    m.INSERT_DEPTH,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )


def seated() -> Part:
    """The hub, in the pose a tripod assembly wants -- which is unchanged.

    Every other mount in this family prints lying on its back and needs
    ``seated()`` to stand it up onto the tube. The stand is the opposite: it
    *prints* standing on the flange, socket opening +Y, and ``SINK`` already
    lands the socket's tube axis on the hub's own vertical (Z) axis at
    x=0, y=0 -- see the module docstring. So the print pose already is the
    assembly pose, and a tube dropped in from above along +Z lands on-axis
    with no further placement. This still goes through its own function
    rather than a bare re-export of ``create_stand_hub``, so a caller
    assembling the family can rely on ``stand.seated()`` existing the way
    ``corner.seated()`` and ``feet.seated()`` do, and so a future change to
    the print pose has one obvious place to add the now-missing transform.
    """
    hub = create_stand_hub()
    hub.label = "stand hub (seated)"
    return hub


def create_leg() -> Part:
    """A bought flat-bar leg, MOCKED for assembly views only.

    **Not a printed part.** Real hardware: LEG_W x LEG_T mild-steel flat bar,
    LEG_LEN long, with a single PIVOT_CLEAR_D clearance hole LEG_HOLE_INSET
    from the pivot end for the M6 through-bolt (see the module docstring and
    ``leg_mass``). This mock exists so an assembly view can show *something*
    where the leg goes; it must never appear in ``assembly.printed_parts()``.

    Local frame: the pivot hole sits on the Z axis at the origin, so placing
    a leg is a Z rotation plus an XY translation with no compensating offset
    -- see ``seated_legs``. The bar extends from the hole out to the tip
    along +X, and sits *under* the flange plane: top face at z=0, thickness
    running down to z=-LEG_T, matching the through-bolt that goes down
    through the flange and into the leg (see ``create_stand_hub``).
    """
    with BuildPart() as bp:
        with Locations((-LEG_HOLE_INSET, 0, -LEG_T)):
            Box(LEG_LEN, LEG_W, LEG_T, align=(Align.MIN, Align.CENTER, Align.MIN))
        with Locations((0, 0, 0)):
            Cylinder(
                PIVOT_CLEAR_D / 2,
                LEG_T,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )

    part = bp.part
    part.color = LEG_COLOR
    part.label = "leg (bought, mock)"
    return part


def seated_legs(splay_deg: float = 0.0) -> list[Part]:
    """Three bought legs, bolted on their pivots and splayed for a stance.

    The pivots are already 120 deg apart (``_pivot_positions``); a leg's
    default bearing is straight out along that same radial line, i.e. it
    points directly away from the hub centre through its own pivot, which is
    the fully-deployed, evenly-spread stance. ``splay_deg`` rotates all three
    legs together, off that radial reference -- 0 is deployed-radial, and
    driving it away from 0 sweeps the legs round their pivots in step, which
    is what a caller wants to animate folding the tripod for packing.

    Each leg's local origin is its own pivot hole (see ``create_leg``), so
    placing one is just rotate-then-translate to the pivot's (x, y) -- no
    offset to compensate for.
    """
    legs = []
    for i, (px, py) in enumerate(_pivot_positions()):
        bearing = 90.0 + 120.0 * i + splay_deg
        leg = as_part(Pos(px, py, 0) * (Rotation(0, 0, bearing) * create_leg()))
        leg.color = LEG_COLOR
        leg.label = f"leg {i}"
        legs.append(leg)
    return legs


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stand``."""
    return create_stand_hub()


__all__ = [
    "create",
    "create_leg",
    "create_stand_hub",
    "leg_mass",
    "leg_reach",
    "seated",
    "seated_legs",
    "tip_force",
]
