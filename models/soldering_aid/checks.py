"""Geometry checks for the SP16/SP17 soldering aid."""

from __future__ import annotations

import sys


from models.lib.checks import Report, is_solid_at

from . import HOLE_SPACING, PLATE_DEPTH, PLATE_THICKNESS, SUPPORT_HEIGHT, WIDTH, create


def run() -> Report:
    report = Report()
    part = create()
    box = part.bounding_box()
    report.section("soldering aid")
    report.check(
        abs(box.min.Z) < 0.01, "print pose sits on z=0", f"min z={box.min.Z:.3f}"
    )
    report.check(
        abs(box.size.X - WIDTH) < 0.01,
        "aid spans both connectors",
        f"width={box.size.X:.2f}",
    )
    report.check(
        HOLE_SPACING < box.size.X,
        "connector spacing fits aid",
        f"spacing={HOLE_SPACING:.1f}",
    )
    report.check(
        len(part.solids()) == 1,
        "aid is one printed solid",
        f"solids={len(part.solids())}",
    )
    report.check(
        is_solid_at(part, 0, 0, PLATE_THICKNESS / 2),
        "lower leg supports the connectors",
    )
    report.check(
        is_solid_at(part, 0, PLATE_DEPTH / 2 - PLATE_THICKNESS / 2, SUPPORT_HEIGHT / 2),
        "rear leg forms the L-profile",
    )
    report.check(
        not is_solid_at(part, 0, 0, SUPPORT_HEIGHT / 2),
        "L-profile keeps its open corner",
    )
    return report


def main() -> None:
    report = run()
    print(report.render())
    sys.exit(1 if report.failures else 0)


if __name__ == "__main__":
    main()
