"""Geometry assertions for the drill_storage package.

    uv run check drill_storage             # the engine and all three sets
    uv run check drill_storage.wood        # one set, which is much faster
    uv run check drill_storage.hex         # the hex boxes, in their own package
    uv run python -m models.drill_storage.checks

A clearance is invisible in a projection and a 0.3 mm land step does not show up
in an SVG, so everything here is either arithmetic on the config or a point
sample of the solid -- never an eyeball.

The per-set checks are written once and run three times, because the three sets
share every clearance and differ only in what is packed into them. That is also
the thing most worth checking: a set that packs eleven bores into the cartridge
is one bore away from a wall too thin to print, and ``pack_rows`` only warns
about *horizontal* overpacking, so the row pitch is checked here or nowhere.

What this file cannot tell you is whether the grip is right. ``LAND_FIT`` is a
judgement about how hard a drill should be to pull out, and only a printed
cartridge settles it -- see ``config.LAND_EASE`` and ``docs/design-notes.md``.
"""

from __future__ import annotations

import itertools
import math
import sys

from build123d import BuildSketch, GeomType, Part, Text

from ..lib import fits
from ..lib.checks import TOL as TOL
from ..lib.checks import Report as Report
from ..lib.checks import is_periodic_seam
from ..lib.checks import is_solid_at as is_solid_at
from ..lib.checks import sharp_convex_edges
from . import config as c
from . import sets
from .box import (
    BASE_H,
    BODY_W,
    CAP_H,
    CAP_SOLID_LAYERS,
    COLLAR_R,
    COLLAR_W,
    CORNER_R,
    COVER_SEAT_CH,
    COVER_W,
    COVER_WALL,
    MOUTH_CH,
    FOOT_TOP,
    HEIGHT_UNIT,
    INNER_R,
    INNER_W,
    LABEL_CHAMFER,
    LABEL_DEPTH,
    LABEL_SIZE,
    LABEL_Z,
    LAYER_H,
    PAD,
    SLIP,
    SNAP_GROOVE_R,
    SNAP_Z,
    TOP_FILLET,
    WALL_LABEL_SIZE,
    WALL_LABEL_Z,
    cover_height_for,
)
from .freepack import sdf, worst_slack
from .cover import create_cover_for
from .insert import _hex_r, create_insert_for
from .sets import DrillSet
from .base import create_base_for

PROBE = 0.08  # how far either side of a modelled radius we sample for material

# The absolute minimum wall a 0.4 mm nozzle resolves: 2 perimeters. Below this a
# feature does not slice as a wall at all, it merges with its neighbour. The same
# figure is the floor for a *hole*: under two extrusions wide, a bore closes up.
MIN_WALL = 0.8

# Air between two steel tools standing in the tray. Not a printed wall, so it is
# not MIN_WALL: nothing has to slice here, the tools only have to not touch, and
# each is already located by its own socket. Enough to get a hand between them.
TOOL_CLEARANCE = 0.5


def _bore_footprints(s: DrillSet) -> list[tuple[str, float, float, float]]:
    """Every cut bore as ``(key, relieved_radius, x, y)`` -- the real footprint,
    not the nominal tool, which is what has to be packed and walled."""
    items = [(f"{d:g}", c.relieved_bore_r(d), x, y) for d, x, y in s.bores]
    items += [
        (f"hex{af:g}", _hex_r(af, c.RELIEF_FIT), x, y) for af, x, y in s.hex_bores
    ]
    return items


def _land_ease(s: DrillSet, d: float) -> float:
    """The size-dependent ease a set opts into for a bore of diameter ``d``:
    ``config.small_bore_comp`` when the set asks for it, zero otherwise. Every
    check that samples the land must go through this, or it verifies a radius
    the geometry does not cut.
    """
    return c.small_bore_comp(d) if s.small_bore_comp else 0.0


def _print_pose_y(y: float) -> float:
    """Mirror a collar-frame y into the insert's print pose: the pose is the
    collar rotated 180 deg about X, which flips Y (the rounded-square body is
    symmetric, so the shape is unchanged -- only the bore positions move).
    Z needs no helper: the checks name the flipped heights directly.
    """
    return -y


# --- Set-independent: the clearances themselves -------------------------------


def check_fits(r: Report) -> None:
    """Every clearance traces back to a named fit class, not a typed number."""
    r.section("fits")
    press = fits.for_material(fits.PRESS, "tpu")
    r.check(
        c.LAND_FIT == press - c.LAND_EXTRA_GRIP + c.LAND_EASE,
        "LAND_FIT is a press fit in TPU, tightened by LAND_EXTRA_GRIP and eased",
        f"{c.LAND_FIT:.2f} mm = {press:.2f} - {c.LAND_EXTRA_GRIP:.2f} "
        f"+ {c.LAND_EASE:.2f}",
    )
    # The small-bore taper is a calibration knob, so its reading is pinned here
    # like any other fit: 0.10 mm of extra land clearance per mm below 4.0 mm,
    # i.e. +0.30 at 1 mm and nothing at 4 mm and up.
    r.check(
        c.SMALL_BORE_COMP_SLOPE == 0.10 and c.SMALL_BORE_COMP_THRESHOLD == 4.0,
        "the small-bore taper eases the land 0.10 mm per mm below 4.0 mm",
        f"{c.SMALL_BORE_COMP_SLOPE:.2f} mm/mm below {c.SMALL_BORE_COMP_THRESHOLD:g} mm",
    )
    r.check(
        c.HEX_LAND_FIT == press + c.LAND_EASE,
        "HEX_LAND_FIT carries the same ease as the round land",
        f"{c.HEX_LAND_FIT:.2f} mm = {press:.2f} + {c.LAND_EASE:.2f}",
    )
    # The ease is a correction, not a redesign: it must stay well inside the
    # interference it is trimming, or the land stops being a land.
    r.check(
        0.0 < c.LAND_EASE < c.LAND_EXTRA_GRIP,
        "the ease gives back less than the extra grip it trims",
        f"ease {c.LAND_EASE:.2f} of extra grip {c.LAND_EXTRA_GRIP:.2f}",
    )
    r.check(
        c.GUIDE_FIT == fits.for_material(fits.FREE, "asa") + c.GUIDE_UNDERSIZE_COMP,
        "GUIDE_FIT is a free fit in ASA plus the hole undersize FDM prints",
        f"{c.GUIDE_FIT:.2f} mm = {fits.for_material(fits.FREE, 'asa'):.2f} "
        f"+ {c.GUIDE_UNDERSIZE_COMP:.2f}",
    )
    # The guide is cut wider than the bore above it, so a drill entering the
    # cartridge never steps *down* onto an ASA edge on its way through -- the only
    # thing it can touch below the land is air.
    r.check(
        c.GUIDE_FIT > c.RELIEF_FIT,
        "the guide is wider than the cartridge relief above it",
        f"guide {c.GUIDE_FIT:.2f} > relief {c.RELIEF_FIT:.2f} mm",
    )
    # The split only works if the two halves are cut on opposite sides of
    # nominal. A guide that grips, or a land that clears, defeats it silently.
    r.check(
        c.LAND_FIT < 0.0 < c.GUIDE_FIT,
        "the ASA guide clears and the TPU land interferes",
        f"guide {c.GUIDE_FIT:+.2f} (loose) / land {c.LAND_FIT:+.2f} (tight)",
    )
    r.check(
        c.RELIEF_FIT == fits.for_material(fits.SLIDING, "tpu"),
        "RELIEF_FIT is a sliding fit in TPU",
        f"{c.RELIEF_FIT:.2f} mm",
    )
    r.check(
        c.CART_SLIP == fits.for_material(fits.SLIDING, "tpu"),
        "CART_SLIP is a sliding fit in TPU",
        f"{c.CART_SLIP:.2f} mm",
    )
    r.check(
        c.LAND_FIT < c.RELIEF_FIT,
        "the land is tighter than the relief",
        f"land {c.LAND_FIT:.2f} < relief {c.RELIEF_FIT:.2f} mm",
    )


def check_retention(r: Report) -> None:
    """A drill leaves the land at maybe 5-15 N and the cartridge weighs ~0.2 N,
    so the bead is not decoration."""
    r.section("retention")
    r.check(
        c.BEAD_ENGAGEMENT > 0.2,
        "retention bead engages past the cartridge's own slip",
        f"{c.BEAD_ENGAGEMENT:.2f} mm (bead {c.CART_BEAD:.2f}, "
        f"slip/2 {c.CART_SLIP / 2:.2f})",
    )
    r.check(
        c.CART_BEAD <= c.GROOVE_D + TOL,
        "bead tip fits inside the groove that receives it",
        f"bead {c.CART_BEAD:.2f} <= groove depth {c.GROOVE_D:.2f}",
    )
    r.check(
        c.BEAD_LEAD_IN > c.BEAD_BACK,
        "insertion ramp is gentler than the retention face",
        f"lead-in {c.BEAD_LEAD_IN:.1f} vs back {c.BEAD_BACK:.1f} mm",
    )
    r.check(
        c.BEAD_Z + c.BEAD_BACK < c.SHELL_TOTAL_H,
        "bead seats below the base rim",
        f"{c.BEAD_Z + c.BEAD_BACK:.1f} mm",
    )
    # The two things the groove's chamfered profile has to deliver. Neither is
    # visible in a projection and both were wrong when the groove was a
    # half-round pocket: see config's "the groove that receives the bead".
    #
    # The roof is the overhang. This is the arithmetic; check_groove measures
    # the same angle off the built solid, which is the claim that actually
    # matters.
    r.check(
        c.GROOVE_ROOF_OVERHANG <= c.MAX_OVERHANG + TOL,
        "the retention groove's roof is a self-supporting ramp",
        f"{c.GROOVE_ROOF_OVERHANG:.1f} deg from vertical "
        f"({c.GROOVE_D:.2f} mm deep over {c.GROOVE_ROOF_RISE:.2f} mm of rise, "
        f"max {c.MAX_OVERHANG:.0f})",
    )
    # ...and the floor is the fit. The bead's ramp stands proud of the
    # cartridge's slip gap over its upper BEAD_RAMP_H * (1 - slip/2 / bead), and
    # every millimetre of that has to have somewhere to go or the bead seats
    # crushed against the groove's bottom lip instead of dropping into it.
    # GROOVE_FLOOR is derived from the same two numbers, so the two sides agree
    # by construction today; what this catches is GROOVE_FLOOR being trimmed by
    # hand later to buy back collar wall. check_groove walks the built solid.
    ramp_proud = c.BEAD_RAMP_H * (1 - (c.CART_SLIP / 2) / c.CART_BEAD)
    r.check(
        c.GROOVE_FLOOR >= c.BEAD_TIP_FLAT / 2 + ramp_proud - TOL,
        "the groove's floor swallows the whole of the bead's insertion ramp",
        f"floor {c.GROOVE_FLOOR:.2f} mm below BEAD_Z vs "
        f"{c.BEAD_TIP_FLAT / 2 + ramp_proud:.2f} mm of proud ramp",
    )
    r.check(
        c.GROOVE_FLOOR > c.GROOVE_ROOF,
        "the groove reaches further down than up -- it is not symmetric, and "
        "the two faces answer to different things",
        f"floor {c.GROOVE_FLOOR:.2f} mm (the fit) vs roof "
        f"{c.GROOVE_ROOF:.2f} mm (the print)",
    )


def check_wall_budget(r: Report) -> None:
    """Every place the two-material split could have left a wall too thin. All
    arithmetic on the config, so it holds for every set at once."""
    r.section("wall budget")
    r.check(
        c.RIM_FLAT >= MIN_WALL - TOL,
        "flat rim survives both top chamfers",
        f"{c.RIM_FLAT:.2f} mm (min {MIN_WALL})",
    )
    # Both grooves are cut into the same 1.6 mm ring of collar wall, from
    # opposite faces, and each is checked against the depth it is really cut at
    # rather than against the other's -- they are the same 0.8 today and are two
    # different numbers, one owned by the cover's joint and one by this package.
    r.check(
        c.SHELL_WALL - SNAP_GROOVE_R >= MIN_WALL - TOL,
        "collar wall survives the cover's snap groove",
        f"{c.SHELL_WALL - SNAP_GROOVE_R:.2f} mm",
    )
    r.check(
        c.SHELL_WALL - c.GROOVE_D >= MIN_WALL - TOL,
        "cavity wall survives the cartridge's retention groove",
        f"{c.SHELL_WALL - c.GROOVE_D:.2f} mm",
    )
    r.check(
        c.SHELL_WALL - c.KEY_D >= MIN_WALL - TOL,
        "cavity wall survives the key slot",
        f"{c.SHELL_WALL - c.KEY_D:.2f} mm",
    )
    r.check(
        c.CART_WALL >= MIN_WALL - TOL,
        "cartridge keeps CART_WALL to its outer face",
        f"{c.CART_WALL:.2f} mm",
    )
    # The two grooves are cut into opposite faces of the same SHELL_WALL, so what
    # matters is that the *grooves* do not overlap in z -- the bead's ramp is on
    # the TPU and takes nothing out of the base. Lip to lip, not centre to
    # centre: the cartridge's groove is chamfered and reaches 1.8 mm below
    # BEAD_Z against 0.95 above, so its centre says nothing about where it ends.
    r.check(
        c.GROOVE_LIP_GAP > 0.0,
        "cover groove and collar groove never thin the same wall",
        f"{c.GROOVE_LIP_GAP:.1f} mm of full-thickness wall between their lips "
        f"({c.GROOVE_SEPARATION:.1f} mm centre to centre)",
    )
    # The seat is the one dimension that must NOT move: it feeds
    # cover_height_for, so lowering it mints a taller cover for one model and
    # every cover already on the shelf stops fitting.
    r.check(
        abs(c.SHELL_FOOT_TOP - FOOT_TOP) < TOL,
        "the cover seat sits where the engine puts it, so covers interchange",
        f"{c.SHELL_FOOT_TOP:.1f} mm -- lower it and shared covers are lost",
    )
    # The flush silhouette, as an identity rather than as two numbers that happen
    # to agree today. This is the whole reason BODY_W exists: the body used to be
    # PAD while the cover was GRID, and the 0.25 mm/side lip that left is exactly
    # what a check on "are they equal" would have caught.
    r.check(
        abs(BODY_W - COVER_W) < TOL,
        "body and cover are the same width, so the assembly has no lip",
        f"body {BODY_W:.2f} mm, cover {COVER_W:.2f} mm",
    )
    # ...and that the pair of them is inside the envelope Gridfinity allows a 1x1,
    # which is the reason both are 41.5 and not 42: PAD is the pitch with the
    # inter-bin gap already deducted, so anything wider stops sitting beside
    # another bin at *any* height, cover included.
    r.check(
        COVER_W <= PAD + TOL,
        "nothing reaches outside the 1x1 pad, so boxes sit in adjacent cells",
        f"widest {max(BODY_W, COVER_W):.2f} mm of {PAD:.2f} mm pad",
    )
    # The cover's wall is now derived (COVER_W - INNER_W), not chosen, so it is
    # the thing to hold to MIN_WALL -- and the bore is a true inward offset, so
    # this one number is the wall at the corners too, not just on the flats.
    r.check(
        COVER_WALL >= MIN_WALL - TOL,
        "cover wall survives being derived from the pad and a frozen bore",
        f"{COVER_WALL:.2f} mm (min {MIN_WALL})",
    )
    r.check(
        abs((CORNER_R - INNER_R) - COVER_WALL) < TOL,
        "cover bore is a true inward offset, so its corners are not the thin spot",
        f"corner wall {CORNER_R - INNER_R:.2f} mm vs flat {COVER_WALL:.2f} mm",
    )

    # Squaring the bore's corners buys that uniform wall by spending corner
    # clearance over the collar. It has room to spend -- the corners are not the
    # fit, the flats are -- but not unlimited room, so the collar's diagonal must
    # still clear the bore's. Reach of a rounded square along a direction.
    def _reach(w: float, rad: float, ux: float, uy: float) -> float:
        return (w / 2 - rad) * (ux + uy) + rad

    diag = 2**-0.5
    corner_gap = _reach(INNER_W, INNER_R, diag, diag) - _reach(
        COLLAR_W, COLLAR_R, diag, diag
    )
    r.check(
        corner_gap >= SLIP / 2 - TOL,
        "collar's corners still clear the bore's, which the offset ate into",
        f"{corner_gap:.3f} mm on the diagonal, vs {SLIP / 2:.3f} on the flats",
    )
    # The cover still has somewhere flat to land. With body and cover flush, the
    # rim is inset by its own two chamfers and nothing else, and both come out of
    # the same 0.95 mm wall.
    rim = COVER_WALL - COVER_SEAT_CH - MOUTH_CH
    r.check(
        rim >= 0.4 - TOL,
        "cover's rim still has a flat to seat on after both its chamfers",
        f"{rim:.2f} mm of flat rim (seat {COVER_SEAT_CH}, mouth {MOUTH_CH})",
    )
    # The cap, bounded from both sides. It is not held to MIN_WALL: it is a plate
    # spanning the bore, not a wall, so what matters is that the pillow has not
    # eaten it at the rim and that it still slices solid without infill.
    #
    # A bore offset COVER_WALL in from the side meets the pillow at this depth --
    # below it, the cut leaves the ceiling and opens the rounded shoulder.
    pillow = TOP_FILLET - math.sqrt(TOP_FILLET**2 - (TOP_FILLET - COVER_WALL) ** 2)
    r.check(
        CAP_H >= pillow + MIN_WALL / 2 - TOL,
        "cap outlasts the pillow, so the bore cannot open the rounded shoulder",
        f"{CAP_H:.2f} mm cap, {pillow:.2f} mm of pillow at the bore, "
        f"{CAP_H - pillow:.2f} mm left (min one 0.4 mm perimeter)",
    )
    r.check(
        CAP_H <= CAP_SOLID_LAYERS * LAYER_H + TOL,
        "cap slices solid at 0% infill -- its bottom and top solid layers meet",
        f"{CAP_H:.2f} mm vs {CAP_SOLID_LAYERS} x {LAYER_H} mm of solid layers",
    )
    # The label pocket, as a *named* exception -- it legitimately fails MIN_WALL,
    # so it is held to the number that actually matters (one 0.4 mm perimeter, so
    # the glyph floor slices as material rather than as a hole) and to the
    # legibility floor on the other side. See box.LABEL_DEPTH for the argument.
    residual = COVER_WALL - LABEL_DEPTH
    r.check(
        residual >= 0.4 - TOL and LABEL_DEPTH >= 0.5 - TOL,
        "engraved label stays legible without punching through the wall",
        f"{residual:.2f} mm behind a {LABEL_DEPTH} mm engrave (stated MIN_WALL exception)",
    )


def check_sets_table(r: Report) -> None:
    """``sets.py`` is a table people edit, so its invariants are checked here
    rather than trusted to review."""
    r.section("sets")
    r.check(
        len({s.name for s in sets.ALL}) == len(sets.ALL),
        "every set has a distinct module name",
        f"{[s.name for s in sets.ALL]}",
    )
    r.check(
        len({s.label for s in sets.ALL}) == len(sets.ALL),
        "every cover carries a distinct label",
        f"{[s.label for s in sets.ALL]}",
    )
    for s in sets.ALL:
        nominal = s.nominal
        r.check(
            nominal == sorted(nominal) and len(nominal) == len(set(nominal)),
            f"{s.name}: sizes are sorted and unique",
            f"{nominal}",
        )
        lengths = [d.length for d in s.drills]
        r.check(
            lengths == sorted(lengths),
            f"{s.name}: lengths do not shrink as the bits grow",
            f"{lengths}",
        )
        r.check(
            s.shank_allowance >= 0.0,
            f"{s.name}: the shank is never wider than the size on the bit",
            f"allowance {s.shank_allowance:.2f} mm",
        )
        r.check(
            all(d.shank is None or d.shank <= d.nominal for d in s.drills),
            f"{s.name}: no measured shank is wider than its nominal",
            f"{[(d.nominal, d.shank) for d in s.drills if d.shank is not None and d.shank > d.nominal]}",
        )
        # The smallest land still has to print as a hole rather than close up.
        smallest = min(c.land_bore_r(d, _land_ease(s, d)) * 2 for d, _x, _y in s.bores)
        r.check(
            smallest >= MIN_WALL - TOL,
            f"{s.name}: the smallest land is still a printable hole",
            f"{smallest:.2f} mm (min {MIN_WALL})",
        )


# --- Per-set ------------------------------------------------------------------


def check_envelope(s: DrillSet, base: Part, insert: Part, r: Report) -> None:
    """Gridfinity envelope, and the cartridge actually fitting its cavity."""
    r.section(f"{s.name}: envelope")
    sb = base.bounding_box()
    # BODY_W is PAD, so the widest thing on the base is one Gridfinity pad from
    # the foot to the shoulder -- nothing on this part reaches outside the
    # envelope, which is what lets a bare base sit next to another bin.
    r.check(
        abs(sb.size.X - BODY_W) < 0.01 and abs(sb.size.Y - BODY_W) < 0.01,
        "base footprint is one Gridfinity pad, flush with the cover",
        f"{sb.size.X:.2f} x {sb.size.Y:.2f} mm",
    )
    r.check(
        abs(sb.size.Z - c.SHELL_TOTAL_H) < 0.01,
        "base is SHELL_TOTAL_H tall",
        f"{sb.size.Z:.1f} mm",
    )
    r.check(
        abs(sb.min.Z) < 0.01, "base sits on z=0 (print pose)", f"min z {sb.min.Z:.3f}"
    )

    ib = insert.bounding_box()
    r.check(
        abs(ib.min.Z) < 0.01,
        "cartridge sits on z=0 (print pose)",
        f"min z {ib.min.Z:.3f}",
    )
    r.check(
        abs(ib.size.Z - c.CART_H) < 0.01,
        "cartridge is CART_H tall",
        f"{ib.size.Z:.2f} mm",
    )
    # The body must clear the cavity; the bead and key rib deliberately do not.
    r.check(
        c.CART_W < c.CAVITY_W - TOL,
        "cartridge body clears the cavity",
        f"{c.CART_W:.2f} < {c.CAVITY_W:.2f} mm, slip {c.CART_SLIP:.2f}",
    )
    r.check(
        c.CART_PROUD > 0.5,
        "cartridge stands proud enough to pinch out",
        f"{c.CART_PROUD:.1f} mm",
    )
    # The collar's defining property: symmetric about its own bead, with the
    # reach derived from what it must contain -- so check both halves of that
    # derivation rather than just the total.
    r.check(
        abs(c.CART_H - 2 * c.CART_ABOVE_BEAD) < TOL
        and abs(c.CART_BELOW_BEAD - c.CART_ABOVE_BEAD) < TOL,
        "collar is symmetric about its own retention bead",
        f"{c.CART_H:.2f} mm = 2 x {c.CART_ABOVE_BEAD:.2f}",
    )
    r.check(
        c.CART_BELOW_BEAD >= c.LAND_H + c.LAND_LEAD_IN - TOL,
        "reach below the bead covers the land and its lead-in",
        f"{c.CART_BELOW_BEAD:.2f} mm vs {c.LAND_H + c.LAND_LEAD_IN:.2f} mm needed",
    )
    r.check(
        c.CART_BELOW_BEAD >= c.BEAD_LEAD_IN - TOL,
        "reach below the bead covers the bead's own insertion ramp",
        f"{c.CART_BELOW_BEAD:.2f} mm vs {c.BEAD_LEAD_IN:.2f} mm needed",
    )
    r.check(
        c.CART_ABOVE_BEAD >= c.BEAD_BACK + c.CART_PROUD - TOL,
        "reach above the bead covers its retention face and the grip lip",
        f"{c.CART_ABOVE_BEAD:.2f} mm vs {c.BEAD_BACK + c.CART_PROUD:.2f} mm needed",
    )


def worst_overhang(part: Part, z_lo: float, z_hi: float) -> tuple[float, str]:
    """The steepest downward-facing surface lying wholly between two heights,
    in degrees off vertical -- 0 is a plain wall, 90 a flat ceiling.

    Measured from the solid rather than from the numbers that produced it,
    because an overhang is exactly the kind of thing a sweep or a boolean can
    quietly hand back different from what was drawn. Faces are sampled on a
    grid rather than at one point: the surfaces this is aimed at include swept
    tori round the cavity's corners, whose steepness is not constant.

    Faces are taken only if they lie *wholly* inside the band, which is what
    scopes this to one feature -- the cavity wall itself spans the whole cavity
    and drops out, as does anything cut through the band from outside it.

    Shared with the hex checks, which import this one.
    """
    worst, where = 0.0, "nothing overhanging"
    for face in part.faces():  # ty: ignore[invalid-argument-type]
        bb = face.bounding_box()
        if bb.min.Z < z_lo - TOL or bb.max.Z > z_hi + TOL:
            continue
        for u in (0.02, 0.25, 0.5, 0.75, 0.98):
            for v in (0.02, 0.25, 0.5, 0.75, 0.98):
                try:
                    at = face.position_at(u, v)
                    n = face.normal_at(at)
                except Exception:
                    continue
                if n.Z >= 0.0:
                    continue
                angle = math.degrees(math.asin(min(1.0, -n.Z)))
                if angle > worst:
                    worst, where = angle, f"z={at.Z:.2f}"
    return worst, where


def _bead_reach(z: float) -> float:
    """How far the seated cartridge's bead stands out from its own body at
    height ``z`` in the base's frame -- ``0`` outside the bead entirely.

    ``box.snap_bead_ring``'s quad, read back as a function of height: a ramp of
    ``BEAD_RAMP_H`` up to the tip flat, then the retention face down to nothing
    at ``BEAD_Z + BEAD_BACK``. The cartridge bottoms out on the cavity floor, so
    this is fixed in the base's coordinates and not a function of how hard
    anyone pushed.
    """
    half = c.BEAD_TIP_FLAT / 2
    if z < c.BEAD_Z - c.BEAD_LEAD_IN or z > c.BEAD_Z + c.BEAD_BACK:
        return 0.0
    if z <= c.BEAD_Z - half:  # the long insertion ramp
        return c.CART_BEAD * (z - (c.BEAD_Z - c.BEAD_LEAD_IN)) / c.BEAD_RAMP_H
    if z <= c.BEAD_Z + half:  # the flat at the tip
        return c.CART_BEAD
    return c.CART_BEAD * (1 - (z - c.BEAD_Z - half) / (c.BEAD_BACK - half))


def check_groove(s: DrillSet, base: Part, r: Report) -> None:
    """The retention groove, on both counts it is cut for: it has to print, and
    it has to receive the bead.

    Nothing else in this file catches either. The groove is a mating feature, so
    the sharp-edge audit names its lips as exceptions; it is a ring inside a
    cavity, so no rendered view shows it; and the bead lives on the *other*
    part, so no check on the cartridge alone can see the two interfere. The
    half-round groove this replaced passed everything here while asking its
    topmost layer to close 0.53 mm of roof in one step and while crushing the
    last millimetre of the bead's ramp against its own bottom lip.
    """
    r.section(f"{s.name}: retention groove")
    z_lo, z_hi = c.BEAD_Z - c.GROOVE_FLOOR, c.BEAD_Z + c.GROOVE_ROOF
    worst, where = worst_overhang(base, z_lo, z_hi)
    r.check(
        worst <= c.MAX_OVERHANG + 0.5,
        "the groove prints without support",
        f"steepest downward face {worst:.1f} deg off vertical at {where} "
        f"(max {c.MAX_OVERHANG:.0f}), sampled over z={z_lo:.2f}..{z_hi:.2f}",
    )
    # ...and it is a groove at all: full depth at the bead's own height, solid
    # behind it. Sampled on +Y, which carries neither the key slot nor a legend.
    y_wall = c.CAVITY_W / 2
    r.check(
        not is_solid_at(base, 0.0, y_wall + c.GROOVE_D - PROBE, c.BEAD_Z)
        and is_solid_at(base, 0.0, y_wall + c.GROOVE_D + PROBE, c.BEAD_Z),
        "the groove is cut to GROOVE_D and no further",
        f"{c.GROOVE_D:.2f} mm deep at z={c.BEAD_Z:.1f}, leaving "
        f"{c.SHELL_WALL - c.GROOVE_D:.2f} mm of wall",
    )
    # The fit, walked rather than argued: at every height the bead reaches past
    # the cartridge's own slip gap, the ASA it would reach into has to be gone.
    # This is the check the old groove failed -- its lower half was 0.8 mm deep
    # against a 2.25 mm ramp, so the ramp seated crushed rather than dropping in.
    worst_z, worst_bite = 0.0, -math.inf
    for i in range(101):
        z = c.BEAD_Z - c.BEAD_LEAD_IN + i * (c.BEAD_LEAD_IN + c.BEAD_BACK) / 100
        surface = c.CART_W / 2 + _bead_reach(z)
        if surface <= y_wall:  # still inside the cavity's own slip gap
            continue
        bite = surface - y_wall  # how far into the wall the bead reaches here
        if is_solid_at(base, 0.0, surface - 0.02, z) and bite > worst_bite:
            worst_z, worst_bite = z, bite
    r.check(
        worst_bite < 0.0,
        "the seated bead is clear of ASA over its whole profile",
        "sampled at 101 heights across the bead"
        if worst_bite < 0.0
        else f"{worst_bite:.2f} mm of interference at z={worst_z:.2f}",
    )


def check_cover_interface(s: DrillSet, cover: Part, r: Report) -> None:
    """The cover is sized by the longest tool and quantised to a whole unit, and
    the tip has to actually fit under the cap that picked."""
    r.section(f"{s.name}: cover")
    want = cover_height_for(
        s.max_len,
        headroom=sets.COVER_TIP_CLEARANCE,
        bore_floor_z=c.GUIDE_FLOOR_Z,
        foot_top=c.SHELL_FOOT_TOP,
    )
    r.check(
        abs(want - s.cover_h) < TOL,
        "cover height is the one cover_height_for picks for the longest tool",
        f"{s.cover_h:.0f} mm for a {s.max_len:.0f} mm tool",
    )
    cb = cover.bounding_box()
    r.check(
        abs(cb.size.Z - s.cover_h) < 0.05 and abs(cb.min.Z) < 0.02,
        "cover is built to that height and sits on z=0 (print pose)",
        f"{cb.size.Z:.2f} mm, min z {cb.min.Z:.3f}",
    )
    assembled = c.SHELL_FOOT_TOP + s.cover_h
    r.check(
        abs(assembled % HEIGHT_UNIT) < TOL,
        "assembled envelope is a whole Gridfinity Z unit",
        f"{assembled:.0f} mm = {assembled / HEIGHT_UNIT:.0f}U "
        f"(the base itself is {c.SHELL_TOTAL_H:.0f} mm, deliberately not a unit)",
    )
    headroom = (assembled - CAP_H) - (c.GUIDE_FLOOR_Z + s.max_len)
    r.check(
        headroom >= sets.COVER_TIP_CLEARANCE - TOL,
        "the longest tip clears the cap ceiling by the clearance asked for",
        f"{headroom:.2f} mm >= {sets.COVER_TIP_CLEARANCE:.2f}",
    )
    r.check(
        abs(c.GUIDE_FLOOR_Z - 6.0) < TOL,
        "tools still bottom out at the engine's bore floor",
        f"{c.GUIDE_FLOOR_Z:.1f} mm",
    )


def check_bore_spacing(s: DrillSet, r: Report) -> None:
    """pack_rows only warns about *horizontal* overpacking and will silently
    overlap rows, so the row pitch is checked here or it is not checked."""
    r.section(f"{s.name}: bore spacing")
    items = _bore_footprints(s)
    worst_key, worst = "", math.inf
    for (k1, r1, x1, y1), (k2, r2, x2, y2) in itertools.combinations(items, 2):
        gap = math.dist((x1, y1), (x2, y2)) - r1 - r2
        if gap < worst:
            worst, worst_key = gap, f"{k1}<->{k2}"
    r.check(
        worst >= c.PACK_HOLE_WALL - TOL,
        "every bore pair meets the mouth-chamfer budget",
        f"worst {worst_key} = {worst:.2f} mm (budget {c.PACK_HOLE_WALL:.2f})",
    )
    r.check(
        worst >= MIN_WALL - TOL,
        "every bore pair is at least a printable wall apart",
        f"{worst:.2f} mm (min {MIN_WALL})",
    )

    # Every bore must also keep CART_WALL of material to the cartridge's face.
    half = c.CART_W / 2
    worst_edge = min(half - max(abs(x), abs(y)) - rad for _k, rad, x, y in items)
    r.check(
        worst_edge >= c.CART_WALL - TOL,
        "every bore keeps CART_WALL to the outer face",
        f"{worst_edge:.2f} mm",
    )
    # The key rib lives outside the body, so no bore can ever reach it -- but say
    # so in code, because that is the whole reason it is out there.
    r.check(
        all(x + rad < half + TOL for _k, rad, x, _y in items),
        "no bore reaches past the cartridge face into the key rib",
        f"max reach {max(x + rad for _k, rad, x, _y in items):.2f} of {half:.2f}",
    )


def _packing_footprints(s: DrillSet) -> list[tuple[str, float, float, float]]:
    """What the *packer* had to fit, as ``(key, radius, x, y)``.

    Not ``_bore_footprints``: for a hex tool this is whichever is wider, its head
    or its relieved socket. The two differ by a factor of three on a step drill
    -- a 20 mm body over a 6.3 mm socket -- and it is the head that decides
    whether the layout was possible. A reduced-shank drill is the same story in
    miniature: the bore is cut to the shank, but the *body* stands above the tray
    at the nominal size, so the wider of the two is what has to be packed.
    """
    items = [
        (
            f"{d.nominal:g}",
            max(c.relieved_bore_r(bore_d), d.nominal / 2),
            x,
            y,
        )
        for d, (bore_d, x, y) in zip(s.drills, s.bores)
    ]
    items += [
        (t.key, max(t.head_d / 2, _hex_r(af, c.RELIEF_FIT)), x, y)
        for t, (af, x, y) in zip(s.hex_tools, s.hex_bores)
    ]
    return items


def check_layout(s: DrillSet, r: Report) -> None:
    """A layout meets the packer's contract however it was arrived at.

    ``pack_rows`` enforces this itself, so for two of the three sets this is a
    restatement. For the one with an explicit ``layout`` it is the whole
    guarantee: those coordinates come out of ``freepack`` and are frozen into
    ``sets.py`` as literals, and a literal that nothing re-derives is exactly the
    kind of number this package does not allow. So it is re-derived here, against
    the same walls and gaps the row packer would have had to meet -- and against
    the *packing* footprints, which is where a head three times its socket shows
    up at all.
    """
    r.section(f"{s.name}: layout")
    items = _packing_footprints(s)
    slack, what = worst_slack(
        [(x, y) for _k, _rad, x, y in items],
        [rad for _k, rad, _x, _y in items],
        c.PACK_HALF_W,
        c.PACK_CORNER_R,
        c.PACK_HOLE_WALL,
        c.PACK_WALL_CLEARANCE,
    )
    r.check(
        slack >= -TOL,
        "every footprint meets its wall and its neighbours"
        + (" (explicit layout)" if s.layout else " (packed in rows)"),
        f"tightest {what}, {slack:+.2f} mm over the requirement",
    )
    r.check(
        len(set(s.pos)) == len(s.bores) + len(s.hex_bores),
        "the layout places every hole exactly once",
        f"{len(s.pos)} keys for {len(s.bores)} bores + {len(s.hex_bores)} sockets",
    )
    # The legend is engraved line by line at each hole's own x, so two labels on
    # one line must not overlap -- and the block must still land on the body wall.
    for line in s.rows:
        xs = sorted((s.pos[k][0], k) for k in line)
        for (x1, k1), (x2, k2) in zip(xs, xs[1:]):
            half = 0.31 * WALL_LABEL_SIZE * (len(k1) + len(k2))
            r.check(
                x2 - x1 >= half - TOL,
                f"legend labels {k1!r} and {k2!r} do not collide",
                f"{x2 - x1:.2f} mm apart, need {half:.2f}",
            )
    block = (len(s.rows) - 1) * s.legend_line_h / 2 + WALL_LABEL_SIZE * 0.75 / 2
    r.check(
        WALL_LABEL_Z - block >= BASE_H + TOL and WALL_LABEL_Z + block <= FOOT_TOP + TOL,
        f"the {len(s.rows)}-line legend block fits the body wall",
        f"{WALL_LABEL_Z - block:.2f} to {WALL_LABEL_Z + block:.2f} mm "
        f"of {BASE_H:.1f}-{FOOT_TOP:.1f}, pitch {s.legend_line_h:.1f}",
    )


def check_hex_tools(s: DrillSet, r: Report) -> None:
    """A hex tool is held by the same land the drills are, or it is held by
    nothing -- and a head wider than its socket has to clear what it sits over.

    Nothing else checks this. ``check_bore_spacing`` walks the *sockets*, so a
    step drill's 20 mm body is invisible to it, and the land engagement is a
    property of the tool's shank rather than of any cut geometry.
    """
    if not s.hex_tools:
        return
    r.section(f"{s.name}: hex tools")
    land_top = c.CAVITY_FLOOR_Z + c.LAND_H
    for t in s.hex_tools:
        r.check(
            t.seat_z <= c.CAVITY_FLOOR_Z + TOL and t.seat_z + t.shank >= land_top - TOL,
            f"{t.key}: the shank spans the whole grip land",
            f"shank {t.seat_z:.1f}-{t.seat_z + t.shank:.1f} mm over a land at "
            f"{c.CAVITY_FLOOR_Z:.1f}-{land_top:.1f}",
        )
        r.check(
            t.seat_z + t.shank >= c.CART_TOP_Z - TOL,
            f"{t.key}: the head stops at the top face, never inside the socket",
            f"shank ends at {t.seat_z + t.shank:.1f} mm, cartridge top "
            f"{c.CART_TOP_Z:.1f}",
        )
        if t.head_d <= 0.0:
            continue
        # The head lives above the tray, where the bounding wall is the cover's
        # bore rather than the cartridge -- so this is the one clearance that is
        # measured against the cover. Against the *rounded square* it really is,
        # not a circle through its flats: a head parked near a corner has another
        # 2.8 mm of diagonal to use, and the wood set's countersink uses it.
        x, y = s.pos[t.key]
        clear = -sdf(x, y, INNER_W / 2, INNER_R) - t.head_d / 2
        r.check(
            clear >= TOOL_CLEARANCE - TOL,
            f"{t.key}: the head clears the cover bore",
            f"{clear:.2f} mm to the bore (min {TOOL_CLEARANCE})",
        )
        # ...and it must clear every tool tall enough to still be there.
        head_z = t.seat_z + t.shank
        others = [
            (f"{d.nominal:g}", d.nominal / 2, bore[1], bore[2])
            for d, bore in zip(s.drills, s.bores)
            if c.GUIDE_FLOOR_Z + d.length > head_z
        ]
        others += [
            (
                o.key,
                max(o.head_d / 2, o.across_flats / 3**0.5),
                s.pos[o.key][0],
                s.pos[o.key][1],
            )
            for o in s.hex_tools
            if o.key != t.key and o.seat_z + o.length > head_z
        ]
        worst_key, worst = "nothing above it", math.inf
        for key, rad, ox, oy in others:
            gap = math.dist((x, y), (ox, oy)) - t.head_d / 2 - rad
            if gap < worst:
                worst, worst_key = gap, key
        r.check(
            worst >= TOOL_CLEARANCE - TOL,
            f"{t.key}: the head clears every tool standing beside it",
            f"worst {worst_key} = {worst:.2f} mm (min {TOOL_CLEARANCE})",
        )


def check_land(s: DrillSet, insert: Part, r: Report) -> None:
    """The grip itself: the land is where it is modelled, and it is tighter than
    the relief above it. This is the one thing point-sampling can prove."""
    r.section(f"{s.name}: grip land")
    # The insert returns in print pose (top face on the bed, land up), so the
    # land band sits at the top of the part and the relief below it.
    z_land = c.CART_H - (c.BORE_FOOT_RELIEF + c.EFFECTIVE_LAND_H / 2)
    z_relief = c.CART_H - (c.LAND_H + c.LAND_LEAD_IN + 2.0)

    for d, x, y in s.bores:
        land_r = c.land_bore_r(d, _land_ease(s, d))
        relief_r = (d + c.RELIEF_FIT) / 2
        py = _print_pose_y(y)  # the print pose mirrors Y; sample the real part
        ok = (
            not is_solid_at(insert, x + land_r - PROBE, py, z_land)
            and is_solid_at(insert, x + land_r + PROBE, py, z_land)
            and not is_solid_at(insert, x + relief_r - PROBE, py, z_relief)
            and is_solid_at(insert, x + relief_r + PROBE, py, z_relief)
        )
        r.check(
            ok,
            f"{d:g} mm bore: land {land_r:.2f} / relief {relief_r:.2f}",
            f"sampled at z={z_land:.2f} and z={z_relief:.2f}",
        )
        # The step is the whole point: at land height the relief radius must be
        # solid, or the land is not actually narrower than the guide.
        r.check(
            is_solid_at(insert, x + land_r + PROBE, py, z_land),
            f"{d:g} mm bore: land is proud of the relief",
            f"{(relief_r - land_r) * 2:.2f} mm diametral step",
        )

    r.check(
        c.EFFECTIVE_LAND_H > 2.0,
        "land is long enough to bear after the foot relief",
        f"{c.EFFECTIVE_LAND_H:.1f} of {c.LAND_H:.1f} mm",
    )


def check_guides(s: DrillSet, base: Part, r: Report) -> None:
    """The ASA half of every hole: open top to bottom, loose, and coaxial with the
    collar's land above it. A guide that is off-axis makes the land a cam."""
    r.section(f"{s.name}: ASA guide bores")
    z_mid = c.GUIDE_FLOOR_Z + c.GUIDE_H / 2

    for d, x, y in s.bores:
        gr = (d + c.GUIDE_FIT) / 2
        ok = not is_solid_at(base, x + gr - PROBE, y, z_mid) and is_solid_at(
            base, x + gr + PROBE, y, z_mid
        )
        r.check(
            ok, f"{d:g} mm guide bored to {gr * 2:.2f} mm", f"sampled at z={z_mid:.1f}"
        )

    # Open all the way down to the floor a drill rests on, and no further.
    open_span = all(
        not is_solid_at(base, x, y, z)
        for _d, x, y in s.bores
        for z in (c.GUIDE_FLOOR_Z + 0.3, z_mid, c.CAVITY_FLOOR_Z - 0.3)
    )
    r.check(
        open_span,
        "every guide is open from its floor to the cavity",
        f"{len(s.bores)} bores sampled at 3 heights",
    )
    floor_intact = all(
        is_solid_at(base, x, y, c.GUIDE_FLOOR_Z - 0.3) for _d, x, y in s.bores
    )
    r.check(
        floor_intact,
        "the base floor under every guide is solid",
        "a drill rests on ASA, not on air",
    )

    hex_ok = all(
        not is_solid_at(base, x, y, z)
        for _af, x, y in s.hex_bores
        for z in (c.GUIDE_FLOOR_Z + 0.3, z_mid)
    )
    r.check(
        hex_ok,
        "every hex guide is bored too",
        f"{len(s.hex_bores)} socket(s)" if s.hex_bores else "none in this set",
    )

    # layout_bores packs on the *cartridge's* relieved bore and knows nothing about
    # how wide the guide is cut, so widening GUIDE_FIT spends a wall nothing else
    # is watching. This is the check that stops it going too far.
    guides = [(f"{d:g}", (d + c.GUIDE_FIT) / 2, x, y) for d, x, y in s.bores]
    guides += [
        (f"hex{af:g}", _hex_r(af, c.GUIDE_FIT), x, y) for af, x, y in s.hex_bores
    ]
    worst_key, worst = "", math.inf
    for (k1, r1, x1, y1), (k2, r2, x2, y2) in itertools.combinations(guides, 2):
        gap = math.dist((x1, y1), (x2, y2)) - r1 - r2
        if gap < worst:
            worst, worst_key = gap, f"{k1}<->{k2}"
    mouth_budget = 2 * c.GUIDE_MOUTH_CH + 0.1
    r.check(
        worst >= mouth_budget - TOL,
        "neighbouring guide mouths do not run into each other",
        f"worst {worst_key} = {worst:.2f} mm (budget {mouth_budget:.2f})",
    )
    r.check(
        worst >= MIN_WALL - TOL,
        "every guide pair is at least a printable wall apart",
        f"{worst:.2f} mm (min {MIN_WALL})",
    )
    # The guides run up into the collar, which is narrower than the body below it.
    reach = max(max(abs(x), abs(y)) + rad for _k, rad, x, y in guides)
    r.check(
        reach + MIN_WALL <= c.CAVITY_W / 2 + TOL,
        "every guide keeps a printable wall to the cavity",
        f"reach {reach:.2f} of {c.CAVITY_W / 2:.2f} mm",
    )
    # Every land is narrower than the guide beneath it -- checked against this
    # set's own bores, since a shank allowance shifts both and a bug that applied
    # it to only one would show up here and nowhere else. The eased land is the
    # real cut, so it is the one compared; the worst case is the smallest bore,
    # whose taper opens it the most.
    steps = [
        (d + c.GUIDE_FIT) - 2 * c.land_bore_r(d, _land_ease(s, d))
        for d, _x, _y in s.bores
    ]
    r.check(
        all(step > 0 for step in steps),
        "every land is narrower than the guide beneath it",
        f"min {min(steps):.2f} mm diametral step (eased land included)",
    )


def check_through_bores(s: DrillSet, insert: Part, r: Report) -> None:
    """Drills must reach the base's ASA floor, so every bore is a through hole."""
    r.section(f"{s.name}: through bores")
    heights = (0.05, c.CART_H / 2, c.CART_H - 0.05)
    ok_round = all(
        not is_solid_at(insert, x, _print_pose_y(y), z)
        for _d, x, y in s.bores
        for z in heights
    )
    r.check(
        ok_round,
        "every round bore is open top to bottom",
        f"{len(s.bores)} bores sampled at 3 heights",
    )
    ok_hex = all(
        not is_solid_at(insert, x, _print_pose_y(y), z)
        for _af, x, y in s.hex_bores
        for z in heights
    )
    r.check(
        ok_hex,
        "every hex socket is open top to bottom",
        f"{len(s.hex_bores)} sockets sampled",
    )


def check_key(s: DrillSet, base: Part, insert: Part, r: Report) -> None:
    """The legend is only true in one orientation, so the key has to work."""
    r.section(f"{s.name}: key")
    rib_tip = c.CART_W / 2 + c.KEY_D
    slot_floor = c.CAVITY_W / 2 + c.KEY_D
    r.check(
        rib_tip < slot_floor - TOL,
        "key rib clears the bottom of its slot",
        f"rib {rib_tip:.2f} < slot {slot_floor:.2f} mm",
    )
    # Sample low in the cavity, deliberately clear of the retention groove: the
    # collar is short enough that mid-cavity lands *inside* the groove at BEAD_Z,
    # where the wall is legitimately void and proves nothing about the key. The
    # groove is not symmetric about BEAD_Z, so this is measured against its own
    # bottom lip rather than against a radius either side of the centre.
    z = c.CAVITY_FLOOR_Z + 1.0
    r.check(
        z < c.BEAD_Z - c.GROOVE_FLOOR - 0.5,
        "key probe height is clear of the retention groove",
        f"z={z:.1f}, groove floor at {c.BEAD_Z - c.GROOVE_FLOOR:.1f}",
    )
    r.check(
        not is_solid_at(base, c.CAVITY_W / 2 + c.KEY_D / 2, 0.0, z),
        "base has a slot on +X in the cavity wall",
        f"z={z:.1f}",
    )
    r.check(
        is_solid_at(base, c.CAVITY_W / 2 + c.KEY_D / 2, 0.0 + c.KEY_W, z),
        "the slot is local, not a groove round the whole cavity",
        f"solid at y={c.KEY_W:.1f}",
    )
    r.check(
        is_solid_at(insert, c.CART_W / 2 + c.KEY_D / 2, 0.0, c.CART_H / 2),
        "cartridge has a rib on +X at mid-height",
        "",
    )


# --- Sharp edges --------------------------------------------------------------


def _is_bore_seam(part: Part, edge) -> bool:
    """A round bore's own untrimmed cylindrical seam, on the base or the
    cartridge insert -- not a real edge, just OCC's periodic parametrisation
    closing up on itself.

    ``sharp_convex_edges`` now reports the ``None`` edges ``min_length`` used
    to let through unseen (see its docstring), and every drill bore this
    family cuts is where that shows up: eleven per base (one per bit
    socket), twenty-two per insert (each socket's land and its relief bore).
    Nothing cuts *sideways* into a bore's own wall, so there is no boolean
    cut nearby for the seam to coincide with -- unlike a seam that happens to
    land on a genuine near-tangent sliver elsewhere in this repo (see
    ``is_periodic_seam``'s docstring for why that distinction matters and why
    this does not stop at "same face"). Confirmed against OCC's own topology
    rather than assumed from the repeating grid position: checked for every
    one of the 11 (base) and 22 (insert) matches on the wood set, not just a
    couple spot-checked by hand.
    """
    if edge.geom_type != GeomType.LINE:
        return False
    bb = edge.bounding_box()
    if bb.size.X > 1e-6 or bb.size.Y > 1e-6:
        return False
    return is_periodic_seam(part, edge)


def edge_faces(part: Part, edge) -> list:
    """The faces of ``part`` that share ``edge``, matched by position.

    The same identity ``models.lib.checks._adjacent_faces`` uses internally
    (an edge's centre + length, since two calls to ``Face.edges()`` hand back
    separate Python objects for the same geometry) -- re-derived here rather
    than imported, because that helper stays private to its owner module.
    Shared with the hex checks, which import this one
    (``drill_storage.hex.checks``).
    """
    at, length = edge.center(), edge.length
    key = (round(at.X, 4), round(at.Y, 4), round(at.Z, 4), round(length, 4))
    faces = []
    for face in part.faces():  # ty: ignore[invalid-argument-type]
        for e in face.edges():  # ty: ignore[invalid-argument-type]
            c = e.center()
            if (round(c.X, 4), round(c.Y, 4), round(c.Z, 4), round(e.length, 4)) == key:
                faces.append(face)
                break
    return faces


def is_flush_seam(part: Part, edge) -> bool:
    """A convex edge that measures a genuine, exact 180 deg -- not a corner at
    all, but a residual split where a boolean subtract's own tool boundary
    landed exactly flush with a face the part already had.

    ``base.key_slot_tool``'s mouth fillet is anchored tangent to the cavity
    wall on purpose (see that function's docstring for why: a fillet offset
    *short* of the wall is always a tighter, worse angle than the plain
    corner it replaces, so full tangency is the only geometry that actually
    helps). OCC leaves the coincident plane as two abutting faces rather than
    silently merging them into one -- ``Part.clean()`` does not remove it
    either, checked rather than assumed -- so the edge between them survives
    into ``part.edges()`` with nothing on either side of it.

    ``sharp_convex_edges`` reports it as *unclassifiable*, not sharp: its own
    probe cannot find an "inside" wedge here because there genuinely isn't
    one to find, which is a different claim from "could not be measured".
    This confirms that claim independently of the probe, by a direct
    measurement rather than an absence of one: both adjacent faces' normals,
    sampled at three points along the edge (not just its centre, so a seam
    that is only *partly* flush cannot slip through), are antiparallel --
    the same plane, seen from both sides.
    """
    if edge.geom_type != GeomType.LINE:
        return False
    faces = edge_faces(part, edge)
    if len(faces) != 2:
        return False
    for t in (0.1, 0.5, 0.9):
        at = edge.position_at(t)
        try:
            n0 = faces[0].normal_at(at)
            n1 = faces[1].normal_at(at)
        except Exception:
            return False
        if n0.get_angle(n1) < 180 - 1e-3:
            return False
    return True


def _base_allow(base: Part) -> tuple:
    """The base's legitimate exceptions to the chamfer-everything rule.

    Named with their reason, never silently omitted -- that is the whole point of
    ``sharp_convex_edges`` taking an allow list rather than a threshold.
    """

    def on_wall_face(e) -> bool:
        b = e.bounding_box()
        half = BODY_W / 2
        return (
            abs(abs(b.min.X) - half) < 0.05 and abs(abs(b.max.X) - half) < 0.05
        ) or (abs(abs(b.min.Y) - half) < 0.05 and abs(abs(b.max.Y) - half) < 0.05)

    def on_shoulder(e) -> bool:
        b = e.bounding_box()
        return (
            abs(b.min.Z - c.SHELL_FOOT_TOP) < 0.05
            and abs(b.max.Z - c.SHELL_FOOT_TOP) < 0.05
        )

    def on_the_cover_groove(e) -> bool:
        """The rims of the *cover's* groove on the outside of the collar, which
        is still the half-round pocket ``snap_ring`` cuts and so still meets the
        wall tangentially at a square rim.

        The cartridge's groove inside the cavity is deliberately not here any
        more: it is chamfered now (config's "the groove that receives the
        bead"), so its lips measure 135 and 156 deg and pass the audit on their
        own geometry rather than on a promise.
        """
        b = e.bounding_box()
        if abs(b.max.Z - b.min.Z) > 0.05:
            return False
        z = c.SHELL_FOOT_TOP + SNAP_Z
        return (
            abs(b.min.Z - (z - SNAP_GROOVE_R)) < 0.05
            or abs(b.min.Z - (z + SNAP_GROOVE_R)) < 0.05
        )

    return (
        (on_wall_face, "engraved size legend -- bevelling a glyph destroys it"),
        (
            on_shoulder,
            "cover seat is deliberately flat so the cover's chamfered "
            "rim lands flat-on-flat (box.create_cover's COVER_SEAT_CH)",
        ),
        (
            on_the_cover_groove,
            "the cover groove's round rims -- the groove is the mating "
            "feature, and rounding its lips would shrink engagement",
        ),
        (
            lambda e: _is_bore_seam(base, e),
            "a bit socket's own untrimmed bore wall seam -- confirmed via "
            "is_periodic_seam, one per socket",
        ),
        (
            lambda e: is_flush_seam(base, e),
            "the key slot's mouth fillet, anchored flush with the cavity "
            "wall -- a genuine 180 deg split OCC left as two faces rather "
            "than one, confirmed by matching face normals, two per base "
            "(see base.key_slot_tool)",
        ),
    )


def _label_window(
    text: str, label_size: float, label_z: float, cover_h: float, horizontal: bool
) -> tuple[float, float, float]:
    """Where an engraved cover label really lands, in print pose.

    Returns ``(x_half, z_centre, z_half)``: the half-width along x, and the band
    along z, that the glyphs occupy on the label face.

    Measured off the same ``Text`` sketch ``box.create_cover`` engraves rather
    than estimated from the font size, because the two differ by a lot -- a word
    is three times longer than it is tall, and which of those runs along z
    depends on ``horizontal``. ``create_cover`` builds the label on the +Y face
    at ``label_z`` and then flips the part into print pose (``Rotation(180,0,0)``
    plus a re-seat on z=0), which puts the label on **-Y** at ``cover_h -
    label_z`` -- so this reports the flipped coordinates, which are the ones an
    edge of the returned part actually has.

    Both spans are grown by ``LABEL_CHAMFER`` (the bevel on the glyph mouths
    reaches outside the glyph itself) plus a small pad.
    """
    with BuildSketch() as sk:
        Text(text, font_size=label_size)
    box = sk.sketch.bounding_box()
    run, thick = box.size.X, box.size.Y  # along the reading direction, and across
    grow = LABEL_CHAMFER + 0.5
    return (
        (run if horizontal else thick) / 2 + grow,
        cover_h - label_z,
        (thick if horizontal else run) / 2 + grow,
    )


def _cover_allow(
    text: str, label_size: float, label_z: float, cover_h: float, horizontal: bool
) -> tuple:
    """The cover's one legitimate exception: the engraved label's own glyphs.

    Scoped to the label and nothing else. The predicate this replaced matched
    any edge whose centre lay within 1.5 mm of *either* +/-Y face, which is
    three things wider than its own reason: it whitelisted the blank face
    opposite the label, the mouth rim's straight -Y segment, and everything
    above and below the word on the labelled face. Nothing was being masked when
    that was found -- every raw edge on all five covers measured is a glyph --
    but an allow list that admits more than it says is how the *next* sharp edge
    hides, so it is written to its reason: on the label face, inside the
    engraving's depth, within the word's own footprint.
    """
    half = COVER_W / 2
    x_half, z_mid, z_half = _label_window(
        text, label_size, label_z, cover_h, horizontal
    )

    def on_label_glyph(e) -> bool:
        centre = e.center()
        return (
            # Cut *into* the -Y face: the mouth lies on it, the floor LABEL_DEPTH
            # behind it, and the chamfer wall between the two.
            -half - 0.05 <= centre.Y <= -half + LABEL_DEPTH + 0.05
            and abs(centre.X) <= x_half
            and abs(centre.Z - z_mid) <= z_half
        )

    return (
        (on_label_glyph, "engraved material label -- bevelling a glyph destroys it"),
    )


def check_sharp_edges(
    s: DrillSet, base: Part, insert: Part, cover: Part, r: Report
) -> None:
    """House rule: chamfer horizontal edges, fillet vertical ones. Exceptions are
    named with their reason, never silently omitted."""
    r.section(f"{s.name}: sharp edges")
    base_edges = sharp_convex_edges(base, allow=_base_allow(base))
    r.check(
        not base_edges.sharp,
        "base has no unexplained sharp convex edges",
        f"{len(base_edges.sharp)} found"
        if base_edges.sharp
        else "all treated or named",
    )
    r.check(
        not base_edges.unclassifiable,
        "base has no unexplained unclassifiable convex edges",
        f"{len(base_edges.unclassifiable)} found"
        if base_edges.unclassifiable
        else "all measured or named",
    )
    insert_edges = sharp_convex_edges(
        insert,
        allow=(
            (
                lambda e: _is_bore_seam(insert, e),
                "a bit socket's own untrimmed bore wall seam (land and "
                "relief bore alike) -- confirmed via is_periodic_seam, two "
                "per socket",
            ),
        ),
    )
    r.check(
        not insert_edges.sharp,
        "cartridge has no sharp convex edges at all",
        f"{len(insert_edges.sharp)} found"
        if insert_edges.sharp
        else "none, no exceptions",
    )
    r.check(
        not insert_edges.unclassifiable,
        "cartridge has no unclassifiable convex edges at all",
        f"{len(insert_edges.unclassifiable)} found"
        if insert_edges.unclassifiable
        else "none, no exceptions",
    )
    # create_cover_for takes box's own label defaults, so the window is measured
    # from exactly what was engraved.
    cover_edges = sharp_convex_edges(
        cover, allow=_cover_allow(s.label, LABEL_SIZE, LABEL_Z, s.cover_h, False)
    )
    r.check(
        not cover_edges.sharp,
        "cover has no unexplained sharp convex edges",
        f"{len(cover_edges.sharp)} found"
        if cover_edges.sharp
        else "all treated or named",
    )
    r.check(
        not cover_edges.unclassifiable,
        "cover has no unexplained unclassifiable convex edges",
        f"{len(cover_edges.unclassifiable)} found"
        if cover_edges.unclassifiable
        else "all measured or named",
    )


def check_set(s: DrillSet, r: Report) -> None:
    """Everything that has to hold for one set, on its three built parts."""
    base = create_base_for(s)
    insert = create_insert_for(s)
    cover = create_cover_for(s)

    check_envelope(s, base, insert, r)
    check_groove(s, base, r)
    check_cover_interface(s, cover, r)
    check_layout(s, r)
    check_hex_tools(s, r)
    check_bore_spacing(s, r)
    check_guides(s, base, r)
    check_land(s, insert, r)
    check_through_bores(s, insert, r)
    check_key(s, base, insert, r)
    check_sharp_edges(s, base, insert, cover, r)


# --- Entry points -------------------------------------------------------------


def _shared(r: Report) -> None:
    """The checks that are the same whichever set you asked about."""
    check_fits(r)
    check_wall_budget(r)
    check_retention(r)


def run_for(s: DrillSet) -> Report:
    """One variant: the shared clearances plus that set's own geometry.

    What ``uv run check drill_storage.<set>`` runs -- three built parts rather
    than the eleven ``run()`` needs, which is the difference between waiting and
    not bothering.
    """
    r = Report()
    _shared(r)
    check_set(s, r)
    return r


def run() -> Report:
    r = Report()
    _shared(r)
    check_sets_table(r)
    for s in sets.ALL:
        check_set(s, r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
