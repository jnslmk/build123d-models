"""Geometry assertions for the enclosure.

Ribs, wall gaps, blind pockets and fit clearances are invisible in a projection,
so per the repo's house rule these get verified in code by point-sampling the
solid rather than by eye.

    uv run check led_psu_enclosure
    uv run python -m models.led_psu_enclosure.checks
"""

from __future__ import annotations

from build123d import Part, Pos

# The instrument itself lives in models.lib.checks; re-exported under the old
# names (the `X as X` form marks a deliberate re-export) so anything already
# importing them from here keeps working.
from ..lib.checks import (
    TOL as TOL,
    Report as Report,
    is_solid_at as is_solid_at,
)
from . import config as c
from . import mocks
from . import penetrations as pen
from .tray import create_tray_finished
from .util import as_part


def check_shell(tray: Part, r: Report) -> None:
    """Wall/floor are solid where they should be and void where they shouldn't."""
    r.section("shell")
    mid_z = 50.0
    wall_mid = c.INTERIOR_X / 2 + c.WALL / 2
    # Sample at y=55, clear of the vent recess (which reaches y=+-45).
    r.check(is_solid_at(tray, wall_mid, 55.0, mid_z), "side wall is solid")
    r.check(not is_solid_at(tray, 0, 0, mid_z), "interior is hollow")
    r.check(is_solid_at(tray, 0, 0, -c.FLOOR / 2), "floor is solid")
    r.check(not is_solid_at(tray, 0, 0, -c.FLOOR - 1), "nothing below the floor")

    # The rim band really is thicker than the plain wall. Sample above the
    # snap groove, which legitimately hollows the band's inner face lower down.
    band_z = c.rim_band_z() + c.RIM_BAND_H * 0.8
    band_y = 30.0
    r.check(
        is_solid_at(tray, c.installable_x() / 2 + 1.0, band_y, band_z),
        "rim band thickens the wall inward",
    )
    r.check(
        not is_solid_at(tray, c.installable_x() / 2 - 1.0, band_y, band_z),
        "rim band opening is clear",
    )


def check_plate_studs(tray: Part, r: Report) -> None:
    """The snap studs are the only plate fixing -- and the floor stays sealed."""
    r.section("PSU plate snap studs")
    for x, y in _plate_boss_positions():
        at = f"({x:+.0f}, {y:+.0f})"
        r.check(is_solid_at(tray, x, y, -1.0), f"floor under the stud is sealed {at}")
        r.check(is_solid_at(tray, x, y, 0.5), f"stud base block is solid {at}")
        r.check(not is_solid_at(tray, x, y, 3.0), f"spring bore is open {at}")
        r.check(is_solid_at(tray, x + 2.9, y, 3.0), f"spring wall is present {at}")
        r.check(not is_solid_at(tray, x, y + 2.9, 3.0), f"split slot is open {at}")
        r.check(is_solid_at(tray, x + 4.7, y, 3.0), f"seat ring is present {at}")
        r.check(
            not is_solid_at(tray, x + 3.8, y, 3.0),
            f"flex gap between tube and seat ring {at}",
        )
        r.check(
            is_solid_at(tray, x + 3.6, y, c.stud_peak_z()), f"snap head is present {at}"
        )

    # Spring + catch arithmetic, with the same cantilever model as the vent latch.
    wall = (c.STUD_TUBE_D - c.STUD_BORE_D) / 2
    catch = (c.STUD_HEAD_D - c.STUD_HOLE_D) / 2
    spring_len = c.stud_peak_z() - 1.0  # flexes from the base block to the peak
    strain = 1.5 * wall * catch / spring_len**2
    r.check(strain < 0.025, "stud snap strain is survivable", f"{strain * 100:.1f} %")
    r.check(catch >= 0.4, "catch engagement holds the plate", f"{catch:.2f} mm/side")

    head_top = c.stud_peak_z() + (c.STUD_HEAD_D - c.STUD_TUBE_D) / 2 + 0.3
    plate_top = c.PSU_PLATE_BOSS_H + c.PSU_PLATE_T
    r.check(
        plate_top - head_top >= 0.5,
        "stud head stays clear of the PSU bottom",
        f"{plate_top - head_top:.2f} mm",
    )
    r.check(
        c.STUD_HEAD_D < c.STUD_RECESS_D,
        "head turns inside the plate recess",
        f"{c.STUD_HEAD_D:.1f} < {c.STUD_RECESS_D:.1f}",
    )
    gap = (c.STUD_RING_ID - c.STUD_TUBE_D) / 2
    flex_at_ring = catch * (c.PSU_PLATE_BOSS_H - 1.0) / spring_len
    r.check(
        flex_at_ring < gap,
        "tube flex does not rub the seat ring",
        f"{flex_at_ring:.2f} < {gap:.2f} mm",
    )


def _plate_boss_positions() -> list[tuple[float, float]]:
    from .tray import PLATE_BOSS_POS

    return PLATE_BOSS_POS


def check_gasket_groove(tray: Part, r: Report) -> None:
    """The groove has to be a continuous ring or it does not seal."""
    r.section("gasket groove")
    z_in = c.INTERIOR_Z - c.GASKET_GROOVE_D / 2
    hx = c.installable_x() / 2 + c.GASKET_INSET
    hy = c.installable_y() / 2 + c.GASKET_INSET
    samples = [(x, hy) for x in (-90, -45, 0, 45, 90)]
    samples += [(x, -hy) for x in (-90, -45, 0, 45, 90)]
    samples += [(hx, y), (-hx, y)] if (y := 0.0) is not None else []
    samples += [(hx, 40), (-hx, 40), (hx, -40), (-hx, -40)]
    continuous = all(not is_solid_at(tray, x, y, z_in) for x, y in samples)
    r.check(continuous, f"groove is open at all {len(samples)} sampled points")

    below = all(
        is_solid_at(tray, x, y, c.INTERIOR_Z - c.GASKET_GROOVE_D - 1.0)
        for x, y in samples
    )
    r.check(below, "rim still solid under the groove")


def check_shelf_ledge(tray: Part, r: Report) -> None:
    r.section("shelf ledge")
    top = c.shelf_ledge_z()
    # Sample the FRONT ledge: the end-wall runs are deliberately cut away by
    # _vent_ledge_relief(), which is fine (the shelf is carried front-to-back)
    # and actually lets plenum air past the shelf edge.
    inner_y = c.INTERIOR_Y / 2 - c.SHELF_LEDGE_W / 2
    r.check(
        is_solid_at(tray, 0, inner_y, top - 0.5), "ledge is solid just below its top"
    )
    r.check(
        not is_solid_at(tray, 0, inner_y, top + 0.5), "space above the ledge is clear"
    )
    r.check(
        not is_solid_at(tray, 0, inner_y, top - c.SHELF_LEDGE_W + 0.5),
        "ledge underside is tapered away (45 self-support)",
    )
    r.check(
        is_solid_at(tray, 0, -inner_y, top - 0.5),
        "front ledge is present too (shelf is carried front-to-back)",
    )
    # ...and the end-wall runs really are cut away. The docstring always said
    # they were; until _vent_ledge_relief() existed they were not, and they sat
    # exactly where the vent frame, the fan and its yoke's rails now live.
    # Sampled inboard of the frame's face -- the relief deliberately stops there,
    # because past it the "ledge" and the frame are the same material.
    probe_x = c.INTERIOR_X / 2 - c.SHELF_LEDGE_W + 1.0
    relief_y = c.VENT_W / 2 + c.VENT_FRAME_MARGIN_Y
    for s in (-1, 1):
        end = "+X" if s > 0 else "-X"
        r.check(
            not is_solid_at(tray, s * probe_x, 0, top - 0.5),
            f"{end} end ledge is cut away across the port",
        )
        r.check(
            not is_solid_at(tray, s * probe_x, relief_y - 1.0, top - 0.5),
            f"{end} end ledge is cut out to the frame's full width",
        )
        # Positive control: beyond the relief the ledge is still there, so a
        # cut that quietly took the whole ring would not read as a pass.
        r.check(
            is_solid_at(tray, s * probe_x, relief_y + 4.0, top - 0.5),
            f"{end} end ledge survives outboard of the relief",
        )


def check_installability(r: Report) -> None:
    """Every internal part must physically drop in past the rim AND the frames.

    The rim mouth is not the narrowest thing on the way down: the two vent
    frames stand ``VENT_FRAME_T`` proud of the end walls and take the clear
    opening from 221 mm to 218. Checking against the mouth alone is how the
    shelf came to be sized with exactly zero clearance at the frames.
    """
    r.section("installability through the rim opening")
    ox, oy = c.drop_opening()
    mouth_x = c.installable_x()
    r.check(
        ox < mouth_x,
        "the vent frames, not the rim, are the narrowest point in X",
        f"{ox:.1f} < mouth {mouth_x:.1f}",
    )
    for name, (px, py) in (
        ("shelf", c.shelf_size()),
        ("PSU plate", c.psu_plate_size()),
        ("PSU itself", (c.PSU_X, c.PSU_Y)),
    ):
        gap = min((ox - px) / 2, (oy - py) / 2)
        r.check(
            gap >= 0.5,
            f"{name} fits with clearance",
            f"{px:.1f}x{py:.1f} in {ox:.1f}x{oy:.1f} ({gap:.1f} mm a side)",
        )


def check_interference(tray: Part, r: Report) -> None:
    """No component may occupy the same space as the shell, or as another part."""
    r.section("component interference")
    parts = mocks.keepouts()
    for m in parts:
        vol = (m & tray).volume
        r.check(vol < 1.0, f"{m.label} clears the shell", f"{vol:.1f} mm3 overlap")

    import itertools

    clashes = [
        (p.label, q.label, (p & q).volume)
        for p, q in itertools.combinations(parts, 2)
        if (p & q).volume > 1.0
    ]
    r.check(not clashes, "components do not clash with each other", str(clashes))


def check_shelf_components(r: Report) -> None:
    """The fuse block and controller must fit side by side on the shelf.

    Checked against where they are actually *placed*, not just their total
    width: with 204.2 mm of component on a 215 mm shelf and a fan yoke claiming
    one end, every margin here is single-digit millimetres.
    """
    r.section("shelf packing")
    sx, sy = c.shelf_size()
    high = c.vent_high_end()
    notch_x, _ = c.shelf_fan_notch()

    fuse_lo = mocks.FUSE_X_CENTER - c.FUSE_X / 2
    fuse_hi = mocks.FUSE_X_CENTER + c.FUSE_X / 2
    tab_lo = mocks.CTRL_X_CENTER - c.CTRL_TAB_X / 2
    tab_hi = mocks.CTRL_X_CENTER + c.CTRL_TAB_X / 2

    r.check(
        fuse_lo > -sx / 2 + 1.0,
        "fuse block sits on the shelf, not over its edge",
        f"{fuse_lo:.1f} inside {-sx / 2:.1f} ({fuse_lo + sx / 2:.1f} mm)",
    )
    r.check(
        tab_lo - fuse_hi >= 2.0,
        "fuse block and controller do not touch",
        f"{tab_lo - fuse_hi:.1f} mm gap",
    )
    # The controller's bolts go through the shelf, so they must land on shelf,
    # not in the bite taken out of it for the fan -- and it is the HOLE EDGE that
    # has to clear it, not the centre. Comparing centres left 0.3 mm of shelf
    # between the hole and the notch and read as a comfortable pass.
    from .shelf import CTRL_BOLT_CLEAR

    bolt_edge = mocks.CTRL_X_CENTER + c.CTRL_BOLT_PITCH / 2 + CTRL_BOLT_CLEAR / 2
    r.check(
        high * bolt_edge < notch_x - 1.5,
        "controller's outer bolt hole leaves shelf between it and the fan notch",
        f"hole edge {bolt_edge:.1f}, notch at {high * notch_x:.1f}"
        f" ({notch_x - high * bolt_edge:.1f} mm)",
    )
    r.check(
        high * tab_hi < c.vent_fan_back_x() - 0.5,
        "controller's tab tip clears the internal fan",
        f"x {tab_hi:.1f} vs fan back at {high * c.vent_fan_back_x():.1f}",
    )

    depth = c.SHELF_FRONT_KEEPOUT + max(c.FUSE_Y, c.CTRL_Y)
    usable = sy / 2 + c.INTERIOR_Y / 2
    r.check(
        depth < usable,
        "keep-out plus deepest component fits front-to-back on the shelf",
        f"{depth:.1f} in {usable:.1f}",
    )
    r.check(
        c.RJ45_BEHIND <= c.SHELF_FRONT_KEEPOUT,
        "deepest wall intruder clears the shelf components",
        f"RJ45 {c.RJ45_BEHIND} <= keepout {c.SHELF_FRONT_KEEPOUT}",
    )


def check_connector_row(r: Report) -> None:
    """The whole front-wall row shares one Z, squeezed from both directions."""
    r.section("connector row height")
    # Below: the RJ45 is the widest pad and would otherwise pass through the
    # shelf plate, which reaches all the way to the front wall.
    pad_bottom = c.RJ45_Z - c.RJ45_PAD_D / 2
    r.check(
        pad_bottom > c.shelf_top_z(),
        "RJ45 pad clears the shelf plate",
        f"{pad_bottom:.1f} > {c.shelf_top_z():.1f}",
    )
    # Above: the SP1712 counterbores are cut into the plain wall, so they must
    # finish before the wall thickens into the rim band.
    bore_top = c.SP17_Z + c.SP17_COUNTERBORE_D / 2
    r.check(
        bore_top < c.rim_band_z(),
        "SP1712 counterbores finish below the rim band",
        f"{bore_top:.1f} < {c.rim_band_z():.1f}",
    )


def _panel_thickness(tray: Part, x: float, z: float) -> float:
    """Measure the front wall at (x, z) by marching along Y in 0.05 mm steps."""
    y0 = -c.INTERIOR_Y / 2 - c.WALL - 1.0
    step = 0.05
    hits = 0
    y = y0
    while y < -c.INTERIOR_Y / 2 + 1.0:
        if is_solid_at(tray, x, y, z):
            hits += 1
        y += step
    return hits * step


def check_sp17_panels(tray: Part, r: Report) -> None:
    """The SP1712 refuses to mount through more than 3 mm of panel."""
    r.section("SP1712 panel thickness (spec: <= 3.0 mm)")
    for i, x in enumerate(c.sp17_positions()):
        # Sample beside the bore but inside the counterbore, where the nut seats.
        probe_x = x + c.SP17_CUTOUT_D / 2 + 3.0
        t = _panel_thickness(tray, probe_x, c.SP17_Z)
        ok = 2.4 <= t <= c.SP17_MAX_PANEL
        r.check(ok, f"connector {i + 1} panel", f"{t:.2f} mm")

    # Away from any counterbore the wall must still be full thickness.
    t = _panel_thickness(tray, 0.0, 20.0)
    r.check(abs(t - c.WALL) < 0.2, "plain front wall is full thickness", f"{t:.2f} mm")


def check_sp17_flat(tray: Part, r: Report) -> None:
    """The anti-rotation flat must be at the TOP so it prints as a bridge."""
    r.section("SP1712 D-flat orientation")
    x = c.sp17_positions()[0]
    y = -c.INTERIOR_Y / 2 - c.WALL / 2
    flat_z = c.SP17_Z + (c.SP17_CUTOUT_FLAT - c.SP17_CUTOUT_D / 2)
    r.check(
        is_solid_at(tray, x, y, flat_z + 0.5),
        "material sits just above the flat (it bridges)",
    )
    r.check(
        not is_solid_at(tray, x, y, flat_z - 0.5),
        "bore is open just below the flat",
    )
    r.check(
        not is_solid_at(tray, x, y, c.SP17_Z - c.SP17_CUTOUT_D / 2 + 0.5),
        "bore is open at the bottom (full radius, no flat there)",
    )


def check_vents(tray: Part, r: Report) -> None:
    r.section("vent ports")
    for z, s in pen.vent_ports():
        side = "+X" if s > 0 else "-X"
        r.check(
            not is_solid_at(tray, s * (c.INTERIOR_X / 2 + c.WALL / 2), 0, z),
            f"{side} aperture is open through the wall",
        )
        # Frame present beside the aperture.
        y_frame = c.VENT_W / 2 + c.VENT_FRAME_MARGIN_Y / 2
        r.check(
            is_solid_at(tray, s * (c.INTERIOR_X / 2 - c.VENT_FRAME_T / 2), y_frame, z),
            f"{side} reinforcing frame is present",
        )
        # Self-tapping pilots must be blind, and must actually have been cut.
        pilot_end = c.INTERIOR_X / 2 + c.WALL - c.VENT_RECESS_D - c.VENT_SCREW_PILOT_L
        blind = all(
            is_solid_at(tray, s * (pilot_end - 0.7), y, zz)
            for y, zz in pen.vent_screw_positions(z)
        )
        r.check(blind, f"{side} cartridge screw pilots are blind")
        open_ = all(
            not is_solid_at(tray, s * (pilot_end + 1.0), y, zz)
            for y, zz in pen.vent_screw_positions(z)
        )
        r.check(open_, f"{side} cartridge screw pilots were actually cut")

    # The frames must not intrude into the rim opening, or the shelf won't drop in.
    top = max(z + c.VENT_H / 2 + c.VENT_FRAME_MARGIN_Z for z, _ in pen.vent_ports())
    bottom = min(z - c.VENT_H / 2 - c.VENT_FRAME_MARGIN_Z for z, _ in pen.vent_ports())
    r.check(bottom > 0, "vent frames stay above the floor", f"bottom {bottom:.1f}")
    r.check(
        c.VENT_W / 2 + c.VENT_SCREW_OFFSET + 3.0  # M3 head radius
        < c.VENT_W / 2 + c.VENT_FRAME_MARGIN_Y,
        "cartridge screws land inside the frame, not past its edge",
    )
    r.check(
        top < c.rim_band_z(),
        "vent frames stay below the rim band",
        f"top {top:.1f} < {c.rim_band_z():.1f}",
    )


def check_shutters(tray: Part, r: Report) -> None:
    """The sliding shutter: it shuts, it opens, and no jet gets through it."""
    from . import vent

    r.section("vent shutter")
    panel = vent.create_shutter()
    slider = vent.create_slider()
    face_z = vent.PANEL_T + c.VENT_SLIDER_T / 2

    # The mechanism itself, sampled through the slider at the panel's own slot
    # rows: shut must be solid at every one of them, open must be clear.
    for state, cy, want in (
        ("open", vent.OPEN_CENTER, False),
        ("shut", vent.SHUT_CENTER, True),
    ):
        placed = as_part(Pos(0, cy, vent.PANEL_T) * slider)
        hits = [
            is_solid_at(placed, sx * vent.COL_X, y, face_z)
            for y in vent.SLOT_ROWS
            for sx in (-1, 1)
        ]
        r.check(all(h is want for h in hits), f"slider is {state} at every slot row")
        r.check(
            (placed & panel).volume < 0.01, f"slider runs free in the channel ({state})"
        )

    # The tilt is what keeps water out: solid directly behind every face opening,
    # with the inner mouth SLOT_RISE further up the wall.
    r.check(
        all(
            not is_solid_at(panel, vent.COL_X, y, vent.PANEL_T - 0.2)
            for y in vent.SLOT_ROWS
        ),
        "louvre slots are open on the weather face",
    )
    r.check(
        all(is_solid_at(panel, vent.COL_X, y, 0.2) for y in vent.SLOT_ROWS),
        "no straight-line path through the louvre",
        f"rise {vent.SLOT_RISE:.1f} >= slot {c.VENT_SLOT_H:.1f}",
    )
    r.check(
        all(
            not is_solid_at(panel, vent.COL_X, y + vent.SLOT_RISE, 0.2)
            for y in vent.SLOT_ROWS
        ),
        "every slot does break through on the inside",
    )

    overlap = (c.VENT_SLOT_BAR - c.VENT_SLOT_H) / 2
    r.check(
        overlap >= 0.25, "shut bars overlap their slots", f"{overlap:.2f} mm a side"
    )
    grip = vent.SLIDER_W / 2 - (vent.CHANNEL_W / 2 - c.VENT_LIP)
    r.check(grip >= 0.8, "rail lips hold the slider", f"{grip:.2f} mm engagement")
    r.check(
        c.VENT_DETENT < c.VENT_SLIDER_LIFT,
        "slider has the slack to ride over the detent",
        f"{c.VENT_DETENT} < {c.VENT_SLIDER_LIFT}",
    )

    # Rails sit on the flange land; over the gasket groove they would bridge a
    # 1.5 mm void, and the panel has to hold them.
    gasket_x = c.VENT_W / 2 + vent.GASKET_INSET - vent.GASKET_GROOVE_W / 2
    rail_x = vent.CHANNEL_W / 2 + c.VENT_RAIL_W
    r.check(
        rail_x < gasket_x,
        "rails stay inboard of the gasket groove",
        f"{rail_x:.1f} < {gasket_x:.1f}",
    )
    r.check(
        vent.CHANNEL_TOP + c.VENT_END_WALL < vent.FLANGE_Y / 2,
        "the whole channel fits on the panel",
    )
    r.check(
        vent.OPEN_AREA > 500.0,
        "wide open is worth having",
        f"{vent.OPEN_AREA:.0f} mm2 per port on the face",
    )

    # Fitted, in both positions: nothing fouls the shell or the contents.
    comps = mocks.keepouts()
    for shut in (False, True):
        state = "shut" if shut else "open"
        for part in vent.seated_shutters(shut=shut):
            vol = (part & tray).volume
            r.check(
                vol < 5.0,
                f"{part.label} ({state}) seats without fouling the shell",
                f"{vol:.1f} mm3",
            )
            clash = [
                (k.label, (part & k).volume) for k in comps if (part & k).volume > 1.0
            ]
            r.check(
                not clash, f"{part.label} ({state}) clears the components", str(clash)
            )


def _swept_up(part: Part, height: float) -> Part:
    """The volume a prismatic drop-in part passes through on its way out.

    Both the shelf and the PSU plate are plain extrusions, so sweeping the
    bottom face upward is exact, not an approximation -- and it is the only way
    to tell "fits where it sits" from "can actually be got in and out".

    Sanity-checked against a negative control: the same sweep of a shelf without
    its fan notch does hit the fan (~4.5 cm3) and the yoke (~6.6 cm3), so a
    "0 mm3 in its path" pass means the notch works, not that the sweep is empty.
    """
    from build123d import Axis, BuildPart, add, extrude

    # ty resolves Part.faces() to Mixin2D.faces and rejects the receiver; it is
    # the right call at runtime.
    face = part.faces().sort_by(Axis.Z).first  # ty: ignore[invalid-argument-type]
    with BuildPart() as bp:
        add(face)
        extrude(amount=height)
    return bp.part


def check_internal_fan(tray: Part, r: Report) -> None:
    """The 24 V exhaust fan, its yoke, and the millimetres they live on."""
    from . import shelf as shelf_mod
    from . import vent

    r.section("internal fan + yoke")
    s = c.vent_high_end()
    yoke = vent.seated_fan_yoke()
    fan = mocks.internal_fan()

    r.check(
        (yoke & tray).volume < 5.0,
        "yoke seats on the frame without fouling the shell",
        f"{(yoke & tray).volume:.1f} mm3",
    )
    clash = [
        (m.label, (yoke & m).volume)
        for m in mocks.keepouts()
        if m.label != fan.label and (yoke & m).volume > 1.0
    ]
    r.check(not clash, "yoke clears every component", str(clash))

    # The controller's mounting tab passes *through* the yoke's throat -- that
    # is what lets a 118 mm controller and a 40 mm fan share one 215 mm shelf.
    # Sampled at the tab, not inferred from the bore radius.
    tab_z = c.shelf_top_z() + 1.5
    for y in (mocks.CTRL_Y_CENTER - 8.0 + 1.0, mocks.CTRL_Y_CENTER + 8.0 - 1.0):
        r.check(
            not is_solid_at(
                yoke, s * (c.vent_yoke_back_x() + c.VENT_YOKE_T / 2), y, tab_z
            ),
            f"yoke throat is open where the controller tab passes (y={y:+.1f})",
        )

    # Blind pilots, actually cut, and not meeting the shutter's own from outside.
    inner = c.vent_frame_inner_x()
    for dz in (-c.VENT_YOKE_SCREW_DZ, c.VENT_YOKE_SCREW_DZ):
        z = c.VENT_HIGH_Z + dz
        for y in (-c.vent_yoke_screw_y(), c.vent_yoke_screw_y()):
            r.check(
                not is_solid_at(tray, s * (inner + 1.0), y, z),
                f"yoke pilot was cut (y={y:+.0f}, z={z:.0f})",
            )
            r.check(
                is_solid_at(tray, s * (inner + c.VENT_SCREW_PILOT_L + 0.7), y, z),
                f"yoke pilot is blind (y={y:+.0f}, z={z:.0f})",
            )
    # Yoke and shutter pilots share a Y and are driven into opposite faces of a
    # slab only 5.5 mm thick -- two 4 mm pilots would meet head-on. What keeps
    # them apart is the offset in Z, so that is what gets asserted.
    slab = c.WALL + c.VENT_FRAME_T - c.VENT_RECESS_D
    r.check(
        2 * c.VENT_SCREW_PILOT_L > slab,
        "the two pilot sets would meet if they shared a Z (hence the offset)",
        f"2 x {c.VENT_SCREW_PILOT_L:.1f} through {slab:.1f} mm",
    )
    r.check(
        c.VENT_YOKE_SCREW_DZ >= c.VENT_SCREW_PILOT_D + 2.0,
        "yoke pilots stand clear of the shutter's in Z",
        f"{c.VENT_YOKE_SCREW_DZ:.1f} mm apart, pilots are O{c.VENT_SCREW_PILOT_D:.1f}",
    )

    # The fan blows onto the louvre panel's inner face; that gap is what it has
    # to spread through to reach the full width of the slot field.
    gap = (c.INTERIOR_X / 2 + c.WALL - c.VENT_RECESS_D) - c.INTERIOR_X / 2
    r.check(gap > 0.0, "fan face clears the shutter panel", f"{gap:.1f} mm")
    r.check(
        c.vent_yoke_rail_h() > 0.0,
        "fan is thicker than the frame is proud (the yoke needs the difference)",
        f"rail standoff {c.vent_yoke_rail_h():.1f} mm",
    )
    r.check(
        c.VENT_FAN_SIZE <= c.VENT_H,
        "fan fits the aperture it blows through",
        f"{c.VENT_FAN_SIZE:.0f} <= {c.VENT_H:.0f}",
    )

    # And the whole point of the shelf's notch: the shelf still lifts out.
    sweep = _swept_up(shelf_mod.seated(), c.INTERIOR_Z - c.shelf_ledge_z())
    for obstacle in (fan, yoke):
        vol = (sweep & obstacle).volume
        r.check(
            vol < 1.0,
            f"shelf lifts straight out past the {obstacle.label}",
            f"{vol:.1f} mm3 in its path",
        )


def check_cartridges(tray: Part, r: Report) -> None:
    """The optional blank/fan cartridges still have to fit the same port."""
    from . import vent

    r.section("vent cartridges")
    fan = mocks.internal_fan()
    # A cartridge's plug body fills the aperture the internal fan noses into, so
    # the two are mutually exclusive by construction: the high port carries a
    # shutter + fan, or a blank, never both. Assert that rather than pretend the
    # clash is a bug -- and keep checking the cartridges against everything else.
    comps = [k for k in mocks.keepouts() if k.label != fan.label]
    exclusive = [b for b in vent.seated_blanks() if (b & fan).volume > 1.0]
    r.check(
        len(exclusive) == 1,
        "a blanking plug and the internal fan claim the same port",
        f"{[b.label for b in exclusive]} -- fit one or the other",
    )
    for b in vent.seated_blanks():
        vol = (b & tray).volume
        r.check(
            vol < 5.0, f"{b.label} seats without fouling the shell", f"{vol:.1f} mm3"
        )
        clash = [(k.label, (b & k).volume) for k in comps if (b & k).volume > 1.0]
        r.check(not clash, f"{b.label} clears the components", str(clash))

    # A cantilever this short would snap rather than click. Keep the strain a
    # printed part can survive: eps ~= 1.5 * t * deflection / L^2.
    arm_len = vent.PLUG_T + vent.LATCH_TAIL
    strain = 1.5 * vent.LATCH_T * vent.LATCH_OVERHANG / arm_len**2
    r.check(strain < 0.03, "latch strain is survivable", f"{strain * 100:.1f} %")


def check_lid_and_deck(tray: Part, r: Report) -> None:
    """The lid must snap into the mouth, and the deck parts must not foul it."""
    from . import lid as lid_mod
    from . import plate as plate_mod
    from . import shelf as shelf_mod

    r.section("lid + deck fit")
    lid = lid_mod.seated()
    vol = (lid & tray).volume
    r.check(vol < 5.0, "lid snaps in without interfering", f"{vol:.1f} mm3")

    # The snap joint: groove open where the bead lands, band solid behind it,
    # and the bead really reaching past the mouth face into that void.
    face = c.installable_x() / 2
    z = c.INTERIOR_Z - c.SNAP_BEAD_Z
    r.check(
        not is_solid_at(tray, face - c.SNAP_GROOVE_D / 2, 0.0, z),
        "snap groove is open at the bead line",
    )
    r.check(
        is_solid_at(tray, face + c.SNAP_GROOVE_D + 0.5, 0.0, z),
        "rim band is solid behind the snap groove",
    )
    engage = c.SNAP_BEAD - c.LID_PLUG_CLEAR
    r.check(
        is_solid_at(lid, face - c.LID_PLUG_CLEAR + engage / 2, 0.0, z),
        "lid bead protrudes past the mouth face",
        f"engagement {engage:.2f} mm",
    )
    r.check(
        engage <= c.SNAP_GROOVE_D,
        "bead engagement fits inside the groove (no weld)",
        f"{engage:.2f} <= {c.SNAP_GROOVE_D:.2f}",
    )

    # The plug skirt hangs 10 mm into the mouth -- nothing inside may reach it.
    fouls = [
        (m.label, (lid & m).volume) for m in mocks.keepouts() if (lid & m).volume > 1.0
    ]
    r.check(not fouls, "lid plug clears every component", str(fouls))

    for mod, name in ((plate_mod, "psu_plate"), (shelf_mod, "shelf")):
        part = mod.seated()
        v = (part & tray).volume
        r.check(v < 50.0, f"{name} drops in without fouling the shell", f"{v:.1f} mm3")


def run() -> Report:
    r = Report()
    tray = create_tray_finished()
    check_shell(tray, r)
    check_plate_studs(tray, r)
    check_gasket_groove(tray, r)
    check_shelf_ledge(tray, r)
    check_installability(r)
    check_shelf_components(r)
    check_connector_row(r)
    check_sp17_panels(tray, r)
    check_sp17_flat(tray, r)
    check_vents(tray, r)
    check_internal_fan(tray, r)
    check_shutters(tray, r)
    check_cartridges(tray, r)
    check_lid_and_deck(tray, r)
    check_interference(tray, r)
    return r


def main() -> None:
    import sys

    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
