"""1×2 Dremel holder scene; export its ASA, TPU and PETG leaves separately."""

from build123d import Compound, Pos, Rotation

from models.drill_storage import config as family
from models.drill_storage.tools import COVER_GLASS
from models.lib.edges import as_part
from . import base, config, cover, insert

IS_ASSEMBLY = True
PARAMS = []


def create() -> Compound:
    """Return the three accepted parts seated in their closed use pose."""
    shell = base.create()
    shell.label = "ASA guide base"
    cartridge = as_part(
        Pos(0, 0, config.CAVITY_FLOOR_Z + family.CART_H)
        * Rotation(180, 0, 0)
        * insert.create()
    )
    cartridge.label = "TPU gripping insert"
    cartridge.color = family.CART_COLOR
    cap = as_part(
        Pos(0, 0, config.SEAT_Z + cover.HEIGHT) * Rotation(180, 0, 0) * cover.create()
    )
    cap.label = "PETG cover"
    cap.color = COVER_GLASS
    return Compound(children=[shell, cartridge, cap], label="Dremel tool holder")
