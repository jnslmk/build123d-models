"""The cover for the stone set: Stone engraved up one face.

137 mm (161 mm / 23U assembled), tied with the metal set as the tallest of the
three, for a 150 mm 10 mm bit.

Interchangeable with the other sets' covers -- every shell seats one the same way
-- so a taller cover simply leaves more air over shorter tools. See
``drill_storage.cover``.

Printed pillow-top down, mouth up, in PETG, no supports.
"""

from __future__ import annotations

from build123d import Part

from ..cover import create_cover_for
from ..sets import STONE as SET


def create() -> Part:
    """Model entry point: the labelled cover for the stone set."""
    return create_cover_for(SET)


__all__ = ["SET", "create"]
