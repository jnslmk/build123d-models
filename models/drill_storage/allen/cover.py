"""The cover for the ALLEN box: "ALLEN" engraved up one face.

45 mm (63 mm / 9U assembled, about 3 mm over the longest key tip). The
50 mm hex keys sit 21 mm into the base and stand 29 mm proud of its rim.

Printed pillow-top down, mouth up, in translucent PETG, no supports.
"""

from __future__ import annotations

from build123d import Part

from ..hex import config as c
from ..hex.cover import create_cover, label_fit


def create() -> Part:
    """Model entry point: the ALLEN box's cover, in print pose."""
    cover_h = c.cover_h_for(c.ALLEN_BIT_LEN, c.guide_floor_z("allen"))
    size, label_z, horizontal = label_fit(cover_h, "ALLEN")
    cover = create_cover(
        "ALLEN",
        cover_h=cover_h,
        label_size=size,
        label_z=label_z,
        label_horizontal=horizontal,
    )
    cover.label = "cover_allen"
    cover.color = c.COVER_COLOR
    return cover


__all__ = ["create"]
