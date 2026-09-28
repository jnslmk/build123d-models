"""Foot-down, side-removable PETG shell, bed and forward Gridfinity feet."""

from build123d import (
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Plane,
    Pos,
    RectangleRounded,
    add,
    extrude,
    loft,
)
from models.lib.edges import as_part
from models.lib.fits import SLIDING
from .box import BASE_H, CORNER_R, GRID, HEIGHT_UNIT, PAD, gridfinity_foot
from .sets import DrillSet
from .sideways import (
    BED_THICKNESS,
    FRONT_CORNER_R,
    cover_detent,
    engrave_set_name,
    layout_for,
    stacking_receiver,
)

WALL = 1.0  # PETG: two perimeters plus slicer reserve
SEAM = SLIDING  # axial running clearance between guide face and cover
ROOF = 1.0
MOUTH_LEAD = 0.2  # matching 45-degree PETG entry bevel for the ASA collar


def create_cover_for(drills: DrillSet):
    """Return the foot-down cover; slicer supports its long roof."""
    cells, _positions = layout_for(drills)
    length = cells * GRID - (GRID - PAD)
    rear = -length / 2
    front = length / 2
    height = 5 * HEIGHT_UNIT
    shell_rear = rear + GRID + SEAM  # leave the rear socket and roof on the ASA half
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
        # Flare the inside of the open shell, leaving 0.8 mm PETG at the
        # narrowest entry rim; the male ASA collar has its own lead-in.
        with BuildPart() as mouth:
            middle_z = (bed_top - 0.02 + height - ROOF) / 2
            cavity_h = height - ROOF - bed_top + 0.02
            with BuildSketch(Plane.XZ.offset(-(shell_rear - 0.16))):
                with Locations((0, middle_z)):
                    RectangleRounded(
                        PAD - 2 * WALL + 2 * MOUTH_LEAD,
                        cavity_h + 2 * MOUTH_LEAD,
                        0.4,
                    )
            with BuildSketch(Plane.XZ.offset(-(shell_rear + MOUTH_LEAD))):
                with Locations((0, middle_z)):
                    RectangleRounded(PAD - 2 * WALL, cavity_h, 0.2)
            loft(ruled=True)
        add(mouth.part, mode=Mode.SUBTRACT)
        # One shallow ramped bead mates with the ASA floor groove; the 1.6 mm
        # PETG bed supports it without thinning the long side walls.
        add(cover_detent(rear, groove=False))
        # Each forward foot has its own 4.4 mm receiver above the 5U roof.
        # Its floor remains the original roof, so no socket cuts into the bits.
        for index in range(1, cells):
            add(stacking_receiver(rear + PAD / 2 + index * GRID, height))

        # The ASA guide's wide, relieved collar enters the open end of this
        # shell. The existing cavity locates it without a separate rail/sleeve.
        engrave_set_name(
            drills.label,
            Plane(
                origin=(PAD / 2, (shell_rear + front) / 2, height / 2),
                x_dir=(0, 1, 0),
                z_dir=(1, 0, 0),
            ),
        )
    return cover.part
