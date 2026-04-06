"""Wall-mounted linear bar lamp inspired by a double-ended tube sconce."""

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Location,
    Mode,
    Part,
    Plane,
    Polygon,
    RectangleRounded,
    extrude,
    loft,
)

# Diffuser tube
TUBE_OUTER_DIAMETER = 26.0
TUBE_WALL = 1.6
TUBE_HALF_LENGTH = 150.0
TUBE_PEG_DIAMETER = 18.2
TUBE_PEG_LENGTH = 10.0
CENTER_GAP = 0.0

# End cap
END_CAP_BODY_LENGTH = 10.0
END_CAP_LIP_DIAMETER = TUBE_OUTER_DIAMETER - 0.4
END_CAP_LIP_LENGTH = 7.0

# Central wall mount
BACKPLATE_WIDTH = 36.0
BACKPLATE_HEIGHT = 24.0
BACKPLATE_THICKNESS = 3.0
BACKPLATE_RADIUS = 5.0
SHROUD_OUTER_DIAMETER = 31.0
SHROUD_BORE_DIAMETER = 26.4
SHROUD_CENTER_WIDTH = 12.0
SHROUD_TRANSITION_LENGTH = 8.0
BASE_WIDTH = 16.0
BASE_DEPTH = 10.0
BASE_HEIGHT = 11.0
BASE_TOP_INSET = 3.0
CABLE_SLOT_WIDTH = 10.0
CABLE_SLOT_HEIGHT = 6.0

# Print layout spacing
LAYOUT_GAP = 10.0


def create_mount() -> Part:
    """Create a one-piece wall mount with smooth shroud and correctly oriented base."""
    shroud_radius = SHROUD_OUTER_DIAMETER / 2
    bore_radius = SHROUD_BORE_DIAMETER / 2
    tube_radius = TUBE_OUTER_DIAMETER / 2
    half_center_width = SHROUD_CENTER_WIDTH / 2
    end_x = half_center_width + SHROUD_TRANSITION_LENGTH

    with BuildPart() as mount:
        with BuildSketch(Plane.XZ):
            RectangleRounded(BACKPLATE_WIDTH, BACKPLATE_HEIGHT, BACKPLATE_RADIUS)
        extrude(amount=BACKPLATE_THICKNESS, both=True)

        outer_sections = []
        for offset, radius in (
            (-end_x, tube_radius + 0.8),
            (-half_center_width, shroud_radius),
            (half_center_width, shroud_radius),
            (end_x, tube_radius + 0.8),
        ):
            with BuildSketch(Plane.YZ.offset(offset)) as section:
                Circle(radius)
            outer_sections.append(section.sketch)
        loft(outer_sections)

        with BuildSketch(Plane.YZ.offset(-end_x)):
            Circle(bore_radius)
        extrude(amount=2 * end_x, mode=Mode.SUBTRACT)

        base_top_z = -shroud_radius + 1.5
        with BuildSketch(Plane.YZ):
            Polygon(
                [
                    (-BASE_DEPTH / 2, base_top_z),
                    (BASE_DEPTH / 2, base_top_z),
                    (BASE_DEPTH / 2 + BASE_TOP_INSET, base_top_z - BASE_HEIGHT),
                    (-BASE_DEPTH / 2 - BASE_TOP_INSET, base_top_z - BASE_HEIGHT),
                ],
                align=None,
            )
        extrude(amount=BASE_WIDTH, both=True)

        with BuildSketch(Plane.XZ.offset(-BACKPLATE_THICKNESS / 2)):
            RectangleRounded(
                CABLE_SLOT_WIDTH,
                CABLE_SLOT_HEIGHT,
                CABLE_SLOT_HEIGHT / 2 - 0.5,
            )
        extrude(amount=BACKPLATE_THICKNESS, mode=Mode.SUBTRACT)

    mount.part.label = "wall_mount"
    return mount.part


def create_tube() -> Part:
    """Create one half-length diffuser tube with a hollow body and mounting peg."""
    outer_radius = TUBE_OUTER_DIAMETER / 2
    inner_radius = outer_radius - TUBE_WALL
    tube_half = TUBE_HALF_LENGTH / 2

    with BuildPart() as tube:
        with BuildSketch(Plane.YZ.offset(-tube_half)):
            Circle(outer_radius)
            Circle(inner_radius, mode=Mode.SUBTRACT)
        extrude(amount=TUBE_HALF_LENGTH)

        with BuildSketch(Plane.YZ.offset(-tube_half)):
            Circle(TUBE_PEG_DIAMETER / 2)
        extrude(amount=TUBE_PEG_LENGTH)

    return tube.part


def create_end_cap() -> Part:
    """Create a flush-faced plug cap for the diffuser tube ends."""
    body_radius = TUBE_OUTER_DIAMETER / 2

    with BuildPart() as end_cap:
        with BuildSketch(Plane.YZ.offset(-END_CAP_BODY_LENGTH / 2)):
            Circle(body_radius)
        extrude(amount=END_CAP_BODY_LENGTH)

        with BuildSketch(Plane.YZ.offset(-END_CAP_BODY_LENGTH / 2 - END_CAP_LIP_LENGTH)):
            Circle(END_CAP_LIP_DIAMETER / 2)
        extrude(amount=END_CAP_LIP_LENGTH)

    return end_cap.part


def _assemble_components() -> list[Part]:
    """Return individually labeled assembled parts for viewer grouping."""
    mount = create_mount()

    left_tube = create_tube().move(Location((-TUBE_HALF_LENGTH / 2 - CENTER_GAP / 2, 0, 0)))
    left_tube.label = "left_tube"

    right_tube = create_tube().move(Location((TUBE_HALF_LENGTH / 2 + CENTER_GAP / 2, 0, 0)))
    right_tube.label = "right_tube"

    cap_center_offset = TUBE_HALF_LENGTH + END_CAP_BODY_LENGTH / 2

    left_cap = create_end_cap().move(Location((-cap_center_offset - CENTER_GAP / 2, 0, 0)))
    left_cap.label = "left_end_cap"

    right_cap = create_end_cap().move(Location((cap_center_offset + CENTER_GAP / 2, 0, 0)))
    right_cap.label = "right_end_cap"

    return [mount, left_tube, right_tube, left_cap, right_cap]


def create_print_layout() -> Compound:
    """Lay out all lamp parts apart from each other for printing/export."""
    mount = create_mount()
    mount.label = "wall_mount"

    left_tube = create_tube().move(Location((0, 0, BACKPLATE_HEIGHT / 2 + TUBE_OUTER_DIAMETER / 2 + LAYOUT_GAP)))
    left_tube.label = "tube_a"

    right_tube = create_tube().move(Location((0, 0, -(BACKPLATE_HEIGHT / 2 + TUBE_OUTER_DIAMETER / 2 + LAYOUT_GAP))))
    right_tube.label = "tube_b"

    cap_offset_x = TUBE_HALF_LENGTH / 2 + END_CAP_BODY_LENGTH / 2 + LAYOUT_GAP
    cap_offset_z = -BACKPLATE_HEIGHT / 2 - TUBE_OUTER_DIAMETER / 2 - LAYOUT_GAP

    left_cap = create_end_cap().move(Location((-cap_offset_x, 0, cap_offset_z)))
    left_cap.label = "end_cap_a"

    right_cap = create_end_cap().move(Location((cap_offset_x, 0, cap_offset_z)))
    right_cap.label = "end_cap_b"

    return Compound(label="wall_bar_lamp_print_layout", children=[mount, left_tube, right_tube, left_cap, right_cap])


def create() -> Compound:
    """Create the lamp arranged in its final assembled wall-sconce form."""
    return Compound(label="wall_bar_lamp", children=_assemble_components())


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "wall_bar_lamp")


if __name__ == "__main__":
    main()
