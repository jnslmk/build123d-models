"""ALLEN key storage, assembled: the 1x1 box with eight hex keys and cover.

Gridfinity storage for an eight-piece set of 50 mm hex keys (1.5 / 2 / 2.5 /
3 / 4 / 5 / 6 / 8 mm), and one of the five top-level drill_storage sets, cut
exactly like the others: a rigid black ASA base that guides each key upright,
a black TPU insert that grips it on a short land, and a translucent PETG cover
that snaps over the collar. The sizes are engraved into the base's body walls,
largest -> smallest, so the set reads as an ordered grid.

A scene, not a print job -- three materials (black ASA base, black TPU insert,
translucent PETG cover) never share a bed. The parts are:

    uv run show drill_storage.allen            # the box, all eight keys standing
    uv run show drill_storage.allen.base       # rigid, foot down, cavity up
    uv run show drill_storage.allen.insert     # TPU, flat down, bores up
    uv run show drill_storage.allen.cover      # translucent, pillow top down

The 50 mm keys sink 21 mm into the base and stand 29 mm proud of its rim; the
45 mm cover (63 mm / 9U assembled) clears the longest key by about 3 mm. The
hole used to be 15 mm deep, which stood the keys 35 mm proud and cost a whole
Gridfinity unit more cover to enclose them.

The geometry is ``drill_storage.hex``'s -- the ALLEN box and the BITS driver-bit
box are cut from the same base / insert / cover modules, and this package only
names the ALLEN one. The set it is cut for, and the argument, live in
``hex.config`` and the family's ``drill_storage.config`` / design notes.
"""

from __future__ import annotations

from build123d import Compound

from ..hex import config as c
from ..hex import create_box_scene

# A display/verification scene, so no STL/STEP download is offered for it: the
# three printable parts next to it are what you download.
IS_ASSEMBLY = True


def create() -> Compound:
    """The ALLEN key box, fully assembled: base, cartridge, keys, cover."""
    return Compound(
        label="drill_storage.allen",
        children=create_box_scene("allen", c.ALLEN_BIT_LEN, "ALLEN", True),
    )


__all__ = ["IS_ASSEMBLY", "create"]
