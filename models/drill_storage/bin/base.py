"""Parametric Gridfinity bin body; the removable lid is a separate CAD slice."""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Pos,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from models.lib.edges import as_part, top_chamfer_tool
from . import config as c
from .features import LabelPosition
from .foot import cell_layout

PARAMS = c.PARAMS
IS_ASSEMBLY = False


def _foot(size_x: float, size_y: float, wall: float, hollow: bool):
    """Full or half-grid foot with the drill family's standard bevel profile."""
    from models.drill_storage.box import FOOT_C1, FOOT_C3, FOOT_STRAIGHT

    with BuildPart() as foot:
        sections = []
        for z, inset in (
            (0, FOOT_C1 + FOOT_C3),
            (FOOT_C1, FOOT_C3),
            (FOOT_C1 + FOOT_STRAIGHT, FOOT_C3),
            (c.BASE_H, 0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as profile:
                RectangleRounded(
                    size_x - 2 * inset, size_y - 2 * inset, c.CORNER_R - inset
                )
            sections.append(profile.sketch)
        loft(sections=sections, ruled=True)
        if hollow:
            # The hollow runs under the floor, with cross ribs shortening the
            # unsupported bridge to less than half a 1x1 cell.
            with BuildSketch(Plane.XY.offset(-0.05)) as opening:
                RectangleRounded(
                    size_x - 2 * (FOOT_C1 + FOOT_C3 + wall),
                    size_y - 2 * (FOOT_C1 + FOOT_C3 + wall),
                    max(0.4, c.CORNER_R - FOOT_C1 - FOOT_C3 - wall),
                )
            with BuildSketch(Plane.XY.offset(c.BASE_H)) as ceiling:
                RectangleRounded(
                    size_x - 2 * wall, size_y - 2 * wall, max(0.4, c.CORNER_R - wall)
                )
            loft(
                sections=[opening.sketch, ceiling.sketch],
                ruled=True,
                mode=Mode.SUBTRACT,
            )
            with Locations((0, 0, 0)):
                Box(
                    wall,
                    size_y - 2 * (FOOT_C1 + FOOT_C3),
                    c.BASE_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                Box(
                    size_x - 2 * (FOOT_C1 + FOOT_C3),
                    wall,
                    c.BASE_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
    return foot.part


def create(
    grid_x: float = 1,
    grid_y: float = 2,
    height_u: int = 3,
    half_grid_base: bool = False,
    half_grid_right: bool = True,
    half_grid_top: bool = True,
    wall_thickness: float = c.WALL,
    ultra_light_base: bool = True,
    ultra_light_labels: bool = True,
    magnets: bool = False,
    magnet_diameter: float = 6,
    magnet_depth: float = 2.2,
    dividers: bool = False,
    dividers_x: int = 0,
    dividers_y: int = 1,
    labels: bool = False,
    label_for_each_section: bool = True,
    label_position: LabelPosition = "Full",
    label_width: float = 30,
    label_depth: float = 13,
    scoops: bool = False,
    scoop_radius: float = 15,
):
    """Create the printable bin body. Optional features are independent switches."""
    if any(value < 0.5 or value * 2 != round(value * 2) for value in (grid_x, grid_y)):
        raise ValueError("grid dimensions must be positive multiples of half a cell")
    if height_u < 2 or height_u != int(height_u):
        raise ValueError("height_u must be a whole number of at least two units")
    if wall_thickness < 1 or wall_thickness > 4:
        raise ValueError("wall_thickness must be between 1 and 4 mm")
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
    width = grid_x * c.GRID - (c.GRID - c.PAD)
    depth = grid_y * c.GRID - (c.GRID - c.PAD)
    height = height_u * c.HEIGHT_UNIT
    floor_z = c.BASE_H + wall
    x_cells = cell_layout(grid_x, half_grid_base, half_grid_right)
    y_cells = cell_layout(grid_y, half_grid_base, half_grid_top)

    feet = {
        (cell_x, cell_y): _foot(
            cell_x * c.GRID - (c.GRID - c.PAD),
            cell_y * c.GRID - (c.GRID - c.PAD),
            wall,
            ultra_light_base,
        )
        for cell_x in {size for size, _ in x_cells}
        for cell_y in {size for size, _ in y_cells}
    }
    with BuildPart() as bin_part:
        for cell_x, x_center in x_cells:
            for cell_y, y_center in y_cells:
                add(as_part(Pos(x_center, y_center, 0) * feet[cell_x, cell_y]))
        with BuildSketch(Plane.XY.offset(c.BASE_H)):
            RectangleRounded(width, depth, c.CORNER_R)
        extrude(amount=height - c.BASE_H)
        add(
            top_chamfer_tool(width, depth, c.CORNER_R, height, c.RIM_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        with BuildSketch(Plane.XY.offset(floor_z)):
            RectangleRounded(
                width - 2 * wall, depth - 2 * wall, max(0.4, c.CORNER_R - wall)
            )
        extrude(amount=height - floor_z + 1, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(height - c.MOUTH_CHAMFER)) as mouth_bottom:
            RectangleRounded(
                width - 2 * wall, depth - 2 * wall, max(0.4, c.CORNER_R - wall)
            )
        with BuildSketch(Plane.XY.offset(height + 0.05)) as mouth_top:
            RectangleRounded(
                width - 2 * wall + 2 * (c.MOUTH_CHAMFER + 0.05),
                depth - 2 * wall + 2 * (c.MOUTH_CHAMFER + 0.05),
                max(0.4, c.CORNER_R - wall) + c.MOUTH_CHAMFER + 0.05,
            )
        loft(
            sections=[mouth_bottom.sketch, mouth_top.sketch],
            ruled=True,
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
    return bin_part.part
