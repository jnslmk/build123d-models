"""Empty Gridfinity bin with its removable stackable lid seated for inspection."""

from typing import Any

from build123d import Compound, Pos, Rotation

from models.lib.edges import as_part
from . import base, config, lid

IS_ASSEMBLY = True
PARAMS = [
    *base.PARAMS,
    next(param for param in lid.PARAMS if param["name"] == "lid_height"),
]


def create(lid_height: float = config.LID_MIN_HEIGHT, **bin_options: Any) -> Compound:
    """Closed scene without the lid's sacrificial print support.

    `base.create()` and `lid.create()` remain the separately downloadable parts.
    """
    body = base.create(**bin_options)
    lid_options = {
        name: bin_options[name]
        for name in (
            "grid_x",
            "grid_y",
            "half_grid_base",
            "half_grid_right",
            "half_grid_top",
            "wall_thickness",
        )
        if name in bin_options
    }
    cover = lid.create(**lid_options, lid_height=lid_height, support=False)
    cover = as_part(
        Pos(
            0,
            0,
            bin_options.get("height_u", 5) * config.HEIGHT_UNIT
            + lid_height
            - config.LID_SKIRT_MIN,
        )
        * Rotation(180, 0, 0)
        * cover
    )
    cover.color = config.LID_COLOR
    return Compound(children=[body, cover], label="empty Gridfinity bin with lid")
