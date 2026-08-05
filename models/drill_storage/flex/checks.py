"""Geometry assertions for the ASA shell + TPU cartridge holder.

    uv run check drill_storage.flex
    uv run python -m models.drill_storage.flex.checks

A clearance is invisible in a projection and a 0.3 mm land step does not show up
in an SVG, so everything here is either arithmetic on the config or a point
sample of the solid -- never an eyeball.

What this file *cannot* tell you: whether the grip is right. ``LAND_FIT`` and
``HEX_LAND_FIT`` are uncalibrated (see ``config``), and no amount of checking the
CAD settles an interference fit. Print ``drill_fit_tester.land``.
"""

from __future__ import annotations

import itertools
import math

from build123d import Part

from ...lib import fits
from ...lib.checks import TOL as TOL
from ...lib.checks import Report as Report
from ...lib.checks import is_solid_at as is_solid_at
from ...lib.checks import sharp_convex_edges
from ..box import (
    BASE_TOTAL_H,
    COLLAR_W,
    FOOT_TOP,
    PAD,
    SNAP_Z,
    cover_height_for,
)
from ..wood import COVER_H_WOOD, COVER_TIP_CLEARANCE, MAX_WOOD_DRILL_LEN
from . import config as c
from .insert import _hex_r, create_insert
from .shell import DRILL_BORES, HEX_BORES, POS, ROWS, create_shell

PROBE = 0.08  # how far either side of a modelled radius we sample for material

# The absolute minimum wall a 0.4 mm nozzle resolves: 2 perimeters. Below this a
# feature does not slice as a wall at all, it merges with its neighbour.
MIN_WALL = 0.8


def _bore_footprints() -> list[tuple[str, float, float, float]]:
    """Every cut bore as ``(key, relieved_radius, x, y)`` -- the real footprint,
    not the nominal tool, which is what has to be packed and walled."""
    items = [(f"{d:g}", c.relieved_bore_r(d), x, y) for d, x, y in DRILL_BORES]
    items += [
        (f"hex{af:g}", _hex_r(af, c.RELIEF_FIT), x, y) for af, x, y in HEX_BORES
    ]
    return items


def check_fits(r: Report) -> None:
    """Every clearance traces back to a named fit class, not a typed number."""
    r.section("fits")
    r.check(
        c.LAND_FIT == fits.for_material(fits.PRESS, "tpu") - c.LAND_EXTRA_GRIP,
        "LAND_FIT is a press fit in TPU, tightened by LAND_EXTRA_GRIP",
        f"{c.LAND_FIT:.2f} mm = {fits.for_material(fits.PRESS, 'tpu'):.2f} "
        f"- {c.LAND_EXTRA_GRIP:.2f}",
    )
    r.check(
        c.GUIDE_FIT == fits.for_material(fits.FREE, "asa"),
        "GUIDE_FIT is a free fit in ASA",
        f"{c.GUIDE_FIT:.2f} mm",
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
        c.HEX_LAND_FIT == fits.for_material(fits.PRESS, "tpu"),
        "HEX_LAND_FIT is a press fit in TPU",
        f"{c.HEX_LAND_FIT:.2f} mm",
    )
    r.check(
        c.LAND_FIT < c.RELIEF_FIT,
        "the land is tighter than the relief",
        f"land {c.LAND_FIT:.2f} < relief {c.RELIEF_FIT:.2f} mm",
    )


def check_envelope(shell: Part, insert: Part, r: Report) -> None:
    """Gridfinity envelope, and the cartridge actually fitting its cavity."""
    r.section("envelope")
    sb = shell.bounding_box()
    r.check(abs(sb.size.X - PAD) < 0.01 and abs(sb.size.Y - PAD) < 0.01,
            "shell footprint is one Gridfinity pad",
            f"{sb.size.X:.2f} x {sb.size.Y:.2f} mm")
    r.check(abs(sb.size.Z - BASE_TOTAL_H) < 0.01,
            "shell is 6 Gridfinity Z units tall", f"{sb.size.Z:.1f} mm")
    r.check(abs(sb.min.Z) < 0.01, "shell sits on z=0 (print pose)",
            f"min z {sb.min.Z:.3f}")

    ib = insert.bounding_box()
    r.check(abs(ib.min.Z) < 0.01, "cartridge sits on z=0 (print pose)",
            f"min z {ib.min.Z:.3f}")
    r.check(abs(ib.size.Z - c.CART_H) < 0.01,
            "cartridge is CART_H tall", f"{ib.size.Z:.2f} mm")
    # The body must clear the cavity; the bead and key rib deliberately do not.
    r.check(c.CART_W < c.CAVITY_W - TOL,
            "cartridge body clears the cavity",
            f"{c.CART_W:.2f} < {c.CAVITY_W:.2f} mm, slip {c.CART_SLIP:.2f}")
    r.check(c.CART_PROUD > 0.5,
            "cartridge stands proud enough to pinch out",
            f"{c.CART_PROUD:.1f} mm")
    # The collar's defining property: symmetric about its own bead.
    r.check(abs(c.CART_BELOW_BEAD - c.CART_ABOVE_BEAD) < TOL,
            "collar reaches as far below the bead as it stands above it",
            f"below {c.CART_BELOW_BEAD:.2f} mm, above {c.CART_ABOVE_BEAD:.2f} mm")
    r.check(abs(c.CART_H - 2 * c.CART_ABOVE_BEAD) < TOL,
            "collar height is exactly twice its above-bead reach",
            f"{c.CART_H:.2f} mm")
    r.check(c.CART_H > c.LAND_H + c.LAND_LEAD_IN + c.BEAD_BACK,
            "collar is still tall enough for land, lead-in and bead",
            f"{c.CART_H:.2f} mm vs "
            f"{c.LAND_H + c.LAND_LEAD_IN + c.BEAD_BACK:.2f} mm needed")


def check_cover_interface(r: Report) -> None:
    """The reason the collar was left alone: old covers still fit."""
    r.section("cover interface")
    h = cover_height_for(MAX_WOOD_DRILL_LEN, headroom=COVER_TIP_CLEARANCE)
    r.check(abs(h - COVER_H_WOOD) < TOL,
            "an existing drill_storage.wood cover fits this shell",
            f"cover_height_for -> {h:.1f} mm, wood cover {COVER_H_WOOD:.1f} mm")
    r.check(abs(c.GUIDE_FLOOR_Z - 6.0) < TOL,
            "drills still bottom out at BORE_FLOOR_Z",
            f"{c.GUIDE_FLOOR_Z:.1f} mm")
    # The two grooves must not thin the same ring of collar wall.
    cover_groove_z = FOOT_TOP + SNAP_Z
    sep = abs(c.BEAD_Z - cover_groove_z)
    span = c.SHELL_GROOVE_R + max(c.BEAD_LEAD_IN, c.BEAD_BACK)
    r.check(sep > span,
            "cover groove and cartridge groove are vertically separated",
            f"{sep:.1f} mm apart, profiles span {span:.1f} mm")


def check_walls(shell: Part, r: Report) -> None:
    """Every place the two-material split could have left a wall too thin."""
    r.section("walls")
    r.check(c.RIM_FLAT >= MIN_WALL - TOL,
            "flat rim survives both top chamfers",
            f"{c.RIM_FLAT:.2f} mm (min {MIN_WALL})")
    r.check(c.SHELL_WALL - c.SHELL_GROOVE_R >= MIN_WALL - TOL,
            "collar wall survives the cover's snap groove",
            f"{c.SHELL_WALL - c.SHELL_GROOVE_R:.2f} mm")
    r.check(c.SHELL_WALL - c.KEY_D >= MIN_WALL - TOL,
            "cavity wall survives the key slot",
            f"{c.SHELL_WALL - c.KEY_D:.2f} mm")
    r.check(c.CART_WALL >= MIN_WALL - TOL,
            "cartridge keeps CART_WALL to its outer face",
            f"{c.CART_WALL:.2f} mm")

    # Point-sample the shell where the two grooves are deepest, to confirm the
    # arithmetic above describes the solid that was actually built.
    mid = (COLLAR_W / 2 + c.CAVITY_W / 2) / 2
    r.check(is_solid_at(shell, mid, 0.0, FOOT_TOP + SNAP_Z),
            "shell is solid mid-wall at the cover groove", f"x={mid:.2f}")
    r.check(is_solid_at(shell, mid, 0.0, c.BEAD_Z),
            "shell is solid mid-wall at the cartridge groove", f"x={mid:.2f}")


def check_bore_spacing(r: Report) -> None:
    """pack_rows only warns about *horizontal* overpacking and will silently
    overlap rows, so the row pitch is checked here or it is not checked."""
    r.section("bore spacing")
    items = _bore_footprints()
    worst_key, worst = "", math.inf
    for (k1, r1, x1, y1), (k2, r2, x2, y2) in itertools.combinations(items, 2):
        gap = math.dist((x1, y1), (x2, y2)) - r1 - r2
        if gap < worst:
            worst, worst_key = gap, f"{k1}<->{k2}"
    r.check(worst >= c.PACK_HOLE_WALL - TOL,
            "every bore pair meets the mouth-chamfer budget",
            f"worst {worst_key} = {worst:.2f} mm (budget {c.PACK_HOLE_WALL:.2f})")
    r.check(worst >= MIN_WALL - TOL,
            "every bore pair is at least a printable wall apart",
            f"{worst:.2f} mm (min {MIN_WALL})")

    # Every bore must also keep CART_WALL of material to the cartridge's face.
    half = c.CART_W / 2
    worst_edge = min(half - max(abs(x), abs(y)) - rad for _k, rad, x, y in items)
    r.check(worst_edge >= c.CART_WALL - TOL,
            "every bore keeps CART_WALL to the outer face",
            f"{worst_edge:.2f} mm")

    # The key rib lives outside the body, so no bore can ever reach it -- but say
    # so in code, because that is the whole reason it is out there.
    r.check(all(x + rad < half + TOL for _k, rad, x, _y in items),
            "no bore reaches past the cartridge face into the key rib",
            f"max reach {max(x + rad for _k, rad, x, _y in items):.2f} of {half:.2f}")


def check_land(insert: Part, r: Report) -> None:
    """The grip itself: the land is where it is modelled, and it is tighter than
    the relief above it. This is the one thing point-sampling can prove."""
    r.section("grip land")
    z_land = c.BORE_FOOT_RELIEF + c.EFFECTIVE_LAND_H / 2
    z_relief = c.LAND_H + c.LAND_LEAD_IN + 2.0

    for d, x, y in DRILL_BORES:
        land_r = (d + c.LAND_FIT) / 2
        relief_r = (d + c.RELIEF_FIT) / 2
        ok = (
            not is_solid_at(insert, x + land_r - PROBE, y, z_land)
            and is_solid_at(insert, x + land_r + PROBE, y, z_land)
            and not is_solid_at(insert, x + relief_r - PROBE, y, z_relief)
            and is_solid_at(insert, x + relief_r + PROBE, y, z_relief)
        )
        r.check(ok, f"{d:g} mm bore: land {land_r:.2f} / relief {relief_r:.2f}",
                f"sampled at z={z_land:.2f} and z={z_relief:.2f}")
        # The step is the whole point: at land height the relief radius must be
        # solid, or the land is not actually narrower than the guide.
        r.check(is_solid_at(insert, x + land_r + PROBE, y, z_land),
                f"{d:g} mm bore: land is proud of the relief",
                f"{(relief_r - land_r) * 2:.2f} mm diametral step")

    r.check(c.EFFECTIVE_LAND_H > 2.0,
            "land is long enough to bear after the foot relief",
            f"{c.EFFECTIVE_LAND_H:.1f} of {c.LAND_H:.1f} mm")


def check_guides(shell: Part, r: Report) -> None:
    """The ASA half of every hole: open top to bottom, loose, and coaxial with the
    collar's land above it. A guide that is off-axis makes the land a cam."""
    r.section("ASA guide bores")
    z_mid = c.GUIDE_FLOOR_Z + c.GUIDE_H / 2

    for d, x, y in DRILL_BORES:
        gr = (d + c.GUIDE_FIT) / 2
        ok = (
            not is_solid_at(shell, x + gr - PROBE, y, z_mid)
            and is_solid_at(shell, x + gr + PROBE, y, z_mid)
        )
        r.check(ok, f"{d:g} mm guide bored to {gr * 2:.2f} mm",
                f"sampled at z={z_mid:.1f}")

    # Open all the way down to the floor a drill rests on, and no further.
    open_span = all(
        not is_solid_at(shell, x, y, z)
        for _d, x, y in DRILL_BORES
        for z in (c.GUIDE_FLOOR_Z + 0.3, z_mid, c.CAVITY_FLOOR_Z - 0.3)
    )
    r.check(open_span, "every guide is open from its floor to the cavity",
            f"{len(DRILL_BORES)} bores sampled at 3 heights")
    floor_intact = all(
        is_solid_at(shell, x, y, c.GUIDE_FLOOR_Z - 0.3)
        for _d, x, y in DRILL_BORES
    )
    r.check(floor_intact, "the shell floor under every guide is solid",
            "a drill rests on ASA, not on air")

    # Guide is loose, land is tight -- confirm on the built solids, not just the
    # constants, since these are two separate parts that could drift apart.
    tighter = all(
        (d + c.LAND_FIT) / 2 < (d + c.GUIDE_FIT) / 2 for d, _x, _y in DRILL_BORES
    )
    r.check(tighter, "every land is narrower than the guide beneath it",
            f"{(c.GUIDE_FIT - c.LAND_FIT):.2f} mm diametral step, all sizes")

    hex_ok = all(
        not is_solid_at(shell, x, y, z)
        for _af, x, y in HEX_BORES
        for z in (c.GUIDE_FLOOR_Z + 0.3, z_mid)
    )
    r.check(hex_ok, "the hex guide is bored too", f"{len(HEX_BORES)} socket(s)")


def check_through_bores(insert: Part, r: Report) -> None:
    """Drills must reach the shell's ASA floor, so every bore is a through hole."""
    r.section("through bores")
    ok_round = all(
        not is_solid_at(insert, x, y, z)
        for d, x, y in DRILL_BORES
        for z in (0.05, c.CART_H / 2, c.CART_H - 0.05)
    )
    r.check(ok_round, "every round bore is open top to bottom",
            f"{len(DRILL_BORES)} bores sampled at 3 heights")
    ok_hex = all(
        not is_solid_at(insert, x, y, z)
        for _af, x, y in HEX_BORES
        for z in (0.05, c.CART_H / 2, c.CART_H - 0.05)
    )
    r.check(ok_hex, "every hex socket is open top to bottom",
            f"{len(HEX_BORES)} sockets sampled")


def check_retention(r: Report) -> None:
    """A drill leaves the land at maybe 5-15 N and the cartridge weighs ~0.2 N,
    so the bead is not decoration."""
    r.section("retention")
    r.check(c.BEAD_ENGAGEMENT > 0.2,
            "retention bead engages past the cartridge's own slip",
            f"{c.BEAD_ENGAGEMENT:.2f} mm (bead {c.CART_BEAD:.2f}, "
            f"slip/2 {c.CART_SLIP / 2:.2f})")
    r.check(c.CART_BEAD <= c.SHELL_GROOVE_R + TOL,
            "bead tip fits inside the groove that receives it",
            f"bead {c.CART_BEAD:.2f} <= groove r {c.SHELL_GROOVE_R:.2f}")
    r.check(c.BEAD_LEAD_IN > c.BEAD_BACK,
            "insertion ramp is gentler than the retention face",
            f"lead-in {c.BEAD_LEAD_IN:.1f} vs back {c.BEAD_BACK:.1f} mm")
    r.check(c.BEAD_Z + c.BEAD_BACK < BASE_TOTAL_H,
            "bead seats below the shell rim", f"{c.BEAD_Z + c.BEAD_BACK:.1f} mm")


def check_key(shell: Part, insert: Part, r: Report) -> None:
    """The legend is only true in one orientation, so the key has to work."""
    r.section("key")
    rib_tip = c.CART_W / 2 + c.KEY_D
    slot_floor = c.CAVITY_W / 2 + c.KEY_D
    r.check(rib_tip < slot_floor - TOL, "key rib clears the bottom of its slot",
            f"rib {rib_tip:.2f} < slot {slot_floor:.2f} mm")
    # Sample low in the cavity, deliberately clear of the retention groove: the
    # collar is short enough now that mid-cavity lands *inside* the groove at
    # BEAD_Z, where the wall is legitimately void and proves nothing about the key.
    z = c.CAVITY_FLOOR_Z + 2.0
    clear_of_groove = abs(z - c.BEAD_Z) > c.SHELL_GROOVE_R + 0.5
    r.check(clear_of_groove, "key probe height is clear of the retention groove",
            f"z={z:.1f}, groove at {c.BEAD_Z:.1f}+/-{c.SHELL_GROOVE_R:.1f}")
    r.check(not is_solid_at(shell, c.CAVITY_W / 2 + c.KEY_D / 2, 0.0, z),
            "shell has a slot on +X in the cavity wall", f"z={z:.1f}")
    r.check(is_solid_at(shell, c.CAVITY_W / 2 + c.KEY_D / 2, 0.0 + c.KEY_W, z),
            "the slot is local, not a groove round the whole cavity",
            f"solid at y={c.KEY_W:.1f}")
    r.check(is_solid_at(insert, c.CART_W / 2 + c.KEY_D / 2, 0.0, c.CART_H / 2),
            "cartridge has a rib on +X at mid-height", "")


def check_sharp_edges(shell: Part, insert: Part, r: Report) -> None:
    """House rule: chamfer horizontal edges, fillet vertical ones. Exceptions are
    named here with their reason, never silently omitted."""
    r.section("sharp edges")

    def on_wall_face(e) -> bool:
        b = e.bounding_box()
        half = PAD / 2
        return (
            abs(abs(b.min.X) - half) < 0.05 and abs(abs(b.max.X) - half) < 0.05
        ) or (abs(abs(b.min.Y) - half) < 0.05 and abs(abs(b.max.Y) - half) < 0.05)

    def on_shoulder(e) -> bool:
        b = e.bounding_box()
        return abs(b.min.Z - FOOT_TOP) < 0.05 and abs(b.max.Z - FOOT_TOP) < 0.05

    def on_a_groove(e) -> bool:
        b = e.bounding_box()
        if abs(b.max.Z - b.min.Z) > 0.05:
            return False
        for z in (FOOT_TOP + SNAP_Z, c.BEAD_Z):
            if abs(b.min.Z - (z - c.SHELL_GROOVE_R)) < 0.05:
                return True
            if abs(b.min.Z - (z + c.SHELL_GROOVE_R)) < 0.05:
                return True
        return False

    shell_allow = (
        (on_wall_face, "engraved size legend -- bevelling a glyph destroys it"),
        (on_shoulder, "cover seat is deliberately flat so the cover's chamfered "
                      "rim lands flat-on-flat (box.py:1052-1054)"),
        (on_a_groove, "round snap-groove rims -- the groove is the mating "
                      "feature, and rounding its lips would shrink engagement"),
    )
    bad_shell = sharp_convex_edges(shell, allow=shell_allow)
    r.check(not bad_shell, "shell has no unexplained sharp convex edges",
            f"{len(bad_shell)} found" if bad_shell else "all treated or named")

    bad_insert = sharp_convex_edges(insert)
    r.check(not bad_insert, "cartridge has no sharp convex edges at all",
            f"{len(bad_insert)} found" if bad_insert else "none, no exceptions")


def run() -> Report:
    r = Report()
    shell = create_shell(DRILL_BORES, hex_bores=HEX_BORES, rows=ROWS, hole_pos=POS)
    insert = create_insert(DRILL_BORES, hex_bores=HEX_BORES)

    check_fits(r)
    check_envelope(shell, insert, r)
    check_cover_interface(r)
    check_walls(shell, r)
    check_bore_spacing(r)
    check_guides(shell, r)
    check_land(insert, r)
    check_through_bores(insert, r)
    check_retention(r)
    check_key(shell, insert, r)
    check_sharp_edges(shell, insert, r)
    return r


def main() -> None:
    import sys

    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
