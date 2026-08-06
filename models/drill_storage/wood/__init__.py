"""Wood drill storage, assembled: ASA shell, TPU cartridge, tools, cover.

Holds eleven brad-point wood drills, 2 - 10 mm (2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9,
10), plus a 10 mm countersink on a 6.3 mm hex shank.

A scene, not a print job -- three filaments never share a bed. The parts are:

    uv run show drill_storage.wood.shell    # ASA, foot down, cavity up
    uv run show drill_storage.wood.insert   # TPU, flat down, bores up
    uv run show drill_storage.wood.cover    # PETG, pillow top down

The countersink is packed by its 10 mm head and bored as a hex socket, and it
swaps places with the 10 mm drill so it sits at a row edge.

Cover: 109 mm (133 mm / 19U assembled, about 3 mm over the longest tip).

The set itself -- sizes, lengths, the shank allowance, what the cover says --
is ``sets.WOOD``. The geometry is shared with the other two variants and lives
one level up; this package is only the naming.
"""

from __future__ import annotations

from build123d import Compound

from ..assembly import create_assembly
from ..sets import WOOD as SET

# A display/verification scene, so no STL/STEP download is offered for it: the
# three printable parts next to it are what you download.
IS_ASSEMBLY = True


def create() -> Compound:
    """The wood holder, fully assembled -- see ``drill_storage.assembly``."""
    return create_assembly(SET)


__all__ = ["IS_ASSEMBLY", "SET", "create"]
