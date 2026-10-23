"""Physical gates for the removable lid, bin rim, and matching stacked feet."""

from typing import Any

from build123d import Part, Pos

from models.lib.gridfinity import (
    BASE_H,
    GRID,
    HEIGHT_UNIT,
    PAD,
)
from models.drill_storage.stackable_checks import check_split_lips
from models.lib.edges import as_part
from models.lib.checks import Report, is_solid_at, sharp_convex_edges
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
        finished = lid._create_finished(**lid_options)
        body_height = body.bounding_box().max.Z
        roof_top = body_height + c.LID_ROOF + c.LID_SOCKET_DEPTH
        print_box = finished.bounding_box()
        report.check(
            finished.is_valid
            and len(finished.solids()) == 1
            and abs(print_box.min.Z) < 0.01,
            "clean assembled reference is one valid socket-down lid",
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
                        lambda edge: abs(abs(edge.center().X) - PAD / 2) < 0.01
                        and abs(edge.center().Z - BASE_H) < 0.01,
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
                finished,
                width=options.get("grid_x", 1) * GRID - (GRID - PAD),
                depth=options.get("grid_y", 2) * GRID - (GRID - PAD),
                wall=options.get("wall_thickness", c.WALL),
                height=options.get("height_u", 5) * HEIGHT_UNIT,
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
        report.check(
            not is_solid_at(finished, print_x, print_y, 1)
            and is_solid_at(finished, print_x, print_y, c.LID_SOCKET_DEPTH + 0.5),
            "socket remains open beneath its solid roof without sacrificial material",
            "sample at first socket centre",
        )
        check_split_lips(
            report,
            printed,
            finished,
            c.LID_SOCKET_DEPTH,
        )
    split_cases: tuple[tuple[str, dict[str, Any]], ...] = (
        ("minimum half-cell lid", {"grid_x": 0.5, "grid_y": 0.5}),
        ("all-half-cell lid", {"grid_x": 1, "grid_y": 1, "half_grid_base": True}),
    )
    for name, options in split_cases:
        report.section(name)
        check_split_lips(
            report,
            lid.create(**options),
            lid._create_finished(**options),
            c.LID_SOCKET_DEPTH,
        )
    report.section("taller split lid")
    check_split_lips(
        report,
        lid.create(lid_height=9),
        lid._create_finished(lid_height=9),
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
