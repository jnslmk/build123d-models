"""Flat-print TPU grip cartridge for the horizontal wood/metal guides."""

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Pos,
    RectangleRounded,
    RegularPolygon,
    Rotation,
    Sphere,
    add,
    extrude,
    loft,
)
from models.lib import fits
from models.lib.edges import (
    as_part,
    bottom_chamfer_tool,
    reseat_on_bed,
    top_chamfer_tool,
)

from models.lib.gridfinity import BASE_H, GRID, HEIGHT_UNIT, PAD
from . import config as c
from .box import hex_mouth_tool
from .sets import DrillSet
from .sideways import (
    BACK_WALL,
    GUIDE_DEPTH,
    INSERT_CATCH_R,
    INSERT_CORNER_R,
    INSERT_DEPTH,
    INSERT_WALL,
    layout_for,
)

INSERT_FIT = fits.for_material(fits.SNUG, "tpu")  # snug fit, TPU; total X/Z gap
INSERT_AXIAL_CLEAR = fits.for_material(fits.SLIDING, "tpu")  # sliding fit, TPU/ASA
INSERT_H = INSERT_DEPTH - INSERT_AXIAL_CLEAR
MOUTH_CH = 0.3  # entry bevel, smaller than the tightest neighbouring shank walls
EXIT_CH = 0.1  # small exit bevel preserves the outermost TPU bore walls


def _round_bore(d: float, x: float, y: float) -> None:
    land_r = c.land_bore_r(d)
    relief_r = (d + c.RELIEF_FIT) / 2
    with Locations((x, y, 0)):
        Cylinder(
            land_r,
            c.LAND_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    with Locations((x, y, c.LAND_H)):
        Cone(
            land_r,
            relief_r,
            c.LAND_LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    with Locations((x, y, c.LAND_H + c.LAND_LEAD_IN)):
        Cylinder(
            relief_r,
            INSERT_H - c.LAND_H - c.LAND_LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    with Locations((x, y, 0)):
        Cone(
            land_r + MOUTH_CH,
            land_r,
            MOUTH_CH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    with Locations((x, y, INSERT_H - EXIT_CH)):
        Cone(
            relief_r,
            relief_r + EXIT_CH,
            EXIT_CH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )


def _hex_bore(af: float, x: float, y: float) -> None:
    land_r = (af + c.HEX_LAND_FIT) / 3**0.5
    relief_r = (af + c.RELIEF_FIT) / 3**0.5
    # Separate sketch tools avoid consuming the cartridge builder's pending faces.
    with BuildPart() as cutter:
        with BuildSketch(Plane.XY):
            RegularPolygon(land_r + MOUTH_CH, 6)
        with BuildSketch(Plane.XY.offset(MOUTH_CH)):
            RegularPolygon(land_r, 6)
        loft(ruled=True)
        with BuildSketch(Plane.XY.offset(MOUTH_CH)):
            RegularPolygon(land_r, 6)
        extrude(amount=c.LAND_H - MOUTH_CH)
        with BuildSketch(Plane.XY.offset(c.LAND_H)):
            RegularPolygon(land_r, 6)
        with BuildSketch(Plane.XY.offset(c.LAND_H + c.LAND_LEAD_IN)):
            RegularPolygon(relief_r, 6)
        loft(ruled=True)
        with BuildSketch(Plane.XY.offset(c.LAND_H + c.LAND_LEAD_IN)):
            RegularPolygon(relief_r, 6)
        extrude(amount=INSERT_H - c.LAND_H - c.LAND_LEAD_IN)
    add(Pos(x, y, 0) * cutter.part, mode=Mode.SUBTRACT)
    add(hex_mouth_tool(relief_r, x, y, INSERT_H, EXIT_CH), mode=Mode.SUBTRACT)


def create_insert_for(drills: DrillSet):
    """Print flat, bores along Z; pose rotated into the ASA pocket in scenes."""
    _cells, positions = layout_for(drills)
    floor = BASE_H + INSERT_WALL
    roof = 5 * HEIGHT_UNIT - INSERT_WALL
    centre_z = (floor + roof) / 2
    width = PAD - 2 * INSERT_WALL - INSERT_FIT
    height = roof - floor - INSERT_FIT
    with BuildPart() as cartridge:
        with BuildSketch():
            RectangleRounded(width, height, INSERT_CORNER_R)
        extrude(amount=INSERT_H)
        add(
            bottom_chamfer_tool(width, height, INSERT_CORNER_R, 0, MOUTH_CH),
            mode=Mode.SUBTRACT,
        )
        add(
            top_chamfer_tool(width, height, INSERT_CORNER_R, INSERT_H, EXIT_CH),
            mode=Mode.SUBTRACT,
        )
        for drill in drills.drills:
            x, z = positions[f"{drill.nominal:g}"]
            _round_bore(drills.cut_d(drill), x, z - centre_z)
        for tool in drills.hex_tools:
            x, z = positions[tool.key]
            _hex_bore(tool.across_flats, x, z - centre_z)
        # One compliant keyed catch prevents the cartridge from following a
        # withdrawn bit; the opposite wall remains continuous and supported.
        with Locations((-(width / 2 - 0.3), -2, INSERT_H / 2)):
            Sphere(INSERT_CATCH_R)
    # Print with the relieved exit on the bed and the tight grip land on the
    # clean upper layers, as on the upright cartridges.
    printed = reseat_on_bed(cartridge.part, flip=True)
    printed.label = f"{drills.name}_sideways_tpu"
    printed.color = c.CART_COLOR
    return printed


def seated_insert_for(drills: DrillSet):
    """Place a print-pose cartridge in the front-facing ASA seat."""
    cells, _positions = layout_for(drills)
    length = cells * GRID - (GRID - PAD)
    front = -length / 2 + BACK_WALL + GUIDE_DEPTH
    centre_z = (BASE_H + 5 * HEIGHT_UNIT) / 2
    insert = create_insert_for(drills)
    return as_part(
        Pos(0, front - INSERT_AXIAL_CLEAR / 2 - INSERT_H, centre_z)
        * Rotation(-90, 0, 0)
        * insert
    )
