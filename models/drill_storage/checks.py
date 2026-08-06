"""Geometry assertions for the drill_storage package.

    uv run check drill_storage             # the engine, all three sets, and hex
    uv run check drill_storage.wood        # one set, which is much faster
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

from build123d import Part

from ..lib import fits
from ..lib.checks import TOL as TOL
from ..lib.checks import Report as Report
from ..lib.checks import is_solid_at as is_solid_at
from ..lib.checks import sharp_convex_edges
from . import config as c
from . import hex as hex_mod
from . import sets
from .box import (
    CAP_H,
    COVER_W,
    FOOT_TOP,
    HEIGHT_UNIT,
    HEX_SLIP,
    PAD,
    SNAP_GROOVE_R,
    SNAP_Z,
    cover_height_for,
    create_base,
    create_cover,
)
from .cover import create_cover_for
from .insert import _hex_r, create_insert_for
from .sets import DrillSet
from .shell import create_shell_for

PROBE = 0.08  # how far either side of a modelled radius we sample for material

# The absolute minimum wall a 0.4 mm nozzle resolves: 2 perimeters. Below this a
# feature does not slice as a wall at all, it merges with its neighbour. The same
# figure is the floor for a *hole*: under two extrusions wide, a bore closes up.
MIN_WALL = 0.8


def _bore_footprints(s: DrillSet) -> list[tuple[str, float, float, float]]:
    """Every cut bore as ``(key, relieved_radius, x, y)`` -- the real footprint,
    not the nominal tool, which is what has to be packed and walled."""
    items = [(f"{d:g}", c.relieved_bore_r(d), x, y) for d, x, y in s.bores]
    items += [(f"hex{af:g}", _hex_r(af, c.RELIEF_FIT), x, y) for af, x, y in s.hex_bores]
    return items


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
        c.CART_BEAD <= c.SHELL_GROOVE_R + TOL,
        "bead tip fits inside the groove that receives it",
        f"bead {c.CART_BEAD:.2f} <= groove r {c.SHELL_GROOVE_R:.2f}",
    )
    r.check(
        c.BEAD_LEAD_IN > c.BEAD_BACK,
        "insertion ramp is gentler than the retention face",
        f"lead-in {c.BEAD_LEAD_IN:.1f} vs back {c.BEAD_BACK:.1f} mm",
    )
    r.check(
        c.BEAD_Z + c.BEAD_BACK < c.SHELL_TOTAL_H,
        "bead seats below the shell rim",
        f"{c.BEAD_Z + c.BEAD_BACK:.1f} mm",
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
    r.check(
        c.SHELL_WALL - c.SHELL_GROOVE_R >= MIN_WALL - TOL,
        "collar wall survives the cover's snap groove",
        f"{c.SHELL_WALL - c.SHELL_GROOVE_R:.2f} mm",
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
    # the TPU and takes nothing out of the shell.
    need = SNAP_GROOVE_R + c.SHELL_GROOVE_R
    r.check(
        c.GROOVE_SEPARATION > need,
        "cover groove and collar groove never thin the same wall",
        f"{c.GROOVE_SEPARATION:.1f} mm apart, {need:.1f} mm required",
    )
    # The seat is the one dimension that must NOT move: it feeds
    # cover_height_for, so lowering it mints a taller cover for one model and
    # every cover already on the shelf stops fitting.
    r.check(
        abs(c.SHELL_FOOT_TOP - FOOT_TOP) < TOL,
        "the cover seat sits where the engine puts it, so covers interchange",
        f"{c.SHELL_FOOT_TOP:.1f} mm -- lower it and shared covers are lost",
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
        # The smallest land still has to print as a hole rather than close up.
        smallest = min(d + c.LAND_FIT for d, _x, _y in s.bores)
        r.check(
            smallest >= MIN_WALL - TOL,
            f"{s.name}: the smallest land is still a printable hole",
            f"{smallest:.2f} mm (min {MIN_WALL})",
        )


# --- Per-set ------------------------------------------------------------------


def check_envelope(s: DrillSet, shell: Part, insert: Part, r: Report) -> None:
    """Gridfinity envelope, and the cartridge actually fitting its cavity."""
    r.section(f"{s.name}: envelope")
    sb = shell.bounding_box()
    r.check(
        abs(sb.size.X - PAD) < 0.01 and abs(sb.size.Y - PAD) < 0.01,
        "shell footprint is one Gridfinity pad",
        f"{sb.size.X:.2f} x {sb.size.Y:.2f} mm",
    )
    r.check(
        abs(sb.size.Z - c.SHELL_TOTAL_H) < 0.01,
        "shell is SHELL_TOTAL_H tall",
        f"{sb.size.Z:.1f} mm",
    )
    r.check(
        abs(sb.min.Z) < 0.01, "shell sits on z=0 (print pose)", f"min z {sb.min.Z:.3f}"
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
        f"(the shell itself is {c.SHELL_TOTAL_H:.0f} mm, deliberately not a unit)",
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


def check_land(s: DrillSet, insert: Part, r: Report) -> None:
    """The grip itself: the land is where it is modelled, and it is tighter than
    the relief above it. This is the one thing point-sampling can prove."""
    r.section(f"{s.name}: grip land")
    z_land = c.BORE_FOOT_RELIEF + c.EFFECTIVE_LAND_H / 2
    z_relief = c.LAND_H + c.LAND_LEAD_IN + 2.0

    for d, x, y in s.bores:
        land_r = (d + c.LAND_FIT) / 2
        relief_r = (d + c.RELIEF_FIT) / 2
        ok = (
            not is_solid_at(insert, x + land_r - PROBE, y, z_land)
            and is_solid_at(insert, x + land_r + PROBE, y, z_land)
            and not is_solid_at(insert, x + relief_r - PROBE, y, z_relief)
            and is_solid_at(insert, x + relief_r + PROBE, y, z_relief)
        )
        r.check(
            ok,
            f"{d:g} mm bore: land {land_r:.2f} / relief {relief_r:.2f}",
            f"sampled at z={z_land:.2f} and z={z_relief:.2f}",
        )
        # The step is the whole point: at land height the relief radius must be
        # solid, or the land is not actually narrower than the guide.
        r.check(
            is_solid_at(insert, x + land_r + PROBE, y, z_land),
            f"{d:g} mm bore: land is proud of the relief",
            f"{(relief_r - land_r) * 2:.2f} mm diametral step",
        )

    r.check(
        c.EFFECTIVE_LAND_H > 2.0,
        "land is long enough to bear after the foot relief",
        f"{c.EFFECTIVE_LAND_H:.1f} of {c.LAND_H:.1f} mm",
    )


def check_guides(s: DrillSet, shell: Part, r: Report) -> None:
    """The ASA half of every hole: open top to bottom, loose, and coaxial with the
    collar's land above it. A guide that is off-axis makes the land a cam."""
    r.section(f"{s.name}: ASA guide bores")
    z_mid = c.GUIDE_FLOOR_Z + c.GUIDE_H / 2

    for d, x, y in s.bores:
        gr = (d + c.GUIDE_FIT) / 2
        ok = not is_solid_at(shell, x + gr - PROBE, y, z_mid) and is_solid_at(
            shell, x + gr + PROBE, y, z_mid
        )
        r.check(
            ok, f"{d:g} mm guide bored to {gr * 2:.2f} mm", f"sampled at z={z_mid:.1f}"
        )

    # Open all the way down to the floor a drill rests on, and no further.
    open_span = all(
        not is_solid_at(shell, x, y, z)
        for _d, x, y in s.bores
        for z in (c.GUIDE_FLOOR_Z + 0.3, z_mid, c.CAVITY_FLOOR_Z - 0.3)
    )
    r.check(
        open_span,
        "every guide is open from its floor to the cavity",
        f"{len(s.bores)} bores sampled at 3 heights",
    )
    floor_intact = all(
        is_solid_at(shell, x, y, c.GUIDE_FLOOR_Z - 0.3) for _d, x, y in s.bores
    )
    r.check(
        floor_intact,
        "the shell floor under every guide is solid",
        "a drill rests on ASA, not on air",
    )

    hex_ok = all(
        not is_solid_at(shell, x, y, z)
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
    guides += [(f"hex{af:g}", _hex_r(af, c.GUIDE_FIT), x, y) for af, x, y in s.hex_bores]
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
    # it to only one would show up here and nowhere else.
    r.check(
        all((d + c.LAND_FIT) < (d + c.GUIDE_FIT) for d, _x, _y in s.bores),
        "every land is narrower than the guide beneath it",
        f"{(c.GUIDE_FIT - c.LAND_FIT):.2f} mm diametral step, all sizes",
    )


def check_through_bores(s: DrillSet, insert: Part, r: Report) -> None:
    """Drills must reach the shell's ASA floor, so every bore is a through hole."""
    r.section(f"{s.name}: through bores")
    heights = (0.05, c.CART_H / 2, c.CART_H - 0.05)
    ok_round = all(
        not is_solid_at(insert, x, y, z) for _d, x, y in s.bores for z in heights
    )
    r.check(
        ok_round,
        "every round bore is open top to bottom",
        f"{len(s.bores)} bores sampled at 3 heights",
    )
    ok_hex = all(
        not is_solid_at(insert, x, y, z) for _af, x, y in s.hex_bores for z in heights
    )
    r.check(
        ok_hex,
        "every hex socket is open top to bottom",
        f"{len(s.hex_bores)} sockets sampled",
    )


def check_key(s: DrillSet, shell: Part, insert: Part, r: Report) -> None:
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
    # where the wall is legitimately void and proves nothing about the key.
    z = c.CAVITY_FLOOR_Z + 2.0
    r.check(
        abs(z - c.BEAD_Z) > c.SHELL_GROOVE_R + 0.5,
        "key probe height is clear of the retention groove",
        f"z={z:.1f}, groove at {c.BEAD_Z:.1f}+/-{c.SHELL_GROOVE_R:.1f}",
    )
    r.check(
        not is_solid_at(shell, c.CAVITY_W / 2 + c.KEY_D / 2, 0.0, z),
        "shell has a slot on +X in the cavity wall",
        f"z={z:.1f}",
    )
    r.check(
        is_solid_at(shell, c.CAVITY_W / 2 + c.KEY_D / 2, 0.0 + c.KEY_W, z),
        "the slot is local, not a groove round the whole cavity",
        f"solid at y={c.KEY_W:.1f}",
    )
    r.check(
        is_solid_at(insert, c.CART_W / 2 + c.KEY_D / 2, 0.0, c.CART_H / 2),
        "cartridge has a rib on +X at mid-height",
        "",
    )


# --- Sharp edges --------------------------------------------------------------


def _shell_allow() -> tuple:
    """The shell's three legitimate exceptions to the chamfer-everything rule.

    Named with their reason, never silently omitted -- that is the whole point of
    ``sharp_convex_edges`` taking an allow list rather than a threshold.
    """

    def on_wall_face(e) -> bool:
        b = e.bounding_box()
        half = PAD / 2
        return (abs(abs(b.min.X) - half) < 0.05 and abs(abs(b.max.X) - half) < 0.05) or (
            abs(abs(b.min.Y) - half) < 0.05 and abs(abs(b.max.Y) - half) < 0.05
        )

    def on_shoulder(e) -> bool:
        b = e.bounding_box()
        return (
            abs(b.min.Z - c.SHELL_FOOT_TOP) < 0.05
            and abs(b.max.Z - c.SHELL_FOOT_TOP) < 0.05
        )

    def on_a_groove(e) -> bool:
        b = e.bounding_box()
        if abs(b.max.Z - b.min.Z) > 0.05:
            return False
        for z in (c.SHELL_FOOT_TOP + SNAP_Z, c.BEAD_Z):
            if abs(b.min.Z - (z - c.SHELL_GROOVE_R)) < 0.05:
                return True
            if abs(b.min.Z - (z + c.SHELL_GROOVE_R)) < 0.05:
                return True
        return False

    return (
        (on_wall_face, "engraved size legend -- bevelling a glyph destroys it"),
        (
            on_shoulder,
            "cover seat is deliberately flat so the cover's chamfered "
            "rim lands flat-on-flat (box.create_cover's COVER_SEAT_CH)",
        ),
        (
            on_a_groove,
            "round snap-groove rims -- the groove is the mating "
            "feature, and rounding its lips would shrink engagement",
        ),
    )


def _cover_allow() -> tuple:
    half = COVER_W / 2

    def on_label_face(e) -> bool:
        centre = e.center()
        return abs(abs(centre.Y) - half) < 1.5 and abs(centre.X) < half

    return ((on_label_face, "engraved material label -- bevelling a glyph destroys it"),)


def check_sharp_edges(
    s: DrillSet, shell: Part, insert: Part, cover: Part, r: Report
) -> None:
    """House rule: chamfer horizontal edges, fillet vertical ones. Exceptions are
    named with their reason, never silently omitted."""
    r.section(f"{s.name}: sharp edges")
    bad_shell = sharp_convex_edges(shell, allow=_shell_allow())
    r.check(
        not bad_shell,
        "shell has no unexplained sharp convex edges",
        f"{len(bad_shell)} found" if bad_shell else "all treated or named",
    )
    bad_insert = sharp_convex_edges(insert)
    r.check(
        not bad_insert,
        "cartridge has no sharp convex edges at all",
        f"{len(bad_insert)} found" if bad_insert else "none, no exceptions",
    )
    bad_cover = sharp_convex_edges(cover, allow=_cover_allow())
    r.check(
        not bad_cover,
        "cover has no unexplained sharp convex edges",
        f"{len(bad_cover)} found" if bad_cover else "all treated or named",
    )


def check_set(s: DrillSet, r: Report) -> None:
    """Everything that has to hold for one set, on its three built parts."""
    shell = create_shell_for(s)
    insert = create_insert_for(s)
    cover = create_cover_for(s)

    check_envelope(s, shell, insert, r)
    check_cover_interface(s, cover, r)
    check_bore_spacing(s, r)
    check_guides(s, shell, r)
    check_land(s, insert, r)
    check_through_bores(s, insert, r)
    check_key(s, shell, insert, r)
    check_sharp_edges(s, shell, insert, cover, r)


# --- The one-material outlier: drill_storage.hex ------------------------------


def check_hex_boxes(r: Report) -> None:
    """``drill_storage.hex`` is the only holder still cut from ``create_base``:
    its 1/4" driver bits are held by a plain socket and their own weight."""
    r.section("hex: bit sizes")
    r.check(
        hex_mod.ALLEN_SIZES == sorted(hex_mod.ALLEN_SIZES, reverse=True),
        "ALLEN_SIZES is documented largest-first",
        f"{hex_mod.ALLEN_SIZES}",
    )
    r.check(
        hex_mod.BOXES[0][2] is not None and hex_mod.BOXES[1][2] is None,
        "only the ALLEN box carries a wall legend (BITS is a mixed bag)",
        f"{[b[0] for b in hex_mod.BOXES]}",
    )

    expected_assembled = {"ALLEN": 70.0, "BITS": 42.0}
    expected_proud = {"ALLEN": 35.0, "BITS": 10.0}

    for label, bit_len, keys in hex_mod.BOXES:
        hex_bores, rows, pos = hex_mod._sockets(keys)
        base = create_base(
            [],
            hex_bores=hex_bores,
            rows=rows if keys else None,
            hole_pos=pos if keys else None,
            bore_depth=hex_mod.SOCKET_DEPTH,
            foot_top=hex_mod.BASE_FOOT_TOP,
            collar_h=hex_mod.BASE_COLLAR_H,
            label_z=hex_mod.LEGEND_Z,
            label_line_h=hex_mod.LEGEND_LINE_H,
        )
        cover_h = cover_height_for(
            bit_len,
            headroom=hex_mod.COVER_TIP_CLEARANCE,
            bore_floor_z=hex_mod.SOCKET_FLOOR_Z,
            foot_top=hex_mod.BASE_FOOT_TOP,
        )
        size, label_z, horizontal = hex_mod._label_fit(cover_h, label)
        cover = create_cover(
            label,
            cover_h=cover_h,
            label_size=size,
            label_z=label_z,
            label_horizontal=horizontal,
        )

        r.section(f"hex {label}")
        bb = base.bounding_box()
        r.check(
            abs(bb.min.Z) < 0.02 and abs(bb.size.Z - hex_mod.BASE_TOTAL_H) < 0.05,
            "base is BASE_TOTAL_H tall and sits on z=0 (print pose)",
            f"{bb.size.Z:.2f} mm, min z {bb.min.Z:.3f}",
        )
        cbb = cover.bounding_box()
        r.check(
            abs(cbb.min.Z) < 0.02 and abs(cbb.size.Z - cover_h) < 0.05,
            "cover is built to its derived height and sits on z=0",
            f"{cbb.size.Z:.2f} mm (want {cover_h:.2f})",
        )
        assembled = hex_mod.BASE_FOOT_TOP + cover_h
        r.check(
            abs(assembled - expected_assembled[label]) < 0.05,
            "assembled envelope matches the module docstring",
            f"{assembled:.0f} mm (want {expected_assembled[label]:.0f})",
        )
        proud = (hex_mod.SOCKET_FLOOR_Z + bit_len) - hex_mod.BASE_TOTAL_H
        r.check(
            abs(proud - expected_proud[label]) < 0.05,
            "a bit stands proud of the base by the documented amount",
            f"{proud:.1f} mm (want {expected_proud[label]:.1f})",
        )

        # The socket is a plain drop-in: no land, no ribs, just the flats.
        z = hex_mod.SOCKET_FLOOR_Z + 5.0
        rc = (hex_mod.HEX_AF + HEX_SLIP) / 3**0.5
        ok = all(
            not is_solid_at(base, x + rc - PROBE, y, z)
            and is_solid_at(base, x + rc + PROBE, y, z)
            for _af, x, y in hex_bores
        )
        r.check(
            ok,
            f"all {len(hex_bores)} sockets bored to "
            f"{hex_mod.HEX_AF:g} mm across-flats (+HEX_SLIP)",
            f"circumradius {rc:.3f} mm, sampled z={z:.1f}",
        )


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
    check_hex_boxes(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
