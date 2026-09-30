"""Feet-down ASA anchor for 36 short bits in a labelled 1×2 Gridfinity base.

Only the rigid base is built here. The rectangular cartridge and cover interfaces
retain the existing BITS fits and heights; their dependent parts await acceptance.
"""

from __future__ import annotations

import fontfix  # noqa: F401 -- register the same sans font as the existing labels
from build123d import (
    BuildPart,
    BuildSketch,
    FontStyle,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    Text,
    add,
    extrude,
    loft,
)

from models.drill_storage import config as family
from models.drill_storage.base import key_slot_tool
from models.drill_storage.box import (
    BASE_H,
    GRID,
    SNAP_GROOVE_D,
    SNAP_GROOVE_FLOOR,
    SNAP_GROOVE_ROOF,
    SNAP_TIP_FLAT,
    SNAP_Z,
    gridfinity_foot,
)
from models.drill_storage.hex import config as hex_config
from models.drill_storage.hex.base import hex_guide_tool
from models.lib.edges import top_chamfer_tool

from . import config as c

IS_ASSEMBLY = False
PARAMS = []


def _cover_groove() -> Part:
    """The family's cover receiver, extended along Y without changing its section."""
    bottom = c.SEAT_Z + SNAP_Z - SNAP_GROOVE_FLOOR
    top = c.SEAT_Z + SNAP_Z + SNAP_GROOVE_ROOF
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(bottom)):
            RectangleRounded(
                c.COLLAR_X + 0.02, c.COLLAR_Y + 0.02, c.COLLAR_CORNER + 0.01
            )
        extrude(amount=top - bottom)
        sections = []
        for z, inset in (
            (bottom, 0),
            (c.SEAT_Z + SNAP_Z - SNAP_TIP_FLAT / 2, SNAP_GROOVE_D),
            (c.SEAT_Z + SNAP_Z + SNAP_TIP_FLAT / 2, SNAP_GROOVE_D),
            (top, 0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.COLLAR_X - 2 * inset,
                    c.COLLAR_Y - 2 * inset,
                    c.COLLAR_CORNER - inset,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True, mode=Mode.SUBTRACT)
    return tool.part


def _insert_groove() -> Part:
    """Rectangular cartridge receiver with the unchanged BITS ramp and 45° roof."""
    with BuildPart() as tool:
        sections = []
        for z, outward in (
            (hex_config.BEAD_Z - hex_config.GROOVE_FLOOR, 0.01),
            (
                hex_config.BEAD_Z - hex_config.GROOVE_TIP_FLAT / 2,
                hex_config.GROOVE_D,
            ),
            (
                hex_config.BEAD_Z + hex_config.GROOVE_TIP_FLAT / 2,
                hex_config.GROOVE_D,
            ),
            (hex_config.BEAD_Z + hex_config.GROOVE_ROOF, 0.01),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.CAVITY_X + 2 * outward,
                    c.CAVITY_Y + 2 * outward,
                    c.CAVITY_CORNER + outward,
                )
                RectangleRounded(
                    c.CAVITY_X - 0.02,
                    c.CAVITY_Y - 0.02,
                    c.CAVITY_CORNER - 0.01,
                    mode=Mode.SUBTRACT,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return tool.part


def label_tools() -> tuple[Part, ...]:
    """Return the 36 exact engraving tools in ``config.SOCKETS`` row-major order.

    Each long wall names its nearest two socket columns. Even columns use the
    +Y member of each pair, odd columns the -Y member. Full strings read upward
    on both walls: local +Y is world +Z, and the planes face outward so negative
    extrusion cuts inward without mirroring the text. Centering uses actual ink
    bounds, not the font's advance width or baseline alignment.
    """
    tools = []
    for index, (label, _x, y) in enumerate(c.SOCKETS):
        column = index % 4
        side = -1 if column < 2 else 1
        center_y = y + (1 if column % 2 == 0 else -1) * c.LABEL_PAIR_OFFSET
        wall = Plane(
            origin=(side * c.BODY_X / 2, center_y, c.LABEL_Z),
            x_dir=(0, side, 0),
            z_dir=(side, 0, 0),
        )
        with BuildSketch() as glyph:
            Text(
                label,
                font_size=c.LABEL_SIZE,
                font_style=FontStyle.BOLD,
                rotation=90,
            )
        center = glyph.sketch.bounding_box().center()
        with BuildPart() as tool:
            with BuildSketch(wall):
                with Locations((-center.X, -center.Y)):
                    add(glyph.sketch)
            extrude(amount=-c.LABEL_DEPTH)
        tools.append(tool.part)
    return tuple(tools)


def _build(tools: tuple[Part, ...]) -> Part:
    """One builder for the printable part and its unengraved comparison solid."""
    # Build independent helper parts before the outer builder so no helper can
    # auto-add an unplaced copy into the base's active context.
    foot = gridfinity_foot()
    cover_groove = _cover_groove()
    insert_groove = _insert_groove()
    key_slot = key_slot_tool(hex_config)
    outer_chamfer = top_chamfer_tool(
        c.COLLAR_X,
        c.COLLAR_Y,
        c.COLLAR_CORNER,
        c.BASE_TOP_Z,
        hex_config.SHELL_TOP_CHAMFER,
    )
    with BuildPart() as base:
        with Locations((0, -GRID / 2, 0), (0, GRID / 2, 0)):
            add(foot)
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(c.BODY_X, c.BODY_Y, c.BODY_R)
        extrude(amount=c.SEAT_Z - BASE_H)
        # Leave the cover's seating shoulder flat; bevel only the collar's top.
        with BuildSketch(Plane.XY.offset(c.SEAT_Z)):
            RectangleRounded(c.COLLAR_X, c.COLLAR_Y, c.COLLAR_CORNER)
        extrude(amount=c.BASE_TOP_Z - c.SEAT_Z)
        add(cover_groove, mode=Mode.SUBTRACT)
        add(outer_chamfer, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            RectangleRounded(c.CAVITY_X, c.CAVITY_Y, c.CAVITY_CORNER)
        extrude(
            amount=c.BASE_TOP_Z - c.CAVITY_FLOOR_Z + 0.01,
            mode=Mode.SUBTRACT,
        )
        add(insert_groove, mode=Mode.SUBTRACT)
        # The +X/y=0 key slot is unchanged: stretching Y does not move its wall.
        add(key_slot, mode=Mode.SUBTRACT)
        ch = hex_config.CAVITY_MOUTH_CH
        with BuildSketch(Plane.XY.offset(c.BASE_TOP_Z - ch)) as low:
            RectangleRounded(c.CAVITY_X, c.CAVITY_Y, c.CAVITY_CORNER)
        with BuildSketch(Plane.XY.offset(c.BASE_TOP_Z + 0.01)) as high:
            RectangleRounded(
                c.CAVITY_X + 2 * (ch + 0.01),
                c.CAVITY_Y + 2 * (ch + 0.01),
                c.CAVITY_CORNER + ch + 0.01,
            )
        loft(sections=[low.sketch, high.sketch], ruled=True, mode=Mode.SUBTRACT)

        for _label, x, y in c.SOCKETS:
            add(
                hex_guide_tool(
                    hex_config.BITS_GUIDE_AF,
                    x,
                    y,
                    hex_config.BITS_GUIDE_MOUTH_CH,
                    c.GUIDE_FLOOR_Z,
                ),
                mode=Mode.SUBTRACT,
            )
        for tool in tools:
            add(tool, mode=Mode.SUBTRACT)
    result = base.part
    result.color = family.SHELL_COLOR
    return result


def create_blank() -> Part:
    """Return the same complete base without legends, for engraving proof."""
    return _build(())


def create() -> Part:
    """Return the labelled rigid anchor, two standard feet down at z=0."""
    return _build(label_tools())
