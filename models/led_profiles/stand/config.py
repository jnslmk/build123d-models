"""Numbers for the folding tripod stand: post, legs and keepers.

Everything derives from ``led_profiles.config`` and ``mount_config``; nothing
here is re-measured off the extrusion.

**Frame.** The post is built in the family's mount-local section coordinates --
``cradle.tube_section`` and ``cradle.body_section`` draw the trough with the
tube's axis at ``m.TUBE_AXIS_Z`` above a bed -- and then sunk by ``SINK`` so
that axis lands on the post's own vertical axis. So in the post's own frame:

* ``z`` is height above the flange's underside, which is the print bed;
* ``y`` is the tube's cross-section height, zero on the tube's axis, ``+`` toward
  the diffuser (the front, where the light goes);
* ``x`` is across the tube, zero on its centre line.

The whole part is a **vertical cradle**: the same trough every other mount in
this family grips the tube with, stood on end. Two consequences follow and both
matter more than they look.

**The tube is captured, not clipped.** ``docs/design-notes.md`` S1 says nothing
wraps this section, and that is not a preference -- the assembled tube's width
rises monotonically from ``z=0`` to the straight band and is *constant* through
it, so a trough opening upward has no undercut to hook at any height. A lip that
does retain has to reach past ``TOP_ARC_Z`` into the diffuser, which both
shadows the light and puts the stand's load into the diffuser's own snap hooks
rather than the aluminium. So the trough holds the tube on three sides and a
**keeper** closes the fourth -- the same job the family's bolted ``strap`` does,
snapped on instead of bolted. ``checks.check_stand_no_undercut`` states the
monotonicity as a test so this cannot quietly be re-litigated.

**The seat is derived from the cable, not from the gland.** S10's defect was an
identity: the room in line with the gland was always ``WELL_H``, whatever the
fitting measured. Here the same identity is the fix -- ``SEAT_Z`` is
``gland.free_length()`` less the leg thickness the flange stands on, so the
clear run below the endcap's face tracks the cable's un-turnable first stretch
and a re-measured gland moves it.
"""

from __future__ import annotations

from math import cos, radians, sin, sqrt

from models.lib import fits

from .. import config as c
from .. import gland as gl
from .. import mount_config as m

# --------------------------------------------------------------------- frame

# The cradle sections are drawn with the tube's underside a wall above zero;
# drop them so the tube's axis lands on the post's own axis, where the mass
# wants it and where ``assemblies.standing`` expects to find it.
SINK = -m.TUBE_AXIS_Z  # -19.0

# The plane the trough is cut off at -- the profile's rim, in post-local y.
MOUTH_Y = m.CRADLE_DEPTH + SINK  # 1.8

# Half the trough's overall width, and how far its back face reaches.
OUTER_HALF_W = m.CRADLE_OUTER_HALF_W  # 17.085
BACK_Y = -(c.HEIGHT + m.BORE_FIT) / 2 - m.CRADLE_WALL  # -19.285

# ----------------------------------------------------------------- the legs

LEG_COUNT = 3

# The legs lie **flat on the floor** and swing about vertical pivots, Astera
# AX1-STD style: that is what nests them for packing, and it is why the pivot
# bores print as plain vertical holes rather than as cross-drilled clevises.
LEG_T = 10.0
LEG_W = 24.0
LEG_LEN = 240.0  # fits the smaller bed flat, with room for the foot's arc
LEG_HOLE_INSET = 14.0  # pivot centre in from the root end
LEG_ROOT_R = LEG_W / 2  # the root is a full round, so it sweeps cleanly
LEG_WAIST = 15.0  # the bar narrows between root and foot to save mass
LEG_FOOT_W = 26.0
LEG_FOOT_LEN = 34.0

# Ribbed rather than solid: a flat bar on the floor is barely loaded in bending
# (the floor supports it along its whole length), so the web only has to keep
# the two rails apart.
LEG_RIB_T = 3.2
LEG_SHELL = 3.2
LEG_POCKET_DEPTH = LEG_T - 2 * LEG_SHELL  # 3.6, a pocket in each face

# ---------------------------------------------------------------- the pivots

# One M6 x 30 socket cap per leg, nyloc under it. This is the only bought
# hardware on the stand and the only thing on it that turns.
PIVOT_R = 30.0
PIVOT_CLEAR_D = 6.6  # M6 normal clearance + the FDM adder
PIVOT_HEAD_D = 10.0  # M6 socket cap
PIVOT_CBORE_D = PIVOT_HEAD_D + fits.for_material(fits.FREE, m.MATERIAL) + 1.0
PIVOT_CBORE_H = 6.0
PIVOT_NUT_AF = 10.0  # M6 nyloc across flats
PIVOT_NUT_POCKET_D = PIVOT_NUT_AF * 2 / sqrt(3) + fits.for_material(
    fits.FREE, m.MATERIAL
)
PIVOT_NUT_POCKET_H = 6.5  # M6 nyloc is 6.0 tall
PIVOT_LEAD_IN = 0.5

# The deployed/folded stop: an arc slot in the flange's underside with a pin on
# the leg riding in it. Its two ends are the two positions, so the tripod lands
# on a true 120 deg spread every time rather than on the user's eye. Radius is
# clear of the pivot counterbore (which reaches r = 8.3) with room for the
# slot's own half width.
STOP_SLOT_R = 19.0
STOP_SLOT_W = 5.6
STOP_SLOT_DEPTH = 3.0
STOP_PIN_D = STOP_SLOT_W - fits.for_material(fits.FREE, m.MATERIAL)
STOP_PIN_H = STOP_SLOT_DEPTH - 0.4

# Measured from +x, so 270 is straight back (-y, behind the lamp). One leg
# points that way, under the post's own mass, which puts the tripod's
# *strongest* direction (over a leg, at full reach) behind the lamp and its
# weakest (the chord between two legs, at half reach) in front. A push on the
# lit face tips the lamp backward, so that is the way round the strength wants
# to go -- and it is free, being only a choice of clocking. design-notes S4.
LEG_AZIMUTHS = (270.0, 30.0, 150.0)

# Folding is what nests them, and the sweeps are **not** all the same, which is
# the thing that looks like an oversight and is not. Nesting means every leg
# ends up pointing the same way; the deployed directions are 120 deg apart; so
# the sweeps have to be 0 and +/-120, not 120 all round. A uniform sweep just
# rotates the whole tripod and leaves the legs 120 deg apart -- still spread,
# still un-packable. So the rear leg is *indexed* rather than swung (its stop is
# a plain socket, no arc) and the two front legs fold back onto it, which also
# means the leg that carries the post's own mass is the one that never moves.
#
# Checked rather than assumed: at the half-way point of the sweep the two front
# legs run parallel, 52 mm of pivot spacing apart, and the perpendicular gap
# between them is 52 * sin 150 = 26 mm against a 24 mm bar. It clears, but only
# just -- ``checks.check_stand_legs`` holds that number.
LEG_FOLD_SWEEP = 120.0
LEG_FOLD_DIRS = (0.0, -1.0, 1.0)

# ---------------------------------------------------------------- the flange

# 12 rather than 10 so an M6 head bears on 6 mm of ASA after its counterbore,
# not on 3.5. The head is the only thing on this part under bolt preload.
FLANGE_T = 12.0
FLANGE_CORE_R = 26.0  # reaches past the trough's own footprint (r = 25.7)
FLANGE_LOBE_R = 13.0  # a round pad under each pivot

# ------------------------------------------------------------------ the seat

# S10's identity, used forwards. ``gland.free_length()`` is the gland's
# protrusion plus the cable's un-turnable first run; the flange stands one leg
# thickness off the floor, so the seat only has to find the rest of it.
SEAT_Z = gl.free_length() - LEG_T  # 38.8

# The bore under the seat: clears the fitted gland, not the cable, because the
# cable turns out through the trough's own mouth well before it reaches here.
WELL_D = m.GLAND_ENV_D + 2.0  # 20.71
CABLE_SLOT_W = m.CABLE_OD + 2.0  # 8.7

# ------------------------------------------------------------- the stations

# Where the keepers go -- the height of each arch's centre. The lower one has
# to grip **aluminium**: the endcap occupies ``CAP_T`` above the seat and
# design-notes S3 is explicit that no mount takes its load through the two M2
# self-tappers holding it on. ``checks.check_stand_stations`` holds that.
STATION_LOW = 70.0
STATION_HIGH = 210.0
STATIONS = (STATION_LOW, STATION_HIGH)
STATION_SPACING = STATION_HIGH - STATION_LOW  # 140

POST_H = STATION_HIGH + 24.0 / 2 + 3.0  # 225

# ------------------------------------------------------- the keeper stations

# A boss pad on each flank at each station, with a blind vertical socket in it,
# and a keeper whose two pegs drop into them.
#
# **Why a key and not a snap.** A snap here would have to hold
# ``keeper_pull()`` -- 96 N of forward pull on the lower keeper under
# design-notes S3's abuse case -- and a snap does not do that. Riding the
# post's own outer stadium gives a return angle of about 20 deg at the lip,
# which with ASA's 0.7 % repeated strain is worth roughly 30 N however the arm
# is proportioned: a snap is an assembly aid, not a retention feature. A peg in
# a socket is bounded by bearing stress instead, and 2 x PEG_D x PEG_L of it
# carries the same load at under 1 MPa. So the keeper drops in, gravity holds
# it, and the socket's front wall -- solid material, not a spring -- is what
# stands between the lamp and the floor.
PEG_D = 6.0
PEG_L = 20.0
PEG_FIT = fits.for_material(fits.SLIDING, m.MATERIAL)  # 0.07, ASA
PEG_LEAD_IN = 0.8
PEG_U = 21.0  # peg axis, out from the tube's centre line
PEG_Y = -3.0  # and where it sits across the section

PAD_OD = 11.0
PAD_BACK_Y = -8.0  # far enough forward that the pad meets the trough all along
PAD_H = PEG_L + 4.0  # socket depth plus a floor

# A pad juts ``PAD_OD`` out of the trough's flank, and in this print pose its
# underside would be a cantilevered horizontal ledge -- the one real overhang
# the part would otherwise have. So the pad is grown out of the flank over
# ``PAD_RAMP`` of 45 deg taper first: self-supporting the whole way, and it puts
# a gusset under the socket at the same time.
PAD_RAMP = 4.0

SOCKET_DEPTH = PEG_L + 1.0  # a relief well, so the peg seats on the pad's face

# ---------------------------------------------------------------- the keeper

# An arch that clears the diffuser exactly the way ``strap.py``'s does: it
# touches nothing, it captures. Same 18 mm width, so the optical cost of a
# station is the one the family already prices in.
KEEPER_W = m.STRAP_W  # 18.0 -- along the tube, and this is the whole shadow
KEEPER_T = 5.0
KEEPER_CLEAR = m.DIFFUSER_CLEAR  # 1.5
KEEPER_FOOT_IN = OUTER_HALF_W + 0.5  # clears the post's own flank

# Where the keeper's section is cut off underneath. Not ``MOUTH_Y``, which is
# the obvious choice and the wrong one: the arch's inner and outer stadiums both
# turn from straight flank into arc at ``STRAIGHT_H / 2``, so a cut anywhere
# between there and the mouth leaves two 0.65 mm slivers of flank on the
# silhouette -- shorter than ``EDGE_CHAMFER``, which makes the whole bed-face
# chamfer an all-or-nothing OCC call that fails. Cutting *on* that plane
# removes them, and it is 0.4 mm clear of the post's mouth into the bargain.
KEEPER_CLIP_Y = c.STRAIGHT_H / 2  # 2.2
KEEPER_FOOT_OUT = PEG_U + PAD_OD / 2

# ------------------------------------------------------------------- finish

EDGE_CHAMFER = m.EDGE_CHAMFER  # 0.8
EDGE_FILLET = m.EDGE_FILLET  # 2.5

# The mouth's lips get less than the family's full radius: the bore's lip and
# the outer wall's are one ``CRADLE_WALL`` apart, and 2.5 on both would eat the
# wall between them. Same 0.6 factor the old stand used, for the same reason.
LIP_FILLET = 0.6 * EDGE_FILLET  # 1.5
PAD_FILLET = 2.0  # the pads are 11 mm wide; this is the biggest that leaves a land
DRAIN_D = m.DRAIN_D  # 4.0

ASA_DENSITY = 1.07e-3  # g/mm^3


def pivot_positions() -> list[tuple[float, float]]:
    """Where the three pivot bolts sit, in the flange's own plane."""
    return [
        (PIVOT_R * cos(radians(a)), PIVOT_R * sin(radians(a))) for a in LEG_AZIMUTHS
    ]


def leg_reach() -> float:
    """Pivot circle plus the leg's own overhang: the tripod's radius."""
    return PIVOT_R + LEG_LEN - LEG_HOLE_INSET


def peg_bearing_stress(tip_force_n: float = 10.0) -> float:
    """Bearing stress in the two pegs under ``keeper_pull``, in MPa.

    The pull is shared by two pegs, each presenting its diametral projection
    over the socket's depth. This is the number that replaced a snap-fit strain
    calculation when the keeper stopped being a spring.
    """
    return keeper_pull(tip_force_n) / (2 * PEG_D * PEG_L)


def keeper_pull(tip_force_n: float = 10.0) -> float:
    """Forward pull on the lower keeper from a push at the tube's far tip.

    The two keepers are a couple, not a grip: a horizontal push ``tip_force_n``
    at the top of the tube is reacted as equal and opposite forces at the two
    stations, divided by their spacing. ``10 N`` is design-notes S3's abuse
    case, the load this family sizes structure against.
    """
    from ..endcap import CAP_T

    tip_z = SEAT_Z + CAP_T + c.LENGTH
    return tip_force_n * (tip_z - STATION_HIGH) / STATION_SPACING


def tip_force(post_mass_g: float, leg_mass_g: float, tube_mass_g: float = 450.0) -> float:
    """Horizontal push at the top of the tube that tips the stand, in newtons.

    A tripod tips about the line joining two adjacent legs, at ``reach *
    cos 60`` -- **half** the reach. Quoting the full reach, or a tip angle,
    flatters it by a factor of two. This is the conservative direction; over a
    leg the tripod is twice as good, which is why ``LEG_AZIMUTHS`` puts one
    behind the lamp.
    """
    mass_kg = (post_mass_g + tube_mass_g + LEG_COUNT * leg_mass_g) / 1000.0
    r_eff = leg_reach() * cos(radians(60.0)) / 1000.0
    return mass_kg * 9.81 * r_eff / (c.LENGTH / 1000.0)
