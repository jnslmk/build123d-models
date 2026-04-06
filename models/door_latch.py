"""Rounded L-shaped door latch that pivots around a screw hole."""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Rectangle,
    extrude,
    fillet,
)

LATCH_LENGTH = 85.0
ARM_WIDTH = 10.0
THICKNESS = 10.0
BEND_START = 75.0
HOOK_LENGTH = 10.0
PIVOT_HOLE_DIAMETER = 3.5
PIVOT_INSET = 5.0
OUTER_FILLET_RADIUS = 4.0


def create() -> Part:
    """Create a printable rounded L-shaped pivoting door latch."""
    with BuildPart() as builder:
        # Main latch footprint with a rounded cap on the short hook end.
        hook_start_x = LATCH_LENGTH - HOOK_LENGTH
        hook_center_y = ARM_WIDTH
        hook_stem_length = max(HOOK_LENGTH - ARM_WIDTH / 2, 0)
        hook_stem_center_x = hook_start_x + hook_stem_length / 2
        hook_cap_center_x = hook_start_x + hook_stem_length

        with BuildSketch():
            with Locations((LATCH_LENGTH / 2, 0)):
                Rectangle(LATCH_LENGTH, ARM_WIDTH)
            if hook_stem_length > 0:
                with Locations((hook_stem_center_x, hook_center_y)):
                    Rectangle(hook_stem_length, ARM_WIDTH)
            with Locations((hook_cap_center_x, hook_center_y)):
                Circle(ARM_WIDTH / 2)
        extrude(amount=THICKNESS / 2, both=True)

        # Through-hole for pivot screw.
        with BuildSketch():
            with Locations((PIVOT_INSET, 0)):
                Circle(PIVOT_HOLE_DIAMETER / 2)
        extrude(amount=THICKNESS, both=True, mode=Mode.SUBTRACT)

        # Round external vertical corners for a softer latch profile.
        vertical_edges = list(builder.edges().filter_by(Axis.Z))
        fillet_edges = []
        for edge in vertical_edges:
            center = edge.center()
            # Exclude stem-to-cap transition edges; they are not valid for this fillet.
            if abs(center.X - hook_cap_center_x) < 1e-7:
                continue
            fillet_edges.append(edge)
        if fillet_edges:
            fillet(fillet_edges, radius=OUTER_FILLET_RADIUS)

    return builder.part
