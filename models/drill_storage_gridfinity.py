"""Gridfinity drill storage tubes -- square-base variant of ``drill_storage``.

Same two-part telescoping idea (a bored base + a tall labelled cover that
friction-fits over it), but the round base is replaced by a **1x1 Gridfinity
foot** so the holder drops into any Gridfinity baseplate, and the cover becomes
a rounded-square tube whose flat face carries the embossed material label.

* Base  -- 42 mm Gridfinity footprint (41.5 mm pad, standard 0.7/1.8/1.9 mm
  foot profile), 42 mm tall (6U). A 41.5 mm body steps down to a 35 mm collar
  that plugs into the cover; graduated drill bores are sunk from the top face.
* Cover -- 42 mm rounded square, 123 mm tall, pillow-rounded closed top, open
  bottom that snaps over the base collar. The material name is engraved (with
  chamfered mouths) up one flat face.

The cover height is derived so the *assembled* holder (cover top above the
baseplate) is a whole number of Gridfinity Z units (147 mm = 21U) and encloses
a drill up to ``MAX_DRILL_LEN`` (132 mm) standing on the bore floor.

Printed standing (cover) / bores-up (base) in PETG, no supports. The base sits
in a Gridfinity baseplate; the cover is a free lid.
"""

import math
import sys

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Cone,
    Cylinder,
    Circle,
    FontStyle,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Polygon,
    Pos,
    RectangleRounded,
    RegularPolygon,
    Rotation,
    Text,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
    sweep,
)

# --- Gridfinity standard ------------------------------------------------------
GRID = 42.0
TOLERANCE = 0.5
PAD = GRID - TOLERANCE  # 41.5 mm pad top
CORNER_R = 4.0  # Gridfinity top corner radius
FOOT_C1 = 0.7  # bottom chamfer (45 deg)
FOOT_STRAIGHT = 1.8  # vertical section
FOOT_C3 = 1.9  # top chamfer (45 deg)
BASE_H = FOOT_C1 + FOOT_STRAIGHT + FOOT_C3  # 4.4 mm foot profile
HEIGHT_UNIT = 7.0  # Gridfinity Z unit

# --- Cover --------------------------------------------------------------------
# (COVER_H is derived under "Assembled height" once the base + cap are known.)
COVER_W = 42.0  # rounded-square outer (roughly flush with body)
COVER_WALL = 1.2  # thin wall (flexes for the snap)
INNER_W = COVER_W - 2 * COVER_WALL  # 39.6 mm bore -- close slip fit over collar
CAP_H = 3.0  # solid rounded cap at the top
TOP_FILLET = 4.0
CAP_FILLET = 1.5  # inner fillet where the bore ceiling meets walls
INNER_R = 2.0
LABEL_SIZE = 13.0
LABEL_Z = 45.0
LABEL_DEPTH = 0.6  # engrave depth into the flat face (< COVER_WALL, no punch-through)
LABEL_CHAMFER = 0.5  # near-full-depth bevel -> a continuous V-groove wall, no step

# --- Snap fit -----------------------------------------------------------------
# A shallow *ramped* bead runs around the inside of the cover near its opening
# and clicks into a rounded groove on the base collar. The bead is an asymmetric
# chamfered ring, not a half-round bump: a long gentle lead-in ramp on the
# insertion side (below the tip) so the cover slides on progressively, and a
# shorter, steeper retention face above so it still detents on the way in. The
# old half-round bead changed height as steeply as it protruded, so the cover
# fought over it going on. Protrusion is also trimmed a touch so the bulge is
# thinner. The groove stays a forgiving round pocket that simply receives the tip.
SLIP = 0.4  # diametral slip clearance, collar in cover bore
SNAP_Z = 6.0  # height of the bead/groove above the cover opening / collar base
SNAP_PROTRUSION = 0.45  # how far the bead tip stands into the bore (was 0.6)
SNAP_LEAD_IN = 2.4  # vertical run of the gentle insertion ramp (below the tip)
SNAP_BACK = 1.1  # vertical run of the steeper retention face (above the tip)
SNAP_TIP_FLAT = 0.3  # short flat at the tip so it isn't a fragile knife edge
SNAP_GROOVE_R = 0.8  # rounded groove radius on the collar (receives the bead tip)

# --- Base ---------------------------------------------------------------------
FOOT_TOP = 24.0  # top of the full-width body (cover seats here)
COLLAR_W = INNER_W - SLIP  # collar is a close slip fit inside the cover bore
COLLAR_R = 3.5
COLLAR_H = 18.0
BASE_TOTAL_H = FOOT_TOP + COLLAR_H  # 42 mm (6U)
COVER_SEAT_CH = 0.4  # cover bottom-edge chamfer so it seats flush on
#                                 the flat body shoulder without overhanging it
BORE_DEPTH = 36.0  # bores sunk from the top face (stops above foot)
BORE_MOUTH_CHAMFER = 0.8  # 45-deg lead-in chamfer depth at every insert-hole mouth
BASE_TOP_CHAMFER = 1.0  # 45-deg chamfer on the base's top outer rim

# --- Size labels on the base body walls ---------------------------------------
# Each drill's size is engraved into the body's outer wall, on whichever of the
# four faces the hole points toward, centred in front of the hole -- so you read
# a face and look straight in, and the set is legible from all four sides.
WALL_LABEL_SIZE = 4.0
WALL_LABEL_Z = 14.0  # vertical centre of the numbers on the ~4.4..24 mm body wall
WALL_LABEL_DEPTH = 0.8  # engrave depth -- deep enough to stay legible under layer
#                         lines on the vertical (bores-up) print orientation
WALL_LABEL_STYLE = FontStyle.BOLD  # bold: ~1 mm strokes + a 0.7 mm decimal point,
#                         so the fine features survive an FDM nozzle in ABS
WALL_LABEL_MAX_LAT = PAD / 2 - CORNER_R - 1.0  # keep numbers off the rounded corners

# --- Automatic hole layout ----------------------------------------------------
# Spacing budget handed to ``pack_rows`` (see ``layout_bores``). HOLE_WALL is the
# minimum edge-to-edge gap used to grade holes into rows -- two mouth chamfers
# plus a hair so both lead-ins fit between neighbours. WALL_CLEARANCE is the
# minimum every hole keeps to the collar wall -- a mouth chamfer + the top-rim
# chamfer + margin, so a hole's lead-in and the rim chamfer both still form.
HOLE_WALL = 2 * BORE_MOUTH_CHAMFER + 0.1
WALL_CLEARANCE = BORE_MOUTH_CHAMFER + BASE_TOP_CHAMFER + 0.4

# --- Assembled height ---------------------------------------------------------
# A drill stands on the bore floor and rises up into the cover. Size the cover
# so the assembled envelope (cover top above the baseplate) rounds UP to a whole
# Gridfinity Z unit and still clears the longest drill plus headroom.
MAX_DRILL_LEN = 132.0  # longest drill the *default* holder must enclose
DRILL_HEADROOM = 6.0  # clear space above the drill tip under the cap
BORE_FLOOR_Z = BASE_TOTAL_H - BORE_DEPTH  # 6 mm above plate


def cover_height_for(
    max_drill_len: float,
    headroom: float = DRILL_HEADROOM,
    bore_floor_z: float = BORE_FLOOR_Z,
    foot_top: float = FOOT_TOP,
) -> float:
    """Cover height whose *assembled* envelope is the smallest whole Gridfinity Z
    unit that still encloses a drill of ``max_drill_len`` standing on the bore
    floor, plus ``headroom`` under the cap. This is the "just fits, not longer"
    rule: the total assembled height quantises up to the next 7 mm unit, so a
    drill any longer would need one more unit.

    ``bore_floor_z`` is where the bit's tail rests. It defaults to the standard
    ``BORE_FLOOR_Z``, but a base with shallower bores (short bits, sunk only far
    enough to leave a grip proud of the collar) stands its tools higher and must
    pass its own floor. ``foot_top`` is the shoulder the cover seats on -- pass
    it too whenever ``create_base`` gets a non-default one.
    """
    cover_top_min = bore_floor_z + max_drill_len + headroom + CAP_H
    total_assembled_h = math.ceil(cover_top_min / HEIGHT_UNIT) * HEIGHT_UNIT
    return total_assembled_h - foot_top


TOTAL_ASSEMBLED_H = (
    math.ceil((BORE_FLOOR_Z + MAX_DRILL_LEN + DRILL_HEADROOM + CAP_H) / HEIGHT_UNIT)
    * HEIGHT_UNIT
)  # 147 (21U)
COVER_H = cover_height_for(MAX_DRILL_LEN)  # 123 mm default cover

# --- Ribbed bores (opt-in) ----------------------------------------------------
# A ribbed bore is cut wider than the bit and given RIB_COUNT rounded ribs
# standing proud of the relieved valley. Each rib is a vertical round-topped bead
# (a cylinder whose inner edge is the grip radius), so the bit rides on a rounded
# contact -- which sits just *inside* it -- and is held by light interference
# rather than rattling. Near the top each rib ramps out to nothing over RIB_TAPER
# (a cone cap) so it flows back into the wall instead of ending in a sharp square
# top: that taper is the bit's lead-in onto the ribs. The rib dimensions SCALE
# with the bit diameter (a fixed-size rib swamps a small hole and rattles in a
# big one), each floored so it stays printable / meaningful on the smallest bits.
# Ribs stop RIB_TOP_GAP below the mouth so the opening stays clean for the lead-in
# chamfer.
RIB_COUNT = 3
#
# --- Why the grip law is shaped the way it is ---------------------------------
# Two full sets were printed and both fought back, in opposite directions:
#
#   v1  grip = 0.04*d (min 0.15)  -> 9/10 mm too tight, 8 mm and under too loose
#   v2  grip = 0.34 flat, falling -> 8/9/10 mm too loose, 6 mm and under too tight
#
# Those reports are consistent, and the reason is *not* the interference number.
# It's that the ribs were never springs. The protrusion past the valley was only
# RIB_RELIEF_MIN = 0.2 mm on the small bores while the bead was 0.8 mm wide, so
# each "rib" was a shallow lens welded to the wall over nearly its full width --
# it cannot deflect, it can only be crushed. v2 asked a 2 mm bore to squash 85%
# of its rib away, and a 10 mm bore to engage only 25% of one. The whole usable
# travel between "rattles" and "jams" was ~0.1 mm of radius, which is finer than
# FDM's own run-to-run variation on a small hole. No constant could have worked.
#
# The fix is geometric, not numeric: give the rib a real compliant travel, then a
# single absolute interference works for every size. The bead is now mostly
# *proud* of the valley (RIB_RELIEF_FRAC_OF_WIDTH), so it meets the wall on a
# narrow neck and behaves like a stub spring instead of a bump. With the rib
# shape held proportional to the bore, its radial stiffness k ~ E*h*(width/relief)
# is roughly constant across sizes -- so a constant deflection gives a constant
# retention force, and grip becomes force-controlled rather than position-
# controlled. That is what makes one number cover 2-10 mm.
#
RIB_GRIP = 0.30  # diametral interference at the rib faces -- ONE value, all sizes
# The bead is now the SAME size in every bore rather than scaled to the bit. That
# is the point: an identically-shaped rib has identical radial stiffness, so an
# identical deflection gives an identical retention force from 2 mm to 10 mm. A
# rib scaled to the bore is a stiffer spring in a big hole, which is how the old
# law ended up needing a different number for every size.
RIB_WIDTH = 0.9  # rounded-bead diameter (>= 2 perimeters at the neck)
# Protrusion past the valley, as a fraction of the bead width. Must stay < 1.0 or
# the bead never reaches the valley wall and prints as a floating pin. At 0.75 the
# bead is mostly proud, giving 0.68 mm of travel on a 0.78 mm neck: the nominal
# 0.15 mm radial crush is then only ~22% of the rib, well inside its elastic
# range, where the old design asked for up to 85% (i.e. destruction).
RIB_RELIEF_FRAC_OF_WIDTH = 0.75
RIB_TAPER = 4.0  # height over which each rib ramps out to nothing near the top

# Ribs grip only a band just above the bore floor, not the whole depth. Every bit
# stands on the floor, so this band always lands on the *plain shank* -- a true
# h8 cylinder with no cutting edges. Higher up sit the flutes, which are not a
# cylinder at all (two narrow spiral margins at nominal diameter over a flute
# void, plus body clearance/back taper), so ribs there grip intermittently and,
# worse, the hardened tip spurs broach the ribs on the way past and the bore
# loses interference permanently. That reaming is the best explanation for the
# "tight going in, loose once seated" feel of the big bits. Bits therefore go in
# SHANK-DOWN (flutes and tip up, under the cover).
RIB_ZONE_H = 14.0  # rib band height above the bore floor (shank engagement)

# Hex sockets used to get their grip from being cut *under* the nominal
# across-flats, and that was the same mistake as the old bumpy ribs: flat-on-flat
# against a solid wall has no compliance whatsoever, so the fit went from drop-in
# (0.00, nominal 6.30) to jammed (0.15) over a tenth and a half. Nothing to tune.
#
# So the hex now works exactly like the round bores: the socket itself is cut
# *over* size and simply guides the shank and stops it rotating, while the grip
# comes from three compliant ribs in a band at the bottom, bearing on alternating
# flats at the same RIB_GRIP interference as every drill. One calibration number
# covers the whole tray. Within that band the socket opens out to a round relief
# pocket (wide enough to swallow the hex corners) so the ribs have travel behind
# them -- invisible from outside, where the mouth stays a clean hex.
HEX_SLIP = 0.05  # across-flats clearance on the guide socket -- drops straight in
HEX_RIB_ANGLE = 30.0  # flat centres sit at 30 deg + k*60 (vertices land on 0 deg)
RIB_TOP_GAP = BORE_MOUTH_CHAMFER + 0.4  # ribs stop this far below the mouth


def _rib_tip_r(d: float, grip: float = RIB_GRIP) -> float:
    """Radius of the rib faces (grip) for a bit of diameter ``d`` -- just inside
    the bit so it's held by light interference. ``grip`` is diametral."""
    return (d - grip) / 2


def _rib_width(d: float, grip: float = RIB_GRIP) -> float:
    """Diameter of the rounded rib bead -- fixed, except on the tiniest bores
    where it is capped so three beads can't choke the hole."""
    return min(RIB_WIDTH, 1.4 * _rib_tip_r(d, grip))


def _rib_relief(d: float, grip: float = RIB_GRIP) -> float:
    """Radial protrusion of the ribs past the relieved valley for diameter ``d``.

    Tied to the bead width (not to ``d``) because it is the ratio of the two that
    decides whether the rib is a spring or a bump -- see the notes above.
    """
    return RIB_RELIEF_FRAC_OF_WIDTH * _rib_width(d, grip)


def ribbed_valley_r(d: float) -> float:
    """Cut (valley) radius of a ribbed bore -- its footprint for layout/packing."""
    return _rib_tip_r(d) + _rib_relief(d)


# Demo drill sets for the default holder -- just the sizes; ``layout_bores``
# solves the positions (see ``create``). A small graduated set and a large-bit
# set, to show both ends of the range.
DEMO_DIAMS_SMALL = [3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.5]
DEMO_DIAMS_LARGE = [6.0, 8.0, 10.0, 12.0]

BASE_COLOR = Color(0.62, 0.64, 0.67)
COVER_COLOR = Color(0.93, 0.93, 0.92)


def _gridfinity_foot() -> Part:
    """One 1x1 Gridfinity base foot; pad top lands at z=BASE_H."""
    bottom = PAD - 2 * (FOOT_C1 + FOOT_C3)
    mid = PAD - 2 * FOOT_C3
    r_bottom = CORNER_R - (FOOT_C1 + FOOT_C3)
    r_mid = CORNER_R - FOOT_C3
    with BuildPart() as foot:
        for size, radius, z in [
            (bottom, r_bottom, 0.0),
            (mid, r_mid, FOOT_C1),
            (mid, r_mid, FOOT_C1 + FOOT_STRAIGHT),
            (PAD, CORNER_R, BASE_H),
        ]:
            with BuildSketch(Plane.XY.offset(z)):
                RectangleRounded(size, size, radius)
        loft(ruled=True)
    return foot.part


def _snap_ring(size: float, corner_r: float, z: float, bead_r: float) -> Part:
    """A half-round bead ring: a circle of radius ``bead_r`` swept around a
    rounded-square perimeter of side ``size`` at height ``z``. Union it for a
    bead (protrudes inward), or subtract it for a groove."""
    with BuildSketch(Plane.XY.offset(z)) as outline:
        RectangleRounded(size, size, corner_r)
    path = outline.faces()[0].outer_wire()
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ):
            with Locations((size / 2, z)):
                Circle(bead_r)
        sweep(path=path)
    return ring.part


def _snap_bead_ring(size: float, corner_r: float, z: float) -> Part:
    """A chamfered (asymmetric) bead ring for a smooth-engaging snap fit.

    Instead of a half-round bump, the cross-section is a quad that protrudes
    ``SNAP_PROTRUSION`` inward from the wall and rises with a long, gentle
    ``SNAP_LEAD_IN`` ramp on the insertion (lower) side and a shorter, steeper
    ``SNAP_BACK`` retention face on the upper side, with a small ``SNAP_TIP_FLAT``
    at the tip. Swept around the rounded-square perimeter of side ``size`` at
    height ``z``; union it into the cover so the cover slides on progressively
    yet still detents into the collar groove. The gentle ramp is the "chamber
    that slides on"; the round groove (``_snap_ring``) forgivingly receives it.
    """
    with BuildSketch(Plane.XY.offset(z)) as outline:
        RectangleRounded(size, size, corner_r)
    path = outline.faces()[0].outer_wire()
    x_wall = size / 2  # bead base sits on the bore wall ...
    x_tip = size / 2 - SNAP_PROTRUSION  # ... and its tip stands inward into the bore
    # Local sketch coords on Plane.XZ: x -> radius, y -> height (matches _snap_ring).
    profile = [
        (x_wall, z - SNAP_LEAD_IN),  # bottom of the gentle insertion ramp
        (x_tip, z - SNAP_TIP_FLAT / 2),  # tip, lower
        (x_tip, z + SNAP_TIP_FLAT / 2),  # tip, upper
        (x_wall, z + SNAP_BACK),  # top of the steeper retention face
    ]
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ):
            Polygon(*profile, align=None)
        sweep(path=path)
    return ring.part


def _rim_chamfer_tool(width: float, corner_r: float, top_z: float, ch: float) -> Part:
    """A subtract tool that 45-deg-chamfers a rounded-square top outer rim.

    Built as booleans (an oversized slab minus the beveled keep-frustum) instead
    of an OCC fillet/chamfer op, which is unreliable on this rim next to the
    perimeter holes. Subtract the returned part from the base.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(top_z - ch)):
            RectangleRounded(width + 4, width + 4, corner_r)
        extrude(amount=ch)
        # Beveled keep-shape: full rim at the bottom, inset by ch at the top.
        with BuildSketch(Plane.XY.offset(top_z - ch)):
            RectangleRounded(width, width, corner_r)
        with BuildSketch(Plane.XY.offset(top_z)):
            RectangleRounded(width - 2 * ch, width - 2 * ch, max(corner_r - ch, 0.2))
        loft(mode=Mode.SUBTRACT)
    return tool.part


# Fixed symmetry slots for the structured layout, outermost group first: the
# corner diagonals, the edge axes, then an inner diagonal ring, an inner axis
# ring, and finally the centre. Each entry is (angles_deg, seed_radius_fraction,
# pinned). Pinned (perimeter) holes are held at their maximum radius so every one
# sits the SAME distance from the wall -- even margins all the way round; the
# rest seed inward and relax so the interior spreads out without touching a wall.
_HOLE_SLOTS = [
    ([45, 135, 225, 315], 0.62, True),  # corners -> pinned to a uniform wall gap
    ([0, 90, 180, 270], 0.60, True),  # edges -> pinned to a uniform wall gap
    ([45, 135, 225, 315], 0.28, False),  # inner diagonal ring -> relaxed inward
    ([0, 90, 180, 270], 0.24, False),  # inner axis ring -> relaxed inward
    ([None], 0.0, False),  # centre
]


def pack_holes(
    footprints: list[tuple[str, float]],
    collar_half: float,
    corner_r: float,
    hole_wall: float,
    collar_wall: float,
    iters: int = 6000,
) -> dict[str, tuple[float, float]]:
    """Place holes in an orderly, symmetric layout; return ``{key: (x, y)}``.

    ``footprints`` is ``(key, radius)`` per hole, ``radius`` being the hole's cut
    footprint (a ribbed bore's valley radius, or the hex countersink's head
    radius). The holes are graded onto fixed symmetry slots (``_HOLE_SLOTS``) --
    largest four to the corner diagonals, next four to the edge axes, the rest to
    an inner ring / centre -- and each hole's radius *along its fixed spoke* is
    relaxed until it keeps at least ``hole_wall`` to its neighbours edge-to-edge
    and at least ``collar_wall`` to the rounded collar wall. Fixing the angles
    keeps the arrangement tidy and symmetric while the radial relaxation resolves
    spacing.

    Size ``hole_wall`` to ``2 * BORE_MOUTH_CHAMFER`` so both mouth fillets fit
    between neighbours, and ``collar_wall`` to ``BORE_MOUTH_CHAMFER +
    BASE_TOP_CHAMFER`` so a hole's mouth fillet and the top-rim fillet both fit;
    then every fillet in ``create_base`` forms. Deterministic (no RNG). Prints a
    WARNING if the collar is too crowded to reach the spacing.
    """
    order = sorted(range(len(footprints)), key=lambda i: -footprints[i][1])
    keys = [footprints[i][0] for i in order]
    r = [footprints[i][1] for i in order]
    n = len(footprints)

    theta: list[float | None] = []
    seed: list[float] = []
    pinned: list[bool] = []
    for angles, frac, pin in _HOLE_SLOTS:
        for a in angles:
            if len(theta) < n:
                theta.append(None if a is None else math.radians(a))
                seed.append(frac * collar_half)
                pinned.append(pin)

    def sdf(px: float, py: float) -> float:
        # Signed distance to the rounded-square collar wall (negative inside).
        qx = abs(px) - (collar_half - corner_r)
        qy = abs(py) - (collar_half - corner_r)
        return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - corner_r

    def max_radius(i: int) -> float:
        # Largest radius on hole i's fixed spoke that still clears the collar
        # wall by ``collar_wall`` -- i.e. an exactly ``collar_wall`` margin.
        lo, hi = 0.0, collar_half
        for _ in range(28):
            m = (lo + hi) / 2.0
            if (
                -sdf(m * math.cos(theta[i]), m * math.sin(theta[i])) - r[i]
                >= collar_wall
            ):
                lo = m
            else:
                hi = m
        return lo

    def spoke(i: int, rho: float) -> list[float]:
        return [rho * math.cos(theta[i]), rho * math.sin(theta[i])]

    # Pin perimeter holes to their max radius (uniform wall margin); seed the
    # rest inward to relax.
    pos = [
        [0.0, 0.0]
        if theta[i] is None
        else spoke(i, max_radius(i) if pinned[i] else seed[i])
        for i in range(n)
    ]

    def reproject(i: int) -> None:
        # Keep each hole on its fixed spoke: perimeter holes stay pinned at the
        # uniform wall margin; inner holes clamp to their max radius but are
        # otherwise free to relax inward.
        if theta[i] is None:
            pos[i] = [0.0, 0.0]
        elif pinned[i]:
            pos[i] = spoke(i, max_radius(i))
        else:
            pos[i] = spoke(i, min(math.hypot(pos[i][0], pos[i][1]), max_radius(i)))

    for _ in range(iters):
        moved = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[j][0] - pos[i][0]
                dy = pos[j][1] - pos[i][1]
                d = math.hypot(dx, dy) or 1e-9
                need = r[i] + r[j] + hole_wall
                if d < need:
                    push = (need - d) / 2.0
                    ux, uy = dx / d, dy / d
                    pos[i][0] -= ux * push
                    pos[i][1] -= uy * push
                    pos[j][0] += ux * push
                    pos[j][1] += uy * push
                    moved = max(moved, push)
        for i in range(n):
            reproject(i)
        if moved < 1e-4:
            break

    worst = min(
        (
            math.hypot(pos[j][0] - pos[i][0], pos[j][1] - pos[i][1]) - r[i] - r[j]
            for i in range(n)
            for j in range(i + 1, n)
        ),
        default=hole_wall,
    )
    if worst < hole_wall - 0.05:
        print(
            f"WARNING: hole placement only reached {worst:.2f} mm walls "
            f"(wanted {hole_wall:.2f} mm) -- the collar is too crowded; drop a "
            f"hole or shrink one.",
            file=sys.stderr,
        )
    return {keys[i]: (round(pos[i][0], 2), round(pos[i][1], 2)) for i in range(n)}


def pack_rows(
    items: list[tuple[str, float]],
    collar_half: float,
    corner_r: float,
    hole_wall: float,
    wall_clearance: float,
) -> tuple[dict[str, tuple[float, float]], list[list[str]]]:
    """Lay holes out in tidy rows, ordered largest -> smallest, rows shrinking,
    spread to fill the collar.

    ``items`` is ``(key, footprint_r)``. Holes are sorted big-first and dealt into
    ~sqrt(n) rows so the biggest fill a short top row and each following row holds
    progressively smaller bits (a balanced pyramid). Within a row they run largest
    -> smallest, left -> right; rows stack back (+Y, biggest) to front (-Y,
    smallest).

    Rather than centre-packing, the holes are *spread*: rows are pushed apart
    vertically and the holes within each row pushed apart horizontally until the
    outermost sit exactly ``wall_clearance`` from the rounded collar wall, then the
    remaining slack is shared out as equal gaps. This maximises the space between
    holes while keeping the minimum edge distance and neat, evenly spaced rows.
    ``hole_wall`` is only the *minimum* spacing used to grade holes into rows.

    Returns ``({key: (x, y)}, rows)`` (``rows`` = keys per row, biggest first).
    Prints a WARNING if a row can't fit (holes would overlap).
    """
    rmap = {k: r for k, r in items}
    order = sorted(items, key=lambda kv: -kv[1])
    n = len(order)
    n_rows = max(1, round(n**0.5))
    a = collar_half - corner_r

    def sdf(px: float, py: float) -> float:
        qx = abs(px) - a
        qy = abs(py) - a
        return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - corner_r

    def reach(coord, r: float) -> float:
        """Largest t >= 0 along the ray ``coord(t)`` where a hole of radius ``r``
        still keeps ``wall_clearance`` to the collar wall."""
        lo, hi = 0.0, collar_half
        for _ in range(44):
            m = (lo + hi) / 2
            px, py = coord(m)
            if -sdf(px, py) - r >= wall_clearance:
                lo = m
            else:
                hi = m
        return lo

    # Grade holes into rows: each row takes its share, but never more than fits
    # across the widest usable span (centres reach in by wall_clearance + radius).
    budget = 2 * reach(lambda t: (t, 0.0), 0.0)
    rows: list[list[str]] = []
    idx = 0
    rows_left = n_rows
    while idx < n:
        cap = math.ceil((n - idx) / rows_left)
        row: list[str] = []
        w = 0.0
        while idx < n and len(row) < cap:
            r = order[idx][1]
            need = 2 * r + (hole_wall if row else 0.0)
            if row and w + need > budget:
                break
            row.append(order[idx][0])
            w += need
            idx += 1
        rows.append(row)
        rows_left = max(1, rows_left - 1)

    row_rmax = [max(rmap[k] for k in row) for row in rows]
    n_r = len(rows)

    # Vertical: push the top/bottom rows out to their wall clearance and share the
    # remaining height as equal gaps between rows.
    if n_r == 1:
        y_centers = [0.0]
    else:
        y_top = reach(lambda t: (0.0, t), row_rmax[0])
        y_bot = -reach(lambda t: (0.0, t), row_rmax[-1])
        adj = sum(row_rmax[i] + row_rmax[i + 1] for i in range(n_r - 1))
        gap_y = (y_top - y_bot - adj) / (n_r - 1)
        y_centers = [y_top]
        for i in range(n_r - 1):
            y_centers.append(y_centers[-1] - (row_rmax[i] + gap_y + row_rmax[i + 1]))

    positions: dict[str, tuple[float, float]] = {}
    worst_gap = 1e9
    for row, yc in zip(rows, y_centers):
        rs = [rmap[k] for k in row]
        k = len(row)
        if k == 1:
            xs = [0.0]
        else:
            # End holes out to their own wall clearance; slack shared as equal gaps.
            x_left = -reach(lambda t: (-t, yc), rs[0])
            x_right = reach(lambda t: (t, yc), rs[-1])
            gap_x = ((x_right - x_left) - (2 * sum(rs) - rs[0] - rs[-1])) / (k - 1)
            worst_gap = min(worst_gap, gap_x)
            xs = [x_left]
            for i in range(k - 1):
                xs.append(xs[-1] + rs[i] + gap_x + rs[i + 1])
        for key, x in zip(row, xs):
            positions[key] = (round(x, 2), round(yc, 2))

    if worst_gap < -0.05:
        print(
            f"WARNING: a row overpacks by {-worst_gap:.2f} mm (holes overlap) -- "
            f"drop a size or shrink one.",
            file=sys.stderr,
        )
    return positions, rows


def layout_bores(
    drill_diams: list[float],
    hex_tools: list[tuple[str, float, float]] | None = None,
    swap: list[tuple[str, str]] | None = None,
) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float, float]],
    list[list[str]],
    dict[str, tuple[float, float]],
]:
    """Intelligently position a graduated drill set on the collar in tidy rows.

    The one-call front end to ``pack_rows`` shared by every variant: hand it the
    drill diameters (and any hex-shank tools) and it returns everything
    ``create_base`` needs -- positioned round bores, hex sockets, the row grouping
    and the ``{key: (x, y)}`` map for the wall legend -- so a set is defined by
    just its sizes and the layout is solved, not hand-placed.

    ``drill_diams`` are round ribbed bores; each is packed by its
    ``ribbed_valley_r`` footprint and keyed by its ``{d:g}`` size string.
    ``hex_tools`` are ``(label, across_flats, footprint_r)`` for hex-shank bits:
    the shank drops into an ``across_flats`` socket while ``footprint_r`` is the
    radius reserved during packing (a countersink's head is wider than its socket;
    a plain hex tool's is just its circumradius). ``swap`` optionally exchanges the
    positions of two keys after packing (e.g. move a countersink out to a row edge
    and give the centre slot to a same-size drill).

    Returns ``(drill_bores, hex_bores, rows, hole_pos)``.
    """
    hex_tools = hex_tools or []
    items = [(f"{d:g}", ribbed_valley_r(d)) for d in drill_diams]
    items += [(label, foot_r) for label, _af, foot_r in hex_tools]
    pos, rows = pack_rows(items, COLLAR_W / 2, COLLAR_R, HOLE_WALL, WALL_CLEARANCE)
    for a, b in swap or []:
        pos[a], pos[b] = pos[b], pos[a]
    drill_bores = [(d, pos[f"{d:g}"][0], pos[f"{d:g}"][1]) for d in drill_diams]
    hex_bores = [(af, pos[label][0], pos[label][1]) for label, af, _foot_r in hex_tools]
    return drill_bores, hex_bores, rows, pos


# Outward-normal, upright (+Z up) text frames for each body face: (origin, x_dir,
# z_dir) as a function of the in-face lateral offset and height. Used to engrave
# the size legend into the base body's four walls.
def _face_frame(face: str, lateral: float, z: float):
    half = PAD / 2
    return {
        "N": ((lateral, half, z), (-1, 0, 0), (0, 1, 0)),
        "S": ((lateral, -half, z), (1, 0, 0), (0, -1, 0)),
        "E": ((half, lateral, z), (0, 1, 0), (1, 0, 0)),
        "W": ((-half, lateral, z), (0, -1, 0), (-1, 0, 0)),
    }[face]


def _engrave_row_legend(
    rows: list[list[str]],
    pos: dict[str, tuple[float, float]],
    z_center: float = WALL_LABEL_Z,
    line_h: float | None = None,
) -> None:
    """Engrave the size legend into the front and back body walls.

    ``rows`` lists the hole keys per row (biggest row first); ``pos`` is each
    key's ``(x, y)``. Only the front and back walls (-Y / +Y) carry the legend --
    the rows run edge-on into the left/right walls, so a legend there can't line
    up with the holes and is left off.

    Each number is engraved *individually*, centred at its hole's own x, so it
    sits directly in front of that hole's column (from either wall -- a label at
    the hole's world-x tracks the hole through the view mirror). Rows stack in z
    with the row nearest the wall at the bottom. A number is nudged inward only if
    it would otherwise run off the flat wall onto a rounded corner.

    ``z_center`` is the vertical middle of the block of rows and ``line_h`` the
    row pitch; a base with a shortened body (see ``create_base``'s ``foot_top``)
    passes its own so the block still lands on the wall. The defaults suit the
    standard 24 mm body.

    Call inside the active BuildPart.
    """
    n = len(rows)
    line_h = WALL_LABEL_SIZE + 1.6 if line_h is None else line_h
    z_top = z_center + (n - 1) * line_h / 2
    flat_half = PAD / 2 - CORNER_R  # numbers must stay on the flat wall face

    def engrave(text: str, face: str, lateral: float, z: float) -> None:
        # Keep the (centre-aligned) glyphs clear of the rounded corners.
        limit = flat_half - 0.31 * WALL_LABEL_SIZE * len(text) - 0.3
        lateral = max(-limit, min(limit, lateral))
        origin, x_dir, z_dir = _face_frame(face, lateral, z)
        with BuildSketch(Plane(origin=origin, x_dir=x_dir, z_dir=z_dir)) as sk:
            Text(text, font_size=WALL_LABEL_SIZE, font_style=WALL_LABEL_STYLE)
        extrude(sk.sketch, amount=-WALL_LABEL_DEPTH, mode=Mode.SUBTRACT)

    row_y = [sum(pos[k][1] for k in row) / len(row) for row in rows]
    # Front (-Y / S): nearest row (min y) at the bottom. Back (+Y / N): nearest
    # row (max y) at the bottom. Each number is placed at its hole's world-x, so
    # it lines up in front of the hole from that wall's side either way.
    for face, order in (
        ("S", sorted(range(n), key=lambda i: -row_y[i])),
        ("N", sorted(range(n), key=lambda i: row_y[i])),
    ):
        for line_idx, ri in enumerate(order):
            z = z_top - line_idx * line_h
            for k in rows[ri]:
                engrave(k, face, pos[k][0], z)


def cut_holes(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None,
    clearance: float,
    ribbed: bool,
    top_z: float,
    bore_depth: float,
    through: bool = False,
    undersize_frac: float = 0.0,
    grip: float | None = None,
) -> None:
    """Sink drill bores + hex sockets into the active part and chamfer every mouth.

    Call this inside a ``with BuildPart()`` block; it operates on the active
    builder and is shared by the Gridfinity base and the fit tester so both get
    identical bore geometry.

    Round ``bores`` are ``(diameter, x, y)`` sunk ``bore_depth`` down from
    ``top_z``. When ``ribbed`` each gets ``RIB_COUNT`` rounded ribs whose contact
    edge sits ``RIB_GRIP`` (one absolute interference, every size) inside it; the
    ribs occupy only ``RIB_ZONE_H`` above the floor so they grip the bit's plain
    shank, and each tapers out to nothing over ``RIB_TAPER`` as a lead-in. ``grip``
    overrides ``RIB_GRIP`` for this call, which is how the fit tester sweeps it. Plain (not ribbed) holes are sized ``clearance``
    (mm) plus ``undersize_frac`` (a fraction of the bit) under -- the fractional
    part compensates the way small holes print tighter than large ones.

    ``hex_bores`` are ``(across_flats, x, y)``. Every mouth gets a 45-deg lead-in
    chamfer of depth ``BORE_MOUTH_CHAMFER``, cut as a boolean (robust; see the
    note below). With ``through`` the bores punch out the bottom (no floor); the
    ribs still start at ``top_z - bore_depth``.
    """
    grip = RIB_GRIP if grip is None else grip
    floor_z = top_z - bore_depth
    below = 1.0 if through else 0.0  # extend the cut past the bottom face
    for d, x, y in bores:
        if ribbed:
            r_tip = _rib_tip_r(d, grip)
            relief = _rib_relief(d, grip)
            r_valley = r_tip + relief
        else:
            r_tip = (d + clearance - undersize_frac * d) / 2
            r_valley = r_tip
        with Locations((x, y, floor_z - below)):
            Cylinder(
                r_valley,
                bore_depth + 1 + below,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        if ribbed:
            # Rounded ribs standing proud of the valley: each is a vertical
            # round-topped bead (a cylinder of diameter ``width``) whose inner
            # edge is the grip radius ``r_tip``, so the bit rides on a rounded
            # contact. The bead is wide enough that its far side always crosses
            # the valley wall (width > relief), so it merges solidly into the
            # body -- never a floating pin. Over the top RIB_TAPER a coaxial cone
            # tapers the bead to nothing (apex at the wall, not free-floating), so
            # it ramps out into the wall as a lead-in instead of ending square.
            # Width scales with the hole (and is capped) so it can't choke a bore.
            # The ribs occupy only a band above the floor (RIB_ZONE_H) so they
            # grip the bit's plain shank and never the flutes -- but never more
            # than the bore itself allows.
            rib_h = min(RIB_ZONE_H, bore_depth - RIB_TOP_GAP)
            width = _rib_width(d, grip)
            bead_r = width / 2
            center_r = r_tip + bead_r  # inner edge of the bead lands on r_tip
            body_h = rib_h - RIB_TAPER
            with Locations((x, y, floor_z)):
                with PolarLocations(center_r, RIB_COUNT):
                    Cylinder(
                        bead_r,
                        body_h,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.ADD,
                    )
                    with Locations((0, 0, body_h)):
                        Cone(
                            bead_r,
                            0.0,
                            RIB_TAPER,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                            mode=Mode.ADD,
                        )

    for af, x, y in hex_bores or []:
        # Guide socket: cut oversize, so the shank drops straight in and is only
        # kept from spinning. All the grip happens in the rib band below.
        with BuildSketch(Plane.XY.offset(top_z)) as hex_sk:
            with Locations((x, y)):
                RegularPolygon((af + HEX_SLIP) / 3**0.5, 6)
        # Pass the sketch explicitly: inside a helper the implicit "pending
        # sketch" lookup that a bare extrude() relies on doesn't resolve.
        extrude(hex_sk.sketch, amount=-(bore_depth + below), mode=Mode.SUBTRACT)

        if not ribbed:
            continue
        # Same rib treatment as a round bore, with the across-flats standing in
        # for the diameter: the rib faces land RIB_GRIP inside the flats, and the
        # band is first opened out to a round relief pocket wide enough to
        # swallow the hex corners so each bead has travel behind it.
        r_tip = _rib_tip_r(af, grip)  # half the across-flats, less half the grip
        width = _rib_width(af, grip)
        r_valley = r_tip + _rib_relief(af, grip)
        rib_h = min(RIB_ZONE_H, bore_depth - RIB_TOP_GAP)
        bead_r = width / 2
        body_h = rib_h - RIB_TAPER
        with Locations((x, y, floor_z - below)):
            Cylinder(
                r_valley,
                rib_h + below,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations((x, y, floor_z)):
            # Beads on alternating flats (every other one, so 3 of the 6).
            with PolarLocations(r_tip + bead_r, RIB_COUNT, start_angle=HEX_RIB_ANGLE):
                Cylinder(
                    bead_r,
                    body_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.ADD,
                )
                with Locations((0, 0, body_h)):
                    Cone(
                        bead_r,
                        0.0,
                        RIB_TAPER,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.ADD,
                    )

    # Lead-in chamfer at every mouth, cut as a boolean 45-deg cone/frustum. We
    # deliberately avoid OCC's fillet op here: filleting a *ribbed* mouth is
    # unreliable, and a failed fillet corrupts the builder so every later fillet
    # fails too (a silent cascade). A boolean cut can't fail that way, and a
    # chamfer on a horizontal top edge is the house style anyway. The ribs fade
    # out below the chamfer zone, so it only bevels the clean valley rim.
    for d, x, y in bores:
        r = ribbed_valley_r(d) if ribbed else (d + clearance - undersize_frac * d) / 2
        with Locations((x, y, top_z - BORE_MOUTH_CHAMFER)):
            Cone(
                r,
                r + BORE_MOUTH_CHAMFER,
                BORE_MOUTH_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    for af, x, y in hex_bores or []:
        rc = (af + HEX_SLIP) / 3**0.5  # hex circumradius, matching the guide socket
        with Locations((x, y, top_z - BORE_MOUTH_CHAMFER)):
            Cone(
                rc,
                rc + BORE_MOUTH_CHAMFER,
                BORE_MOUTH_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )


def create_base(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None = None,
    clearance: float = 0.0,
    ribbed: bool = False,
    rows: list[list[str]] | None = None,
    hole_pos: dict[str, tuple[float, float]] | None = None,
    bore_depth: float = BORE_DEPTH,
    foot_top: float = FOOT_TOP,
    collar_h: float = COLLAR_H,
    label_z: float = WALL_LABEL_Z,
    label_line_h: float | None = None,
) -> Part:
    """A Gridfinity 1x1 base: foot + body stepping to a collar, with drill bores.

    ``bores`` are round holes ``(diameter, x, y)``. ``hex_bores`` are hex
    sockets ``(across_flats, x, y)`` for hex-shank bits -- the shank drops into
    the socket and any wider head above just rests on the top face, so leave
    clearance around a hex position for the head diameter.

    ``rows`` (hole keys per row, biggest row first) with ``hole_pos``
    (``{key: (x, y)}``) engrave the size legend into all four body walls, each
    ordered to read correctly from its own side, so the sizes read from any side.

    ``clearance`` is a diametral allowance (mm) added to every round bore so the
    bit drops in freely. FDM prints small vertical holes 0.1-0.3 mm *under* the
    modelled size, so a bore cut at exactly the nominal diameter ends up a tight
    press fit; a modest positive clearance restores a slip fit. Hex sockets are
    unaffected -- their across-flats already carries its own fit allowance.

    ``ribbed`` relieves each round bore and restores ``RIB_COUNT`` rounded ribs
    whose contact edge sits ``RIB_GRIP`` inside it -- one absolute interference
    for every size, which works because the ribs are identical compliant beads
    rather than bumps scaled to the bore. They grip only the bottom
    ``RIB_ZONE_H`` (the plain shank), and taper out near the top as a lead-in. Ribbed bores need more room, so a
    tightly packed layout may need re-spacing.

    ``bore_depth`` is how far every hole is sunk below the top face. The default
    swallows a full-length drill; a set of *short* bits wants a shallower bore so
    each bit still stands proud enough to pinch (see ``drill_storage_hex``).

    ``foot_top`` (shoulder the cover seats on) and ``collar_h`` set how tall the
    base is; together they are its total height, which the defaults put at 42 mm
    (6U). Shallow bores don't need all that depth under them, so a short-bit
    holder can drop to a smaller whole Gridfinity unit -- but keep ``foot_top``
    tall enough for the wall legend and leave the collar comfortably above
    ``SNAP_Z`` so the snap groove isn't at its rim. ``label_z`` / ``label_line_h``
    re-centre and tighten that legend for a shortened body; the defaults suit the
    standard 24 mm one.

    Every hole mouth (round *and* hex) gets a lead-in fillet of ``BORE_MOUTH_CHAMFER``.
    """
    total_h = foot_top + collar_h
    with BuildPart() as base:
        add(_gridfinity_foot())

        # Full-width body from the pad top up to the shoulder.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(PAD, PAD, CORNER_R)
        extrude(amount=foot_top - BASE_H)
        # Leave the body top a flat shoulder (no chamfer) so the cover's bottom
        # rim seats flush on it. The cover carries the matching bottom chamfer
        # (COVER_SEAT_CH) so it clears the body edge instead of overhanging it.

        # Collar that plugs into the cover.
        with BuildSketch(Plane.XY.offset(foot_top)):
            RectangleRounded(COLLAR_W, COLLAR_W, COLLAR_R)
        extrude(amount=collar_h)
        # Snap groove around the collar (mates with the cover's internal bead).
        add(
            _snap_ring(COLLAR_W, COLLAR_R, foot_top + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # Sink the graduated drill bores + hex socket and round every mouth.
        cut_holes(bores, hex_bores, clearance, ribbed, total_h, bore_depth)

        # Chamfer the collar's top outer rim (softer top edge + a lead-in for the
        # cover) via a boolean cut -- robust, unlike the flaky fillet op.
        add(
            _rim_chamfer_tool(COLLAR_W, COLLAR_R, total_h, BASE_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )

        # Engrave the size legend into the body walls (all four sides).
        if rows and hole_pos:
            _engrave_row_legend(rows, hole_pos, label_z, label_line_h)
    return base.part


def create_cover(
    label: str,
    cover_h: float = COVER_H,
    label_size: float = LABEL_SIZE,
    label_z: float = LABEL_Z,
    label_horizontal: bool = False,
) -> Part:
    """A tall rounded-square cover with a pillow top and an engraved label.

    ``cover_h`` sets the wall height; pass ``cover_height_for(max_drill_len)`` to
    size a cover to a specific drill set (the default clears ``MAX_DRILL_LEN``).

    ``label_size`` / ``label_z`` set the glyph height and the vertical centre of
    the engraving. The defaults suit a tall cover; a short one must move the
    label down (and usually shrink it) or it lands off the part. ``label`` may
    contain newlines -- two short lines fit a 42 mm face where one long one
    doesn't.

    The label reads *up* the face by default, which is what a tall tube wants: a
    long word has the whole cover height to run along. ``label_horizontal`` turns
    it a quarter so it reads across the face instead -- on a short cover that is
    the only way to get a decent glyph size, since the face is then wider than it
    is tall.
    """
    with BuildPart() as cover:
        with BuildSketch():
            RectangleRounded(COVER_W, COVER_W, CORNER_R)
        extrude(amount=cover_h)
        # Round the top over into a pillow.
        fillet(cover.edges().group_by(Axis.Z)[-1], TOP_FILLET)
        # Chamfer the bottom outer edge so the open rim seats flush on the flat
        # base shoulder rather than overhanging the body edge (the cover is a
        # touch wider than the body). Doubles as elephant-foot relief, since the
        # cover prints open-end-down.
        chamfer(cover.edges().group_by(Axis.Z)[0], COVER_SEAT_CH)

        # Hollow: a single uniform bore (no step), open bottom to the solid cap.
        with BuildSketch():
            RectangleRounded(INNER_W, INNER_W, INNER_R)
        extrude(amount=cover_h - CAP_H, mode=Mode.SUBTRACT)
        # Small internal fillet where the bore ceiling meets the walls: relieves
        # stress at the cap join and eases the overhang printed under the cap.
        ceiling = cover.edges().filter_by_position(
            Axis.Z, cover_h - CAP_H, cover_h - CAP_H
        )
        if ceiling:
            fillet(ceiling, CAP_FILLET)
        # Snap bead: a chamfered (ramped) ridge just inside the opening that
        # slides on gently and clicks into the groove on the base collar.
        add(_snap_bead_ring(INNER_W, INNER_R, SNAP_Z))

        # Engraved label on the +Y flat face -- reading up it, or across it when
        # ``label_horizontal``. The glyphs are cut into the wall (durable, can't
        # snag or shear off), shallower than the wall, and their mouths chamfered
        # so they read crisply, print without a square overhang on the vertical
        # wall, and take a paint-fill. In both cases the in-plane x_dir is the
        # reading direction as seen from *outside* the cover (looking in -Y, that
        # is world -X across / world +Z up), so the text never comes out mirrored.
        text_plane = Plane(
            origin=(0, COVER_W / 2, label_z),
            x_dir=(-1, 0, 0) if label_horizontal else (0, 0, 1),
            z_dir=(0, 1, 0),
        )
        with BuildSketch(text_plane):
            Text(label, font_size=label_size)
        extrude(amount=-LABEL_DEPTH, mode=Mode.SUBTRACT)
        # Chamfer the engraved mouths: the glyph edges lying on the face, keeping
        # only the short ones so the cover's long face-boundary edges are left
        # alone. Best-effort -- the engraving stands on its own if it fails.
        mouth = (
            cover.edges()
            .filter_by_position(Axis.Y, COVER_W / 2, COVER_W / 2)
            .filter_by(lambda e: e.length < 30.0)
        )
        if mouth:
            try:
                chamfer(mouth, LABEL_CHAMFER)
            except Exception:
                pass
    # Print orientation: flip the cover upside down (pillow top on the bed, open
    # mouth up) and re-seat on z=0 so it exports in the pose it prints in.
    part = Rotation(180, 0, 0) * cover.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


def create() -> Compound:
    """Full set: three labelled square covers with two Gridfinity bases."""
    covers = []
    for label, x in [("Metal", -52), ("Stone", 0), ("Wood", 52)]:
        c = create_cover(label)
        c.label = f"cover_{label.lower()}"
        c.color = COVER_COLOR
        covers.append(Pos(x, 30, 0) * c)

    bores9, _, rows9, pos9 = layout_bores(DEMO_DIAMS_SMALL)
    base9 = create_base(bores9, ribbed=True, rows=rows9, hole_pos=pos9)
    base9.label = "base_9_bore"
    base9.color = BASE_COLOR
    bores4, _, rows4, pos4 = layout_bores(DEMO_DIAMS_LARGE)
    base4 = create_base(bores4, ribbed=True, rows=rows4, hole_pos=pos4)
    base4.label = "base_4_bore"
    base4.color = BASE_COLOR

    return Compound(
        label="drill_storage_gridfinity",
        children=[
            *covers,
            Pos(-26, -30, 0) * base9,
            Pos(26, -30, 0) * base4,
        ],
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_storage_gridfinity")


if __name__ == "__main__":
    main()
