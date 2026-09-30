"""Dremel variant: the drill family's square interface extended by one cell."""

from models.drill_storage import config as family
from models.drill_storage.box import (
    COLLAR_R,
    COLLAR_W,
    COVER_W,
    FOOT_TOP,
    GRID,
    INNER_W,
    PAD,
    SLIP,
)

BODY_X = PAD
BODY_Y = GRID + PAD
COLLAR_X = COLLAR_W
COLLAR_Y = COLLAR_W + GRID
COLLAR_CORNER = COLLAR_R
CAVITY_X = family.CAVITY_W
CAVITY_Y = CAVITY_X + GRID
CAVITY_CORNER = family.CAVITY_R
COVER_X = COVER_W
COVER_Y = COVER_W + GRID
COVER_INNER_X = INNER_W
COVER_INNER_Y = INNER_W + GRID
COVER_FIT = SLIP  # 0.4 mm diametral, family PETG cover-to-ASA collar slip
SEAT_Z = FOOT_TOP
BASE_TOP_Z = family.SHELL_TOTAL_H
CAVITY_FLOOR_Z = family.CAVITY_FLOOR_Z
GUIDE_FLOOR_Z = 3.0  # 50 mm tools reach z=53, below the 8U cover's z=54 ceiling
# Inventory plus 14 spares: +4 at 2.35, +4 at 2.9 and +6 at 3.1 mm.
SHANK_COUNTS = ((1.0, 1), (1.5, 1), (2.0, 1), (2.35, 10), (2.9, 25), (3.1, 17))
# Contiguous diameter groups run along Y, then advance to the next X column.
BORES = tuple(
    (x, y, diameter)
    for (x, y), diameter in zip(
        tuple(
            (x, y)
            for x in (-15.0, -9.0, -3.0, 3.0, 9.0, 15.0)
            for y in (-35.0, -28.0, -21.0, -14.0, -7.0, 7.0, 14.0, 21.0, 28.0, 35.0)
        )[:55],
        (diameter for diameter, count in SHANK_COUNTS for _ in range(count)),
        strict=True,
    )
)
# Apply the family's calibrated small-bore compensation before either fit.
CUT_BORES = tuple(
    (x, y, diameter + family.small_bore_comp(diameter)) for x, y, diameter in BORES
)

# Future mating parts use these same coordinates and dimensions.
CART_X = family.CART_W
CART_Y = CART_X + GRID
CART_CORNER = family.CART_R
