"""Hex-bit storage, assembled: both two-material boxes, all 24 tools, covers.

Gridfinity storage for a 16-piece 1/4" hex-shank bit set -- 8 long + 8 short --
and the last member of the drill_storage family to go two-material: every box is
now a rigid base that guides, a TPU insert that grips, and a translucent cover,
exactly like the drill sets. The bases and inserts are black; the covers are
translucent so the bits read through them.

Two boxes, one per bit family, both 1x1 Gridfinity:

* **ALLEN** -- the 50 mm hex-key bits, sizes 1.5 / 2 / 2.5 /
  3 / 4 / 5 / 6 / 8. Those sizes are engraved into the body walls, laid out in
  rows largest -> smallest like the drill variants, so the set reads as an
  ordered grid.
* **BITS** -- the 25 mm driver bits (Torx, Phillips, Pozidriv,
  slotted, ...), sixteen of them in a **literal 4x4 grid**. A mixed bag with no
  single size scale to engrave, so the walls stay blank and you read the tip
  itself -- which is exactly what's left standing proud.

Sixteen sockets cannot meet the family's clearances on one 1x1 collar -- the
cartridge's mouth lead-ins alone need an 8.88 mm pitch where the wall allows
8.27 mm -- so the BITS box **shaves** the lead-in clearances instead of growing
to 2x2 (the shaved numbers and the margins they leave are argued and pinned in
`config.py` / `checks.py`). The user accepted the tight margins; TPU bores
print undersize, so the real ones are better.

A scene, not a print job -- three materials (black ASA base, black TPU insert,
translucent PETG cover) never share a bed. The parts are:

    uv run show drill_storage.hex.allen.base    # rigid, foot down, cavity up
    uv run show drill_storage.hex.allen.insert  # TPU, flat down, bores up
    uv run show drill_storage.hex.allen.cover   # translucent, pillow top down
    uv run show drill_storage.hex.bits.base     # 1x1, foot down, cavity up
    uv run show drill_storage.hex.bits.insert   # TPU, flat down, bores up
    uv run show drill_storage.hex.bits.cover    # translucent, pillow top down

Bases are 30 mm, not the family's 36 -- a bit needs none of a drill's depth.
Bits rest on the guide floor at z=15 and stand proud of the rim by the
documented amounts:

    ALLEN (50 mm bits): 35 mm proud, 52 mm cover -> 70 mm (10U) assembled
    BITS  (25 mm bits): 10 mm proud, 31 mm cover -> 49 mm (7U) assembled

The geometry is this package's, re-derived from the family's clearances; the
argument lives with the family in ``drill_storage.config`` and its design notes.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rotation

from ..tools import COVER_GLASS, STEEL, create_hex_tool
from . import config as c
from .base import create_base
from .cover import create_cover, label_fit
from .insert import create_insert

# A display/verification scene, so no STL/STEP download is offered for it: the
# six printable parts next to it are what you download.
IS_ASSEMBLY = True

GAP = 10.0  # edge-to-edge gap between the two boxes, like the family's pitch


def _box(
    x: float,
    name: str,
    bit_len: float,
    label: str,
    has_legend: bool,
) -> list:
    """One box, fully assembled: base, cartridge, tools, cover on top.

    Mirrors ``drill_storage.assembly.create_assembly`` (it builds one set; this
    builds one of the two hex boxes). The bits stand on the rigid guide floor,
    gripped by the cartridge's lands, with the translucent cover seated on the
    shoulder. Both boxes share the family's 1x1 envelopes; the per-box guide
    and mouth numbers come from ``config.box_fits``.
    """
    guide_af, guide_mouth_ch, cart_mouth_ch = c.box_fits(name)
    hex_bores, rows, pos = c.socket_layout(name)

    base = create_base(
        hex_bores,
        guide_af=guide_af,
        guide_mouth_ch=guide_mouth_ch,
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
    # floor like the drill sets' bits stand on the shell floor.
    tools = [
        Pos(xp, yp, c.GUIDE_FLOOR_Z) * create_hex_tool(c.HEX_SHANK_AF, bit_len)
        for _af, xp, yp in hex_bores
    ]
    for tool in tools:
        tool.label = f"bit_{name}"
        tool.color = STEEL

    # create_cover returns print pose (pillow on the bed, mouth up); flip it
    # back and seat it on the shoulder, translucent so the bits read through.
    cover_h = c.cover_h_for(bit_len)
    size, label_z, horizontal = label_fit(cover_h, label)
    cover = create_cover(
        label,
        cover_h=cover_h,
        label_size=size,
        label_z=label_z,
        label_horizontal=horizontal,
    )
    cover = Rotation(180, 0, 0) * cover
    cover = Pos(0, 0, c.BASE_FOOT_TOP - cover.bounding_box().min.Z) * cover
    cover.label = f"cover_{name}"
    cover.color = COVER_GLASS

    return [Pos(x, 0, 0) * child for child in (base, insert, *tools, cover)]


def create() -> Compound:
    """Both hex-bit boxes, side by side: ALLEN (1x1) left, BITS (1x1) right."""
    # BODY_W, not PAD: GAP is meant to be the air you see between the two boxes,
    # and what stands closest is the body/cover silhouette, not the foot.
    x_allen = -(c.BODY_W / 2 + c.BODY_W / 2 + GAP / 2)
    x_bits = -x_allen
    children = []
    children += _box(
        x_allen,
        "allen",
        c.ALLEN_BIT_LEN,
        "ALLEN",
        True,
    )
    children += _box(
        x_bits,
        "bits",
        c.BITS_BIT_LEN,
        "BITS",
        False,
    )
    return Compound(label="drill_storage.hex", children=children)


__all__ = ["GAP", "IS_ASSEMBLY", "create"]
