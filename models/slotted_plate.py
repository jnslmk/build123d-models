"""Door latch plate - rectangular plate with slot and tapered entry ramp."""

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    RectangleRounded,
    extrude,
)

# Plate dimensions
PLATE_WIDTH = 50.0
PLATE_HEIGHT = 40.0
PLATE_THICKNESS = 3.0

# Slot dimensions (offset to the right, open at bottom)
SLOT_WIDTH = 8.0
SLOT_HEIGHT = 25.0
SLOT_OFFSET_X = 10.0  # offset to the right from center

# Taper ramp on right side of slot (for slide-in latch action)
TAPER_WIDTH = 10.0  # horizontal extent of the taper

# Finishing
CORNER_RADIUS = 3.0  # rounded corners on outer plate
SLOT_FILLET = 1.5  # fillet at top corners of slot


def create() -> Part:
    """Create a door latch plate with slot and tapered entry ramp."""
    with BuildPart() as builder:
        # Main plate with rounded corners (sketch on XZ plane for vertical plate)
        with BuildSketch(Plane.XZ):
            RectangleRounded(PLATE_WIDTH, PLATE_HEIGHT, CORNER_RADIUS)
        extrude(amount=PLATE_THICKNESS, both=True)

        # Cut the slot from bottom, offset to the right
        # Use a rounded rectangle for the slot to get nice fillets at top corners
        slot_center_z = -PLATE_HEIGHT / 2 + SLOT_HEIGHT / 2
        with Locations((SLOT_OFFSET_X, 0, slot_center_z)):
            Box(SLOT_WIDTH, PLATE_THICKNESS * 2, SLOT_HEIGHT, mode=Mode.SUBTRACT)

        # Tapered ramp on the right side of the slot
        # Creates an angled cut so a latch can slide in from the right
        # and drop into the slot. The ramp goes from back face at slot edge
        # to front face at outer edge (full thickness on right, tapers to slot)
        slot_right_edge = SLOT_OFFSET_X + SLOT_WIDTH / 2
        taper_end_x = slot_right_edge + TAPER_WIDTH
        front_y = PLATE_THICKNESS / 2

        # Create triangular profile in XY plane
        # Triangle: back face at slot edge -> front face at slot edge -> back at outer edge
        # This removes material from the front, creating a ramp from front to back
        with BuildSketch(Plane.XY.offset(-PLATE_HEIGHT / 2)):
            Polygon(
                [
                    (slot_right_edge, -front_y),  # back face at slot edge
                    (slot_right_edge, front_y),  # front face at slot edge
                    (taper_end_x, -front_y),  # back face at outer edge
                ],
                align=None,
            )
        # Extrude upward through slot height
        extrude(amount=SLOT_HEIGHT, mode=Mode.SUBTRACT)

    return builder.part
