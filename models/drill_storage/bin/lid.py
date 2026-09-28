"""Lift-off stackable Gridfinity bin lid, socket-down in print pose."""

from math import floor

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage.box import FOOT_C1, FOOT_C3, FOOT_STRAIGHT
from models.lib import fits
from models.lib.edges import bottom_chamfer_tool, top_chamfer_tool
from . import config as c
from .foot import cell_layout

SKIRT_WALL = 1.0  # PETG: two perimeters, without thinning the 1 mm bin wall
SKIRT_LEAD_IN = 0.3  # the skirt's entering outer edge
SOCKET_LEAD_IN = 0.3  # functional entry funnel for a Gridfinity foot
LATTICE_PITCH = 5.0
LATTICE_RIB = 0.8
LATTICE_GAP = 0.2  # one layer between removable support and socket ceiling
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
                    c.CORNER_R - inset + STACK_FIT / 2 + lead,
                )
        profiles.append(section.sketch)
    loft(sections=profiles, ruled=True, mode=Mode.SUBTRACT)


def _support(cell_w: float, cell_d: float, x: float, y: float) -> None:
    """One breakaway lattice, printed under the socket ceiling and peeled out."""
    bottom_x = cell_w - 2 * (FOOT_C1 + FOOT_C3)
    bottom_y = cell_d - 2 * (FOOT_C1 + FOOT_C3)
    nx = max(1, floor((bottom_x / 2 - 1) / LATTICE_PITCH))
    ny = max(1, floor((bottom_y / 2 - 1) / LATTICE_PITCH))
    span_x = 2 * nx * LATTICE_PITCH + LATTICE_RIB
    span_y = 2 * ny * LATTICE_PITCH + LATTICE_RIB
    for ix in range(-nx, nx + 1):
        with Locations((x + ix * LATTICE_PITCH, y, 0)):
            Box(
                LATTICE_RIB,
                span_y,
                c.LID_SOCKET_DEPTH - LATTICE_GAP,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    for iy in range(-ny, ny + 1):
        with Locations((x, y + iy * LATTICE_PITCH, 0)):
            Box(
                span_x,
                LATTICE_RIB,
                c.LID_SOCKET_DEPTH - LATTICE_GAP,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    for dx in (-min(nx, 2) * LATTICE_PITCH, min(nx, 2) * LATTICE_PITCH):
        for dy in (-min(ny, 2) * LATTICE_PITCH, min(ny, 2) * LATTICE_PITCH):
            with Locations((x + dx, y + dy, c.LID_SOCKET_DEPTH - LATTICE_GAP)):
                Box(
                    0.6,
                    0.6,
                    LATTICE_GAP + 0.02,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )


def create(
    grid_x: float = 1,
    grid_y: float = 2,
    half_grid_base: bool = False,
    half_grid_right: bool = True,
    half_grid_top: bool = True,
    wall_thickness: float = c.WALL,
    lid_height: float = c.LID_MIN_HEIGHT,
    support: bool = True,
):
    """Print pose: exposed top/socket on z=0 and locating skirt pointing up."""
    if lid_height < c.LID_MIN_HEIGHT or lid_height > 14:
        raise ValueError("lid_height must fit a foot socket, solid roof and 3 mm skirt")
    if wall_thickness < 1 or wall_thickness > 4:
        raise ValueError("wall_thickness must be between 1 and 4 mm")
    x_cells = cell_layout(grid_x, half_grid_base, half_grid_right)
    # The lid is printed upside-down; rotating it into use pose reverses Y.
    y_cells = cell_layout(grid_y, half_grid_base, not half_grid_top)
    width = grid_x * c.GRID - (c.GRID - c.PAD)
    depth = grid_y * c.GRID - (c.GRID - c.PAD)
    plate_height = lid_height - c.LID_SKIRT_MIN
    skirt_w = width - 2 * wall_thickness - PLUG_FIT
    skirt_d = depth - 2 * wall_thickness - PLUG_FIT
    skirt_r = max(0.4, c.CORNER_R - wall_thickness) - PLUG_FIT / 2

    with BuildPart() as lid:
        with BuildSketch():
            RectangleRounded(width, depth, c.CORNER_R)
        extrude(amount=plate_height)
        add(bottom_chamfer_tool(width, depth, c.CORNER_R, 0, 0.3), mode=Mode.SUBTRACT)
        # Match the body's exterior rim bevel without spending its flat landing.
        add(
            top_chamfer_tool(width, depth, c.CORNER_R, plate_height, c.RIM_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        for cell_x, x in x_cells:
            for cell_y, y in y_cells:
                _socket(
                    cell_x * c.GRID - (c.GRID - c.PAD),
                    cell_y * c.GRID - (c.GRID - c.PAD),
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
        if support:
            for cell_x, x in x_cells:
                for cell_y, y in y_cells:
                    _support(
                        cell_x * c.GRID - (c.GRID - c.PAD),
                        cell_y * c.GRID - (c.GRID - c.PAD),
                        x,
                        y,
                    )
    part = lid.part
    part.color = c.LID_COLOR
    return part
