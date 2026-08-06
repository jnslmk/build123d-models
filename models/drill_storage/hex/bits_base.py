"""The rigid base for the BITS box: 2x2 Gridfinity, cavity + guide bores.

Rigid half of the two-material BITS box: a black ASA base on a **2x2**
Gridfinity footprint (83.5 mm pad) with a cavity that holds the TPU cartridge
and sixteen hex guide bores under it. The 25 mm driver bits are a mixed bag
(Torx/PH/PZ/slotted) with no size scale to engrave, so the walls stay blank and
you read the tip itself -- which is exactly what's left standing proud. Shape,
argument and print notes are in ``hex.base``.

Printed foot down, cavity up, in black ASA, no supports.
"""

from __future__ import annotations

from build123d import Part

from . import config as c
from .base import create_base


def create() -> Part:
    """Model entry point: the BITS box's rigid base, in print pose."""
    hex_bores, rows, pos = c.socket_layout("bits")
    base = create_base(
        hex_bores,
        pad=c.BITS_PAD,
        collar_w=c.BITS_COLLAR_W,
        cavity_w=c.BITS_CAVITY_W,
        rows=rows,
        hole_pos=pos,
    )
    base.label = "base_bits"
    base.color = c.BASE_COLOR
    return base


__all__ = ["create"]
