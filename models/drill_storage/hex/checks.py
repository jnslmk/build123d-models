"""Geometry assertions for the two hex-bit boxes.

    uv run check drill_storage.hex

The hex boxes are the drill family's two-material design -- rigid base guides,
TPU insert grips, translucent cover -- cut shorter (30 mm bases). Both are 1x1:
the ALLEN box keeps the family's clearances outright, the BITS box shaves
three of them (the two mouth chamfers and the guide fit) to fit sixteen
sockets in a literal 4x4 grid on the same cartridge, and the argument lives in
``config.py``'s footprints section. The assertions were ported from the
family's ``drill_storage.checks`` and re-derived against this package's own
config: the sockets are bored at the right across-flats and cut at exactly the
radius the layout reserved, the walls and the neighbour gaps hold to each
box's budgets, the base is the documented height in print pose, the assembled
envelope is a whole Gridfinity unit, and no part ships a raw sharp edge that
is not named.

The BITS box gets assertions of its own: the shared 1x1 footprint, exactly
sixteen sockets in a literal 4x4 grid at the shaved pitch, and every margin
the shave trades on -- the flat-face and top-rim walls at CART_WALL (measured
with the rounded-square SDF, corner sockets included), the land and relief
gaps between neighbours, and the two mouth gaps.

What this file cannot tell you is whether the grip is right. The land these
cartridges are cut at is the family's judgement (settled by printed cartridges
-- see ``config.LAND_EASE`` and ``docs/design-notes.md``) tightened by this
package's ``HEX_LAND_TIGHTEN``, and no measurement off a solid can say whether
a key now lifts the base with it. What *is* checked is the pair of bounds that
tightening has to stay inside: the land may not pass the family's own hex land
measured from the shank, and the rigid guide below must stay looser than it.
"""

from __future__ import annotations

import itertools
import math
import sys

from build123d import Part

from ...lib.checks import TOL as TOL
from ...lib.checks import Report as Report
from ...lib.checks import is_solid_at as is_solid_at
from ...lib.checks import sharp_convex_edges
from ..box import (
    BASE_H,
    BODY_W,
    CAP_H,
    HEIGHT_UNIT,
    INNER_W,
    SNAP_BACK,
    SNAP_LEAD_IN,
    SNAP_PROTRUSION,
    SNAP_TIP_FLAT,
    SNAP_Z,
    WALL_LABEL_SIZE,
)
from ..checks import (
    is_flush_seam,
    label_window,
    wall_legend_window,
    worst_bead_bite,
    worst_overhang,
)
from .. import config as fam
from ..freepack import sdf, worst_slack
from . import config as c
from .base import create_base
from .cover import create_cover, label_fit
from .insert import create_insert

PROBE = 0.08  # how far either side of a modelled radius we sample for material

# The absolute minimum wall a 0.4 mm nozzle resolves: 2 perimeters. The same
# figure is the floor for a *hole*: under two extrusions wide, a bore closes up.
MIN_WALL = 0.8

# ``pack_rows`` rounds every position it solves onto a 0.01 mm grid, so a hole
# it pushed out to *exactly* its wall clearance can land up to half a step
# outside it. That is quantisation, not a violated requirement, so a layout
# re-derived from those coordinates is allowed this much and no more. (The BITS
# grid is solved exactly, but the same tolerance costs nothing and keeps the
# check uniform.)
PACK_ROUNDING = 0.01


def _cover_allow(
    text: str,
    label_size: float,
    label_z: float,
    cover_h: float,
    horizontal: bool,
    cover_w: float,
) -> tuple:
    """The cover's one legitimate exception: the engraved label's own glyphs.

    Scoped to the label and nothing else -- the same allow the family's
    ``drill_storage.checks._cover_allow`` builds, at any cover width: on the
    label face, inside the engraving's depth, within the word's own footprint.
    The window itself is the family's ``label_window``, imported rather than
    re-derived: this file used to carry its own copy, and the copy carried the
    same bug (a window centred on the label's *anchor* rather than on its ink,
    which clipped BITS' own glyphs out of their exception).
    """
    half = cover_w / 2
    x_lo, x_hi, z_lo, z_hi = label_window(
        text, label_size, label_z, cover_h, horizontal
    )

    def on_label_glyph(e) -> bool:
        centre = e.center()
        return (
            # Cut *into* the -Y face: the mouth lies on it, the floor LABEL_DEPTH
            # behind it, and the chamfer wall between the two.
            -half - 0.05 <= centre.Y <= -half + c.LABEL_DEPTH + 0.05
            and x_lo <= centre.X <= x_hi
            and z_lo <= centre.Z <= z_hi
        )

    return ((on_label_glyph, "engraved cover label -- bevelling a glyph destroys it"),)


def _hex_base_allow(base: Part, has_legend: bool) -> tuple:
    """The hex base's legitimate exceptions, each named with its reason.

    The same ones the base claims (``drill_storage.checks._base_allow``),
    re-derived against this base's own shortened body -- and the legend one only
    for the box that actually carries a legend, so the BITS base is held to the
    stricter standard its blank walls deserve.
    """
    top = c.BASE_FOOT_TOP
    # Only the ALLEN box engraves one, and only its own rows decide where the
    # ink sits -- the BITS base's walls are blank and get no legend exception
    # at all, so the window is not even computed for it.
    legend_rows = c.socket_layout("allen")[1] if has_legend else None
    legend_lo, legend_hi = (
        wall_legend_window(legend_rows, c.LEGEND_Z, c.LEGEND_LINE_H)
        if legend_rows
        else (0.0, 0.0)
    )

    def on_cover_seat(e) -> bool:
        b = e.bounding_box()
        return abs(b.min.Z - top) < 0.05 and abs(b.max.Z - top) < 0.05

    def on_wall_legend(e) -> bool:
        b = e.bounding_box()
        half = BODY_W / 2
        # In a front/back wall plane -- the only two engrave_row_legend cuts.
        if not (abs(abs(b.min.Y) - half) < 0.05 and abs(abs(b.max.Y) - half) < 0.05):
            return False
        # ...and inside the legend block itself, which is what makes this the
        # legend rather than "anything on that wall": the shoulder rim, the foot
        # and the collar all lie outside the band. The band is *measured* off
        # the glyphs (``wall_legend_window``) rather than estimated at
        # 0.75 * font_size: the estimate is symmetric and the ink is not, and it
        # fell 0.10 mm short of the top row's own "8" on the ALLEN base.
        return legend_lo <= e.center().Z <= legend_hi

    allow = (
        (
            on_cover_seat,
            "cover seat is deliberately flat so the cover's chamfered "
            "rim lands flat-on-flat (box.create_cover's COVER_SEAT_CH)",
        ),
        (
            lambda e: is_flush_seam(base, e),
            "the key slot's mouth fillet, anchored flush with the cavity "
            "wall -- a genuine 180 deg split OCC left as two faces rather "
            "than one, confirmed by matching face normals, two per base "
            "(see drill_storage.base.key_slot_tool)",
        ),
    )
    if has_legend:
        allow += (
            (on_wall_legend, "engraved size legend -- bevelling a glyph destroys it"),
        )
    return allow


def _socket_cut_r(part: Part, x: float, y: float, z: float) -> float:
    """The circumradius a hex socket is *really* cut at, measured off the solid.

    Bisected outward from the socket's centre along +X, where the socket's
    ``RegularPolygon`` puts its first vertex, so what is found is the
    circumradius and not the apothem -- the same ray the socket-width check
    samples on. Bisection rather than a two-point straddle because the number
    this exists to catch differs by ~0.03 mm, far inside ``PROBE``.
    """
    lo, hi = 0.5, 8.0
    while hi - lo > 1e-4:
        mid = (lo + hi) / 2
        if is_solid_at(part, x + mid, y, z):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def check_box(
    r: Report,
    name: str,
    bit_len: float,
    label: str,
    has_legend: bool,
    expected_assembled: float,
    expected_proud: float,
    expected_depth: float,
) -> None:
    """Everything that has to hold for one hex box, on its three built parts.

    The horizontal envelope is the shared family 1x1 set (``config``); the
    per-box deviations -- guide across-flats, guide mouth chamfer, cartridge
    mouth chamfer -- come from ``config.box_fits``.
    """
    guide_af, guide_mouth_ch, cart_mouth_ch = c.box_fits(name)
    hex_bores, rows, pos = c.socket_layout(name)
    floor_z = c.guide_floor_z(name)

    base = create_base(
        hex_bores,
        guide_af=guide_af,
        guide_mouth_ch=guide_mouth_ch,
        guide_floor_z=floor_z,
        rows=rows if has_legend else None,
        hole_pos=pos if has_legend else None,
    )
    insert = create_insert(hex_bores, mouth_ch=cart_mouth_ch)
    cover_h = c.cover_h_for(bit_len, floor_z)
    size, label_z, horizontal = label_fit(cover_h, label)
    cover = create_cover(
        label,
        cover_h=cover_h,
        label_size=size,
        label_z=label_z,
        label_horizontal=horizontal,
    )

    r.section(f"hex {label}")

    # Envelope and print pose.
    bb = base.bounding_box()
    r.check(
        abs(bb.min.Z) < 0.02 and abs(bb.size.Z - c.BASE_TOTAL_H) < 0.05,
        "base is BASE_TOTAL_H tall and sits on z=0 (print pose)",
        f"{bb.size.Z:.2f} mm, min z {bb.min.Z:.3f}",
    )
    # BODY_W is the pad, so the body, the foot and the cover are all one 1x1
    # Gridfinity envelope and nothing on the part reaches outside it.
    r.check(
        abs(bb.size.X - c.BODY_W) < 0.05 and abs(bb.size.Y - c.BODY_W) < 0.05,
        f"base footprint is the shared {c.BODY_W:.1f} mm 1x1 Gridfinity pad",
        f"{bb.size.X:.2f} x {bb.size.Y:.2f} mm",
    )
    ib = insert.bounding_box()
    r.check(
        abs(ib.min.Z) < 0.02 and abs(ib.size.Z - c.CART_H) < 0.05,
        "insert is CART_H tall and sits on z=0 (print pose)",
        f"{ib.size.Z:.2f} mm, min z {ib.min.Z:.3f}",
    )
    cbb = cover.bounding_box()
    r.check(
        abs(cbb.min.Z) < 0.02 and abs(cbb.size.Z - cover_h) < 0.05,
        "cover is built to its derived height and sits on z=0 (print pose)",
        f"{cbb.size.Z:.2f} mm (want {cover_h:.2f})",
    )
    r.check(
        abs(cbb.size.X - c.COVER_W) < 0.05 and abs(cbb.size.Y - c.COVER_W) < 0.05,
        f"cover is the shared {c.COVER_W:.1f} mm width, flush with the base",
        f"{cbb.size.X:.2f} mm (want {c.COVER_W:.2f})",
    )

    # The assembled envelope: a whole Gridfinity unit, matching the docstring.
    assembled = c.BASE_FOOT_TOP + cover_h
    r.check(
        abs(assembled - expected_assembled) < 0.05,
        "assembled envelope matches the module docstring",
        f"{assembled:.0f} mm (want {expected_assembled:.0f})",
    )
    r.check(
        abs(assembled % HEIGHT_UNIT) < TOL,
        "assembled envelope is a whole Gridfinity Z unit",
        f"{assembled:.0f} mm = {assembled / HEIGHT_UNIT:.0f}U",
    )
    headroom = (assembled - CAP_H) - (floor_z + bit_len)
    r.check(
        headroom >= c.COVER_TIP_CLEARANCE - TOL,
        "the longest tip clears the cap ceiling by the clearance asked for",
        f"{headroom:.2f} mm >= {c.COVER_TIP_CLEARANCE:.2f}",
    )
    proud = (floor_z + bit_len) - c.BASE_TOTAL_H
    r.check(
        abs(proud - expected_proud) < 0.05,
        "a bit stands proud of the base by the documented amount",
        f"{proud:.1f} mm (want {expected_proud:.1f})",
    )
    # ...and the hole it went into is the depth the box asked for. Measured off
    # the floor the base was actually built with rather than off the config
    # constant, so this fails if a box's depth is changed in ``config`` and the
    # geometry, the cover or the docs are not brought along with it.
    depth = c.BASE_TOTAL_H - floor_z
    r.check(
        abs(depth - expected_depth) < 0.05,
        "a bit sinks the documented depth below the base rim",
        f"{depth:.1f} mm (want {expected_depth:.1f}), leaving {proud:.1f} proud "
        f"of a {bit_len:.0f} mm tool",
    )
    # What a deeper hole runs out of first: the solid body between the bore
    # floor and the Gridfinity foot. Nothing else watches it -- ``floor_intact``
    # below only samples 0.3 mm under the floor, so it would still pass with the
    # bores opening into the foot's chamfer. ALLEN's 21 mm hole leaves 4.6 mm
    # here; MIN_WALL is the printable floor, and any box wanting more depth than
    # that allows has to move ``BASE_TOTAL_H``, not this number.
    under_floor = floor_z - BASE_H
    r.check(
        under_floor >= MIN_WALL - TOL,
        "the bores stop clear of the Gridfinity foot",
        f"{under_floor:.2f} mm of solid body between the floor and BASE_H "
        f"({BASE_H:.1f}), want >= {MIN_WALL:.1f}",
    )

    # The two grooves cut into the collar are the only features on this base
    # hanging off a vertical wall, and nothing else in this file would catch
    # them: a groove is a mating feature, so the sharp-edge audit used to name
    # its lips; one is a ring inside a cavity and the other a ring behind the
    # cover, so no rendered view shows either; and each bead lives on the *other*
    # part, so no check on one part alone can see the two interfere. Measured off
    # the solid, as the family does -- same grooves, same argument, in
    # ``drill_storage.config`` and ``drill_storage.box``.
    steepest, where = worst_overhang(base, c.BASE_FOOT_TOP, c.BASE_TOTAL_H)
    r.check(
        steepest <= c.MAX_OVERHANG + 0.5,
        "nothing on the collar overhangs past what FDM prints unsupported",
        f"steepest downward face {steepest:.1f} deg off vertical at {where} "
        f"(max {c.MAX_OVERHANG:.0f}), sampled over "
        f"z={c.BASE_FOOT_TOP:.1f}..{c.BASE_TOTAL_H:.1f}",
    )
    for what, bead_z, prot, lead, back, tip, bead_wall, mate, sign in (
        ("cartridge", c.BEAD_Z, c.CART_BEAD, c.BEAD_LEAD_IN, c.BEAD_BACK,
         c.BEAD_TIP_FLAT, c.CART_W / 2, c.CAVITY_W / 2, +1.0),
        ("cover", c.BASE_FOOT_TOP + SNAP_Z, SNAP_PROTRUSION, SNAP_LEAD_IN,
         SNAP_BACK, SNAP_TIP_FLAT, INNER_W / 2, c.COLLAR_W / 2, -1.0),
    ):
        bite, at_z = worst_bead_bite(
            base, bead_z, prot, lead, back, tip,
            bead_wall=bead_wall, mating_wall=mate, sign=sign,
        )
        r.check(
            bite < 0.0,
            f"the seated {what} bead is clear of the base over its whole profile",
            "sampled at 101 heights across the bead"
            if bite < 0.0
            else f"{bite:.2f} mm of interference at z={at_z:.2f}",
        )
    # ...and the two grooves in that one ring of wall still miss each other,
    # lip to lip -- neither is symmetric about its own bead any more.
    r.check(
        c.GROOVE_LIP_GAP > 0.0,
        "cover groove and cartridge groove never thin the same wall",
        f"{c.GROOVE_LIP_GAP:.2f} mm between their lips "
        f"({c.GROOVE_SEPARATION:.1f} mm centre to centre)",
    )

    # The sockets in the insert: a land at the bottom (HEX_LAND_FIT) and a
    # relieved guide above (RELIEF_FIT), the same profile the drill sets cut.
    z_land = c.BORE_FOOT_RELIEF + c.EFFECTIVE_LAND_H / 2
    z_relief = c.LAND_H + c.LAND_LEAD_IN + 2.0
    land_r = (c.HEX_AF + c.HEX_LAND_FIT) / 3**0.5
    rc = c.HEX_SOCKET_R
    ok = all(
        not is_solid_at(insert, x + land_r - PROBE, y, z_land)
        and is_solid_at(insert, x + land_r + PROBE, y, z_land)
        and not is_solid_at(insert, x + rc - PROBE, y, z_relief)
        and is_solid_at(insert, x + rc + PROBE, y, z_relief)
        for _af, x, y in hex_bores
    )
    r.check(
        ok,
        f"all {len(hex_bores)} sockets: land at HEX_LAND_FIT, relief at RELIEF_FIT",
        f"land r {land_r:.3f} / relief r {rc:.3f} mm, sampled at insert z "
        f"{z_land:.2f} and {z_relief:.2f}",
    )
    # The two bounds the tightened land has to stay inside (config's "The grip").
    # A socket here is named by HEX_AF, so its land carries HEX_CLEARANCE the
    # family's does not: measured from the *shank*, it may come down to the
    # family's own hex land and no further, or the step has overshot the one
    # number that was ever proven on printed cartridges.
    over_shank = (c.HEX_AF + c.HEX_LAND_FIT) - c.HEX_SHANK_AF
    r.check(
        fam.HEX_LAND_FIT - TOL <= over_shank <= fam.HEX_LAND_FIT + c.HEX_CLEARANCE,
        "the tightened land stays between the family's hex land and the "
        "untightened one",
        f"shank +{over_shank:.2f} mm, between +{fam.HEX_LAND_FIT:.2f} (family) "
        f"and +{fam.HEX_LAND_FIT + c.HEX_CLEARANCE:.2f} (untightened), "
        f"tightened by {c.HEX_LAND_TIGHTEN:.2f}",
    )
    # ...and the split's own premise: the rigid guide below clears where the TPU
    # land grips. A guide that gripped, or a land that cleared, would each
    # quietly defeat the two-material design, and tightening the land is exactly
    # the edit that could invert them.
    r.check(
        guide_af > c.HEX_AF + c.HEX_LAND_FIT,
        "the rigid guide stays looser than the TPU land it feeds",
        f"guide {guide_af:.2f} mm across-flats vs land "
        f"{c.HEX_AF + c.HEX_LAND_FIT:.2f}",
    )
    ok = all(
        not is_solid_at(insert, x, y, z)
        for _af, x, y in hex_bores
        for z in (0.05, c.CART_H / 2, c.CART_H - 0.05)
    )
    r.check(
        ok,
        "every socket is open top to bottom",
        f"{len(hex_bores)} sockets sampled at 3 heights",
    )

    # What you pack is what you cut. The check above only proves the socket is
    # the size the *config* says; this one compares the radius the layout
    # reserved against the radius the cutter took out of the solid, measured off
    # the insert. The two were 0.03 mm apart on the old one-material base --
    # hex.py reserved HEX_AF/sqrt(3) while box.cut_holes sank
    # (HEX_AF + HEX_SLIP)/sqrt(3) -- and every downstream number still measured
    # "fine". Only comparing the two radii to each other catches it.
    cut = [_socket_cut_r(insert, x, y, z_relief) for _af, x, y in hex_bores]
    r.check(
        max(abs(rad - c.HEX_SOCKET_R) for rad in cut) < 0.005,
        "every socket is cut at exactly the circumradius the layout reserved",
        f"reserved {c.HEX_SOCKET_R:.4f} mm, cut {min(cut):.4f}..{max(cut):.4f} mm",
    )
    # ...and the layout that reservation produced still holds when it is
    # re-derived from the radii actually cut, against the same cartridge
    # envelope the packer packed into. This is the other half of the same
    # guard: it fails whether the packer under-books the socket or the cutter
    # grows it. Each box checks against its own budgets: ALLEN keeps the
    # family's (PACK_WALL_CLEARANCE / PACK_HOLE_WALL), BITS the shaved ones:
    # a wall budget of CART_WALL + cart_mouth_ch (1.2) and the between-socket
    # rule at the shaved chamfer -- two mouth chamfers plus a sliver (0.5).
    # BITS_PITCH is derived so the outermost sockets sit exactly on the wall
    # budget, which is why the edge sockets land at 0.0 slack here; what
    # actually binds is the top-rim wall, CART_WALL (1.0), measured
    # separately below. The check stays conservative for the corner sockets:
    # the SDF charges the true nearest-surface distance, which is the flat
    # face (the corner arc's nearest point is a tangent point, farther out),
    # and the hexagon sits inside its circumcircle (config's footprints
    # section has the argument).
    if name == "bits":
        hole_wall = 2 * cart_mouth_ch + 0.1
        wall_clearance = c.CART_WALL + cart_mouth_ch
    else:
        hole_wall = c.PACK_HOLE_WALL
        wall_clearance = c.PACK_WALL_CLEARANCE
    slack, what = worst_slack(
        [(x, y) for _af, x, y in hex_bores],
        cut,
        c.CART_W / 2,
        c.CART_R,
        hole_wall,
        wall_clearance,
    )
    r.check(
        slack >= -PACK_ROUNDING,
        "every socket meets its wall clearance and its neighbours",
        f"tightest {what}, {slack:+.4f} mm over the requirement "
        f"(wall {wall_clearance:.2f}, hole {hole_wall:.2f})",
    )

    # The BITS box's whole point: a literal 4x4 grid at the shaved pitch, and
    # every margin the shave trades on, pinned by name (the argument is in
    # config's footprints section). The radii below are the measured cuts from
    # the insert, so the reservations and the cuts cannot drift apart.
    if name == "bits":
        xs = sorted({round(x, 3) for _af, x, _y in hex_bores})
        ys = sorted({round(y, 3) for _af, _x, y in hex_bores})
        r.check(
            len(hex_bores) == c.BITS_GRID**2
            and len(xs) == c.BITS_GRID
            and len(ys) == c.BITS_GRID,
            "exactly 16 sockets in a 4x4 square grid",
            f"{len(hex_bores)} sockets, {len(xs)} x-columns, {len(ys)} y-rows",
        )
        pitch_x = [b - a for a, b in zip(xs, xs[1:])]
        pitch_y = [b - a for a, b in zip(ys, ys[1:])]
        r.check(
            all(abs(p - c.BITS_PITCH) < 0.01 for p in pitch_x + pitch_y),
            "the grid is even at the solved BITS_PITCH",
            f"pitch {c.BITS_PITCH:.3f} mm, measured {pitch_x} x / {pitch_y} y",
        )

        half = c.CART_W / 2
        positions = [(x, y) for _af, x, y in hex_bores]

        # The top-rim wall is the binding one: the mouth chamfer widens every
        # bore by BITS_CART_MOUTH_CH radially at the cartridge's top face, so
        # the wall there is exactly one chamfer thinner than the flat-face
        # wall -- and BITS_PITCH is derived to land it on CART_WALL. Measured
        # with the rounded-square SDF, which is the true distance to the wall
        # surface: every socket's nearest surface is a flat face (the corner
        # sockets included -- 5.14 mm to the flat face against 6.16 mm to the
        # corner arc's nearest point, at its tangent points), so the
        # flat-face budget is exactly what the edge sockets sit on.
        # The design sits on the floor exactly, so the tolerance is one order
        # over the bisection the measured radii resolve to (~1e-4 mm) and
        # float noise, and far under any real regression.
        top_rim = min(
            -sdf(x, y, half, c.CART_R) - (rad + cart_mouth_ch)
            for (x, y), rad in zip(positions, cut)
        )
        r.check(
            top_rim >= c.CART_WALL - 1e-3,
            "every BITS socket keeps CART_WALL to the cartridge wall at the top rim",
            f"{top_rim:.3f} mm (want >= {c.CART_WALL:.1f})",
        )

        # The land is the narrowest cut (HEX_LAND_FIT), so the material
        # between neighbours at the land is the second binding gap, and it
        # holds the printable floor.
        land_gap = min(
            math.dist(positions[i], positions[j]) - 2 * land_r
            for i, j in itertools.combinations(range(len(positions)), 2)
        )
        r.check(
            land_gap >= MIN_WALL - TOL,
            "BITS lands keep MIN_WALL of TPU between neighbours",
            f"{land_gap:.3f} mm (want >= {MIN_WALL:.1f})",
        )

        # The relief is the widest cut (RELIEF_FIT), so at the relief z the
        # material between neighbours is thinner than at the land -- and no
        # other check watches it: the land check samples the land z, so a
        # wider RELIEF_FIT eats this gap while the land still holds MIN_WALL.
        # It holds the family's between-socket floor instead, measured off
        # the solid like the mouth check (config.BITS_RELIEF_GAP_FLOOR; the
        # argument is in config's footprints section).
        relief_gap = min(
            math.dist(positions[i], positions[j]) - cut[i] - cut[j]
            for i, j in itertools.combinations(range(len(positions)), 2)
        )
        r.check(
            relief_gap >= c.BITS_RELIEF_GAP_FLOOR - TOL,
            "BITS relief bores keep the between-socket floor between neighbours",
            f"{relief_gap:.3f} mm (want >= {c.BITS_RELIEF_GAP_FLOOR:.2f})",
        )

        # Cartridge mouths: two neighbouring lead-ins must not merge -- the
        # gap between the chamfered mouths, p - 2 x (r + chamfer), keeps a
        # 0.1 mm sliver (the same rule as the family's PACK_HOLE_WALL, written
        # out by name because the shaved chamfer is the whole point here).
        mouth_gap = min(
            math.dist(positions[i], positions[j]) - cut[i] - cut[j] - 2 * cart_mouth_ch
            for i, j in itertools.combinations(range(len(positions)), 2)
        )
        r.check(
            mouth_gap >= 0.1 - TOL,
            "neighbouring BITS cartridge mouths keep a 0.1 mm sliver",
            f"{mouth_gap:.3f} mm",
        )

    # The guides: bored in the base at the box's guide across-flats -- loose,
    # because the base guides and the insert grips -- open from the floor to
    # the cavity, and their mouths clear each other.
    gr = guide_af / 3**0.5
    z_mid = floor_z + c.guide_h(name) / 2
    ok = all(
        not is_solid_at(base, x + gr - PROBE, y, z_mid)
        and is_solid_at(base, x + gr + PROBE, y, z_mid)
        for _af, x, y in hex_bores
    )
    r.check(
        ok,
        f"all {len(hex_bores)} guides bored at {guide_af:g} mm across-flats",
        f"circumradius {gr:.3f} mm, sampled z={z_mid:.1f}",
    )
    open_span = all(
        not is_solid_at(base, x, y, z)
        for _af, x, y in hex_bores
        for z in (floor_z + 0.3, z_mid, c.CAVITY_FLOOR_Z - 0.3)
    )
    r.check(
        open_span,
        "every guide is open from its floor to the cavity",
        f"{len(hex_bores)} guides sampled at 3 heights",
    )
    floor_intact = all(
        is_solid_at(base, x, y, floor_z - 0.3) for _af, x, y in hex_bores
    )
    r.check(
        floor_intact,
        "the base floor under every guide is solid",
        "a bit rests on the rigid base, not on air",
    )
    # layout_bores packs on the cartridge's relieved bore and knows nothing about
    # how wide the guide is cut, so widening GUIDE_FIT spends a wall nothing else
    # is watching. This is the check that stops it going too far.
    guides = [(f"h{i}", gr, x, y) for i, (_af, x, y) in enumerate(hex_bores)]
    worst_key, worst = "", math.inf
    for (k1, r1, x1, y1), (k2, r2, x2, y2) in itertools.combinations(guides, 2):
        gap = math.dist((x1, y1), (x2, y2)) - r1 - r2
        if gap < worst:
            worst, worst_key = gap, f"{k1}<->{k2}"
    mouth_budget = 2 * guide_mouth_ch + 0.1
    r.check(
        worst >= mouth_budget - TOL,
        "neighbouring guide mouths do not run into each other",
        f"worst {worst_key} = {worst:.2f} mm (budget {mouth_budget:.2f})",
    )
    # The guides are bored below the cavity floor, where the body is solid
    # across the full pad -- the cavity only exists above CAVITY_FLOOR_Z. So the
    # wall this check protects is the base's outer wall, not the cavity's.
    reach = max(max(abs(x), abs(y)) + gr for _af, x, y in hex_bores)
    r.check(
        reach + MIN_WALL <= c.BODY_W / 2 + TOL,
        "every guide keeps a printable wall to the base's outer wall",
        f"reach {reach:.2f} of {c.BODY_W / 2:.2f} mm",
    )

    # The ALLEN wall legend: the keys on one line must not collide, and the
    # block must land on the body wall. (A legend box always has rows and a
    # position map -- socket_layout returns them only when has_legend.)
    if has_legend:
        assert rows is not None and pos is not None
        for line in rows:
            xs = sorted((pos[k][0], k) for k in line)
            for (x1, k1), (x2, k2) in zip(xs, xs[1:]):
                half = 0.31 * WALL_LABEL_SIZE * (len(k1) + len(k2))
                r.check(
                    x2 - x1 >= half - TOL,
                    f"legend labels {k1!r} and {k2!r} do not collide",
                    f"{x2 - x1:.2f} mm apart, need {half:.2f}",
                )
        block = (c.LEGEND_ROWS - 1) * c.LEGEND_LINE_H / 2 + c.LEGEND_GLYPH_H / 2
        r.check(
            c.LEGEND_Z - block >= BASE_H + TOL
            and c.LEGEND_Z + block <= c.BASE_FOOT_TOP + TOL,
            f"the {c.LEGEND_ROWS}-line legend block fits the body wall",
            f"{c.LEGEND_Z - block:.2f} to {c.LEGEND_Z + block:.2f} mm "
            f"of {BASE_H:.1f}-{c.BASE_FOOT_TOP:.1f}, pitch {c.LEGEND_LINE_H:.1f}",
        )

    # Edge treatment, per the house rule: chamfer horizontal edges, fillet
    # vertical ones, and name every legitimate exception.
    base_edges = sharp_convex_edges(base, allow=_hex_base_allow(base, has_legend))
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
    insert_edges = sharp_convex_edges(insert)
    r.check(
        not insert_edges.sharp,
        "insert has no sharp convex edges at all",
        f"{len(insert_edges.sharp)} found"
        if insert_edges.sharp
        else "none, no exceptions",
    )
    r.check(
        not insert_edges.unclassifiable,
        "insert has no unclassifiable convex edges at all",
        f"{len(insert_edges.unclassifiable)} found"
        if insert_edges.unclassifiable
        else "none, no exceptions",
    )
    cover_edges = sharp_convex_edges(
        cover,
        allow=_cover_allow(label, size, label_z, cover_h, horizontal, c.COVER_W),
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


def run() -> Report:
    """Every assertion for the two hex boxes -- ``uv run check drill_storage.hex``."""
    r = Report()
    r.section("hex: bit sizes")
    r.check(
        c.ALLEN_SIZES == sorted(c.ALLEN_SIZES, reverse=True),
        "ALLEN_SIZES is documented largest-first",
        f"{c.ALLEN_SIZES}",
    )
    r.check(
        c.socket_layout("allen")[1] is not None and c.socket_layout("bits")[1] is None,
        "only the ALLEN box carries a wall legend (BITS is a mixed bag)",
        "ALLEN rows from layout_bores, BITS none",
    )
    check_box(
        r,
        "allen",
        c.ALLEN_BIT_LEN,
        "ALLEN",
        True,
        63.0,
        29.0,
        21.0,
    )
    check_box(
        r,
        "bits",
        c.BITS_BIT_LEN,
        "BITS",
        False,
        42.0,
        10.0,
        15.0,
    )
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
