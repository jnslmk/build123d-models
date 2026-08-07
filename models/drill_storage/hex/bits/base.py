"""The rigid base for the BITS box: 1x1 Gridfinity, cavity + guide bores.

Rigid half of the two-material BITS box: a black ASA base on the shared 1x1
Gridfinity footprint (41.5 mm, pad and body alike) with a cavity that holds the TPU cartridge
and sixteen hex guide bores under it. The 25 mm driver bits are a mixed bag
(Torx/PH/PZ/slotted) with no size scale to engrave, so the walls stay blank and
you read the tip itself -- which is exactly what's left standing proud. The
guides are cut at the shaved ``BITS_GUIDE_AF`` (drop-in, not the drill
family's free fit); the argument is in ``hex.config``. Shape, argument and
print notes are in ``hex.base``.

Printed foot down, cavity up, in black ASA, no supports.
"""

from __future__ import annotations

from build123d import Part

from .. import config as c
from ..base import create_base


def create() -> Part:
    """Model entry point: the BITS box's rigid base, in print pose."""
    hex_bores, _rows, _pos = c.socket_layout("bits")
    base = create_base(
        hex_bores,
        guide_af=c.BITS_GUIDE_AF,
        guide_mouth_ch=c.BITS_GUIDE_MOUTH_CH,
    )
    base.label = "base_bits"
    base.color = c.BASE_COLOR
    return base


__all__ = ["create"]
