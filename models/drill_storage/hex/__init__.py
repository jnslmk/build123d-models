"""Hex-bit storage, assembled: the BITS driver-bit box, all 16 tools, cover.

Gridfinity storage for the 16-piece 1/4" hex-shank driver-bit set -- 25 mm
bits (Torx, Phillips, Pozidriv, slotted, ...) -- and one of the five top-level
drill_storage sets, cut exactly like the others: a rigid black ASA base that
guides, a black TPU insert that grips, and a translucent cover that reads
through. Sixteen identical sockets sit in a **literal 4x4 grid**.

Sixteen sockets cannot meet the family's clearances on one 1x1 collar -- the
insert's mouth lead-ins alone need an 8.88 mm pitch where the wall allows
8.27 mm -- so this box **shaves** the lead-in clearances instead of growing to
2x2 (the shaved numbers and the margins they leave are argued and pinned in
`config.py` / `checks.py`). The user accepted the tight margins; TPU bores
print undersize, so the real ones are better.

The ALLEN key box -- the other half of what used to be one two-box ``hex``
scene -- now lives in its own package, ``drill_storage.allen``. The geometry
is shared: both boxes are cut from this package's ``base`` / ``insert`` /
``cover`` modules, and the ALLEN box's models are thin naming modules over
them. ``create_box_scene`` builds either box from its own
``config.socket_layout``.

A scene, not a print job -- three materials (black ASA base, black TPU insert,
translucent PETG cover) never share a bed. The parts are:

    uv run show drill_storage.hex            # the BITS box, all 16 bits standing
    uv run show drill_storage.hex.bits.base  # 1x1, foot down, cavity up
    uv run show drill_storage.hex.bits.insert  # TPU, flat down, bores up
    uv run show drill_storage.hex.bits.cover   # translucent, pillow top down

Bits sink ``BITS_HOLE_DEPTH`` (15 mm) below the rim, resting on the guide floor
at z=15, and stand 10 mm proud; the 24 mm cover (42 mm / 6U assembled) clears
the longest bit by exactly ``COVER_TIP_CLEARANCE`` and not a micron more. The
ALLEN box sinks its keys 21 mm on the same base -- ``config.guide_floor_z`` is
the one place that says which box gets which.

The geometry is this package's, re-derived from the family's clearances; the
argument lives with the family in ``drill_storage.config`` and its design
notes.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rotation

from ..tools import COVER_GLASS, STEEL, create_hex_tool
from . import config as c
from .base import create_base
from .cover import create_cover, label_fit
from .insert import create_insert

# A display/verification scene, so no STL/STEP download is offered for it: the
# three printable parts next to it are what you download.
IS_ASSEMBLY = True


def create_box_scene(
    name: str,
    bit_len: float,
    label: str,
    has_legend: bool,
) -> list:
    """One hex box, fully assembled: base, cartridge, tools, cover on top.

    Mirrors ``drill_storage.assembly.create_assembly`` (it builds one drill
    set; this builds one of the two hex boxes). The bits stand on the box's own
    rigid guide floor, gripped by the cartridge's lands, with the translucent
    cover seated on the shoulder. Both boxes share the family's 1x1 envelopes;
    the per-box guide and mouth numbers come from ``config.box_fits`` and the
    floor from ``config.guide_floor_z`` -- read once here, so the base, the
    tools and the cover cannot disagree about how deep the hole is.

    Returns the children only -- each package wraps them in its own
    ``Compound``, so the scene carries the package's name
    (``drill_storage.hex`` vs ``drill_storage.allen``).
    """
    guide_af, guide_mouth_ch, cart_mouth_ch = c.box_fits(name)
    hex_bores, rows, pos = c.socket_layout(name)
    floor_z = c.guide_floor_z(name)

    base = create_base(
        hex_bores,
        guide_af=guide_af,
        guide_mouth_ch=guide_mouth_ch,
        guide_floor_z=floor_z,
        rows=rows if has_legend else None,
        hole_pos=pos if has_legend else None,
    )
    base.label = f"base_{name}"
    base.color = c.BASE_COLOR

    insert = Pos(0, 0, c.CAVITY_FLOOR_Z) * create_insert(
        hex_bores, mouth_ch=cart_mouth_ch
    )
    insert.label = f"insert_{name}"
    insert.color = c.INSERT_COLOR

    # Every bit is the same plain 1/4" hex shank, drawn standing on the guide
    # floor like the drill sets' bits stand on the base floor.
    tools = [
        Pos(xp, yp, floor_z) * create_hex_tool(c.HEX_SHANK_AF, bit_len)
        for _af, xp, yp in hex_bores
    ]
    for tool in tools:
        tool.label = f"bit_{name}"
        tool.color = STEEL

    # create_cover returns print pose (pillow on the bed, mouth up); flip it
    # back and seat it on the shoulder, translucent so the bits read through.
    cover_h = c.cover_h_for(bit_len, floor_z)
    size, label_z, horizontal = label_fit(cover_h, label)
    cover = create_cover(
        label,
        cover_h=cover_h,
        label_size=size,
        label_z=label_z,
        label_horizontal=horizontal,
        snap_protrusion=c.cover_snap_protrusion(name),
    )
    cover = Rotation(180, 0, 0) * cover
    cover = Pos(0, 0, c.BASE_FOOT_TOP - cover.bounding_box().min.Z) * cover
    cover.label = f"cover_{name}"
    cover.color = COVER_GLASS

    return [base, insert, *tools, cover]


def create() -> Compound:
    """The BITS driver-bit box, fully assembled: base, cartridge, tools, cover."""
    return Compound(
        label="drill_storage.hex",
        children=create_box_scene("bits", c.BITS_BIT_LEN, "BITS", False),
    )


__all__ = ["IS_ASSEMBLY", "create", "create_box_scene"]
