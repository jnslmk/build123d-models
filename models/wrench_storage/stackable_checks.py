"""Focused physical proof for lidless stacking, without removal-sweep reruns."""

import sys
from math import sqrt
from typing import cast

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Part,
    Plane,
    Polygon,
    Pos,
    Shape,
    extrude,
    offset,
)

from models.lib.checks import Report, sharp_convex_edges, solid_probe
from models.lib.edges import as_part
from models.lib.gridfinity import (
    GRID,
    HEIGHT_UNIT,
    PAD,
)

from . import config as c
from . import layout as l
from . import preview
from . import profiles as p
from . import stackable as s
from .stackable import BASE_H, FOOT_C1, FOOT_C3, FOOT_STRAIGHT
from .checks import check_slots, overlap_volume

VOLUME_TOL = 1e-5


def headroom_ok(layout: l.Layout, pitch: float) -> bool:
    """Same predicate used for the real stack and too-low-pitch control."""
    return (
        pitch - max(layout.tool_top, *(col.rack_top for col in layout.columns))
        >= c.FUTURE_LID_HEADROOM
    )


def _convex_corners(layout: l.Layout):
    """Physical corner centres, derived from occupied cells and reference facts."""
    for ix in range(len(layout.columns) + 1):
        for iy in range(max(column.cells for column in layout.columns) + 1):
            neighbors = [
                (x, y)
                for x in (ix - 1, ix)
                for y in (iy - 1, iy)
                if (x, y) in layout.occupied
            ]
            if len(neighbors) != 1:
                continue
            x, y = neighbors[0]
            nx, ny = (1 if x < ix else -1), (1 if y < iy else -1)
            yield (
                ix * GRID - GRID / 2 - nx * 4.0,
                iy * GRID - GRID / 2 - ny * 4.0,
                nx,
                ny,
            )


def _body_profiles(part: Part, layout: l.Layout):
    inside = solid_probe(part)
    shoulder = s.stack_pitch(layout) - s.LANDING_HEIGHT - s.SHOULDER_RISE
    levels = (
        (5.95, "lower body"),
        ((5.95 + shoulder) / 2, "middle body"),
        (shoulder - 0.25, "upper body"),
    )
    corners = tuple(_convex_corners(layout))
    # Probe the external corner immediately above the actual foot transition.
    # The local reference base relief still thickens the inside at this height.
    yield (
        "outer corners at 4.85 mm foot/body junction",
        bool(corners)
        and all(
            inside(cx + nx * r / sqrt(2), cy + ny * r / sqrt(2), 4.85) == expected
            for cx, cy, nx, ny in corners
            for r, expected in ((3.73, True), (3.77, False))
        ),
    )
    for z, name in levels:
        yield (
            f"{name}: continuous 1 mm straight walls",
            all(
                inside(xx + nx * (PAD / 2 - depth), yy + ny * (PAD / 2 - depth), z)
                == expected
                for xx, yy, nx, ny in _rim_samples(layout)
                for depth, expected in (
                    (-0.02, False),
                    (0.02, True),
                    (0.98, True),
                    (1.02, False),
                )
            ),
        )
        corner_ok = len(corners) >= 4 and all(
            inside(cx + nx * r / sqrt(2), cy + ny * r / sqrt(2), z) == expected
            for cx, cy, nx, ny in corners
            for r, expected in (
                (3.77, False),
                (3.73, True),
                (2.77, True),
                (2.73, False),
            )
        )
        yield f"{name}: 3.75 mm convex corners and 1 mm normal wall", corner_ok


def reference_body_ok(part: Part, layout: l.Layout) -> bool:
    """Consumer-solid predicate; rejects the old 4 mm lower body and junction.

    Parent negative control: compare this on ``s.create(6)`` and ``base.create(6)``,
    or replace only z<14 mm of a tall bin with the old low tray.
    """
    return all(ok for _, ok in _body_profiles(part, layout))


def reference_foot_ok(part: Part, layout: l.Layout) -> bool:
    """Measure every real foot's flat and corner outlines, independent of CAD helpers."""
    inside = solid_probe(part)
    return all(
        inside(xx + nx * radius, yy, z) == expected
        and inside(xx, yy + nx * radius, z) == expected
        and all(
            inside(
                xx + nx * 17 + nx * corner_r / sqrt(2),
                yy + ny * 17 + ny * corner_r / sqrt(2),
                z,
            )
            == expected
            for ny in (-1, 1)
        )
        for x, y in sorted(layout.occupied)
        for xx, yy in ((x * GRID, y * GRID),)
        for z, r in ((0.4, 1.2), (1.7, 1.6), (3.675, 2.675), (4.74, 3.74))
        for nx in (-1, 1)
        for corner_r, radius, expected in (
            (r - 0.02, 17 + r - 0.02, True),
            (r + 0.02, 17 + r + 0.02, False),
        )
    )


def _base_and_racks(report: Report, part: Part, layout: l.Layout) -> None:
    inside = solid_probe(part)
    report.check(
        reference_foot_ok(part, layout),
        "actual feet: 34 mm corner spacing; .8/1.8/2.15 mm reference stages",
        "widths 35.6 at z0, 37.2 at z.8/2.6, 41.5 at z4.75",
    )
    for name, ok in _body_profiles(part, layout):
        report.check(ok, name, "consumer samples, not construction sketch equality")
    for x, y in sorted(layout.occupied):
        xx, yy = x * GRID, y * GRID
        report.check(
            all(
                inside(xx + dx, yy + dy, z)
                for dx in (-10, 0, 10)
                for dy in (-10, 0, 10)
                for z in (0.05, 0.99)
            ),
            f"cell {x},{y}: closed 1 mm reference bed",
        )
        report.check(
            all(
                inside(xx + nx * (17 + r + delta), yy, z) == expected
                for z, r in ((1.1, 0.4858), (2.0, 0.6), (3.7, 1.2858), (4.9, 2.4858))
                for nx in (-1, 1)
                for delta, expected in ((-0.02, False), (0.02, True))
            ),
            f"cell {x},{y}: actual reference ultra-light hollow contours",
        )
        if (x, y + 1) in layout.occupied:
            seam_y = yy + GRID / 2
            report.check(
                inside(xx, seam_y, 5.65) and not inside(xx, seam_y, 5.85),
                f"cell {x},{y}: full reference seam web retained to 5.75 mm",
                "actual reference floor preserved; fixed tools checked separately",
            )
            report.check(
                all(
                    inside(
                        xx + nx * (17 + r / sqrt(2)),
                        yy + 17 + r / sqrt(2),
                        5.3,
                    )
                    == expected
                    for nx in (-1, 1)
                    for r, expected in ((2.8658, False), (2.9058, True))
                ),
                f"cell {x},{y}: upper reference hollow relief reaches seam corners",
                "radius 2.8858 at z5.3; detects omitted overlapping upper relief",
            )
    for column in layout.columns:
        for station, distance in enumerate(p.HANDLE_STATIONS):
            y = l.TOOL_START_Y + distance
            for lane in column.lanes:
                root_x = lane.x + lane.slot_width / 2 + 0.25
                floor = lane.floor_z(station)
                report.check(
                    all(
                        inside(root_x, y, z)
                        for z in (0.05, 0.9, 2.0, 4.7, 5.8, floor - 0.1)
                    ),
                    f"{lane.wrench.label} rack {station + 1}: uninterrupted bed-rooted load path",
                )


def _rim_samples(layout: l.Layout):
    """Flat perimeter midpoints plus cell seams on uninterrupted wall runs."""
    for x, y in sorted(layout.occupied):
        for nx, ny in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (x + nx, y + ny) in layout.occupied:
                continue
            yield x * GRID, y * GRID, nx, ny
            tx, ty = -ny, nx
            neighbor = (x + tx, y + ty)
            if (
                neighbor in layout.occupied
                and (neighbor[0] + nx, neighbor[1] + ny) not in layout.occupied
            ):
                yield x * GRID + tx * GRID / 2, y * GRID + ty * GRID / 2, nx, ny


def continuous_rim_ok(part: Part, layout: l.Layout) -> bool:
    """Real constant-section lip at cell centres AND seams, not socket scallops.

    Kept independent of construction sketches so a throwaway reconstruction of
    the former per-cell socket ring exercises exactly this permanent predicate.
    """
    inside = solid_probe(part)
    nominal_inset = FOOT_C3 - s.RECEIVER_CLEARANCE / 2
    z = s.stack_pitch(layout) + FOOT_C1 + FOOT_STRAIGHT / 2
    return all(
        not inside(
            xx + nx * (PAD / 2 - inset - 0.03), yy + ny * (PAD / 2 - inset - 0.03), z
        )
        and inside(
            xx + nx * (PAD / 2 - inset + 0.03), yy + ny * (PAD / 2 - inset + 0.03), z
        )
        for xx, yy, nx, ny in _rim_samples(layout)
        for inset in (
            min(
                nominal_inset,
                s.FRONT_THROAT_INSET
                if ny == -1
                else s.back_throat_inset(layout)
                if ny == 1
                else s.SHOULDER_INSET,
            ),
        )
    )


def _rim(report: Report, part: Part, layout: l.Layout) -> None:
    inside = solid_probe(part)
    pitch, top = s.stack_pitch(layout), s.rim_top(layout)
    report.check(
        continuous_rim_ok(part, layout),
        "continuous actual-foot throat at cell centres and perimeter seams",
        "former socket scallops retain stock at these same seam probes",
    )
    shoulder_start = pitch - s.LANDING_HEIGHT - s.SHOULDER_RISE
    sections = (
        ((s.BASE_BLOCK_TOP + layout.tool_top) / 2, s.WALL, 0.0, "nominal wall"),
        (
            shoulder_start + s.SHOULDER_RISE / 2,
            (s.WALL + s.SHOULDER_INSET) / 2,
            0.0,
            "support-free underside",
        ),
        (pitch - s.LANDING_HEIGHT / 2, s.SHOULDER_INSET, 0.0, "narrow landing"),
        (
            pitch + FOOT_C1 / 2,
            s.STANDARD_RIM_WIDTH - s.RECEIVER_CLEARANCE / 2 - FOOT_C1 / 2,
            0.0,
            "lower 45-degree bevel",
        ),
        (
            pitch + FOOT_C1 + FOOT_STRAIGHT / 2,
            FOOT_C3 - s.RECEIVER_CLEARANCE / 2,
            0.0,
            "straight locating band",
        ),
        (
            pitch + FOOT_C1 + FOOT_STRAIGHT + 0.5,
            FOOT_C3 - s.RECEIVER_CLEARANCE / 2 - 0.5,
            0.0,
            "upper 45-degree mouth",
        ),
        (
            top - s.EDGE_BREAK / 2,
            s.TOP_TRIM - s.RECEIVER_CLEARANCE / 2 + s.EDGE_BREAK / 2,
            s.EDGE_BREAK / 2,
            "finished exposed mouth",
        ),
    )
    for z, inset, outer_inset, name in sections:
        good = True
        for xx, yy, nx, ny in _rim_samples(layout):
            cap = (
                s.FRONT_THROAT_INSET
                if ny == -1
                else s.back_throat_inset(layout)
                if ny == 1
                else s.SHOULDER_INSET
            )
            throat = min(inset, cap)
            if shoulder_start < z < pitch - s.LANDING_HEIGHT:
                progress = (z - shoulder_start) / s.SHOULDER_RISE
                throat = s.WALL + progress * (min(s.SHOULDER_INSET, cap) - s.WALL)
            inner = PAD / 2 - throat
            outer = PAD / 2 - outer_inset
            good &= (
                not inside(xx + nx * (inner - 0.03), yy + ny * (inner - 0.03), z)
                and inside(xx + nx * (inner + 0.03), yy + ny * (inner + 0.03), z)
                and inside(xx + nx * (outer - 0.03), yy + ny * (outer - 0.03), z)
                and not inside(xx + nx * (outer + 0.03), yy + ny * (outer + 0.03), z)
            )
        report.check(
            good,
            f"real perimeter section: {name}",
            f"z={z:.4f}; inset={inset:.4f}; outer inset={outer_inset:.4f} mm",
        )


def _fixture(report: Report, part: Part, layout: l.Layout) -> None:
    box = part.bounding_box()
    pitch = s.stack_pitch(layout)
    report.check(
        part.is_valid and len(part.solids()) == 1, "one valid connected print solid"
    )
    report.check(
        abs(box.min.Z) < 1e-6,
        "reference feet on print bed z=0",
        f"min.Z={box.min.Z:.6g}",
    )
    report.check(
        abs(box.max.Z - s.rim_top(layout)) < 1e-6,
        "locating rim defines full height",
        f"height={box.max.Z:.6g}",
    )
    report.check(
        all(
            abs(a - b) < 1e-6
            for a, b in (
                (box.min.X, -PAD / 2),
                (box.min.Y, -PAD / 2),
                (box.max.X, (len(layout.columns) - 1) * GRID + PAD / 2),
                (
                    box.max.Y,
                    (max(col.cells for col in layout.columns) - 1) * GRID + PAD / 2,
                ),
            )
        ),
        "same compact stepped XY footprint",
        f"size={box.size.X:.6g} x {box.size.Y:.6g} mm",
    )
    check_slots(report, part, layout)
    report.check(
        headroom_ok(layout, pitch),
        "upper foot bottoms >=3 mm above all tools/racks",
        f"pitch={pitch:.6g}; tool top={layout.tool_top:.6g}; headroom={pitch - layout.tool_top:.6g} mm",
    )
    report.check(
        abs(pitch / HEIGHT_UNIT - round(pitch / HEIGHT_UNIT)) < 1e-8,
        "whole-7-mm stack pitch",
        f"pitch={pitch:.6g} mm",
    )
    report.check(
        s.SHOULDER_RISE == s.SHOULDER_INSET - s.WALL,
        "support-free 45-degree bearing shoulder growth",
        f"rise=inward growth={s.SHOULDER_RISE:.6g} mm",
    )
    for x, y in sorted(layout.occupied):
        xx, yy = x * GRID, y * GRID
        report.check(
            not report.solid_at(part, xx, yy, l.BED_THICKNESS + 0.05),
            f"cell {x},{y}: reference hollow foot",
        )
        report.check(
            all(
                not report.solid_at(part, xx, yy, z)
                for z in (
                    layout.tool_top + 0.1,
                    pitch - 0.1,
                    pitch + 0.1,
                    s.rim_top(layout) - 0.1,
                )
            ),
            f"cell {x},{y}: roof-free open center above tools",
        )
    for column in layout.columns:
        for y in range(max(col.cells for col in layout.columns)):
            if (column.index, y) not in layout.occupied:
                with BuildPart() as omitted:
                    with Locations((column.x, y * GRID, -0.1)):
                        Box(
                            PAD - 0.1,
                            PAD - 0.1,
                            box.max.Z + 0.2,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                        )
                volume = overlap_volume(part, omitted.part)
                report.check(
                    volume < VOLUME_TOL,
                    f"omitted stepped cell {column.index},{y} remains empty",
                    f"overlap={volume:.6g} mm³",
                )


def _stack(
    report: Report, part: Part, layout: l.Layout, tools: dict[str, Part]
) -> None:
    pitch = s.stack_pitch(layout)
    upper = as_part(Pos(0, 0, pitch) * part)
    overlap = overlap_volume(part, upper)
    report.check(
        overlap < VOLUME_TOL,
        "actual identical upper bin seats without solid overlap",
        f"overlap={overlap:.6g} mm³",
    )
    for column in layout.columns:
        for lane in column.lanes:
            # Cache each real photo envelope once; grouping changes only X.
            tool = as_part(Pos(lane.x, 0, 0) * tools[lane.wrench.label])
            lower_overlap = overlap_volume(tool, part)
            upper_overlap = overlap_volume(tool, upper)
            report.check(
                lower_overlap < VOLUME_TOL,
                f"{lane.wrench.label}: seated photo tool clears tall walls/rim",
                f"overlap={lower_overlap:.6g} mm³",
            )
            report.check(
                upper_overlap < VOLUME_TOL,
                f"{lane.wrench.label}: stacked upper feet/base clear loaded tool",
                f"overlap={upper_overlap:.6g} mm³",
            )
            # This conservative XY prism contains every point of the seated
            # photo tool, at every lift through the rim. It avoids rebuilding
            # six expensive contour-sweep unions while proving continuous
            # passage above the already-qualified unchanged racks.
            bottom = max(col.rack_top for col in layout.columns) + 0.1
            with BuildPart() as passage:
                with BuildSketch(Plane.XY.offset(bottom)):
                    Polygon(
                        *(
                            (lane.x + x, l.TOOL_START_Y + y)
                            for x, y in preview.thickness_outline(lane.wrench)
                        ),
                        align=None,
                    )
                    offset(amount=s.PASSAGE_CLEARANCE / 2 - 0.001)
                extrude(amount=s.rim_top(layout) + 0.1 - bottom)
            passage_overlap = overlap_volume(part, passage.part)
            report.check(
                passage_overlap < VOLUME_TOL,
                f"{lane.wrench.label}: continuous drop-in/lift-out free-fit rim passage",
                f"projected-prism overlap={passage_overlap:.6g} mm³; diametral fit={s.PASSAGE_CLEARANCE:.6g} mm",
            )
    bearing_count = 0
    for x, y in sorted(layout.occupied):
        xx, yy = x * GRID, y * GRID
        for nx, ny in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (x + nx, y + ny) in layout.occupied:
                continue
            name = f"cell {x},{y} perimeter {nx},{ny}"
            radius = PAD / 2 - c.WALL / 2
            report.check(
                all(
                    report.solid_at(part, xx + nx * radius, yy + ny * radius, z)
                    for z in (
                        s.BASE_BLOCK_TOP + 0.2,
                        (s.BASE_BLOCK_TOP + layout.tool_top) / 2,
                        layout.tool_top + 0.1,
                        pitch - s.SHOULDER_RISE - 0.1,
                    )
                ),
                f"{name}: continuous wall covers entire tool height",
            )
            if ny != -1:
                # The widened front throat serves retrieval; actual flat
                # bearing remains distributed along both sides and the back.
                shoulder_inset = s.SHOULDER_INSET
                if ny == 1:
                    shoulder_inset = min(shoulder_inset, s.back_throat_inset(layout))
                inner_inset = shoulder_inset - s.EDGE_BREAK
                flat_width = inner_inset - s.STANDARD_RIM_WIDTH
                bearing_radius = PAD / 2 - s.STANDARD_RIM_WIDTH - flat_width / 2
                bx, by = xx + nx * bearing_radius, yy + ny * bearing_radius
                report.check(
                    flat_width > 0.05
                    and report.solid_at(part, bx, by, pitch)
                    and report.solid_at(upper, bx, by, pitch)
                    and report.solid_at(part, bx, by, pitch - 0.05)
                    and not report.solid_at(upper, bx, by, pitch - 0.05)
                    and not report.solid_at(part, bx, by, pitch + 0.05)
                    and report.solid_at(upper, bx, by, pitch + 0.05),
                    f"{name}: actual upper foot shares flat shoulder bearing datum",
                    f"bearing=({bx:.4f},{by:.4f},{pitch:.4f}); flat width={flat_width:.4f} mm",
                )
                bearing_count += 1
            receiver_z = pitch + FOOT_C1 + FOOT_STRAIGHT / 2
            foot_radius = PAD / 2 - FOOT_C3
            cap = (
                s.FRONT_THROAT_INSET
                if ny == -1
                else s.back_throat_inset(layout)
                if ny == 1
                else s.SHOULDER_INSET
            )
            receiver_radius = max(foot_radius + s.RECEIVER_CLEARANCE / 2, PAD / 2 - cap)
            report.check(
                report.solid_at(
                    upper,
                    xx + nx * (foot_radius - 0.03),
                    yy + ny * (foot_radius - 0.03),
                    receiver_z,
                )
                and not report.solid_at(
                    part,
                    xx + nx * (foot_radius + s.RECEIVER_CLEARANCE / 4),
                    yy + ny * (foot_radius + s.RECEIVER_CLEARANCE / 4),
                    receiver_z,
                )
                and report.solid_at(
                    part,
                    xx + nx * (receiver_radius + 0.03),
                    yy + ny * (receiver_radius + 0.03),
                    receiver_z,
                ),
                f"{name}: lower-foot locating engagement and PETG sliding gap",
                f"straight engagement={FOOT_STRAIGHT:.6g}; radial gap={receiver_radius - foot_radius:.6g} mm",
            )
    report.check(
        bearing_count >= 4,
        "distributed actual perimeter foot bearing points",
        f"count={bearing_count}; nominal radial landing={s.BEARING_WIDTH:.6g} mm",
    )


def _edges(report: Report, part: Part, layout: l.Layout) -> None:
    def base_profile(edge):
        box = edge.bounding_box()
        return box.size.Z < 1e-6 and any(
            abs(box.min.Z - z) < 1e-5
            for z in (
                0,
                FOOT_C1,
                FOOT_C1 + FOOT_STRAIGHT,
                BASE_H,
                l.BED_THICKNESS,
                s.BASE_BLOCK_TOP,
            )
        )

    def rack_seat(edge):
        box = edge.bounding_box()
        return box.size.Z < 1e-6 and any(
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
            base_profile,
            "Horizontal reference bed bearings, .8/1.8/2.15 foot transitions and unmodified 5.75 mm internal seam-web seats.",
        ),
        (
            rack_seat,
            "Unchanged raw-band horizontal handle bearing seats; cheeks and mouths retain their accepted relief.",
        ),
    )
    survey = sharp_convex_edges(part, allow=allow)
    report.check(
        not survey.sharp,
        "no untreated non-bearing convex edges",
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
            "explicit legitimate bearing edge allowance",
            f"matched={sum(predicate(edge) for edge in cast(Shape, part).edges())}: {reason}",
        )
    for edge in (*survey.sharp, *survey.unclassifiable):
        report.check(
            False,
            "unapproved edge detail",
            f"center={edge.center()}, length={edge.length:.4f}",
        )


def run() -> Report:
    report = Report()
    tools = {
        wrench.label: preview.tool_envelope(l.Lane(wrench, 0)) for wrench in c.WRENCHES
    }
    # Every supported grouping gets real shape/stack/interface proof; photo
    # envelopes are reused, and expensive continuous removal sweeps are omitted.
    for count in (6, 3, 1, 2, 4, 5):
        report.section(f"{count} per column — lidless tall stackable physical gate")
        layout = l.arrange(count)
        part = s.create(count)
        _fixture(report, part, layout)
        _base_and_racks(report, part, layout)
        _rim(report, part, layout)
        _stack(report, part, layout, tools)
        _edges(report, part, layout)
    report.section("Negative control — lower the actual foot-bottom stack datum")
    layout = l.arrange(6)
    low_pitch = s.stack_pitch(layout) - HEIGHT_UNIT
    report.check(
        not headroom_ok(layout, low_pitch),
        "too-low stack pitch makes permanent headroom predicate fail",
        f"mutant pitch={low_pitch:.6g}; tool top={layout.tool_top:.6g} mm",
    )
    return report


def main() -> None:
    report = run()
    print(report.render())
    sys.exit(1 if report.failures else 0)
