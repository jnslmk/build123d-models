"""Stackable BITS cover: supported one-piece or separate glue-on lips."""

from build123d import Compound, Part

from ...box import STACK_SOCKET_DEPTH, split_stacking_lips
from .. import config as c
from ..cover import create_cover, label_fit
from ...stackable_checks import check_cover, check_split_lips
from ...cover import SEPARATE_STACKING_LIPS_PARAM, SUPPORT_PARAM

PARAMS = [SUPPORT_PARAM, SEPARATE_STACKING_LIPS_PARAM]
IS_ASSEMBLY = False


def create(
    support: bool = True, separate_stacking_lips: bool = False
) -> Part | Compound:
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
        support=support and not separate_stacking_lips,
    )
    cover.label = "cover_stackable_bits"
    cover.color = c.COVER_COLOR
    if separate_stacking_lips:
        return split_stacking_lips(cover, STACK_SOCKET_DEPTH)
    return cover


def check():
    report = check_cover(
        create(),
        c.BASE_FOOT_TOP,
        c.guide_floor_z("bits") + c.BITS_BIT_LEN,
        c.COVER_TIP_CLEARANCE,
    )
    check_split_lips(report, create(separate_stacking_lips=True), create(support=False))
    return report
