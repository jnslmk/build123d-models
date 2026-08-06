"""Stone drill storage, assembled: ASA shell, TPU cartridge, tools, cover.

Holds eight carbide-tipped masonry bits, 3 - 12 mm (3, 4, 5, 6, 7, 8, 10, 12).
No hex tool -- a masonry set is drills.

A scene, not a print job -- three filaments never share a bed. The parts are:

    uv run show drill_storage.stone.shell    # ASA, foot down, cavity up
    uv run show drill_storage.stone.insert   # TPU, top down, bores down
    uv run show drill_storage.stone.cover    # PETG, pillow top down

Every bore is cut to its drill's measured shank, which is ground below nominal
-- a reduced-shank masonry set. See ``sets.STONE``'s per-drill ``shank``.

Cover: 137 mm (161 mm / 23U assembled), the tallest of the three, for a 150 mm
12 mm bit.

The set itself -- sizes, lengths, the shank measurements, what the cover says --
is ``sets.STONE``. The geometry is shared with the other two variants and lives
one level up; this package is only the naming.
"""

from __future__ import annotations

from build123d import Compound

from ..assembly import create_assembly
from ..sets import STONE as SET

# A display/verification scene, so no STL/STEP download is offered for it: the
# three printable parts next to it are what you download.
IS_ASSEMBLY = True


def create() -> Compound:
    """The stone holder, fully assembled -- see ``drill_storage.assembly``."""
    return create_assembly(SET)


__all__ = ["IS_ASSEMBLY", "SET", "create"]
