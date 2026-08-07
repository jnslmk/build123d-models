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

What this file cannot tell you is whether the grip is right. ``HEX_LAND_FIT``
is the family's judgement, settled by printed cartridges -- see
``config.LAND_EASE`` and ``docs/design-notes.md``.
"""

from __future__ import annotations

import itertools
import math
import sys

from build123d import BuildSketch, Part, Text

from ...lib.checks import TOL as TOL
from ...lib.checks import Report as Report
from ...lib.checks import is_solid_at as is_solid_at
from ...lib.checks import sharp_convex_edges
from ..box import (
    BASE_H,
    BODY_W,
    CAP_H,
    HEIGHT_UNIT,
    SNAP_GROOVE_R,
    SNAP_Z,
    WALL_LABEL_SIZE,
)
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

# The block a wall legend really occupies is estimated from ``0.75 * font_size``
# (build123d renders digits at about that), which is a rule of thumb rather than
# a measurement -- a real glyph's ink can sit a few tenths outside it. Used only
# to widen the band an allow-predicate calls "the legend", never a clearance.
LEGEND_INK_PAD = 0.3


def _label_window(
    text: str,
    label_size: float,
    label_z: float,
    cover_h: float,
    horizontal: bool,
    cover_w: float,
) -> tuple[float, float, float]:
    """Where an engraved cover label really lands, in print pose.

    Returns ``(x_half, z_centre, z_half)``: the half-width along x, and the band
    along z, that the glyphs occupy on the label face.

    Measured off the same ``Text`` sketch ``hex.cover.create_cover`` engraves
    rather than estimated from the font size, because the two differ by a lot --
    a word is three times longer than it is tall, and which of those runs along
    z depends on ``horizontal``. ``create_cover`` builds the label on the +Y
    face at ``label_z`` and then flips the part into print pose
    (``Rotation(180,0,0)`` plus a re-seat on z=0), which puts the label on **-Y**
    at ``cover_h - label_z`` -- so this reports the flipped coordinates, which
    are the ones an edge of the returned part actually has.

    Both spans are grown by ``LABEL_CHAMFER`` (the bevel on the glyph mouths
    reaches outside the glyph itself) plus a small pad. This is the family's
    ``drill_storage.checks._label_window``, at any cover width.
    """
    with BuildSketch() as sk:
        Text(text, font_size=label_size)
    box = sk.sketch.bounding_box()
    run, thick = box.size.X, box.size.Y  # along the reading direction, and across
    grow = c.LABEL_CHAMFER + 0.5
    return (
        (run if horizontal else thick) / 2 + grow,
        cover_h - label_z,
        (thick if horizontal else run) / 2 + grow,
    )


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
    """
    half = cover_w / 2
    x_half, z_mid, z_half = _label_window(
        text, label_size, label_z, cover_h, horizontal, cover_w
    )

    def on_label_glyph(e) -> bool:
        centre = e.center()
        return (
            # Cut *into* the -Y face: the mouth lies on it, the floor LABEL_DEPTH
            # behind it, and the chamfer wall between the two.
            -half - 0.05 <= centre.Y <= -half + c.LABEL_DEPTH + 0.05
            and abs(centre.X) <= x_half
            and abs(centre.Z - z_mid) <= z_half
        )

    return ((on_label_glyph, "engraved cover label -- bevelling a glyph destroys it"),)


def _hex_base_allow(has_legend: bool) -> tuple:
    """The hex base's legitimate exceptions, each named with its reason.

    The same three the shell claims (``drill_storage.checks._shell_allow``),
    re-derived against this base's own shortened body -- and the legend one only
    for the box that actually carries a legend, so the BITS base is held to the
    stricter standard its blank walls deserve.
    """
    top = c.BASE_FOOT_TOP

    def on_cover_seat(e) -> bool:
        b = e.bounding_box()
        return abs(b.min.Z - top) < 0.05 and abs(b.max.Z - top) < 0.05

    def on_a_groove(e) -> bool:
        b = e.bounding_box()
        if abs(b.max.Z - b.min.Z) > 0.05:
            return False
        # The cover's snap groove and the cartridge's bead groove, both round
        # rings cut into the collar.
        for z in (top + SNAP_Z, c.BEAD_Z):
            if abs(b.min.Z - (z - SNAP_GROOVE_R)) < 0.05:
                return True
            if abs(b.min.Z - (z + SNAP_GROOVE_R)) < 0.05:
                return True
        return False

    def on_wall_legend(e) -> bool:
        b = e.bounding_box()
        half = BODY_W / 2
        # In a front/back wall plane -- the only two engrave_row_legend cuts.
        if not (abs(abs(b.min.Y) - half) < 0.05 and abs(abs(b.max.Y) - half) < 0.05):
            return False
        # ...and inside the legend block itself, which is what makes this the
        # legend rather than "anything on that wall": the shoulder rim, the foot
        # and the collar all lie outside the band.
        block = (
            (c.LEGEND_ROWS - 1) * c.LEGEND_LINE_H / 2
            + c.LEGEND_GLYPH_H / 2
            + LEGEND_INK_PAD
        )
        return abs(e.center().Z - c.LEGEND_Z) <= block

    allow = (
        (
            on_cover_seat,
            "cover seat is deliberately flat so the cover's chamfered "
            "rim lands flat-on-flat (box.create_cover's COVER_SEAT_CH)",
        ),
        (
            on_a_groove,
            "round snap-groove rims -- the grooves are the mating "
            "features, and rounding their lips would shrink engagement",
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
) -> None:
    """Everything that has to hold for one hex box, on its three built parts.

    The horizontal envelope is the shared family 1x1 set (``config``); the
    per-box deviations -- guide across-flats, guide mouth chamfer, cartridge
    mouth chamfer -- come from ``config.box_fits``.
    """
    guide_af, guide_mouth_ch, cart_mouth_ch = c.box_fits(name)
    hex_bores, rows, pos = c.socket_layout(name)

    base = create_base(
        hex_bores,
        guide_af=guide_af,
        guide_mouth_ch=guide_mouth_ch,
        rows=rows if has_legend else None,
        hole_pos=pos if has_legend else None,
    )
    insert = create_insert(hex_bores, mouth_ch=cart_mouth_ch)
    cover_h = c.cover_h_for(bit_len)
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
    headroom = (assembled - CAP_H) - (c.GUIDE_FLOOR_Z + bit_len)
    r.check(
        headroom >= c.COVER_TIP_CLEARANCE - TOL,
        "the longest tip clears the cap ceiling by the clearance asked for",
        f"{headroom:.2f} mm >= {c.COVER_TIP_CLEARANCE:.2f}",
    )
    proud = (c.GUIDE_FLOOR_Z + bit_len) - c.BASE_TOTAL_H
    r.check(
        abs(proud - expected_proud) < 0.05,
        "a bit stands proud of the base by the documented amount",
        f"{proud:.1f} mm (want {expected_proud:.1f})",
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
    z_mid = c.GUIDE_FLOOR_Z + c.GUIDE_H / 2
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
        for z in (c.GUIDE_FLOOR_Z + 0.3, z_mid, c.CAVITY_FLOOR_Z - 0.3)
    )
    r.check(
        open_span,
        "every guide is open from its floor to the cavity",
        f"{len(hex_bores)} guides sampled at 3 heights",
    )
    floor_intact = all(
        is_solid_at(base, x, y, c.GUIDE_FLOOR_Z - 0.3) for _af, x, y in hex_bores
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
    bad_base = sharp_convex_edges(base, allow=_hex_base_allow(has_legend))
    r.check(
        not bad_base,
        "base has no unexplained sharp convex edges",
        f"{len(bad_base)} found" if bad_base else "all treated or named",
    )
    bad_insert = sharp_convex_edges(insert)
    r.check(
        not bad_insert,
        "insert has no sharp convex edges at all",
        f"{len(bad_insert)} found" if bad_insert else "none, no exceptions",
    )
    bad_cover = sharp_convex_edges(
        cover,
        allow=_cover_allow(label, size, label_z, cover_h, horizontal, c.COVER_W),
    )
    r.check(
        not bad_cover,
        "cover has no unexplained sharp convex edges",
        f"{len(bad_cover)} found" if bad_cover else "all treated or named",
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
        70.0,
        35.0,
    )
    check_box(
        r,
        "bits",
        c.BITS_BIT_LEN,
        "BITS",
        False,
        42.0,
        10.0,
    )
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
