"""Accepted labelled 1×2 BITS holder, assembled for display, not printing.

The three printable leaves keep their accepted geometry and print poses. Like
the original BITS scene, tools are representative 25 mm ¼-inch hex shanks,
not manufacturer-specific working tips. Socket labels identify their positions.
"""

from build123d import Compound, Pos, Rotation

from models.drill_storage.hex import config as h
from models.drill_storage.tools import STEEL, create_hex_tool
from models.lib.edges import as_part

from . import base, config as c, cover, insert

IS_ASSEMBLY = True
PARAMS = []


def create() -> Compound:
    """Return the accepted parts and all 36 short bits in their closed use pose."""
    shell = base.create()
    shell.label = "ASA labelled guide base"
    cartridge = as_part(Pos(0, 0, c.CAVITY_FLOOR_Z) * insert.create())
    cartridge.label = "TPU gripping insert"
    cap = as_part(
        Pos(0, 0, c.SEAT_Z + c.COVER_H) * Rotation(180, 0, 0) * cover.create()
    )
    cap.label = "PETG long-side-labelled cover"

    # All shanks share one geometry; placement and the assigned label differ.
    shank = create_hex_tool(h.HEX_SHANK_AF, h.BITS_BIT_LEN)
    shank.color = STEEL
    tools = []
    for index, (label, x, y) in enumerate(c.SOCKETS, 1):
        bit = as_part(Pos(x, y, c.GUIDE_FLOOR_Z) * shank)
        bit.label = f"{label} bit ({index})"
        tools.append(bit)

    return Compound(
        label="drill_storage.hex.bits_double",
        children=[shell, cartridge, *tools, cap],
    )
