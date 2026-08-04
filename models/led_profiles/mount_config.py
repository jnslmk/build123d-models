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

from math import radians, tan

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

# Contact in two bands at the ends only. The relieved middle is not a fit: it is
# the +/-1 deg of angular compliance a closed polygon needs, because 0.5 deg of
# error is 13 mm over 1500 mm and three tubes will not otherwise close.
BAND_LEN = 15.0
BAND_RELIEF = 0.6

DRAIN_D = 4.0  # every upward-facing pocket drains; see design-notes S5
EDGE_CHAMFER = 0.8

# ------------------------------------------------------------------- strap

STRAP_W = 18.0  # along the tube -- this, and only this, is the shadow
STRAP_T = 5.0

# The strap touches nothing. An earlier design had it grip the aluminium flank
# with compliant lips; there is no flank to grip. At the rim the extrusion
# offers only two ~0.5 mm wall edges and everything above it is diffuser, so
# the strap clears the lot and captures the tube instead of clamping it. This
# clearance is therefore also the tube's vertical play -- see strap.py.
DIFFUSER_CLEAR = 1.5
FOOT_H = 6.0

BOSS_U = 19.5  # bolt axis, outboard of the cradle wall
BOSS_OD = 12.0
INSERT_D = 5.7  # M4 heat-set: 5.5 table + FDM correction. NO lead-in chamfer.
INSERT_DEPTH = 9.0  # insert length + 1 mm relief well for displaced plastic
BOLT_CLEAR_D = 4.75  # M4 normal + 0.25; must stay under INSERT_D
BOLT_LEAD_IN = 0.5

# Strap stations along a cradle. Set by the strap's own width, not the band's:
# at BAND_LEN/2 the boss pad would hang 1.5 mm off the end of the cradle. Half a
# strap in from each end still lands the clamp over the contact bands.
STRAP_STATIONS = (STRAP_W / 2, CRADLE_LEN - STRAP_W / 2)

# ------------------------------------------------------- gland envelope

# ASSUMED, both of them, and both worth ~15 mm of dark run at every corner.
# GLAND_ENV_D is the circle containing the fitted gland seen down the tube axis
# -- across the corners of its hex, or the dome nut, whichever is bigger.
# GLAND_PROUD is how far it stands out past the cap's outer face; it is not the
# gland's overall length, since CAP_T of it is buried in the printed thread.
# Measure both before printing a corner. A nylon M12 is ~17.3 across corners.
GLAND_ENV_D = 24.0
GLAND_PROUD = 30.0

CABLE_OD = 6.7  # LAPP OLFLEX CLASSIC 110, 3x1.5 -- see README
CABLE_BEND_R = 4 * CABLE_OD  # 26.8, fixed installation
SP16_D = 21.0  # inline connector barrel
SP16_LEN = 45.0


def gland_setback(angle: float) -> float:
    """Distance from the vertex to the cap's outer face, for a corner.

    Two glands pointing at a vertex are cylinders whose axes intersect, not
    spheres, so the clearance condition is not "twice the radius":

        a = r_gland / tan(angle / 2)

    at 60 deg that is 20.8 mm, and the cap face follows at ``a + GLAND_PROUD``.
    """
    return GLAND_ENV_D / 2 / tan(radians(angle / 2)) + GLAND_PROUD


def dark_run(angle: float) -> float:
    """Unlit tube at a corner, both sides, in mm.

    The aluminium starts CAP_T behind the cap face -- ``endcap.seated()`` puts
    the flange *outside* the tube -- and forgetting that term is worth 24 mm.
    """
    from .endcap import CAP_T

    return 2 * (gland_setback(angle) + CAP_T)
