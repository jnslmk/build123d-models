"""Single-piece 1×2 Gridfinity rack for upright 2.5 mm Dremel shanks."""

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cone,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage.box import (
    BASE_H,
    CORNER_R,
    FOOT_C1,
    FOOT_C3,
    FOOT_STRAIGHT,
    GRID,
    PAD,
)
from models.lib import fits
from models.lib.edges import top_chamfer_tool

IS_ASSEMBLY = False
PARAMS = []

WIDTH = PAD
LENGTH = GRID + PAD
TOP_Z = 21.0  # 3 Gridfinity height units including the foot
FLOOR_Z = 8.0  # 3.6 mm of solid material above the foot
SHANK_D = 2.5
BORE_FIT = fits.FREE  # free fit, PETG baseline; tools lift out by hand
BORE_R = (SHANK_D + BORE_FIT) / 2
PITCH = 7.0
MOUTH_CH = 0.5
TOP_CH = 0.6
POSITIONS = tuple((x * PITCH, y * PITCH) for x in range(-2, 3) for y in range(-5, 6))


def create():
    """Return the support-free, feet-down holder with 55 blind tool bores."""
    with BuildPart() as rack:
        for center_y in (-GRID / 2, GRID / 2):
            # Match the standard drill-storage foot section, twice along Y.
            sections = []
            for z, inset in (
                (0, FOOT_C1 + FOOT_C3),
                (FOOT_C1, FOOT_C3),
                (FOOT_C1 + FOOT_STRAIGHT, FOOT_C3),
                (BASE_H, 0),
            ):
                with BuildSketch(Plane.XY.offset(z)) as profile:
                    with Locations((0, center_y)):
                        RectangleRounded(
                            PAD - 2 * inset, PAD - 2 * inset, CORNER_R - inset
                        )
                sections.append(profile.sketch)
            loft(sections=sections, ruled=True)

        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(WIDTH, LENGTH, CORNER_R)
        extrude(amount=TOP_Z - BASE_H)

        add(
            top_chamfer_tool(WIDTH, LENGTH, CORNER_R, TOP_Z, TOP_CH), mode=Mode.SUBTRACT
        )

        with BuildSketch(Plane.XY.offset(FLOOR_Z)):
            with Locations(*POSITIONS):
                Circle(BORE_R)
        extrude(amount=TOP_Z - FLOOR_Z + 0.1, mode=Mode.SUBTRACT)

        # A shallow printed lead-in opens each vertical bore without an OCC edge op.
        for x, y in POSITIONS:
            with Locations((x, y, TOP_Z - MOUTH_CH)):
                Cone(
                    BORE_R,
                    BORE_R + MOUTH_CH,
                    MOUTH_CH + 0.01,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    result = rack.part
    result.color = Color(0.1, 0.1, 0.1)
    return result
