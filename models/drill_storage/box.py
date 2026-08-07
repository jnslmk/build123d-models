"""The Gridfinity base/cover engine every drill holder in this package is cut from.

Not a model -- the shared geometry, constants and packers. A tool set supplies a
drill list and a label and gets a finished holder back; nothing here knows about
a particular one.

Two-part telescoping holder: a bored base and a tall labelled cover that
friction-fits over it, on a **1x1 Gridfinity foot** so the holder drops into any
Gridfinity baseplate.

* Base  -- 1x1 Gridfinity footprint (41.5 mm pad, standard 0.7/1.8/1.9 mm foot
  profile), 42 mm tall (6U). A 41.5 mm body -- ``BODY_W``, the pad and the
  cover's width alike, so the assembly has no lip at the seam -- steps down to a
  35 mm collar that plugs into the cover; graduated drill bores are sunk from the
  top face. The three drill sets do not use this: they are two-material
  (``shell`` + ``insert``), and the hex-bit boxes are two-material too
  (``drill_storage.hex``), so ``create_base`` survives as the one-material
  baseline the split replaced.
* Cover -- 41.5 mm rounded square (the pad, flush with the body), 123 mm tall,
  pillow-rounded closed top, open bottom that snaps over the base collar. The
  material name is engraved (with chamfered mouths) up one flat face. Every
  variant shares it.

Nothing on either part reaches outside the 41.5 mm pad, at any height. That is
the whole envelope Gridfinity gives a 1x1 -- the 0.5 mm held back from the 42 mm
pitch is the gap to the next bin -- so an assembled holder sits in a baseplate
cell beside another bin, cover and all.

The cover height is derived so the *assembled* holder (cover top above the
baseplate) is a whole number of Gridfinity Z units (147 mm = 21U) and encloses
a drill up to ``MAX_DRILL_LEN`` (132 mm) standing on the bore floor.

Printed standing (cover) / bores-up (base) in PETG, no supports. The base sits
in a Gridfinity baseplate; the cover is a free lid.
"""

import math
import sys
from collections.abc import Mapping, Sequence

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Circle,
    FontStyle,
    Locations,
    Mode,
    Part,
    Plane,
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

from ..lib.edges import chamfer_edge

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
# The cover is one Gridfinity pad, exactly like the body. Both numbers below are
# now *given* -- the outer by the standard, the bore by the joint -- and the wall
# is what falls out between them. That is the opposite of how this used to read,
# and the inversion is the point:
#
#   was:  COVER_W 42.0 (the grid pitch) -> COVER_WALL 1.2 -> INNER_W 39.6
#   now:  COVER_W 41.5 (the pad)  and  INNER_W 39.6  ->  COVER_WALL 0.95
#
# Taking the 0.5 mm out of the *wall* rather than the bore is deliberate. INNER_W
# is the joint: COLLAR_W is derived from it, and the shell and cartridge from
# COLLAR_W, so moving it re-cuts the snap fit and orphans every shell and cover
# already printed -- in both directions. A new 39.1 bore will not go over an old
# 39.2 collar at all, and an old 39.6 cover over a new 38.7 collar has 0.9 mm of
# slip against a 0.45 mm bead, which is no detent left. Freezing INNER_W costs
# 0.25 mm of wall; moving it costs the shelf.
COVER_W = PAD  # 41.5 -- one Gridfinity pad, flush with the body (see BODY_W)
INNER_W = 39.6  # frozen: the bore every collar this package has ever cut plugs
#                 into. Not derived from COVER_WALL any more -- it outranks it.
COVER_WALL = (COVER_W - INNER_W) / 2  # 0.95 -- what is left, and it is enough:
#                 above MIN_WALL (0.8), and a mouth that flexes more easily over
#                 the snap bead than the old 1.2 did, which this joint wants --
#                 SNAP_PROTRUSION was already trimmed once because the cover
#                 fought going on.
CAP_H = 3.0  # solid rounded cap at the top
TOP_FILLET = 4.0
CAP_FILLET = 1.5  # inner fillet where the bore ceiling meets walls
MOUTH_CH = 0.3  # lead-in on the *inner* rim of the open end (see create_cover)
# A true inward offset of the outer profile, so the wall is COVER_WALL at the
# corners too. It was a flat 2.0, which made the corners the *thinnest* part of
# the tube rather than the thickest -- 0.87 mm against a 1.2 mm flat at the old
# width, and 0.52 mm at this one, which is under MIN_WALL and under two
# perimeters. The same "offset, don't re-guess" rule CAVITY_R follows against
# COLLAR_W.
#
# It costs corner clearance and can afford to: the bore still stands 0.469 mm
# outside the collar on the diagonal, down from 0.904 at the old flat 2.0 but
# still more than twice the 0.200 mm the flats carry. Nothing binds, because the
# corners are not the fit -- the flats are, at exactly SLIP/2, and that is where
# the snap bead engages. Held in checks.py rather than left to this note.
INNER_R = CORNER_R - COVER_WALL  # 3.05
LABEL_SIZE = 13.0
LABEL_Z = 45.0
LABEL_DEPTH = 0.5  # engrave depth into the flat face (< COVER_WALL, no punch-through)
# That leaves COVER_WALL - LABEL_DEPTH = 0.45 mm of wall behind every glyph, under
# the package's own MIN_WALL (0.8, checks.py). Accepted, deliberately, and here is
# the whole argument so nobody has to re-derive it:
#
# * There is no room to satisfy both, and less than there was. COVER_WALL is no
#   longer a knob at all -- it is COVER_W minus INNER_W, and both of those are
#   fixed by something outside this file (the Gridfinity pad, and a joint that
#   must stay interchangeable). An 0.8 mm residual would need LABEL_DEPTH = 0.15,
#   which is a third of `printed-text`'s 0.5 mm floor for a legible engrave, on a
#   *vertical* wall crossing the layer lines -- the orientation that skill says to
#   spend extra depth on, not save it. So 0.5 is the floor, and the residual is
#   whatever is left over.
# * 0.45 mm is still more than one 0.4 mm perimeter, which is the number that
#   actually matters here: the glyph floor still slices as material rather than
#   as a hole. It was 0.6 before, so this trade cost 0.15 mm of an allowance that
#   was already a stated exception -- not a new category of risk.
# * MIN_WALL's own stated reason does not reach here. It is the floor for a wall
#   that has to *be* something -- a free-standing rib, or a bore that closes up
#   under two extrusions. This is the floor of a blind pocket with a full 0.95 mm
#   of wall all around it, and its worst case is that the slicer lays one 0.4 mm
#   perimeter instead of a filled 0.45: a translucent patch behind a label, on a
#   lid, which is cosmetic and arguably an improvement.
# * It is nowhere near the load. What flexes on this part is the mouth, over the
#   snap bead at SNAP_Z = 6 mm from the opening. LABEL_Z is 45, so the nearest
#   glyph edge is ~40 mm of full-section tube away from anything that deflects.
#
# So: not a defect, a priced trade. What would make it a defect is LABEL_DEPTH
# rising or the residual dropping under a perimeter, so the pair is pinned in
# `checks.py` by `check_wall_budget` -- named there as a stated exception to
# MIN_WALL rather than compared against it, since it legitimately fails that
# comparison.
# Bevel on the engraved glyph mouths -> a continuous V-groove wall, no step. It
# has to stay *under* LABEL_DEPTH: a bevel as deep as the pocket it is cut into
# is degenerate, and OCC answers by refusing the whole edge set (this is the
# all-or-nothing failure `build123d-geometry-ops` describes). At the old 0.6 mm
# depth 0.5 was merely near-full; at 0.5 it was exactly full, and the Wood cover
# -- the one variant whose label chamfer OCC had always accepted -- started
# skipping it. Sized off the depth rather than typed as a literal so the two
# cannot drift into that state again.
LABEL_CHAMFER = LABEL_DEPTH - 0.15  # 0.35

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
# The body, the cover and the Gridfinity pad are all one number. They were not
# always: the body took PAD (41.5) while the cover took GRID (42.0), and an
# assembled holder stepped out by 0.25 mm per side at the seam -- a lip you can
# feel all the way up a 109 mm cover, and a silhouette 0.5 mm wider than the base
# under it. BODY_W exists to make the agreement structural rather than a
# coincidence of two literals, and 41.5 is the right value for both because the
# pad is the *whole* envelope Gridfinity gives a 1x1: the 0.5 mm it holds back
# from the 42 mm pitch is the gap between neighbours, and anything that spends it
# stops sitting next to another bin. So the holder is one flush rounded square
# from the foot to the top of the cover, and it is a well-behaved bin at every
# height rather than only below 4.4 mm.
BODY_W = PAD  # 41.5 -- the pad, and COVER_W too, so the two are flush
FOOT_TOP = 24.0  # top of the full-width body (cover seats here)
COLLAR_W = INNER_W - SLIP  # collar is a close slip fit inside the cover bore
COLLAR_R = 3.5
COLLAR_H = 18.0
BASE_TOTAL_H = FOOT_TOP + COLLAR_H  # 42 mm (6U)
# Cover bottom-edge chamfer. With BODY_W == COVER_W the cover no longer overhangs
# the body, so this is no longer clearance -- it is elephant-foot relief on the
# rim the cover prints on, plus a hair of lead-in onto the shoulder for the
# 0.1-0.2 mm the two parts really differ by (different filaments, different
# shrinkage -- a printed PETG cover measured 41.9 against an ASA shell on
# nominal). Trimmed from 0.4 because it and MOUTH_CH are now cut from a 0.95 mm
# wall, not a 1.2: at 0.4 the flat rim left to seat on would be 0.25 mm, under a
# single perimeter. At 0.2 it is 0.45, which is what the old 1.2 mm wall left
# anyway (0.5). checks.py holds the rim rather than trusting the arithmetic.
COVER_SEAT_CH = 0.2
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
# (There is no WALL_LABEL_MAX_LAT constant. Keeping the numbers off the rounded
# corners is ``engrave_row_legend``'s job and it works the limit out per label,
# from that label's own width -- a single constant cannot, since "1.5" needs
# more room than "8".)
# How far above and below WALL_LABEL_Z the block of lines may reach. The body
# wall runs BASE_H (4.4) to FOOT_TOP (24); this keeps the glyphs off both ends,
# the foot's chamfer below and the cover's seat above.
WALL_LABEL_BAND = 7.5


def wall_label_line_h(n_lines: int) -> float:
    """Row pitch for ``n_lines`` of legend, so the block still lands on the wall.

    Three lines get the comfortable default -- the pitch every set built from
    ``pack_rows`` has always used, and this returns exactly that for n <= 3 so
    none of them moves. A fourth line only appears under a free layout, whose
    labels are packed rather than read off rows, and it has to be squeezed: at
    the default 5.6 mm pitch the bottom line lands on the Gridfinity foot.
    """
    default = WALL_LABEL_SIZE + 1.6
    if n_lines < 2:
        return default
    return min(default, 2 * WALL_LABEL_BAND / (n_lines - 1))


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


# The default holder's assembled envelope is 147 mm (21U). It is not a constant:
# ``cover_height_for`` derives it from the numbers above and hands back the cover
# height, and a second copy of that arithmetic here would only be one edit away
# from disagreeing with the one that is actually built.
COVER_H = cover_height_for(MAX_DRILL_LEN)  # 123 mm default cover (147 - FOOT_TOP)

# --- Bores --------------------------------------------------------------------
# A bore here is plain: a cylinder at the bit's diameter plus a clearance, with a
# lead-in chamfer at its mouth. Nothing in this engine grips a bit any more.
#
# It used to. Every round bore carried three compliant ribs standing into it at a
# measured diametral interference, and that machinery -- the grip law, its
# small-bore compensation table, and the printed coupons that settled both -- was
# the largest thing in this file. It is gone: the three drill sets are now
# two-material, the TPU insert is the spring, and a ribbed PETG bore holds nothing
# that a ``LAND_FIT`` in ``config.py`` does not hold better. ``docs/design-notes.md``
# keeps the history, because the lesson (a rib welded to a wall over its full
# width is not a spring, and no interference number rescues it) outlives the code.
#
# What is left is the engine's own drop-in socket: a 1/4" driver bit is held by
# nothing but its own weight and the socket's flats. Nothing cuts one any more --
# ``drill_storage.hex`` has joined the two-material family, and a hex bit now
# sits in a TPU land like any other hex shank -- but the machinery stays, as the
# one-material baseline the split is measured against.
HEX_SLIP = 0.05  # across-flats clearance on the guide socket -- drops straight in


def plain_bore_r(d: float, clearance: float = 0.0) -> float:
    """Cut radius of a plain bore for a bit of diameter ``d`` -- its footprint for
    layout/packing. The default packer footprint, and the one ``cut_holes`` cuts.

    A two-material set passes its own instead (``config.relieved_bore_r``): what
    has to be packed is the widest thing actually cut at that position, and in the
    TPU insert that is the relieved bore above the grip land, not the nominal bit.
    """
    return (d + clearance) / 2


BASE_COLOR = Color(0.62, 0.64, 0.67)
COVER_COLOR = Color(0.93, 0.93, 0.92)


def gridfinity_foot() -> Part:
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


def create_body(foot_top: float = FOOT_TOP) -> Part:
    """The full-width body: from the Gridfinity pad top up to the cover seat.

    One function rather than three copies of the same two sketches, because all
    three bases in this package (``create_base``, ``shell.create_shell_for``,
    ``hex.base``) grow the same body and used to each spell it out -- which is
    how the pad-versus-cover width mismatch would have had to be fixed three
    times and stayed fixed in only two.

    ``BODY_W`` wide -- which is the pad the foot below already ends at, so the
    two meet with no step, and is the cover's width too, so the assembled holder
    is one flush silhouette. All three of those being the same number is the
    whole point of ``BODY_W``; see it for why 41.5 and not 42.

    The top is left a flat shoulder, no chamfer, so the cover's chamfered bottom
    rim lands flat-on-flat on it (``create_cover``'s ``COVER_SEAT_CH``). Both
    ``checks.py`` files name that as a stated exception to the chamfer-everything
    rule rather than quietly omitting it.
    """
    with BuildPart() as body:
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(BODY_W, BODY_W, CORNER_R)
        extrude(amount=foot_top - BASE_H)
    return body.part


def snap_ring(size: float, corner_r: float, z: float, bead_r: float) -> Part:
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


def snap_bead_ring(
    size: float,
    corner_r: float,
    z: float,
    protrusion: float = SNAP_PROTRUSION,
    lead_in: float = SNAP_LEAD_IN,
    back: float = SNAP_BACK,
    tip_flat: float = SNAP_TIP_FLAT,
    outward: bool = False,
) -> Part:
    """A chamfered (asymmetric) bead ring for a smooth-engaging snap fit.

    Instead of a half-round bump, the cross-section is a quad that protrudes
    ``protrusion`` from the wall and rises with a long, gentle ``lead_in`` ramp
    on the insertion (lower) side and a shorter, steeper ``back`` retention face
    on the upper side, with a small ``tip_flat`` at the tip. Swept around the
    rounded-square perimeter of side ``size`` at height ``z``; union it into the
    cover so the cover slides on progressively yet still detents into the collar
    groove. The gentle ramp is the "chamfer that slides on"; the round groove
    (``snap_ring``) forgivingly receives it.

    ``outward=True`` mirrors the tip so the bead stands *out* of a plug rather
    than *into* a bore -- the same profile seen from the other side of the joint,
    for a compliant male part that detents into a groove in a rigid female one
    (``drill_storage.insert``). The ramp stays on the lower side either way,
    because both parts are inserted downward.

    The defaults reproduce the cover's bead exactly, so existing callers are
    unaffected.
    """
    with BuildSketch(Plane.XY.offset(z)) as outline:
        RectangleRounded(size, size, corner_r)
    path = outline.faces()[0].outer_wire()
    reach = -protrusion if outward else protrusion
    x_wall = size / 2  # bead base sits on the bore wall ...
    x_tip = size / 2 - reach  # ... and its tip stands off it, into the joint
    # Local sketch coords on Plane.XZ: x -> radius, y -> height (matches snap_ring).
    profile = [
        (x_wall, z - lead_in),  # bottom of the gentle insertion ramp
        (x_tip, z - tip_flat / 2),  # tip, lower
        (x_tip, z + tip_flat / 2),  # tip, upper
        (x_wall, z + back),  # top of the steeper retention face
    ]
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ):
            Polygon(*profile, align=None)
        sweep(path=path)
    return ring.part


def rim_chamfer_tool(width: float, corner_r: float, top_z: float, ch: float) -> Part:
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
    footprint_r=plain_bore_r,
    half_w: float = COLLAR_W / 2,
    corner_r: float = COLLAR_R,
    hole_wall: float = HOLE_WALL,
    wall_clearance: float = WALL_CLEARANCE,
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

    ``drill_diams`` are round bores; each is packed by its ``footprint_r(d)``
    and keyed by its ``{d:g}`` size string.
    ``hex_tools`` are ``(label, across_flats, footprint_r)`` for hex-shank bits:
    the shank drops into an ``across_flats`` socket while ``footprint_r`` is the
    radius reserved during packing (a countersink's head is wider than its socket;
    a plain hex tool's is just its circumradius). ``swap`` optionally exchanges the
    positions of two keys after packing (e.g. move a countersink out to a row edge
    and give the centre slot to a same-size drill).

    ``footprint_r`` is the *cut* radius each drill really occupies, which is not
    always its nominal radius: the two-material sets pass
    ``config.relieved_bore_r``, because what has to be packed is the relieved
    bore the TPU insert really cuts, not the bit that goes in it. ``half_w`` /
    ``corner_r`` / ``hole_wall`` / ``wall_clearance`` are the envelope packed
    into; the defaults are the standard collar, so an existing caller sees no
    change.

    Returns ``(drill_bores, hex_bores, rows, hole_pos)``.
    """
    hex_tools = hex_tools or []
    items = [(f"{d:g}", footprint_r(d)) for d in drill_diams]
    items += [(label, foot_r) for label, _af, foot_r in hex_tools]
    pos, rows = pack_rows(items, half_w, corner_r, hole_wall, wall_clearance)
    for a, b in swap or []:
        pos[a], pos[b] = pos[b], pos[a]
    drill_bores = [(d, pos[f"{d:g}"][0], pos[f"{d:g}"][1]) for d in drill_diams]
    hex_bores = [(af, pos[label][0], pos[label][1]) for label, af, _foot_r in hex_tools]
    return drill_bores, hex_bores, rows, pos


# Outward-normal, upright (+Z up) text frames for each body face: (origin, x_dir,
# z_dir) as a function of the in-face lateral offset and height. Used to engrave
# the size legend into the base body's four walls.
def face_frame(face: str, lateral: float, z: float):
    # BODY_W, not PAD: this plane is the wall the glyphs are cut *from*, and the
    # engrave runs inward from it. Left at the pad it would sit BODY_STEP inside
    # the real wall, and every number would come out as a sealed void behind
    # 0.25 mm of skin rather than as an engraving.
    half = BODY_W / 2
    return {
        "N": ((lateral, half, z), (-1, 0, 0), (0, 1, 0)),
        "S": ((lateral, -half, z), (1, 0, 0), (0, -1, 0)),
        "E": ((half, lateral, z), (0, 1, 0), (1, 0, 0)),
        "W": ((-half, lateral, z), (0, -1, 0), (-1, 0, 0)),
    }[face]


def engrave_row_legend(
    rows: Sequence[Sequence[str]],
    pos: Mapping[str, tuple[float, float]],
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
    flat_half = BODY_W / 2 - CORNER_R  # numbers must stay on the flat wall face

    def engrave(text: str, face: str, lateral: float, z: float) -> None:
        # Keep the (centre-aligned) glyphs clear of the rounded corners.
        limit = flat_half - 0.31 * WALL_LABEL_SIZE * len(text) - 0.3
        lateral = max(-limit, min(limit, lateral))
        origin, x_dir, z_dir = face_frame(face, lateral, z)
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


def hex_mouth_tool(r: float, x: float, y: float, top_z: float, ch: float) -> Part:
    """A subtractable lead-in for a hex socket mouth, hex-shaped all the way round.

    A lofted hex frustum, from circumradius ``r`` at ``top_z - ch`` out to
    ``r + ch`` at ``top_z``. Subtract it from the part after the socket is cut.

    It is a frustum and not a cone because the bevel has to *start on the socket
    wall*, and a circle through the hexagon's vertices does not lie on that wall
    anywhere except at the six vertices themselves.

    What the cone this replaced got wrong was not that it under-cut the flats --
    it over-cut them. ``Cone(rc, rc + ch, ch)`` begins at the circumradius, but
    along a flat's normal the socket wall is only an apothem away
    (``rc * cos(30)``), a full ``rc - apothem`` = 0.51 mm further in. So the cut
    opened to 3.78 mm the instant it began, where the wall below it stood at
    3.28: a 0.52 mm horizontal ledge encircling the mouth, and *that* ledge was
    the sharp edge -- 6 per socket, one per flat, each one hex-side long. Not a
    missing bevel, a step. Measured on this base, the cone opened a flat to
    3.7916 mm at z = 27.21 where the wall below was 3.2750.

    So the frustum cuts strictly *less* than the cone did (0.51-0.61 mm less
    along a flat at every height through the mouth); at the six corners the two
    are identical to 4 dp, since that is where the circle and the hexagon touch.
    The mouth ends up bevelled at 45 deg at the corners and ~40 deg to vertical
    across the flats, which is what growing the *circumradius* by ``ch`` buys and
    is the established shape here -- ``shell.hex_guide_tool`` and
    ``insert.hex_mouth_tool`` are the same loft, so all three stay comparable.

    Nothing here is an overhang: the base prints bores-up, and a mouth that
    widens toward +Z takes material away as it rises, so every layer lands fully
    on the one beneath it. Self-supporting by construction, at any bevel angle.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(top_z - ch)):
            with Locations((x, y)):
                RegularPolygon(r, 6)
        with BuildSketch(Plane.XY.offset(top_z)):
            with Locations((x, y)):
                RegularPolygon(r + ch, 6)
        loft(ruled=True)
    return tool.part


def cut_holes(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None,
    clearance: float,
    top_z: float,
    bore_depth: float,
    undersize_frac: float = 0.0,
) -> None:
    """Sink drill bores + hex sockets into the active part and chamfer every mouth.

    Call this inside a ``with BuildPart()`` block; it operates on the active
    builder.

    Round ``bores`` are ``(diameter, x, y)`` sunk ``bore_depth`` down from
    ``top_z``, sized ``clearance`` (mm) over and ``undersize_frac`` (a fraction of
    the bit) under -- the fractional part compensates the way small holes print
    tighter than large ones.

    ``hex_bores`` are ``(across_flats, x, y)``, cut ``HEX_SLIP`` over so a shank
    drops straight in and is only kept from spinning. Every mouth gets a lead-in
    of depth ``BORE_MOUTH_CHAMFER``, cut as a boolean (robust; see the note
    below) -- a 45-deg cone at a round bore, and a lofted hex frustum
    (``hex_mouth_tool``) at a hex socket, which is the only shape whose bevel
    starts on the socket wall instead of outside it.
    """
    floor_z = top_z - bore_depth
    for d, x, y in bores:
        with Locations((x, y, floor_z)):
            Cylinder(
                plain_bore_r(d, clearance - undersize_frac * d),
                bore_depth + 1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    for af, x, y in hex_bores or []:
        with BuildSketch(Plane.XY.offset(top_z)) as hex_sk:
            with Locations((x, y)):
                RegularPolygon((af + HEX_SLIP) / 3**0.5, 6)
        # Pass the sketch explicitly: inside a helper the implicit "pending
        # sketch" lookup that a bare extrude() relies on doesn't resolve.
        extrude(hex_sk.sketch, amount=-bore_depth, mode=Mode.SUBTRACT)

    # Lead-in chamfer at every mouth, cut as a boolean 45-deg cone/frustum. We
    # deliberately avoid OCC's fillet op here: a failed fillet corrupts the
    # builder so every later fillet fails too (a silent cascade). A boolean cut
    # can't fail that way, and a chamfer on a horizontal top edge is the house
    # style anyway.
    for d, x, y in bores:
        r = plain_bore_r(d, clearance - undersize_frac * d)
        with Locations((x, y, top_z - BORE_MOUTH_CHAMFER)):
            Cone(
                r,
                r + BORE_MOUTH_CHAMFER,
                BORE_MOUTH_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    # A hex mouth gets a *hex* frustum, never a cone -- see ``hex_mouth_tool``.
    for af, x, y in hex_bores or []:
        rc = (af + HEX_SLIP) / 3**0.5  # hex circumradius, matching the guide socket
        add(
            hex_mouth_tool(rc, x, y, top_z, BORE_MOUTH_CHAMFER),
            mode=Mode.SUBTRACT,
        )


def create_base(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None = None,
    clearance: float = 0.0,
    rows: list[list[str]] | None = None,
    hole_pos: dict[str, tuple[float, float]] | None = None,
    bore_depth: float = BORE_DEPTH,
    foot_top: float = FOOT_TOP,
    collar_h: float = COLLAR_H,
    label_z: float = WALL_LABEL_Z,
    label_line_h: float | None = None,
) -> Part:
    """A Gridfinity 1x1 base: foot + body stepping to a collar, with plain bores.

    The one-material holder, and the shape of every holder in this package until
    the drill sets went two-material. Nothing cuts from it any more -- a drill
    set wants ``shell`` + ``insert``, and the hex-bit boxes are two-material too
    (``drill_storage.hex``) -- but it stays as the engine's documented baseline,
    and the collar profile it introduced is what every shell still plugs into.

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

    ``bore_depth`` is how far every hole is sunk below the top face. The default
    swallows a full-length drill; a set of *short* bits wants a shallower bore so
    each bit still stands proud enough to pinch.

    ``foot_top`` (shoulder the cover seats on) and ``collar_h`` set how tall the
    base is; together they are its total height, which the defaults put at 42 mm
    (6U). Shallow bores don't need all that depth under them, so a short-bit
    holder can drop to a smaller whole Gridfinity unit -- but keep ``foot_top``
    tall enough for the wall legend and leave the collar comfortably above
    ``SNAP_Z`` so the snap groove isn't at its rim. ``label_z`` / ``label_line_h``
    re-centre and tighten that legend for a shortened body; the defaults suit the
    standard 24 mm one.

    Every hole mouth (round *and* hex) gets a lead-in chamfer of
    ``BORE_MOUTH_CHAMFER`` -- a cone at a round bore, a hex frustum at a socket,
    so the bevel starts on the socket wall rather than 0.5 mm outside it (which
    is what left a sharp ledge round every hex mouth; see ``hex_mouth_tool``).
    """
    total_h = foot_top + collar_h
    with BuildPart() as base:
        add(gridfinity_foot())

        # Full-width body from the pad top up to the shoulder -- BODY_W wide,
        # flush with the cover, and left a flat shoulder on top for it to seat
        # on. See ``create_body``.
        add(create_body(foot_top))

        # Collar that plugs into the cover.
        with BuildSketch(Plane.XY.offset(foot_top)):
            RectangleRounded(COLLAR_W, COLLAR_W, COLLAR_R)
        extrude(amount=collar_h)
        # Snap groove around the collar (mates with the cover's internal bead).
        add(
            snap_ring(COLLAR_W, COLLAR_R, foot_top + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # Sink the graduated drill bores + hex socket and round every mouth.
        cut_holes(bores, hex_bores, clearance, total_h, bore_depth)

        # Chamfer the collar's top outer rim (softer top edge + a lead-in for the
        # cover) via a boolean cut -- robust, unlike the flaky fillet op.
        add(
            rim_chamfer_tool(COLLAR_W, COLLAR_R, total_h, BASE_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )

        # Engrave the size legend into the body walls (all four sides).
        if rows and hole_pos:
            engrave_row_legend(rows, hole_pos, label_z, label_line_h)
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

        # Lead-in at the mouth -- the *inner* rim of the open end, which is the
        # one edge on this part that ``chamfer(edges().group_by(Axis.Z)[0])``
        # above can never reach: it runs before the hollow is cut, so the only
        # bottom rim in existence then is the solid outer rectangle. Left alone,
        # the mouth ships as a raw square rim on the edge you handle every time
        # the cover comes off, and as the one mating mouth in the joint with no
        # lead-in at all (part-joints rule 1).
        #
        # Cut as a lofted frustum rather than an OCC chamfer: an edge op on this
        # rim is unreliable next to the snap bead, and a failed one corrupts the
        # builder so every later op fails silently.
        #
        # Sized to the joint, not to taste: it only has to swallow the collar's
        # own half-slip (SLIP / 2 = 0.2 mm of possible misalignment), and the
        # 1.2 mm wall has to pay for it twice over -- COVER_SEAT_CH takes 0.4
        # from the outside, so 0.3 here still leaves 0.5 mm of flat rim to seat
        # on. Do not raise either without raising COVER_WALL.
        with BuildSketch():
            RectangleRounded(
                INNER_W + 2 * MOUTH_CH, INNER_W + 2 * MOUTH_CH, INNER_R + MOUTH_CH
            )
        with BuildSketch(Plane.XY.offset(MOUTH_CH)):
            RectangleRounded(INNER_W, INNER_W, INNER_R)
        loft(ruled=True, mode=Mode.SUBTRACT)

        # Snap bead: a chamfered (ramped) ridge just inside the opening that
        # slides on gently and clicks into the groove on the base collar.
        add(snap_bead_ring(INNER_W, INNER_R, SNAP_Z))

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
        #
        # Deliberately accepted False: OCC refuses this chamfer for Metal and
        # Stone at every length (0.5/0.3/0.15 all fail), and the kernel is
        # chaotic on the edge set ("Ston" chamfers where "Sto" doesn't), so
        # per-glyph calls are no rescue either. Only Wood takes it. The boolean
        # V-groove (lofted ring between the offset glyph and the glyph,
        # subtracted) is the documented fix if paint-fill ever needs it, but at
        # LABEL_SIZE=13 (~9.75 mm glyphs) the bevel is polish -- the 4 mm base
        # wall numbers, where it pays off, are plain engraves.
        mouth = (
            cover.edges()
            .filter_by_position(Axis.Y, COVER_W / 2, COVER_W / 2)
            .filter_by(lambda e: e.length < 30.0)
        )
        if mouth:
            # Snapshot-restore rather than a bare try/except: a failed OCC
            # chamfer leaves the builder corrupted, and this is the last
            # operation before the part is returned.
            chamfer_edge(cover, mouth, LABEL_CHAMFER)
    # Print orientation: flip the cover upside down (pillow top on the bed, open
    # mouth up) and re-seat on z=0 so it exports in the pose it prints in.
    part = Rotation(180, 0, 0) * cover.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part
