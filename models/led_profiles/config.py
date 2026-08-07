"""Measured dimensions of the aluminium T8 profile the lamp system is built on.

One source of truth for the extrusion. Every printed part in this package
(endcaps, PCB mount, mounting hardware) derives from these numbers rather than
re-measuring, so a corrected measurement propagates everywhere at once.

Coordinate convention for the cross-section, shared by every module here:

* ``u`` -- across the width, 0 on the centre line, +/- ``WIDTH / 2`` at the flanks
* ``z`` -- up from the *bottom* of the profile, so ``z = 0`` is the lowest point
  and ``z = HEIGHT`` the apex. The LED channel opens at the top.

The profile is modelled lying along +X in its use pose, LED facing up.

Values marked MEASURED came off the real extrusion with calipers. Values marked
DIALLED were set by matching a to-scale cross-section against the part in hand,
which is how the vertical stack was pinned down. Values marked DRAWN come off
``docs/assets/profile-dimensions.jpg``, a 1:1 pencil outline of the extrusion,
the diffuser and the assembled tube on 5 mm graph paper -- read back against the
grid, so good to roughly +/-0.2 mm and no better. Values marked ASSUMED are
reconstructions neither pinned down -- plausible, but check them before a
printed part depends on one.

What the 1:1 drawing says that this file deliberately does **not** follow, so a
future re-measurement knows it is disagreeing on purpose rather than by
oversight:

* the strip slot scales off the drawing at ~8.0 x 2.1 mm, against the 10 x 1.3
  a caliper gave. The caliper wins: a slot is two crisp inside faces to measure
  and the hardest thing on the sheet to trace freehand.
* the aluminium's outer wall runs up to z ~= 19.4 and rolls inward into the
  two snap hooks that catch the diffuser. That roll is still not modelled (see
  the diffuser block below); ``RIM_Z`` remains the shoulder the recess floor
  steps up to, which the drawing puts at 16.6 against this file's 16.8.
* the drawing shows no screw ports at all -- the corner curls are the rim roll,
  not a bore -- so ``SCREW_SPACING`` and ``SCREW_BOSS_Z`` stay as measured.
"""

from __future__ import annotations

from math import hypot

# ---------------------------------------------------------------- outer shape

# Not an ellipse: two half-circles joined by straight flanks, so the outline is
# a stadium/obround standing on end. The straight section is exactly
# HEIGHT - WIDTH tall.
#
# DRAWN, and the width corrected against hardware. The assembled outline on the
# 1:1 sheet reads 26.30 x 30.72 at the pencil's centreline; a traced outline
# runs wide by about half a pencil per side, and the printed endcap measured
# 0.55 mm proud of the extrusion per side at a collar of 0.6 -- which puts the
# real tube at 26.1. Scaling the sheet's own aspect ratio onto that gives 30.5.
WIDTH = 26.1
HEIGHT = 30.5
WALL = 0.5  # MEASURED -- thin, as extruded tube profiles go

RADIUS = WIDTH / 2  # 13.05, both the top and the bottom half-circle
STRAIGHT_H = HEIGHT - WIDTH  # 4.4 of vertical flank between the two arcs
BOT_ARC_Z = RADIUS  # 13.05, centre height of the lower half-circle
TOP_ARC_Z = HEIGHT - RADIUS  # 17.45, centre height of the upper half-circle

# ------------------------------------------------------------------- the rim

# DIALLED. Where the aluminium stops and the diffuser takes over. It lands just
# below TOP_ARC_Z, i.e. inside the straight band where the section is at its
# full WIDTH -- which is exactly why the diffuser measures WIDTH across.
RIM_Z = 16.8

# ------------------------------------------------------------- LED channel

# The channel is two steps, not one: a wide shallow recess in the top of the
# shelf, with a narrower deeper slot inside it that locates the strip.
CHANNEL_W = 19.0  # DIALLED, width of the shallow recess
STRIP_SLOT_W = 10.0  # MEASURED
STRIP_SLOT_H = 1.3  # MEASURED
STRIP_FLOOR_Z = 14.1  # DIALLED, the surface the strip is stuck to

# Derived: the shallow recess is whatever is left between the slot and the rim.
RECESS_H = RIM_Z - STRIP_FLOOR_Z - STRIP_SLOT_H  # 1.4

CHANNEL_WALL = 0.5  # ASSUMED, the webs flanking the recess
FLOOR_T = 1.0  # ASSUMED, the web under the strip slot
CAVITY_TOP_Z = STRIP_FLOOR_Z - FLOOR_T  # 13.1 -- ceiling of the wiring cavity

# --------------------------------------------------------- endcap screw ports

# MEASURED spacing and screw size: two lengthwise ports in the shelf corners,
# 22 mm apart, taking 2 mm self-tappers driven in from the end face. These are
# what an endcap screws to.
SCREW_SPACING = 22.0
SCREW_D = 2.0
SCREW_PILOT_D = 1.7  # self-tapper pilot in aluminium

# DIALLED. The bosses straddle the shelf, hanging down into the wiring cavity --
# which is why the bores read as sitting below the divider in the photo.
SCREW_BOSS_Z = 14.7

# ASSUMED at 3.3, with a floor under it that is *not* assumed: the boss is
# formed **in** the shell wall, so its circle has to reach past that wall at the
# corner pocket's own floor rather than stop a hair short of it.
#
# Not fussiness -- this is the difference between a clean solid and a degenerate
# one. At 3.3 against a 26.0 mm tube the circle crossed the wall 0.09 mm *below*
# the pocket floor and the two merged. Correcting the tube to 26.1 moved the wall
# out by 0.05 and the crossing to 0.034 mm *above* the floor, which left a wedge
# of pocket 0.034 mm tall and 0.013 mm wide hugging the wall: a 13-micron sliver
# face running the whole 1.5 m of extrusion. That is not a feature, and it is not
# harmless -- it stopped the aluminium's own end caps being the two smallest
# faces on the solid, which is the assumption ``checks._end_face_points`` reads
# the triangle's closure through, and the dark-run check duly reported 890 mm of
# unlit tube against 86 predicted.
#
# So the floor is derived from the geometry it has to clear, with a margin that
# is an actual merge rather than the 0.024 mm it happened to be short by.
BOSS_WALL_MERGE = 0.2
BOSS_OD = max(
    3.3,
    2 * hypot(WIDTH / 2 - WALL - SCREW_SPACING / 2, SCREW_BOSS_Z - STRIP_FLOOR_Z)
    + BOSS_WALL_MERGE,
)  # 3.52

# -------------------------------------------------------------- diffuser

# MEASURED: WIDTH across the outside, 25 mm across the inside just above the
# rim, and 1.0 mm of wall. Those three do not describe a constant-thickness
# shell, so the inner face is a separate circle -- thinner at the rim than at
# the crown, which is how the part actually measures. (The 1:1 drawing reads
# 1.4 mm at the crown, but it traces a translucent 1 mm wall in pencil, which
# is exactly the measurement a caliper is better at than a pencil.)
DIFFUSER_T = 1.0  # at the crown
DIFFUSER_INNER_W = 25.0  # at the rim


def _inner_arc() -> tuple[float, float]:
    """Centre height and radius of the diffuser's inner face.

    Solved from the two measurements: it passes through +/-12.5 at ``RIM_Z``
    and leaves ``DIFFUSER_T`` at the apex.
    """
    half = DIFFUSER_INNER_W / 2
    z_in = HEIGHT - DIFFUSER_T
    centre = (z_in**2 - RIM_Z**2 - half**2) / (2 * (z_in - RIM_Z))
    return centre, z_in - centre


DIFFUSER_INNER_Z, DIFFUSER_INNER_R = _inner_arc()  # ~16.50, ~12.50

# The snap detail at the rim (the little hooks visible in the photo) is
# deliberately not modelled: the diffuser is a bought part, no printed part
# touches the hooks, and inventing them would clash with the screw bosses that
# fill the same corner. What matters here is the envelope and the seat height.

# ------------------------------------------------------------------ strip

# 24 V WS2811 dual-IC COB, 960 LED/m RGBCCT -- see README.md. 10 mm wide to fill
# the slot; the emitting phosphor band is narrower than the carrier.
STRIP_W = STRIP_SLOT_W - 0.2  # slip into the slot
STRIP_T = 1.0
STRIP_EMITTER_W = 8.0
STRIP_EMITTER_T = 0.4

# ------------------------------------------------------------------ length

LENGTH = 1500.0  # a full 1.5 m stick
SECTION_LENGTH = 60.0  # short slice, for looking at the cross-section
