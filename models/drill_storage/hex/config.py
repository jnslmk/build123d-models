"""Measured and derived numbers for the two hex-bit boxes.

The drill family's argument, cut for 1/4" hex-shank bits. Everything the two
boxes share with the drill sets -- the TPU land, the guide fit, the retention
bead, the key rib, the packing budget -- is imported from ``drill_storage.config``
and re-exported here, so there is one copy of each fit and it cannot drift.
What this file owns is what the hex boxes own: the bit sizes, the shortened
heights (30 mm bases, because a bit needs none of the 36 mm a drill does), the
two Gridfinity footprints (1x1 for ALLEN, 2x2 for BITS), and the colours.

The vertical stack, in world z with the base's foot on z=0 (mirroring the
family's ``config.py``)::

    0.0  -  4.4   Gridfinity foot (BASE_H)
    4.4  - 18.0   body -- the ALLEN size legend lives on its walls
   15.0           GUIDE_FLOOR_Z -- bits bottom out here, on the rigid base,
                  never on TPU (which would creep under a point load)
   18.0           BASE_FOOT_TOP, the shoulder the cover seats on
   18.0 - 30.0    collar, with the cover's snap groove at FOOT_TOP + SNAP_Z
   23.2           CAVITY_FLOOR_Z -- the cartridge sits here
   23.2 - 31.2    TPU cartridge (CART_H = 8.0), standing CART_PROUD = 1.2
                  above the base rim so it can be pinched back out
   27.2           cartridge retention bead / base groove (BEAD_Z)
   30.0           BASE_TOTAL_H -- base rim

A bit rests on the guide floor at z=15 and rises through the guide bore (rigid)
and the cartridge's hex land (TPU) into the cover: the ALLEN keys stand 35 mm
proud of the rim, the driver bits 10 mm, which is how you pinch either out.

The base is 30 mm, not the family's 36: the drill set's 36 is for drills that
need 23.2 mm of guide under the collar, and a 25 mm bit standing 10 mm proud
does not. What did *not* move is the collar's 12 mm, which is set by the same
two grooves the family's is (cover snap groove at FOOT_TOP + SNAP_Z, cartridge
bead groove at BEAD_Z) -- they must not thin the same ring of wall.
"""

from __future__ import annotations

from build123d import Color

from .. import config as fam
from ..box import (
    BASE_H,
    CAP_H,
    COLLAR_R,
    COLLAR_W,
    COVER_W,
    COVER_WALL,
    CORNER_R,
    FOOT_C1,
    FOOT_C3,
    FOOT_STRAIGHT,
    GRID,
    INNER_R,
    LABEL_CHAMFER,
    LABEL_DEPTH,
    LABEL_SIZE,
    PAD,
    SLIP,
    SNAP_GROOVE_R,
    SNAP_Z,
    TOLERANCE,
    TOP_FILLET,
    WALL_LABEL_SIZE,
    cover_height_for,
    layout_bores,
)

# --- Re-exports from the family ----------------------------------------------
# The hex boxes are the family's two-material design cut shorter and wider, so
# every fit and every shared dimension is the family's own, re-exported so the
# hex modules read one config (the family's ``config.py`` does the same for
# ``box``). Nothing here is a number the hex boxes get to re-decide.
BEAD_BACK = fam.BEAD_BACK
BEAD_LEAD_IN = fam.BEAD_LEAD_IN
BEAD_TIP_FLAT = fam.BEAD_TIP_FLAT
BORE_FOOT_RELIEF = fam.BORE_FOOT_RELIEF
CART_BEAD = fam.CART_BEAD
CART_BELOW_BEAD = fam.CART_BELOW_BEAD
CART_H = fam.CART_H
CART_MOUTH_CH = fam.CART_MOUTH_CH
CART_PROUD = fam.CART_PROUD
CART_R = fam.CART_R
CART_SLIP = fam.CART_SLIP
CART_WALL = fam.CART_WALL
CAVITY_MOUTH_CH = fam.CAVITY_MOUTH_CH
CAVITY_R = fam.CAVITY_R
EFFECTIVE_LAND_H = fam.EFFECTIVE_LAND_H
GUIDE_FIT = fam.GUIDE_FIT
GUIDE_MOUTH_CH = fam.GUIDE_MOUTH_CH
HEX_LAND_FIT = fam.HEX_LAND_FIT
KEY_D = fam.KEY_D
KEY_FILLET = fam.KEY_FILLET
KEY_LEAD_IN = fam.KEY_LEAD_IN
KEY_ROOT = fam.KEY_ROOT
KEY_SLIP = fam.KEY_SLIP
KEY_W = fam.KEY_W
LAND_H = fam.LAND_H
LAND_LEAD_IN = fam.LAND_LEAD_IN
PACK_CORNER_R = fam.PACK_CORNER_R
PACK_HALF_W = fam.PACK_HALF_W
PACK_HOLE_WALL = fam.PACK_HOLE_WALL
PACK_WALL_CLEARANCE = fam.PACK_WALL_CLEARANCE
RELIEF_FIT = fam.RELIEF_FIT
SHELL_GROOVE_R = fam.SHELL_GROOVE_R
SHELL_TOP_CHAMFER = fam.SHELL_TOP_CHAMFER
SHELL_WALL = fam.SHELL_WALL

# --- The bits ----------------------------------------------------------------
# 1/4" hex shank. Nothing here is compliant, so the fit lives entirely in this
# across-flats clearance: enough that a bit drops in and lifts out one-handed,
# not so much that it rattles. (The grip is the TPU land's job, exactly like a
# drill shank; the clearance only has to let the shank through.)
HEX_SHANK_AF = 6.35  # nominal 1/4" across-flats
# Diametral allowance (added straight across the flats, like a bore-diameter
# formula -- not doubled, so it's already the total gap). Sits between
# fits.SNUG (0.10 mm, PETG baseline) and fits.SLIDING (0.22 mm, PETG
# baseline), closer to SNUG. Deliberately tighter than a round SLIDING bore
# would need: a hex socket's flat sides don't suffer the concave-arc
# undersizing a round bore does (fdm-fits-and-clearances Rule 4 -- the nozzle
# dragging the inner perimeter inward is an arc effect), so less allowance
# still drops a bit in and lifts it out one-handed without rattling.
HEX_CLEARANCE = 0.15  # across-flats allowance -> slip fit
HEX_AF = HEX_SHANK_AF + HEX_CLEARANCE  # 6.5

# The circumradius a socket really occupies in the cartridge -- what you pack is
# what you cut. ``insert.hex_bore_tool`` cuts a relief at ``(af + RELIEF_FIT) /
# sqrt(3)`` (the land below is narrower), so the packer reserves that radius and
# not the bare across-flats one: ``sets.py`` reserves its hex tools the same way,
# at ``(af + RELIEF_FIT) / sqrt(3)``, against what ``insert.py`` cuts.
HEX_SOCKET_R = (HEX_AF + fam.RELIEF_FIT) / 3**0.5

# Metric hex-key sizes in the 50 mm set, largest first -- the packer deals them
# into rows in this order, so the biggest land in the back row like the drill
# variants. The 25 mm driver bits are a mixed bag (Torx/PH/PZ/slotted) with no
# common scale, so that box carries no legend.
ALLEN_SIZES = [8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5]
ALLEN_BIT_LEN = 50.0
BITS_BIT_LEN = 25.0

# Pick each cover on the true minimum Gridfinity unit (see ``drill_storage.wood``):
# ask only for a tip clearance rather than the generic headroom, so the 7 mm
# quantisation isn't pushed up a whole unit by slack it doesn't need.
COVER_TIP_CLEARANCE = 1.0

# --- Heights -----------------------------------------------------------------
# The base is 30 mm (the family's 36 is for drills that need the depth). That is
# as low as this base goes while keeping everything it needs:
#   * the ALLEN legend band on the body wall -- the binding constraint, exactly
#     as it was on the old one-material base: three rows of the house minimum
#     glyph height need the wall from the foot to FOOT_TOP = 18;
#   * a collar whose snap groove (SNAP_Z = 6 above the shoulder) has the same
#     separation from the cartridge's bead groove the family's collar has --
#     COLLAR_H = 12 reproduces the family's 3.2 mm GROOVE_SEPARATION exactly;
#   * the cartridge features: the cavity and the proud lip above the rim.
BASE_FOOT_TOP = 18.0  # shoulder the cover seats on
BASE_COLLAR_H = 12.0  # set by the two grooves, like SHELL_COLLAR_H
BASE_TOTAL_H = BASE_FOOT_TOP + BASE_COLLAR_H  # 30.0
# The cartridge is the family's own (CART_H = 8.0, standing CART_PROUD = 1.2
# above the rim), so the cavity floor and the bead drop out of its geometry.
CAVITY_FLOOR_Z = BASE_TOTAL_H - (fam.CART_H - fam.CART_PROUD)  # 23.2
BEAD_Z = CAVITY_FLOOR_Z + fam.CART_BELOW_BEAD  # 27.2
# Bits rest on the rigid floor, 15 mm up the body. The floor is as high as it
# can be while a 25 mm driver bit still stands 10 mm proud of the rim (the same
# proud heights the old one-material box documented), which is what makes the
# guide short enough to leave the collar wall alone. Under the floor: 10.6 mm of
# solid body, so the bores stop well above the foot.
GUIDE_FLOOR_Z = 15.0
GUIDE_H = CAVITY_FLOOR_Z - GUIDE_FLOOR_Z  # 8.2 of rigid guide under the collar
CAVITY_H = BASE_TOTAL_H - CAVITY_FLOOR_Z  # 6.8, the family's own
# The two grooves cut into opposite faces of the same ring of collar wall, so
# they must not overlap in z. Same 3.2 mm the family keeps.
GROOVE_SEPARATION = BEAD_Z - (BASE_FOOT_TOP + SNAP_Z)

# --- The ALLEN wall legend ----------------------------------------------------
# Re-fitted to the shortened body exactly as the old one-material base fitted
# it: centred on the wall (BASE_H..BASE_FOOT_TOP) and pitched just far enough
# apart that three rows fit between the foot and the shoulder.
LEGEND_MARGIN = 0.6  # clear space kept above/below the block of rows
LEGEND_ROWS = 3
LEGEND_GLYPH_H = 0.75 * WALL_LABEL_SIZE  # build123d renders digits at ~0.75 * size
LEGEND_Z = (BASE_H + BASE_FOOT_TOP) / 2
LEGEND_LINE_H = ((BASE_FOOT_TOP - BASE_H - 2 * LEGEND_MARGIN) - LEGEND_GLYPH_H) / (
    LEGEND_ROWS - 1
)

MARGIN = 0.9  # fraction of a face a label may span, so it never runs to the edge

# --- Footprints ---------------------------------------------------------------
# Two Gridfinity sizes: the ALLEN box keeps the family's 1x1, the BITS box grows
# to 2x2 because 16 sockets cannot meet the cartridge's clearances on one 1x1
# collar -- a 4x4 grid needs an 8.98 mm pitch to keep its neighbours at
# PACK_HOLE_WALL, and the 1x1 cartridge's wall leaves only 8.27 mm of pitch
# (PACK_WALL_CLEARANCE at the outer sockets), so no pitch satisfies both.
# Everything below the cavity floor is shared between the two boxes; only these
# horizontal envelopes differ. The corner radii (collar, cavity, cartridge) are
# the family's for both -- a bigger pad lengthens the straight edges, it does
# not change the corner profile.
ALLEN_PAD = PAD  # 41.5
ALLEN_COVER_W = COVER_W  # 42.0, the family's cover
ALLEN_COLLAR_W = COLLAR_W  # 39.2
ALLEN_CAVITY_W = fam.CAVITY_W  # 36.0
ALLEN_CART_W = fam.CART_W  # 35.68

BITS_PAD = 2 * GRID - TOLERANCE  # 83.5, a 2x2 Gridfinity pad
BITS_COVER_W = BITS_PAD + 1.0  # 84.5 -- family rule: cover = pad + 1.0
BITS_INNER_W = BITS_COVER_W - 2 * COVER_WALL  # 82.1 cover bore
BITS_COLLAR_W = BITS_INNER_W - SLIP  # 81.7, close slip fit in the bore
BITS_CAVITY_W = BITS_COLLAR_W - 2 * fam.SHELL_WALL  # 78.5
BITS_CART_W = BITS_CAVITY_W - fam.CART_SLIP  # 78.18

# The BITS sockets are dealt in a literal 4x4 square grid, never pack_rows --
# a packer deals 16 identical items as ragged rows (3+3+3+3+3+1), and the grid
# is the point. The pitch spreads the grid to the cartridge envelope exactly
# like pack_rows spreads a row: the outermost sockets land on
# PACK_WALL_CLEARANCE of wall. The corner sockets face the *flat* edge -- a
# rounded square's corner arc only intrudes beyond its tangent points, and at
# this pitch the holes sit clear of the arcs by ~2.6 mm -- so the flat edge is
# the binding constraint, and every neighbour gap comes out an order of
# magnitude over PACK_HOLE_WALL.
BITS_GRID = 4  # 4x4
BITS_PITCH = (BITS_CART_W / 2 - HEX_SOCKET_R - PACK_WALL_CLEARANCE) / (
    (BITS_GRID - 1) / 2
)

# --- Colours ------------------------------------------------------------------
# Base and insert both black (``wall_bar_lamp.BLACK`` precedent); covers
# translucent so the bits read through them (``tools.COVER_GLASS`` precedent).
BASE_COLOR = Color(0.1, 0.1, 0.1)
INSERT_COLOR = Color(0.1, 0.1, 0.1)
COVER_COLOR = Color(0.86, 0.87, 0.84, 0.32)

# --- Derived helpers ----------------------------------------------------------
# What the family solves in ``sets.DrillSet.__post_init__``, in miniature: one
# cover height per box, and the socket layout each box's parts are all cut from.
# Only one call to ``layout_bores`` ever decides where a hole is, so the base's
# guides and the cartridge's lands cannot disagree about it.


def cover_h_for(bit_len: float) -> float:
    """The cover for a bit length, quantised to a whole Gridfinity unit."""
    return cover_height_for(
        bit_len,
        headroom=COVER_TIP_CLEARANCE,
        bore_floor_z=GUIDE_FLOOR_Z,
        foot_top=BASE_FOOT_TOP,
    )


def socket_layout(
    name: str,
) -> tuple[
    list[tuple[float, float, float]],
    list[list[str]] | None,
    dict[str, tuple[float, float]] | None,
]:
    """The hex sockets for one box: ``(hex_bores, rows, pos)``.

    ALLEN: eight sockets packed by the family packer into the cartridge
    envelope (``sets.py``'s envelope), keyed by the sizes so ``rows``/``pos``
    engrave the wall legend. BITS: sixteen sockets in the literal 4x4 grid at
    ``BITS_PITCH``; no rows and no positions map, because there is no legend.
    """
    if name == "allen":
        keys = [f"{s:g}" for s in ALLEN_SIZES]
        _, hex_bores, rows, pos = layout_bores(
            [],
            hex_tools=[(k, HEX_AF, HEX_SOCKET_R) for k in keys],
            half_w=fam.PACK_HALF_W,
            corner_r=fam.PACK_CORNER_R,
            hole_wall=fam.PACK_HOLE_WALL,
            wall_clearance=fam.PACK_WALL_CLEARANCE,
        )
        return hex_bores, rows, pos
    half = (BITS_GRID - 1) / 2
    positions = [(i - half) * BITS_PITCH for i in range(BITS_GRID)]
    hex_bores = [(HEX_AF, x, y) for y in positions for x in positions]
    return hex_bores, None, None


__all__ = [
    "ALLEN_BIT_LEN",
    "ALLEN_CART_W",
    "ALLEN_CAVITY_W",
    "ALLEN_COLLAR_W",
    "ALLEN_COVER_W",
    "ALLEN_PAD",
    "ALLEN_SIZES",
    "BASE_COLLAR_H",
    "BASE_COLOR",
    "BASE_FOOT_TOP",
    "BASE_TOTAL_H",
    "BEAD_Z",
    "BITS_BIT_LEN",
    "BITS_CART_W",
    "BITS_CAVITY_W",
    "BITS_COLLAR_W",
    "BITS_COVER_W",
    "BITS_GRID",
    "BITS_INNER_W",
    "BITS_PAD",
    "BITS_PITCH",
    "CAVITY_FLOOR_Z",
    "CAVITY_H",
    "COVER_COLOR",
    "COVER_TIP_CLEARANCE",
    "GROOVE_SEPARATION",
    "GUIDE_FLOOR_Z",
    "GUIDE_H",
    "HEX_AF",
    "HEX_CLEARANCE",
    "HEX_SHANK_AF",
    "HEX_SOCKET_R",
    "INSERT_COLOR",
    "LEGEND_GLYPH_H",
    "LEGEND_LINE_H",
    "LEGEND_MARGIN",
    "LEGEND_ROWS",
    "LEGEND_Z",
    "MARGIN",
    "cover_h_for",
    "socket_layout",
    # re-exported from ``box`` so the hex modules read one config
    "BASE_H",
    "CAP_H",
    "COLLAR_R",
    "COLLAR_W",
    "COVER_W",
    "COVER_WALL",
    "CORNER_R",
    "FOOT_C1",
    "FOOT_C3",
    "FOOT_STRAIGHT",
    "GRID",
    "INNER_R",
    "LABEL_CHAMFER",
    "LABEL_DEPTH",
    "LABEL_SIZE",
    "PAD",
    "SLIP",
    "SNAP_GROOVE_R",
    "SNAP_Z",
    "TOLERANCE",
    "TOP_FILLET",
    "WALL_LABEL_SIZE",
    "cover_height_for",
    "layout_bores",
    # re-exported from the family so the hex modules read one config
    "BEAD_BACK",
    "BEAD_LEAD_IN",
    "BEAD_TIP_FLAT",
    "BORE_FOOT_RELIEF",
    "CART_BEAD",
    "CART_BELOW_BEAD",
    "CART_H",
    "CART_MOUTH_CH",
    "CART_PROUD",
    "CART_R",
    "CART_SLIP",
    "CART_WALL",
    "CAVITY_MOUTH_CH",
    "CAVITY_R",
    "EFFECTIVE_LAND_H",
    "GUIDE_FIT",
    "GUIDE_MOUTH_CH",
    "HEX_LAND_FIT",
    "KEY_D",
    "KEY_FILLET",
    "KEY_LEAD_IN",
    "KEY_ROOT",
    "KEY_SLIP",
    "KEY_W",
    "LAND_H",
    "LAND_LEAD_IN",
    "PACK_CORNER_R",
    "PACK_HALF_W",
    "PACK_HOLE_WALL",
    "PACK_WALL_CLEARANCE",
    "RELIEF_FIT",
    "SHELL_GROOVE_R",
    "SHELL_TOP_CHAMFER",
    "SHELL_WALL",
]
