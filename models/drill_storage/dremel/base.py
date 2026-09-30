"""1×2 ASA guide base for the Dremel TPU cartridge and PETG cover."""

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage import config as family
from models.drill_storage.box import (
    BASE_H,
    CORNER_R,
    FOOT_C1,
    FOOT_C3,
    FOOT_STRAIGHT,
    GRID,
    PAD,
    SNAP_GROOVE_D,
    SNAP_GROOVE_FLOOR,
    SNAP_GROOVE_ROOF,
    SNAP_TIP_FLAT,
    SNAP_Z,
)
from models.lib.edges import top_chamfer_tool
from . import config as c

IS_ASSEMBLY = False
PARAMS = []
GUIDE_MOUTH_CH = family.GUIDE_MOUTH_CH


def _cover_groove():
    """Cut the family's ramped snap groove around a rectangular collar."""
    bottom = c.SEAT_Z + SNAP_Z - SNAP_GROOVE_FLOOR
    top = c.SEAT_Z + SNAP_Z + SNAP_GROOVE_ROOF
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(bottom)):
            RectangleRounded(
                c.COLLAR_X + 0.02, c.COLLAR_Y + 0.02, c.COLLAR_CORNER + 0.01
            )
        extrude(amount=top - bottom)
        sections = []
        for z, inset in (
            (bottom, 0),
            (c.SEAT_Z + SNAP_Z - SNAP_TIP_FLAT / 2, SNAP_GROOVE_D),
            (c.SEAT_Z + SNAP_Z + SNAP_TIP_FLAT / 2, SNAP_GROOVE_D),
            (top, 0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.COLLAR_X - 2 * inset,
                    c.COLLAR_Y - 2 * inset,
                    c.COLLAR_CORNER - inset,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True, mode=Mode.SUBTRACT)
    return tool.part


def _insert_groove():
    """A 45-degree-roofed receiver for the TPU cartridge's outward bead."""
    bottom = family.BEAD_Z - family.GROOVE_FLOOR - 0.05  # ease the TPU bead's ramp foot
    top = family.BEAD_Z + family.GROOVE_ROOF
    with BuildPart() as tool:
        sections = []
        for z, outward in (
            (bottom, 0.01),
            (family.BEAD_Z - family.GROOVE_TIP_FLAT / 2, family.GROOVE_D),
            (family.BEAD_Z + family.GROOVE_TIP_FLAT / 2, family.GROOVE_D),
            (top, 0.01),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.CAVITY_X + 2 * outward,
                    c.CAVITY_Y + 2 * outward,
                    c.CAVITY_CORNER + outward,
                )
                # An annular profile stays one solid through both ramp and roof.
                RectangleRounded(
                    c.CAVITY_X - 0.02,
                    c.CAVITY_Y - 0.02,
                    c.CAVITY_CORNER - 0.01,
                    mode=Mode.SUBTRACT,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return tool.part


def create():
    """Return the feet-down rigid base with 55 free guides and a TPU cavity."""
    with BuildPart() as base:
        for center_y in (-GRID / 2, GRID / 2):
            sections = []
            for z, inset in (
                (0, FOOT_C1 + FOOT_C3),
                (FOOT_C1, FOOT_C3),
                (FOOT_C1 + FOOT_STRAIGHT, FOOT_C3),
                (BASE_H, 0),
            ):
                with BuildSketch(Plane.XY.offset(z)) as section:
                    with Locations((0, center_y)):
                        RectangleRounded(
                            PAD - 2 * inset, PAD - 2 * inset, CORNER_R - inset
                        )
                sections.append(section.sketch)
            loft(sections=sections, ruled=True)

        # Keep the shoulder at the family's 24 mm seat. The cover's rim lands
        # on this flat face, rather than on a bevel or the collar groove.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(c.BODY_X, c.BODY_Y, CORNER_R)
        extrude(amount=c.SEAT_Z - BASE_H)
        with BuildSketch(Plane.XY.offset(c.SEAT_Z)):
            RectangleRounded(c.COLLAR_X, c.COLLAR_Y, c.COLLAR_CORNER)
        extrude(amount=c.BASE_TOP_Z - c.SEAT_Z)
        add(_cover_groove(), mode=Mode.SUBTRACT)
        add(
            top_chamfer_tool(
                c.COLLAR_X,
                c.COLLAR_Y,
                c.COLLAR_CORNER,
                c.BASE_TOP_Z,
                family.SHELL_TOP_CHAMFER,
            ),
            mode=Mode.SUBTRACT,
        )

        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            RectangleRounded(c.CAVITY_X, c.CAVITY_Y, c.CAVITY_CORNER)
        extrude(amount=c.BASE_TOP_Z - c.CAVITY_FLOOR_Z + 0.1, mode=Mode.SUBTRACT)
        add(_insert_groove(), mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(c.BASE_TOP_Z - family.CAVITY_MOUTH_CH)) as low:
            RectangleRounded(c.CAVITY_X, c.CAVITY_Y, c.CAVITY_CORNER)
        with BuildSketch(Plane.XY.offset(c.BASE_TOP_Z + 0.01)) as high:
            ch = family.CAVITY_MOUTH_CH + 0.01
            RectangleRounded(
                c.CAVITY_X + 2 * ch, c.CAVITY_Y + 2 * ch, c.CAVITY_CORNER + ch
            )
        loft(sections=[low.sketch, high.sketch], ruled=True, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(c.GUIDE_FLOOR_Z)):
            for x, y, diameter in c.CUT_BORES:
                with Locations((x, y)):
                    Circle((diameter + family.GUIDE_FIT) / 2)
        extrude(amount=c.CAVITY_FLOOR_Z - c.GUIDE_FLOOR_Z + 0.01, mode=Mode.SUBTRACT)
        for x, y, diameter in c.CUT_BORES:
            guide_r = (diameter + family.GUIDE_FIT) / 2  # free ASA guide
            with Locations((x, y, c.CAVITY_FLOOR_Z - GUIDE_MOUTH_CH)):
                Cone(
                    guide_r,
                    guide_r + GUIDE_MOUTH_CH,
                    GUIDE_MOUTH_CH + 0.01,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
    result = base.part
    result.color = family.SHELL_COLOR
    return result
