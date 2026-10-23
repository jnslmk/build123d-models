"""Stackable PETG stone cover: roof-down body and glue-on stacking lips."""

from build123d import Compound
from .. import config as c
from ..sets import COVER_TIP_CLEARANCE
from ..stackable_checks import check_cover, check_split_lips

from ..cover import _create_finished_stackable_cover_for, create_stackable_cover_for
from ..sets import STONE

PARAMS = []
IS_ASSEMBLY = False


def create() -> Compound:
    return create_stackable_cover_for(STONE)


def check():
    clean = _create_finished_stackable_cover_for(STONE)
    report = check_cover(
        clean,
        c.SHELL_FOOT_TOP,
        c.GUIDE_FLOOR_Z + STONE.max_len,
        COVER_TIP_CLEARANCE,
    )
    check_split_lips(report, create(), clean)
    return report
