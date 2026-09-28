"""Physical gates for the removable lid, bin rim, and matching stacked feet."""

from typing import Any

from build123d import Pos

from models.lib.checks import Report, is_solid_at
from . import config as c, create as seated, lid
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
        printed = lid.create(
            **{
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
        )
        # The public scene seats a clean lid; the printed leaf includes supports.
        body_height = body.bounding_box().max.Z
        roof_top = body_height + c.LID_ROOF + c.LID_SOCKET_DEPTH
        print_box = printed.bounding_box()
        report.check(
            len(printed.solids()) == 1 and abs(print_box.min.Z) < 0.01,
            "lattice is joined to one print-pose lid",
            f"solids={len(printed.solids())}, z={print_box.min.Z:.3f}",
        )
        joint_overlap = _overlap(body, closed_lid)
        report.check(
            joint_overlap < 0.01,
            "lift-off skirt enters bin without collision",
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
    return report


def main() -> None:
    report = run()
    print(report.render())
    if report.failures:
        raise SystemExit(1)
