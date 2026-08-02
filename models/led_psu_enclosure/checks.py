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
    # Sample the FRONT ledge: the end-wall ledges are deliberately interrupted by
    # the vent apertures, which is fine (the shelf is carried front-to-back) and
    # actually lets plenum air past the shelf edge.
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


def check_installability(r: Report) -> None:
    """Every internal part must physically drop through the rim opening."""
    r.section("installability through the rim opening")
    ox, oy = c.installable_x(), c.installable_y()
    sx, sy = c.shelf_size()
    px, py = c.psu_plate_size()
    r.check(
        sx <= ox and sy <= oy, "shelf fits", f"{sx:.1f}x{sy:.1f} <= {ox:.1f}x{oy:.1f}"
    )
    r.check(
        px <= ox and py <= oy,
        "PSU plate fits",
        f"{px:.1f}x{py:.1f} <= {ox:.1f}x{oy:.1f}",
    )
    r.check(
        c.PSU_X <= ox and c.PSU_Y <= oy,
        "PSU itself fits",
        f"{c.PSU_X}x{c.PSU_Y} <= {ox:.1f}x{oy:.1f}",
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
    """The fuse block and controller must fit side by side on the shelf."""
    r.section("shelf packing")
    sx, sy = c.shelf_size()
    total = c.FUSE_X + c.CTRL_TAB_X
    r.check(
        total < sx,
        "fuse block + controller fit across the shelf",
        f"{total:.1f} in {sx:.1f} ({sx - total:.1f} mm spare)",
    )
    depth = c.SHELF_FRONT_KEEPOUT + max(c.FUSE_Y, c.CTRL_Y)
    r.check(
        depth < c.INTERIOR_Y,
        "keep-out plus deepest component fits front-to-back",
        f"{depth:.1f} in {c.INTERIOR_Y:.1f}",
    )
    r.check(
        c.RJ45_BEHIND <= c.SHELF_FRONT_KEEPOUT,
        "deepest wall intruder clears the shelf components",
        f"RJ45 {c.RJ45_BEHIND} <= keepout {c.SHELF_FRONT_KEEPOUT}",
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


def check_cartridges(tray: Part, r: Report) -> None:
    """The optional blank/fan cartridges still have to fit the same port."""
    from . import vent

    r.section("vent cartridges")
    comps = mocks.keepouts()
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
    check_sp17_panels(tray, r)
    check_sp17_flat(tray, r)
    check_vents(tray, r)
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
