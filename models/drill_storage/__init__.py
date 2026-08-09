"""Gridfinity drill storage: one two-material holder, one variant per tool set.

Every holder here is the same idea, cut for a different set of tools: a rigid
**ASA base** that keeps its shape and guides a bit upright, a short compliant
**TPU cartridge** that grips it and does nothing else, and a tall labelled
**PETG cover** that snaps over the collar. Three filaments, three print jobs, one
1x1 Gridfinity footprint.

    uv run show drill_storage              # all three drill sets, bases and covers
    uv run show drill_storage.wood         # 2-10 mm brad-point set + countersink
    uv run show drill_storage.metal        # 1-10 mm twist + tap + step drill
    uv run show drill_storage.stone        # 3-10 mm carbide masonry set
    uv run show drill_storage.allen        # 8-piece 50 mm hex-key box
    uv run show drill_storage.hex          # 16-piece 1/4" hex-shank driver bits
    uv run show drill_storage.wood.insert  # just the TPU cartridge, print pose
    uv run export drill_storage.wood.base # STL + STEP for the slicer

A variant is four modules of naming (``__init__`` scene, ``base``, ``insert``,
``cover``) over a set defined in ``sets.py``. The clearances are in ``config.py``
and are shared by the drill sets: one land fit, one guide fit, one relief. Adding
a set is a ``DrillSet`` and a package, and nothing in the geometry has to
know about it.

**Fit is the whole game**, and the two halves are cut on opposite sides of
nominal on purpose: the ASA guide clears (``GUIDE_FIT``, +0.49) so a bit never
drags over 23.2 mm of base, and the TPU land interferes (``LAND_FIT``, -0.05) so
3.5 mm of cartridge holds it. ``checks.py`` asserts that ordering, because a
guide that gripped or a land that cleared would each defeat the split silently.

The two 1/4" hex-shank sets share one geometry: ``drill_storage.allen`` is the
1x1 ALLEN key box (eight 50 mm keys, sizes engraved largest -> smallest) and
``drill_storage.hex`` the 1x1 driver-bit box (sixteen 25 mm bits in a literal
4x4 grid). Both are rigid black base + black TPU insert + translucent cover;
ALLEN keeps the family's clearances outright, BITS shaves its lead-in
clearances to spread 16 across a 4x4 grid. The geometry lives in ``hex`` and
``allen`` names it.
"""

from . import box, config, sets
from .box import (
    BASE_COLOR,
    COVER_COLOR,
    cover_height_for,
    create_base,
    create_cover,
    layout_bores,
    plain_bore_r,
)
from .sampler import IS_ASSEMBLY, create

__all__ = [
    "BASE_COLOR",
    "COVER_COLOR",
    "IS_ASSEMBLY",
    "box",
    "config",
    "cover_height_for",
    "create",
    "create_base",
    "create_cover",
    "layout_bores",
    "plain_bore_r",
    "sets",
]
