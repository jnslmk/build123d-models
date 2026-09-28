"""Stackable PETG cover for the metal set, with integral removable print support."""

from build123d import Part
from .. import config as c
from ..sets import COVER_TIP_CLEARANCE
from ..stackable_checks import check_cover

from ..cover import create_stackable_cover_for
from ..sets import METAL


def create() -> Part:
    return create_stackable_cover_for(METAL)


def check():
    return check_cover(
        create(),
        c.SHELL_FOOT_TOP,
        c.GUIDE_FLOOR_Z + METAL.max_len,
        COVER_TIP_CLEARANCE,
    )
