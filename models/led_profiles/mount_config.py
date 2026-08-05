"""Shared numbers for everything that grips the tube from outside.

The cradle, the strap, the corner, the stand and the feet all derive from here,
which in turn derives from ``config.py``. Nothing in this file is re-measured
off the extrusion.

Reasoning lives in ``docs/design-notes.md``. The two things worth knowing before
reading any of it:

**The mounts print in ASA, not PETG.** UV outdoors, and an HDT of ~95 C against a
tube that runs 40-60 C at 30-45 W. That changes every clearance -- see
``BORE_FIT`` below, which is the trap.

**Mount-local z is measured from the bed**, not from the tube's underside like
``config.py``. A cradle floor is ``CRADLE_WALL`` thick, so the tube's underside
sits at ``TUBE_UNDER_Z`` and its axis at ``TUBE_AXIS_Z``. Everything in this file
and its dependents uses that convention; ``config``'s z is offset by
``TUBE_UNDER_Z``.
"""

from __future__ import annotations

from math import radians, sqrt, tan

from models.lib import fits

from . import config as c

MATERIAL = "asa"

# ------------------------------------------------------------------ cradle

CRADLE_WALL = 4.0
CRADLE_LEN = 60.0

TUBE_UNDER_Z = CRADLE_WALL  # 4.0 -- the tube's underside, above the bed
TUBE_AXIS_Z = TUBE_UNDER_Z + c.HEIGHT / 2  # 19.0
# The cradle stops dead at the profile's rim. The stadium is at its full 26 mm
# from z=13 to z=17 (config's convention) and RIM_Z=16.8 is inside that band, so
# a trough ending here has no undercut at all: the tube drops straight in
# sideways, the diffuser is never shadowed, and nothing traps it.
CRADLE_DEPTH = TUBE_UNDER_Z + c.RIM_Z  # 20.8

# THE TRAP. fits.SNUG in ASA is -0.05 mm -- an interference fit on a 0.5 mm wall
# aluminium tube. SLIDING is the class that lands where SNUG does in PETG.
BORE_FIT = fits.for_material(fits.SLIDING, MATERIAL)  # 0.07 diametral

# Half the cradle's overall width at the mouth. Lives here rather than in
# cradle.py because the bolt circle below has to know where the wall's outer
# face is, and cradle.py imports *this* module. ``cradle.outer_half_width()``
# returns it.
CRADLE_OUTER_HALF_W = (c.WIDTH + BORE_FIT) / 2 + CRADLE_WALL  # 17.04

# Contact in two bands at the ends only. The relieved middle is not a fit: it is
# the +/-1 deg of angular compliance a closed polygon needs, because 0.5 deg of
# error is 13 mm over 1500 mm and three tubes will not otherwise close.
BAND_LEN = 15.0
BAND_RELIEF = 0.6

DRAIN_D = 4.0  # every upward-facing pocket drains; see design-notes S5

# House rule (AGENTS.md): chamfer horizontal edges, fillet vertical ones.
EDGE_CHAMFER = 0.8
EDGE_FILLET = 2.5

# ------------------------------------------------------------------- strap

STRAP_W = 18.0  # along the tube -- this, and only this, is the shadow
STRAP_T = 5.0

# The strap touches nothing. An earlier design had it grip the aluminium flank
# with compliant lips; there is no flank to grip. At the rim the extrusion
# offers only two ~0.5 mm wall edges and everything above it is diffuser, so
# the strap clears the lot and captures the tube instead of clamping it. This
# clearance is therefore also the tube's vertical play -- see strap.py.
DIFFUSER_CLEAR = 1.5
FOOT_H = 8.0  # see the bolt circle below -- this and BOSS_U are one decision

# --------------------------------------------------- the strap's arch envelope

# The strap's outer flank, in strap-local z (zero at the land it bolts to). It
# is a stadium: full width up to the upper arc's centre, then curving in. The
# bolt circle below is derived from it, so both live here rather than in
# strap.py, which is the module that *draws* this shape.
STRAP_AXIS_Z = TUBE_AXIS_Z - CRADLE_DEPTH  # -1.8, the tube's axis from the land
ARCH_HALF_W = c.WIDTH / 2 + DIFFUSER_CLEAR + STRAP_T  # 19.50
_ARCH_ARC_Z = STRAP_AXIS_Z + (c.HEIGHT - c.WIDTH) / 2  # 0.20


def arch_half_width(z: float) -> float:
    """Half the strap's outer width at height ``z`` above the land."""
    if z <= _ARCH_ARC_Z:
        return ARCH_HALF_W
    return sqrt(max(ARCH_HALF_W**2 - (z - _ARCH_ARC_Z) ** 2, 0.0))


# ------------------------------------------------------------- the bolt circle

# THE OTHER TRAP, and the reason none of these three are typed numbers. BOSS_U
# used to be 19.5 -- which is ARCH_HALF_W exactly, i.e. the bolt axis was *on*
# the arch's own flank. The hole's top mouth came out bisected by the arch
# springing (no flat land for two thirds of it) and an M4 head fouled the flank
# by 2.6 mm, so the strap could not actually be bolted down.
#
# The bolt must therefore stand clear of the flank at the height its head sits:
# the foot's top face. Raising FOOT_H is half the fix and moving BOSS_U out is
# the other, because the flank curves in as it rises -- 8 mm of foot buys 1.6 mm
# of the 4.25 mm needed, and BOSS_U pays the rest.
BOLT_HEAD_D = 7.0  # M4 socket cap; a button head is 7.6 but sits lower
BOLT_HEAD_CLEAR = 0.75
BOSS_U = arch_half_width(FOOT_H) + BOLT_HEAD_D / 2 + BOLT_HEAD_CLEAR  # 22.12

# The pad has to reach *inboard* far enough to fuse into the cradle wall -- it
# is not a free-standing column -- and outboard far enough to seat the head.
PAD_MERGE = 2.0  # ligament into the cradle's outer face
BOSS_OD = 2 * (BOSS_U - CRADLE_OUTER_HALF_W + PAD_MERGE)  # 14.17

INSERT_D = 5.7  # M4 heat-set: 5.5 table + FDM correction. NO lead-in chamfer.
INSERT_DEPTH = 9.0  # insert length + 1 mm relief well for displaced plastic
BOLT_CLEAR_D = 4.75  # M4 normal + 0.25; must stay under INSERT_D
BOLT_LEAD_IN = 0.5

# Strap stations along a cradle. Set by the strap's own width, not the band's:
# at BAND_LEN/2 the boss pad would hang 1.5 mm off the end of the cradle. Half a
# strap in from each end still lands the clamp over the contact bands.
STRAP_STATIONS = (STRAP_W / 2, CRADLE_LEN - STRAP_W / 2)

# ------------------------------------------------------- gland envelope

# MEASURED, with calipers, off the gland in hand. Both of the numbers derived
# from them below used to be ASSUMED -- 24.0 and 30.0 -- with the file telling
# whoever got there first to measure them before printing a corner. Doing that
# took ~5 mm off the envelope and 11 mm off the protrusion, and since the two
# together set every corner's setback, ~31 mm off the dark run at each vertex.
#
# A cable gland is two hexes. The **body** carries the male thread that goes
# into the cap, and its flats are what a spanner holds while the gland is done
# up, so they sit right against the cap's face. The **compression nut** screws
# onto the body's other end and closes the seal onto the cable; its outer end
# is not a taper but a round-over. ``gland.py`` draws all of it.
GLAND_BODY_AF = 16.2  # across flats, the hex against the cap's face
GLAND_BODY_H = 4.4  # and how much of the cap's face it stands on
GLAND_NUT_AF = 16.1  # across flats, the compression nut
GLAND_NUT_H = 14.4  # the nut's whole length ...
GLAND_NUT_HEX_H = 10.0  # ... of which this much is hex
GLAND_NUT_ROUND_H = GLAND_NUT_H - GLAND_NUT_HEX_H  # 4.4, the round-over

_AF_TO_AC = 2 / sqrt(3)  # a hexagon is 2/sqrt(3) wider across corners than flats

# The circle containing the fitted gland seen down the tube axis -- across the
# corners of whichever of the two hexes is wider. 18.71 mm.
GLAND_ENV_D = max(GLAND_BODY_AF, GLAND_NUT_AF) * _AF_TO_AC

# How far it stands out past the cap's outer face: the body's hex plus the nut
# that lands on it. Not the gland's overall length -- CAP_T of it is buried in
# the printed thread, and the nut's own thread is buried in the body. 18.8 mm.
GLAND_PROUD = GLAND_BODY_H + GLAND_NUT_H

CABLE_OD = 6.7  # LAPP OLFLEX CLASSIC 110, 3x1.5 -- see README
CABLE_BEND_R = 4 * CABLE_OD  # 26.8, fixed installation
SP16_D = 21.0  # inline connector barrel
SP16_LEN = 45.0


def gland_setback(angle: float) -> float:
    """Distance from the vertex to the cap's outer face, for a corner.

    Two glands pointing at a vertex are cylinders whose axes intersect, not
    spheres, so the clearance condition is not "twice the radius":

        a = r_gland / tan(angle / 2)

    at 60 deg that is 16.2 mm, and the cap face follows at ``a + GLAND_PROUD``.
    """
    return GLAND_ENV_D / 2 / tan(radians(angle / 2)) + GLAND_PROUD


def dark_run(angle: float) -> float:
    """Unlit tube at a corner, both sides, in mm.

    The aluminium starts CAP_T behind the cap face -- ``endcap.seated()`` puts
    the flange *outside* the tube -- and forgetting that term is worth 24 mm.
    """
    from .endcap import CAP_T

    return 2 * (gland_setback(angle) + CAP_T)
