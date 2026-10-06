"""Accepted bin and photo-approximate tools with the clean lid seated for review.

This is an inspection scene, not a print layout or a measured tool-fit claim.
The lid is translucent only to keep the tool envelopes visible.
"""

from build123d import Color, Compound

from . import config as c
from . import lid, preview

IS_ASSEMBLY = True
PARAMS = c.PARAMS


def create(
    wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN,
) -> Compound:
    """Keep the open preview's canonical pose and add exactly one clean lid."""
    open_scene = preview.create(wrenches_per_column)
    cover = lid.seated(wrenches_per_column)
    cover.color = Color(0.86, 0.87, 0.84, 0.32)
    return Compound(
        children=[*open_scene.children, cover],
        label="Closed on-edge WORKZONE storage (photo approximations)",
    )
