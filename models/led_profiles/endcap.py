"""Endcap: closes the profile, carries the M12 cable gland, screws to the ports.

One design, used at both ends -- every lamp has an input and an output pigtail,
so both caps are glanded.

The cap is two pieces of one solid: a thin **flange** the width of the tube, and
a 15 mm **plug** that goes down the wiring cavity behind it.

**The flange is as thin as the gland's own thread.** A stock M12x1.5 gland
carries ~8 mm of male thread and seals on its flange against the cap's face, so
anything past 8 mm of cap is depth the gland cannot reach into and screw length
the two cap screws cannot spend on the aluminium. ``CAP_T`` is therefore 8.0,
of which ``GLAND_COLLAR`` is plain bore and the rest is cut thread.

**The plug is solid, not a ring.** It fills the cavity's lower half-disc for
``PLUG_DEPTH``, with the gland bore driven straight through it -- nothing is
left standing in the bore's way. A ring would have to dodge the bore; a
half-disc simply has the bore taken out of it, and the same material takes the
rocking moment off the two screws that a much longer ring used to.

**The gland is on the cap's own centre.** ``GLAND_Z`` is ``c.HEIGHT / 2``, so
the bore, the flange and the plug are all one axis and the part is symmetric
about it. Worth stating plainly, because it costs something: the wiring cavity's
ceiling is at ``c.CAVITY_TOP_Z``, well below that axis, so a bore centred on the
cap opens into the cavity through a slot only about
``c.CAVITY_TOP_Z - (GLAND_Z - GLAND_MAJOR_D / 2)`` mm tall. That is narrower
than the 6.7 mm cable the gland seals on, so **a cable cannot be fed from this
gland into the tube's wiring cavity**; the gland is a fitting on a centred axis,
not a route into the cavity. ``check_gland`` measures that slot rather than
asserting a route that is not there.

**The screw heads are sunk, and they break out.** The screws are short and their
heads are ``SCREW_HEAD_D`` = 4.4 mm across, so each gets a pocket from the outer
face down to a ``SCREW_FLOOR_T`` floor -- the head goes in, the screw spends its
length in the aluminium, and only the floor carries the clamp. The ports sit
``c.SCREW_SPACING / 2`` from the axis and the cap is flush with the tube, so
that pocket reaches about 0.35 mm past the flank and bites a shallow scallop out
of each side. Deliberate, and the size of the bite is asserted in
``check_screw_pockets`` so it cannot quietly grow.

Print pose: outer face down on the bed, plug up. That puts the gland thread on a
vertical axis (the only axis worth printing a thread on), gives the largest
possible first layer, and leaves no overhang anywhere -- the plug grows *out of*
the flange rather than hanging off it.

Edge treatments, house rule: chamfer horizontal, fillet vertical. Two chamfers
are taken while the part is still a plain two-step prism, before the bore, the
screw pockets and the thread exist -- the bed face's outer wire
(``EDGE_CHAMFER``, elephant's foot) and the plug's leading edge
(``PLUG_LEAD_IN``). The hole mouths are coned as booleans instead. The flange
has nothing to fillet -- it is a stadium, so its flanks run into its arcs
tangentially and it has no vertical corners at all -- but the plug does: the
gland bore leaves two lengthwise seams down its flat top where the cylinder
breaks out through it, and those get ``PLUG_SEAM_FILLET`` after the bore is cut.

Edges left square on purpose, and which should stay that way: the whole of the
``CAP_T`` face, which is what beds against the extrusion's 0.5 mm wall; the
gland bore's mouth there, which is the thread's own faded exit and the one place
a lead-in would hand OCC a degenerate fuse (see ``GLAND_COLLAR``); the bore's
crescent through the plug's tip, where only the outer wire got the lead-in; and
the seams where a screw pocket cuts out through the flank, which are the scallop
the paragraph above owns up to -- breaking those would only widen the bite.
"""

from __future__ import annotations

from math import sqrt

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cone,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    Rotation,
    ShapeList,
    Sketch,
    SlotOverall,
    add,
    extrude,
)

from models.lib import fits
from models.lib.edges import as_part, chamfer_edge, fillet_edge

from . import config as c
from .profile import _big, _loc

# ------------------------------------------------------------------ the cap

# Flush with the extrusion. It used to stand 0.6 mm proud all round so an M2 pan
# head could land entirely on the face outboard of the port; measured against
# the real tube that collar read 0.55 mm too wide per side, and the head is sunk
# into the face now rather than sitting on it, so the collar has no job left.
CAP_PROUD = 0.0
CAP_W = c.WIDTH + 2 * CAP_PROUD
CAP_H = c.HEIGHT + 2 * CAP_PROUD

# Set by the gland's own thread, not by the printed-thread engagement rule: a
# stock M12x1.5 cable gland carries ~8 mm of male thread and then seals on its
# flange, so a cap thicker than 8 mm is bore the gland never reaches and screw
# length spent in plastic instead of in the aluminium.
CAP_T = 8.0
# Same 0.8 as ``mount_config.EDGE_CHAMFER``, kept local because this module sits
# *upstream* of that one -- corner.py imports CAP_T and CAP_W from here, and
# mount_config carries the mounts' ASA material with it.
EDGE_CHAMFER = 0.8

# ----------------------------------------------------------------- the plug

# The part that goes into the aluminium. A solid half-disc following the
# cavity's lower arc, not a ring: the gland bore is driven straight through it,
# and a ring would have had to dodge the bore rather than simply lose the
# material to it.
PLUG_DEPTH = 15.0
# SLIDING, not SNUG -- it has to go together against a 1.5 m aluminium
# extrusion's straightness, not a printed hole.
PLUG_FIT = fits.SLIDING
PLUG_TOP_GAP = 0.4  # clears the screw bosses bulging out of the cavity ceiling

# Lead-in on the plug's leading edge, so it starts into the cavity instead of
# catching on it. 0.4 mm is already ~3.5x the radial clearance and leaves a flat
# the slicer can lay real beads on.
PLUG_LEAD_IN = 0.4

# The two lengthwise seams the gland bore leaves down the plug's flat top. A
# fillet, not a chamfer: they are vertical in print pose. Kept small because the
# crescent's own walls are what carry the plug, and a big radius here would eat
# into them for no gain -- nothing mates against these edges.
PLUG_SEAM_FILLET = 0.5

# ---------------------------------------------------------------- the gland

GLAND_THREAD_D = 12.0  # M12 x 1.5, the size the README specifies
GLAND_PITCH = 1.5
# Printed female against a real metal gland: +0.30 mm on the female major
# diameter. IsoThread emits the basic profile with zero allowance, so every bit
# of printing clearance has to be added here.
THREAD_CLEARANCE = 0.30
GLAND_MAJOR_D = GLAND_THREAD_D + THREAD_CLEARANCE

# One full pitch of plain bore below the thread, chamfered, per the printed-
# thread rule against starting a thread at z=0. It also keeps the mouth's
# lead-in cone clear of the thread: cut the two into each other and OCC's fuse
# quietly returns the thread alone instead of the cap.
GLAND_COLLAR = GLAND_PITCH
GLAND_THREAD_L = CAP_T - GLAND_COLLAR
GLAND_LEAD_IN = 0.8

# On the cap's own centre -- see the module docstring, including what that costs
# the cable route.
GLAND_Z = c.HEIGHT / 2

# ---------------------------------------------------------------- the screws

SCREW_CLEAR_D = 2.65  # M2 normal clearance + the FDM adder
SCREW_LEAD_IN = 0.5

# The heads are 4.4 mm across and the screws are short, so each head is sunk to
# within SCREW_FLOOR_T of the aluminium and the whole of the screw's length is
# available to the port. FREE, not a named bore fit: this pocket locates
# nothing, it only has to swallow a head.
SCREW_HEAD_D = 4.4
SCREW_CBORE_D = SCREW_HEAD_D + fits.FREE
# What is left under the head. Six 0.2 mm layers -- enough to carry the clamp of
# a 2 mm screw and nothing more, which is the whole point of sinking the head.
SCREW_FLOOR_T = 1.2
SCREW_CBORE_DEPTH = CAP_T - SCREW_FLOOR_T

CAP_COLOR = Color(0.25, 0.27, 0.30)


def _cap_outline() -> Sketch:
    """The flange: the profile's own stadium, flush with it."""
    with BuildSketch() as s:
        SlotOverall(CAP_H, CAP_W, rotation=90)
    return s.sketch


def _cavity_outline(inset: float, top_gap: float) -> Sketch:
    """The wiring cavity's cross-section, shrunk by ``inset`` all round.

    Shrinking a stadium is exact -- both overall dimensions lose ``2 * inset``,
    the straight section is untouched -- so this needs no offset operation.
    """
    with BuildSketch() as s:
        SlotOverall(
            c.HEIGHT - 2 * c.WALL - 2 * inset,
            c.WIDTH - 2 * c.WALL - 2 * inset,
            rotation=90,
        )
        with Locations((0, _loc(c.CAVITY_TOP_Z - top_gap))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.INTERSECT
            )
    return s.sketch


def plug_section() -> Sketch:
    """The plug: the cavity's half-disc, solid, less its running clearance."""
    return _cavity_outline(PLUG_FIT / 2, PLUG_TOP_GAP)


def plug_top_z() -> float:
    """Tube-local height of the plug's flat top, in ``config``'s convention."""
    return c.CAVITY_TOP_Z - PLUG_TOP_GAP


def cavity_slot_h() -> float:
    """How much of the gland bore actually opens into the wiring cavity.

    The bore is on the cap's centre and the cavity's ceiling is well below it,
    so only the bore's lower crescent looks into the tube. This is the height of
    that opening, and it is what says whether a cable can pass -- see the module
    docstring, which is explicit that it cannot.
    """
    return c.CAVITY_TOP_Z - (GLAND_Z - GLAND_MAJOR_D / 2)


def create_endcap() -> Part:
    """The endcap, in its print pose: outer face on z=0, plug pointing up.

    Cap-local axes map to the profile's as x -> u and y -> z, so every constant
    from ``config`` can be used directly through ``_loc``.
    """
    # Built *before* the BuildPart is opened, deliberately. IsoThread is a
    # BasePartObject with mode=Mode.ADD, so constructing it inside a builder
    # auto-adds it at the origin; the add() below would then be a *second* copy.
    # That matters more here than it used to: the gland is on the cap's centre
    # now, so the builder's origin *is* the bore's mouth and a stray copy would
    # land squarely in the lead-in cone, where OCC's fuse quietly returns the
    # thread alone instead of the cap. Construct it outside, add it once.
    thread = IsoThread(
        major_diameter=GLAND_MAJOR_D,
        pitch=GLAND_PITCH,
        length=GLAND_THREAD_L,
        external=False,
        end_finishes=("fade", "fade"),
    )

    with BuildPart() as bp:
        with BuildSketch():
            add(_cap_outline())
        extrude(amount=CAP_T)

        with BuildSketch(Plane.XY.offset(CAP_T)):
            add(plug_section())
        extrude(amount=PLUG_DEPTH)

        # Edge treatments, house rule: chamfer horizontal, fillet vertical.
        # Both chamfers are taken here rather than at the end -- this is the last
        # moment at which every face they select from is still clean, before the
        # bore, the screw pockets and the thread arrive, and a chamfer OCC
        # refuses on a bare face is a chamfer that was never going to work. Each
        # goes through ``chamfer_edge`` so a refusal is confined to its own
        # feature instead of quietly taking the one after it. The flange has
        # nothing to fillet: it is a stadium, so its flanks meet its arcs
        # tangentially and it has no vertical corners at all. The plug's two
        # bore seams do, and they have to wait for the bore -- see below. There
        # is no collar chamfer any more either: the cap is flush with the tube,
        # so there is no step to break.
        chamfer_edge(  # elephant's foot on the bed-facing perimeter
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), EDGE_CHAMFER
        )
        chamfer_edge(  # the plug's lead-in, on the way into the cavity
            bp, bp.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), PLUG_LEAD_IN
        )

        # Gland bore, then the thread fused into it. Through the plug as well as
        # the flange: nothing is left standing in the bore's way.
        with BuildSketch():
            Circle(GLAND_MAJOR_D / 2)
        extrude(amount=CAP_T + PLUG_DEPTH, mode=Mode.SUBTRACT)

        # Screw pockets: the head's counterbore from the outer face down to the
        # floor, with the clearance hole carrying on through it. Through the
        # flange only -- the plug is a half-disc and the ports sit above it.
        with BuildSketch():
            with Locations(*_screw_centres()):
                Circle(SCREW_CBORE_D / 2)
        extrude(amount=SCREW_CBORE_DEPTH, mode=Mode.SUBTRACT)
        with BuildSketch():
            with Locations(*_screw_centres()):
                Circle(SCREW_CLEAR_D / 2)
        extrude(amount=CAP_T, mode=Mode.SUBTRACT)

        # Lead-ins at every bed-facing hole mouth, cut as boolean cones rather
        # than edge chamfers -- house style, and OCC chamfers are flaky next to
        # a thread. The screws' cone sits on the *counterbore floor*, where the
        # screw has to find its hole blind from inside the pocket; the pocket's
        # own mouth at the bed is part of the outer wire the EDGE_CHAMFER above
        # already treated, because it breaks out through the flank.
        for u, v in _screw_centres():
            with Locations((u, v, SCREW_CBORE_DEPTH)):
                Cone(
                    bottom_radius=SCREW_CLEAR_D / 2 + SCREW_LEAD_IN,
                    top_radius=SCREW_CLEAR_D / 2,
                    height=SCREW_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        Cone(
            bottom_radius=GLAND_MAJOR_D / 2 + GLAND_LEAD_IN,
            top_radius=GLAND_MAJOR_D / 2,
            height=GLAND_LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        # The two seams the bore leaves down the plug's flat top, where the
        # cylinder breaks out through it. They run the length of the plug and
        # are vertical in print pose, so the house rule wants a fillet, not a
        # chamfer -- and taken here, after the bore and before the thread, they
        # are the only edges in the part at that (x, y).
        fillet_edge(bp, _plug_bore_seams(bp), PLUG_SEAM_FILLET)

        # Sits on top of the plain collar, so it never meets the lead-in above.
        with Locations((0, 0, GLAND_COLLAR)):
            add(thread)

    part = bp.part
    part.color = CAP_COLOR
    part.label = "endcap"
    return part


def plug_bore_half_width() -> float:
    """Half-width of the gland bore where it breaks through the plug's top.

    The bore is on the cap's centre and the plug's top is ``PLUG_TOP_GAP`` below
    the cavity ceiling, so the crescent the bore takes out of that top face is
    this wide either side of the axis.
    """
    drop = GLAND_Z - plug_top_z()
    return sqrt(max((GLAND_MAJOR_D / 2) ** 2 - drop**2, 0.0))


def _plug_bore_seams(bp: BuildPart) -> ShapeList:
    """The two lengthwise edges where the bore breaks out of the plug's top.

    Selected by geometry rather than off a face: the plug's top face and the
    bore's wall both carry other wires (the tip's outer stadium, the thread's
    exit), and only these two run the plug's length at the crescent's ends.
    """
    y_top = _loc(plug_top_z())
    x_seam = plug_bore_half_width()

    def is_seam(edge) -> bool:
        bb = edge.bounding_box()
        return (
            bb.min.Z > CAP_T - 0.01
            and abs(bb.max.Y - y_top) < 0.01
            and abs(abs(bb.center().X) - x_seam) < 0.05
        )

    return ShapeList([edge for edge in bp.edges().filter_by(Axis.Z) if is_seam(edge)])


def _screw_centres() -> list[tuple[float, float]]:
    """Cap-local centres of the two screw holes, on the profile's ports."""
    return [
        (-c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z)),
        (c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z)),
    ]


def cap_half_width(z: float) -> float:
    """Half-width of the cap's stadium at tube-local height ``z``.

    Full ``CAP_W / 2`` through the straight band between the two arc centres,
    and off the arc above or below it.
    """
    if c.BOT_ARC_Z <= z <= c.TOP_ARC_Z:
        return CAP_W / 2
    arc_z = c.TOP_ARC_Z if z > c.TOP_ARC_Z else c.BOT_ARC_Z
    rise = abs(z - arc_z)
    return sqrt(max((CAP_W / 2) ** 2 - rise**2, 0.0))


def screw_breakout() -> float:
    """How far a screw pocket reaches past the cap's flank, in mm.

    Positive means the pocket cuts out through the side -- the scallop the
    module docstring owns up to. It is the price of a flush cap: the head is
    4.4 mm across and the port sits ``c.SCREW_SPACING / 2`` out, which leaves
    less room outboard than half a head.
    """
    return c.SCREW_SPACING / 2 + SCREW_CBORE_D / 2 - cap_half_width(c.SCREW_BOSS_Z)


def seated(at_far_end: bool = False, length: float = c.LENGTH) -> Part:
    """The cap moved from its print pose into place on the profile.

    House rule: the part is authored in the pose it prints in, and the assembly
    is what moves it. Cap-local +z is the insertion direction, so it maps to the
    profile's +x at the near end and -x at the far end.
    """
    cap = create_endcap()
    # cap (x, y, z) -> profile (y, z, x). Composed explicitly rather than as a
    # single Rotation(90, 0, 90): build123d's three-angle form does not apply
    # them in the order that reads, and lands the cap on its side.
    upright = Rotation(0, 0, 90) * Rotation(90, 0, 0) * cap
    if not at_far_end:
        placed = as_part(Pos(-CAP_T, 0, c.HEIGHT / 2) * upright)
    else:
        placed = as_part(
            Pos(length + CAP_T, 0, c.HEIGHT / 2) * (Rotation(0, 0, 180) * upright)
        )
    placed.color = CAP_COLOR
    placed.label = "endcap (far)" if at_far_end else "endcap (near)"
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.endcap``."""
    return create_endcap()


__all__ = ["create", "create_endcap", "seated"]
