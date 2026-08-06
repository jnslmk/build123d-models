"""The rigid base for the ALLEN box: 1x1 Gridfinity, cavity + guide bores.

Rigid half of the two-material ALLEN box: a black ASA base with a cavity that
holds the TPU cartridge and eight hex guide bores under it, plus the size
legend (1.5 / 2 / 2.5 / 3 / 4 / 5 / 6 / 8, largest first) engraved into the
body walls. Shape, argument and print notes are in ``hex.base``.

Printed foot down, cavity up, in black ASA, no supports.
"""

from __future__ import annotations

from build123d import Part

from . import config as c
from .base import create_base


def create() -> Part:
    """Model entry point: the ALLEN box's rigid base, in print pose."""
    hex_bores, rows, pos = c.socket_layout("allen")
    base = create_base(
        hex_bores,
        guide_af=c.HEX_AF + c.GUIDE_FIT,
        guide_mouth_ch=c.GUIDE_MOUTH_CH,
        rows=rows,
        hole_pos=pos,
    )
    base.label = "base_allen"
    base.color = c.BASE_COLOR
    return base


__all__ = ["create"]
