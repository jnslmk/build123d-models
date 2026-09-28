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
GUIDE_FLOOR_Z = 8.0  # preserve the original 50 mm Dremel tool reference floor
SHANK_D = 2.5
CUT_D = SHANK_D + family.small_bore_comp(
    SHANK_D
)  # same compensation in guide and TPU bores
PITCH = 7.0
POSITIONS = tuple((x * PITCH, y * PITCH) for x in range(-2, 3) for y in range(-5, 6))

# Future mating parts use these same coordinates and dimensions.
CART_X = family.CART_W
CART_Y = CART_X + GRID
CART_CORNER = family.CART_R
COVER_TOP_Z = 9 * 7.0
