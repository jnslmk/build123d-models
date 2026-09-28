"""Physical tool-envelope, side-cover, and print-pose gates."""

from itertools import combinations
from math import hypot, sqrt

from build123d import BuildSketch, CenterOf, FontStyle, Pos, Text, Vector
from models.lib.checks import Report, is_solid_at

from . import config as c
from .box import BASE_H, CORNER_R, GRID, HEIGHT_UNIT, PAD, gridfinity_foot
from .sets import DrillSet
from .sideways import (
    BACK_WALL,
    EDGE_CHAMFER,
    FRONT_CORNER_R,
    LABEL_SIZE,
    RAIL_X,
    create_preview_for,
    layout_for,
    tool_map_glyphs,
)
from .sideways_cover import SEAM

# Wall budgets are independent of the frozen optimiser's objective: a bit must
# clear the next bit by this much even at the widest point of its body.
MIN_TOOL_GAP = 1.4  # 1 mm reserved + 0.4 mm diametral running clearance
SIDE_WALL = 1.2  # three 0.4 mm ASA perimeters
FLOOR_WALL = 1.2
TOP_WALL = 1.2


def _ink_point(face):
    """Find material in each letter face, including rings with hollow centres."""
    centre = face.center(CenterOf.MASS)
    if face.is_inside(centre):
        return centre
    box = face.bounding_box()
    for ix in range(1, int(box.size.X / 0.2)):
        for iz in range(1, int(box.size.Y / 0.2)):
            point = Vector(box.min.X + ix * 0.2, box.min.Y + iz * 0.2, 0)
            if face.is_inside(point):
                return point
    return None


def run_for(drills: DrillSet, part) -> Report:
    report = Report()
    cells, positions = layout_for(drills)
    length = cells * GRID - (GRID - PAD)
    height = 5 * HEIGHT_UNIT
    report.section(f"Sideways {drills.name}: tool envelopes and print pose")
    b = part.bounding_box()
    report.check(
        len(part.solids()) == 1
        and abs(b.min.Z) < 1e-5
        and abs(b.max.Z - (height + BASE_H)) < 1e-5
        and abs(b.size.X - GRID) < 1e-5
        and abs(b.size.Y - (GRID + (GRID - PAD) / 2)) < 1e-5
        and abs(b.min.Y + length / 2 + (GRID - PAD) / 2) < 1e-5
        and not is_solid_at(part, 0, -length / 2 + GRID + 1, BASE_H / 2),
        "one rear foot only, no forward bed or foot",
    )
    rear_y = -length / 2 + PAD / 2
    foot = gridfinity_foot()
    report.check(
        part.intersect(Pos(0, rear_y, height) * foot).volume < 1e-5
        and is_solid_at(part, 0, rear_y, height - 0.5)
        and not is_solid_at(part, 0, rear_y, height + 0.5),
        "rear socket seats a complete foot on a solid 5U roof",
    )
    tools = {
        **{f"{d.nominal:g}": (d.nominal / 2, d.length) for d in drills.drills},
        **{
            t.key: (max(t.head_d / 2, t.across_flats / sqrt(3)), t.length)
            for t in drills.hex_tools
        },
    }
    report.check(positions.keys() == tools.keys(), "all set tools have guide locations")
    for key, (radius, tool_length) in tools.items():
        x, z = positions[key]
        report.check(
            PAD / 2 - abs(x) - radius >= SIDE_WALL
            and z - radius - BASE_H >= FLOOR_WALL
            and height - z - radius >= TOP_WALL,
            f"{key} clears outer walls",
        )
        report.check(
            tool_length + BACK_WALL + 2 <= length,
            f"{key} fits behind closed front with 2 mm allowance",
        )
        report.check(
            not is_solid_at(part, x, -length / 2 + 12, z),
            f"{key} ASA guide is open",
        )
    mouth_radii = {
        **{
            f"{drill.nominal:g}": (drills.cut_d(drill) + c.GUIDE_FIT) / 2
            for drill in drills.drills
        },
        **{
            tool.key: (tool.across_flats + c.GUIDE_FIT) / sqrt(3)
            for tool in drills.hex_tools
        },
    }
    wall, key = min(
        (
            PAD / 2 - FRONT_CORNER_R - abs(positions[key][0]) - radius - EDGE_CHAMFER,
            key,
        )
        for key, radius in mouth_radii.items()
    )
    report.check(
        wall >= 0.8,
        "narrowest ASA bore-mouth side wall",
        f"{key}: {wall:.2f} mm (minimum two 0.4 mm perimeters)",
    )
    gaps = (
        (
            hypot(positions[a][0] - positions[b][0], positions[a][1] - positions[b][1])
            - ra
            - rb,
            a,
            b,
        )
        for (a, (ra, _)), (b, (rb, _)) in combinations(tools.items(), 2)
    )
    gap, a, b = min(gaps)
    report.check(
        gap >= MIN_TOOL_GAP,
        "tightest tool-body gap",
        f"{a}/{b}: {gap:.2f} mm (minimum {MIN_TOOL_GAP:.2f} mm)",
    )
    # Every character must be recessed into the back wall, not merely placed
    # in the layout. Its solid backing must survive behind the engraving.
    legends = list(tool_map_glyphs(drills))
    rear = -length / 2
    flat_half = PAD / 2 - CORNER_R
    rectangles = []
    for key, x, z, glyph in legends:
        bounds = glyph.bounding_box()
        rectangle = (
            x + bounds.min.X,
            x + bounds.max.X,
            z + bounds.min.Y,
            z + bounds.max.Y,
        )
        rectangles.append(rectangle)
        ink = [_ink_point(face) for face in glyph.faces()]
        report.check(
            key in tools
            and bounds.size.Y >= 3.0
            and rectangle[0] > -flat_half
            and rectangle[1] < flat_half
            and rectangle[2] > BASE_H
            and rectangle[3] < height
            and bool(ink)
            and all(
                point is not None
                and not is_solid_at(part, x + point.X, rear + 0.4, z + point.Y)
                and is_solid_at(part, x + point.X, rear + 1.2, z + point.Y)
                for point in ink
            ),
            f"{key} back-wall label is legible, engraved and backed by ASA",
        )
    report.check(
        len(legends) == len(tools)
        and all(
            a[1] + 0.2 <= b[0]
            or b[1] + 0.2 <= a[0]
            or a[3] + 0.2 <= b[2]
            or b[3] + 0.2 <= a[2]
            for a, b in combinations(rectangles, 2)
        ),
        "tool-map glyphs have separate printable footprints",
    )
    return report


def run_cover_for(drills: DrillSet, cover) -> Report:
    """Check both printable halves and real posed-bit interference."""
    report = Report()
    cells, _positions = layout_for(drills)
    length = cells * GRID - (GRID - PAD)
    rear = -length / 2
    front = length / 2
    preview = create_preview_for(drills)
    base = preview.children[0]
    report.section(f"Sideways {drills.name}: seated PETG cover")
    box = cover.bounding_box()
    report.check(
        len(cover.solids()) == 1
        and abs(box.min.Z) < 1e-5
        and abs(box.max.Z - (5 * HEIGHT_UNIT + BASE_H)) < 1e-5
        and abs(box.size.X - GRID) < 1e-5
        and abs(box.max.Y - (front + (GRID - PAD) / 2)) < 1e-5
        and not is_solid_at(cover, 0, rear + GRID / 2, BASE_H / 2)
        and all(
            is_solid_at(cover, 0, rear + (i + 0.5) * GRID, BASE_H / 2)
            for i in range(1, cells)
        ),
        "one cover solid with only the forward Gridfinity feet",
    )
    foot = gridfinity_foot()
    report.check(
        all(
            cover.intersect(
                Pos(0, rear + PAD / 2 + i * GRID, 5 * HEIGHT_UNIT) * foot
            ).volume
            < 1e-5
            and is_solid_at(cover, 0, rear + PAD / 2 + i * GRID, 5 * HEIGHT_UNIT - 0.5)
            and not is_solid_at(
                cover, 0, rear + PAD / 2 + i * GRID, 5 * HEIGHT_UNIT + 0.5
            )
            for i in range(1, cells)
        ),
        "all forward sockets seat full feet on intact 5U roofs",
    )
    report.check(
        is_solid_at(cover, 0, front - 4, 5 * HEIGHT_UNIT - 0.5)
        and not is_solid_at(cover, 0, front - 4, 5 * HEIGHT_UNIT - 2)
        and is_solid_at(cover, 0, front - 0.5, 20)
        and is_solid_at(cover, 0, rear + GRID + 4, BASE_H + 0.8),
        "roof, hollow interior, closed nose and forward bed",
    )
    # The larger cover name must stay on its flat wall and leave material
    # behind every letter; the nominal font size alone is not the glyph size.
    with BuildSketch() as lettering:
        Text(drills.label.upper(), font_size=LABEL_SIZE, font_style=FontStyle.BOLD)
    name = lettering.sketch
    bounds = name.bounding_box()
    shell_rear = rear + GRID + SEAM
    label_y = (shell_rear + front) / 2
    ink = [_ink_point(face) for face in name.faces()]
    report.check(
        bounds.size.Y >= 8
        and label_y + bounds.min.X > shell_rear + FRONT_CORNER_R + 0.5
        and label_y + bounds.max.X < front - CORNER_R - 0.5
        and 5 * HEIGHT_UNIT / 2 + bounds.min.Y > BASE_H + 2
        and 5 * HEIGHT_UNIT / 2 + bounds.max.Y < 5 * HEIGHT_UNIT - 1
        and bool(ink)
        and all(
            point is not None
            and not is_solid_at(
                cover, PAD / 2 - 0.25, label_y + point.X, 5 * HEIGHT_UNIT / 2 + point.Y
            )
            and is_solid_at(
                cover, PAD / 2 - 0.8, label_y + point.X, 5 * HEIGHT_UNIT / 2 + point.Y
            )
            for point in ink
        ),
        "enlarged cover name is legible, recessed and backed by PETG",
    )
    report.check(
        is_solid_at(base, RAIL_X, rear + 30, BASE_H + 2.4)
        and not is_solid_at(cover, RAIL_X, rear + 30, BASE_H + 2.4)
        and is_solid_at(cover, RAIL_X + 2, rear + 30, BASE_H + 2.4)
        and base.intersect(cover).volume < 1e-5,
        "ASA rail captured in PETG sleeve without seated overlap",
    )
    report.check(
        all(
            base.intersect(Pos(0, offset, 0) * cover).volume < 1e-5
            for offset in (5, 10, 15, 18)
        ),
        "cover slides sideways off the rail after lifting off the baseplate",
    )
    for tool in preview.children[1:]:
        overlap = cover.intersect(tool).volume
        report.check(
            overlap < 1e-5,
            f"{tool.label} clears closed PETG cover",
            f"overlap {overlap:.4f} mm³",
        )
    return report
