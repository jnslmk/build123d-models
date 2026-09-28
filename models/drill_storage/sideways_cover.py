"""Foot-down, side-removable PETG shell, bed and forward Gridfinity feet."""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    add,
    extrude,
    loft,
)
from models.lib.edges import as_part
from models.lib.fits import SLIDING, SNUG
from .box import BASE_H, CORNER_R, GRID, HEIGHT_UNIT, PAD, gridfinity_foot
from .sets import DrillSet
from .sideways import (
    BACK_WALL,
    BED_THICKNESS,
    FRONT_CORNER_R,
    GUIDE_DEPTH,
    RAIL_X,
    layout_for,
)

WALL = 1.0  # PETG: two perimeters plus slicer reserve
SEAM = SLIDING  # axial running clearance between guide face and cover
ROOF = 1.0
JOINT_FIT = SNUG  # PETG-on-ASA hand-removable friction fit; calibrate on prints
TONGUE_WIDTH = 4.9  # 0.8 mm cheeks at the widened groove
TONGUE_HEIGHT = 2.5
TONGUE_START = BACK_WALL + GUIDE_DEPTH + 0.5
TONGUE_END = GRID + 1.5
GROOVE_END = GRID - 0.5


def create_cover_for(drills: DrillSet):
    """Return the cover in foot-down print pose; slicer supports its roof and tongue."""
    cells, _positions = layout_for(drills)
    length = cells * GRID - (GRID - PAD)
    rear = -length / 2
    front = length / 2
    height = 5 * HEIGHT_UNIT
    shell_rear = rear + BACK_WALL + GUIDE_DEPTH + SEAM
    shell_length = front - shell_rear
    bed_rear = rear + GRID
    bed_length = front - bed_rear
    bed_top = BASE_H + BED_THICKNESS
    with BuildPart() as cover:
        # Feet are separate Gridfinity cells, linked by the continuous raised bed.
        for index in range(1, cells):
            y = rear + PAD / 2 + index * GRID
            add(as_part(Pos(0, y, 0) * gridfinity_foot()))
        with BuildSketch(Plane.XY.offset(BASE_H)):
            with Locations((0, (bed_rear + front) / 2)):
                RectangleRounded(PAD, bed_length, CORNER_R)
        extrude(amount=BED_THICKNESS)

        # Square up the receiving end where wide bits approach the X edges;
        # the three loft sections chamfer the entire outer roof perimeter.
        with BuildPart() as shell:
            shell_sections = []
            for z, inset in ((bed_top, 0.0), (height - 0.2, 0.0), (height, 0.2)):
                with BuildSketch(Plane.XY.offset(z)) as section:
                    with Locations((0, (shell_rear + front) / 2)):
                        RectangleRounded(
                            PAD - 2 * inset,
                            shell_length - 2 * inset,
                            CORNER_R - inset,
                        )
                    with Locations((0, shell_rear + 2)):
                        RectangleRounded(
                            PAD - 2 * inset,
                            4 - 2 * inset,
                            FRONT_CORNER_R - inset,
                        )
                shell_sections.append(section.sketch)
            loft(sections=shell_sections, ruled=True)
        add(shell.part)
        with BuildSketch(Plane.XY.offset(bed_top - 0.02)):
            inner_front = front - WALL
            with Locations((0, (shell_rear - 0.1 + inner_front) / 2)):
                RectangleRounded(
                    PAD - 2 * WALL,
                    inner_front - shell_rear + 0.1,
                    CORNER_R - WALL,
                )
            with Locations((0, shell_rear + 1.9)):
                RectangleRounded(PAD - 2 * WALL, 4.1, FRONT_CORNER_R)
        extrude(amount=height - ROOF - bed_top + 0.02, mode=Mode.SUBTRACT)

        # PETG sleeve over the guide's ASA rail. Two-perimeter cheeks and a
        # located friction fit constrain X/Z; the blind end limits insertion.
        tongue_rear = rear + TONGUE_START
        tongue_front = rear + TONGUE_END
        with Locations(
            (RAIL_X, (tongue_rear + tongue_front) / 2, bed_top + SLIDING / 2)
        ):
            Box(
                TONGUE_WIDTH,
                tongue_front - tongue_rear,
                TONGUE_HEIGHT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with BuildSketch(Plane.XZ.offset(-(tongue_rear - 0.01))):
            Polygon(
                (RAIL_X - 1.0 - JOINT_FIT / 2, bed_top - 0.1),
                (RAIL_X + 1.0 + JOINT_FIT / 2, bed_top - 0.1),
                (RAIL_X + 1.6 + JOINT_FIT / 2, bed_top + 0.9),
                (RAIL_X + 1.6 + JOINT_FIT / 2, bed_top + 1.7),
                (RAIL_X - 1.6 - JOINT_FIT / 2, bed_top + 1.7),
                (RAIL_X - 1.6 - JOINT_FIT / 2, bed_top + 0.9),
                align=None,
            )
        extrude(amount=-(rear + GROOVE_END - tongue_rear + 0.01), mode=Mode.SUBTRACT)
        # Bond the overhanging sleeve to the deck; its underside running gap
        # otherwise leaves it as a separate solid.
        with Locations((RAIL_X, rear + (GROOVE_END + TONGUE_END) / 2, bed_top - 0.1)):
            Box(
                TONGUE_WIDTH,
                TONGUE_END - GROOVE_END,
                TONGUE_HEIGHT + SLIDING / 2 + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    return cover.part
