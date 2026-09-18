"""Geometry checks for the thin-wall SP16/SP17 soldering aid."""

from __future__ import annotations

import sys

from build123d import Edge, GeomType

from models.lib.checks import Report, is_solid_at, sharp_convex_edges

from . import (
    BASE_DEPTH,
    HOLE_OFFSETS,
    HOLE_SPACING,
    HOLE_Z,
    INNER_CHAMFER,
    LEFT_THREAD_RADIUS,
    RIGHT_THREAD_RADIUS,
    SIDE_MARGIN_TOLERANCE,
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
        abs(box.size.Y - SUPPORT_HEIGHT) < 0.01,
        "threaded plate lies flat on the heatbed",
        f"bed depth={box.size.Y:.2f}",
    )
    report.check(
        abs(box.size.Z - BASE_DEPTH) < 0.01,
        "former lower leg rises from the bed",
        f"height={box.size.Z:.2f}",
    )
    actual_spacing = HOLE_OFFSETS[1] - HOLE_OFFSETS[0]
    report.check(
        abs(actual_spacing - HOLE_SPACING) < 0.01,
        "connector spacing fits aid",
        f"spacing={actual_spacing:.1f}",
    )
    left_margin = WIDTH / 2 + HOLE_OFFSETS[0] - LEFT_THREAD_RADIUS
    right_margin = WIDTH / 2 - HOLE_OFFSETS[1] - RIGHT_THREAD_RADIUS
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
        is_solid_at(part, 0, WALL_THICKNESS / 2, BASE_DEPTH / 2),
        "former lower leg rises as a side support",
    )
    report.check(
        is_solid_at(part, 0, SUPPORT_HEIGHT / 2, WALL_THICKNESS / 2),
        "threaded rear wall lies on the heatbed",
    )
    report.check(
        not is_solid_at(part, 0, SUPPORT_HEIGHT / 2, BASE_DEPTH / 2),
        "L-profile keeps its open corner",
    )
    chamfer_inside = WALL_THICKNESS + INNER_CHAMFER / 4
    chamfer_outside = WALL_THICKNESS + INNER_CHAMFER * 3 / 4
    report.check(
        is_solid_at(part, 0, chamfer_inside, chamfer_inside)
        and not is_solid_at(part, 0, chamfer_outside, chamfer_outside),
        "full-width triangular chamfer reinforces the inner corner",
    )
    for offset, radius in zip(
        HOLE_OFFSETS,
        (LEFT_THREAD_RADIUS, RIGHT_THREAD_RADIUS),
        strict=True,
    ):
        thread_edges = [
            edge
            for edge in part.edges()  # ty: ignore[invalid-argument-type]
            if edge.geom_type == GeomType.BSPLINE
            and ((edge.center().X - offset) ** 2 + (edge.center().Y - HOLE_Z) ** 2)
            < (radius + 0.5) ** 2
            and edge.bounding_box().size.Z > THREAD_LENGTH / 4
        ]
        report.check(
            bool(thread_edges),
            "connector bore contains helical thread flanks",
            f"x={offset:.1f}, edges={len(thread_edges)}",
        )
        report.check(
            not is_solid_at(
                part,
                offset,
                HOLE_Z,
                THREAD_LENGTH / 2,
            ),
            "connector bore opens vertically through the bed-facing plate",
            f"x={offset:.1f}",
        )

    def is_thread_edge(edge: Edge) -> bool:
        box = edge.bounding_box()
        center = box.center()
        return (
            box.min.Z >= -0.01
            and box.max.Z <= THREAD_LENGTH + 0.01
            and any(
                (center.X - offset) ** 2 + (center.Y - HOLE_Z) ** 2
                < (radius + 0.5) ** 2
                for offset, radius in zip(
                    HOLE_OFFSETS,
                    (LEFT_THREAD_RADIUS, RIGHT_THREAD_RADIUS),
                    strict=True,
                )
            )
        )

    def is_full_width_end(edge: Edge) -> bool:
        box = edge.bounding_box()
        return edge.geom_type == GeomType.LINE and (
            (abs(box.min.X + WIDTH / 2) < 0.01 and abs(box.max.X + WIDTH / 2) < 0.01)
            or (abs(box.min.X - WIDTH / 2) < 0.01 and abs(box.max.X - WIDTH / 2) < 0.01)
        )

    survey = sharp_convex_edges(
        part,
        allow=(
            (
                is_thread_edge,
                "thread flanks are mating surfaces; the direct-seat mouths stay "
                "square to preserve the full 2 mm engagement",
            ),
            (
                is_full_width_end,
                "side-face edges stay square so the reinforcement reaches the "
                "full part width",
            ),
        ),
    )
    report.check(
        not survey.sharp,
        "no unexplained sharp convex edges remain",
        f"sharp={len(survey.sharp)}",
    )
    report.check(
        not survey.unclassifiable,
        "every long edge is geometrically classified or explained",
        f"unclassifiable={len(survey.unclassifiable)}",
    )
    return report


def main() -> None:
    report = run()
    print(report.render())
    sys.exit(1 if report.failures else 0)


if __name__ == "__main__":
    main()
