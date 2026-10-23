"""Stackable ALLEN cover: roof-down body and glue-on stacking lips."""

from build123d import Compound, Part

from ..box import STACK_SOCKET_DEPTH, split_stacking_lips
from ..hex import config as c
from ..hex.cover import create_cover, label_fit
from ..stackable_checks import check_cover, check_split_lips

PARAMS = []
IS_ASSEMBLY = False


def _create_finished() -> Part:
    """Clean assembled reference for splitting and interface checks."""
    cover_h = c.cover_h_for(c.ALLEN_BIT_LEN, c.guide_floor_z("allen"), stackable=True)
    size, label_z, horizontal = label_fit(cover_h, "ALLEN")
    cover = create_cover(
        "ALLEN",
        cover_h,
        size,
        label_z,
        label_horizontal=horizontal,
        stackable=True,
    )
    cover.label = "cover_stackable_allen"
    cover.color = c.COVER_COLOR
    return cover


def create() -> Compound:
    return split_stacking_lips(_create_finished(), STACK_SOCKET_DEPTH)


def check():
    clean = _create_finished()
    report = check_cover(
        clean,
        c.BASE_FOOT_TOP,
        c.guide_floor_z("allen") + c.ALLEN_BIT_LEN,
        c.COVER_TIP_CLEARANCE,
    )
    check_split_lips(report, create(), clean)
    return report
