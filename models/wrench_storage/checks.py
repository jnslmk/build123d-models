"""Physical gate for the bin anchor, including a missing-notch negative control.

Photo envelopes and their upward sweeps prove only consumer-model clearance.
They do not certify photo accuracy, the illustrative thickness transitions or
fit of the real wrenches. A printed trial and human anchor acceptance are pending.
"""

import sys
from math import sqrt
from typing import cast

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    Shape,
    add,
    extrude,
)

from models.lib.checks import Report, sharp_convex_edges
from models.lib.gridfinity import BASE_H, CORNER_R, FOOT_C1, FOOT_STRAIGHT, GRID, PAD

from . import base
from . import config as c
from . import layout as l
from . import preview
from . import profiles as p

VOLUME_TOL = 1e-5


def overlap_volume(first: Part, second: Part) -> float:
    with BuildPart() as common:
        add(first)
        add(second, mode=Mode.INTERSECT)
    return common.part.volume


def check_slots(report: Report, part: Part, layout: l.Layout) -> None:
    """Independent probes at measured widths and raw whole-band contact bounds."""
    for column in layout.columns:
        for station, distance in enumerate(p.HANDLE_STATIONS):
            y = l.TOOL_START_Y + distance
            for lane in column.lanes:
                name = f"{lane.wrench.label} rack {station + 1}"
                raw_min, raw_max = p.HANDLE_SPANS[lane.wrench.label][station]
                floor = l.SEAT_Z + raw_min - l.SLOT_FLOOR_RESERVE
                width = lane.wrench.handle_thickness + c.SLOT_CLEARANCE
                height = min(
                    column.rack_top - l.EDGE_BREAK - 0.1, l.SEAT_Z + raw_max - 0.1
                )
                probes = (
                    (lane.x + dx, y + dy, z)
                    for dx in (-width / 2 + 0.01, 0, width / 2 - 0.01)
                    for dy in (
                        -c.RACK_THICKNESS / 2 + 0.1,
                        0,
                        c.RACK_THICKNESS / 2 - 0.1,
                    )
                    for z in (floor + 0.02, height)
                )
                report.check(
                    all(not report.solid_at(part, *point) for point in probes),
                    f"{name}: slot void at full free-fit width",
                )
                report.check(
                    report.solid_at(part, lane.x, y, floor - 0.02),
                    f"{name}: bearing floor exists at raw-band underside",
                )
                report.check(
                    column.rack_top - floor >= l.SLOT_ENGAGEMENT + l.EDGE_BREAK - 1e-8,
                    f"{name}: lateral engagement",
                )
                # Independent raw handle rectangle over the entire proven band.
                with BuildPart() as raw_handle:
                    with Locations((lane.x, y, l.SEAT_Z + raw_min)):
                        Box(
                            lane.wrench.handle_thickness,
                            c.RACK_THICKNESS,
                            raw_max - raw_min,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                        )
                volume = overlap_volume(part, raw_handle.part)
                report.check(
                    volume < VOLUME_TOL,
                    f"{name}: raw full-band handle clearance",
                    f"photo-only rectangle overlap {volume:.6g} mm³",
                )
            for left, right in zip(column.lanes, column.lanes[1:]):
                x0 = left.x + (left.wrench.handle_thickness + c.SLOT_CLEARANCE) / 2
                x1 = right.x - (right.wrench.handle_thickness + c.SLOT_CLEARANCE) / 2
                z = column.rack_top - l.SLOT_LEAD / 2
                # At the lead-in midpoint the tooth must still carry a full 1 mm
                # transverse section, not merely a single solid center point.
                center = (x0 + x1) / 2
                points = (
                    (center + dx, y, z)
                    for dx in (-c.WALL / 2 + 0.001, 0, c.WALL / 2 - 0.001)
                )
                report.check(
                    x1 - x0 - 2 * l.SLOT_LEAD >= c.WALL - 1e-8
                    and all(report.solid_at(part, *point) for point in points),
                    f"{left.wrench.label}/{right.wrench.label} rack {station + 1}: printable tooth",
                )


def _check_base(report: Report, part: Part, layout: l.Layout) -> None:
    bbox = part.bounding_box()
    report.check(part.is_valid and len(part.solids()) == 1, "one valid connected solid")
    report.check(abs(bbox.min.Z) < 1e-6, "foot-down at z=0", f"min.Z={bbox.min.Z:.6g}")
    report.check(
        abs(bbox.max.Z - max(l.RIM_Z, *(col.rack_top for col in layout.columns)))
        < 1e-6,
        "low rim / racks define height, no cover",
    )
    with BuildPart() as cell_union:
        with BuildSketch(Plane.XY.offset(-1)):
            for x, y in sorted(layout.occupied):
                with Locations((x * GRID, y * GRID)):
                    Rectangle(GRID, GRID)
        extrude(amount=bbox.max.Z + 2)
    with BuildPart() as escaped:
        add(part)
        add(cell_union.part, mode=Mode.SUBTRACT)
    report.check(
        escaped.part.volume < VOLUME_TOL,
        "occupied-foot containment",
        f"escaped={escaped.part.volume:.6g} mm³",
    )
    for x in range(len(layout.columns)):
        for y in range(max(col.cells for col in layout.columns)):
            if (x, y) not in layout.occupied:
                with BuildPart() as omitted:
                    with Locations((x * GRID, y * GRID, -1)):
                        Box(
                            PAD - 0.1,
                            PAD - 0.1,
                            bbox.max.Z + 2,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                        )
                volume = overlap_volume(part, omitted.part)
                report.check(
                    volume < VOLUME_TOL,
                    f"omitted stepped cell {x},{y} is empty",
                    f"overlap={volume:.6g} mm³",
                )
    for x, y in sorted(layout.occupied):
        xx, yy = x * GRID, y * GRID
        report.check(
            all(
                report.solid_at(part, xx + dx, yy + dy, z)
                for dx in (-10, 0, 10)
                for dy in (-10, 0, 10)
                for z in (0.05, l.BED_THICKNESS - 0.01)
            ),
            f"cell {x},{y}: closed minimum bed plate",
        )
        report.check(
            not report.solid_at(part, xx, yy, l.BED_THICKNESS + 0.05),
            f"cell {x},{y}: hollow foot interior",
        )
        # Probe each exposed straight perimeter through the 1 mm wall section.
        for nx, ny in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (x + nx, y + ny) not in layout.occupied:
                points = (
                    (
                        xx + nx * (PAD / 2 - depth),
                        yy + ny * (PAD / 2 - depth),
                        l.RIM_Z - 1,
                    )
                    for depth in (0.01, c.WALL / 2, c.WALL - 0.01)
                )
                report.check(
                    all(report.solid_at(part, *point) for point in points),
                    f"cell {x},{y} wall {nx},{ny}: 1 mm section",
                )
        # Normal (not XY) thickness on the 45-degree foot shoulder, including
        # its rounded corners. These samples detect a nominal 1 mm XY offset
        # accidentally producing only 0.707 mm of normal wall.
        z0 = BASE_H - 1.2
        radial = CORNER_R - (BASE_H - z0)
        corner_center = PAD / 2 - CORNER_R
        for sx in (-1, 1):
            for sy in (-1, 1):
                points = (
                    (
                        xx + sx * (corner_center + radial / sqrt(2) - depth / 2),
                        yy + sy * (corner_center + radial / sqrt(2) - depth / 2),
                        z0 + depth / sqrt(2),
                    )
                    for depth in (0.01, 0.5, c.WALL - 0.01)
                )
                report.check(
                    all(report.solid_at(part, *point) for point in points),
                    f"cell {x},{y} corner {sx},{sy}: 1 mm normal foot wall",
                )
    # Curve-normal wall probes also cover the actual rounded tray corners and
    # concave step offsets, rather than trusting straight section widths.
    outside = base.footprint(layout)
    with BuildPart() as filled:
        with BuildSketch(Plane.XY.offset(l.RIM_Z - 1.5)):
            add(outside)
        extrude(amount=1)
    for index, edge in enumerate(cast(Shape, outside).edges()):
        point = edge.position_at(0.5)
        tangent = edge.tangent_at(0.5)
        normal = (-tangent.Y, tangent.X)
        norm = sqrt(normal[0] ** 2 + normal[1] ** 2)
        nx, ny = normal[0] / norm, normal[1] / norm
        if not report.solid_at(
            filled.part,
            point.X + nx * c.WALL / 2,
            point.Y + ny * c.WALL / 2,
            l.RIM_Z - 1,
        ):
            nx, ny = -nx, -ny
        samples = (
            (point.X + nx * depth, point.Y + ny * depth, l.RIM_Z - 1)
            for depth in (0.01, 0.5, c.WALL - 0.01)
        )
        report.check(
            all(report.solid_at(part, *sample) for sample in samples),
            f"tray perimeter edge {index}: 1 mm normal wall below edge breaks",
        )
    # Every lane's rack material continues through the hollow feet to its bed
    # plate. No rack starts at 5.4 mm over an unsupported 30+ mm cavity span.
    for column in layout.columns:
        for station, distance in enumerate(p.HANDLE_STATIONS):
            y = l.TOOL_START_Y + distance
            for lane in column.lanes:
                levels = (
                    0.5,
                    l.BED_THICKNESS + 0.1,
                    2.0,
                    BASE_H - 0.1,
                    BASE_H + 0.1,
                    lane.floor_z(station) - 0.1,
                )
                report.check(
                    all(report.solid_at(part, lane.x, y, z) for z in levels),
                    f"{lane.wrench.label} rack {station + 1}: supported root to bed",
                )


def _check_tools(report: Report, part: Part, layout: l.Layout) -> None:
    tools = []
    sweeps = []
    for column in layout.columns:
        for lane in column.lanes:
            tool = preview.tool_envelope(lane)
            tools.append(tool)
            report.check(
                tool.is_valid and len(tool.solids()) == 1,
                f"{lane.wrench.label}: valid photo consumer envelope",
            )
            volume = overlap_volume(part, tool)
            report.check(
                volume < VOLUME_TOL,
                f"{lane.wrench.label}: photo silhouette clears actual walls/racks",
                f"overlap={volume:.6g} mm³; display tolerance {l.PREVIEW_ERROR:.3f} mm, not metrology",
            )
            lift = part.bounding_box().max.Z - l.SEAT_Z + 1
            sweep = preview.tool_envelope(lane, lift=lift)
            sweeps.append(sweep)
            volume = overlap_volume(part, sweep)
            report.check(
                volume < VOLUME_TOL,
                f"{lane.wrench.label}: continuous straight-up photo removal sweep",
                f"overlap={volume:.6g} mm³; illustrative thickness map",
            )
            report.check(
                tool.bounding_box().max.Z > l.RIM_Z + c.FUTURE_LID_HEADROOM,
                f"{lane.wrench.label}: head exposed above low rim",
            )
    for index, first in enumerate(tools):
        for second in tools[index + 1 :]:
            report.check(
                overlap_volume(first, second) < VOLUME_TOL,
                f"{first.label}/{second.label}: independent tool lanes",
            )
    for index, sweep in enumerate(sweeps):
        for neighbor_index, tool in enumerate(tools):
            if index != neighbor_index:
                volume = overlap_volume(sweep, tool)
                report.check(
                    volume < VOLUME_TOL,
                    f"{tools[index].label}: lift without disturbing {tool.label}",
                    f"continuous photo sweep overlap={volume:.6g} mm³",
                )
    report.lines.append(
        f"  Photo-envelope evidence only: tool top={layout.tool_top:.3f}, future ceiling={layout.future_cover_ceiling:.3f} mm; constraint only, no cover/interface proof."
    )


def _check_edges(report: Report, part: Part, layout: l.Layout) -> None:
    def base_bearing_or_profile(edge):
        box = edge.bounding_box()
        return box.max.Z - box.min.Z < 1e-6 and any(
            abs(box.min.Z - z) < 1e-5
            for z in (
                0,
                FOOT_C1,
                FOOT_C1 + FOOT_STRAIGHT,
                BASE_H,
                l.BED_THICKNESS,
                l.SEAT_Z,
            )
        )

    def slot_bearing(edge):
        box = edge.bounding_box()
        if box.max.Z - box.min.Z > 1e-6:
            return False
        return any(
            abs(box.min.Z - lane.floor_z(station)) < 1e-5
            and box.min.X >= lane.x - lane.slot_width / 2 - l.SLOT_LEAD - 1e-5
            and box.max.X <= lane.x + lane.slot_width / 2 + l.SLOT_LEAD + 1e-5
            and box.min.Y >= l.TOOL_START_Y + distance - c.RACK_THICKNESS / 2 - 1e-5
            and box.max.Y <= l.TOOL_START_Y + distance + c.RACK_THICKNESS / 2 + 1e-5
            for col in layout.columns
            for lane in col.lanes
            for station, distance in enumerate(p.HANDLE_STATIONS)
        )

    allow = (
        (
            base_bearing_or_profile,
            "Exact horizontal bed bearing, standard foot-profile transitions and internal cell-seam web seats; not exposed tray/rack lips.",
        ),
        (
            slot_bearing,
            "Raw-band horizontal notch bearing seats preserve predictable contact height; their upright cheeks and top mouths are relieved.",
        ),
    )
    survey = sharp_convex_edges(part, allow=allow)
    report.check(
        not survey.sharp,
        "no untreated exposed convex edges",
        f"sharp={len(survey.sharp)}",
    )
    report.check(
        not survey.unclassifiable,
        "edge survey classifies all non-exempt edges",
        f"unclassifiable={len(survey.unclassifiable)}",
    )
    for predicate, reason in allow:
        report.check(
            True,
            "named edge allowance",
            f"matched={sum(predicate(edge) for edge in cast(Shape, part).edges())}: {reason}",
        )
    for edge in (*survey.sharp, *survey.unclassifiable):
        report.check(
            False,
            "unapproved edge detail",
            f"center={edge.center()}, length={edge.length:.4f}",
        )


def missing_notch_control(part: Part, layout: l.Layout) -> Report:
    """Plausible fault: fuse material back into one complete handle notch."""
    column = layout.columns[0]
    lane = column.lanes[0]
    floor = lane.floor_z(0)
    with BuildPart() as mutant:
        add(part)
        with Locations((lane.x, l.TOOL_START_Y + p.HANDLE_STATIONS[0], floor)):
            Box(
                lane.slot_width,
                c.RACK_THICKNESS,
                column.rack_top - floor,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    negative = Report()
    check_slots(negative, mutant.part, layout)
    return negative


def run() -> Report:
    report = Report()
    for count, occupied in ((6, 5), (3, 9)):
        report.section(f"{count} per column — bin anchor / photo-qualified clearance")
        layout = l.arrange(count)
        report.check(
            len(layout.occupied) == occupied,
            "minimum occupied-cell count",
            f"cells={len(layout.occupied)}",
        )
        part = base.create(count)
        _check_base(report, part, layout)
        check_slots(report, part, layout)
        _check_tools(report, part, layout)
        _check_edges(report, part, layout)
        if count == 6:
            negative = missing_notch_control(part, layout)
            expected = f"{layout.columns[0].lanes[0].wrench.label} rack 1: slot void at full free-fit width"
            report.check(
                expected in negative.failures,
                "missing-notch mutant makes the permanent physical predicate fail",
                "; ".join(negative.failures),
            )
    return report


def main() -> None:
    report = run()
    print(report.render())
    sys.exit(1 if report.failures else 0)
