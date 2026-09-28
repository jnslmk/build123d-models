"""Stackable PETG cover for the wood set, with integral removable print support."""

from build123d import Part
from .. import config as c

from ..sets import COVER_TIP_CLEARANCE
from ..stackable_checks import check_cover
from ..cover import create_stackable_cover_for
from ..sets import WOOD


def create() -> Part:
    return create_stackable_cover_for(WOOD)


def check():
    return check_cover(
        create(),
        c.SHELL_FOOT_TOP,
        c.GUIDE_FLOOR_Z + WOOD.max_len,
        COVER_TIP_CLEARANCE,
    )
