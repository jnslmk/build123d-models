"""The enclosure body: a deep tray that prints floor-down, open mouth up.

Shape decisions worth knowing before reading the code:

* **Rounded rectangles, not fillet ops.** Every vertical corner comes from
  ``RectangleRounded`` in the sketch, so there is no OCC edge fillet to fail.
  Per the repo gotchas, edge ops are reserved for places a boolean can't reach.
* **The wall thickens inward over the top band** (``RIM_WALL``) so the rim ring
  is wide enough to carry the gasket groove on its top face and the lid's snap
  groove on its inner face. The transition is a 45 taper cut by the cavity
  loft, not a ledge, so it prints without an overhang. There is NO outboard
  flange: the lid's sides sit flush with the walls.
* **Nothing bores through the shell.** The PSU bolts to a plate that snaps
  onto four hollow split studs (no screw can reach that joint -- see
  ``config``'s stud block), and the lid needs no fasteners at all -- it snaps
  into the mouth. The only holes through the wall are the ones components
  deliberately seal.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    add,
    chamfer,
    extrude,
    loft,
)

from . import config as c
from .util import top_chamfer_tool

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

# The four snap studs the PSU mounting plate clicks onto.
PLATE_BOSS_POS = [(sx * 100.0, sy * 48.0) for sx in (-1, 1) for sy in (-1, 1)]


def _plate_stud(x: float, y: float) -> Part:
    """One hollow split snap stud at (x, y) -- the plate detents onto this.

    A thin-walled tube rises off a solid base block, split into two C-springs
    by a slot; the 45 head compresses the springs as the plate's hole passes
    and detents into the plate's recess. The seat ring around it carries the
    plate at ``PSU_PLATE_BOSS_H`` and the gap between ring and tube is what
    the springs flex into. Every ramp is 45 deg: it prints clean, clicks in
    on a press, and releases on a straight pull.
    """
    peak = c.stud_peak_z()
    ramp = (c.STUD_HEAD_D - c.STUD_TUBE_D) / 2  # 45 deg: rise == radial run
    lead = peak - ramp
    tip = 0.3  # entry chamfer on the stud top
    top = peak + ramp + tip
    with BuildPart() as bp:
        with Locations((x, y, 0)):
            Cylinder(c.PSU_PLATE_BOSS_D / 2, 1.0, align=MIN_Z)  # base block
        with Locations((x, y, 1.0)):
            Cylinder(
                c.PSU_PLATE_BOSS_D / 2, c.PSU_PLATE_BOSS_H - 1.0, align=MIN_Z
            )  # seat ring
        with Locations((x, y, 1.0)):
            Cylinder(
                c.STUD_RING_ID / 2,
                c.PSU_PLATE_BOSS_H - 0.9,
                align=MIN_Z,
                mode=Mode.SUBTRACT,
            )  # the flex gap -- cut BEFORE the tube exists, or it eats the tube
        with Locations((x, y, 1.0)):
            Cylinder(c.STUD_TUBE_D / 2, lead - 1.0, align=MIN_Z)  # spring tube
        with Locations((x, y, lead)):
            Cone(c.STUD_TUBE_D / 2, c.STUD_HEAD_D / 2, ramp, align=MIN_Z)
        with Locations((x, y, peak)):
            Cone(c.STUD_HEAD_D / 2, c.STUD_TUBE_D / 2, ramp, align=MIN_Z)
        with Locations((x, y, peak + ramp)):
            Cone(c.STUD_TUBE_D / 2, c.STUD_TUBE_D / 2 - tip, tip, align=MIN_Z)
        # Hollow the spring; everything stops at the base block, so the floor
        # stays sealed. The slot also splits the seat ring into two arcs,
        # which is cosmetic -- they seat the plate just the same.
        with Locations((x, y, 1.0)):
            Cylinder(c.STUD_BORE_D / 2, top - 0.9, align=MIN_Z, mode=Mode.SUBTRACT)
            Box(
                c.STUD_SLOT_W,
                c.PSU_PLATE_BOSS_D + 2,
                top - 0.9,
                align=MIN_Z,
                mode=Mode.SUBTRACT,
            )
    return bp.part


def _chamfer_edge(builder: BuildPart, edge, size: float) -> None:
    """Chamfer one edge, isolating an OCC failure so it can't cascade."""
    saved = builder.part
    try:
        chamfer(edge, length=size)
    except Exception as exc:  # noqa: BLE001 -- OCC edge ops are flaky
        builder.part = saved  # ty: ignore[invalid-assignment]
        print(f"warning: chamfer skipped ({exc})")


def _cavity() -> Part:
    """The interior void, tapering inward over the top band.

    The last ``LEAD_IN`` at the mouth flares back out: a 45 lead-in on the
    rim's inner edge so the lid's snap bead ramps the plug skirt inward
    instead of catching on a sharp corner.
    """
    r = c.CORNER_R - c.WALL
    taper = c.RIM_WALL - c.WALL
    z_taper_start = c.rim_band_z() - taper
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(0)):
            RectangleRounded(c.INTERIOR_X, c.INTERIOR_Y, r)
        with BuildSketch(Plane.XY.offset(z_taper_start)):
            RectangleRounded(c.INTERIOR_X, c.INTERIOR_Y, r)
        with BuildSketch(Plane.XY.offset(c.rim_band_z())):
            RectangleRounded(c.installable_x(), c.installable_y(), r)
        with BuildSketch(Plane.XY.offset(c.INTERIOR_Z - c.LEAD_IN)):
            RectangleRounded(c.installable_x(), c.installable_y(), r)
        # Overshoot the rim top so the cut opens cleanly.
        with BuildSketch(Plane.XY.offset(c.INTERIOR_Z + 2)):
            RectangleRounded(
                c.installable_x() + 2 * c.LEAD_IN,
                c.installable_y() + 2 * c.LEAD_IN,
                r + c.LEAD_IN,
            )
        loft(ruled=True)
    return bp.part


def _shelf_ledge() -> Part:
    """A ring the shelf drops onto, with a 45 underside so it self-supports."""
    top = c.shelf_ledge_z()
    proj = c.SHELF_LEDGE_W
    bot = top - proj  # equal rise and run -> 45
    r = c.CORNER_R - c.WALL
    inner_r = max(r - proj, 0.5)

    with BuildPart() as taper:
        with BuildSketch(Plane.XY.offset(bot)):
            RectangleRounded(c.INTERIOR_X, c.INTERIOR_Y, r)
        with BuildSketch(Plane.XY.offset(top)):
            RectangleRounded(c.INTERIOR_X - 2 * proj, c.INTERIOR_Y - 2 * proj, inner_r)
        loft(ruled=True)

    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(bot)):
            RectangleRounded(c.INTERIOR_X, c.INTERIOR_Y, r)
        extrude(amount=proj)
        add(taper.part, mode=Mode.SUBTRACT)
    return bp.part


def _gasket_groove() -> Part:
    """Rounded-rect groove in the rim top for the silicone cord."""
    half = c.GASKET_GROOVE_W / 2
    r_mouth = c.CORNER_R - c.WALL
    o_x = c.installable_x() + 2 * (c.GASKET_INSET + half)
    o_y = c.installable_y() + 2 * (c.GASKET_INSET + half)
    i_x = c.installable_x() + 2 * (c.GASKET_INSET - half)
    i_y = c.installable_y() + 2 * (c.GASKET_INSET - half)

    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(c.INTERIOR_Z - c.GASKET_GROOVE_D)):
            RectangleRounded(o_x, o_y, r_mouth + c.GASKET_INSET + half)
            RectangleRounded(
                i_x, i_y, r_mouth + c.GASKET_INSET - half, mode=Mode.SUBTRACT
            )
        extrude(amount=c.GASKET_GROOVE_D + 1)
    return bp.part


def _snap_groove() -> Part:
    """Ring groove in the rim band's inner face; the lid's snap bead clicks in."""
    r_mouth = c.CORNER_R - c.WALL
    z_bot = c.INTERIOR_Z - c.SNAP_BEAD_Z - c.SNAP_GROOVE_H / 2
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(z_bot)):
            # Overshoot into the cavity so the cut opens cleanly.
            RectangleRounded(
                c.installable_x() + 1, c.installable_y() + 1, r_mouth + 0.5
            )
            RectangleRounded(
                c.installable_x() - 2 * c.SNAP_GROOVE_D,
                c.installable_y() - 2 * c.SNAP_GROOVE_D,
                max(r_mouth - c.SNAP_GROOVE_D, 0.5),
                mode=Mode.SUBTRACT,
            )
        extrude(amount=c.SNAP_GROOVE_H)
    return bp.part


def create_tray() -> Part:
    """The tray body, in print pose (floor on the bed, mouth up)."""
    with BuildPart() as bp:
        # --- Outer shell ----------------------------------------------------
        with BuildSketch(Plane.XY.offset(-c.FLOOR)):
            RectangleRounded(c.outer_x(), c.outer_y(), c.CORNER_R)
        extrude(amount=c.FLOOR + c.INTERIOR_Z)

        # --- Hollow it out ---------------------------------------------------
        add(_cavity(), mode=Mode.SUBTRACT)

        # --- Internal features ----------------------------------------------
        add(_shelf_ledge(), mode=Mode.ADD)

        # PSU-plate snap studs (no screws: none could be reached -- see config).
        for x, y in PLATE_BOSS_POS:
            add(_plate_stud(x, y), mode=Mode.ADD)

        # --- Subtractive features -------------------------------------------
        add(_gasket_groove(), mode=Mode.SUBTRACT)
        add(_snap_groove(), mode=Mode.SUBTRACT)

        # --- Edges ------------------------------------------------------------
        # Bottom exterior ring: 45 chamfer, doubling as elephant's-foot relief.
        bottom = bp.faces().sort_by(Axis.Z).first
        _chamfer_edge(bp, bottom.edges(), c.RING_CHAMFER)
        # Outer top edge of the rim. Boolean, not the OCC edge op: the top face
        # also carries the gasket groove, and OCC is flaky on such faces.
        add(
            top_chamfer_tool(
                c.outer_x(), c.outer_y(), c.CORNER_R, c.INTERIOR_Z, c.RING_CHAMFER
            ),
            mode=Mode.SUBTRACT,
        )

    part = bp.part
    part.label = "tray"
    return part


def create_tray_finished() -> Part:
    """The tray with every penetration cut -- the part you actually print."""
    from .penetrations import apply

    return apply(create_tray())


def create() -> Part:
    """Entry point so ``uv run show led_psu_enclosure.tray`` works."""
    return create_tray_finished()


__all__ = ["create", "create_tray", "create_tray_finished"]
