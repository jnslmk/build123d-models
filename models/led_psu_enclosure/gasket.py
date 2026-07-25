"""The 3 mm silicone cord, shown seated in its groove.

Not a printed part -- a bought consumable -- so it never appears in the print
layout. It is drawn at its **compressed** size: the round cord squeezed ~23 %
to the groove depth (area conserved, so it widens into the groove's spare
width). That is exactly flush with the rim top, which is what lets the seated
lid close flat onto the rim.
"""

from __future__ import annotations

import math

from build123d import (
    BuildPart,
    BuildSketch,
    Color,
    Ellipse,
    Locations,
    Part,
    Plane,
    RectangleRounded,
    sweep,
)

from . import config as c

GASKET_COLOR = Color(0.12, 0.12, 0.14)  # black silicone


def seated() -> Part:
    """The cord in the groove, compressed by the lid: flush with the rim top."""
    centerline_x = c.installable_x() + 2 * c.GASKET_INSET
    centerline_y = c.installable_y() + 2 * c.GASKET_INSET
    r = (c.CORNER_R - c.WALL) + c.GASKET_INSET

    # Squeezed from a circle to an ellipse of the same area (pi*a*b), groove-
    # depth tall. Real cord fills the groove corners; the ellipse is 0.1 mm
    # wider than the groove, which no one can see in a visual mock.
    area = math.pi * (c.GASKET_CORD / 2) ** 2
    half_h = c.GASKET_GROOVE_D / 2
    half_w = area / (math.pi * half_h)
    z = c.INTERIOR_Z - half_h

    with BuildSketch(Plane.XY) as outline:
        RectangleRounded(centerline_x, centerline_y, r)
    path = outline.faces()[0].outer_wire()

    with BuildPart() as bp:
        # Plane.XZ: sketch x -> global X (radial here), sketch y -> global Z.
        with BuildSketch(Plane.XZ):
            with Locations((centerline_x / 2, z)):
                Ellipse(half_w, half_h)
        sweep(path=path)

    part = bp.part
    part.label = "gasket"
    part.color = GASKET_COLOR
    return part


def create() -> Part:
    """Entry point for ``uv run show led_psu_enclosure.gasket``."""
    return seated()


__all__ = ["create", "seated"]
