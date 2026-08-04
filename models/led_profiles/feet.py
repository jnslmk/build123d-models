"""Small feet: the same cradle, different backs.

``create_eye_foot()``  -- two Ø6.6 holes for bought M6 eye bolts, for wire
                          suspension. **Through-bolts, not heat-set inserts**:
                          an insert pulls out under a shock load and a
                          through-bolt with a penny washer and a nyloc cannot.
``create_wall_foot()`` -- two Ø5.5 holes for M5 screws into a wall or ceiling.

Both carry two holes rather than one, deliberately. A single hang point offset
to one side twists the tube about its own axis and turns the beam; a symmetric
pair holds it square. Either take one wire each side in a V, or bolt through
both.

The pads sit outboard of ``13.5`` mm, which is clear of the bore at every
height, so a vertical hole through them can never break into the tube's space.

Print pose, both: back on the bed, cradle opening up. Same as everything else
in the family.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Color,
    Cylinder,
    Locations,
    Mode,
    Part,
    Pos,
    add,
)

from models.lib.edges import as_part, chamfer_edge

from . import mount_config as m
from .cradle import create_cradle

PAD_U_IN = 13.5  # clear of the bore, whose widest half is 13.04
PAD_U_OUT = 26.0
PAD_LEN = 22.0
HOLE_U = 20.0

EYE_HOLE_D = 6.6  # M6 eye bolt
EYE_CBORE_D = 12.0  # nyloc + washer, reached from the open side
WALL_HOLE_D = 5.5  # M5 into the wall
WALL_CBORE_D = 10.0

FOOT_COLOR = Color(0.30, 0.32, 0.36)


def _create_foot(hole_d: float, cbore_d: float, label: str) -> Part:
    """A cradle with two bolt pads on its flanks."""
    base = create_cradle()
    mid = m.CRADLE_LEN / 2

    with BuildPart() as bp:
        add(base)
        pad_w = PAD_U_OUT - PAD_U_IN
        for side in (-1, 1):
            with Locations((mid, side * (PAD_U_IN + pad_w / 2), 0)):
                Box(
                    PAD_LEN,
                    pad_w,
                    m.CRADLE_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        for side in (-1, 1):
            with Locations((mid, side * HOLE_U, 0)):
                Cylinder(
                    hole_d / 2,
                    m.CRADLE_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            # Counterbore from the open side, so the nut is reachable with the
            # tube out and the bolt head lands on the back face against the wall.
            with Locations((mid, side * HOLE_U, m.CRADLE_DEPTH)):
                Cylinder(
                    cbore_d / 2,
                    m.CRADLE_DEPTH * 0.45,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
        chamfer_edge(
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), m.EDGE_CHAMFER
        )

    part = bp.part
    part.color = FOOT_COLOR
    part.label = label
    return part


def create_eye_foot() -> Part:
    """Suspension foot: two M6 through-holes for bought eye bolts."""
    return _create_foot(EYE_HOLE_D, EYE_CBORE_D, "eye foot")


def create_wall_foot() -> Part:
    """Wall or ceiling foot: two M5 clearance holes."""
    return _create_foot(WALL_HOLE_D, WALL_CBORE_D, "wall foot")


def seated(x: float = 0.0, foot: Part | None = None) -> Part:
    """A foot moved onto a tube running along +X, near end of its cradle at ``x``.

    House rule: the foot is authored in its print pose (back on the bed,
    cradle opening +Z, near end on its own x=0); the assembly is what moves
    it. Mount-local z is measured from the bed and the tube's underside sits
    ``mount_config.TUBE_UNDER_Z`` above that -- the same convention
    ``checks.py::_mount_pose`` uses -- so dropping onto the tube is a plain
    z-shift; the cradle already runs along +X, so nothing has to turn.
    Defaults to the eye foot, the one used for the common case (suspension).
    """
    if foot is None:
        foot = create_eye_foot()
    placed = as_part(Pos(x, 0, -m.TUBE_UNDER_Z) * foot)
    placed.color = foot.color
    placed.label = foot.label
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.feet``."""
    return create_eye_foot()


__all__ = ["create", "create_eye_foot", "create_wall_foot", "seated"]
