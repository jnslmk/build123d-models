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
which is how the vertical stack was pinned down. Values marked ASSUMED are
reconstructions neither pinned down -- plausible, but check them before a
printed part depends on one.
"""

from __future__ import annotations

# ---------------------------------------------------------------- outer shape

# MEASURED. Not an ellipse: two R13 half-circles joined by straight flanks, so
# the outline is a stadium/obround standing on end. The straight section is
# exactly HEIGHT - WIDTH tall.
WIDTH = 26.0
HEIGHT = 30.0
WALL = 0.5  # MEASURED -- thin, as extruded tube profiles go

RADIUS = WIDTH / 2  # 13.0, both the top and the bottom half-circle
STRAIGHT_H = HEIGHT - WIDTH  # 4.0 of vertical flank between the two arcs
BOT_ARC_Z = RADIUS  # 13.0, centre height of the lower half-circle
TOP_ARC_Z = HEIGHT - RADIUS  # 17.0, centre height of the upper half-circle

# ------------------------------------------------------------------- the rim

# DIALLED. Where the aluminium stops and the diffuser takes over. It lands just
# below TOP_ARC_Z, i.e. inside the straight band where the section is at its
# full 26 mm -- which is exactly why the diffuser measures 26 mm across.
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
BOSS_OD = 3.3  # ASSUMED

# DIALLED. The bosses straddle the shelf, hanging down into the wiring cavity --
# which is why the bores read as sitting below the divider in the photo.
SCREW_BOSS_Z = 14.7

# -------------------------------------------------------------- diffuser

# MEASURED: 26 mm across the outside, 25 mm across the inside just above the
# rim, and 1.0 mm of wall. Those three do not describe a constant-thickness
# shell, so the inner face is a separate circle -- thinner at the rim than at
# the crown, which is how the part actually measures.
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
