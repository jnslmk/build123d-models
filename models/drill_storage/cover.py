"""The third printed part: the labelled cover, one per set.

Thin on purpose -- ``box.create_cover`` does the work, and this only decides what
a set's cover says and how tall it is. Both come off the ``DrillSet``:
``cover_h`` is solved from the longest tool in the set, so a cover is exactly the
smallest whole Gridfinity Z unit that swallows it.

The covers are **interchangeable between sets**, and deliberately: every shell
keeps ``SHELL_FOOT_TOP`` and ``GUIDE_FLOOR_Z`` where ``box`` has them, so a taller
cover fits a shorter set's shell and simply leaves more air over the tips. Only
the engraved word and the height differ, which is why the stone cover (137 mm)
will happily close over the wood shell and the wood one (109 mm) will not close
over a 150 mm twist drill.

Printed pillow-top down, mouth up, in PETG -- ``create_cover`` already returns it
in that pose. The set's own material is engraved up one flat face.
"""

from __future__ import annotations

from build123d import Part

from .box import COVER_COLOR, create_cover
from .sets import DrillSet


def create_cover_for(drill_set: DrillSet) -> Part:
    """The cover for one ``sets.DrillSet``, labelled and coloured."""
    cover = create_cover(drill_set.label, cover_h=drill_set.cover_h)
    cover.label = f"cover_{drill_set.name}"
    cover.color = COVER_COLOR
    return cover


__all__ = ["create_cover_for"]
