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
    BED_THICKNESS,
    COLLAR_END,
    COLLAR_CLEAR,
    COLLAR_LEAD,
    DETENT_BEAD,
    DETENT_GROOVE,
    DETENT_W,
    DETENT_X,
    DETENT_Y,
    EDGE_CHAMFER,
    FRONT_CORNER_R,
    GUIDE_DEPTH,
    INSERT_DEPTH,
    LABEL_SIZE,
    create_preview_for,
    layout_for,
    tool_map_glyphs,
)
from .sideways_insert import INSERT_FIT, INSERT_H, seated_insert_for
from .sideways_cover import MOUTH_LEAD, SEAM, WALL

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
        part.is_valid
        and len(part.solids()) == 1
        and abs(b.min.Z) < 1e-5
        and abs(b.max.Z - (height + BASE_H)) < 1e-5
        and abs(b.size.X - GRID) < 1e-5
        and abs(b.size.Y - (COLLAR_END + (GRID - PAD) / 2)) < 1e-5
        and abs(b.min.Y + length / 2 + (GRID - PAD) / 2) < 1e-5
        and not is_solid_at(part, 0, -length / 2 + GRID + 1, BASE_H / 2),
        "one rear foot and a cover collar, no forward bed or foot",
    )
    # A single planar skin from behind the rear radius through the cover joint
    # rules out both the old butt-jointed extension and its lower-edge stripe.
    rear = -length / 2
    report.check(
        all(
            any(
                abs(face.bounding_box().min.X - side) < 1e-5
                and abs(face.bounding_box().max.X - side) < 1e-5
                and face.bounding_box().min.Y <= rear + CORNER_R + 1e-5
                and face.bounding_box().max.Y >= rear + GRID - FRONT_CORNER_R - 1e-5
                and face.bounding_box().min.Z <= BASE_H + 1e-5
                and face.bounding_box().max.Z >= height - 0.2 - 1e-5
                and all(
                    face.is_inside(Vector(side, rear + offset, z))
                    for offset, z in (
                        (22.9, 20),
                        (27, BASE_H + 0.2),
                        (27, 20),
                        (39, 20),
                    )
                )
                for face in part.faces()
            )
            for side in (-PAD / 2, PAD / 2)
        ),
        "flush continuous ASA side and lower bed edge through the collar joint",
    )
    rear_y = -length / 2 + PAD / 2
    foot = gridfinity_foot()
    report.check(
        part.intersect(Pos(0, rear_y, height) * foot).volume < 1e-5
        and is_solid_at(part, 0, rear_y, height - 0.5)
        and not is_solid_at(part, 0, rear_y, height + 0.5),
        "rear socket seats a complete foot on a solid 5U roof",
    )
    pocket_front = -length / 2 + BACK_WALL + GUIDE_DEPTH
    pocket_mid = pocket_front - INSERT_DEPTH / 2
    report.check(
        not is_solid_at(part, 0, pocket_mid, 20)
        and is_solid_at(part, PAD / 2 - 0.5, pocket_mid, 20)
        and is_solid_at(part, 0, pocket_mid, BASE_H + 0.5)
        and is_solid_at(part, 0, pocket_mid, height - 0.5)
        and is_solid_at(part, 0, pocket_front - INSERT_DEPTH - 0.5, height - 2),
        "front-facing TPU seat retains ASA side, floor, roof and back walls",
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
        report.check(
            not is_solid_at(part, x, pocket_mid, z),
            f"{key} through-path is open in the cartridge seat",
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


def run_insert_for(drills: DrillSet, insert) -> Report:
    """Check grip versus relief, wall budget, and seating in the ASA guide."""
    from .sideways import create_base_for

    report = Report()
    _cells, positions = layout_for(drills)
    bottom = BASE_H + 1.0
    centre_z = (BASE_H + 5 * HEIGHT_UNIT) / 2
    half_width = (PAD - 2.0 - INSERT_FIT) / 2
    half_height = (5 * HEIGHT_UNIT - 1.0 - bottom - INSERT_FIT) / 2
    box = insert.bounding_box()
    report.section(f"Sideways {drills.name}: printable TPU cartridge")
    report.check(
        insert.is_valid
        and len(insert.solids()) == 1
        and abs(box.min.Z) < 1e-5
        and abs(box.max.Z - INSERT_H) < 1e-5
        and box.min.X > -PAD / 2
        and box.max.X < PAD / 2,
        "one valid flat-bed TPU print including its keyed catch",
    )
    for drill in drills.drills:
        key = f"{drill.nominal:g}"
        x, z = positions[key]
        y = centre_z - z
        d = drills.cut_d(drill)
        land = c.land_bore_r(d)
        relief = (d + c.RELIEF_FIT) / 2
        probe_r = (land + relief) / 2
        report.check(
            half_width - abs(x) - land >= 0.6
            and half_height - abs(y) - land >= 0.6
            and not is_solid_at(insert, x, y, 1.0)
            and is_solid_at(insert, x + probe_r, y, INSERT_H - 1)
            and not is_solid_at(insert, x + probe_r, y, 1.0),
            f"{key} has a supported short TPU grip land and relieved bore",
        )
    for tool in drills.hex_tools:
        x, z = positions[tool.key]
        y = centre_z - z
        land = (tool.across_flats + c.HEX_LAND_FIT) / sqrt(3)
        relief = (tool.across_flats + c.RELIEF_FIT) / sqrt(3)
        probe_r = (land + relief) / 2
        report.check(
            half_width - abs(x) - land >= 0.6
            and half_height - abs(y) - land >= 0.6
            and not is_solid_at(insert, x, y, 1.0)
            and is_solid_at(insert, x + probe_r, y, INSERT_H - 1)
            and not is_solid_at(insert, x + probe_r, y, 1.0),
            f"{tool.key} has a hex grip land and relieved bore",
        )
    base = create_base_for(drills)
    seated = seated_insert_for(drills)
    report.check(
        base.intersect(seated).volume < 1e-5
        and base.intersect(Pos(0, 2, 0) * seated).volume > 0,
        "keyed TPU catch seats without collision and resists axial withdrawal",
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
        cover.is_valid
        and len(cover.solids()) == 1
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
    collar_y = rear + GRID + 2
    report.check(
        is_solid_at(base, 19.4, collar_y, 20)
        and not is_solid_at(cover, 19.4, collar_y, 20)
        and is_solid_at(cover, PAD / 2 - 0.5, collar_y, 20)
        and base.intersect(cover).volume < 1e-5
        and base.intersect(preview.children[1]).volume < 1e-5
        and cover.intersect(preview.children[1]).volume < 1e-5,
        "ASA collar slides inside PETG mouth with seated TPU cartridge",
    )
    male_outer_x = (PAD - 2 * WALL - COLLAR_CLEAR) / 2
    mouth_x = (PAD - 2 * WALL) / 2 + MOUTH_LEAD / 4
    report.check(
        is_solid_at(base, male_outer_x - COLLAR_LEAD / 3, rear + COLLAR_END - 0.5, 20)
        and not is_solid_at(
            base, male_outer_x - COLLAR_LEAD / 3, rear + COLLAR_END - 0.1, 20
        )
        and not is_solid_at(cover, mouth_x, shell_rear + 0.01, 20)
        and is_solid_at(cover, mouth_x, shell_rear + MOUTH_LEAD + 0.1, 20),
        "both sides of the collar joint have an entry lead-in",
    )
    # The bead sits clear inside the seated groove; moving the cover 1 mm
    # forward drives it into the collar floor before it can withdraw.
    detent_y = rear + DETENT_Y
    detent_x = DETENT_X + DETENT_W / 2
    detent_floor = BASE_H + BED_THICKNESS + COLLAR_CLEAR / 2
    engagement = DETENT_BEAD - COLLAR_CLEAR / 2
    report.check(
        not is_solid_at(base, detent_x, detent_y, detent_floor + 0.25)
        and is_solid_at(base, detent_x, detent_y, detent_floor + DETENT_GROOVE + 0.75)
        and not is_solid_at(
            base, detent_x, detent_y, detent_floor + DETENT_GROOVE + 0.85
        )
        and is_solid_at(cover, detent_x, detent_y, BASE_H + BED_THICKNESS + 0.2)
        and is_solid_at(cover, detent_x, detent_y - 0.5, BASE_H + BED_THICKNESS + 0.15)
        and not is_solid_at(
            cover, detent_x, detent_y + 0.35, BASE_H + BED_THICKNESS + 0.15
        )
        and base.intersect(cover).volume < 1e-5
        and base.intersect(Pos(0, 1, 0) * cover).volume > 0
        and engagement > 0.1,
        "backed ASA groove seats PETG bead with axial retention",
        f"{engagement:.2f} mm nominal engagement, 0.8 mm groove backing",
    )
    report.check(
        all(
            base.intersect(Pos(0, offset, 0) * cover).volume < 1e-5
            for offset in (5, 10, 15, 18)
        ),
        "cover clears collar after releasing detent off the baseplate",
    )
    for tool in preview.children[2:]:
        overlap = cover.intersect(tool).volume
        report.check(
            overlap < 1e-5 and base.intersect(tool).volume < 1e-5,
            f"{tool.label} clears closed PETG cover and ASA guide",
            f"cover overlap {overlap:.4f} mm³",
        )
    return report
