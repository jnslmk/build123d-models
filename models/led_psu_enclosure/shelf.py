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


def create_shelf() -> Part:
    """The shelf, in print pose (flat on the bed)."""
    sx, sy = c.shelf_size()

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(sx, sy, 5.0)
        extrude(amount=c.SHELF_T)

        # Ventilation slots, kept clear of the component footprints so they are
        # not blocked by the very parts they are meant to cool around.
        pitch = c.SHELF_VENT_SLOT_W + c.SHELF_VENT_SLOT_GAP
        slot_len = 46.0
        y_front = -sy / 2 + 12.0  # ahead of the SHELF_FRONT_KEEPOUT line
        n = int((sx - 30) // pitch)
        for i in range(n):
            x = -((n - 1) / 2 - i) * pitch
            with BuildSketch(Plane.XY):
                with Locations((x, y_front + slot_len / 2 - 6.0)):
                    RectangleRounded(
                        c.SHELF_VENT_SLOT_W, slot_len, c.SHELF_VENT_SLOT_W / 2 - 0.4
                    )
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
