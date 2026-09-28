"""Stackable BITS cover; remove the built-in socket support after printing."""

from build123d import Part

from .. import config as c
from ..cover import create_cover, label_fit
from ...stackable_checks import check_cover


def create() -> Part:
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


def check():
    return check_cover(
        create(),
        c.BASE_FOOT_TOP,
        c.guide_floor_z("bits") + c.BITS_BIT_LEN,
        c.COVER_TIP_CLEARANCE,
    )
