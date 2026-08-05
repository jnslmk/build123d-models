"""Gridfinity drill storage: one base/cover engine, one holder per tool set.

Every holder here is the same two-part telescoping idea -- a bored 1x1 Gridfinity
base with a tall labelled cover that snaps over it -- cut from the shared engine
in ``box.py``. A holder module supplies nothing but a drill list, a cover label
and (where the set is short) a cover height; ``box`` solves the hole packing, the
rib geometry, the wall legends and the print poses.

    uv run show drill_storage             # the engine's demo set: 3 covers, 2 bases
    uv run show drill_storage.wood        # 2-10 mm brad-point set + countersink
    uv run show drill_storage.metal       # 1-10 mm HSS twist set + hex tap
    uv run show drill_storage.hex         # 16-piece 1/4" hex-shank bit set
    uv run show drill_storage.assemblies.wood   # the wood set with drills in it
    uv run export drill_storage.wood      # STLs for the slicer (base + cover)

Fit is the whole game here: the bores grip on three compliant ribs at a measured
interference, and that number was settled by printing coupons rather than by
arithmetic. The coupons live next door in ``models.drill_fit_tester``, and
``box.grip_for`` is the law they produced.
"""

from . import box
from .box import (
    BASE_COLOR,
    COVER_COLOR,
    RIB_GRIP,
    cover_height_for,
    create_base,
    create_cover,
    grip_for,
    layout_bores,
    ribbed_valley_r,
)
from .sampler import create

__all__ = [
    "BASE_COLOR",
    "COVER_COLOR",
    "RIB_GRIP",
    "box",
    "cover_height_for",
    "create",
    "create_base",
    "create_cover",
    "grip_for",
    "layout_bores",
    "ribbed_valley_r",
]
