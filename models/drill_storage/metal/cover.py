"""The cover for the metal set: Metal engraved up one face.

116 mm (140 mm / 20U assembled) -- sized by the 132 mm twist drill, the longest
tool in the package, which it clears by exactly COVER_TIP_CLEARANCE.

Interchangeable with the other sets' covers -- every base seats one the same way
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
