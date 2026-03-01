"""Rounded L-shaped door latch that pivots around a screw hole."""

from build123d import Axis, Box, BuildPart, Cylinder, Locations, Mode, Part, fillet

LATCH_LENGTH = 78.0
ARM_WIDTH = 20.0
THICKNESS = 10.0
BEND_START = 65.0
HOOK_LENGTH = 20.0
PIVOT_HOLE_DIAMETER = 3.5
PIVOT_INSET = 10.0
OUTER_FILLET_RADIUS = 4.0


def create() -> Part:
    """Create a printable rounded L-shaped pivoting door latch."""
    with BuildPart() as builder:
        # Main arm (x from 0 to LATCH_LENGTH, y from -ARM_WIDTH/2 to +ARM_WIDTH/2)
        with Locations((LATCH_LENGTH / 2, 0, 0)):
            Box(LATCH_LENGTH, ARM_WIDTH, THICKNESS)

        # Hook leg extends on one side to form the L profile.
        hook_center_x = LATCH_LENGTH - HOOK_LENGTH / 2
        hook_center_y = ARM_WIDTH
        with Locations((hook_center_x, hook_center_y, 0)):
            Box(HOOK_LENGTH, ARM_WIDTH, THICKNESS)

        # Through-hole for pivot screw.
        with Locations((PIVOT_INSET, 0, 0)):
            Cylinder(PIVOT_HOLE_DIAMETER / 2, THICKNESS * 2, mode=Mode.SUBTRACT)

        # Round external vertical corners for a softer latch profile.
        vertical_edges = list(builder.edges().filter_by(Axis.Z))
        if vertical_edges:
            fillet(vertical_edges, radius=OUTER_FILLET_RADIUS)

    return builder.part
