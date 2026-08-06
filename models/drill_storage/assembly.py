"""The assembled scene for a set: shell, cartridge, every tool, cover on top.

One builder for all three variants -- ``wood``, ``metal`` and ``stone`` each call
it with their own ``DrillSet`` and get the same scene cut to their own set. It is
the one view where the whole argument is visible at once: the tools stand on the
shell's **ASA** floor and are guided by ASA over 23.2 mm, and only the short blue
TPU collar at the top touches them with any interference.

A scene, not a print job. The three printable parts are downloadable on their own
(``<set>.shell``, ``<set>.insert``, ``<set>.cover``), which they must be -- they
are three different filaments and never share a bed.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rotation

from . import config as c
from .cover import create_cover_for
from .insert import create_insert_for
from .sets import DrillSet
from .shell import create_shell_for
from .tools import CARBIDE, COVER_GLASS, STEEL, create_drill, create_hex_tool


def create_assembly(drill_set: DrillSet) -> Compound:
    """Shell, collar seated in it, every tool in its bore, cover on top."""
    shell = create_shell_for(drill_set)

    insert = Pos(0, 0, c.CAVITY_FLOOR_Z) * create_insert_for(drill_set)
    insert.label = f"insert_tpu_{drill_set.name}"
    insert.color = c.CART_COLOR

    tools = []
    for (bore_d, x, y), drill in zip(drill_set.bores, drill_set.drills):
        bit = create_drill(
            drill.nominal, drill.length, style=drill_set.style, shank_d=bore_d
        )
        bit.label = f"drill_{drill.nominal:g}mm"
        bit.color = CARBIDE if drill_set.style == "masonry" else STEEL
        # GUIDE_FLOOR_Z, not CAVITY_FLOOR_Z: a bit drops through the collar and
        # rests on the shell's ASA floor, 23.2 mm below where the collar sits.
        # Soft plastic creeps under a point load; ASA does not.
        tools.append(Pos(x, y, c.GUIDE_FLOOR_Z) * bit)

    for (af, x, y), spec in zip(drill_set.hex_bores, drill_set.hex_tools):
        tool = create_hex_tool(af, spec.length, head_d=spec.head_d)
        tool.label = f"hex_{spec.key.lower()}"
        tool.color = STEEL
        # Shank-end on the shell floor, same as every drill: a hex socket 31.2 mm
        # deep no longer swallows a 40 mm shank, so the tool bottoms out and its
        # head stands proud rather than resting on the top face. The collar still
        # grips the shank, and the cover has room to spare.
        tools.append(Pos(x, y, c.GUIDE_FLOOR_Z) * tool)

    # create_cover returns print pose (pillow on the bed, mouth up); flip it back
    # and seat it on the shoulder, translucent so the tools read through it.
    cover = Rotation(180, 0, 0) * create_cover_for(drill_set)
    cover = Pos(0, 0, c.SHELL_FOOT_TOP - cover.bounding_box().min.Z) * cover
    cover.label = f"cover_{drill_set.name}"
    cover.color = COVER_GLASS

    return Compound(
        label=f"drill_storage.{drill_set.name}",
        children=[shell, insert, *tools, cover],
    )


__all__ = ["create_assembly"]
