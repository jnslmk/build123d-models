"""Optional interior fixtures for the Gridfinity bin (all dimensions in mm).

Call ``add_label_tabs`` and ``add_scoops`` *inside* the bin's BuildPart,
*after* its cavity and divider walls have been formed. Both add material to the
active builder, leave the outer perimeter untouched, and are no-ops when their
corresponding option is false. XY is centered; ``floor_z`` is the top of the
solid floor, not the bottom of the foot.
"""

from __future__ import annotations

from math import ceil
from typing import Literal

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Polygon,
    extrude,
    add,
)
from .config import FEATURE_HEADROOM

LabelPosition = Literal["Full", "Left", "Center", "Right"]

LABEL_THICKNESS = 1.0
TOP_CLEARANCE = FEATURE_HEADROOM  # keep fixtures below the lid's locating skirt
WALL_ENGAGEMENT = 0.25
RIB_SPACING = 13.0  # maximum unsupported span under an ultra-light label


def _section_bounds(
    half_extent: float, wall: float, dividers: int, section: int
) -> tuple[float, float]:
    """Inner faces of a section, including half-thickness partition offsets."""
    low, high = -half_extent, half_extent
    pitch = (high - low) / (dividers + 1)
    return (
        low + section * pitch + (wall / 2 if section else 0),
        low + (section + 1) * pitch - (wall / 2 if section < dividers else 0),
    )


def _one_label(
    x_left: float,
    x_width: float,
    y_wall: float,
    tab_depth: float,
    z_top: float,
    wall: float,
    ultra_light_labels: bool,
) -> None:
    """Make a tab on a +Y wall, inside the current BuildPart."""
    z_under = z_top - LABEL_THICKNESS
    y_root = y_wall + WALL_ENGAGEMENT
    y_tip = y_wall - tab_depth
    with BuildPart() as tab:
        # The 45-degree triangular gusset is self-supporting in foot-down pose.
        # Sketch normal of YZ is +X; the top overlaps the slab slightly to fuse.
        with BuildSketch(Plane.YZ.offset(x_left)) as section:
            Polygon(
                (y_tip, z_under + 0.05),
                (y_root, z_under + 0.05),
                (y_root, z_under - tab_depth),
                align=None,
            )
        extrude(section.sketch, amount=x_width)
        with Locations((x_left, y_tip, z_under)):
            Box(
                x_width,
                y_root - y_tip,
                LABEL_THICKNESS,
                align=(Align.MIN, Align.MIN, Align.MIN),
            )
        if ultra_light_labels and x_width > 2 * wall + 1.0:
            # Remove only material below the slab; repeated ribs keep each
            # unsupported slab span at most 13 mm. The root still fuses to
            # the wall even where the triangle is hollowed out.
            count = max(2, ceil(x_width / RIB_SPACING) + 1)
            rib = min(wall, x_width / (2 * count))
            gap = (x_width - count * rib) / (count - 1)
            for index in range(count - 1):
                x_gap = x_left + rib + index * (rib + gap)
                with Locations((x_gap, y_tip - 0.1, z_under - tab_depth - 0.1)):
                    Box(
                        gap,
                        y_root - y_tip + 0.2,
                        tab_depth + 0.2,
                        align=(Align.MIN, Align.MIN, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
    add(tab.part)


def add_label_tabs(
    *,
    width: float,
    depth: float,
    height: float,
    wall: float,
    floor_z: float,
    labels: bool = False,
    label_for_each_section: bool = True,
    label_position: LabelPosition = "Full",
    label_width: float = 30.0,
    label_depth: float = 13.0,
    ultra_light_labels: bool = True,
    dividers_x: int = 0,
    dividers_y: int = 0,
) -> None:
    """Fuse downward-gusseted label shelves onto +Y walls of the active bin.

    With ``label_for_each_section``, each Y row receives a tab, and Left,
    Center, Right select a tab per X section. Full spans all X sections in
    that row. Without it there is one tab at the outside +Y wall. Oversized
    tabs shrink to their section rather than escaping the footprint or closing
    the cavity; a 0.6 mm headroom remains above the label for a future lid.
    """
    if not labels or label_depth <= 0:
        return
    if label_position not in ("Full", "Left", "Center", "Right"):
        raise ValueError(f"Unknown label position: {label_position}")
    if label_position != "Full" and label_width <= 0:
        return
    nx = dividers_x if label_for_each_section else 0
    ny = dividers_y if label_for_each_section else 0
    half_x = width / 2 - wall
    half_y = depth / 2 - wall
    z_top = height - TOP_CLEARANCE
    max_vertical = z_top - LABEL_THICKNESS - floor_z - 0.25
    if half_x <= 0 or half_y <= 0 or max_vertical <= 0:
        return
    for iy in range(ny + 1):
        y_low, y_high = _section_bounds(half_y, wall, ny, iy)
        # A clear central opening survives even in a short, divided cell.
        tab_depth = min(label_depth, (y_high - y_low) * 0.45, max_vertical)
        if tab_depth <= 0:
            continue
        if label_position == "Full":
            _one_label(
                -half_x + 0.2,
                2 * half_x - 0.4,
                y_high,
                tab_depth,
                z_top,
                wall,
                ultra_light_labels,
            )
            continue
        for ix in range(nx + 1):
            x_low, x_high = _section_bounds(half_x, wall, nx, ix)
            x_low += 0.2
            x_high -= 0.2
            x_width = min(label_width, x_high - x_low)
            if x_width <= 0:
                continue
            if label_position == "Left":
                x_left = x_low
            elif label_position == "Right":
                x_left = x_high - x_width
            else:
                x_left = (x_low + x_high - x_width) / 2
            _one_label(
                x_left, x_width, y_high, tab_depth, z_top, wall, ultra_light_labels
            )


def add_scoops(
    *,
    width: float,
    depth: float,
    height: float,
    wall: float,
    floor_z: float,
    scoops: bool = False,
    scoop_radius: float = 15.0,
    dividers_y: int = 0,
) -> None:
    """Fuse an upward concave sweep onto each section's -Y floor/wall junction.

    This is a positive quarter-circle ramp (not a cut through the bin floor).
    The transverse X cylinder cuts *only* the wedge's private builder; the
    active bin is never cut. ``dividers_y`` partitions the inner depth into
    equal rows, with the divider walls centered on the section boundaries.
    """
    if not scoops or scoop_radius <= 0:
        return
    half_x = width / 2 - wall
    half_y = depth / 2 - wall
    if half_x <= 0 or half_y <= 0:
        return
    for iy in range(dividers_y + 1):
        y_low, y_high = _section_bounds(half_y, wall, dividers_y, iy)
        radius = min(
            scoop_radius,
            (y_high - y_low) * 0.45,
            height - TOP_CLEARANCE - floor_z - 0.25,
        )
        if radius <= 0:
            continue
        y_center = y_low + radius
        y_start = y_low - WALL_ENGAGEMENT
        # Set the cylinder slightly above the floor so the wedge overlaps the
        # floor throughout its width; keep the positive ramp rooted in its wall.
        z_base = floor_z - 0.15
        with BuildPart() as scoop:
            with Locations((-half_x, y_start, z_base)):
                Box(
                    2 * half_x,
                    y_center - y_start,
                    radius + 0.15,
                    align=(Align.MIN, Align.MIN, Align.MIN),
                )
            with Locations((0, y_center, floor_z + radius + 0.05)):
                Cylinder(
                    radius, 2 * half_x + 0.2, rotation=(0, 90, 0), mode=Mode.SUBTRACT
                )
        add(scoop.part)
