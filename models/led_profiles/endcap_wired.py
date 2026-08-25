"""Wired endcap: 10 mm more protrusion, and a through wiring chamber behind it.

A second endcap for the same tube, alongside ``endcap`` rather than replacing
it. The standard cap's docstring is explicit about what a centred gland on a
15.85 mm flange costs: only a ``cavity_slot_h()`` = 5.5 mm slot of the bore
looks into the wiring cavity, narrower than the 6.7 mm cable the gland seals
on, so **the standard cap's gland is a fitting, not a cable route**. This cap
buys that route back with length: the flange grows by ``EXTRA_T`` = 10 mm --
the plug is unchanged, so all of it is protrusion past the aluminium -- and
everything above the gland's own reach is opened into one chamber whose lower
half is the wiring cavity's own cross-section, carried straight through the
cap. A cable threaded through the gland exits the thread into that chamber,
has ``CAP_T - CHAMBER_FLOOR_Z`` = 14.75 mm of run to bow down in, and enters
the tube through the plug's channel with no lip, step or slot anywhere on the
way down: the chamber's stadium is the plug hollow's own (``CHAMBER_INSET``
is that hollow's inset), so below the cavity's chord the walls are flush from
the chamber floor to the plug's tip. The one place the two sections differ is
the two screw columns, which exist only in the flange -- where they end at
the inner face the channel steps *outward*, up near the chord where a cable
lying in the channel's bottom never rides, so nothing narrows on the way in.

**The chamber is the relief pocket grown into a job.** The standard cap
hollows the flange above the thread because nothing there works
(``endcap.POCKET_*``); here the same region is the cable's turning room, so
the outline stops being "the flange less clearances" and becomes the full
stadium at the plug hollow's inset -- as big as the section gets without
stepping past the channel it feeds -- less only the two screw columns, each a
local circle at ``endcap.POCKET_CLEAR`` off its clearance hole exactly as the
pocket drew them. The floor sits at ``CHAMBER_FLOOR_Z``, which clears both
tenants below it: the gland's ``GLAND_MALE_L`` of reach plus the same
collar-and-lead the pocket keeps above the thread (10.0), and the screw seats,
whose cones bottom out at ``SCREW_ACCESS_DEPTH + SCREW_SEAT_DEPTH`` = 11.1 --
the larger of the two, so the floor is one clean plane with three holes in it
rather than a plane with cones poking through.

**The screws keep their length, so their holes gain a first stage.** The same
M2 x 20 countersunk screws have to reach the same ports through a flange
10 mm deeper, and every millimetre of flange is a millimetre of screw spent in
plastic. So each hole starts as an access bore of ``SCREW_ACCESS_D`` -- the
seat cone's own rim diameter, so the bore hands over to the cone with no ledge
-- sunk exactly ``EXTRA_T`` deep, and the seat and clearance hole carry on
from there unchanged. The head therefore lands 10 mm below the outer face and
``screw_reach()`` is *identical* to the standard cap's, asserted in checks
rather than assumed. The bore is 0.5 mm a side over the head; the screw rides
in on the driver's tip, which is how a sunk countersunk head is driven anyway.
Like the seat it extends, the bore breaks out through the flank -- same
diameter, same deliberate ``screw_breakout()``, just running the depth of the
access stage -- and the seams it leaves are filleted down the same ladder.

**No strap slot, and that is the trade.** The slot runs through exactly the
flange the chamber opens up -- its span (1.8 to 14.05 along the axis, at
y = -9.9) is inside the chamber both ways, so a slot here would dump the strap
into the cable run. A lamp that hangs from velcro straps takes the standard
cap; this one is for the ends where the cable leaves. ``CAP_T`` is therefore
no longer derived from the slot -- it is the standard cap's flange plus
``EXTRA_T``, so the two caps' proportions stay coupled through one number.

Print pose: outer face down, plug up, same as the standard cap and for the
same reasons -- thread on a vertical axis, biggest first layer. The chamber
suits it: a cup open toward the nozzle, vertical walls, floor printed on the
solid gland block below it, no ceiling anywhere. The seat cones are 45 deg and
self-supporting, and the access bore above each is a plain vertical wall.

Edge treatments, house rule: chamfer horizontal, fillet vertical. The bed
wire's chamfer and the plug's lead-in are taken while the part is a plain
two-step prism, as in the standard cap; the chamber floor's rim into the bore
is a clipped boolean cone (``endcap.POCKET_LEAD``), each access bore's mouth
on the bed face gets a ``SCREW_MOUTH_LEAD`` cone (the seat cone used to open
at the face and be its own lead-in; the bore that replaced it is square-
mouthed without one), and the hollow's rim at the plug's tip, the plug-top
seams and corners, and the screw seams ride the same selectors and ladders as
the standard cap, re-anchored to this cap's own depth. Edges left square on
purpose: the whole ``CAP_T`` face (the tube's wall seat), the screw seats'
breakout tail slivers, and the sub-millimetre stubs where the access mouth's
breakout crosses the bed chamfer -- rolling those drags the fillet below z=0
exactly the way ``SCREW_SEAM_FILLET``'s own history records, so
``screw_seam_fillet_edges`` holds them out of the ladder and checks bounds
what stays. All three are named in checks, not merely left.
"""

from __future__ import annotations

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    GeomType,
    Locations,
    Mode,
    Part,
    Plane,
    ShapeList,
    Sketch,
    SlotOverall,
    add,
    extrude,
    fillet,
)

from models.lib.checks import interior_angle
from models.lib.edges import chamfer_edge, fillet_edge

from . import config as c
from . import endcap as e
from .profile import _loc

# ------------------------------------------------------------------ the cap

# The whole difference in length, and where it goes: the plug is unchanged, so
# the cap stands exactly this much further out of the aluminium than the
# standard one does.
EXTRA_T = 10.0
CAP_T = e.CAP_T + EXTRA_T  # 25.85
CAP_W = e.CAP_W
CAP_H = e.CAP_H
PLUG_DEPTH = e.PLUG_DEPTH

# ---------------------------------------------------------------- the screws

# The access stage: a plain bore the screw and driver travel down before the
# seat begins. Its diameter is the seat cone's own rim -- head + FREE + the
# deliberate sink, all inherited from the standard cap -- so bore and cone
# meet at the same radius and there is no ledge between the two. Its depth is
# exactly the flange growth, which is what keeps screw_reach() identical.
SCREW_ACCESS_D = e.SCREW_SEAT_D  # 4.85
SCREW_ACCESS_DEPTH = EXTRA_T

# The bore's mouth on the bed face. The standard cap's seat cone opened at the
# face and was its own lead-in; the access bore is square-mouthed without one,
# and this is also where a hand starts a screw. Sized like the other small
# hole-mouth breaks in this family (POCKET_LEAD's order), cut as a cone.
SCREW_MOUTH_LEAD = 0.4

# --------------------------------------------------------------- the chamber

# One inset for the whole run, and it is the plug hollow's own: the chamber is
# the same stadium the plug's channel is, just not clipped at the cavity
# ceiling -- so below the chord the two share their walls, and the cable meets
# no step inward at the flange/plug boundary. What the section keeps to the
# outside is c.WALL + CHAMBER_INSET = 2.225 mm of shell.
CHAMBER_INSET = e.PLUG_FIT / 2 + e.PLUG_WALL  # 1.725 off the cavity outline
CHAMBER_WALL = c.WALL + CHAMBER_INSET  # 2.225 of shell left all round

# The two screw columns, exactly as the relief pocket drew them: a local
# circle at POCKET_CLEAR off each clearance hole, tangent to the old POCKET_X
# at the screw's own height and giving the curvature back everywhere else.
CHAMBER_SCREW_R = e.SCREW_CLEAR_D / 2 + e.POCKET_CLEAR  # 3.325

# Where the circle runs into the stadium -- concave in the material, rounded
# for the same stress-riser and infill reasons as the pocket's corners.
CHAMBER_CORNER_R = e.POCKET_CORNER_R

# The floor: the higher of what the two features under it need. The gland
# wants GLAND_MALE_L + POCKET_COLLAR + POCKET_LEAD = 10.0 (the same
# thread-collar rule the pocket follows -- nothing may cut into the thread's
# own geometry); the screw seats bottom out at 11.1. Taking the max keeps the
# floor a single plane above both, three holes and no cones through it.
CHAMBER_FLOOR_Z = max(
    e.POCKET_FLOOR_Z, SCREW_ACCESS_DEPTH + e.SCREW_SEAT_DEPTH
)  # 11.10


def chamber_section() -> Sketch:
    """The chamber's outline: the plug hollow's stadium, less the screw columns.

    The stadium is ``_cavity_outline``'s arithmetic at ``CHAMBER_INSET`` with
    no ceiling clip -- shrinking a stadium is exact, so the wall is
    ``CHAMBER_WALL`` everywhere by construction. The gland bore's whole circle
    is inside this outline (checked, not assumed: ``check_wired_chamber``
    measures the landing), which is the point of the cap -- past the floor the
    cable is in the chamber, not in a bore looking at it through a slot.
    """
    with BuildSketch() as s:
        SlotOverall(
            c.HEIGHT - 2 * c.WALL - 2 * CHAMBER_INSET,
            c.WIDTH - 2 * c.WALL - 2 * CHAMBER_INSET,
            rotation=90,
        )
        with Locations(*e._screw_centres()):
            Circle(CHAMBER_SCREW_R, mode=Mode.SUBTRACT)
        fillet(s.vertices(), CHAMBER_CORNER_R)
    return s.sketch


def _chamber_rim_chamfer() -> Part:
    """The chamfer at the floor's inner rim, clipped to the chamber's footprint.

    ``endcap._pocket_rim_chamfer`` verbatim, re-anchored: a boolean cone at
    the floor (the house rule's chamfer for a horizontal convex rim, cut as a
    cone because the thread lives a collar below it), intersected with the
    chamber's own outline so it can exist exactly where the floor does. As
    the numbers stand the clip removes nothing -- the outline holds a 4 mm
    landing round the bore -- and it is kept for the same reason the pocket
    keeps its own: the floor is a derived number, and an unclipped full-circle
    cone grooves the bore's wall the day something moves it.

    Built outside ``create_endcap_wired``'s builder: a nested ``BuildPart``
    adds itself to its parent on exit, and this is a cutter, not a feature.
    """
    with BuildPart() as tool:
        with Locations((0, 0, CHAMBER_FLOOR_Z - e.POCKET_LEAD)):
            Cone(
                bottom_radius=e.GLAND_MAJOR_D / 2,
                top_radius=e.GLAND_MAJOR_D / 2 + e.POCKET_LEAD,
                height=e.POCKET_LEAD,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with BuildSketch(Plane.XY.offset(CHAMBER_FLOOR_Z - e.POCKET_LEAD)):
            add(chamber_section())
        extrude(amount=e.POCKET_LEAD, mode=Mode.INTERSECT)
    return tool.part


# ------------------------------------------------------------ edge selectors
#
# The standard cap's selectors, re-anchored to this cap's own CAP_T and tip.
# They cannot be imported as-is because they read endcap's module constants;
# the *logic* is identical and documented there, so each carries only the
# note of what changed.


def _plug_void_tip_edges(shape: BuildPart | Part) -> ShapeList:
    """The hollow's rim at the plug's tip -- ``endcap._plug_void_tip_edges``,
    with the tip 10 mm further out. Same elimination: of the closed curves at
    the tip, the void's is the shorter, and the tab lines are LINEs."""
    part = shape.part if isinstance(shape, BuildPart) else shape
    if part is None:
        return ShapeList([])
    tip = CAP_T + PLUG_DEPTH
    curves = [
        edge
        for edge in part.edges()  # ty: ignore[invalid-argument-type]
        if abs(edge.bounding_box().center().Z - tip) < 0.02
        and edge.geom_type != GeomType.LINE
    ]
    if not curves:
        return ShapeList([])
    outer_len = max(edge.length for edge in curves)
    return ShapeList([edge for edge in curves if edge.length < outer_len - 1.0])


def _plug_top_seams(bp: BuildPart) -> ShapeList:
    """The two lengthwise seams down the plug's flat top -- same section as the
    standard cap (the chamber IS the hollow's stadium), so the same
    ``plug_void_half_width()``; only the z floor moves with CAP_T."""
    y_top = _loc(e.plug_top_z())
    x_seam = e.plug_void_half_width()

    def is_seam(edge) -> bool:
        bb = edge.bounding_box()
        return (
            bb.min.Z > CAP_T - 0.01
            and abs(bb.max.Y - y_top) < 0.01
            and abs(abs(bb.center().X) - x_seam) < 0.05
        )

    return ShapeList([edge for edge in bp.edges().filter_by(Axis.Z) if is_seam(edge)])


def _plug_top_corners(bp: BuildPart) -> ShapeList:
    """The two corners where the plug's flat top meets its arc -- see
    ``endcap._plug_top_corners``; only the z floor moves."""
    y_top = _loc(e.plug_top_z())
    half = (c.WIDTH - 2 * c.WALL - e.PLUG_FIT) / 2

    def is_corner(edge) -> bool:
        bb = edge.bounding_box()
        return (
            bb.min.Z > CAP_T - 0.01
            and abs(bb.max.Y - y_top) < 0.01
            and abs(abs(bb.center().X) - half) < 0.2
        )

    return ShapeList([edge for edge in bp.edges().filter_by(Axis.Z) if is_corner(edge)])


def plug_tip_corner_edges(shape: BuildPart | Part) -> ShapeList:
    """Sharp corners the tip's lead-in leaves -- ``endcap.plug_tip_corner_edges``
    at this cap's tip. Public because checks re-runs it: empty = the fillet
    took."""
    part = shape.part if isinstance(shape, BuildPart) else shape
    if part is None:
        return ShapeList([])
    tip = CAP_T + PLUG_DEPTH

    def in_chamfer_band(edge) -> bool:
        bb = edge.bounding_box()
        return (
            bb.min.Z > tip - e.PLUG_LEAD_IN - 0.05
            and bb.max.Z < tip + 0.05
            and (bb.max.Z - bb.min.Z) > 0.05
        )

    edges = part.edges()  # ty: ignore[invalid-argument-type]
    near = [edge for edge in edges if in_chamfer_band(edge)]
    return ShapeList(
        [
            edge
            for edge in near
            if (angle := interior_angle(part, edge)) is None or angle <= 120.0
        ]
    )


def screw_seam_edges(shape: BuildPart | Part) -> ShapeList:
    """Edges still sharp where a screw hole opens out through the cap's flank.

    ``endcap.screw_seam_edges`` with the z band grown from the seat's own
    depth to the whole screw feature -- mouth lead, access bore and seat cone
    all break out at the same ``screw_breakout()``, so the seams now run from
    the bed to the cone's bottom at 11.1 rather than stopping at 1.1. Same
    two-pass selection: a box finds the neighbourhood, the angle decides.
    """
    part = shape.part if isinstance(shape, BuildPart) else shape
    if part is None:
        return ShapeList([])
    v = _loc(c.SCREW_BOSS_Z)
    inboard = e.cap_half_width(c.SCREW_BOSS_Z) - e.SCREW_SEAT_DEPTH - 0.1
    z_top = SCREW_ACCESS_DEPTH + e.SCREW_SEAT_DEPTH

    def near_a_seat(edge) -> bool:
        bb = edge.bounding_box()
        return (
            abs(bb.center().X) > inboard
            and bb.max.Z < z_top + 0.05
            and abs(bb.center().Y - v) < SCREW_ACCESS_D / 2 + 0.25
        )

    edges = part.edges()  # ty: ignore[invalid-argument-type]
    near = [edge for edge in edges if near_a_seat(edge)]
    return ShapeList(
        [
            edge
            for edge in near
            if (angle := interior_angle(part, edge)) is None or angle <= 120.0
        ]
    )


def screw_seam_fillet_edges(shape: BuildPart | Part) -> ShapeList:
    """The screw seams the fillet is allowed to roll: everything clear of the
    bed face.

    The seams that terminate on z=0 -- the sub-millimetre stubs where the
    access mouth's cone crosses the bed chamfer -- are held out, because OCC
    extrapolates a fillet slightly past the edge it terminates on and that
    edge ends on the bed: rolling them measured the part 0.017 mm below z=0,
    the same excursion ``SCREW_SEAM_FILLET``'s own sizing history records at
    0.25 on the standard cap. They are all far below the audit's 2 mm floor,
    and ``check_wired_screws`` bounds what stays raw here rather than letting
    it drift.
    """
    return ShapeList(
        [
            edge
            for edge in screw_seam_edges(shape)
            if edge.bounding_box().min.Z > 0.05
        ]
    )


# ---------------------------------------------------------------- derivations


def screw_reach() -> float:
    """How far the screw goes into the aluminium -- same law as the standard
    cap's, with the head's rim sunk an access stage deeper. The whole point of
    ``SCREW_ACCESS_DEPTH = EXTRA_T`` is that this equals ``e.screw_reach()``,
    and checks asserts the equality rather than trusting the arithmetic."""
    head_top = SCREW_ACCESS_DEPTH + (e.SCREW_SEAT_D - e.SCREW_HEAD_D) / 2
    return head_top + e.SCREW_LEN - CAP_T


def screw_breakout() -> float:
    """How far the screw feature reaches past the flank -- the access bore is
    the seat's own diameter, so this is ``e.screw_breakout()`` by construction,
    just standing 11.1 mm tall instead of 1.1."""
    return c.SCREW_SPACING / 2 + SCREW_ACCESS_D / 2 - e.cap_half_width(c.SCREW_BOSS_Z)


def chamber_run() -> float:
    """The cable's turning room: floor to the flange's inner face."""
    return CAP_T - CHAMBER_FLOOR_Z


def create_endcap_wired() -> Part:
    """The wired endcap, in its print pose: outer face on z=0, plug up.

    Same build discipline as ``endcap.create_endcap``: the thread and the
    rim-chamfer cutter are constructed *outside* the builder (a BasePartObject
    auto-adds itself; a nested BuildPart fuses into its parent), the two early
    chamfers are taken while every face is still clean, every OCC edge op goes
    through ``chamfer_edge``/``fillet_edge``, and the negotiable radii walk
    ladders.
    """
    thread = IsoThread(
        major_diameter=e.GLAND_MAJOR_D,
        pitch=e.GLAND_PITCH,
        length=e.GLAND_THREAD_L,
        external=False,
        end_finishes=("fade", "fade"),
    )
    rim_chamfer = _chamber_rim_chamfer()

    with BuildPart() as bp:
        with BuildSketch():
            add(e._cap_outline())
        extrude(amount=CAP_T)

        with BuildSketch(Plane.XY.offset(CAP_T)):
            add(e.plug_section())
        extrude(amount=PLUG_DEPTH)

        # The two clean-face chamfers, before any hole exists to refuse over.
        chamfer_edge(  # elephant's foot on the bed-facing perimeter
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), e.EDGE_CHAMFER
        )
        chamfer_edge(  # the plug's lead-in, on the way into the cavity
            bp, bp.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), e.PLUG_LEAD_IN
        )

        # Gland bore, driven through everything on the cap's axis.
        with BuildSketch():
            Circle(e.GLAND_MAJOR_D / 2)
        extrude(amount=CAP_T + PLUG_DEPTH, mode=Mode.SUBTRACT)

        # The chamber, cut from the floor to the flange's inner face. It stops
        # at CAP_T on purpose: the screw columns its section keeps have to run
        # the flange's whole depth (they are what the screws travel down and
        # what beds against the ports), but they have no business standing in
        # the plug's channel -- one cut carried through the plug would leave
        # them there as solid ribs down the hollow. The plug gets the standard
        # cap's own hollowing cut below, and the two voids meet at CAP_T over
        # a section that is identical except at the columns.
        with BuildSketch(Plane.XY.offset(CHAMBER_FLOOR_Z)):
            add(chamber_section())
        extrude(amount=CAP_T - CHAMBER_FLOOR_Z, mode=Mode.SUBTRACT)

        # The floor's rim into the bore: chamfered as a clipped boolean cone.
        add(rim_chamfer, mode=Mode.SUBTRACT)

        # The plug's own hollow, exactly as the standard cap cuts it -- same
        # section, same overshot ceiling clip (see plug_void_section's
        # docstring for why the clip sits above the plug's top on purpose).
        with BuildSketch(Plane.XY.offset(CAP_T)):
            add(e.plug_void_section())
        extrude(amount=PLUG_DEPTH, mode=Mode.SUBTRACT)

        # The hollow's own lead-in at the plug's tip, same ladder as the
        # standard cap -- the wire only exists now that the chamber is cut.
        for size in (e.PLUG_LEAD_IN, 0.3, 0.2):
            if chamfer_edge(bp, _plug_void_tip_edges(bp), size):
                break

        # Screws: mouth lead-in, then the seat cone sunk an access stage deep.
        for u, v in e._screw_centres():
            with Locations((u, v, 0)):
                Cone(
                    bottom_radius=SCREW_ACCESS_D / 2 + SCREW_MOUTH_LEAD,
                    top_radius=SCREW_ACCESS_D / 2,
                    height=SCREW_MOUTH_LEAD,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations((u, v, SCREW_ACCESS_DEPTH)):
                Cone(
                    bottom_radius=SCREW_ACCESS_D / 2,
                    top_radius=e.SCREW_CLEAR_D / 2,
                    height=e.SCREW_SEAT_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        with BuildSketch():
            with Locations(*e._screw_centres()):
                Circle(SCREW_ACCESS_D / 2)
        extrude(amount=SCREW_ACCESS_DEPTH, mode=Mode.SUBTRACT)
        with BuildSketch():
            with Locations(*e._screw_centres()):
                Circle(e.SCREW_CLEAR_D / 2)
        extrude(amount=CAP_T, mode=Mode.SUBTRACT)

        # The gland's own lead-in at the mouth, as in the standard cap.
        Cone(
            bottom_radius=e.GLAND_MAJOR_D / 2 + e.GLAND_LEAD_IN,
            top_radius=e.GLAND_MAJOR_D / 2,
            height=e.GLAND_LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        # The plug-top seams and corners, then the tip's own corners, then the
        # screw seams -- the standard cap's order and ladders throughout.
        fillet_edge(bp, _plug_top_seams(bp), e.PLUG_SEAM_FILLET)
        fillet_edge(bp, _plug_top_corners(bp), e.PLUG_SEAM_FILLET)

        # One rung deeper than the standard cap's ladder: this cap's tip
        # corners measure max_fillet ~= 0.17, so 0.3 and 0.2 are known
        # refusals and 0.15 is the rung that takes.
        for radius in (e.PLUG_TIP_FILLET, 0.2, 0.15):
            if fillet_edge(bp, plug_tip_corner_edges(bp), radius):
                break

        for radius in (e.SCREW_SEAM_FILLET, 0.15, 0.1):
            if fillet_edge(bp, screw_seam_fillet_edges(bp), radius):
                break

        # Sits on top of the plain collar, never meeting the mouth's lead-in.
        with Locations((0, 0, e.GLAND_COLLAR)):
            add(thread)

    part = bp.part
    part.color = e.CAP_COLOR
    part.label = "endcap (wired)"
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.endcap_wired``."""
    return create_endcap_wired()


__all__ = [
    "CAP_T",
    "CHAMBER_FLOOR_Z",
    "EXTRA_T",
    "chamber_run",
    "chamber_section",
    "create",
    "create_endcap_wired",
    "plug_tip_corner_edges",
    "screw_breakout",
    "screw_reach",
    "screw_seam_edges",
    "screw_seam_fillet_edges",
]
