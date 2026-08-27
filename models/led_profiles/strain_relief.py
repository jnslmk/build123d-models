"""Strain-relief insert: a printed stand-in for the M12 gland, when glands run out.

Screws into the same printed M12 x 1.5 female thread every cap in this family
carries (``endcap.GLAND_MAJOR_D``), so it needs nothing the caps do not already
have. Where the bought gland seals and clamps with a compression nut, this
part strain-relieves with a **cable tie**: the cable runs through a central
bore and out along a slotted collet snout, and the tie sits in a groove around
that snout, cinching the four fingers down onto the jacket. Pull on the cable
is taken by the tie bearing on the groove's shoulder and by the clamped
fingers, not by the solder joints inside the tube. No IP sealing -- that is
the one thing of the gland's this does not replace.

A collet rather than a tie-off post beside the cable, for two reasons. A
thread stops at an uncontrolled angle, so any one-sided feature would point
wherever the last turn left it -- the collet is axisymmetric and cannot clock
wrong. And the tie squeezes the jacket over four arcs of its full
circumference instead of kinking it sideways against a post, which respects
the ~27 mm bend radius ``mount_config.CABLE_BEND_R`` says this cable needs.

The thread: printed male in printed female wants 0.50 mm total diametral
clearance (V-profile, PETG -- see the printed-thread reference). The caps'
female thread is already cut 0.30 over nominal for the metal gland, so this
male thread gives back only the remaining 0.20. Under the head, a 45 deg cone
seats flush into the 45 deg lead-in the caps already chamfer into the bore
mouth (``endcap.GLAND_LEAD_IN``) -- a self-centring conical seat, which is
also what fixes the axial stop: the cone bottoms out with the male thread
spanning exactly the female's own band, and the stem tip on the relief
pocket's floor plane.

Which cap it serves: any of them mechanically, but a cable can only actually
*route* through ``endcap_wired`` -- the standard cap's own docstring is
explicit that its gland port is a fitting, not a cable route.

Print pose: stem tip down, snout up, thread axis vertical -- the only
orientation a thread prints well in, and it leaves every other feature
(45 deg seat cone, ruled loft to the hex, vertical collet fingers)
self-supporting. The bed contact is only the stem tip's ring (~23 mm^2), so
**slice it with a brim**. Hand-tighten by the hex (a 17 mm spanner fits
loosely); the conical seat needs no more.

Hardware: one standard cable tie up to 3.6 mm wide, ~1.3 mm thick (2.5 mm
ties fit too). Cable is the family's 6.7 mm LAPP round cable
(``mount_config.CABLE_OD``).
"""

from __future__ import annotations

from math import radians, tan

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    RegularPolygon,
    ShapeList,
    SlotOverall,
    add,
    extrude,
    fillet,
    loft,
    make_face,
    revolve,
)

from models.lib import fits
from models.lib.checks import interior_angle
from models.lib.edges import chamfer_edge, fillet_edge

from . import endcap as e
from . import mount_config as m

# ------------------------------------------------------------------ the thread

# Printed male inside printed female, ISO V profile: 0.50 mm total diametral
# clearance (printed-thread reference, PETG first attempt). The female is
# already cut e.THREAD_CLEARANCE = 0.30 over the gland's nominal, so the male
# major gives back only the remainder -- stating it this way keeps the *total*
# pinned at 0.50 even if the cap's own clearance is retuned.
MALE_CLEARANCE = 0.50
MALE_MAJOR_D = e.GLAND_THREAD_D - (MALE_CLEARANCE - e.THREAD_CLEARANCE)  # 11.80

# The root radius IsoThread will use, restated from its own min_radius formula
# (major - 2 * 5/8 * H, H the ISO fundamental triangle height) so the stem's
# core can be drawn before the thread object exists. create() asserts the two
# agree rather than trusting the copy.
_H = (e.GLAND_PITCH / 2) / tan(radians(30))
MALE_ROOT_D = MALE_MAJOR_D - 2 * (5 / 8) * _H  # 10.18

# The female thread's own crest bore, same formula on the cap's major: what
# the tip collar and thread root must pass through.
FEMALE_MINOR_D = e.GLAND_MAJOR_D - 2 * (5 / 8) * _H  # 10.68

# -------------------------------------------------------------------- the stem
#
# Print-pose z runs tip -> head: the tip enters the cap first in use. All
# lengths are derived from the cap's own thread stack so a cap change moves
# this part with it.

# How far the 45 deg seat cone sinks into the cap's 45 deg mouth lead-in
# before the two cones mate flush: the male major starts MALE_CLEARANCE/2 -
# THREAD_CLEARANCE/2 per side inside the female bore.
SEAT_SINK = (e.GLAND_MAJOR_D - MALE_MAJOR_D) / 2  # 0.25

# Tip lands exactly on the relief pocket's floor plane when seated -- the
# deepest the bore is guaranteed open in *both* caps (the wired cap's chamber
# floor is deeper still).
STEM_L = e.POCKET_FLOOR_Z - SEAT_SINK  # 9.75

# The thread band, placed so that at full seat it spans the female thread's
# own cap-z band [GLAND_COLLAR, GLAND_MALE_L] exactly: full 6.5 mm engagement,
# and the fade ends meet the female's own collar and fade.
THREAD_L = e.GLAND_THREAD_L  # 6.5
THREAD_Z0 = STEM_L - (e.GLAND_COLLAR - SEAT_SINK) - THREAD_L  # 2.0

# Below the thread, one-plus pitch of plain collar at the root diameter,
# chamfered at the tip -- the printed-thread lead-in rule, and the bed ring.
TIP_CHAMFER = 0.3

# ------------------------------------------------------------ seat cone + head

# The cone runs from the thread's major out past the mouth chamfer's rim
# (bore major + lead-in each side), plus margin so the seat still lands on
# the chamfer face when thread play lets the insert stop a little short.
SEAT_MARGIN = 0.5
SEAT_TOP_R = e.GLAND_MAJOR_D / 2 + e.GLAND_LEAD_IN + SEAT_MARGIN  # 7.45
SEAT_TOP_Z = STEM_L + (SEAT_TOP_R - MALE_MAJOR_D / 2)  # 45 deg by construction

# Hex head: hand/spanner grip. Across corners it must clear the envelope every
# mount already reserves for the bought gland (checked, not assumed).
HEAD_AF = 16.0
HEAD_H = 4.0
HEAD_CORNER_R = 1.0  # house rule: vertical edges fillet -- cut in the sketch

# Ruled loft from the seat cone's top circle to the hex, tall enough that the
# steepest ruling (to a hex corner) stays at 45 deg. Corner reach of the
# filleted hexagon: circumradius less what the corner fillet takes off.
_HEX_CIRCUM_R = (HEAD_AF / 2) / (3**0.5 / 2)  # apothem -> circumradius
_HEX_CORNER_REACH = _HEX_CIRCUM_R - HEAD_CORNER_R * (2 / 3**0.5 - 1)
LOFT_H = _HEX_CORNER_REACH - SEAT_TOP_R  # ~1.63
HEX_Z0 = SEAT_TOP_Z + LOFT_H
HEAD_TOP = HEX_Z0 + HEAD_H
HEAD_CHAMFER = 0.8  # top rim, house standard

# ------------------------------------------------------------ the collet snout

# Bore: the cable must thread through freely; the *grip* comes from the tie
# closing the fingers, not from the bore.
BORE_D = m.CABLE_OD + fits.FREE  # free fit, PETG baseline -- cable pass-through
BORE_MOUTH_LEAD = 0.4  # lead-in cone at the tip-end mouth

SNOUT_D = 11.5
SNOUT_H = 13.0
TIP_Z = HEAD_TOP + SNOUT_H

# The tie groove, revolved into the snout. Groove width takes ties up to
# 3.6 mm wide; depth is about a tie's thickness, so the tie rides flush.
TIE_SLOT_W = 4.2  # not a fit: pocket for a <=3.6 mm cable tie + hand room
GROOVE_DEPTH = 1.0
WAIST_R = SNOUT_D / 2 - GROOVE_DEPTH
# Crisp shoulder on the tip side (the direction cable pull would drag the
# tie), chamfered back to full diameter; 45 deg ramp on the head side, which
# is also what makes the groove's overhang printable.
SHOULDER_CHAMFER = 0.3
WAIST_TOP = TIP_Z - 2.0  # leaves a full-diameter retention band above
RAMP_Z0 = WAIST_TOP - TIE_SLOT_W - GROOVE_DEPTH

# Four slots (two crossed diametral cuts) make the wall four fingers the tie
# can close onto the jacket. Slot roots sit below the groove so the fingers
# hinge under the tie, not at it.
SLOT_W = 2.4
SLOT_Z0 = HEAD_TOP + 2.0

SNOUT_TIP_CHAMFER = 0.5
FLARE_H = 1.0  # 45 deg flare at the exit mouth, easy on the jacket


def slot_rim_edges(shape: BuildPart | Part) -> ShapeList:
    """Vertical slot-rim edges still sharp on the snout.

    The two crossed slot cuts leave vertical seams down the outer wall and
    the bore wall of every finger. They are the edges the fillet ladder in
    ``create()`` rolls; re-run after it, an empty answer is the assertion the
    ladder took. Same two-pass selection as the endcap's seam selectors: a
    cheap geometric gate (vertical, on the snout), then the interior angle
    decides -- which is also what keeps the fillets' own tangent lines from
    re-selecting themselves.
    """
    part = shape.part if isinstance(shape, BuildPart) else shape
    if part is None:
        return ShapeList([])
    out = []
    for edge in part.edges().filter_by(Axis.Z):  # ty: ignore[invalid-argument-type]
        if edge.bounding_box().center().Z < HEAD_TOP - 0.05:
            continue
        # None here is a periodic seam (a full-circumference wall's own
        # closing edge), not a sharp rim: handing one to OCC's fillet fails
        # the whole all-or-nothing call, so seams are excluded, and the edge
        # audit in checks.py accounts for them under their own allow entry.
        angle = interior_angle(part, edge)
        if angle is not None and angle <= 120.0:
            out.append(edge)
    return ShapeList(out)


def _stem_profile() -> Polyline:
    """The stem's revolve outline: tip collar, thread core, seat cone.

    One closed polyline on ``Plane.XZ`` (sketch (u, v) = global (x, z), so
    every constant goes in unconverted): chamfered tip ring at the thread's
    root diameter, root-diameter core under the thread band, a 45 deg flare
    up to the major, a stub of major-diameter shank, then the 45 deg seat
    cone -- closed back along the axis so ``revolve`` gets a face touching it.
    """
    root_r = MALE_ROOT_D / 2
    major_r = MALE_MAJOR_D / 2
    flare_z0 = THREAD_Z0 + THREAD_L  # core flares to major above the thread
    return Polyline(
        (0, 0),
        (root_r - TIP_CHAMFER, 0),
        (root_r, TIP_CHAMFER),
        (root_r, flare_z0),
        (major_r, flare_z0 + (major_r - root_r)),
        (major_r, STEM_L),
        (SEAT_TOP_R, SEAT_TOP_Z),
        (0, SEAT_TOP_Z),
        close=True,
    )


def _snout_profile() -> Polyline:
    """The collet snout's revolve outline, annular, grooved and chamfered.

    Everything the snout needs is in the one profile -- tie groove (45 deg
    ramp up, straight waist, chamfered shoulder), tip chamfer, and the exit
    mouth's 45 deg flare -- so no OCC edge op ever has to touch the snout's
    horizontal rims. The base is buried half a millimetre into the head so
    the fuse is a volume overlap, not a face-on-face coincidence.
    """
    snout_r = SNOUT_D / 2
    bore_r = BORE_D / 2
    base_z = HEAD_TOP - 0.5
    return Polyline(
        (bore_r, base_z),
        (snout_r, base_z),
        (snout_r, RAMP_Z0),
        (WAIST_R, RAMP_Z0 + GROOVE_DEPTH),
        (WAIST_R, WAIST_TOP),
        (snout_r - SHOULDER_CHAMFER, WAIST_TOP),
        (snout_r, WAIST_TOP + SHOULDER_CHAMFER),
        (snout_r, TIP_Z - SNOUT_TIP_CHAMFER),
        (snout_r - SNOUT_TIP_CHAMFER, TIP_Z),
        (bore_r + FLARE_H, TIP_Z),
        (bore_r, TIP_Z - FLARE_H),
        close=True,
    )


def create_strain_relief() -> Part:
    """The insert, in its print pose: tip ring on z=0, collet snout up.

    Build discipline as the endcap's: the thread is constructed *outside* the
    builder (a BasePartObject auto-adds itself at the origin otherwise) and
    added once, last, over a collar the mouth cones never touch; the one OCC
    chamfer (hex top rim) is taken while its face is still clean; the slot
    rims go through ``fillet_edge`` on a ladder and are read back by checks.
    """
    thread = IsoThread(
        major_diameter=MALE_MAJOR_D,
        pitch=e.GLAND_PITCH,
        length=THREAD_L,
        external=True,
        end_finishes=("fade", "fade"),
    )
    assert abs(thread.root_radius - MALE_ROOT_D / 2) < 1e-6, (
        "MALE_ROOT_D restates IsoThread.min_radius; the two have drifted"
    )

    with BuildPart() as bp:
        # Stem: one revolve, tip chamfer and seat cone baked into the profile.
        # The profile sketch is PRIVATE: a plain nested sketch stays *pending*
        # on the parent builder even after revolve() consumes it explicitly,
        # and the loft below would then sweep it up as a third section --
        # which is exactly what zeroed the part on the first build of this.
        with BuildSketch(Plane.XZ, mode=Mode.PRIVATE) as stem:
            with BuildLine():
                _stem_profile()
            make_face()
        revolve(profiles=stem.sketch.faces(), axis=Axis.Z)

        # Seat cone's top circle -> rounded hex, ruled so the steepest ruling
        # is the 45 deg the loft height was derived from, not a lofted bulge.
        with BuildSketch(Plane.XY.offset(SEAT_TOP_Z)):
            Circle(SEAT_TOP_R)
        with BuildSketch(Plane.XY.offset(HEX_Z0)) as hex_lo:
            RegularPolygon(HEAD_AF / 2, 6, major_radius=False)
            fillet(hex_lo.vertices(), HEAD_CORNER_R)
        loft(ruled=True)

        # The hex head proper.
        with BuildSketch(Plane.XY.offset(HEX_Z0)) as hex_hi:
            RegularPolygon(HEAD_AF / 2, 6, major_radius=False)
            fillet(hex_hi.vertices(), HEAD_CORNER_R)
        extrude(amount=HEAD_H)

        # Top rim chamfer while the face is still clean -- before the snout
        # stands on it and the bore opens through it.
        for size in (HEAD_CHAMFER, 0.5, 0.3):
            if chamfer_edge(
                bp, bp.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), size
            ):
                break

        # The collet snout: one revolve, groove and mouths in the profile.
        # PRIVATE for the same pending-face reason as the stem's.
        with BuildSketch(Plane.XZ, mode=Mode.PRIVATE) as snout:
            with BuildLine():
                _snout_profile()
            make_face()
        revolve(profiles=snout.sketch.faces(), axis=Axis.Z)

        # Cable bore through stem and head; the snout's own bore is already
        # open from its profile and lines up by construction.
        with BuildSketch():
            Circle(BORE_D / 2)
        extrude(amount=HEAD_TOP, mode=Mode.SUBTRACT)

        # Lead-in at the tip-end mouth. Boolean cone, per house style; it
        # stops a full collar below the thread's first turn.
        Cone(
            bottom_radius=BORE_D / 2 + BORE_MOUTH_LEAD,
            top_radius=BORE_D / 2,
            height=BORE_MOUTH_LEAD,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        # Two crossed diametral cuts -> four fingers. Each cut is a plate with
        # a rounded lower end (the finger hinge's stress relief), open out the
        # snout's tip.
        slot_l = TIP_Z + 2.0 - SLOT_Z0
        for plane in (Plane.XZ, Plane.YZ):
            with BuildSketch(plane):
                with Locations((0, SLOT_Z0 + slot_l / 2)):
                    SlotOverall(slot_l, SLOT_W, rotation=90)
            extrude(amount=SNOUT_D / 2 + 2.0, both=True, mode=Mode.SUBTRACT)

        # The slot rims, rolled: vertical edges, so the house rule says
        # fillet, on a ladder in case OCC refuses the first size.
        for radius in (0.5, 0.4, 0.3):
            if fillet_edge(bp, slot_rim_edges(bp), radius):
                break

        # The thread, last, over its collar -- constructed outside, added once.
        with Locations((0, 0, THREAD_Z0)):
            add(thread)

    part = bp.part
    part.color = e.CAP_COLOR
    part.label = "strain relief insert"
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.strain_relief``."""
    return create_strain_relief()


__all__ = [
    "BORE_D",
    "FEMALE_MINOR_D",
    "HEAD_AF",
    "HEAD_TOP",
    "MALE_CLEARANCE",
    "MALE_MAJOR_D",
    "MALE_ROOT_D",
    "SEAT_SINK",
    "SEAT_TOP_R",
    "SLOT_W",
    "SLOT_Z0",
    "SNOUT_D",
    "STEM_L",
    "THREAD_L",
    "THREAD_Z0",
    "TIE_SLOT_W",
    "TIP_Z",
    "WAIST_R",
    "create",
    "create_strain_relief",
    "slot_rim_edges",
]
