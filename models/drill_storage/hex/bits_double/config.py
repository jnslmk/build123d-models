"""Accepted 36-bit layout; extend BITS by one 42 mm Gridfinity cell."""

from models.drill_storage.hex import config as hex_config
from models.drill_storage.box import COLLAR_R, INNER_W
from models.lib.gridfinity import BASE_H, CORNER_R, GRID, PAD

LABELS = (
    ("H1.5", "H2", "H2.5", "H3"),
    ("H4", "H5", "H6", "H8"),
    ("T10", "T10", "T15", "T15"),
    ("T20", "T20", "T20", "T27"),
    ("T25", "T25", "T25", "T40"),
    ("T30", "T30", "SL6.5", "SL8"),
    ("SL3", "SL4", "SL5", "SL6"),
    ("PZ1", "PZ2", "PZ2", "PZ3"),
    ("PH1", "PH2", "PH2", "PH3"),
)
BODY_X = PAD
BODY_Y = PAD + GRID
BODY_R = CORNER_R
COLLAR_X = hex_config.COLLAR_W
COLLAR_Y = COLLAR_X + GRID
COLLAR_CORNER = COLLAR_R
CAVITY_X = hex_config.CAVITY_W
CAVITY_Y = CAVITY_X + GRID
CAVITY_CORNER = hex_config.CAVITY_R
CART_X = hex_config.CART_W
CART_Y = CART_X + GRID
PITCH_X = hex_config.BITS_PITCH
PITCH_Y = (
    CART_Y / 2
    - hex_config.HEX_SOCKET_R
    - (hex_config.CART_WALL + hex_config.BITS_CART_MOUTH_CH)
) / 4
# Row 1 is the back (+Y), columns run left to right (+X) viewed from above.
SOCKETS = tuple(
    (label, (col - 1.5) * PITCH_X, (4 - row) * PITCH_Y)
    for row, labels in enumerate(LABELS)
    for col, label in enumerate(labels)
)
BASE_TOP_Z = hex_config.BASE_TOTAL_H
SEAT_Z = hex_config.BASE_FOOT_TOP
CAVITY_FLOOR_Z = hex_config.CAVITY_FLOOR_Z
GUIDE_FLOOR_Z = hex_config.guide_floor_z("bits")
LABEL_SIZE = 4.15
LABEL_DEPTH = 0.8
LABEL_PAIR_OFFSET = 1.85
LABEL_Z = (BASE_H + SEAT_Z) / 2

# Same short-bit cover as BITS, stretched by one cell; all fits are inherited.
COVER_X = hex_config.COVER_W
COVER_Y = COVER_X + GRID
COVER_INNER_X = INNER_W
COVER_INNER_Y = COVER_INNER_X + GRID
COVER_H = hex_config.cover_h_for(hex_config.BITS_BIT_LEN, GUIDE_FLOOR_Z)
