"""The TPU cartridge for the stone set.

Compliant half: an 8 mm collar of plain round bores, each gripping on a 3.5 mm
land at its bottom and relieved above it. This is the part to re-cut when the
tools change. Shape, argument and print notes are in ``drill_storage.insert``;
the set it is cut for is ``sets.STONE``.

Printed top-face down, bores down, in TPU, no supports.
"""

from __future__ import annotations

from build123d import Part

from ..insert import create_insert_for
from ..sets import STONE as SET


def create() -> Part:
    """Model entry point: the TPU cartridge for the stone set."""
    return create_insert_for(SET)


__all__ = ["SET", "create"]
