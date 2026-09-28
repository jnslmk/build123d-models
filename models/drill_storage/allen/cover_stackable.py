"""Stackable ALLEN cover; remove the built-in socket support after printing."""

from build123d import Part

from ..hex import config as c
from ..hex.cover import create_cover, label_fit
from ..stackable_checks import check_cover


def create() -> Part:
    cover_h = c.cover_h_for(c.ALLEN_BIT_LEN, c.guide_floor_z("allen"), stackable=True)
    size, label_z, horizontal = label_fit(cover_h, "ALLEN")
    cover = create_cover(
        "ALLEN", cover_h, size, label_z, label_horizontal=horizontal, stackable=True
    )
    cover.label = "cover_stackable_allen"
    cover.color = c.COVER_COLOR
    return cover


def check():
    return check_cover(
        create(),
        c.BASE_FOOT_TOP,
        c.guide_floor_z("allen") + c.ALLEN_BIT_LEN,
        c.COVER_TIP_CLEARANCE,
    )
