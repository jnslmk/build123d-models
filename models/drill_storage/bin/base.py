"""Parametric Gridfinity bin body; the removable lid is a separate CAD slice."""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    sweep,
    Pos,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.lib.edges import as_part, top_chamfer_tool
from models.lib.gridfinity import (
    BASE_H,
    CORNER_R,
    GRID,
    HEIGHT_UNIT,
    PAD,
    gridfinity_foot,
    gridfinity_foot_cavity,
)
from . import config as c
from .features import LabelPosition
from .foot import cell_layout

PARAMS = c.PARAMS
IS_ASSEMBLY = False


def _snap_groove(inner_w: float, inner_d: float, inner_r: float, z_tip: float) -> Part:
    """Cut the snap bead's receiving groove into the bin's inner wall.

    The mirror of the lid's bead: the same quad cross-section, cut into the
    cavity wall instead of standing out of it. ``SNAP_GROOVE_FLOOR`` is how far
    below ``z_tip`` the groove's lower face meets the wall again and
    ``SNAP_GROOVE_ROOF`` how far above. Subtract it.
    """
    with BuildSketch(Plane.XY.offset(z_tip)) as outline:
        RectangleRounded(inner_w, inner_d, inner_r)
    path = outline.faces()[0].outer_wire()
    x_wall = inner_w / 2
    x_tip = x_wall + c.SNAP_PROTRUSION
    profile = [
        (x_wall, z_tip + c.SNAP_GROOVE_ROOF),
        (x_tip, z_tip + c.SNAP_TIP_FLAT / 2),
        (x_tip, z_tip - c.SNAP_TIP_FLAT / 2),
        (x_wall, z_tip - c.SNAP_GROOVE_FLOOR),
    ]
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ):
            Polygon(*profile, align=None)
        sweep(path=path)
    return tool.part


def create(
    grid_x: float = 1,
    grid_y: float = 2,
    height_u: int = 5,
    half_grid_base: bool = False,
    half_grid_right: bool = True,
    half_grid_top: bool = True,
    wall_thickness: float = c.WALL,
    ultra_light_base: bool = True,
    bottom_thickness: float = 0,
    ultra_light_labels: bool = True,
    magnets: bool = False,
    magnet_diameter: float = 6.15,
    magnet_depth: float = 2.2,
    dividers: bool = True,
    dividers_x: int = 0,
    dividers_y: int = 0,
    labels: bool = False,
    label_for_each_section: bool = True,
    label_position: LabelPosition = "Full",
    label_width: float = 30,
    label_depth: float = 13,
    scoops: bool = False,
    scoop_radius: float = 30,
):
    """Create the printable bin body. Optional features are independent switches."""
    if any(value < 0.5 or value * 2 != round(value * 2) for value in (grid_x, grid_y)):
        raise ValueError("grid dimensions must be positive multiples of half a cell")
    if height_u < 2 or height_u != int(height_u):
        raise ValueError("height_u must be a whole number of at least two units")
    if wall_thickness < 1 or wall_thickness > 4:
        raise ValueError("wall_thickness must be between 1 and 4 mm")
    if bottom_thickness < 0 or bottom_thickness > 4:
        raise ValueError("bottom_thickness must be between 0 and 4 mm")
    if any(value < 0 or value != int(value) for value in (dividers_x, dividers_y)):
        raise ValueError("divider counts must be nonnegative integers")
    if label_position not in ("Full", "Left", "Center", "Right"):
        raise ValueError("unknown label alignment")
    if magnets and half_grid_base:
        raise ValueError("magnet pockets need full-grid feet; disable half_grid_base")
    if magnets and (
        magnet_diameter < 3
        or magnet_diameter > 8
        or magnet_depth < 1
        or magnet_depth > 3
    ):
        raise ValueError("magnet dimensions are outside the supported range")
    if labels and (label_width < 8 or label_depth < 4):
        raise ValueError("label dimensions are too small to print")
    if scoops and scoop_radius < 3:
        raise ValueError("scoop_radius must be at least 3 mm")

    wall = wall_thickness
    width = grid_x * GRID - (GRID - PAD)
    depth = grid_y * GRID - (GRID - PAD)
    height = height_u * HEIGHT_UNIT
    floor_z = BASE_H + wall
    x_cells = cell_layout(grid_x, half_grid_base, half_grid_right)
    y_cells = cell_layout(grid_y, half_grid_base, half_grid_top)

    feet = {
        (cell_x, cell_y): gridfinity_foot(
            cell_x * GRID - (GRID - PAD),
            cell_y * GRID - (GRID - PAD),
        )
        for cell_x in {size for size, _ in x_cells}
        for cell_y in {size for size, _ in y_cells}
    }
    cavity_keys = [
        (cell_x, cell_y, ix > 0, ix < len(x_cells) - 1, iy > 0, iy < len(y_cells) - 1)
        for ix, (cell_x, _) in enumerate(x_cells)
        for iy, (cell_y, _) in enumerate(y_cells)
    ]
    cavities = (
        {
            key: gridfinity_foot_cavity(
                key[0] * GRID - (GRID - PAD),
                key[1] * GRID - (GRID - PAD),
                wall,
                max(wall, bottom_thickness),
                key[2:],
                seam_chamfer=c.FLOOR_SEAM_CHAMFER,
            )
            for key in set(cavity_keys)
        }
        if ultra_light_base
        else {}
    )
    with BuildPart() as bin_part:
        for cell_x, x_center in x_cells:
            for cell_y, y_center in y_cells:
                add(as_part(Pos(x_center, y_center, 0) * feet[cell_x, cell_y]))
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(width, depth, CORNER_R)
        extrude(amount=height - BASE_H)
        add(
            top_chamfer_tool(width, depth, CORNER_R, height, c.RIM_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        with BuildSketch(Plane.XY.offset(floor_z)):
            RectangleRounded(
                width - 2 * wall, depth - 2 * wall, max(0.4, CORNER_R - wall)
            )
        extrude(amount=height - floor_z + 1, mode=Mode.SUBTRACT)
        for ix, (cell_x, x_center) in enumerate(x_cells):
            for iy, (cell_y, y_center) in enumerate(y_cells):
                if ultra_light_base:
                    key = (
                        cell_x,
                        cell_y,
                        ix > 0,
                        ix < len(x_cells) - 1,
                        iy > 0,
                        iy < len(y_cells) - 1,
                    )
                    add(
                        as_part(Pos(x_center, y_center, 0) * cavities[key]),
                        mode=Mode.SUBTRACT,
                    )
        with BuildSketch(Plane.XY.offset(height - c.MOUTH_CHAMFER)) as mouth_bottom:
            RectangleRounded(
                width - 2 * wall, depth - 2 * wall, max(0.4, CORNER_R - wall)
            )
        with BuildSketch(Plane.XY.offset(height + 0.05)) as mouth_top:
            RectangleRounded(
                width - 2 * wall + 2 * (c.MOUTH_CHAMFER + 0.05),
                depth - 2 * wall + 2 * (c.MOUTH_CHAMFER + 0.05),
                max(0.4, CORNER_R - wall) + c.MOUTH_CHAMFER + 0.05,
            )
        loft(
            sections=[mouth_bottom.sketch, mouth_top.sketch],
            ruled=True,
            mode=Mode.SUBTRACT,
        )
        inner_w = width - 2 * wall
        inner_d = depth - 2 * wall
        inner_r = max(0.4, CORNER_R - wall)
        add(
            _snap_groove(
                inner_w,
                inner_d,
                inner_r,
                height - (c.LID_SKIRT_MIN - c.SNAP_Z),
            ),
            mode=Mode.SUBTRACT,
        )

        if magnets:
            pocket_r = (magnet_diameter + c.MAGNET_FIT) / 2
            # Magnet boss reaches the floor; pocket opens from below the foot.
            for cell_x, x_center in x_cells:
                for cell_y, y_center in y_cells:
                    if cell_x != 1 or cell_y != 1:
                        continue
                    for dx in (-13, 13):
                        for dy in (-13, 13):
                            with Locations((x_center + dx, y_center + dy, 0)):
                                Cylinder(
                                    pocket_r + wall,
                                    floor_z,
                                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                                )
                                Cylinder(
                                    pocket_r,
                                    magnet_depth,
                                    mode=Mode.SUBTRACT,
                                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                                )
        if dividers:
            inner_x = width - 2 * wall
            inner_y = depth - 2 * wall
            for index in range(1, dividers_x + 1):
                x = -inner_x / 2 + index * inner_x / (dividers_x + 1)
                with Locations((x, 0, floor_z)):
                    Box(
                        wall,
                        inner_y,
                        height - floor_z - c.FEATURE_HEADROOM,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
            for index in range(1, dividers_y + 1):
                y = -inner_y / 2 + index * inner_y / (dividers_y + 1)
                with Locations((0, y, floor_z)):
                    Box(
                        inner_x,
                        wall,
                        height - floor_z - c.FEATURE_HEADROOM,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
        if labels or scoops:
            from .features import add_label_tabs, add_scoops

            if labels:
                add_label_tabs(
                    width=width,
                    depth=depth,
                    height=height,
                    floor_z=floor_z,
                    wall=wall,
                    dividers_x=dividers_x if dividers else 0,
                    dividers_y=dividers_y if dividers else 0,
                    labels=labels,
                    label_for_each_section=label_for_each_section,
                    label_position=label_position,
                    label_width=label_width,
                    label_depth=label_depth,
                    ultra_light_labels=ultra_light_labels,
                )
            if scoops:
                add_scoops(
                    width=width,
                    depth=depth,
                    height=height,
                    floor_z=floor_z,
                    wall=wall,
                    dividers_y=dividers_y if dividers else 0,
                    scoops=scoops,
                    scoop_radius=scoop_radius,
                )
    part = bin_part.part
    part.color = c.BASE_COLOR
    return part
