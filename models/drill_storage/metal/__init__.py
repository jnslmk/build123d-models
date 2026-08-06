"""Metal drill storage, assembled: ASA shell, TPU cartridge, tools, cover.

Holds ten HSS twist drills on jobber lengths, 1 - 10 mm (1, 1.5, 2, 2.5, 3, 4, 5, 6,
8, 10), plus an M6 hex-shank tap.

A scene, not a print job -- three filaments never share a bed. The parts are:

    uv run show drill_storage.metal.shell    # ASA, foot down, cavity up
    uv run show drill_storage.metal.insert   # TPU, flat down, bores up
    uv run show drill_storage.metal.cover    # PETG, pillow top down

The 1 and 1.5 mm bores are the smallest in the package and sit at the edge of
what a 0.4 mm nozzle resolves in TPU. See ``sets.METAL``.

Cover: 123 mm (147 mm / 21U assembled) -- the family default, since the 132 mm
twist drill is the longest tool in the package.

The set itself -- sizes, lengths, the shank allowance, what the cover says --
is ``sets.METAL``. The geometry is shared with the other two variants and lives
one level up; this package is only the naming.
"""

from __future__ import annotations

from build123d import Compound

from ..assembly import create_assembly
from ..sets import METAL as SET

# A display/verification scene, so no STL/STEP download is offered for it: the
# three printable parts next to it are what you download.
IS_ASSEMBLY = True


def create() -> Compound:
    """The metal holder, fully assembled -- see ``drill_storage.assembly``."""
    return create_assembly(SET)


__all__ = ["IS_ASSEMBLY", "SET", "create"]
