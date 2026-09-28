"""The third printed part: the labelled cover, one per set.

Thin on purpose -- ``box.create_cover`` does the work, and this only decides what
a set's cover says and how tall it is. Both come off the ``DrillSet``:
``cover_h`` is solved from the longest tool in the set, so a cover is exactly the
smallest whole Gridfinity Z unit that swallows it.

The covers are **interchangeable between sets**, and deliberately: every base
keeps ``SHELL_FOOT_TOP`` and ``GUIDE_FLOOR_Z`` where ``box`` has them, so a taller
cover fits a shorter set's base and simply leaves more air over the tips. Only
the engraved word and the height differ, which is why the stone cover (137 mm)
will happily close over the wood base and the wood one (109 mm) will not close
over a 132 mm twist drill.

Printed pillow-top down, mouth up, in PETG -- ``create_cover`` already returns it
in that pose. The set's own material is engraved up one flat face.
"""

from __future__ import annotations

from build123d import Part

from .box import (
    BASE_H,
    CAP_H,
    COVER_COLOR,
    STACK_SOCKET_DEPTH,
    cover_height_for,
    create_cover,
)
from . import config as c
from .sets import COVER_TIP_CLEARANCE, DrillSet

SUPPORT_PARAM = {
    "name": "support",
    "label": "Include breakaway socket supports",
    "type": "boolean",
    "default": True,
}


def create_cover_for(drill_set: DrillSet) -> Part:
    """The cover for one ``sets.DrillSet``, labelled and coloured."""
    cover = create_cover(drill_set.label, cover_h=drill_set.cover_h)
    cover.label = f"cover_{drill_set.name}"
    cover.color = COVER_COLOR
    return cover


def create_stackable_cover_for(drill_set: DrillSet, support: bool = True) -> Part:
    """The same collar fit, with an optionally supported Gridfinity-foot seat."""
    cover_h = cover_height_for(
        drill_set.max_len,
        headroom=COVER_TIP_CLEARANCE,
        bore_floor_z=c.GUIDE_FLOOR_Z,
        foot_top=c.SHELL_FOOT_TOP,
        cap_h=CAP_H + STACK_SOCKET_DEPTH,
        stack_lip_h=BASE_H,
    )
    cover = create_cover(
        drill_set.label, cover_h=cover_h, stackable=True, support=support
    )
    cover.label = f"cover_stackable_{drill_set.name}"
    cover.color = COVER_COLOR
    return cover


__all__ = ["create_cover_for", "create_stackable_cover_for"]
