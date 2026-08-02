"""The upper deck carrying the fuse block and the WLED controller.

A separate drop-in part rather than a printed-in floor, for three reasons: a
235 mm horizontal web mid-print would need support, the PSU terminal block and
its +V ADJ trimmer have to stay reachable, and the whole electronics deck can
come out in one piece for wiring on the bench.

It rests on the tray's ledge (front and back walls carry it; the end-wall ledges
are deliberately interrupted by the vent apertures). It is sized to drop through
the **rim opening**, which is narrower than the interior -- see
``config.shelf_size``.

Ventilation slots run across it so the PSU's fan plenum below stays connected to
the high vent port above.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    extrude,
)

from . import config as c
from .util import as_part
from . import mocks

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

FUSE_BOLT_CLEAR = 4.5  # M4 through the fuse block's 5.2 mm ears
CTRL_BOLT_CLEAR = 3.4  # M3 through the controller's 4 mm tabs


def _mount_points() -> list[tuple[float, float, float]]:
    """(x, y, clearance) for every component fixing on the shelf."""
    pts: list[tuple[float, float, float]] = []
    # Fuse block: two ears on its long centre line.
    for sx in (-1, 1):
        pts.append(
            (
                mocks.FUSE_X_CENTER + sx * c.FUSE_BOLT_PITCH / 2,
                mocks.FUSE_Y_CENTER,
                FUSE_BOLT_CLEAR,
            )
        )
    # Controller: two tabs overhanging each end of its long axis.
    for sx in (-1, 1):
        pts.append(
            (
                mocks.CTRL_X_CENTER + sx * c.CTRL_BOLT_PITCH / 2,
                mocks.CTRL_Y_CENTER,
                CTRL_BOLT_CLEAR,
            )
        )
    return pts


def _slot_row(y0: float, y1: float, x_max: float) -> list[tuple[float, float, float]]:
    """(x, y centre, length) for a row of slots filling the band y0..y1."""
    length = y1 - y0
    if length < c.SHELF_VENT_SLOT_W:
        return []
    pitch = c.SHELF_VENT_SLOT_W + c.SHELF_VENT_SLOT_GAP
    n = int((2 * x_max) // pitch)
    return [(-((n - 1) / 2 - i) * pitch, (y0 + y1) / 2, length) for i in range(n)]


def create_shelf() -> Part:
    """The shelf, in print pose (flat on the bed)."""
    sx, sy = c.shelf_size()
    notch_x, notch_y = c.shelf_fan_notch()
    high = c.vent_high_end()

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(sx, sy, 5.0)
        extrude(amount=c.SHELF_T)

        # Ventilation. Two bands, in front of and behind the component
        # footprints -- the old single field ran on under the fuse block and the
        # controller, where a slot vents nothing. With the shelf now only 13 mm
        # above the PSU's top-cover fan, the plenum needs every clear path it
        # can get to the high port.
        front = (-sy / 2 + 4.0, -c.INTERIOR_Y / 2 + c.SHELF_FRONT_KEEPOUT - 2.0)
        back = (mocks.CTRL_Y_CENTER + c.CTRL_Y / 2 + 2.0, sy / 2 - 4.0)
        for y0, y1 in (front, back):
            for x, yc, length in _slot_row(y0, y1, sx / 2 - 15.0):
                with BuildSketch(Plane.XY):
                    with Locations((x, yc)):
                        RectangleRounded(
                            c.SHELF_VENT_SLOT_W,
                            length,
                            min(c.SHELF_VENT_SLOT_W, length) / 2 - 0.4,
                        )
                extrude(amount=c.SHELF_T, mode=Mode.SUBTRACT)

        # The bite the internal fan takes out of the high port's edge. Without it
        # the shelf goes in (the fan is fitted last) but can never come out
        # again, and lifting it out is how the PSU's terminals are reached. It
        # doubles as the plenum's shortest path to the exhaust.
        notch_w = sx / 2 + 2.0 - notch_x
        with BuildSketch(Plane.XY):
            with Locations((high * (notch_x + notch_w / 2), 0)):
                Rectangle(notch_w, 2 * notch_y)
        extrude(amount=c.SHELF_T, mode=Mode.SUBTRACT)

        # Component fixings: plain clearance holes, screw + nut from underneath.
        # Deliberately not heat-set inserts -- a 4 mm deck cannot host one, and a
        # boss to carry it would hold the fuse block off the deck. The shelf lifts
        # out, so its underside is easy to reach.
        for x, y, clear in _mount_points():
            with Locations((x, y, 0)):
                Cylinder(clear / 2, c.SHELF_T, align=MIN_Z, mode=Mode.SUBTRACT)

    part = bp.part
    part.label = "shelf"
    return part


def seated() -> Part:
    """The shelf at its installed height, for the assembled view."""
    part = as_part(Pos(0, 0, c.shelf_ledge_z()) * create_shelf())
    part.label = "shelf"
    return part


def create() -> Part:
    """Entry point for ``uv run show led_psu_enclosure.shelf``."""
    return create_shelf()


__all__ = ["create", "create_shelf", "seated"]
