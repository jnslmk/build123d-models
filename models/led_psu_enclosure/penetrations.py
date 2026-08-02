"""Everything that deliberately breaks through the shell.

Kept apart from ``tray.py`` because these are the features that decide whether
the box actually seals, and each one carries a spec constraint worth reading:

* **SP1712 (x4)** -- the cutout is Ø17 with a 15.6 mm flat. The flat is oriented
  **up**: in a horizontal hole the top is where an arc would droop, and a chord
  there turns it into a ~9.3 mm flat bridge that prints cleanly. The connector
  also refuses to mount through more than 3 mm of panel, so a counterbore on the
  inside takes the local wall down to ``SP17_PANEL_T`` and gives the rear nut a
  flat seat.
* **Vent ports** -- one low at the cool end, one high over the PSU's top-cover
  fan, so a fitted pair gives real cross-flow rather than one hole. Each gets an
  inner reinforcing frame (the 3.5 mm wall is far too thin to host an M3 insert)
  and an outer recess for the cartridge flange and its gasket. The high port also
  gets four blind pilots for the internal fan's yoke, driven into the frame's
  side bands from the *inside* -- the shutter's own pilots come at the same slab
  from the outside, and only the offset in Z keeps the two sets from meeting.
* **Shelf-ledge relief** -- the ledge is built as a ring on all four walls, but
  its end-wall runs sit exactly where the vent frames, the fan and the yoke's
  rails live, so they are cut back to the frame's inner face.

Bore mouths get **boolean** chamfers -- a subtracted ``Cone`` frustum -- rather
than OCC edge ops, which are flaky on a rim beside other holes.

Both wall planes were probed rather than assumed:
``Plane.XZ`` has normal (0,-1,0), so ``offset(d)`` sits at ``y = -d`` and extrude
runs toward **-Y**; ``Plane.YZ`` has normal (1,0,0), so ``offset(d)`` sits at
``x = +d`` and extrude runs toward **+X**. The two span helpers below encode
that so no call site has to think about it.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Rotation,
    add,
    extrude,
)

from . import config as c
from .util import as_part

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

FRONT_INNER_Y = -c.INTERIOR_Y / 2
FRONT_OUTER_Y = FRONT_INNER_Y - c.WALL

# How far a cutting tool overshoots a face, so a boolean never leaves a sliver.
OVERSHOOT = 4.0


def _y_span(start: float, end: float) -> tuple[float, float]:
    """``(Plane.XZ offset, extrude amount)`` for a tool spanning Y from start to end.

    Plane.XZ extrudes toward -Y, so ``start`` must be the larger (rear-most) Y.
    """
    hi, lo = max(start, end), min(start, end)
    return -hi, hi - lo


def _x_span(start: float, end: float) -> tuple[float, float]:
    """``(Plane.YZ offset, extrude amount)`` for a tool spanning X from start to end.

    Plane.YZ extrudes toward +X, so the tool always starts at the lower X --
    which is what makes one function work for both end walls.
    """
    return min(start, end), abs(end - start)


# --- Front wall: connectors, gland, RJ45 -------------------------------------

# Front-wall through-tools all run from inside the cavity to outside the wall.
_FRONT_TOOL = _y_span(FRONT_INNER_Y + OVERSHOOT, FRONT_OUTER_Y - OVERSHOOT)


def _sp17_cutout(x: float, z: float) -> Part:
    """One D-shaped panel cutout: Ø17 with the anti-rotation flat at the top."""
    off, amt = _FRONT_TOOL
    flat_offset = c.SP17_CUTOUT_FLAT - c.SP17_CUTOUT_D / 2  # centre out to the flat
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ.offset(off)):
            with Locations((x, z)):
                Circle(c.SP17_CUTOUT_D / 2)
            # On Plane.XZ sketch +Y is box +Z, so this trims the *top* of the bore.
            with Locations((x, z + flat_offset + c.SP17_CUTOUT_D / 2)):
                Rectangle(c.SP17_CUTOUT_D * 2, c.SP17_CUTOUT_D, mode=Mode.SUBTRACT)
        extrude(amount=amt)
    return bp.part


def _round_hole(dia: float, x: float, z: float) -> Part:
    """A plain through-hole in the front wall."""
    off, amt = _FRONT_TOOL
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ.offset(off)):
            with Locations((x, z)):
                Circle(dia / 2)
        extrude(amount=amt)
    return bp.part


def _sp17_counterbore(x: float, z: float) -> Part:
    """Inside pocket taking the local panel down to the 3 mm spec limit.

    Depth is measured off the *inner* face and is only ``WALL - SP17_PANEL_T``;
    the overshoot runs into the cavity, never further into the wall. Getting this
    backwards would quietly remove the whole wall.
    """
    cut = c.WALL - c.SP17_PANEL_T
    off, amt = _y_span(FRONT_INNER_Y + OVERSHOOT, FRONT_INNER_Y - cut)
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ.offset(off)):
            with Locations((x, z)):
                Circle(c.SP17_COUNTERBORE_D / 2)
        extrude(amount=amt)
    return bp.part


def _front_lead_in(dia: float, x: float, z: float) -> Part:
    """Boolean chamfer at a front-wall bore mouth, cut into the outer face."""
    with BuildPart() as bp:
        Cone(dia / 2 + c.LEAD_IN, dia / 2, c.LEAD_IN, align=MIN_Z)
    # Rotation(-90,0,0) maps +Z to +Y, so the wide end lands on the outer face.
    return as_part(Pos(x, FRONT_OUTER_Y, z) * Rotation(-90, 0, 0) * bp.part)


# --- End walls: vent ports ----------------------------------------------------


def vent_ports() -> list[tuple[float, int]]:
    """(z, end_sign) for the two ports: low intake, high exhaust over the fan."""
    high = c.vent_high_end()
    return [(c.VENT_LOW_Z, -high), (c.VENT_HIGH_Z, high)]


def vent_screw_positions(z: float) -> list[tuple[float, float]]:
    """(y, z) of the two M3 screws that compress a cartridge's gasket."""
    y = c.VENT_W / 2 + c.VENT_SCREW_OFFSET
    return [(-y, z), (y, z)]


def _vent_frame(z: float, s: int) -> Part:
    """Inner reinforcing frame around a vent aperture.

    The 3.5 mm wall cannot host an M3 heat-set insert, so the wall is thickened
    inward here. Thickness is capped by the PSU, which passes within 6.5 mm of
    the end walls -- hence ``VENT_FRAME_T`` at 5 mm, not more.
    """
    inner = s * (c.INTERIOR_X / 2)
    off, amt = _x_span(inner, inner - s * c.VENT_FRAME_T)
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(off)):
            with Locations((0, z)):
                RectangleRounded(
                    c.VENT_W + 2 * c.VENT_FRAME_MARGIN_Y,
                    c.VENT_H + 2 * c.VENT_FRAME_MARGIN_Z,
                    6.0,
                )
                RectangleRounded(c.VENT_W, c.VENT_H, 4.0, mode=Mode.SUBTRACT)
        extrude(amount=amt)
    return bp.part


def _vent_aperture(z: float, s: int) -> Part:
    """The rectangular opening itself, straight through wall and frame."""
    inner = s * (c.INTERIOR_X / 2)
    outer = s * (c.INTERIOR_X / 2 + c.WALL)
    off, amt = _x_span(inner - s * (OVERSHOOT + c.VENT_FRAME_T), outer + s * OVERSHOOT)
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(off)):
            with Locations((0, z)):
                RectangleRounded(c.VENT_W, c.VENT_H, 4.0)
        extrude(amount=amt)
    return bp.part


def _vent_ledge_relief(s: int) -> Part:
    """Clears the shelf ledge off an end wall, across the port's full width.

    The ledge is built as a ring on all four walls, but the end-wall runs are in
    the way: the vent frame, the internal fan and its yoke's rails all live in
    that band. Cutting them out is what makes the shelf carried front-to-back --
    which the ledge docstring already claimed and the geometry did not do.
    """
    # Stops at the frame's inner face, not the wall's: past that the ledge and
    # the vent frame are the same material, and cutting to the wall would take
    # the frame -- and the yoke's screw pilots -- with it.
    inner = s * (c.INTERIOR_X / 2)
    off, amt = _x_span(inner - s * (c.SHELF_LEDGE_W + 1.0), s * c.vent_frame_inner_x())
    half_y = c.VENT_W / 2 + c.VENT_FRAME_MARGIN_Y
    top = c.shelf_ledge_z() + 1.0
    bot = c.shelf_ledge_z() - c.SHELF_LEDGE_W - 1.0
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(off)):
            with Locations((0, (top + bot) / 2)):
                Rectangle(2 * half_y, top - bot)
        extrude(amount=amt)
    return bp.part


def _vent_yoke_pilots(z: float, s: int) -> Part:
    """Blind self-tapping pilots for the internal fan's yoke, entered inside.

    Same 5.5 mm of material the shutter's screws bite into, approached from the
    other face and offset in Z so the two sets never meet. They sit in the
    frame's side bands rather than above and below the aperture -- see
    ``VENT_YOKE_SCREW_DZ`` for why that decides the height of the whole box.
    """
    inner = s * c.vent_frame_inner_x()
    off, amt = _x_span(inner, inner + s * c.VENT_SCREW_PILOT_L)
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(off)):
            for y in (-c.vent_yoke_screw_y(), c.vent_yoke_screw_y()):
                for dz in (-c.VENT_YOKE_SCREW_DZ, c.VENT_YOKE_SCREW_DZ):
                    with Locations((y, z + dz)):
                        Circle(c.VENT_SCREW_PILOT_D / 2)
        extrude(amount=amt)
    return bp.part


def _vent_recess(z: float, s: int) -> Part:
    """Shallow pocket on the outer face seating the cartridge flange + gasket."""
    outer = s * (c.INTERIOR_X / 2 + c.WALL)
    off, amt = _x_span(outer - s * c.VENT_RECESS_D, outer + s * OVERSHOOT)
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(off)):
            with Locations((0, z)):
                RectangleRounded(
                    c.VENT_W + 2 * c.VENT_RECESS_MARGIN_Y,
                    c.VENT_H + 2 * c.VENT_RECESS_MARGIN_Z,
                    6.0,
                )
        extrude(amount=amt)
    return bp.part


def _vent_screw_pockets(z: float, s: int) -> Part:
    """Blind self-tapping pilots for the cartridge screws.

    Entered from the **recess floor**, not the outer face -- the recess has
    already removed VENT_RECESS_D of wall, and starting at the outer face would
    leave barely 2 mm of thread.
    """
    floor = s * (c.INTERIOR_X / 2 + c.WALL - c.VENT_RECESS_D)
    off, amt = _x_span(floor, floor - s * c.VENT_SCREW_PILOT_L)
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(off)):
            for y, zz in vent_screw_positions(z):
                with Locations((y, zz)):
                    Circle(c.VENT_SCREW_PILOT_D / 2)
        extrude(amount=amt)
    return bp.part


# --- Assembly of all of the above --------------------------------------------


def apply(tray: Part) -> Part:
    """Cut every penetration into a finished tray body."""
    ports = vent_ports()

    with BuildPart() as bp:
        add(tray)

        # Additive first, so the later cuts pass through the new material too.
        for z, s in ports:
            add(_vent_frame(z, s), mode=Mode.ADD)

        # Four SP1712 output connectors.
        for x in c.sp17_positions():
            add(_sp17_cutout(x, c.SP17_Z), mode=Mode.SUBTRACT)
            add(_sp17_counterbore(x, c.SP17_Z), mode=Mode.SUBTRACT)
            add(_front_lead_in(c.SP17_CUTOUT_D, x, c.SP17_Z), mode=Mode.SUBTRACT)

        # Mains gland and RJ45 bulkhead, beside the connector row.
        for dia, x, z in (
            (c.GLAND_HOLE_D, c.GLAND_X, c.GLAND_Z),
            (c.RJ45_HOLE_D, c.RJ45_X, c.RJ45_Z),
        ):
            add(_round_hole(dia, x, z), mode=Mode.SUBTRACT)
            add(_front_lead_in(dia, x, z), mode=Mode.SUBTRACT)

        # Vent ports.
        high_end = c.vent_high_end()
        for z, s in ports:
            add(_vent_aperture(z, s), mode=Mode.SUBTRACT)
            add(_vent_recess(z, s), mode=Mode.SUBTRACT)
            add(_vent_screw_pockets(z, s), mode=Mode.SUBTRACT)
            add(_vent_ledge_relief(s), mode=Mode.SUBTRACT)
            # Only the high port can host the internal fan: at the low port the
            # PSU passes within 6.5 mm of the wall and the frame spends 5.
            if s == high_end:
                add(_vent_yoke_pilots(z, s), mode=Mode.SUBTRACT)

    part = bp.part
    part.label = "tray"
    return part
