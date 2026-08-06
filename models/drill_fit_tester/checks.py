"""Geometry assertions for the drill-fit-test coupons.

    uv run check drill_fit_tester
    uv run python -m models.drill_fit_tester.checks

This package's whole job is dimensional accuracy, so "the part built without
raising" proves nothing -- every check here either point-samples a bore at the
radius its module's own formula predicts, or recomputes a hole's position from
the same layout arithmetic ``frame.coupon`` / ``sweep.create_bar`` use, then
asks the solid whether it agrees. What it *cannot* verify is the grip itself:
that is a felt judgement a coupon exists to collect by hand, not something a
classifier can rule on. See ``report()`` in each module for the numbers to read
against a printed bar.
"""

from __future__ import annotations

import math

from build123d import Compound, Edge, Part

from ..drill_storage import box
from ..drill_storage.flex import config as fc
from ..drill_storage.wood import CSK_HEAD_D, CSK_HEX_AF, DRILL_DIAMS
from ..lib.checks import TOL, Report, is_solid_at, sharp_convex_edges
from . import frame, full, land, plain, ribbed, small, sweep, taper
from .frame import EDGE, HOLE_WALL, LABEL_PITCH, layout_r

FRAME_PLATE_H = frame.PLATE_H  # 7.5 mm -- ribbed/plain/taper/land's plate thickness

# How far either side of a modelled boundary a point is sampled. This has to be
# tight: RIB_GRIP_SMALL's own entries differ by as little as 0.01 mm (diametral)
# from their neighbour (2.0 mm -> 0.46, 2.5 mm -> 0.45), i.e. 0.005 mm of radius,
# and an earlier draft of this file used PROBE=0.08 -- coarse enough that a
# deliberately injected +0.15 mm grip error (0.075 mm of radius) sampled clean on
# both sides of the wrong boundary and the check passed anyway. 0.02 mm is well
# clear of solid-classifier/float noise (OCC's own tolerance is 1e-6, and these
# are exact BRep cylinders/cones, not tessellated meshes) while still resolving
# any error bigger than about 0.04 mm diametral -- smaller than that is out of
# this check's reach, see the implementer's report.
PROBE = 0.02

# HEX_GRIP and the round-bore law both land near 0.22-0.25 at CSK_HEX_AF (6.3 mm),
# so the gap between "the hex socket used its own law" and "it silently fell back
# to the round-bore law" is only ~0.015 mm of radius -- even PROBE would swallow
# that difference and pass either way. This one is for telling those two apart.
FINE_PROBE = 0.01

# The absolute minimum wall a 0.4 mm nozzle resolves: 2 perimeters.
MIN_WALL = 0.8


# --- Layout replicas ------------------------------------------------------------
# frame.coupon() and sweep.create_bar() compute hole positions inline and never
# return them, so a check that wants to point-sample a *specific* bore has to
# reproduce the same left-to-right, wall-clamped placement loop. Both mirrors are
# exercised (and cross-checked against the built solids) by check_layout /
# check_sweep below -- if the real placement loop ever changes shape, the mirror
# drifts out of sync with it and those checks go red rather than silently
# sampling the wrong spot.


def _placements(diams: list[float]) -> dict[str, tuple[float, float]]:
    """Reproduce ``frame.coupon``'s row layout: ``{key: (x, footprint_r)}``."""
    items = [(f"{d:g}", layout_r(d)) for d in sorted(diams)]
    items.append(("hex", CSK_HEAD_D / 2))
    placed: list[list] = []
    c = 0.0
    prev_r = None
    for key, rad in items:
        if prev_r is not None:
            c += max(prev_r + rad + HOLE_WALL, LABEL_PITCH)
        placed.append([key, c, rad])
        prev_r = rad
    min_x = placed[0][1] - placed[0][2]
    max_x = placed[-1][1] + placed[-1][2]
    mid_x = (min_x + max_x) / 2
    return {key: (x - mid_x, rad) for key, x, rad in placed}


def _bar_placements(
    diams: list[float], layout_grip: sweep.GripLaw, with_hex: bool
) -> dict[str, float]:
    """Reproduce ``sweep.create_bar``'s row layout: ``{key: x}``.

    ``layout_grip`` is a flat number or a ``d -> grip`` callable, exactly as
    ``create_bar`` accepts it.
    """
    layout_of = (
        layout_grip if callable(layout_grip) else (lambda _d, _g=layout_grip: _g)
    )
    keys = [(f"{d:g}", sweep._valley_r(d, layout_of(d))) for d in diams]
    if with_hex:
        keys.append(("hex", CSK_HEAD_D / 2))
    placed: list[list] = []
    c = 0.0
    prev_r = None
    for key, rad in keys:
        if prev_r is not None:
            c += max(prev_r + rad + HOLE_WALL, LABEL_PITCH)
        placed.append([key, c, rad])
        prev_r = rad
    min_x = placed[0][1] - placed[0][2]
    max_x = placed[-1][1] + placed[-1][2]
    mid_x = (min_x + max_x) / 2
    return {key: x - mid_x for key, x, _rad in placed}


# --- Rib point-sampling ----------------------------------------------------------
# A ribbed bore's grip is a *rib*, not a plain cylinder: the bit is only gripped
# on a spoke every 120 deg (60 deg for the hex, offset by HEX_RIB_ANGLE), and is
# free between spokes. Sampling both tells the check apart from a bore that
# merely has the right *valley* radius but lost its ribs entirely.


def _rib_mid_z(bore_depth: float) -> float:
    """Mid-height of a rib's straight body, below its RIB_TAPER lead-in cap."""
    rib_h = min(box.RIB_ZONE_H, bore_depth - box.RIB_TOP_GAP)
    return (rib_h - box.RIB_TAPER) / 2


def _check_round_grip(
    part: Part,
    x: float,
    d: float,
    grip: float,
    z: float,
    r: Report,
    label: str,
    y0: float = 0.0,
) -> None:
    """A round bore's rib grip (on a rib, angle 0) and relieved valley (between
    ribs, angle 60) -- the two radii that decide whether a bit of diameter ``d``
    feels ``grip`` mm of interference at all.

    ``y0`` is the bore's own row offset -- 0 for a lone coupon, but non-zero for
    a bar inside a ``sweep.lay_out`` family, which stacks bars along +/-Y (see
    ``lay_out``); every sample point has to carry that offset or it lands on a
    neighbouring bar (or empty space) instead of the one being tested.
    """
    r_tip = box.rib_tip_r(d, grip)
    valley_r = r_tip + box.rib_relief(d, grip)
    on_rib = not is_solid_at(part, x + r_tip - PROBE, y0, z) and is_solid_at(
        part, x + r_tip + PROBE, y0, z
    )
    r.check(
        on_rib,
        f"{label}: {d:g} mm rib grips at r={r_tip:.3f} mm (grip {grip:.2f})",
        f"sampled at z={z:.2f}",
    )
    ang = math.radians(60)
    in_x = x + (valley_r - PROBE) * math.cos(ang)
    in_y = y0 + (valley_r - PROBE) * math.sin(ang)
    out_x = x + (valley_r + PROBE) * math.cos(ang)
    out_y = y0 + (valley_r + PROBE) * math.sin(ang)
    off_rib = not is_solid_at(part, in_x, in_y, z) and is_solid_at(
        part, out_x, out_y, z
    )
    r.check(
        off_rib,
        f"{label}: {d:g} mm valley relieved to r={valley_r:.3f} mm between ribs",
        f"sampled at z={z:.2f}",
    )


def _check_hex_grip(
    part: Part,
    x: float,
    af: float,
    grip: float,
    z: float,
    r: Report,
    label: str,
    y0: float = 0.0,
) -> None:
    """As ``_check_round_grip``, for the hex socket -- ribs sit at HEX_RIB_ANGLE
    + k*60 deg (on flats), valleys 30 deg off that. ``y0`` as above."""
    r_tip = box.rib_tip_r(af, grip)
    valley_r = r_tip + box.rib_relief(af, grip)
    ang_on = math.radians(box.HEX_RIB_ANGLE)
    ang_off = ang_on + math.radians(60)
    on_in = (
        x + (r_tip - PROBE) * math.cos(ang_on),
        y0 + (r_tip - PROBE) * math.sin(ang_on),
    )
    on_out = (
        x + (r_tip + PROBE) * math.cos(ang_on),
        y0 + (r_tip + PROBE) * math.sin(ang_on),
    )
    on_rib = not is_solid_at(part, *on_in, z) and is_solid_at(part, *on_out, z)
    r.check(
        on_rib,
        f"{label}: hex rib grips at r={r_tip:.3f} mm (grip {grip:.2f})",
        f"sampled at z={z:.2f}",
    )
    off_in = (
        x + (valley_r - PROBE) * math.cos(ang_off),
        y0 + (valley_r - PROBE) * math.sin(ang_off),
    )
    off_out = (
        x + (valley_r + PROBE) * math.cos(ang_off),
        y0 + (valley_r + PROBE) * math.sin(ang_off),
    )
    off_rib = not is_solid_at(part, *off_in, z) and is_solid_at(part, *off_out, z)
    r.check(
        off_rib,
        f"{label}: hex valley relieved to r={valley_r:.3f} mm between ribs",
        f"sampled at z={z:.2f}",
    )


def _check_hex_uses_hex_law(
    bar: Part, x: float, offset: float, z: float, r: Report, label: str, y0: float = 0.0
) -> None:
    """The hex socket must ride HEX_GRIP's law (``hex_grip_shifted``), not the
    round-bore law (``grip_shifted``) evaluated at its across-flats -- the whole
    reason ``create_bar`` takes a separate ``hex_grip`` argument (sweep.py:109-113).
    The two laws land within 0.015 mm of radius of each other at CSK_HEX_AF, so
    this samples with FINE_PROBE at exactly the hex-law radius: if a future edit
    ever drops the explicit ``hex_grip=`` and the socket falls back to the round
    law, the real cut boundary moves to the *other* side of this sample and the
    check goes red. ``y0`` is the bar's row offset, as in ``_check_round_grip``.
    """
    af = CSK_HEX_AF
    hex_grip = sweep.hex_grip_shifted(offset)
    r_hex = box.rib_tip_r(af, hex_grip)
    ang = math.radians(box.HEX_RIB_ANGLE)
    in_x = x + (r_hex - FINE_PROBE) * math.cos(ang)
    in_y = y0 + (r_hex - FINE_PROBE) * math.sin(ang)
    out_x = x + (r_hex + FINE_PROBE) * math.cos(ang)
    out_y = y0 + (r_hex + FINE_PROBE) * math.sin(ang)
    ok = not is_solid_at(bar, in_x, in_y, z) and is_solid_at(bar, out_x, out_y, z)
    round_law = sweep.grip_shifted(offset)(af)
    r.check(
        ok,
        f"{label}: hex rib follows HEX_GRIP's law, not the round-bore law",
        f"hex grip {hex_grip:.3f} vs round-law {round_law:.3f} at af={af:g}",
    )


# --- Single-value coupons: ribbed / plain / taper --------------------------------


def check_layout(parts: dict[str, Part], placements: dict, r: Report) -> None:
    """ribbed / plain / taper share one hole layout (frame.py docstring) and are
    all through-bored, sitting flat on z=0 in print pose."""
    r.section("print pose + shared layout")
    xs = list(placements.values())
    expected_len = (
        max(x + rad for x, rad in xs) - min(x - rad for x, rad in xs)
    ) + 2 * EDGE
    expected_half_w = max(rad for _x, rad in xs) + EDGE
    keys_order = [f"{d:g}" for d in sorted(DRILL_DIAMS)] + ["hex"]
    worst_gap = min(
        (placements[b][0] - placements[a][0]) - placements[a][1] - placements[b][1]
        for a, b in zip(keys_order, keys_order[1:])
    )
    r.check(
        worst_gap >= HOLE_WALL - TOL,
        "every adjacent hole pair meets the mouth-chamfer wall budget",
        f"worst gap {worst_gap:.2f} mm (budget {HOLE_WALL:.2f})",
    )
    for name, part in parts.items():
        b = part.bounding_box()
        r.check(
            abs(b.min.Z) < TOL,
            f"{name}: coupon sits on z=0 (print pose)",
            f"min z {b.min.Z:.4f}",
        )
        r.check(
            abs(b.max.Z - FRAME_PLATE_H) < TOL,
            f"{name}: bored all the way through (no floor)",
            f"{b.max.Z:.2f} of {FRAME_PLATE_H:.2f} mm",
        )
        r.check(
            abs(b.size.X - expected_len) < 0.05,
            f"{name}: plate length matches the recomputed hole layout",
            f"{b.size.X:.2f} mm (expected {expected_len:.2f})",
        )
        r.check(
            abs(b.size.Y - 2 * expected_half_w) < 0.05,
            f"{name}: plate width matches the widest hole + edge margin",
            f"{b.size.Y:.2f} mm (expected {2 * expected_half_w:.2f})",
        )


def check_plain(part: Part, placements: dict, r: Report) -> None:
    """Every hole is a plain cylinder undersized PLAIN_UNDERSIZE% of the bit."""
    r.section("plain.py -- fixed-percentage undersize, no ribs")
    z = FRAME_PLATE_H / 2
    for d in sorted(DRILL_DIAMS):
        x, _ = placements[f"{d:g}"]
        r_bore = d * (1 - plain.PLAIN_UNDERSIZE) / 2
        ok = not is_solid_at(part, x + r_bore - PROBE, 0.0, z) and is_solid_at(
            part, x + r_bore + PROBE, 0.0, z
        )
        r.check(
            ok,
            f"{d:g} mm plain bore cut to {r_bore * 2:.3f} mm dia",
            f"PLAIN_UNDERSIZE={plain.PLAIN_UNDERSIZE:.0%}",
        )
    x0, _ = placements[f"{sorted(DRILL_DIAMS)[0]:g}"]
    r.check(
        not is_solid_at(part, x0, 0.0, 0.1)
        and not is_solid_at(part, x0, 0.0, FRAME_PLATE_H - 0.1),
        "plain bores are open top to bottom (through-bored)",
        "sampled just inside both faces",
    )


def check_taper(part: Part, placements: dict, r: Report) -> None:
    """Every hole tapers: clearance at the top, undersize at the bottom."""
    r.section("taper.py -- clearance at top, undersize at bottom")
    depth = FRAME_PLATE_H
    for d in sorted(DRILL_DIAMS):
        x, _ = placements[f"{d:g}"]
        r_bot = (d - taper.TAPER_BOTTOM) / 2
        r_top = (d + taper.TAPER_TOP) / 2
        slope = (r_top - r_bot) / depth
        for z, where in ((0.2, "near the floor"), (depth - 0.2, "near the mouth")):
            rz = r_bot + slope * z
            ok = not is_solid_at(part, x + rz - PROBE, 0.0, z) and is_solid_at(
                part, x + rz + PROBE, 0.0, z
            )
            r.check(
                ok, f"{d:g} mm taper bore is {rz * 2:.3f} mm dia {where}", f"z={z:.2f}"
            )
        r.check(
            r_top > r_bot,
            f"{d:g} mm taper widens toward the top (self-centring)",
            f"top {r_top * 2:.3f} > bottom {r_bot * 2:.3f} mm dia",
        )


def check_ribbed(part: Part, placements: dict, r: Report) -> None:
    """The holder's real geometry: production ``grip_for(d)`` ribs, HEX_GRIP hex."""
    r.section("ribbed.py -- the holder's real geometry (production grip law)")
    z = _rib_mid_z(FRAME_PLATE_H)
    for d in sorted(DRILL_DIAMS):
        x, _ = placements[f"{d:g}"]
        _check_round_grip(part, x, d, box.grip_for(d), z, r, f"ribbed {d:g} mm")
    x_hex, _ = placements["hex"]
    _check_hex_grip(part, x_hex, CSK_HEX_AF, box.HEX_GRIP, z, r, "ribbed hex")


# --- Sweep coupons: sweep / small / full -----------------------------------------


def check_sweep(fam: Compound, r: Report) -> None:
    """One bar per candidate flat grip, SWEEP_DIAMS + the hex on every bar."""
    r.section("sweep.py -- flat grip values, SWEEP_DIAMS on every bar")
    bars = list(fam.children)
    r.check(
        len(bars) == len(sweep.SWEEP_GRIPS),
        "one bar per candidate grip",
        f"{len(bars)} bars, {len(sweep.SWEEP_GRIPS)} grips",
    )
    layout_grip = min(sweep.SWEEP_GRIPS)
    pl = _bar_placements(sweep.SWEEP_DIAMS, layout_grip, sweep.SWEEP_HEX)
    z = _rib_mid_z(sweep.PLATE_H)
    for grip, bar in zip(sweep.SWEEP_GRIPS, bars):
        # lay_out stacks bars along Y (see sweep.lay_out); pl's x positions are
        # bore-local (computed on an untranslated bar), so every sample needs
        # this bar's own row offset added back in, or it lands on empty space
        # (or a neighbouring bar) for every bar except the one dead-centred at
        # y=0.
        y0 = bar.bounding_box().center().Y
        for d in (sweep.SWEEP_DIAMS[0], sweep.SWEEP_DIAMS[-1]):
            _check_round_grip(
                bar, pl[f"{d:g}"], d, grip, z, r, f"sweep {grip:.2f}", y0=y0
            )
        _check_hex_grip(
            bar, pl["hex"], CSK_HEX_AF, grip, z, r, f"sweep {grip:.2f} hex", y0=y0
        )

    volumes = [b.volume for b in bars]
    increasing = all(v1 <= v2 + TOL for v1, v2 in zip(volumes, volumes[1:]))
    r.check(
        increasing,
        "solid volume rises with grip (a tighter rib removes less material)",
        f"{[round(v) for v in volumes]} mm^3 at grips {sweep.SWEEP_GRIPS}",
    )


def check_offset_family(
    fam: Compound,
    offsets: list[float],
    diams: list[float],
    with_hex: bool,
    name: str,
    r: Report,
) -> None:
    """small.py / full.py: bars shift the *production law* by a fixed offset."""
    r.section(f"{name}.py -- production law shifted by a fixed offset")
    bars = list(fam.children)
    r.check(
        len(bars) == len(offsets),
        f"{name}: one bar per offset",
        f"{len(bars)} bars, {len(offsets)} offsets",
    )
    layout_grip = sweep.grip_shifted(min(offsets))
    pl = _bar_placements(diams, layout_grip, with_hex)
    z = _rib_mid_z(sweep.PLATE_H)
    lo, hi = min(diams), max(diams)
    for offset, bar in zip(offsets, bars):
        # As in check_sweep: recover this bar's own row offset from the built
        # solid rather than assuming y=0 -- lay_out translates every bar but
        # the one it centres at y=0.
        y0 = bar.bounding_box().center().Y
        law = sweep.grip_shifted(offset)
        for d in {lo, hi}:
            _check_round_grip(
                bar, pl[f"{d:g}"], d, law(d), z, r, f"{name} {offset:+.2f}", y0=y0
            )
        if with_hex:
            hex_grip = sweep.hex_grip_shifted(offset)
            _check_hex_grip(
                bar,
                pl["hex"],
                CSK_HEX_AF,
                hex_grip,
                z,
                r,
                f"{name} {offset:+.2f} hex",
                y0=y0,
            )
            _check_hex_uses_hex_law(
                bar, pl["hex"], offset, z, r, f"{name} {offset:+.2f}", y0=y0
            )


# --- Land coupon (TPU) ------------------------------------------------------------


def check_land(fam: Compound, placements: dict, r: Report) -> None:
    """land.py: the TPU grip-land sweep for drill_storage.flex.LAND_FIT. Hex is
    left uncut on purpose (module docstring); every other bore gets a land +
    relief step at LAND_FIT + offset."""
    r.section("land.py -- TPU grip-land sweep (drill_storage.flex)")
    bars = list(fam.children)
    r.check(
        len(bars) == len(land.LAND_OFFSETS),
        "one bar per land offset",
        f"{len(bars)} bars, {len(land.LAND_OFFSETS)} offsets",
    )
    names = [land.bar_name(o) for o in land.LAND_OFFSETS]
    r.check(
        len(set(names)) == len(names),
        "every offset's export filename is unique (no +/- sign collision)",
        f"{names}",
    )

    z_land = fc.BORE_FOOT_RELIEF + fc.EFFECTIVE_LAND_H / 2
    z_relief = fc.LAND_H + fc.LAND_LEAD_IN + 2.0
    z_mid = FRAME_PLATE_H / 2
    x_hex, _ = placements["hex"]
    diams = sorted(DRILL_DIAMS)
    for offset, bar in zip(land.LAND_OFFSETS, bars):
        # land.create() stacks bars along Y too (Pos(0, i*(depth+BAR_GAP), 0));
        # only the first bar (i=0) sits at y=0, so every other bar needs its own
        # row offset added back into the sample point -- as in check_sweep.
        y0 = bar.bounding_box().center().Y
        for d in (diams[0], diams[-1]):
            x, _ = placements[f"{d:g}"]
            land_r = (d + fc.LAND_FIT + offset) / 2
            relief_r = (d + fc.RELIEF_FIT) / 2
            ok = (
                not is_solid_at(bar, x + land_r - PROBE, y0, z_land)
                and is_solid_at(bar, x + land_r + PROBE, y0, z_land)
                and not is_solid_at(bar, x + relief_r - PROBE, y0, z_relief)
                and is_solid_at(bar, x + relief_r + PROBE, y0, z_relief)
            )
            r.check(
                ok,
                f"land {offset:+.2f}: {d:g} mm land r={land_r:.3f} / relief r={relief_r:.3f}",
                f"sampled at z={z_land:.2f} / {z_relief:.2f}",
            )
        r.check(
            is_solid_at(bar, x_hex, y0, z_mid),
            f"land {offset:+.2f}: hex socket is left uncut on purpose",
            "no hex land -- judged on the cartridge, not swept here",
        )


# --- Minimum feature size ---------------------------------------------------------


def check_feature_sizes(r: Report) -> None:
    """A 0.4 mm nozzle resolves ~2 perimeters (0.8 mm); anything narrower doesn't
    slice as a distinct wall."""
    r.section("minimum feature size (0.4 mm nozzle)")
    r.check(
        box.RIB_WIDTH >= MIN_WALL,
        "rib bead width prints as at least 2 perimeters",
        f"{box.RIB_WIDTH:.2f} mm (min {MIN_WALL})",
    )
    r.check(
        HOLE_WALL >= MIN_WALL,
        "the minimum adjacent-hole wall is at least 2 perimeters",
        f"{HOLE_WALL:.2f} mm (min {MIN_WALL})",
    )


# --- Sharp edges -------------------------------------------------------------------


def _label_edges(part: Part):
    """Edges lying flat on the coupon's own +-Y face -- where the size legend and
    the variant title are engraved."""
    b = part.bounding_box()

    def pred(e: Edge) -> bool:
        eb = e.bounding_box()
        return (abs(eb.min.Y - b.max.Y) < 0.05 and abs(eb.max.Y - b.max.Y) < 0.05) or (
            abs(eb.min.Y - b.min.Y) < 0.05 and abs(eb.max.Y - b.min.Y) < 0.05
        )

    return pred


def check_sharp_edges(parts: dict[str, Part], r: Report) -> None:
    """House rule: chamfer horizontal edges, fillet vertical ones. The only
    deliberate exception is the engraved label text -- bevelling a glyph destroys
    it, the same reasoning drill_storage.flex.checks uses for its wall legend.
    Everything else that comes back here is a real, currently untreated edge (see
    the implementer's report for what each family's failures are)."""
    r.section("sharp edges")
    for name, part in parts.items():
        allow = (
            (_label_edges(part), "engraved label -- bevelling a glyph destroys it"),
        )
        bad = sharp_convex_edges(part, allow=allow)
        r.check(
            not bad,
            f"{name}: no unexplained sharp convex edges",
            f"{len(bad)} found" if bad else "all treated or named",
        )


def run() -> Report:
    r = Report()

    ribbed_p = ribbed.create()
    plain_p = plain.create()
    taper_p = taper.create()
    placements = _placements(DRILL_DIAMS)

    parts = {"ribbed": ribbed_p, "plain": plain_p, "taper": taper_p}
    check_layout(parts, placements, r)
    check_plain(plain_p, placements, r)
    check_taper(taper_p, placements, r)
    check_ribbed(ribbed_p, placements, r)

    sweep_fam = sweep.create()
    check_sweep(sweep_fam, r)

    small_fam = small.create()
    check_offset_family(
        small_fam, small.SMALL_OFFSETS, small.SMALL_DIAMS, False, "small", r
    )

    full_fam = full.create()
    check_offset_family(
        full_fam, full.FULL_OFFSETS, full.FULL_DIAMS, full.FULL_HEX, "full", r
    )

    land_fam = land.create()
    check_land(land_fam, placements, r)

    check_feature_sizes(r)

    check_sharp_edges(
        {
            "ribbed": ribbed_p,
            "plain": plain_p,
            "taper": taper_p,
            "sweep grip=0.22": sweep_fam.children[sweep.SWEEP_GRIPS.index(0.22)],
            "small off=+0.00": small_fam.children[small.SMALL_OFFSETS.index(0.0)],
            "full off=+0.00": full_fam.children[full.FULL_OFFSETS.index(0.0)],
            "land off=+0.00": land_fam.children[land.LAND_OFFSETS.index(0.0)],
        },
        r,
    )

    return r


def main() -> None:
    import sys

    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
