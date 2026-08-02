"""Every dimension for the LED PSU enclosure, in one place.

Coordinate system (shared by every part and every mock):

    origin  = centre of the *interior* floor
    +X      = along the PSU's long axis; -X is the terminal-block end
    +Y      = toward the back wall; -Y is the front wall (the connector face)
    z = 0   = inner floor surface

The vertical stack is the thing to keep straight, so it is **derived** here
rather than written down as magic numbers -- every height below follows from a
component dimension or a stated clearance, and ``interior_z()`` is whichever of
the three competing chains ends up tallest:

    z=0.0    inner floor
    z=5.0    top of the PSU-plate bosses        (snap-stud spring length)
    z=9.0    top of the PSU mounting plate      (plate is 4 mm)
    z=39.0   top of the PSU                     (PSU is 30 mm)
    z=47.0   bottom of the high vent port, and of the internal fan
    z=52.0   underside of the shelf             <- 13 mm fan plenum
    z=56.0   top of the shelf                   (shelf is 4 mm)
    z=74.0   centre of the SP1712 connector row
    z=87.0   top of the high vent port, and of the internal fan
    z=96.0   bottom of the thickened rim band
    z=97.7   top of the fuse block              (41.7 mm tall)
    z=108.0  interior ceiling / rim top

Sources for the component numbers are in ``docs/part-data.md``.
"""

from __future__ import annotations

import math

# --- Box shell ---------------------------------------------------------------
# X is locked by the PSU plus the vent frames: 215 + 2 x (VENT_FRAME_T + 1.5).
# Y only has to clear the PSU and pass the PSU plate through the rim opening.
# Z is derived -- see interior_z() at the bottom of this file.
INTERIOR_X = 228.0  # PSU is 215 -> 6.5 mm each side, 5 of which is the vent frame
INTERIOR_Y = 125.0  # PSU is 115 -> 5.0 mm each side

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
# Only has to swallow LID_PLUG_H plus a little, and every millimetre of band is a
# millimetre the high vent port's frame has to stay below (see interior_z()), so
# it is kept as short as the plug allows rather than round.
RIM_BAND_H = 12.0  # height of that thickened band

GASKET_CORD = 3.0  # silicone O-ring cord diameter
GASKET_GROOVE_W = 3.8  # groove width  (cord squeezes sideways)
GASKET_GROOVE_D = 2.3  # groove depth  (~23 % compression on a 3 mm cord)
# Groove centred on the rim ring, measured inward from the MOUTH edge. Fair
# warning: one perimeter bead cannot crush a cord the way 14 screws did --
# behind the plug labyrinth this is a dust/splash seal, not an IP65 crush.
GASKET_INSET = RIM_WALL / 2  # centreline, 1.6 mm clear of each ring edge

LID_T = 6.0  # flat lid plate thickness
LID_PLUG_T = 2.0  # plug skirt thickness -- the flexing element of the snap
LID_PLUG_H = 10.0  # how far the skirt reaches into the mouth (band is RIM_BAND_H)
# Per-side gap between the skirt (lid.py's SKIRT_X/Y) and the mouth it drops
# into -- diametral equivalent is 0.6 mm (lid.py applies it as
# installable_x/y() - 2 * LID_PLUG_CLEAR). Looser than fits.FREE (0.40 mm
# diametral, PETG baseline), the nearest class. Deliberate, not an error, and
# the same reasoning as round_snap_box.py's CLEARANCE (identical 0.6 mm
# diametral): the skirt spans ~221 x 121 mm, well past the scaling rule's
# +0.05 mm/100 mm threshold, and centring/retention is SNAP_BEAD's job, not
# this gap's -- it only has to clear the mouth without binding while the bead
# rides its ramp into the groove.
LID_PLUG_CLEAR = 0.3  # running clearance between skirt and mouth, per side

# Perimeter snap: a triangular bead on the skirt clicks into a groove in the
# band's inner face. Engagement is deliberately light -- a 221 x 121 ring is
# far stiffer than the round_snap_box hoop, so much more than ~0.3 mm would
# need real force and a pry tool to open.
SNAP_BEAD = 0.6  # bead protrusion; engagement = BEAD - PLUG_CLEAR = 0.3
SNAP_BEAD_H = 2.4  # bead height (triangular: ramps in AND back out)
SNAP_BEAD_Z = 7.0  # bead centre, measured down from the rim top
SNAP_GROOVE_D = 0.6  # groove depth into the band's inner face
SNAP_GROOVE_H = 3.0  # groove height (bead + 0.3 clearance each side)

# --- PSU plate snap studs (no inserts, no screws -- none could be reached) ----
# The PSU bolts to its plate from BELOW the plate, so that joint can only be
# made on the bench -- and once it is, the PSU covers every boss position, so
# no driver can reach a plate-to-tray screw either. The plate+PSU drops in as
# one assembly and snaps onto four hollow split studs: a 1 mm walled tube cut
# into two C-springs by a slot, with a 45 head that detents into the plate.
# Ramps run both ways, so it clicks in on a press and releases on a hard pull.
STUD_HOLE_D = 7.0  # plate through-hole
STUD_TUBE_D = 6.7  # snap tube OD
STUD_BORE_D = 4.7  # tube ID -> 1.0 mm spring wall
STUD_SLOT_W = 1.0  # slot splitting tube + head into two halves
STUD_HEAD_D = 8.0  # catch = (HEAD - HOLE) / 2 = 0.5 mm per side
STUD_RECESS_D = 10.0  # pocket in the plate top hiding the head under the PSU
STUD_RECESS_DEPTH = 2.2
STUD_RING_ID = 8.5  # seat ring ID -- the gap the tube flexes into

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
# NOT dead air: this is the snap studs' spring length. The C-spring tube runs
# from the base block at z = 1 up to the head, so shortening the boss shortens
# the cantilever and the strain goes as 1/L^2 -- at 5 mm the stud snap works out
# at ~2.0 % strain, and checks.py fails the build below 4.5 mm. Do not trim this
# to save box height without re-reading check_plate_studs().
PSU_PLATE_BOSS_H = 5.0  # lifts the plate off the floor (seat ring top)
PSU_PLATE_BOSS_D = 11.0  # seat ring OD around each snap stud

# --- LXD-4P 4-way blade-fuse block -------------------------------------------
FUSE_X = 86.2  # footprint including the mounting ears
FUSE_Y = 53.0
FUSE_Z = 41.7
FUSE_BOLT_PITCH = 76.5  # 2 x O5.2 on the long centre line
FUSE_BOLT_D = 5.2
# Clear air the fuse block's cover needs above it. The block is the tallest thing
# in the box and one of the three chains that set interior_z(); the old box gave
# it 9.3 mm, which is not enough to get a finger to an ATO fuse -- you had to
# lift the whole wired shelf out to change one. 10 mm plus whatever the vent
# chain wins gets that back.
FUSE_HEADROOM = 10.0

# --- Athom / IoTorero Ethernet WLED ESP32 controller (measured) --------------
CTRL_X = 102.0
CTRL_Y = 65.0
CTRL_Z = 22.0
CTRL_BOLT_PITCH = 110.0  # 2 x O4 tabs overhanging each end of the long axis
CTRL_BOLT_D = 4.0
CTRL_TAB_X = 118.0  # footprint including the tabs

# --- Shelf -------------------------------------------------------------------
SHELF_T = 4.0
# Gap between the PSU's top cover and the shelf's underside. The RSP-320's
# O50 top-cover fan wants roughly 0.25 x D of unobstructed space to breathe, so
# this is a floor, not a preference -- and it is the single cheapest millimetre
# of box height there is, which is exactly why it is a named parameter and not
# a hard-coded shelf Z. SHELF_TOP_Z is derived from it; see shelf_ledge_z().
PLENUM_H = 13.0
SHELF_LEDGE_W = 10.0  # ledge protruding inward from the walls to carry it
# Not a fits.py class: this is per-side hand clearance to drop a ~221 x 121 mm
# plate past the rim opening (shelf_size() = installable_x/y() - 2 * this), not
# a located fit -- the ledge (SHELF_LEDGE_W) does the locating once the shelf
# is resting on it. Sized generously on purpose: the shelf is the single
# largest printed dimension in the box, dropping through the single narrowest
# opening in the box (the rim mouth, not the interior).
SHELF_DROP_CLEAR = 1.5  # per-side clearance when dropping it in past the rim; not a fit
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
# The whole row (SP1712s, gland, RJ45) shares one height. Bounded below by the
# shelf -- the RJ45's O30 pad must clear the shelf plate, which its body would
# otherwise pass straight through -- and above by rim_band_z() less half the
# O29 counterbore. check_connector_row() enforces both, so move it and the
# build tells you if you went too far either way.
SP17_Z = 74.0

# --- Cable gland + RJ45 bulkhead (front wall, beside the connector row) ------
# NOTE: an M12 gland clamps 7.8 mm max. H05VV-F 3G1.5 is ~9.5 mm OD and will NOT
# fit; only 3G0.75 (~6.8 mm) does. M16 is the safer choice -- hence a parameter.
GLAND_HOLE_D = 12.5  # M12 x 1.5 -> 12.5 mm panel hole
GLAND_PAD_D = 22.0
GLAND_X = -95.0
GLAND_Z = SP17_Z

RJ45_HOLE_D = 22.0  # IP68 panel-mount RJ45 coupler
RJ45_PAD_D = 30.0
RJ45_BEHIND = 32.0  # needs a notch in the shelf's front edge
# Pulled inboard off the corner: at 92 the coupler's body ran into the internal
# fan's yoke plate, which reaches y = +-44 at the same end of the box. It still
# has to clear the outermost SP1712's rear nut on the other side, so there is
# only a couple of millimetres of freedom either way -- check_internal_fan() and
# check_interference() hold both ends of it.
RJ45_X = 82.0
RJ45_Z = SP17_Z

# --- Vent ports (one low at -X, one high at +X, cross-flow over the PSU) -----
VENT_W = 62.0
# Sized to the internal fan, so a 40 mm fan drops straight into the aperture and
# blows through the louvre rather than replacing it. Changing VENT_FAN_SIZE
# resizes the port and re-derives the box height with it.
VENT_H = 40.0
# The low port sits at PSU height, feeding the PSU's own case louvres at the
# terminal end; the high port sits above the PSU at the top-cover fan end. The
# 30 mm difference is worth ~2 W of buoyancy (see docs/design-notes.md) -- what
# earns its keep is the two ports being at opposite *ends*, so a fan-driven flow
# sweeps the PSU's whole length. Bounded below by the floor (the frame reaches
# VENT_FRAME_MARGIN_Z past the aperture) and above by rim_band_z(); the high
# port's height is derived from the fan, see vent_high_z().
VENT_LOW_Z = 30.0
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
# Per-side gap between the optional cartridge's plug body (vent.py's
# PLUG_X/Y) and the VENT_W x VENT_H aperture it passes through -- diametral
# equivalent is 0.70 mm. Still live: only vent_blank/vent_fan use PLUG_X/Y
# (vent_shutter's panel is sized off FLANGE_X/Y instead), so this stays in use
# even though the sliding shutter, not a cartridge, is now the default fit --
# see VENT_SLIDER_CLEAR below for that one, a different mating pair on a
# different part. Looser than fits.FREE (0.40 mm diametral, PETG baseline),
# the nearest class: the plug is fitted once and retained by latches, not
# located precisely, over a 62 x 40 mm span past the scaling rule's
# +0.05 mm/100 mm threshold -- it only has to clear the aperture without
# binding while the latch hooks flex past the frame on the way in.
VENT_CLEAR = 0.35  # cartridge-to-aperture clearance, per side

# --- Internal 24 V exhaust fan (the high port only) ---------------------------
# Why an internal fan exists at all: with the sliders open, buoyancy through two
# ~600 mm2 throats 30 mm apart in height moves about 0.055 L/s and carries ~2 W
# of the PSU's 40 W. The PSU's own top-cover fan does not make that up -- it is a
# recirculating fan, and the path back to its inlet through the box interior is
# near-zero resistance next to the ~13 Pa the ports cost, so it stirs the box
# rather than ventilating it. A fan in series with a port is the only element
# that produces real through-flow. Full arithmetic in docs/design-notes.md.
#
# It goes *inside*, behind the louvre, rather than in the wall like the old
# vent_fan cartridge: that keeps the 45 deg labyrinth in front of the blades, so
# forced ventilation costs nothing in weatherproofing. The 24 V rail is already
# there on the PSU's output terminals.
#
# Only the high port can host it. At the low port the PSU passes within 6.5 mm
# of the wall and the frame already spends 5 of them.
VENT_FAN_SIZE = 40.0  # 40 x 40 x 10 24 V DC fan (the aperture is sized to it)
VENT_FAN_T = 10.0
VENT_FAN_BOLT = 32.0  # standard 4-hole pattern, 4 mm in from each edge
VENT_FAN_CLEAR = 0.5  # per side, fan body to the yoke's locating rim
VENT_FAN_BORE_D = 38.0  # yoke's throat -- clears the blades, keeps the bolt pads

# The yoke: a plate BEHIND the fan that the fan bolts to, standing off the vent
# frame's inner face on two rails. Depth is the tight axis, because the
# controller's mounting tabs reach to within a millimetre, so the budget is
# spelled out rather than left implicit:
#     inner wall face            x = 114.0
#     fan (VENT_FAN_T)           x = 104.0 .. 114.0
#     yoke plate (VENT_YOKE_T)   x = 101.5 .. 104.0
# The rails bridge the remaining VENT_FAN_T - VENT_FRAME_T back to the frame.
VENT_YOKE_T = 2.5  # plate thickness -- 6 perimeters, and it carries ~30 g
VENT_YOKE_T_EDGE = 2.0  # plate edge, out past the fan in Z
VENT_YOKE_RAIL_W = 8.0  # rail width in Y, seating on the frame's side bands
# Screws go into the frame's SIDE bands, at the same radius as the shutter's own
# (offset in Z so the two pilot sets never meet). Putting them above and below
# instead would need ~7 mm of yoke below the fan, and since the yoke's lowest
# edge is what sets how low the high port can sit -- and the port sets the box
# height -- that is 7 mm of enclosure for two screws. See vent_high_z().
VENT_YOKE_SCREW_DZ = 12.0  # screw centres, up and down from the port centre
# The yoke's bottom edge hangs over the PSU's plan (x = 101.5 is well inboard of
# the PSU's 107.5), so it cannot go below the top cover.
VENT_YOKE_PSU_GAP = 3.0  # yoke plate's bottom edge to the PSU's top cover

# --- Sliding shutter (what is actually fitted in both ports) ------------------
# Screwed in once and adjusted in place, instead of swapping a blank for a louvre
# whenever the load changes. The panel's slots are cut at VENT_SLOT_TILT, so they
# climb up-and-in through the 3 mm panel: no straight-line path from outside, and
# 45 is also the steepest self-supporting overhang. A slider rides in a T-channel
# on the outer face -- down and its slots line up (open), up half a pitch and its
# bars cover them (shut).
VENT_SLOT_H = 3.0  # slot opening measured on the panel face
VENT_SLOT_BAR = 3.8  # material between two slots; > SLOT_H so a shut slot overlaps
VENT_SLOT_COUNT = 5
VENT_SLOT_TILT = 45.0
VENT_MULLION_W = 4.0  # centre post; halves the unsupported span of every bar
VENT_RAIL_W = 2.5  # rail footprint each side of the channel
VENT_LIP = 1.5  # how far the rail lip reaches back over the slider
VENT_LIP_T = 1.2
VENT_SLIDER_T = 2.4
# Per-side gap between the slider (SLIDER_W) and the T-channel it rides in
# (CHANNEL_W) -- diametral equivalent is 0.60 mm. This is a repeatedly
# hand-operated slide, not a located fit, so the closer comparison is the
# per-material clearance table's PETG "sliding" row (0.40 mm diametral,
# visible play by design) rather than fits.SLIDING (0.22 mm, PETG baseline --
# a *located* running fit with no perceptible play, the wrong semantics here).
# Even that looser row is undershot on purpose: the slider is a separate,
# weather-exposed part that has to keep moving gritty and wet, and it only
# needs to stay located in-plane -- VENT_DETENT_R and VENT_SLIDER_LIFT are
# what actually retain it out-of-plane. Distinct from VENT_CLEAR above: a
# different mating pair on a different part (the always-fitted slider vs. the
# optional cartridge plug), 0.05 mm apart by coincidence, not redundancy.
VENT_SLIDER_CLEAR = 0.3  # in-plane running clearance, per side
VENT_SLIDER_LIFT = 0.45  # out-of-plane slack -- the slider needs it to ride the detent
VENT_DETENT = 0.4  # how far the detent rod stands above the channel floor
VENT_DETENT_R = 0.8
VENT_END_WALL = 2.6  # solid block closing the top of the channel = the shut stop
VENT_TAB_W = 30.0  # thumb tab on the slider
VENT_TAB_H = 3.6
VENT_TAB_PROUD = 2.0


# --- Derived: the vertical stack ---------------------------------------------
# Read top to bottom. Each function depends only on the ones above it, so the
# box's height is a consequence of the components and the stated clearances
# rather than a number anyone chose.


def psu_top_z() -> float:
    """Top cover of the PSU -- the datum everything above the floor hangs off."""
    return PSU_PLATE_BOSS_H + PSU_PLATE_T + PSU_Z


def vent_frame_inner_x() -> float:
    """Inner face of a vent port's reinforcing frame (positive end)."""
    return INTERIOR_X / 2 - VENT_FRAME_T


def vent_fan_back_x() -> float:
    """Innermost face of the internal fan (positive end).

    The fan sits with its outer face flush with the inner wall face, nosing into
    the aperture; the shutter panel's inner face is another 0.5 mm out.
    """
    return INTERIOR_X / 2 - VENT_FAN_T


def vent_yoke_back_x() -> float:
    """Innermost face of the fan yoke -- the deepest the fan assembly reaches."""
    return vent_fan_back_x() - VENT_YOKE_T


def vent_yoke_screw_y() -> float:
    """Yoke screw centres in Y -- the frame's side bands, as for the shutter."""
    return VENT_W / 2 + VENT_SCREW_OFFSET


def vent_yoke_half_y() -> float:
    """Half-width of the yoke plate: out to its rails, 1 mm inside the frame."""
    return vent_yoke_screw_y() + VENT_YOKE_RAIL_W / 2


def vent_yoke_rail_h() -> float:
    """How far the yoke's rails stand off its plate to reach the frame's face.

    The fan is thicker than the frame is proud, and the difference is exactly
    the standoff -- which is what puts the fan's outer face flush with the inner
    wall face, blowing straight into the aperture.
    """
    return VENT_FAN_T - VENT_FRAME_T


def vent_yoke_half_z() -> float:
    """Half-height of the yoke plate -- just past the fan it carries."""
    return VENT_FAN_SIZE / 2 + VENT_YOKE_T_EDGE


def vent_high_z() -> float:
    """Centre of the high port -- as low as the fan yoke's bottom edge allows.

    Every millimetre here costs a millimetre of box height (see interior_z()), so
    the port is pushed down until the yoke plate would foul the PSU's top cover.
    """
    return psu_top_z() + VENT_YOKE_PSU_GAP + vent_yoke_half_z()


VENT_HIGH_Z = vent_high_z()


def shelf_ledge_z() -> float:
    """Top surface of the ledge the shelf rests on = the shelf's underside."""
    return psu_top_z() + PLENUM_H


def shelf_top_z() -> float:
    """Top surface of the shelf -- what the fuse block and controller sit on."""
    return shelf_ledge_z() + SHELF_T


SHELF_TOP_Z = shelf_top_z()


def interior_z() -> float:
    """Interior height: the tallest of the three chains that compete for it.

    1. **The vent chain.** The high port's frame must stay below rim_band_z() or
       it narrows the mouth and the shelf cannot drop in -- and the port's height
       is set by the internal fan. This is the binding one.
    2. **The fuse chain.** The LXD-4P is the tallest thing in the box and wants
       finger room over its cover.
    3. **The connector chain.** The SP1712 counterbores must clear the rim band.

    Rounded up to the millimetre so the printed part has a tidy dimension.
    """
    vent = vent_high_z() + VENT_H / 2 + VENT_FRAME_MARGIN_Z + 1.0 + RIM_BAND_H
    fuse = shelf_top_z() + FUSE_Z + FUSE_HEADROOM
    conn = SP17_Z + SP17_COUNTERBORE_D / 2 + 1.0 + RIM_BAND_H
    return math.ceil(max(vent, fuse, conn))


INTERIOR_Z = interior_z()


# --- Derived: everything else -------------------------------------------------
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


def drop_opening() -> tuple[float, float]:
    """The clear opening a drop-in part actually has to pass, in X and Y.

    Not the same as the rim mouth. On the way down a part also has to get past
    the two vent frames, which stand ``VENT_FRAME_T`` proud of the end walls and
    are *narrower* than the mouth -- 218 mm against the mouth's 221. Sizing a
    part to ``installable_x()`` alone gives it zero clearance at the frames,
    which is exactly what the shelf used to have.
    """
    return (min(installable_x(), 2 * vent_frame_inner_x()), installable_y())


def shelf_size() -> tuple[float, float]:
    """Shelf plate size: as big as will drop past the rim AND the vent frames."""
    ox, oy = drop_opening()
    return (ox - 2 * SHELF_DROP_CLEAR, oy - 2 * SHELF_DROP_CLEAR)


def shelf_fan_notch() -> tuple[float, float]:
    """(inner x, half-width in y) of the corner the shelf gives up to the fan.

    The fan and its yoke reach inboard past the shelf's own edge at the high
    port, so the shelf loses a shallow bite out of its +X edge. Without it the
    shelf could still be *fitted* (the fan goes in last) but never lifted out
    again without unscrewing the fan -- and lifting the shelf out is how the
    PSU's terminal block and +V ADJ trimmer are reached.
    """
    return (vent_yoke_back_x() - 0.5, vent_yoke_half_y() + 1.0)


def psu_plate_size() -> tuple[float, float]:
    """PSU mounting plate size (also limited by the rim opening)."""
    return (PSU_X + 2 * PSU_PLATE_MARGIN, PSU_Y + 2 * PSU_PLATE_MARGIN)


def stud_peak_z() -> float:
    """Z of the stud head's max diameter, in tray coordinates.

    0.3 mm above the seated plate's recess floor, so the hole edge rests on
    the lead cone with a light preload pressing the plate down onto the seat
    ring instead of rattling on the neck.
    """
    return PSU_PLATE_BOSS_H + PSU_PLATE_T - STUD_RECESS_DEPTH + 0.3


def psu_bolts() -> list[tuple[float, float]]:
    """The PSU's four M4 bottom-face holes, in box coordinates."""
    return [
        (sx * PSU_BOLT_X / 2, sy * PSU_BOLT_Y / 2) for sx in (-1, 1) for sy in (-1, 1)
    ]


def psu_fan_center_x() -> float:
    """X of the PSU's top-cover fan; the high vent port faces this end."""
    return -PSU_TERMINAL_END * (PSU_X / 2 - PSU_FAN_OFFSET)


def vent_high_end() -> int:
    """Which end wall carries the high port (and so the internal fan).

    The end the PSU's own top-cover fan is at, so the box's exhaust and the
    PSU's exhaust are at the same end and the intake is a PSU-length away.
    """
    return 1 if psu_fan_center_x() > 0 else -1


def sp17_positions() -> list[float]:
    """X centres of the connector row, centred on the front wall."""
    span = (SP17_COUNT - 1) * SP17_PITCH
    return [-span / 2 + i * SP17_PITCH for i in range(SP17_COUNT)]
