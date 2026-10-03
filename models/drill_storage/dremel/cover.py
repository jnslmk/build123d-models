"""Translucent PETG 1×2 cover for the Dremel guide base and TPU cartridge."""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Mode,
    Plane,
    RectangleRounded,
    Text,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
)

from models.lib.gridfinity import CORNER_R
from models.drill_storage.box import (
    COVER_SEAT_CH,
    INNER_R,
    MOUTH_CH,
    SNAP_BACK,
    SNAP_LEAD_IN,
    SNAP_TIP_FLAT,
    SNAP_Z,
    TOP_FILLET,
    cover_height_for,
)
from models.drill_storage.tools import COVER_GLASS
from models.lib.edges import fillet_edge, reseat_on_bed
from . import config as c

IS_ASSEMBLY = False
PARAMS = []
CAP_H = 2.0  # ten fully solid 0.2 mm layers over the 1×2 cover plate
# The smooth cover keeps its accepted 10U height; only the stackable option shrinks.
HEIGHT = cover_height_for(50, bore_floor_z=8.0, cap_h=CAP_H)
SNAP_REACH = 0.38  # radial: <1% nominal PETG strain crossing the ASA collar
INNER_CORNER = INNER_R
LABEL_DEPTH = 0.2  # shallow lettering preserves most of the 0.95 mm PETG wall


def _snap_bead():
    """Ramped internal detent with the family's vertical snap profile."""
    with BuildPart() as bead:
        sections = []
        for z, reach in (
            (SNAP_Z - SNAP_LEAD_IN, 0.01),
            (SNAP_Z - SNAP_TIP_FLAT / 2, SNAP_REACH),
            (SNAP_Z + SNAP_TIP_FLAT / 2, SNAP_REACH),
            (SNAP_Z + SNAP_BACK, 0.01),
        ):
            with BuildSketch(Plane.XY.offset(z)) as section:
                RectangleRounded(
                    c.COVER_INNER_X + 0.02,
                    c.COVER_INNER_Y + 0.02,
                    INNER_CORNER + 0.01,
                )
                RectangleRounded(
                    c.COVER_INNER_X - 2 * reach,
                    c.COVER_INNER_Y - 2 * reach,
                    INNER_CORNER - reach,
                    mode=Mode.SUBTRACT,
                )
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return bead.part


def _create(height: float):
    """Build the common labelled snap cover at its variant's print height."""
    with BuildPart() as cover:
        with BuildSketch():
            RectangleRounded(c.COVER_X, c.COVER_Y, CORNER_R)
        extrude(amount=height)
        fillet(cover.edges().group_by(Axis.Z)[-1], TOP_FILLET)
        chamfer(cover.edges().group_by(Axis.Z)[0], COVER_SEAT_CH)

        with BuildSketch():
            RectangleRounded(c.COVER_INNER_X, c.COVER_INNER_Y, INNER_CORNER)
        extrude(amount=height - CAP_H, mode=Mode.SUBTRACT)
        ceiling_z = height - CAP_H
        ceiling = cover.edges().filter_by_position(Axis.Z, ceiling_z, ceiling_z)
        if ceiling and not fillet_edge(cover, ceiling, 1.0):
            raise RuntimeError("cannot soften the cover's inner ceiling")

        with BuildSketch() as opening:
            RectangleRounded(
                c.COVER_INNER_X + 2 * MOUTH_CH,
                c.COVER_INNER_Y + 2 * MOUTH_CH,
                INNER_CORNER + MOUTH_CH,
            )
        with BuildSketch(Plane.XY.offset(MOUTH_CH)) as bore:
            RectangleRounded(c.COVER_INNER_X, c.COVER_INNER_Y, INNER_CORNER)
        loft(sections=[opening.sketch, bore.sketch], ruled=True, mode=Mode.SUBTRACT)
        add(_snap_bead())

        # Read across the long +X wall while the holder stands foot-down.
        label_plane = Plane(
            origin=(c.COVER_X / 2, 0, height / 2),
            x_dir=(0, 1, 0),
            z_dir=(1, 0, 0),
        )
        with BuildSketch(label_plane):
            Text("DREMEL", font_size=11)
        extrude(amount=-LABEL_DEPTH, mode=Mode.SUBTRACT)

    result = reseat_on_bed(cover.part, flip=True)
    result.color = COVER_GLASS
    return result


def create():
    """Return the smooth labelled cover pillow-down, hollow mouth up."""
    return _create(HEIGHT)
