"""Flat-bottom TPU cartridge for the accepted labelled 1×2 BITS base.

The 35.68×77.68 mm collar carries the fixed 36-socket grid and the existing
BITS grip, relief, key and retention-bead section. Print land-side down at
z=0, bores up, without supports; seating translates it to CAVITY_FLOOR_Z.
Hex socket corners and grip transitions, the bead's ramp datums, and the
reused key's boundary edges are functional rather than cosmetic edge breaks.
"""

from __future__ import annotations

from build123d import (
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage.box import hex_mouth_tool
from models.drill_storage.hex import config as h
from models.drill_storage.hex.insert import key_rib
from models.drill_storage.insert import hex_bore_tool
from models.lib.checks import Report
from models.lib.edges import bottom_chamfer_tool, top_chamfer_tool

from . import config as c

IS_ASSEMBLY = False
PARAMS = []


def _retention_bead() -> Part:
    """Extend the BITS asymmetric outward bead around the rectangular collar."""
    with BuildPart() as bead:
        sections = []
        for z, reach in (
            (h.CART_BELOW_BEAD - h.BEAD_LEAD_IN, 0.0),
            (h.CART_BELOW_BEAD - h.BEAD_TIP_FLAT / 2, h.CART_BEAD),
            (h.CART_BELOW_BEAD + h.BEAD_TIP_FLAT / 2, h.CART_BEAD),
            (h.CART_BELOW_BEAD + h.BEAD_BACK, 0.0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.CART_X + 2 * reach,
                    c.CART_Y + 2 * reach,
                    h.CART_R + reach,
                )
                # A 0.01 mm buried root avoids a merely tangent fuse, as in the
                # rectangular Dremel cartridge; this is not a mating clearance.
                RectangleRounded(
                    c.CART_X - 0.02,
                    c.CART_Y - 0.02,
                    h.CART_R - 0.01,
                    mode=Mode.SUBTRACT,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return bead.part


def create() -> Part:
    """Return the keyed 36-socket cartridge, grip lands down on the z=0 bed."""
    # Standalone builders must finish outside the cartridge builder: creating a
    # helper in an active parent can auto-add a second, unplaced copy.
    rib = key_rib()
    bead = _retention_bead()
    top_chamfer = top_chamfer_tool(
        c.CART_X, c.CART_Y, h.CART_R, h.CART_H, h.SHELL_TOP_CHAMFER
    )
    bottom_chamfer = bottom_chamfer_tool(
        c.CART_X,
        c.CART_Y,
        h.CART_R,
        0.0,
        0.4,  # inherited BITS outer foot relief
    )
    bore_tools = tuple(
        hex_bore_tool(h.HEX_AF, x, y, land_fit=h.HEX_LAND_FIT)
        for _label, x, y in c.SOCKETS
    )
    # The mouth helper takes the relief's circumradius, not across-flats and not
    # the grip-land radius. Its hex frustum begins directly on the relief wall.
    relief_r = (h.HEX_AF + h.RELIEF_FIT) / 3**0.5
    mouth_tools = tuple(
        hex_mouth_tool(relief_r, x, y, h.CART_H, h.BITS_CART_MOUTH_CH)
        for _label, x, y in c.SOCKETS
    )

    with BuildPart() as cartridge:
        with BuildSketch(Plane.XY):
            RectangleRounded(c.CART_X, c.CART_Y, h.CART_R)
        extrude(amount=h.CART_H)
        add(rib)
        add(bead)
        add(top_chamfer, mode=Mode.SUBTRACT)
        add(bottom_chamfer, mode=Mode.SUBTRACT)
        for tool in bore_tools:
            add(tool, mode=Mode.SUBTRACT)
        for tool in mouth_tools:
            add(tool, mode=Mode.SUBTRACT)

    result = cartridge.part
    result.label = "insert_bits_double"
    result.color = h.INSERT_COLOR
    return result


def check() -> Report:
    """Run the cartridge's physical geometry gate without building on import."""
    from . import insert_checks

    return insert_checks.run()
