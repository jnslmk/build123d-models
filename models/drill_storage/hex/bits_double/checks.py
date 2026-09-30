"""Physical gate for the 1×2 BITS base anchor, without dependent parts.

``check_guides(report, base)`` also accepts altered geometry: filling one guide
or moving its blind floor must fail without changing the accepted configuration.
"""

from itertools import combinations
from math import cos, pi, sin, sqrt

from build123d import BuildSketch, CenterOf, FontStyle, GeomType, Part, Text

from models.lib.checks import Report, adjacent_faces, is_flush_seam, sharp_convex_edges
from models.lib.fits import MIN_WALL
from models.drill_storage import box
from models.drill_storage.hex import config as h

from . import config as c
from .base import create, label_tools

PROBE = 0.04


def _hex_land(first, second, radius: float) -> tuple[float, tuple[float, float]]:
    """True distance between two translated, equally oriented hex mouth polygons."""
    ax, ay = first
    bx, by = second
    apothem = radius * sqrt(3) / 2
    if (
        max(
            abs(
                (bx - ax) * cos((2 * k + 1) * pi / 6)
                + (by - ay) * sin((2 * k + 1) * pi / 6)
            )
            - 2 * apothem
            for k in range(6)
        )
        <= 0
    ):
        return 0.0, ((ax + bx) / 2, (ay + by) / 2)
    polygons = [
        [(x + radius * cos(k * pi / 3), y + radius * sin(k * pi / 3)) for k in range(6)]
        for x, y in (first, second)
    ]
    nearest = (float("inf"), (0.0, 0.0))
    for vertices, other in (polygons, polygons[::-1]):
        for px, py in vertices:
            for i, (qx, qy) in enumerate(other):
                rx, ry = other[(i + 1) % 6]
                dx, dy = rx - qx, ry - qy
                t = max(
                    0.0,
                    min(1.0, ((px - qx) * dx + (py - qy) * dy) / (dx * dx + dy * dy)),
                )
                sx, sy = qx + t * dx, qy + t * dy
                gap = sqrt((px - sx) ** 2 + (py - sy) ** 2)
                if gap < nearest[0]:
                    nearest = gap, ((px + sx) / 2, (py + sy) / 2)
    return nearest


def check_guides(report: Report, base: Part) -> None:
    """Probe every actual guide, including six flats and its exact blind floor."""
    report.section("36 blind hex guides")
    across_flats, mouth_ch, _ = h.box_fits("bits")
    radius = across_flats / sqrt(3)
    apothem = across_flats / 2
    middle = (c.GUIDE_FLOOR_Z + c.CAVITY_FLOOR_Z - mouth_ch) / 2
    for index, (label, x, y) in enumerate(c.SOCKETS):
        name = f"guide {index + 1} ({label}, x={x:.3f}, y={y:.3f})"
        report.check(
            all(
                not report.solid_at(base, x, y, z)
                for z in (c.GUIDE_FLOOR_Z + PROBE, middle, c.CAVITY_FLOOR_Z - PROBE)
            )
            and report.solid_at(base, x, y, c.GUIDE_FLOOR_Z - PROBE),
            f"{name}: open centre and blind floor",
            f"floor z={c.GUIDE_FLOOR_Z:.3f}, straddled by ±{PROBE}",
        )
        report.check(
            all(
                not report.solid_at(
                    base,
                    x + (apothem - PROBE) * cos(angle),
                    y + (apothem - PROBE) * sin(angle),
                    middle,
                )
                and report.solid_at(
                    base,
                    x + (apothem + PROBE) * cos(angle),
                    y + (apothem + PROBE) * sin(angle),
                    middle,
                )
                for angle in ((2 * k + 1) * pi / 6 for k in range(6))
            ),
            f"{name}: all six flats at the BITS guide fit",
            f"{across_flats:.3f} mm across flats",
        )
        # A conical counterbore leaves a ledge at the flats. Sampling halfway
        # up the loft on every flat catches that as well as an omitted lead-in.
        z = c.CAVITY_FLOOR_Z - mouth_ch / 2
        widened_flat = (radius + mouth_ch / 2) * sqrt(3) / 2
        report.check(
            all(
                not report.solid_at(
                    base,
                    x + (widened_flat - PROBE) * cos(angle),
                    y + (widened_flat - PROBE) * sin(angle),
                    z,
                )
                and report.solid_at(
                    base,
                    x + (widened_flat + PROBE) * cos(angle),
                    y + (widened_flat + PROBE) * sin(angle),
                    z,
                )
                for angle in ((2 * k + 1) * pi / 6 for k in range(6))
            ),
            f"{name}: continuous hex mouth chamfer",
            f"radial lead-in {mouth_ch:.3f} mm",
        )
    mouth_radius = radius + mouth_ch
    lands = [
        (_hex_land((a[1], a[2]), (b[1], b[2]), mouth_radius), a, b)
        for a, b in combinations(c.SOCKETS, 2)
    ]
    # Only adjacent grid neighbours are sampled: a midpoint between distant
    # sockets can legitimately lie in a third socket. In Y the nearest points
    # are on opposing flats, not on the sockets' circumscribed circles.
    for (land, point), a, b in lands:
        adjacent_x = (
            abs(a[2] - b[2]) < 1e-6 and abs(abs(a[1] - b[1]) - c.PITCH_X) < 1e-6
        )
        adjacent_y = (
            abs(a[1] - b[1]) < 1e-6 and abs(abs(a[2] - b[2]) - c.PITCH_Y) < 1e-6
        )
        if adjacent_x or adjacent_y:
            dx, dy = b[1] - a[1], b[2] - a[2]
            length = sqrt(dx * dx + dy * dy)
            report.check(
                all(
                    report.solid_at(
                        base,
                        point[0] + offset * dx / length,
                        point[1] + offset * dy / length,
                        z,
                    )
                    for offset in (-0.05, -0.025, 0, 0.025, 0.05)
                    for z in (c.CAVITY_FLOOR_Z - 1e-4, c.CAVITY_FLOOR_Z - mouth_ch / 2)
                ),
                f"neighbour mouth land at ({point[0]:.3f}, {point[1]:.3f}) is actual solid",
                f"polygon land {land:.3f} mm",
            )
    report.check(
        all(
            report.solid_at(base, x, y, z)
            for _, x, y in c.SOCKETS
            for z in (box.BASE_H + PROBE, c.GUIDE_FLOOR_Z - MIN_WALL)
        ),
        "blind floors stay above the foot with printable backing",
        f"{c.GUIDE_FLOOR_Z - box.BASE_H:.3f} mm backing",
    )
    for index, (_, x, y) in enumerate(c.SOCKETS):
        # Probe the reserved outer-body margin, not a nonexistent cartridge.
        report.check(
            all(
                report.solid_at(base, x + dx, y + dy, middle)
                for dx, dy in (
                    (radius + PROBE, 0),
                    (-radius - PROBE, 0),
                    (0, radius + PROBE),
                    (0, -radius - PROBE),
                )
            )
            and c.BODY_X / 2 - abs(x) - radius >= MIN_WALL
            and c.BODY_Y / 2 - abs(y) - radius >= MIN_WALL,
            f"guide {index + 1}: intact surrounding body and outer-wall margin",
        )


def _wall_point(axis: str, sign: int, radius: float, along: float, z: float):
    return (sign * radius, along, z) if axis == "x" else (along, sign * radius, z)


def check_shell(report: Report, base: Part) -> None:
    report.section("Envelope, print pose and both Gridfinity feet")
    bounds = base.bounding_box()
    report.check(
        base.is_valid and len(base.solids()) == 1, "base is one valid printable solid"
    )
    report.check(
        abs(bounds.min.X + c.BODY_X / 2) < 1e-5
        and abs(bounds.max.X - c.BODY_X / 2) < 1e-5
        and abs(bounds.min.Y + c.BODY_Y / 2) < 1e-5
        and abs(bounds.max.Y - c.BODY_Y / 2) < 1e-5
        and abs(bounds.min.Z) < 1e-5
        and abs(bounds.max.Z - c.BASE_TOP_Z) < 1e-5,
        "true 41.5 × 83.5 × 30 mm bounds; feet down at z=0",
        f"{bounds.size.X:.5f} × {bounds.size.Y:.5f} × {bounds.size.Z:.5f}",
    )
    half_mid = box.PAD / 2 - box.FOOT_C3
    for foot_y in (-box.GRID / 2, box.GRID / 2):
        samples = (
            (box.FOOT_C1 / 2, half_mid - box.FOOT_C1 / 2),
            (box.FOOT_C1 + box.FOOT_STRAIGHT / 2, half_mid),
            (
                box.FOOT_C1 + box.FOOT_STRAIGHT + box.FOOT_C3 / 2,
                half_mid + box.FOOT_C3 / 2,
            ),
        )
        report.check(
            report.solid_at(base, 0, foot_y, 0.02)
            and all(
                report.solid_at(
                    base, dx * (reach - PROBE), foot_y + dy * (reach - PROBE), z
                )
                and not report.solid_at(
                    base, dx * (reach + PROBE), foot_y + dy * (reach + PROBE), z
                )
                for z, reach in samples
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ),
            f"foot at y={foot_y:g}: bed face, lower relief, straight and upper chamfer",
        )
    report.check(
        not report.solid_at(base, 0, 0, box.BASE_H / 2)
        and report.solid_at(base, 0, 0, box.BASE_H + PROBE),
        "two separate standard feet join the continuous body above z=4.4",
    )
    report.section("Rectangular cavity and stretched retention interfaces")
    stations = [("x", sign, along) for sign in (-1, 1) for along in (-21, 0, 21)]
    stations += [("y", sign, 0) for sign in (-1, 1)]
    # Probe immediately beside the key as well; the two cuts legitimately
    # overlap on its centreline, where a groove-depth straddle cannot apply.
    beside_key = (h.KEY_W + h.KEY_SLIP) / 2 + h.KEY_FILLET
    stations += [("x", 1, -beside_key), ("x", 1, beside_key)]
    cavity_z = (
        h.BEAD_Z - h.GROOVE_FLOOR + c.SEAT_Z + box.SNAP_Z + box.SNAP_GROOVE_ROOF
    ) / 2
    report.check(
        report.solid_at(base, 0, 0, c.CAVITY_FLOOR_Z - PROBE)
        and not report.solid_at(base, 0, 0, c.CAVITY_FLOOR_Z + PROBE),
        "real cavity floor at z=23.2 between the guides",
    )
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        inner_cx = c.CAVITY_X / 2 - c.CAVITY_CORNER
        inner_cy = c.CAVITY_Y / 2 - c.CAVITY_CORNER
        outer_cx = c.COLLAR_X / 2 - c.COLLAR_CORNER
        outer_cy = c.COLLAR_Y / 2 - c.COLLAR_CORNER
        report.check(
            not report.solid_at(
                base,
                sx * (inner_cx + (c.CAVITY_CORNER - PROBE) / sqrt(2)),
                sy * (inner_cy + (c.CAVITY_CORNER - PROBE) / sqrt(2)),
                cavity_z,
            )
            and report.solid_at(
                base,
                sx * (inner_cx + (c.CAVITY_CORNER + PROBE) / sqrt(2)),
                sy * (inner_cy + (c.CAVITY_CORNER + PROBE) / sqrt(2)),
                cavity_z,
            )
            and report.solid_at(
                base,
                sx * (outer_cx + (c.COLLAR_CORNER - PROBE) / sqrt(2)),
                sy * (outer_cy + (c.COLLAR_CORNER - PROBE) / sqrt(2)),
                cavity_z,
            )
            and not report.solid_at(
                base,
                sx * (outer_cx + (c.COLLAR_CORNER + PROBE) / sqrt(2)),
                sy * (outer_cy + (c.COLLAR_CORNER + PROBE) / sqrt(2)),
                cavity_z,
            ),
            f"corner {sx:+},{sy:+}: actual cavity and collar radii retain their wall",
        )
    for axis, sign, along in stations:
        inner = (c.CAVITY_X if axis == "x" else c.CAVITY_Y) / 2
        outer = (c.COLLAR_X if axis == "x" else c.COLLAR_Y) / 2
        # Avoid the antirotation key itself, whose reach is tested separately.
        ordinary = not (axis == "x" and sign == 1 and along == 0)
        tag = f"{sign:+}{axis}, along={along:g}"
        if ordinary:
            report.check(
                not report.solid_at(
                    base, *_wall_point(axis, sign, inner - PROBE, along, cavity_z)
                )
                and report.solid_at(
                    base, *_wall_point(axis, sign, inner + PROBE, along, cavity_z)
                )
                and report.solid_at(
                    base, *_wall_point(axis, sign, outer - PROBE, along, cavity_z)
                )
                and not report.solid_at(
                    base, *_wall_point(axis, sign, outer + PROBE, along, cavity_z)
                ),
                f"{tag}: real cavity wall and intact collar margin",
                f"wall {outer - inner:.3f} mm",
            )
        ch = h.CAVITY_MOUTH_CH
        z = c.BASE_TOP_Z - ch / 2
        if ordinary:
            report.check(
                not report.solid_at(
                    base, *_wall_point(axis, sign, inner + ch / 2 - PROBE, along, z)
                )
                and report.solid_at(
                    base, *_wall_point(axis, sign, inner + ch / 2 + PROBE, along, z)
                ),
                f"{tag}: cavity mouth lead-in",
            )
        ch = h.SHELL_TOP_CHAMFER
        z = c.BASE_TOP_Z - ch / 2
        report.check(
            report.solid_at(
                base, *_wall_point(axis, sign, outer - ch / 2 - PROBE, along, z)
            )
            and not report.solid_at(
                base, *_wall_point(axis, sign, outer - ch / 2 + PROBE, along, z)
            ),
            f"{tag}: outer top chamfer",
        )
        for name, wall, centre, depth, floor, roof, tip, direction in (
            (
                "cover",
                outer,
                c.SEAT_Z + box.SNAP_Z,
                box.SNAP_GROOVE_D,
                box.SNAP_GROOVE_FLOOR,
                box.SNAP_GROOVE_ROOF,
                box.SNAP_TIP_FLAT,
                -1,
            ),
            (
                "cartridge",
                inner,
                h.BEAD_Z,
                h.GROOVE_D,
                h.GROOVE_FLOOR,
                h.GROOVE_ROOF,
                h.GROOVE_TIP_FLAT,
                1,
            ),
        ):
            if not ordinary:
                continue
            profile = (
                (centre - (floor + tip / 2) / 2, depth / 2),
                (centre, depth),
                (centre + (roof + tip / 2) / 2, depth / 2),
            )
            report.check(
                all(
                    not report.solid_at(
                        base,
                        *_wall_point(
                            axis, sign, wall + direction * (reach - PROBE), along, z
                        ),
                    )
                    and report.solid_at(
                        base,
                        *_wall_point(
                            axis, sign, wall + direction * (reach + PROBE), along, z
                        ),
                    )
                    for z, reach in profile
                )
                and all(
                    report.solid_at(
                        base,
                        *_wall_point(axis, sign, wall + direction * PROBE, along, z),
                    )
                    for z in (centre - floor - PROBE, centre + roof + PROBE)
                ),
                f"{tag}: {name} groove depth, straight ramps and uncut lips",
                f"depth {depth:.3f} mm; floor {floor:.3f}, roof {roof:.3f}",
            )
        gap_z = (
            h.BEAD_Z - h.GROOVE_FLOOR + c.SEAT_Z + box.SNAP_Z + box.SNAP_GROOVE_ROOF
        ) / 2
        if ordinary:
            report.check(
                all(
                    report.solid_at(
                        base, *_wall_point(axis, sign, radius, along, gap_z)
                    )
                    for radius in (inner + PROBE, (inner + outer) / 2, outer - PROBE)
                ),
                f"{tag}: full wall separates the two groove lips",
            )
    key_x = c.CAVITY_X / 2
    key_z = cavity_z  # Width needs an intact wall, not the cartridge groove.
    report.check(
        all(
            not report.solid_at(base, key_x + h.KEY_D - PROBE, 0, z)
            and report.solid_at(base, key_x + h.KEY_D + PROBE, 0, z)
            for z in (
                c.CAVITY_FLOOR_Z + PROBE,
                key_z,
                c.BASE_TOP_Z - h.CAVITY_MOUTH_CH - PROBE,
            )
        )
        and report.solid_at(
            base, key_x + h.KEY_D / 2, (h.KEY_W + h.KEY_SLIP) / 2 + PROBE, key_z
        )
        and report.solid_at(base, -key_x - h.KEY_D / 2, 0, key_z),
        "antirotation slot retains its +X, y=0 end, depth and width",
    )


def _glyph_point(report: Report, tool: Part, solid, x: float):
    """Prefer a glyph centroid; scan ink for letters with hollow centroids."""
    centre = solid.center(CenterOf.MASS)
    if report.solid_at(tool, x, centre.Y, centre.Z):
        return (centre.Y, centre.Z)
    bounds = solid.bounding_box()
    for iy in range(1, 40):
        for iz in range(1, 80):
            y = bounds.min.Y + bounds.size.Y * iy / 40
            z = bounds.min.Z + bounds.size.Z * iz / 80
            if report.solid_at(tool, x, y, z):
                return (y, z)
    return None


def check_labels(report: Report, base: Part, tools: tuple[Part, ...]) -> None:
    report.section("Full engraved strings on both long walls")
    report.check(len(tools) == len(c.SOCKETS) == 36, "36 complete label tools")
    rectangles = []
    for index, (tool, (label, _, row_y)) in enumerate(zip(tools, c.SOCKETS)):
        column = index % 4
        sign = -1 if column < 2 else 1
        centre_y = row_y + (
            c.LABEL_PAIR_OFFSET if column % 2 == 0 else -c.LABEL_PAIR_OFFSET
        )
        wall = sign * c.BODY_X / 2
        bounds = tool.bounding_box()
        with BuildSketch() as expected:
            Text(label, font_size=c.LABEL_SIZE, font_style=FontStyle.BOLD)
        ink = expected.sketch
        ink_bounds = ink.bounding_box()
        glyphs = list(tool.solids())
        report.check(
            tool.is_valid
            and len(glyphs) == len(ink.faces())
            and abs(bounds.size.Y - ink_bounds.size.Y) < 1e-4
            and abs(bounds.size.Z - ink_bounds.size.X) < 1e-4
            and abs((bounds.min.Y + bounds.max.Y) / 2 - centre_y) < 1e-4
            and abs((bounds.min.Z + bounds.max.Z) / 2 - c.LABEL_Z) < 1e-4
            and bounds.min.Z >= box.BASE_H + 0.6 - 1e-4
            and bounds.max.Z <= c.SEAT_Z - 0.6 + 1e-4
            and bounds.min.Y > -c.BODY_Y / 2 + c.BODY_R
            and bounds.max.Y < c.BODY_Y / 2 - c.BODY_R,
            f"label {index + 1} {label!r}: true bold ink bounds, complete glyphs and semantic position",
            f"Y={bounds.min.Y:.3f}..{bounds.max.Y:.3f}; Z={bounds.min.Z:.3f}..{bounds.max.Z:.3f}",
        )
        cut_depth = c.BODY_X / 2 - (bounds.min.X if sign == 1 else -bounds.max.X)
        report.check(
            abs(cut_depth - c.LABEL_DEPTH) < 1e-4
            and bounds.min.X <= wall <= bounds.max.X,
            f"label {index + 1}: exact {c.LABEL_DEPTH:g} mm tool depth through the wall face",
        )
        # True ink dimensions prove the whole strings, including punctuation.
        # OCC's curved-face area quadrature changes slightly under rotation,
        # so comparing extruded volume against an unrotated face area is invalid.
        actual = sorted(
            (s.bounding_box().size.Z, s.bounding_box().size.Y) for s in glyphs
        )
        expected_glyphs = sorted(
            (f.bounding_box().size.X, f.bounding_box().size.Y) for f in ink.faces()
        )
        report.check(
            len(actual) == len(expected_glyphs)
            and all(
                all(abs(a - b) < 1e-4 for a, b in zip(got, want))
                for got, want in zip(actual, expected_glyphs)
            ),
            f"label {index + 1}: full-size bold font and decimal geometry survive",
        )
        if "." in label:
            period = min(glyphs, key=lambda s: s.bounding_box().size.Z)
            period_bounds = period.bounding_box()
            report.check(
                period_bounds.size.Y >= 0.7 and period_bounds.size.Z >= 0.7,
                f"label {index + 1}: actual decimal footprint survives a 0.4 mm nozzle",
                f"{period_bounds.size.Y:.3f} × {period_bounds.size.Z:.3f} mm",
            )
        removed = True
        sampled = 0
        x = wall - sign * c.LABEL_DEPTH / 2
        for glyph in glyphs:
            point = _glyph_point(report, tool, glyph, x)
            if point is None:
                removed = False
                continue
            y, z = point
            sampled += 1
            removed &= (
                not report.solid_at(base, wall - sign * PROBE, y, z)
                and not report.solid_at(
                    base, wall - sign * (c.LABEL_DEPTH - PROBE), y, z
                )
                and report.solid_at(base, wall - sign * (c.LABEL_DEPTH + PROBE), y, z)
            )
        report.check(
            bool(glyphs) and removed and sampled == len(glyphs),
            f"label {index + 1} {label!r}: every glyph really removes material and retains backing",
            f"{sampled}/{len(glyphs)} glyphs, including isolated punctuation, depth straddled by ±{PROBE}",
        )
        rectangles.append((sign, bounds, index + 1))
    for (sign_a, a, ia), (sign_b, b, ib) in combinations(rectangles, 2):
        if sign_a != sign_b:
            continue
        report.check(
            a.max.Y < b.min.Y
            or b.max.Y < a.min.Y
            or a.max.Z < b.min.Z
            or b.max.Z < a.min.Z,
            f"label ink bounds {ia}/{ib} do not overlap",
        )


def _edge_allow(base: Part, tools: tuple[Part, ...]) -> tuple:
    """Only functional seats, known guide corners and actual glyph envelopes."""
    radius = h.box_fits("bits")[0] / sqrt(3)

    def on_contour(edge, width, length, corner, centre_y=0.0):
        for p in (edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)):
            qx = abs(p.X) - (width / 2 - corner)
            qy = abs(p.Y - centre_y) - (length / 2 - corner)
            distance = (
                sqrt(max(qx, 0) ** 2 + max(qy, 0) ** 2) + min(max(qx, qy), 0) - corner
            )
            if abs(distance) > 1e-5:
                return False
        return True

    def on_seat(edge):
        b = edge.bounding_box()
        at_shoulder = abs(b.min.Z - c.SEAT_Z) < 1e-5 and abs(b.max.Z - c.SEAT_Z) < 1e-5
        at_foot_join = (
            abs(b.min.Z - box.BASE_H) < 1e-5 and abs(b.max.Z - box.BASE_H) < 1e-5
        )
        shoulder_contour = at_shoulder and (
            on_contour(edge, c.BODY_X, c.BODY_Y, c.BODY_R)
            or on_contour(edge, c.COLLAR_X, c.COLLAR_Y, c.COLLAR_CORNER)
        )
        foot_contour = at_foot_join and (
            on_contour(edge, c.BODY_X, c.BODY_Y, c.BODY_R)
            or any(
                on_contour(edge, box.PAD, box.PAD, box.CORNER_R, y)
                for y in (-box.GRID / 2, box.GRID / 2)
            )
        )
        if not (shoulder_contour or foot_contour):
            return False
        return any(
            face.geom_type == GeomType.PLANE
            and abs(face.normal_at().Z) > 0.999
            and abs(face.bounding_box().min.Z - b.min.Z) < 1e-5
            and abs(face.bounding_box().max.Z - b.max.Z) < 1e-5
            for face in adjacent_faces(base, edge)
        )

    def on_retention_lip(edge):
        b = edge.bounding_box()
        if not any(
            abs(b.min.Z - z) < 1e-5 and abs(b.max.Z - z) < 1e-5
            for z in (h.BEAD_Z - h.GROOVE_FLOOR, h.BEAD_Z + h.GROOVE_ROOF)
        ):
            return False
        if not on_contour(edge, c.CAVITY_X, c.CAVITY_Y, c.CAVITY_CORNER):
            return False
        # The receiver tool overlaps the cavity by .01 mm at each lip. Only
        # its resulting thin horizontal annular face qualifies, never a whole
        # groove-height band, pocket, untreated ramp or collar edge.
        return any(
            face.geom_type == GeomType.PLANE
            and abs(face.normal_at().Z) > 0.999
            and abs(face.bounding_box().min.Z - b.min.Z) < 1e-5
            and abs(face.bounding_box().max.Z - b.max.Z) < 1e-5
            and face.area <= 0.02 * 2 * (c.CAVITY_X + c.CAVITY_Y)
            for face in adjacent_faces(base, edge)
        )

    def on_guide_corner(edge):
        b = edge.bounding_box()
        if (
            b.min.Z < c.GUIDE_FLOOR_Z - 1e-5
            or b.max.Z > c.CAVITY_FLOOR_Z - h.box_fits("bits")[1] + 1e-5
        ):
            return False
        for _, x, y in c.SOCKETS:
            points = [edge.position_at(t) for t in (0, 0.5, 1)]
            if not all(
                abs(p.X - x) <= radius + 1e-5 and abs(p.Y - y) <= radius + 1e-5
                for p in points
            ):
                continue
            floor_edge = all(
                abs(p.Z - c.GUIDE_FLOOR_Z) < 1e-5
                and abs(
                    max(
                        (p.X - x) * cos((2 * k + 1) * pi / 6)
                        + (p.Y - y) * sin((2 * k + 1) * pi / 6)
                        for k in range(6)
                    )
                    - radius * sqrt(3) / 2
                )
                < 1e-5
                for p in points
            )
            vertical_vertex = (
                b.size.X < 1e-5
                and b.size.Y < 1e-5
                and abs(sqrt((points[0].X - x) ** 2 + (points[0].Y - y) ** 2) - radius)
                < 1e-5
            )
            if floor_edge or vertical_vertex:
                return True
        return False

    label_probe = Report()
    label_regions = tuple((tool, tool.bounding_box()) for tool in tools)

    def on_label(edge):
        # Geometric membership in the actual glyph cuts, rather than a broad
        # wall band or text bounding rectangle that could hide an unrelated edge.
        points = [edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)]
        b = edge.bounding_box()
        return any(
            b.min.X >= t.min.X - 1e-5
            and b.max.X <= t.max.X + 1e-5
            and b.min.Y >= t.min.Y - 1e-5
            and b.max.Y <= t.max.Y + 1e-5
            and b.min.Z >= t.min.Z - 1e-5
            and b.max.Z <= t.max.Z + 1e-5
            and all(label_probe.solid_at(tool, p.X, p.Y, p.Z) for p in points)
            for tool, t in label_regions
        )

    def key_flush(edge):
        b = edge.bounding_box()
        return (
            b.min.X >= c.CAVITY_X / 2 - 1e-5
            and b.max.X <= c.CAVITY_X / 2 + h.KEY_D + 1e-5
            and max(abs(b.min.Y), abs(b.max.Y)) <= (h.KEY_W + h.KEY_SLIP) / 2 + 1e-5
            and is_flush_seam(base, edge)
        )

    return (
        (
            on_seat,
            "flat cover shoulder and foot/body joins preserve their seating planes",
        ),
        (
            on_guide_corner,
            "blind hex floor and vertical socket corners preserve shank support/fit; mouth chamfers are not exempt",
        ),
        (
            on_retention_lip,
            "cartridge receiver's .01 mm overlap lips retain the exact square detent datum; the ramps themselves are audited",
        ),
        (
            on_label,
            "edges belonging to actual label cut solids: bevelling glyph edges would erase readable strokes",
        ),
        (key_flush, "only the antirotation slot's tangent 180-degree mouth split"),
    )


def run() -> Report:
    base = create()
    tools = label_tools()
    report = Report()
    check_shell(report, base)
    check_guides(report, base)
    check_labels(report, base, tools)
    report.section("Sharp convex edge audit")
    allowances = _edge_allow(base, tools)
    survey = sharp_convex_edges(base, allow=allowances)
    for _, reason in allowances:
        report.lines.append(f"  allowed: {reason}")
    for bucket, edges in (
        ("sharp", survey.sharp),
        ("unclassifiable", survey.unclassifiable),
    ):
        detail = "; ".join(
            f"{edge.center()} length={edge.length:.3f}" for edge in edges
        )
        report.check(
            not edges,
            f"no unexplained {bucket} convex edges",
            f"{len(edges)}: {detail}" if edges else "0",
        )
    return report


def handles_model(name: str) -> bool:
    return name == "drill_storage.hex.bits_double.base"


def run_model(name: str) -> Report:
    if not handles_model(name):
        raise ValueError(f"unsupported model: {name}")
    return run()


def main() -> None:
    report = run()
    print(report.render())
    if report.failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
