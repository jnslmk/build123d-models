"""Removable 1×2 TPU cartridge with 55 short shank-gripping lands."""

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage import config as family
from models.lib.edges import bottom_chamfer_tool, reseat_on_bed, top_chamfer_tool
from . import config as c

IS_ASSEMBLY = False
PARAMS = []


def _retention_bead():
    """Rectangular version of the family's outward, ramped TPU snap bead."""
    bottom = family.CART_BELOW_BEAD - family.BEAD_LEAD_IN
    top = family.CART_BELOW_BEAD + family.BEAD_BACK
    with BuildPart() as bead:
        sections = []
        for z, reach in (
            (bottom, 0.01),
            (family.CART_BELOW_BEAD - family.BEAD_TIP_FLAT / 2, family.CART_BEAD),
            (family.CART_BELOW_BEAD + family.BEAD_TIP_FLAT / 2, family.CART_BEAD),
            (top, 0.01),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.CART_X + 2 * reach,
                    c.CART_Y + 2 * reach,
                    c.CART_CORNER + reach,
                )
                RectangleRounded(
                    c.CART_X - 0.02,
                    c.CART_Y - 0.02,
                    c.CART_CORNER - 0.01,
                    mode=Mode.SUBTRACT,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return bead.part


def create():
    """Return the insert in print pose, with its narrow grip lands facing up."""
    with BuildPart() as cartridge:
        with BuildSketch():
            RectangleRounded(c.CART_X, c.CART_Y, c.CART_CORNER)
        extrude(amount=family.CART_H)
        add(_retention_bead())
        add(
            top_chamfer_tool(
                c.CART_X,
                c.CART_Y,
                c.CART_CORNER,
                family.CART_H,
                family.SHELL_TOP_CHAMFER,
            ),
            mode=Mode.SUBTRACT,
        )
        add(
            bottom_chamfer_tool(c.CART_X, c.CART_Y, c.CART_CORNER, 0, 0.4),
            mode=Mode.SUBTRACT,
        )

        with BuildSketch():
            for x, y, diameter in c.CUT_BORES:
                with Locations((x, y)):
                    Circle((diameter + family.LAND_FIT) / 2)
        extrude(amount=family.LAND_H, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(family.LAND_H + family.LAND_LEAD_IN)):
            for x, y, diameter in c.CUT_BORES:
                with Locations((x, y)):
                    Circle((diameter + family.RELIEF_FIT) / 2)
        extrude(
            amount=family.CART_H - family.LAND_H - family.LAND_LEAD_IN + 0.01,
            mode=Mode.SUBTRACT,
        )
        for x, y, diameter in c.CUT_BORES:
            land_r = (diameter + family.LAND_FIT) / 2  # TPU interference land
            relief_r = (diameter + family.RELIEF_FIT) / 2  # TPU sliding relief
            with Locations((x, y, family.LAND_H)):
                Cone(
                    land_r,
                    relief_r,
                    family.LAND_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations((x, y, 0)):
                Cone(
                    land_r + family.BORE_FOOT_RELIEF,
                    land_r,
                    family.BORE_FOOT_RELIEF,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations((x, y, family.CART_H - family.CART_MOUTH_CH)):
                Cone(
                    relief_r,
                    relief_r + family.CART_MOUTH_CH,
                    family.CART_MOUTH_CH + 0.01,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
    result = reseat_on_bed(cartridge.part, flip=True)
    result.color = family.CART_COLOR
    return result
