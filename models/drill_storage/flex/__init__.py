"""Two-material drill storage: a rigid ASA shell holding a compliant TPU cartridge.

The same Gridfinity holder as ``drill_storage.wood``, split along the line where
the two jobs actually differ. The **shell** (``flex.shell``, ASA) keeps its shape:
the Gridfinity foot, the collar, the cover's snap groove, the engraved size
legend. The **cartridge** (``flex.insert``, TPU) does the gripping and nothing
else, and drops in from the top so a different drill set is a cartridge reprint
rather than a whole new base.

**No ribs.** The PETG base grips on three compliant beads per bore because PETG
has none of its own; TPU is the spring, so the rib geometry stops earning its
complexity. What does *not* follow is a plain deep interference bore -- in TPU
that reaches tens of kgf of pull-out at any interference big enough to model. So
the bores are plain and round, and the *contact* is short instead: a 3.5 mm land
at the bottom of an otherwise free-fit bore, on the plain shank where the PETG
version's ribs already grip. ``config.LAND_FIT`` has the full argument and the
numbers.

The shell keeps ``BORE_FLOOR_Z`` and ``FOOT_TOP``, so ``cover_height_for``
returns the same 109 mm it does for ``drill_storage.wood`` -- **an already-printed
wood cover fits this shell**. ``checks.py`` asserts it.

The land fit is uncalibrated. See ``drill_fit_tester.land`` and README.md.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rotation

from ..assemblies.wood import (
    COVER_GLASS,
    DRILL_LENGTHS,
    STEEL,
    create_countersink,
    create_drill,
)
from ..box import BASE_TOTAL_H, FOOT_TOP, create_cover
from ..wood import COVER_H_WOOD, CSK_HEAD_D, LABEL
from . import config as config
from .insert import create as create_insert_part
from .insert import create_insert as create_insert
from .shell import DRILL_BORES, HEX_BORES, POS, ROWS
from .shell import create as create_shell_part
from .shell import create_shell as create_shell

# A scene, not a print job: no STL/STEP download is offered for it. Both halves
# are downloadable from ``drill_storage.flex.shell`` and ``.insert``.
IS_ASSEMBLY = True


def create_flex_assembly() -> Compound:
    """Shell, collar seated in it, every drill in its bore, cover on top.

    The one view that shows the whole argument at once: the drills stand on the
    shell's ASA floor and are guided by ASA for 24.8 mm, and only the short blue
    TPU collar at the top touches them with any interference. The cover is the
    *existing* wood cover, unmodified, which is the point of keeping the collar
    interface untouched.
    """
    shell = create_shell_part()
    insert = Pos(0, 0, config.CAVITY_FLOOR_Z) * create_insert_part()
    insert.label = "insert_tpu"
    insert.color = config.CART_COLOR

    drills = []
    for d, x, y in DRILL_BORES:
        bit = create_drill(d, DRILL_LENGTHS.get(d, 80.0))
        bit.label = f"drill_{d:g}mm"
        bit.color = STEEL
        # GUIDE_FLOOR_Z, not CAVITY_FLOOR_Z: a drill drops through the collar and
        # rests on the shell's ASA floor, 24.8 mm below where the collar sits.
        drills.append(Pos(x, y, config.GUIDE_FLOOR_Z) * bit)

    for af, x, y in HEX_BORES:
        csk = create_countersink(af, CSK_HEAD_D)
        csk.label = "countersink_10mm"
        csk.color = STEEL
        # Head rests on the cartridge's top face, which stands CART_PROUD above
        # the shell rim.
        drills.append(Pos(x, y, BASE_TOTAL_H + config.CART_PROUD - 40.0) * csk)

    # create_cover returns print pose (pillow on the bed, mouth up); flip it back
    # and seat it on the shoulder, translucent so the drills read through it.
    cover = Rotation(180, 0, 0) * create_cover(LABEL, cover_h=COVER_H_WOOD)
    cover = Pos(0, 0, FOOT_TOP - cover.bounding_box().min.Z) * cover
    cover.label = "cover_wood"
    cover.color = COVER_GLASS

    return Compound(
        label="drill_storage.flex",
        children=[shell, insert, *drills, cover],
    )


def create() -> Compound:
    """Model entry point -- see ``create_flex_assembly``."""
    return create_flex_assembly()


__all__ = [
    "DRILL_BORES",
    "HEX_BORES",
    "IS_ASSEMBLY",
    "POS",
    "ROWS",
    "config",
    "create",
    "create_flex_assembly",
    "create_insert",
    "create_shell",
]
