"""Geometry checks for the thin-wall SP16/SP17 soldering aid."""

from __future__ import annotations

import sys

from models.lib.checks import Report, is_solid_at

from . import (
    BASE_DEPTH,
    HOLE_OFFSETS,
    HOLE_SPACING,
    HOLE_Y,
    HOLE_Z,
    SIDE_MARGIN_TOLERANCE,
    SP16_THREAD_RADIUS,
    SP17_THREAD_RADIUS,
    SUPPORT_HEIGHT,
    THREAD_LENGTH,
    WALL_THICKNESS,
    WIDTH,
    create,
)


def run() -> Report:
    report = Report()
    part = create()
    box = part.bounding_box()
    report.section("soldering aid")
    report.check(
        abs(box.min.Z) < 0.01,
        "print pose sits on z=0",
        f"min z={box.min.Z:.3f}",
    )
    report.check(
        abs(box.size.X - WIDTH) < 0.01,
        "aid spans both connectors",
        f"width={box.size.X:.2f}",
    )
    report.check(
        abs(box.size.Y - BASE_DEPTH) < 0.01,
        "aid depth includes the rear wall",
        f"depth={box.size.Y:.2f}",
    )
    report.check(
        abs(box.size.Z - SUPPORT_HEIGHT) < 0.01,
        "rear wall is 50 percent taller",
        f"height={box.size.Z:.2f}",
    )
    actual_spacing = HOLE_OFFSETS[1] - HOLE_OFFSETS[0]
    report.check(
        abs(actual_spacing - HOLE_SPACING) < 0.01,
        "connector spacing fits aid",
        f"spacing={actual_spacing:.1f}",
    )
    left_margin = WIDTH / 2 + HOLE_OFFSETS[0] - SP16_THREAD_RADIUS
    right_margin = WIDTH / 2 - HOLE_OFFSETS[1] - SP17_THREAD_RADIUS
    report.check(
        abs(left_margin - right_margin) < SIDE_MARGIN_TOLERANCE,
        "holes have similar side margins",
        f"left={left_margin:.2f}, right={right_margin:.2f}",
    )
    report.check(
        len(part.solids()) == 1,
        "aid is one printed solid",
        f"solids={len(part.solids())}",
    )
    report.check(
        is_solid_at(part, 0, 0, WALL_THICKNESS / 2),
        "lower leg supports the connectors",
    )
    report.check(
        is_solid_at(part, 0, BASE_DEPTH / 2 - WALL_THICKNESS / 2, SUPPORT_HEIGHT / 2),
        "rear wall is a thin upright",
    )
    report.check(
        not is_solid_at(part, 0, 0, SUPPORT_HEIGHT / 2),
        "L-profile keeps its open corner",
    )
    for offset in HOLE_OFFSETS:
        report.check(
            not is_solid_at(
                part,
                offset,
                HOLE_Y + THREAD_LENGTH / 2,
                HOLE_Z,
            ),
            "connector bore is threaded through the long side",
            f"x={offset:.1f}",
        )
    return report


def main() -> None:
    report = run()
    print(report.render())
    sys.exit(1 if report.failures else 0)


if __name__ == "__main__":
    main()
