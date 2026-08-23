"""The wire itself -- not a printed part, a mock-up for the assembly view.

Two strands of a loop, on the path the clamp actually puts them on: in through
the window level with the sill, down past the end of the plunger, flat along the
ribbed floor under it, up the other side and out. Four bends, which is the whole
argument for the slot (see ``config.Clamp.wire_pass``) drawn rather than
written -- the original's round bore admits no such path, and a picture of the
difference is worth the fifty lines.

Schematic, and only that: a real wire under a plunger flattens against the ribs
and takes its bend radii from what it is made of. Nothing here is measured off
anything and nothing else in the package reads these numbers.
"""

from __future__ import annotations

from build123d import (
    BuildLine,
    BuildSketch,
    Circle,
    FilletPolyline,
    Part,
    Plane,
    Pos,
    sweep,
)

from ..lib.edges import as_part

from .config import STRANDS, Clamp

TAIL = 6.0
"""How far the strands stick out of the clamp, each side."""

BEND_R = 0.5
"""Bend radius at the four corners, as drawn."""


def _path_points(c: Clamp) -> list[tuple[float, float]]:
    """The strand's centreline in the (y, z) plane, entry to exit."""
    y_out = c.body_r + TAIL
    y_turn = (c.plunger_r + c.channel_l / 2) / 2
    z_high = c.window_z0 + c.wire_d / 2
    z_low = c.base_t + c.rib_h + c.wire_d / 2
    return [
        (y_out, z_high),
        (y_turn, z_high),
        (y_turn, z_low),
        (-y_turn, z_low),
        (-y_turn, z_high),
        (-y_out, z_high),
    ]


def wire_strands(c: Clamp) -> list[Part]:
    """``STRANDS`` strands, side by side across the slot."""
    gap = c.wire_d + 0.3
    offsets = [(i - (STRANDS - 1) / 2) * gap for i in range(STRANDS)]
    # ``Plane.YZ`` maps a 2D ``(y, z)`` corner straight onto the section this
    # module thinks in, so the path is drawn in the same coordinates as
    # ``_path_points`` writes it.
    with BuildLine(Plane.YZ) as line:
        FilletPolyline(*_path_points(c), radius=BEND_R)
    path = line.line
    with BuildSketch(Plane(origin=path @ 0, z_dir=path % 0)) as section:
        Circle(c.wire_d / 2)
    strand = sweep(sections=section.sketch, path=path, is_frenet=True)
    return [as_part(Pos(dx, 0, 0) * strand) for dx in offsets]
