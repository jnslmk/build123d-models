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

from models.lib.checks import Report, is_solid_at, sharp_convex_edges

# The absolute minimum a 0.4 mm nozzle resolves: 2 perimeters. Below this a
# feature does not slice as a wall or a gap, it merges with its neighbour.
MIN_WALL = 0.8

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


def check() -> Report:
    """Geometry assertions for the door latch plate: outer envelope, the
    through-slot's position and width, slot/web minimums against a 0.4 mm
    nozzle, print pose, and the house edge rule.
    """
    r = Report()
    part = create()
    bb = part.bounding_box()

    r.section("envelope")
    r.check(
        abs(bb.size.X - PLATE_WIDTH) < 1e-6,
        "plate width matches PLATE_WIDTH",
        f"{bb.size.X:.3f} mm",
    )
    r.check(
        abs(bb.size.Z - PLATE_HEIGHT) < 1e-6,
        "plate height matches PLATE_HEIGHT",
        f"{bb.size.Z:.3f} mm",
    )
    r.check(
        abs(bb.size.Y - PLATE_THICKNESS * 2) < 1e-6,
        "plate thickness matches PLATE_THICKNESS (extruded both=True)",
        f"{bb.size.Y:.3f} mm vs {PLATE_THICKNESS * 2:.3f} mm expected",
    )

    r.section("slot")
    slot_center_z = -PLATE_HEIGHT / 2 + SLOT_HEIGHT / 2
    slot_top_z = slot_center_z + SLOT_HEIGHT / 2
    slot_x_lo = SLOT_OFFSET_X - SLOT_WIDTH / 2
    slot_x_hi = SLOT_OFFSET_X + SLOT_WIDTH / 2
    r.check(
        is_solid_at(part, slot_x_lo - 0.5, 0, slot_center_z),
        "material remains just left of the slot (pins the left edge)",
        f"probed x={slot_x_lo - 0.5:.1f}",
    )
    r.check(
        not is_solid_at(part, slot_x_lo + 0.5, 0, slot_center_z)
        and not is_solid_at(part, slot_x_hi - 0.5, 0, slot_center_z),
        "slot is open across its full designed width (SLOT_WIDTH)",
        f"x in [{slot_x_lo:.1f}, {slot_x_hi:.1f}], probed 0.5 mm inside each edge",
    )
    r.check(
        not is_solid_at(part, SLOT_OFFSET_X, 0, -PLATE_HEIGHT / 2 + 0.1),
        "slot is open at the plate's bottom edge (open-ended by design)",
        f"probed z={-PLATE_HEIGHT / 2 + 0.1:.2f}",
    )
    r.check(
        is_solid_at(part, -(PLATE_WIDTH / 2 - 7), 0, -PLATE_HEIGHT / 2 + 0.1),
        "plate is solid along the same bottom edge, away from the slot",
        "probed the left side, clear of the rounded corner and the slot",
    )
    r.check(
        is_solid_at(part, SLOT_OFFSET_X, 0, slot_top_z + 1),
        "slot is closed above SLOT_HEIGHT (not open all the way to the top)",
        f"probed z={slot_top_z + 1:.1f}",
    )

    r.section("wall and slot minimums (0.4 mm nozzle, 2 perimeters)")
    left_web = slot_x_lo - (-PLATE_WIDTH / 2)
    r.check(
        left_web >= MIN_WALL,
        "web left of the slot clears the printable minimum",
        f"{left_web:.2f} mm (min {MIN_WALL})",
    )
    r.check(
        SLOT_WIDTH >= 2 * MIN_WALL,
        "slot itself is wide enough to print as an open feature",
        f"{SLOT_WIDTH:.2f} mm (min {2 * MIN_WALL})",
    )

    r.section("print pose")
    r.check(
        abs(bb.min.Z) < 1e-6,
        "part sits on the build plate (min z = 0)",
        f"min z = {bb.min.Z:.3f} mm -- create() never re-seats the part after "
        "the symmetric extrude",
    )

    r.section("sharp edges")
    bad = sharp_convex_edges(part)
    r.check(
        not bad,
        "no unexplained sharp convex edges (chamfer horizontal, fillet vertical)",
        f"{len(bad)} found -- the flat front/back faces and the slot's own "
        "top corners (SLOT_FILLET is declared but never applied) are "
        "unchamfered"
        if bad
        else "none",
    )

    return r
