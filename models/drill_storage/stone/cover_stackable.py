"""Stackable PETG stone cover: supported one-piece or separate glue-on lips."""

from build123d import Compound, Part
from .. import config as c
from ..sets import COVER_TIP_CLEARANCE
from ..stackable_checks import check_cover, check_split_lips

from ..cover import (
    SEPARATE_STACKING_LIPS_PARAM,
    SUPPORT_PARAM,
    create_stackable_cover_for,
)
from ..sets import STONE

PARAMS = [SUPPORT_PARAM, SEPARATE_STACKING_LIPS_PARAM]
IS_ASSEMBLY = False


def create(
    support: bool = True, separate_stacking_lips: bool = False
) -> Part | Compound:
    return create_stackable_cover_for(
        STONE, support=support, separate_stacking_lips=separate_stacking_lips
    )


def check():
    report = check_cover(
        create(),
        c.SHELL_FOOT_TOP,
        c.GUIDE_FLOOR_Z + STONE.max_len,
        COVER_TIP_CLEARANCE,
    )
    check_split_lips(report, create(separate_stacking_lips=True), create(support=False))
    return report
