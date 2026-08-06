"""The TPU cartridge for the BITS box: sixteen hex sockets in a literal 4x4 grid.

Compliant half of the two-material BITS box: a black TPU collar, 78.18 mm wide
for the 2x2 footprint, whose sixteen identical 1/4" sockets sit in a **literal
4x4 square grid** -- never pack_rows, which would deal sixteen identical items
as ragged rows. Each socket grips on a ``HEX_LAND_FIT`` land at its bottom,
exactly like the drill sets' cartridges. Shape, argument and print notes are in
``hex.insert``.

Printed flat-bottom down, bores up, in black TPU, no supports.
"""

from __future__ import annotations

from build123d import Part

from . import config as c
from .insert import create_insert


def create() -> Part:
    """Model entry point: the BITS box's TPU cartridge, in print pose."""
    hex_bores, _rows, _pos = c.socket_layout("bits")
    insert = create_insert(hex_bores, cart_w=c.BITS_CART_W)
    insert.label = "insert_bits"
    insert.color = c.INSERT_COLOR
    return insert


__all__ = ["create"]
