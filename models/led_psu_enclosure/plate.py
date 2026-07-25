"""PSU mounting plate -- the reason no screw pierces the sealed shell.

Bolting the RSP-320 straight through the enclosure floor would put four leak
paths in the bottom of a box that is supposed to be waterproof. Instead the PSU
bolts to this plate, and the plate drops onto four blind bosses in the floor.
Same trick as the mounting plate in a commercial IP enclosure.

Two constraints the geometry has to respect:

* **The PSU's bottom M4 holes accept only 3 mm of screw.** The plate is
  counterbored so an M4x8 lands with exactly ``PSU_BOLT_MAX_DEPTH`` protruding.
* **The plate has to fit through the rim opening**, which is narrower than the
  interior -- hence the small ``PSU_PLATE_MARGIN``. See ``config.psu_plate_size``.

Also carries a cutout under the PSU's top-cover fan intake path and lightening
slots, so the plate does not seal the floor off from the low vent port.
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
    RectangleRounded,
    extrude,
)

from . import config as c
from .util import as_part
from .tray import PLATE_BOSS_POS

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

BOLT_CLEAR = 4.5  # M4 clearance for the PSU bolts
BOSS_CLEAR = 3.4  # M3 clearance where the plate screws to the floor bosses
AIR_SLOT_W = 12.0
AIR_SLOT_GAP = 14.0


def create_psu_plate() -> Part:
    """The plate, in print pose (flat on the bed)."""
    px, py = c.psu_plate_size()

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(px, py, 6.0)
        extrude(amount=c.PSU_PLATE_T)

        # PSU bolt holes, counterbored so an M4x8 cannot bottom out in the PSU.
        # Head recess depth = screw length - plate left under the head - 3 mm max.
        head_depth = max(c.PSU_PLATE_T - c.PSU_BOLT_MAX_DEPTH, 1.5)
        for x, y in c.psu_bolts():
            with Locations((x, y, 0)):
                Cylinder(BOLT_CLEAR / 2, c.PSU_PLATE_T, align=MIN_Z, mode=Mode.SUBTRACT)
                Cylinder(8.4 / 2, head_depth, align=MIN_Z, mode=Mode.SUBTRACT)

        # Clearance holes where the plate screws down to the floor bosses.
        for x, y in PLATE_BOSS_POS:
            with Locations((x, y, 0)):
                Cylinder(BOSS_CLEAR / 2, c.PSU_PLATE_T, align=MIN_Z, mode=Mode.SUBTRACT)
                Cylinder(6.4 / 2, 2.0, align=MIN_Z, mode=Mode.SUBTRACT)

        # Air slots: keep the floor connected to the low vent port instead of
        # turning the plate into a second floor.
        n = int((py - 40) // (AIR_SLOT_W + AIR_SLOT_GAP))
        for i in range(n):
            y = -((n - 1) / 2 - i) * (AIR_SLOT_W + AIR_SLOT_GAP)
            for sx in (-1, 1):
                with BuildSketch(Plane.XY):
                    with Locations((sx * (px / 2 - 26.0), y)):
                        RectangleRounded(30.0, AIR_SLOT_W, AIR_SLOT_W / 2 - 0.5)
                extrude(amount=c.PSU_PLATE_T, mode=Mode.SUBTRACT)

    part = bp.part
    part.label = "psu_plate"
    return part


def seated() -> Part:
    """The plate at its installed height, for the assembled view."""
    from build123d import Pos

    part = as_part(Pos(0, 0, c.PSU_PLATE_BOSS_H) * create_psu_plate())
    part.label = "psu_plate"
    return part


def create() -> Part:
    """Entry point for ``uv run show led_psu_enclosure.plate``."""
    return create_psu_plate()


__all__ = ["create", "create_psu_plate", "seated"]
