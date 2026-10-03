"""Lift-off stackable bin lid: supported one-piece or separate glue-on lips."""

from math import floor

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    sweep,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage.box import split_stacking_lips
from models.lib.gridfinity import CORNER_R, FOOT_C1, FOOT_C3, FOOT_STRAIGHT, GRID, PAD
from models.drill_storage.cover import SEPARATE_STACKING_LIPS_PARAM
from models.lib import fits
from models.lib.edges import bottom_chamfer_tool, top_chamfer_tool
from . import config as c
from .foot import cell_layout

SKIRT_WALL = 1.0  # PETG: two perimeters, without thinning the 1 mm bin wall
SKIRT_LEAD_IN = 0.3  # the skirt's entering outer edge
SOCKET_LEAD_IN = 0.3  # functional entry funnel for a Gridfinity foot
LATTICE_PITCH = 5.0
LATTICE_RIB = 0.8
# Support process candidates, not mating fits or calibrated PETG defaults.
# Retain the existing nominal gap to isolate attachment/coverage changes;
# effective separation must still be checked in the sliced PETG layer paths.
LATTICE_GAP = 0.2
SUPPORT_XY_GAP = 0.6  # per side: extrusion/first-layer separation from socket walls
SUPPORT_TAB_WIDTH = 0.4  # one nominal bead along a straight rail; verify in slicer
SUPPORT_TAB_DEPTH = 0.8  # across rail, retaining only 0.64 mm² total neck per cell
SUPPORT_ROOF_OVERLAP = 0.02  # minimal positive weld, not the fracture section
STACK_FIT = fits.SLIDING  # PETG sliding fit, diametral, between foot and socket
PLUG_FIT = fits.SLIDING  # PETG sliding fit, diametral, between skirt and bin cavity

PARAMS = [
    *(
        param
        for param in c.PARAMS
        if param["name"]
        in (
            "grid_x",
            "grid_y",
            "half_grid_base",
            "half_grid_right",
            "half_grid_top",
            "wall_thickness",
        )
    ),
    {
        "name": "lid_height",
        "label": "Lid height (mm)",
        "type": "number",
        "min": c.LID_MIN_HEIGHT,
        "max": 14,
        "step": 0.5,
        "default": c.LID_MIN_HEIGHT,
    },
    {
        "name": "support",
        "label": "Include breakaway socket supports",
        "type": "boolean",
        "default": True,
    },
    SEPARATE_STACKING_LIPS_PARAM,
]
IS_ASSEMBLY = False


def _socket(cell_w: float, cell_d: float, x: float, y: float) -> None:
    """Cut the lower bevel and straight portion of one matching foot."""
    bottom_inset = FOOT_C1 + FOOT_C3
    mid_inset = FOOT_C3
    profiles = []
    for z, inset, lead in (
        (-0.05, mid_inset, SOCKET_LEAD_IN),
        (SOCKET_LEAD_IN, mid_inset, 0),
        (FOOT_STRAIGHT, mid_inset, 0),
        (c.LID_SOCKET_DEPTH, bottom_inset, 0),
    ):
        with BuildSketch(Plane.XY.offset(z)) as section:
            with Locations((x, y)):
                RectangleRounded(
                    cell_w - 2 * inset + STACK_FIT + 2 * lead,
                    cell_d - 2 * inset + STACK_FIT + 2 * lead,
                    CORNER_R - inset + STACK_FIT / 2 + lead,
                )
        profiles.append(section.sketch)
    loft(sections=profiles, ruled=True, mode=Mode.SUBTRACT)


def _support(cell_w: float, cell_d: float, x: float, y: float) -> None:
    """Bed-seated rail/lattice with two accessible gap-spanning roof tabs."""
    inset = FOOT_C1 + FOOT_C3
    # The ceiling is the narrowest socket section. Offset its whole contour,
    # including the corner radius, so no lower wall/bevel can touch the support.
    rail_w = cell_w - 2 * inset + STACK_FIT - 2 * SUPPORT_XY_GAP
    rail_d = cell_d - 2 * inset + STACK_FIT - 2 * SUPPORT_XY_GAP
    rail_r = CORNER_R - inset + STACK_FIT / 2 - SUPPORT_XY_GAP
    support_h = c.LID_SOCKET_DEPTH - LATTICE_GAP
    nx = max(1, floor(((cell_w - 2 * inset) / 2 - 1) / LATTICE_PITCH))
    ny = max(1, floor(((cell_d - 2 * inset) / 2 - 1) / LATTICE_PITCH))
    with BuildPart() as backing:
        with BuildSketch():
            with Locations((x, y)):
                RectangleRounded(rail_w, rail_d, rail_r)
                RectangleRounded(
                    rail_w - 2 * LATTICE_RIB,
                    rail_d - 2 * LATTICE_RIB,
                    rail_r - LATTICE_RIB,
                    mode=Mode.SUBTRACT,
                )
        extrude(amount=support_h)
        # Extend every rib into the rail. Clipping the combined field prevents
        # rectangular rib ends protruding into half-cell rounded corners.
        for ix in range(-nx, nx + 1):
            with Locations((x + ix * LATTICE_PITCH, y, 0)):
                Box(
                    LATTICE_RIB,
                    rail_d,
                    support_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        for iy in range(-ny, ny + 1):
            with Locations((x, y + iy * LATTICE_PITCH, 0)):
                Box(
                    rail_w,
                    LATTICE_RIB,
                    support_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        with BuildSketch():
            with Locations((x, y)):
                RectangleRounded(rail_w, rail_d, rail_r)
        extrude(amount=support_h, mode=Mode.INTERSECT)
    add(backing.part)
    # Opposite short-side straight rail midpoints: substantial roof above,
    # direct access through the socket below. Cut tabs and peel inward rather
    # than levering on the finished lip. Rotate for a wide/short half cell.
    along_y = rail_d >= rail_w
    tab_offset = (rail_d if along_y else rail_w) / 2 - LATTICE_RIB / 2
    for sign in (-1, 1):
        with Locations(
            (
                x if along_y else x + sign * tab_offset,
                y + sign * tab_offset if along_y else y,
                support_h,
            )
        ):
            Box(
                SUPPORT_TAB_WIDTH if along_y else SUPPORT_TAB_DEPTH,
                SUPPORT_TAB_DEPTH if along_y else SUPPORT_TAB_WIDTH,
                LATTICE_GAP + SUPPORT_ROOF_OVERLAP,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )


def _snap_bead(skirt_w: float, skirt_d: float, skirt_r: float, z_tip: float) -> Part:
    """A chamfered bead ring standing out of the skirt's outer wall.

    The cross-section is a quad that protrudes ``SNAP_PROTRUSION`` from the
    skirt and rises with a long gentle ``SNAP_LEAD_IN`` ramp on the free-end
    (insertion) side and a shorter ``SNAP_BACK`` retention face on the plate
    side, with a small ``SNAP_TIP_FLAT`` at the tip. Swept around the skirt's
    rounded-rectangle perimeter; union it into the lid so the skirt slides
    into the bin progressively yet detents into the bin's groove.
    """
    with BuildSketch(Plane.XY.offset(z_tip)) as outline:
        RectangleRounded(skirt_w, skirt_d, skirt_r)
    path = outline.faces()[0].outer_wire()
    x_wall = skirt_w / 2
    x_tip = x_wall + c.SNAP_PROTRUSION
    profile = [
        (x_wall, z_tip + c.SNAP_LEAD_IN),
        (x_tip, z_tip + c.SNAP_TIP_FLAT / 2),
        (x_tip, z_tip - c.SNAP_TIP_FLAT / 2),
        (x_wall, z_tip - c.SNAP_BACK),
    ]
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ):
            Polygon(*profile, align=None)
        sweep(path=path)
    return ring.part


def create(
    grid_x: float = 1,
    grid_y: float = 2,
    half_grid_base: bool = False,
    half_grid_right: bool = True,
    half_grid_top: bool = True,
    wall_thickness: float = c.WALL,
    lid_height: float = c.LID_MIN_HEIGHT,
    support: bool = True,
    separate_stacking_lips: bool = False,
):
    """Socket-down one-piece print, or body roof-down and lips socket-up."""
    if lid_height < c.LID_MIN_HEIGHT or lid_height > 14:
        raise ValueError("lid_height must fit a foot socket, solid roof and 3 mm skirt")
    if wall_thickness < 1 or wall_thickness > 4:
        raise ValueError("wall_thickness must be between 1 and 4 mm")
    x_cells = cell_layout(grid_x, half_grid_base, half_grid_right)
    # The lid is printed upside-down; rotating it into use pose reverses Y.
    y_cells = cell_layout(grid_y, half_grid_base, not half_grid_top)
    width = grid_x * GRID - (GRID - PAD)
    depth = grid_y * GRID - (GRID - PAD)
    plate_height = lid_height - c.LID_SKIRT_MIN
    skirt_w = width - 2 * wall_thickness - PLUG_FIT
    skirt_d = depth - 2 * wall_thickness - PLUG_FIT
    skirt_r = max(0.4, CORNER_R - wall_thickness) - PLUG_FIT / 2

    with BuildPart() as lid:
        with BuildSketch():
            RectangleRounded(width, depth, CORNER_R)
        extrude(amount=plate_height)
        add(bottom_chamfer_tool(width, depth, CORNER_R, 0, 0.3), mode=Mode.SUBTRACT)
        # Match the body's exterior rim bevel without spending its flat landing.
        add(
            top_chamfer_tool(width, depth, CORNER_R, plate_height, c.RIM_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        for cell_x, x in x_cells:
            for cell_y, y in y_cells:
                _socket(
                    cell_x * GRID - (GRID - PAD),
                    cell_y * GRID - (GRID - PAD),
                    x,
                    y,
                )
        with BuildSketch(Plane.XY.offset(plate_height)):
            RectangleRounded(skirt_w, skirt_d, skirt_r)
        extrude(amount=c.LID_SKIRT_MIN)
        with BuildSketch(Plane.XY.offset(plate_height)):
            RectangleRounded(
                skirt_w - 2 * SKIRT_WALL,
                skirt_d - 2 * SKIRT_WALL,
                max(0.2, skirt_r - SKIRT_WALL),
            )
        extrude(amount=c.LID_SKIRT_MIN + 0.1, mode=Mode.SUBTRACT)
        add(
            top_chamfer_tool(skirt_w, skirt_d, skirt_r, lid_height, SKIRT_LEAD_IN),
            mode=Mode.SUBTRACT,
        )
        add(_snap_bead(skirt_w, skirt_d, skirt_r, lid_height - c.SNAP_Z))
        inner_w = skirt_w - 2 * SKIRT_WALL
        inner_d = skirt_d - 2 * SKIRT_WALL
        inner_r = max(0.2, skirt_r - SKIRT_WALL)
        with BuildSketch(Plane.XY.offset(lid_height - 0.2)) as inner_start:
            RectangleRounded(inner_w, inner_d, inner_r)
        with BuildSketch(Plane.XY.offset(lid_height + 0.05)) as inner_mouth:
            RectangleRounded(inner_w + 0.5, inner_d + 0.5, inner_r + 0.25)
        loft(
            sections=[inner_start.sketch, inner_mouth.sketch],
            ruled=True,
            mode=Mode.SUBTRACT,
        )
        if support and not separate_stacking_lips:
            for cell_x, x in x_cells:
                for cell_y, y in y_cells:
                    _support(
                        cell_x * GRID - (GRID - PAD),
                        cell_y * GRID - (GRID - PAD),
                        x,
                        y,
                    )
    part = lid.part
    part.color = c.LID_COLOR
    if separate_stacking_lips:
        return split_stacking_lips(part, c.LID_SOCKET_DEPTH)
    return part
