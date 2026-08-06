"""The cover for the ALLEN box: "ALLEN" engraved up one face.

52 mm (70 mm / 10U assembled, about 2 mm over the longest key tip). The
50 mm hex keys stand 35 mm proud of the base rim.

Printed pillow-top down, mouth up, in translucent PETG, no supports.
"""

from __future__ import annotations

from build123d import Part

from . import config as c
from .cover import create_cover, label_fit


def create() -> Part:
    """Model entry point: the ALLEN box's cover, in print pose."""
    cover_h = c.cover_h_for(c.ALLEN_BIT_LEN)
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
