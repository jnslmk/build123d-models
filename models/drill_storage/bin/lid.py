"""Lift-off stackable bin lid: supported one-piece or separate glue-on lips."""

from build123d import (
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Polygon,
    Pos,
    sweep,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.drill_storage.box import split_stacking_lips
from models.lib.gridfinity import CORNER_R, GRID, PAD
from models.drill_storage.cover import SEPARATE_STACKING_LIPS_PARAM
from models.lib import fits
from models.lib.edges import as_part, bottom_chamfer_tool, top_chamfer_tool
from models.lib.gridfinity_socket import socket_support, socket_tool
from . import config as c
from .foot import cell_layout

SKIRT_WALL = 1.0  # PETG: two perimeters, without thinning the 1 mm bin wall
SKIRT_LEAD_IN = 0.3  # the skirt's entering outer edge
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
    cells = [
        (
            cell_x * GRID - (GRID - PAD),
            cell_y * GRID - (GRID - PAD),
            x,
            y,
        )
        for cell_x, x in x_cells
        for cell_y, y in y_cells
    ]
    cell_sizes = dict.fromkeys((cell_w, cell_d) for cell_w, cell_d, _, _ in cells)
    socket_tools = {size: socket_tool(*size, c.LID_SOCKET_DEPTH) for size in cell_sizes}
    socket_supports = (
        {size: socket_support(*size, c.LID_SOCKET_DEPTH) for size in cell_sizes}
        if support and not separate_stacking_lips
        else {}
    )

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
        for cell_w, cell_d, x, y in cells:
            add(
                as_part(Pos(x, y, 0) * socket_tools[cell_w, cell_d]),
                mode=Mode.SUBTRACT,
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
            for cell_w, cell_d, x, y in cells:
                add(as_part(Pos(x, y, 0) * socket_supports[cell_w, cell_d]))
    part = lid.part
    part.color = c.LID_COLOR
    if separate_stacking_lips:
        return split_stacking_lips(part, c.LID_SOCKET_DEPTH)
    return part
