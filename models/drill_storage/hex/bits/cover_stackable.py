"""Stackable BITS cover: roof-down body and glue-on stacking lips."""

from build123d import Compound, Part

from ...box import STACK_SOCKET_DEPTH, split_stacking_lips
from .. import config as c
from ..cover import create_cover, label_fit
from ...stackable_checks import check_cover, check_split_lips

PARAMS = []
IS_ASSEMBLY = False


def _create_finished() -> Part:
    """Clean assembled reference for splitting and interface checks."""
    cover_h = c.cover_h_for(c.BITS_BIT_LEN, c.guide_floor_z("bits"), stackable=True)
    size, label_z, horizontal = label_fit(cover_h, "BITS")
    cover = create_cover(
        "BITS",
        cover_h,
        size,
        label_z,
        label_horizontal=horizontal,
        snap_protrusion=c.cover_snap_protrusion("bits"),
        stackable=True,
    )
    cover.label = "cover_stackable_bits"
    cover.color = c.COVER_COLOR
    return cover


def create() -> Compound:
    return split_stacking_lips(_create_finished(), STACK_SOCKET_DEPTH)


def check():
    clean = _create_finished()
    report = check_cover(
        clean,
        c.BASE_FOOT_TOP,
        c.guide_floor_z("bits") + c.BITS_BIT_LEN,
        c.COVER_TIP_CLEARANCE,
    )
    check_split_lips(report, create(), clean)
    return report
