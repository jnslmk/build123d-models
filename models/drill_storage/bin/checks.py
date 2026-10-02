"""Physical gates for the removable lid, bin rim, and matching stacked feet."""

from math import sqrt
from typing import Any

from build123d import Align, Box, BuildPart, Locations, Mode, Part, Pos, add

from models.drill_storage.box import FOOT_C1, FOOT_C3
from models.drill_storage.stackable_checks import check_split_lips
from models.lib.edges import as_part
from models.lib.checks import Report, is_solid_at, sharp_convex_edges, solid_probe
from . import base, config as c, create as seated, lid
from .foot import cell_layout


def _overlap(a, b) -> float:
    intersection = a & b
    if not intersection:
        return 0.0
    return (
        intersection.volume
        if hasattr(intersection, "volume")
        else sum(solid.volume for solid in intersection)
    )


def _window(
    part: Part, x: float, y: float, w: float, d: float, z: float, h: float
) -> Part:
    """Measure existing material in a cell/layer window, not a model constant."""
    with BuildPart() as cut:
        add(part)
        with Locations((x, y, z)):
            Box(
                w,
                d,
                h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.INTERSECT,
            )
    return cut.part


def _check_supports(
    report: Report,
    printed: Part,
    clean: Part,
    x_cells: list[tuple[float, float]],
    y_cells: list[tuple[float, float]],
) -> None:
    """Consumer-visible support predicates, also usable on broken specimens."""
    box = printed.bounding_box()
    report.check(
        printed.is_valid and len(printed.solids()) == 1 and abs(box.min.Z) < 1e-6,
        "supported lid is one valid connected solid on z=0",
    )
    report.check(
        clean.is_valid
        and len(clean.solids()) == 1
        and abs(clean.bounding_box().min.Z) < 1e-6,
        "support-off lid is one valid clean solid on z=0",
    )
    missing = clean.volume - _overlap(clean, printed)
    with BuildPart() as extra:
        add(printed)
        add(clean, mode=Mode.SUBTRACT)
    supports = extra.part
    report.check(
        abs(missing) < 1e-5
        and supports.volume > 1
        and supports.bounding_box().max.Z <= c.LID_SOCKET_DEPTH + 1e-5,
        "support toggle preserves all finished geometry and adds only socket material",
        f"missing clean volume={missing:.6f} mm³",
    )
    if supports.volume <= 1:
        return
    probe = solid_probe(printed)
    # Roof-free wall geometry catches any lateral weld, including at corners.
    walls = _window(
        clean, 0, 0, box.size.X + 1, box.size.Y + 1, 0, c.LID_SOCKET_DEPTH - 0.05
    )
    inset = FOOT_C1 + FOOT_C3
    roof_r = c.CORNER_R - inset + lid.STACK_FIT / 2
    for cell_x, x in x_cells:
        for cell_y, y in y_cells:
            w = cell_x * c.GRID - (c.GRID - c.PAD)
            d = cell_y * c.GRID - (c.GRID - c.PAD)
            label = f"socket ({x:g}, {y:g}), {cell_x:g}×{cell_y:g}"
            # Stop below the release gap so tabs cannot mask detached rib/rail
            # islands. Full and half-cell bodies must each reach the bed.
            body = _window(supports, x, y, w, d, 0, c.LID_SOCKET_DEPTH - 0.21)
            body_solids = body.solids()
            bed_z = body.bounding_box().min.Z if body_solids else float("inf")
            report.check(
                body.is_valid and len(body_solids) == 1 and abs(bed_z) < 1e-6,
                f"{label}: rail and lattice form one bed-seated support body",
                f"components={len(body_solids)}, z={bed_z:.6f}",
            )
            side_material = _window(supports, x, y, w, d, 0, c.LID_SOCKET_DEPTH - 0.05)
            separation = side_material.distance_to(walls) if body_solids else 0
            report.check(
                separation >= 0.59,
                f"{label}: support has positive separation from every socket wall",
                f"minimum separation={separation:.3f} mm",
            )
            hx = (w - 2 * inset + lid.STACK_FIT) / 2
            hy = (d - 2 * inset + lid.STACK_FIT) / 2
            # Probe 0.75 mm inward of the actual roof contour: beyond the old
            # full-cell lattice by 2.11 mm, and off all centre-grid ribs.
            edge_points = [
                (x + sign * (hx - 0.75), y + along)
                for sign in (-1, 1)
                for along in (-2.5, 2.5)
            ] + [
                (x + along, y + sign * (hy - 0.75))
                for sign in (-1, 1)
                for along in (-2.5, 2.5)
            ]
            corner_offset = (roof_r - 0.75) / sqrt(2)
            edge_points += [
                (
                    x + sx * (hx - roof_r + corner_offset),
                    y + sy * (hy - roof_r + corner_offset),
                )
                for sx in (-1, 1)
                for sy in (-1, 1)
            ]
            report.check(
                all(probe(px, py, c.LID_SOCKET_DEPTH - 0.25) for px, py in edge_points),
                f"{label}: straight-edge bands and all rounded corners have backing",
                "full-cell probes extend >2 mm beyond the old 30.8 mm lattice",
            )
            report.check(
                probe(x, y, c.LID_SOCKET_DEPTH - 0.21)
                and not probe(x, y, c.LID_SOCKET_DEPTH - 0.19)
                and all(
                    not probe(px, py, c.LID_SOCKET_DEPTH - 0.1)
                    for px, py in [(x, y), *edge_points]
                )
                and is_solid_at(clean, x, y, c.LID_SOCKET_DEPTH + 0.01),
                f"{label}: nominal 0.2 mm roof gap remains away from tabs",
                "body ends within 0.01 mm of z=2.3; gap/roof independently probed",
            )
            # A thin actual-material slice counts EVERY welded path through the
            # gap; four old nibs, a filled gap or widened tabs cannot pass.
            necks = _window(supports, x, y, w, d, c.LID_SOCKET_DEPTH - 0.1, 0.05)
            sections = necks.solids()
            areas = [solid.volume / 0.05 for solid in sections]
            report.check(
                len(sections) == 2
                and all(0.28 <= area <= 0.36 for area in areas)
                and 0.56 <= sum(areas) <= 0.72,
                f"{label}: exactly two deliberately bounded weak attachments",
                f"neck sections={areas} mm²; old total was 1.44 mm²",
            )
            along_y = d >= w
            midpoint = (hy if along_y else hx) - 1.0
            centres = []
            narrow = []
            wide = []
            for solid in sections:
                bounds = solid.bounding_box()
                centres.append(
                    (
                        (bounds.min.X + bounds.max.X) / 2 - x,
                        (bounds.min.Y + bounds.max.Y) / 2 - y,
                    )
                )
                narrow.append(bounds.size.X if along_y else bounds.size.Y)
                wide.append(bounds.size.Y if along_y else bounds.size.X)
            expected = [
                (0, sign * midpoint) if along_y else (sign * midpoint, 0)
                for sign in (-1, 1)
            ]
            report.check(
                len(centres) == 2
                and all(
                    any(
                        abs(px - ex) < 0.05 and abs(py - ey) < 0.05
                        for px, py in centres
                    )
                    for ex, ey in expected
                )
                and all(0.35 <= value <= 0.45 for value in narrow)
                and all(0.75 <= value <= 0.85 for value in wide),
                f"{label}: one-bead tabs sit at accessible straight rail midpoints",
                f"centres={centres}, narrow={narrow}, across rail={wide} mm",
            )


def _check_snap_fit(
    report: Report,
    body: Part,
    lid_part: Part,
    width: float,
    depth: float,
    wall: float,
    height: float,
    lid_height: float,
) -> None:
    """Verify the lid's snap bead and the bin's groove."""
    skirt_w = width - 2 * wall - lid.PLUG_FIT
    inner_w = width - 2 * wall
    bead_z = lid_height - c.SNAP_Z
    groove_z = height - (c.LID_SKIRT_MIN - c.SNAP_Z)
    # The bead protrudes from the skirt.
    report.check(
        is_solid_at(lid_part, skirt_w / 2 + c.SNAP_PROTRUSION / 2, 0, bead_z),
        "lid skirt carries the snap bead",
    )
    # The groove is cut into the bin's inner wall.
    report.check(
        not is_solid_at(body, inner_w / 2 + c.SNAP_PROTRUSION / 2, 0, groove_z),
        "bin inner wall carries the snap groove",
    )


def run() -> Report:
    report = Report()
    cases: tuple[tuple[str, dict[str, Any]], ...] = (
        ("default 1×2", {}),
        (
            "offset half-grid 1.5×1.5",
            {
                "grid_x": 1.5,
                "grid_y": 1.5,
                "half_grid_right": False,
                "half_grid_top": True,
            },
        ),
        (
            "organized 1×1",
            {
                "grid_y": 1,
                "labels": True,
                "dividers": True,
                "dividers_x": 1,
                "dividers_y": 1,
                "scoops": True,
            },
        ),
    )
    for name, options in cases:
        report.section(name)
        scene = seated(**options)
        body, closed_lid = scene.solids()
        body_part = as_part(body)
        lid_options = {
            key: value
            for key, value in options.items()
            if key
            in (
                "grid_x",
                "grid_y",
                "half_grid_base",
                "half_grid_right",
                "half_grid_top",
                "wall_thickness",
            )
        }
        printed = lid.create(**lid_options)
        # The public scene seats a clean lid; the printed leaf includes supports.
        body_height = body.bounding_box().max.Z
        roof_top = body_height + c.LID_ROOF + c.LID_SOCKET_DEPTH
        print_box = printed.bounding_box()
        report.check(
            len(printed.solids()) == 1 and abs(print_box.min.Z) < 0.01,
            "lattice is joined to one print-pose lid",
            f"solids={len(printed.solids())}, z={print_box.min.Z:.3f}",
        )
        if not options:
            report.check(
                len(body.solids()) == 1 and abs(body.bounding_box().min.Z) < 0.01,
                "bin has one connected solid seated on the print bed",
            )
            report.check(
                is_solid_at(body_part, 5, -16, 0.5)
                and not is_solid_at(body_part, 5, -16, 1.5)
                and not is_solid_at(body_part, 5, -16, 5)
                and is_solid_at(body_part, 5, 0, 5),
                "closed 1 mm foot plates open into the cavity with a cell seam",
                "per-cell floor at z=1, raised seam between the two feet",
            )
            # The two square foot-to-body shoulders preserve the Gridfinity
            # transition. No other exposed edge may be left raw.
            survey = sharp_convex_edges(
                body_part,
                allow=(
                    (
                        lambda edge: abs(abs(edge.center().X) - c.PAD / 2) < 0.01
                        and abs(edge.center().Z - c.BASE_H) < 0.01,
                        "foot-to-body shoulders retain the Gridfinity transition",
                    ),
                    (
                        lambda edge: body_height
                        - (c.LID_SKIRT_MIN - c.SNAP_Z)
                        - c.SNAP_GROOVE_FLOOR
                        - 0.01
                        < edge.center().Z
                        < body_height
                        - (c.LID_SKIRT_MIN - c.SNAP_Z)
                        + c.SNAP_GROOVE_ROOF
                        + 0.01,
                        "snap groove edges are functional",
                    ),
                ),
            )
            report.check(
                not survey.sharp and not survey.unclassifiable,
                "floor and rim have no untreated convex edges",
                f"sharp={len(survey.sharp)}, unclassifiable={len(survey.unclassifiable)}; "
                "2 square outer foot shoulders intentionally excepted",
            )
            _check_snap_fit(
                report,
                body_part,
                printed,
                width=options.get("grid_x", 1) * c.GRID - (c.GRID - c.PAD),
                depth=options.get("grid_y", 2) * c.GRID - (c.GRID - c.PAD),
                wall=options.get("wall_thickness", c.WALL),
                height=options.get("height_u", 5) * c.HEIGHT_UNIT,
                lid_height=c.LID_MIN_HEIGHT,
            )
        joint_overlap = _overlap(body, closed_lid)
        report.check(
            joint_overlap < 0.01,
            "seated lid enters bin without collision",
            f"overlap={joint_overlap:.4f} mm³",
        )
        width = options.get("grid_x", 1)
        depth = options.get("grid_y", 2)
        upper = Pos(0, 0, roof_top - c.LID_SOCKET_DEPTH) * body
        upper_overlap = _overlap(closed_lid, upper)
        report.check(
            upper_overlap < 0.01,
            "matching upper Gridfinity foot enters every socket",
            f"overlap={upper_overlap:.4f} mm³",
        )
        lower = Pos(0, 0, roof_top - c.LID_SOCKET_DEPTH - 0.3) * body
        lower_overlap = _overlap(closed_lid, lower)
        report.check(
            lower_overlap > 0.1,
            "socket has a floor supporting the foot",
            f"0.3 mm over-travel overlaps {lower_overlap:.2f} mm³",
        )
        print_y = cell_layout(
            depth,
            options.get("half_grid_base", False),
            not options.get("half_grid_top", True),
        )[0][1]
        print_x = cell_layout(
            width,
            options.get("half_grid_base", False),
            options.get("half_grid_right", True),
        )[0][1]
        cleared = lid.create(
            grid_x=width,
            grid_y=depth,
            half_grid_right=options.get("half_grid_right", True),
            half_grid_top=options.get("half_grid_top", True),
            support=False,
        )
        report.check(
            is_solid_at(printed, print_x, print_y, 1)
            and not is_solid_at(cleared, print_x, print_y, 1)
            and is_solid_at(cleared, print_x, print_y, c.LID_SOCKET_DEPTH + 0.5),
            "removed lattice exposes socket beneath solid roof",
            "sample at first socket centre",
        )
        _check_supports(
            report,
            printed,
            cleared,
            cell_layout(
                width,
                options.get("half_grid_base", False),
                options.get("half_grid_right", True),
            ),
            cell_layout(
                depth,
                options.get("half_grid_base", False),
                not options.get("half_grid_top", True),
            ),
        )
        check_split_lips(
            report,
            lid.create(**lid_options, separate_stacking_lips=True),
            cleared,
            c.LID_SOCKET_DEPTH,
        )
    support_cases: tuple[tuple[str, dict[str, Any]], ...] = (
        ("minimum half-cell lid", {"grid_x": 0.5, "grid_y": 0.5}),
        ("all-half-cell lid", {"grid_x": 1, "grid_y": 1, "half_grid_base": True}),
    )
    for name, options in support_cases:
        report.section(name)
        _check_supports(
            report,
            lid.create(**options),
            lid.create(**options, support=False),
            cell_layout(options["grid_x"], options.get("half_grid_base", False), True),
            cell_layout(options["grid_y"], options.get("half_grid_base", False), False),
        )
        check_split_lips(
            report,
            lid.create(**options, separate_stacking_lips=True),
            lid.create(**options, support=False),
            c.LID_SOCKET_DEPTH,
        )
    report.section("taller split lid")
    check_split_lips(
        report,
        lid.create(lid_height=9, separate_stacking_lips=True),
        lid.create(lid_height=9, support=False),
        c.LID_SOCKET_DEPTH,
    )
    report.section("base variants")
    thicker = base.create(bottom_thickness=2)
    report.check(
        is_solid_at(thicker, 5, -16, 1.5) and not is_solid_at(thicker, 5, -16, 2.5),
        "bottom thickness thickens the print-bed plate without filling the cavity",
    )
    solid = base.create(ultra_light_base=False)
    report.check(
        is_solid_at(solid, 5, -16, 0.5) and is_solid_at(solid, 5, -16, 5),
        "solid-base option retains a solid floor",
    )
    return report


def main() -> None:
    report = run()
    print(report.render())
    if report.failures:
        raise SystemExit(1)
