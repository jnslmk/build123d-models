"""The TPU cartridge for the ALLEN box: eight hex sockets, land at the bottom.

Compliant half of the two-material ALLEN box: a black TPU collar whose eight
hex sockets each grip on a ``HEX_LAND_FIT`` land at their bottom and are
relieved above it, exactly like a drill shank in the family cartridges. Shape,
argument and print notes are in ``hex.insert``.

Printed flat-bottom down, bores up, in black TPU, no supports.
"""

from __future__ import annotations

from build123d import Part

from . import config as c
from .insert import create_insert


def create() -> Part:
    """Model entry point: the ALLEN box's TPU cartridge, in print pose."""
    hex_bores, _rows, _pos = c.socket_layout("allen")
    insert = create_insert(hex_bores, cart_w=c.ALLEN_CART_W)
    insert.label = "insert_allen"
    insert.color = c.INSERT_COLOR
    return insert


__all__ = ["create"]
