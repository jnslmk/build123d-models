"""The snap-in lid: a flush plate with a plug skirt that clicks into the mouth.

No flange, no screws. The plate's sides sit flush with the tray walls, the
skirt drops **into** the mouth, and a triangular bead around the skirt snaps
into a groove in the rim band's inner face. The gasket cord sits in a groove in
the rim top and is pressed by the plate's flat underside.

The honest trade-off, since the old screw-down lid's docstring made the case
for screws: fourteen screws could crush a 3 mm cord to its design compression
over a ~700 mm perimeter; one perimeter bead cannot. With the plug labyrinth in
front of it the joint is still a sound dust/splash seal -- it is just not the
screwed-down crush, and the README says so.

Modelled in use orientation (plate up, skirt down) and returned **flipped** into
print pose, so the weather face is the smooth first layer on the bed and the
skirt points up needing no support.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Rotation,
    add,
    extrude,
    loft,
)

from . import config as c
from .util import as_part
from .util import bottom_chamfer_tool, top_chamfer_tool

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

# The plug enters the mouth with a running clearance; the bead then protrudes
# past the mouth face by exactly the snap engagement (BEAD - PLUG_CLEAR).
SKIRT_X = c.installable_x() - 2 * c.LID_PLUG_CLEAR
SKIRT_Y = c.installable_y() - 2 * c.LID_PLUG_CLEAR
PLUG_R = (c.CORNER_R - c.WALL) - c.LID_PLUG_CLEAR


def _build_lid_use_pose() -> Part:
    """The lid as it sits on the box: plate z=0..LID_T, skirt z=-LID_PLUG_H..0."""
    with BuildPart() as bp:
        # --- Plate: flush with the tray walls, pressing the gasket ------------
        with BuildSketch(Plane.XY):
            RectangleRounded(c.outer_x(), c.outer_y(), c.CORNER_R)
        extrude(amount=c.LID_T)

        # --- Plug skirt, reaching into the mouth ------------------------------
        with BuildSketch(Plane.XY.offset(-c.LID_PLUG_H)):
            RectangleRounded(SKIRT_X, SKIRT_Y, PLUG_R)
            RectangleRounded(
                SKIRT_X - 2 * c.LID_PLUG_T,
                SKIRT_Y - 2 * c.LID_PLUG_T,
                max(PLUG_R - c.LID_PLUG_T, 0.5),
                mode=Mode.SUBTRACT,
            )
        extrude(amount=c.LID_PLUG_H)

        # --- Snap bead: a triangular ridge, so it ramps in AND back out -------
        # Every sketch is a RING: a filled profile would plug the skirt's bore.
        z = -c.SNAP_BEAD_Z
        h = c.SNAP_BEAD_H / 2
        bore = (
            SKIRT_X - 2 * c.LID_PLUG_T,
            SKIRT_Y - 2 * c.LID_PLUG_T,
            max(PLUG_R - c.LID_PLUG_T, 0.5),
        )
        with BuildSketch(Plane.XY.offset(z - h)):
            RectangleRounded(SKIRT_X, SKIRT_Y, PLUG_R)
            RectangleRounded(*bore, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(z)):
            RectangleRounded(
                SKIRT_X + 2 * c.SNAP_BEAD,
                SKIRT_Y + 2 * c.SNAP_BEAD,
                PLUG_R + c.SNAP_BEAD,
            )
            RectangleRounded(*bore, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(z + h)):
            RectangleRounded(SKIRT_X, SKIRT_Y, PLUG_R)
            RectangleRounded(*bore, mode=Mode.SUBTRACT)
        loft(ruled=True)

        # --- Edges -------------------------------------------------------------
        # Weather face (and the bed face once flipped). Boolean, not the OCC
        # edge op -- booleans cannot fail the way edge ops do.
        add(
            top_chamfer_tool(
                c.outer_x(), c.outer_y(), c.CORNER_R, c.LID_T, c.RING_CHAMFER
            ),
            mode=Mode.SUBTRACT,
        )
        # Lead-in on the skirt foot so the plug funnels into the mouth.
        add(
            bottom_chamfer_tool(SKIRT_X, SKIRT_Y, PLUG_R, -c.LID_PLUG_H, c.LEAD_IN),
            mode=Mode.SUBTRACT,
        )

    return bp.part


def create_lid() -> Part:
    """The lid in print pose: weather face on the bed, skirt pointing up."""
    flipped = as_part(Rotation(180, 0, 0) * _build_lid_use_pose())
    part = as_part(Pos(0, 0, -flipped.bounding_box().min.Z) * flipped)
    part.label = "lid"
    return part


def seated() -> Part:
    """The lid in its closed position, for the assembled view."""
    part = as_part(Pos(0, 0, c.INTERIOR_Z) * _build_lid_use_pose())
    part.label = "lid"
    return part


def create() -> Part:
    """Entry point for ``uv run show led_psu_enclosure.lid``."""
    return create_lid()


__all__ = ["create", "create_lid", "seated"]
