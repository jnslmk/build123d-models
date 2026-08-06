"""The cover for the wood set: Wood engraved up one face.

109 mm (133 mm / 19U assembled, about 3 mm over the longest tip).

Interchangeable with the other sets' covers -- every shell seats one the same way
-- so a taller cover simply leaves more air over shorter tools. See
``drill_storage.cover``.

Printed pillow-top down, mouth up, in PETG, no supports.
"""

from __future__ import annotations

from build123d import Part

from ..cover import create_cover_for
from ..sets import WOOD as SET


def create() -> Part:
    """Model entry point: the labelled cover for the wood set."""
    return create_cover_for(SET)


__all__ = ["SET", "create"]
