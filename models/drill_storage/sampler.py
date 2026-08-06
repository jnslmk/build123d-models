"""The whole family in one view: three shells with their cartridges, three covers.

``drill_storage`` itself, so the package is showable without first picking a set.
Not a print job and not an assembly of one thing -- it is the three variants side
by side, in the order they are defined: wood, metal, stone.

The row of covers behind is the point of the layout rather than a filler: they
are the same part in three heights, and standing them next to each other shows
what the set's longest tool costs in Gridfinity units (19U, 23U, 23U -- wood,
metal, stone). The shells
in front all look alike because they are -- only the bore pattern differs, and
each carries its own engraved legend for it.

Each set's own scene, with the tools standing in it, is ``drill_storage.<set>``.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rotation

from . import config as c
from .box import GRID
from .cover import create_cover_for
from .insert import create_insert_for
from .sets import ALL
from .shell import create_shell_for

# A display view: the parts are downloadable from the variants themselves.
IS_ASSEMBLY = True

PITCH = GRID + 10.0  # one Gridfinity cell plus a gap, so they read as three units
ROW_GAP = 34.0  # covers behind, shells in front


def create() -> Compound:
    """Every variant: its shell with the cartridge seated, its cover beside it."""
    children = []
    for i, drill_set in enumerate(ALL):
        x = (i - 1) * PITCH

        shell = create_shell_for(drill_set)
        # Print pose is top-face-down; flip back into the cavity's orientation.
        insert = Rotation(180, 0, 0) * create_insert_for(drill_set)
        insert = Pos(0, 0, c.CAVITY_FLOOR_Z - insert.bounding_box().min.Z) * insert
        insert.label = f"insert_tpu_{drill_set.name}"
        insert.color = c.CART_COLOR
        cover = create_cover_for(drill_set)

        children += [
            Pos(x, -ROW_GAP, 0) * shell,
            Pos(x, -ROW_GAP, 0) * insert,
            Pos(x, ROW_GAP, 0) * cover,
        ]

    return Compound(label="drill_storage", children=children)


__all__ = ["IS_ASSEMBLY", "PITCH", "ROW_GAP", "create"]
