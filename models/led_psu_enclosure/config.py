"""Every dimension for the LED PSU enclosure, in one place.

Coordinate system (shared by every part and every mock):

    origin  = centre of the *interior* floor
    +X      = along the PSU's long axis; -X is the terminal-block end
    +Y      = toward the back wall; -Y is the front wall (the connector face)
    z = 0   = inner floor surface

The vertical stack is the thing to keep straight, so it lives here as one
readable ladder rather than scattered magic numbers:

    z=0.0    inner floor
    z=6.0    top of the PSU-plate bosses
    z=10.0   top of the PSU mounting plate      (plate is 4 mm)
    z=40.0   top of the PSU                     (PSU is 30 mm)
    z=63.0   underside of the shelf             <- 23 mm fan plenum
    z=67.0   top of the shelf                   (shelf is 4 mm)
    z=85.0   centre of the SP1712 connector row
    z=103.0  bottom of the thickened rim band
    z=108.7  top of the fuse block              (41.7 mm tall)
    z=118.0  interior ceiling / rim top

Sources for the component numbers are in ``docs/part-data.md``.
"""

from __future__ import annotations

# --- Box shell ---------------------------------------------------------------
INTERIOR_X = 228.0  # PSU is 215 -> 6.5 mm each side
INTERIOR_Y = 128.0  # PSU is 115 -> 6.5 mm each side
INTERIOR_Z = 118.0  # see the stack above

WALL = 3.5  # 4 perimeters at a 0.4 mm nozzle -> watertight-capable
FLOOR = 3.5

CORNER_R = 6.0  # vertical corner fillet (fillets suit vertical walls)
RING_CHAMFER = 0.8  # 45 chamfer on exterior horizontal rings
LEAD_IN = 0.6  # lead-in chamfer at bore mouths
INNER_FILLET = 3.0  # wall-to-floor internal fillet (crack relief)

# --- Sealing rim + snap-in lid -------------------------------------------------
# No outboard flange and no lid screws: the lid's sides sit flush with the
# walls, and a plug skirt drops INTO the mouth to locate and retain it. The
# wall thickens inward over the top RIM_BAND_H so the rim ring (RIM_WALL wide)
# has room for the gasket groove on its top face and the snap groove on its
# inner face. The transition is a 45 taper cut by the cavity loft, not a ledge,
# so it prints without an overhang.
RIM_WALL = 7.0  # wall thickness over the top band (grows inward)
RIM_BAND_H = 15.0  # height of that thickened band

GASKET_CORD = 3.0  # silicone O-ring cord diameter
GASKET_GROOVE_W = 3.8  # groove width  (cord squeezes sideways)
GASKET_GROOVE_D = 2.3  # groove depth  (~23 % compression on a 3 mm cord)
# Groove centred on the rim ring, measured inward from the MOUTH edge. Fair
# warning: one perimeter bead cannot crush a cord the way 14 screws did --
# behind the plug labyrinth this is a dust/splash seal, not an IP65 crush.
GASKET_INSET = RIM_WALL / 2  # centreline, 1.6 mm clear of each ring edge

LID_T = 6.0  # flat lid plate thickness
LID_PLUG_T = 2.0  # plug skirt thickness -- the flexing element of the snap
LID_PLUG_H = 10.0  # how far the skirt reaches into the mouth (band is 15)
LID_PLUG_CLEAR = 0.3  # running clearance between skirt and mouth

# Perimeter snap: a triangular bead on the skirt clicks into a groove in the
# band's inner face. Engagement is deliberately light -- a 221 x 121 ring is
# far stiffer than the round_snap_box hoop, so much more than ~0.3 mm would
# need real force and a pry tool to open.
SNAP_BEAD = 0.6  # bead protrusion; engagement = BEAD - PLUG_CLEAR = 0.3
SNAP_BEAD_H = 2.4  # bead height (triangular: ramps in AND back out)
SNAP_BEAD_Z = 7.0  # bead centre, measured down from the rim top
SNAP_GROOVE_D = 0.6  # groove depth into the band's inner face
SNAP_GROOVE_H = 3.0  # groove height (bead + 0.3 clearance each side)

# --- Heat-set inserts (brass, standard M-series) -----------------------------
# Blind pockets: nothing bores through into the sealed volume.
INSERT_M3_D = 4.2
INSERT_M3_L = 5.8
BOSS_WALL = 2.5  # material around an insert pocket

# --- Mean Well RSP-320-24 ----------------------------------------------------
PSU_X = 215.0
PSU_Y = 115.0
PSU_Z = 30.0
PSU_BOLT_X = 150.0  # bottom-face M4 pattern, centred
PSU_BOLT_Y = 50.0
PSU_BOLT_MAX_DEPTH = 3.0  # !! screws must not enter further than this
PSU_TERMINAL_END = -1  # terminal block + V-ADJ trimmer are at -X
PSU_FAN_D = 50.0  # fan on the TOP cover
PSU_FAN_OFFSET = 47.45  # fan centre, in from the non-terminal end
PSU_HEAT_W = 40.0  # ~40 W dissipated at full load (89 % efficient)

PSU_PLATE_T = 4.0
# Kept small on purpose: the plate has to drop through the rim opening, which is
# narrower than the interior. See installable_x()/installable_y().
# Small on two counts: the plate must drop through the rim opening, and it must
# stay clear of the low vent's inner reinforcing frame at x = +-109.
PSU_PLATE_MARGIN = 0.5
PSU_PLATE_BOSS_H = 6.0  # lifts the plate off the floor
PSU_PLATE_BOSS_D = 11.0

# --- LXD-4P 4-way blade-fuse block -------------------------------------------
FUSE_X = 86.2  # footprint including the mounting ears
FUSE_Y = 53.0
FUSE_Z = 41.7
FUSE_BOLT_PITCH = 76.5  # 2 x O5.2 on the long centre line
FUSE_BOLT_D = 5.2

# --- Athom / IoTorero Ethernet WLED ESP32 controller (measured) --------------
CTRL_X = 102.0
CTRL_Y = 65.0
CTRL_Z = 22.0
CTRL_BOLT_PITCH = 110.0  # 2 x O4 tabs overhanging each end of the long axis
CTRL_BOLT_D = 4.0
CTRL_TAB_X = 118.0  # footprint including the tabs

# --- Shelf -------------------------------------------------------------------
SHELF_T = 4.0
SHELF_TOP_Z = 67.0
SHELF_LEDGE_W = 10.0  # ledge protruding inward from the walls to carry it
SHELF_DROP_CLEAR = 1.5  # clearance each side when dropping it in past the rim
# Anything mounted on the shelf must clear the bodies protruding from the front
# wall, so nothing sits closer than this to it. Set by the deepest intruder --
# the RJ45 coupler at RJ45_BEHIND (32 mm) -- not by the SP1712s (19.7 mm).
SHELF_FRONT_KEEPOUT = 36.0
SHELF_VENT_SLOT_W = 6.0  # slots letting plenum air reach the high vent
SHELF_VENT_SLOT_GAP = 6.0

# --- Weipu SP1712 rear-nut panel socket --------------------------------------
SP17_CUTOUT_D = 17.0
SP17_CUTOUT_FLAT = 15.6  # across the D-flat; oriented UP so it bridges cleanly
SP17_FLANGE_D = 25.0
SP17_BEHIND = 19.7  # body depth behind the panel
SP17_MAX_PANEL = 3.0  # !! hard spec limit
SP17_PANEL_T = 2.8  # what we counterbore the local wall down to
SP17_COUNTERBORE_D = 29.0  # inside pocket giving the rear nut a flat seat
SP17_COUNT = 4
SP17_PITCH = 35.0  # finger room for the mating SP1710 coupling nut
SP17_Z = 85.0

# --- Cable gland + RJ45 bulkhead (front wall, beside the connector row) ------
# NOTE: an M12 gland clamps 7.8 mm max. H05VV-F 3G1.5 is ~9.5 mm OD and will NOT
# fit; only 3G0.75 (~6.8 mm) does. M16 is the safer choice -- hence a parameter.
GLAND_HOLE_D = 12.5  # M12 x 1.5 -> 12.5 mm panel hole
GLAND_PAD_D = 22.0
GLAND_X = -95.0
GLAND_Z = 85.0

RJ45_HOLE_D = 22.0  # IP68 panel-mount RJ45 coupler
RJ45_PAD_D = 30.0
RJ45_BEHIND = 32.0  # needs a notch in the shelf's front edge
RJ45_X = 92.0
RJ45_Z = 85.0

# --- Rain hood over the connector row ----------------------------------------
HOOD_PROJ = 9.0  # how far the ledge overhangs the front wall
HOOD_T = 3.0
HOOD_DROP = 2.0  # drip lip on the outer edge

# --- Vent ports (one low at -X, one high at +X, cross-flow over the PSU) -----
VENT_W = 62.0
VENT_H = 40.0
# Heights are constrained at both ends: the frame must clear the floor below and
# stay under rim_band_z() above, or it would intrude into the rim opening and
# block the shelf from dropping in.
VENT_LOW_Z = 30.0
VENT_HIGH_Z = 74.0
# Frame and recess margins are asymmetric on purpose. They must reach past the
# M3 screws in Y, but stay short in Z or the high port's frame would climb into
# the rim band and block the shelf from dropping in.
VENT_FRAME_MARGIN_Y = 14.0
VENT_FRAME_MARGIN_Z = 8.0
VENT_FRAME_T = 5.0  # how far the frame stands proud of the inner wall face
VENT_RECESS_D = 3.0  # == the cartridge flange thickness, so it sits flush
VENT_RECESS_MARGIN_Y = 14.0
VENT_RECESS_MARGIN_Z = 8.0
VENT_SCREW_OFFSET = 9.0  # M3 screw centres, out from the aperture edge
# Self-tapping M3 into a blind pilot, not a heat-set insert: once the recess is
# cut there is only WALL + VENT_FRAME_T - VENT_RECESS_D = 5.5 mm of material to
# work with, and the frame cannot grow inward because the PSU passes within
# 6.5 mm of the end walls. 4 mm of thread in ASA is ample for a cartridge that
# is also held by two latches.
VENT_SCREW_PILOT_D = 2.5
VENT_SCREW_PILOT_L = 4.0
VENT_CLEAR = 0.35  # cartridge-to-aperture clearance
VENT_LATCH_W = 12.0
VENT_LATCH_H = 8.0
VENT_BEAD = 1.2  # snap bead protrusion on the latch
VENT_FAN_SIZE = 40.0  # optional 40 x 40 x 10 fan cartridge
VENT_FAN_BOLT = 32.0
VENT_LOUVRE_COUNT = 5
VENT_LOUVRE_ANGLE = 45.0


# --- Derived -----------------------------------------------------------------
def outer_x() -> float:
    """Outer width across the walls."""
    return INTERIOR_X + 2 * WALL


def outer_y() -> float:
    """Outer depth across the walls."""
    return INTERIOR_Y + 2 * WALL


def total_h() -> float:
    """Tray height from the bed to the top of the rim."""
    return FLOOR + INTERIOR_Z


def rim_band_z() -> float:
    """Z where the wall thickens inward to RIM_WALL."""
    return INTERIOR_Z - RIM_BAND_H


def installable_x() -> float:
    """Clear opening at the rim -- the real limit on anything fitted inside.

    The rim band narrows the mouth, so a part that fits the *interior* can still
    be impossible to get in. Everything internal is sized against this.
    """
    return INTERIOR_X - 2 * (RIM_WALL - WALL)


def installable_y() -> float:
    """Clear opening at the rim, in Y."""
    return INTERIOR_Y - 2 * (RIM_WALL - WALL)


def shelf_size() -> tuple[float, float]:
    """Shelf plate size: as big as will drop through the rim opening."""
    return (
        installable_x() - 2 * SHELF_DROP_CLEAR,
        installable_y() - 2 * SHELF_DROP_CLEAR,
    )


def psu_plate_size() -> tuple[float, float]:
    """PSU mounting plate size (also limited by the rim opening)."""
    return (PSU_X + 2 * PSU_PLATE_MARGIN, PSU_Y + 2 * PSU_PLATE_MARGIN)


def shelf_ledge_z() -> float:
    """Top surface of the ledge the shelf rests on."""
    return SHELF_TOP_Z - SHELF_T


def psu_bolts() -> list[tuple[float, float]]:
    """The PSU's four M4 bottom-face holes, in box coordinates."""
    return [
        (sx * PSU_BOLT_X / 2, sy * PSU_BOLT_Y / 2) for sx in (-1, 1) for sy in (-1, 1)
    ]


def psu_fan_center_x() -> float:
    """X of the PSU's top-cover fan; the high vent port faces this end."""
    return -PSU_TERMINAL_END * (PSU_X / 2 - PSU_FAN_OFFSET)


def sp17_positions() -> list[float]:
    """X centres of the connector row, centred on the front wall."""
    span = (SP17_COUNT - 1) * SP17_PITCH
    return [-span / 2 + i * SP17_PITCH for i in range(SP17_COUNT)]
