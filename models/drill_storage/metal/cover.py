"""The cover for the metal set: Metal engraved up one face.

137 mm (161 mm / 23U assembled) -- tied with the stone set, since the 150 mm
twist drill is the longest tool in the package.

Interchangeable with the other sets' covers -- every shell seats one the same way
-- so a taller cover simply leaves more air over shorter tools. See
``drill_storage.cover``.

Printed pillow-top down, mouth up, in PETG, no supports.
"""

from __future__ import annotations

from build123d import Part

from ..cover import create_cover_for
from ..sets import METAL as SET


def create() -> Part:
    """Model entry point: the labelled cover for the metal set."""
    return create_cover_for(SET)


__all__ = ["SET", "create"]
