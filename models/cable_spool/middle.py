"""The divider between the two cable channels.

    uv run show cable_spool.middle
    uv run export cable_spool.middle     # the STL to print
    uv run check cable_spool

The same six-window disc as the other two, and everything interesting about it
is in the bore:

* **Four relief pockets** on the hub's rib centres, so the disc drops straight
  past the ribs instead of landing on them. They are the only reason it can
  reach `MIDDLE_Z` at all, and the only reason the cover -- which has none --
  stops seven millimetres higher.
* **Two keys**, diametrically opposite, that reach into the hub's slots. The
  cable's end is anchored through one of those slots, so a disc free to rotate
  is a disc that saws at the anchor every time the spool is wound.

Print flat, chamfered face up, no supports. It is 2 mm of plate and it is the
quickest of the three to print.
"""

from __future__ import annotations

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Rotation,
    Sketch,
    add,
    extrude,
)

from . import config as cfg
from .plate import bore_mouth_chamfers, plate_body, sector


def bore_sketch() -> Sketch:
    """The middle disc's bore: a sliding fit on the hub, plus relief and keys."""
    relief = sector(
        cfg.MIDDLE_BORE_R - 0.5, cfg.MIDDLE_RELIEF_R, cfg.MIDDLE_RELIEF_ARC
    )
    key = sector(cfg.MIDDLE_KEY_R, cfg.MIDDLE_BORE_R + 0.5, cfg.MIDDLE_KEY_ARC)
    step = 360.0 / cfg.HUB_RIB_COUNT
    with BuildSketch() as sk:
        Circle(cfg.MIDDLE_BORE_R)
        with Locations(
            *[
                Rotation(0.0, 0.0, cfg.HUB_RIB_PHASE + i * step)
                for i in range(cfg.HUB_RIB_COUNT)
            ]
        ):
            add(relief)
        with Locations(
            Rotation(0.0, 0.0, cfg.CABLE_SLOT_PHASE),
            Rotation(0.0, 0.0, cfg.KEY_SLOT_PHASE),
        ):
            add(key, mode=Mode.SUBTRACT)
    return sk.sketch


def create() -> Part:
    """The middle disc, in print pose on `z = 0`."""
    bore = bore_sketch()
    lower, upper = bore_mouth_chamfers(bore)
    with BuildPart() as part:
        add(plate_body(cfg.MIDDLE_RIM_CHAMFER_W))
        with BuildSketch():
            add(bore)
        extrude(amount=cfg.PLATE_T, mode=Mode.SUBTRACT)
        add(lower, mode=Mode.SUBTRACT)
        add(upper, mode=Mode.SUBTRACT)
    return part.part
