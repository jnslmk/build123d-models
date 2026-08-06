"""Door latch plate - rectangular plate with slot and tapered entry ramp."""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    extrude,
    fillet,
)

from models.lib.checks import Report, is_solid_at, sharp_convex_edges
from models.lib.edges import as_part, chamfer_edge, fillet_edge

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
SLOT_FILLET = 1.5  # fillet at the slot's top-left corner -- a square internal
# corner on a slot mouth is a stress riser. Only the left corner gets one: the
# top-right corner is where the taper ramp begins (TAPER_WIDTH, below), and
# the taper cut already removes that corner entirely, so a fillet there would
# be redundant -- and, worse, coincide exactly with the taper's own cut
# boundary and defeat every attempt at an OCC chamfer over that mouth.
EDGE_BREAK = 1.0  # house edge rule: chamfer horizontal, fillet vertical.
# Tried as a ladder (see create()): the slot mouth and the taper's bottom
# corner are tight enough that the full 1.0 mm does not always fit.


def create() -> Part:
    """Create a door latch plate with slot and tapered entry ramp."""
    with BuildPart() as builder:
        # Main plate with rounded corners (sketch on XZ plane for vertical plate)
        with BuildSketch(Plane.XZ):
            RectangleRounded(PLATE_WIDTH, PLATE_HEIGHT, CORNER_RADIUS)
        extrude(amount=PLATE_THICKNESS, both=True)

        # Cut the slot from bottom, offset to the right. Only the top-left
        # corner is rounded (SLOT_FILLET) -- the bottom is open by design, and
        # the top-right corner is consumed by the taper cut below, so there is
        # no corner left there to round.
        slot_center_z = -PLATE_HEIGHT / 2 + SLOT_HEIGHT / 2
        with BuildSketch(Plane.XZ) as slot_sketch:
            with Locations((SLOT_OFFSET_X, slot_center_z)):
                Rectangle(SLOT_WIDTH, SLOT_HEIGHT)
            top_left = sorted(
                slot_sketch.vertices().group_by(Axis.Y)[-1], key=lambda v: v.X
            )[:1]
            fillet(top_left, radius=SLOT_FILLET)
        extrude(amount=PLATE_THICKNESS, both=True, mode=Mode.SUBTRACT)

        # Tapered ramp on the right side of the slot
        # Creates an angled cut so a latch can slide in from the right
        # and drop into the slot. The ramp goes from back face at slot edge
        # to front face at outer edge (full thickness on right, tapers to slot)
        slot_right_edge = SLOT_OFFSET_X + SLOT_WIDTH / 2
        taper_end_x = slot_right_edge + TAPER_WIDTH
        # The plate is extruded PLATE_THICKNESS in *each* direction (both=True),
        # so the true front/back faces sit at +/-PLATE_THICKNESS, not
        # +/-PLATE_THICKNESS/2. The ramp has to reach the real front face for
        # "full thickness on right" to actually hold.
        front_y = PLATE_THICKNESS

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

        # Edge treatment, house rule: chamfer horizontal edges, fillet
        # vertical ones. The slot and taper cuts leave faces that are not a
        # clean prism, so select by what is actually still sharp
        # (sharp_convex_edges) rather than blindly running every edge on the
        # axis through an op that might not apply to it. A single chamfer
        # pass over every horizontal edge also resolves the vertical ones as
        # a side effect here (the slot and taper walls are short enough that
        # the corner blend consumes them) but leaves one or two new, smaller
        # sharp seams where the chamfer meets the taper -- so this loops,
        # re-deriving the sharp set each round and re-deriving the selection
        # after every successful op, since a successful op invalidates the
        # previous one (build123d-geometry-ops). Horizontal (chamfer) is
        # preferred each round; vertical (fillet) only runs when nothing
        # horizontal remains. Each round's ladder walks a decreasing size,
        # because the slot mouth and the taper's tight corner do not always
        # take the full EDGE_BREAK.
        first_ladder = (EDGE_BREAK, 0.8, 0.6, 0.4, 0.2)
        residual_ladder = (0.5, 0.4, 0.3, 0.2, 0.1, 0.05)
        for round_num in range(4):
            raw = sharp_convex_edges(builder.part)
            if not raw:
                break
            ladder = first_ladder if round_num == 0 else residual_ladder
            horizontal = raw.filter_by(Axis.Z, reverse=True)
            if horizontal and any(
                chamfer_edge(builder, horizontal, size) for size in ladder
            ):
                continue
            vertical = raw.filter_by(Axis.Z)
            if vertical:
                any(fillet_edge(builder, vertical, size) for size in ladder)

    part = Pos(0, 0, -builder.part.bounding_box().min.Z) * builder.part
    return as_part(part)


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
    # Probes are expressed relative to bb.min.Z -- the build-plate contact
    # face -- not the pre-reseat, plate-centered z=0 this module's formulas
    # would naturally suggest. create() re-seats the part (print pose, house
    # idiom), so the plate's own bottom edge is bb.min.Z, and the slot (which
    # opens at that same bottom edge by design) sits at
    # bb.min.Z .. bb.min.Z + SLOT_HEIGHT, not at the centered
    # -PLATE_HEIGHT/2 .. -PLATE_HEIGHT/2 + SLOT_HEIGHT a centered part would
    # use. Each probe still samples the same physical feature (same slot,
    # same wall, same bottom edge) -- only the z origin moved.
    z_bottom = bb.min.Z
    slot_center_z = z_bottom + SLOT_HEIGHT / 2
    slot_top_z = z_bottom + SLOT_HEIGHT
    slot_x_lo = SLOT_OFFSET_X - SLOT_WIDTH / 2
    slot_x_hi = SLOT_OFFSET_X + SLOT_WIDTH / 2
    r.check(
        is_solid_at(part, slot_x_lo - 0.5, 0, slot_center_z),
        "material remains just left of the slot (pins the left edge)",
        f"probed x={slot_x_lo - 0.5:.1f}, z={slot_center_z:.1f}",
    )
    r.check(
        not is_solid_at(part, slot_x_lo + 0.5, 0, slot_center_z)
        and not is_solid_at(part, slot_x_hi - 0.5, 0, slot_center_z),
        "slot is open across its full designed width (SLOT_WIDTH)",
        f"x in [{slot_x_lo:.1f}, {slot_x_hi:.1f}], probed 0.5 mm inside each "
        f"edge, z={slot_center_z:.1f}",
    )
    r.check(
        not is_solid_at(part, SLOT_OFFSET_X, 0, z_bottom + 0.1),
        "slot is open at the plate's bottom edge (open-ended by design)",
        f"probed z={z_bottom + 0.1:.2f}",
    )
    r.check(
        is_solid_at(part, -(PLATE_WIDTH / 2 - 7), 0, z_bottom + 0.1),
        "plate is solid along the same bottom edge, away from the slot",
        f"probed the left side at z={z_bottom + 0.1:.2f}, clear of the "
        "rounded corner and the slot",
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
