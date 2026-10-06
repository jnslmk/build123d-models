"""Consumer BRep gate for compact and stepped removable wrench lids.

These are CAD/photo-envelope predicates, not slicer calibration, physical
support-removal evidence or a loaded-stack rating. Deliberately faulty roofs
and release gaps go through the same permanent predicates as the real parts.
"""

import sys
from math import isfinite, pi, sqrt
from typing import cast

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Edge,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Shape,
    Solid,
    add,
    extrude,
    loft,
)

from models.lib.checks import Report, sharp_convex_edges
from models.lib.edges import as_part
from models.lib.gridfinity import (
    CORNER_R,
    FOOT_C1,
    FOOT_C3,
    GRID,
    HEIGHT_UNIT,
    PAD,
    gridfinity_foot,
)
from models.lib.gridfinity_socket import (
    LATTICE_GAP,
    LATTICE_PITCH,
    LATTICE_RIB,
    SOCKET_LEAD_IN,
    STACK_FIT,
    SUPPORT_TAB_DEPTH,
    SUPPORT_TAB_WIDTH,
    SUPPORT_XY_GAP,
    SUPPORT_ROOF_OVERLAP,
    socket_support,
    socket_tool,
)

from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # ty: ignore[unresolved-import]
from OCP.BRepGProp import BRepGProp  # ty: ignore[unresolved-import]
from OCP.GProp import GProp_GProps  # ty: ignore[unresolved-import]

from . import base
from . import config as c
from . import layout as l
from . import lid
from . import preview
from . import profiles as p
from .corners import passage_corner_tools

VOLUME_TOL = 1e-5


def _reference_volume(part: Part | Solid) -> float:
    """Add accurate solid masses; native compound integrals are not additive.

    Part.volume uses the native overload without a precision argument. Use
    per-solid Gauss–Kronrod integration with B-spline span subdivision,
    retaining every face and shared entity within each solid. Reject an
    inadequate precision estimate, never relax geometric conservation.
    """
    volume = 0.0
    absolute_error = 0.0
    for solid in part.solids():
        properties = GProp_GProps()
        error = BRepGProp.VolumePropertiesGK_s(
            solid.wrapped,
            properties,
            Eps=1e-12,
            OnlyClosed=False,
            IsUseSpan=True,
            CGFlag=False,
            IFlag=False,
            SkipShared=False,
        )
        mass = properties.Mass()
        if not isfinite(mass) or mass < 0 or not isfinite(error) or error < 0:
            raise ValueError(
                "Unreliable adaptive reference solid volume; "
                f"volume={mass:.12g} mm³, estimated relative error={error:.6g}"
            )
        volume += mass
        absolute_error += error * mass
    if not isfinite(volume) or absolute_error >= VOLUME_TOL / 100:
        raise ValueError(
            "Unreliable adaptive reference volume; "
            f"volume={volume:.12g} mm³, estimated absolute error={absolute_error:.6g} mm³"
        )
    return volume


def _require_nonempty(part: Part | None, name: str) -> Part:
    """Empty measured differences are valid; empty requirement stock is not."""
    if part is None:
        raise ValueError(f"Empty checker requirement: {name}; builder produced no part")
    count = len(part.solids())
    if not count:
        raise ValueError(f"Empty checker requirement: {name}; solids=0")
    if not part.is_valid:
        raise ValueError(f"Invalid checker requirement: {name}; solids={count}")
    volume = _reference_volume(part)
    if volume <= VOLUME_TOL:
        raise ValueError(
            f"Empty checker requirement: {name}; solids={count}, volume={volume:.6g} mm³"
        )
    return part


def _intersection(first: Part, second: Part) -> Part:
    """Builder add(empty) is a no-op, not an empty-set intersection."""
    if not first.solids() or not second.solids():
        return Part([])
    with BuildPart(mode=Mode.PRIVATE) as common:
        add(first)
        add(second, mode=Mode.INTERSECT)
    result = common.part
    if result is None or not result.is_valid:
        raise ValueError(
            "Invalid checker intersection; "
            f"left={first.volume:.9g}, right={second.volume:.9g}, "
            f"result={None if result is None else result.volume} mm³"
        )
    return result if result.solids() else Part([])


def overlap_volume(first: Part, second: Part) -> float:
    return _reference_volume(_intersection(first, second))


def _difference(first: Part, second: Part) -> Part:
    """Apply true empty-set identities without seeding an empty builder."""
    if not first.solids():
        return Part([])
    if not second.solids():
        return first
    with BuildPart(mode=Mode.PRIVATE) as difference:
        add(first)
        add(second, mode=Mode.SUBTRACT)
    result = difference.part
    if result is None or not result.is_valid:
        raise ValueError(
            "Invalid checker subtraction; "
            f"left={first.volume:.9g}, right={second.volume:.9g}, "
            f"result={None if result is None else result.volume} mm³"
        )
    return result if result.solids() else Part([])


def _box(x: float, y: float, z: float, w: float, d: float, h: float) -> Part:
    with BuildPart(mode=Mode.PRIVATE) as window:
        with Locations((x, y, z)):
            Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return _require_nonempty(window.part, "independent box mask")


def _window(
    part: Part, x: float, y: float, z: float, w: float, d: float, h: float
) -> Part:
    if not part.solids():
        return Part([])
    return _intersection(part, _box(x, y, z, w, d, h))


def _slab(layout: l.Layout, inset: float, z: float, h: float) -> Part:
    outline = base.footprint(layout, inset)
    with BuildPart(mode=Mode.PRIVATE) as slab:
        with BuildSketch(Plane.XY.offset(z)):
            add(outline)
        extrude(amount=h)
    return _require_nonempty(
        slab.part, f"complete footprint slab inset={inset:g}, z={z:g}, height={h:g}"
    )


def check_roof(report: Report, seated: Part, layout: l.Layout) -> None:
    """Full actual roof section, not a centre probe that can miss a hole."""
    floor = lid.socket_floor_z(layout)
    roof = _slab(layout, c.WALL, floor - c.WALL, c.WALL)
    missing = _reference_volume(_difference(roof, seated))
    report.check(
        missing < VOLUME_TOL,
        "continuous full-footprint 1 mm roof below every receiver",
        f"missing section volume={missing:.6g} mm³",
    )
    report.check(
        floor - c.WALL >= layout.future_cover_ceiling
        and floor - HEIGHT_UNIT < layout.future_cover_ceiling + c.WALL,
        "minimum whole-7-mm floor datum retains required cover ceiling",
        f"floor={floor:.3f}, ceiling={floor - c.WALL:.3f}, required={layout.future_cover_ceiling:.3f} mm",
    )
    prototype = gridfinity_foot()
    for x, y in sorted(layout.occupied):
        foot = as_part(Pos(x * GRID, y * GRID, floor) * prototype)
        volume = overlap_volume(seated, foot)
        report.check(
            volume < VOLUME_TOL,
            f"cell {x},{y}: real matching full foot enters clean receiver",
            f"overlap={volume:.6g} mm³; upper bevel remains above the mouth",
        )
        driven = as_part(Pos(0, 0, -0.3) * foot)
        report.check(
            overlap_volume(seated, driven) > 0.1,
            f"cell {x},{y}: downward-driven real foot meets roof floor",
        )


def _check_pose_and_seat(
    report: Report, clean: Part, seated: Part, bin_part: Part, layout: l.Layout
) -> None:
    bounds = clean.bounding_box()
    report.check(
        clean.is_valid and len(clean.solids()) == 1,
        "clean lid is one valid connected solid",
    )
    report.check(abs(bounds.min.Z) < 1e-6, "socket-down clean print starts at z=0")
    use_bounds = seated.bounding_box()
    report.check(
        abs(use_bounds.min.Z - (l.RIM_Z - lid.SKIRT_ENGAGEMENT)) < 1e-6
        and abs(use_bounds.max.Z - lid.socket_top_z(layout)) < 1e-6,
        "use pose has actual 11 mm skirt tip and 51.5 mm socket mouth",
        f"actual z={use_bounds.min.Z:.3f}..{use_bounds.max.Z:.3f} mm",
    )
    transformed = as_part(lid.use_location(layout) * clean)
    report.check(
        _reference_volume(_difference(transformed, seated)) < VOLUME_TOL
        and _reference_volume(_difference(seated, transformed)) < VOLUME_TOL,
        "inverse print transform reproduces canonical seated geometry",
    )
    volume = overlap_volume(seated, bin_part)
    report.check(
        volume < VOLUME_TOL,
        "seated lid clears actual frozen bin including all rack material",
        f"overlap={volume:.6g} mm³",
    )
    # Match the actual planar landing faces, not nominal rim constants alone.
    rim_faces = [
        face
        for face in cast(Shape, bin_part).faces()
        if abs(face.bounding_box().min.Z - l.RIM_Z) < 1e-6
        and abs(face.bounding_box().max.Z - l.RIM_Z) < 1e-6
    ]
    shoulder_faces = [
        face
        for face in cast(Shape, seated).faces()
        if abs(face.bounding_box().min.Z - l.RIM_Z) < 1e-6
        and abs(face.bounding_box().max.Z - l.RIM_Z) < 1e-6
    ]
    with BuildSketch(Plane.XY.offset(l.RIM_Z)) as landing:
        add(rim_faces)
        add(shoulder_faces, mode=Mode.INTERSECT)
    rim_area = sum(face.area for face in rim_faces)
    report.check(
        rim_area > 1 and landing.sketch.area >= rim_area * 0.99,
        "actual bin flat rim retains broad flat-on-flat seating outside rack passages",
        f"rim={rim_area:.3f}, common planar landing={landing.sketch.area:.3f} mm²; only local rack clearances interrupt contact",
    )
    with BuildPart(mode=Mode.PRIVATE) as occupied:
        with BuildSketch(Plane.XY.offset(l.RIM_Z - lid.SKIRT_ENGAGEMENT - 1)):
            for x, y in sorted(layout.occupied):
                with Locations((x * GRID, y * GRID)):
                    Rectangle(GRID, GRID)
        extrude(amount=lid.socket_top_z(layout) + 2)
    report.check(
        _reference_volume(_difference(seated, occupied.part)) < VOLUME_TOL,
        "canonical use pose occupies only the original bin cells",
    )
    for column in layout.columns:
        for y in range(max(col.cells for col in layout.columns)):
            if (column.index, y) not in layout.occupied:
                void = _box(column.x, y * GRID, 10, PAD, PAD, 43)
                report.check(
                    overlap_volume(seated, void) < VOLUME_TOL,
                    f"absent stepped cell {column.index},{y} remains empty at original shortened end",
                )
    # A conservative DOWNWARD-monotone envelope contains every pose of the
    # frozen bin during straight-up lid withdrawal: each rack is its whole
    # full-width vertical prism, feet stay below SEAT_Z, and the shell below
    # RIM_Z contains every downward-translated rim/wall section. Downward
    # portions below z=0 cannot reach the lid's 11 mm tip.
    outside = base.footprint(layout)
    inside = base.footprint(layout, c.WALL)
    with BuildPart(mode=Mode.PRIVATE) as withdrawal_envelope:
        with BuildSketch():
            add(outside)
        extrude(amount=l.RIM_Z)
        with BuildSketch(Plane.XY.offset(l.SEAT_Z)):
            add(inside)
        extrude(amount=l.RIM_Z, mode=Mode.SUBTRACT)
        for column in layout.columns:
            for distance in p.HANDLE_STATIONS:
                with BuildSketch():
                    with Locations((column.x, l.TOOL_START_Y + distance)):
                        RectangleRounded(PAD, c.RACK_THICKNESS, l.RACK_CORNER_R)
                extrude(amount=column.rack_top)
    report.check(
        overlap_volume(seated, withdrawal_envelope.part) < VOLUME_TOL,
        "continuous straight-up lid withdrawal clears conservative bin/rack envelope",
        "Open-bottom rack passages; all downward relative rack poses contained, not selected pose samples.",
    )


def _check_tools(report: Report, seated: Part, layout: l.Layout) -> None:
    for column in layout.columns:
        for lane in column.lanes:
            tool = preview.tool_envelope(lane)
            reserve = preview.tool_envelope(lane, lift=c.FUTURE_LID_HEADROOM)
            report.check(
                overlap_volume(seated, tool) < VOLUME_TOL,
                f"{lane.wrench.label}: actual photo-tool envelope clears skirt, shoulder and roof",
            )
            report.check(
                overlap_volume(seated, reserve) < VOLUME_TOL
                and lid.ceiling_z(layout) - tool.bounding_box().max.Z
                >= c.FUTURE_LID_HEADROOM,
                f"{lane.wrench.label}: continuous 3 mm vertical cover reserve clears actual lid",
                "photo consumer envelope, not a real-tool fit claim",
            )
            travel = layout.tool_top - (l.RIM_Z - lid.SKIRT_ENGAGEMENT) + 1
            downward_sweep = as_part(
                Pos(0, 0, -travel) * preview.tool_envelope(lane, lift=travel)
            )
            volume = overlap_volume(seated, downward_sweep)
            report.check(
                volume < VOLUME_TOL,
                f"{lane.wrench.label}: continuous loaded straight-up lid removal",
                f"exact downward relative photo-envelope sweep overlap={volume:.6g} mm³; travel={travel:.3f} mm",
            )


def _inset_loft(layout: l.Layout, levels: tuple[tuple[float, float], ...]) -> Part:
    outlines = {inset: base.footprint(layout, inset) for _, inset in levels}
    with BuildPart(mode=Mode.PRIVATE) as region:
        sections = []
        for z, inset in levels:
            with BuildSketch(Plane.XY.offset(z)) as section:
                add(outlines[inset])
            sections.append(section.sketch)
        loft(sections=sections, ruled=True)
    return region.part


def _passage_masks(
    layout: l.Layout,
    *,
    old_short_caps: bool = False,
) -> tuple[Part, Part]:
    """Exact declared rack/end cuts; NO uniform corner-allowance bands."""
    corner = l.EDGE_BREAK
    tip = l.RIM_Z - lid.SKIRT_ENGAGEMENT
    end = -GRID / 2 + (GRID - PAD) / 2
    with BuildPart(mode=Mode.PRIVATE) as racks:
        for column in layout.columns:
            for distance in p.HANDLE_STATIONS:
                sections = []
                for z, sx, sy in (
                    (tip - 0.05, -corner, -corner),
                    (tip, -corner, -corner),
                    (tip + corner, 0.0, 0.0),
                    (column.rack_top + lid.RACK_CLEARANCE, 0.0, 0.0),
                    (
                        (
                            column.rack_top + lid.RACK_CLEARANCE + lid.RACK_CAP_RISE
                            if old_short_caps
                            else lid.rack_cap_z(column)
                        ),
                        lid.RACK_CAP_RISE,
                        corner,
                    ),
                ):
                    with BuildSketch(Plane.XY.offset(z)) as section:
                        with Locations((column.x, l.TOOL_START_Y + distance)):
                            RectangleRounded(
                                PAD + 2 * (l.RACK_CORNER_R + lid.RACK_CLEARANCE - sx),
                                c.RACK_THICKNESS + 2 * (lid.RACK_CLEARANCE - sy),
                                l.RACK_CORNER_R + lid.RACK_CLEARANCE - sy,
                            )
                    sections.append(section.sketch)
                loft(sections=sections, ruled=True)
    with BuildPart(mode=Mode.PRIVATE) as ends:
        for column in layout.columns:
            left, right = lid.end_relief_span(column)
            outer = end + c.WALL
            inner = end + lid.SKIRT_INNER_INSET + lid.END_CLEARANCE
            sections = []
            for z, flare in (
                (tip - 0.05, corner),
                (tip, corner),
                (tip + corner, 0.0),
                (l.RIM_Z + lid.SHOULDER_RISE + 0.05, 0.0),
            ):
                with BuildSketch(Plane.XY.offset(z)) as section:
                    with Locations(((left + right) / 2, (outer + inner) / 2)):
                        Rectangle(right - left + 2 * flare, inner - outer)
                sections.append(section.sketch)
            loft(sections=sections, ruled=True)
    return racks.part, ends.part


def _passage_corner_allowance(
    stock: Part,
    passages: tuple[Part, Part],
    layout: l.Layout,
) -> tuple[Part, list[tuple]]:
    """Intersect declared explicit cutters with independent dimensional stock.

    Original upright edges identify the corners before any cutter is applied.
    Each cutter and its actual material loss must be valid, nonempty and
    local to that corner's dimensional passage/lead envelope. Locality boxes
    only reject escaped tools: they NEVER become removal allowances.
    """
    tip = l.RIM_Z - lid.SKIRT_ENGAGEMENT
    half_band = (c.RACK_THICKNESS + lid.PLUG_FIT) / 2
    end = -GRID / 2 + (GRID - PAD) / 2
    tolerance = 1e-6
    radius = l.EDGE_BREAK
    _require_nonempty(stock, "independent stock before passage cuts")
    for index, passage in enumerate(passages):
        _require_nonempty(passage, f"independent declared passage family {index}")
    with BuildPart(mode=Mode.PRIVATE) as cut_stock:
        add(stock)
        add(passages[0], mode=Mode.SUBTRACT)
        add(passages[1], mode=Mode.SUBTRACT)
    unrounded = _require_nonempty(
        cut_stock.part, "independent stock after declared passage cuts"
    )
    designated: list[tuple[Edge, tuple]] = []
    for edge in cast(Shape, unrounded).edges().filter_by(Axis.Z):
        box = edge.bounding_box()
        point = edge.center()
        feature = None
        for column in layout.columns:
            if (
                column.x - PAD / 2 - tolerance
                <= point.X
                <= column.x + PAD / 2 + tolerance
                and box.min.Z >= tip + radius - tolerance
                and box.max.Z <= column.rack_top + lid.RACK_CLEARANCE + tolerance
                and any(
                    abs(abs(point.Y - (l.TOOL_START_Y + distance)) - half_band)
                    < tolerance
                    for distance in p.HANDLE_STATIONS
                )
            ):
                feature = f"column {column.index} rack passage"
                break
            if (
                end + c.WALL - tolerance
                <= point.Y
                <= end + lid.SKIRT_INNER_INSET + lid.END_CLEARANCE + tolerance
                and box.min.Z >= tip + radius - tolerance
                and box.max.Z <= l.RIM_Z + lid.SHOULDER_RISE + 0.05 + tolerance
                and any(
                    abs(point.X - side) < tolerance
                    for side in lid.end_relief_span(column)
                )
            ):
                feature = f"column {column.index} common-end passage"
                break
        if feature is not None:
            identity = (point.X, point.Y, box.min.Z, box.max.Z, feature)
            if any(
                abs(previous[1][0] - point.X) < tolerance
                and abs(previous[1][1] - point.Y) < tolerance
                for previous in designated
            ):
                raise ValueError(
                    f"Non-unique independent passage corner: {feature} at {point.X}, {point.Y}"
                )
            designated.append((edge, identity))
    if not designated:
        raise ValueError("Declared passages have no identifiable upright corners")
    losses = []
    loss_volume = 0.0
    for edge, identity in designated:
        x, y, bottom, top, feature = identity
        tool = _require_nonempty(
            passage_corner_tools(unrounded, [edge], radius),
            f"explicit corner cutter: {feature} at {x}, {y}",
        )
        bounds = tool.bounding_box()
        # Full-radius upright rounding has two-radius-long conical lead-outs
        # ending in independently classified air, never retreating cap stock.
        # Check the ORIGINAL endpoint envelope, never a whole-height prism.
        if (
            bounds.min.X < x - radius - tolerance
            or bounds.max.X > x + radius + tolerance
            or bounds.min.Y < y - radius - tolerance
            or bounds.max.Y > y + radius + tolerance
            or bounds.min.Z < bottom - 2 * radius - tolerance
            or bounds.max.Z > top + 2 * radius + tolerance
            or bounds.size.X < radius - tolerance
            or bounds.size.X > 2 * radius + tolerance
            or bounds.size.Y < radius - tolerance
            or bounds.size.Y > 2 * radius + tolerance
            or abs(bounds.min.Z - (bottom - 2 * radius)) > tolerance
            or abs(bounds.max.Z - (top + 2 * radius)) > tolerance
        ):
            raise ValueError(
                f"Explicit cutter escapes declared corner/lead envelope: "
                f"{feature} at {x}, {y}; bounds={bounds}"
            )
        tool_volume = _reference_volume(tool)
        # Each air-directed homothetic lead-out integrates to one third of
        # the upright cross-section times its explicit two-radius Z length.
        nominal_volume = (1 - pi / 4) * radius**2 * (top - bottom + 4 * radius / 3)
        loss = _require_nonempty(
            _intersection(unrounded, tool),
            f"direct stock/cutter loss: {feature} at {x}, {y}",
        )
        measured_loss = _reference_volume(loss)
        if (
            tool_volume <= VOLUME_TOL
            or abs(tool_volume - nominal_volume) > VOLUME_TOL
            or measured_loss <= VOLUME_TOL
            or measured_loss > tool_volume + VOLUME_TOL
        ):
            raise ValueError(
                f"Invalid explicit corner loss: {feature} at {x}, {y}; "
                f"tool={tool_volume:.9g}, nominal={nominal_volume:.9g}, "
                f"loss={measured_loss:.9g} mm³"
            )
        losses.append(loss)
        loss_volume += measured_loss
    with BuildPart(mode=Mode.PRIVATE) as combined:
        add(losses)
    removed = _require_nonempty(combined.part, "union of direct declared corner losses")
    removed_volume = _reference_volume(removed)
    retained = _require_nonempty(
        _difference(unrounded, removed),
        "complete independent passage stock after explicit corner cutters",
    )
    before_volume = _reference_volume(unrounded)
    retained_volume = _reference_volume(retained)
    if (
        abs(loss_volume - removed_volume) > VOLUME_TOL
        or abs(before_volume - retained_volume - removed_volume) > VOLUME_TOL
        or _reference_volume(_difference(removed, unrounded)) > VOLUME_TOL
        or _reference_volume(_intersection(removed, retained)) > VOLUME_TOL
    ):
        raise ValueError(
            "Incomplete or inconsistent direct passage-cutter allowance; "
            f"stock={before_volume:.9g}, retained={retained_volume:.9g}, "
            f"individual losses={loss_volume:.9g}, union={removed_volume:.9g} mm³"
        )
    return removed, [identity for _, identity in designated]


def check_passage_corners(report: Report, seated: Part, corner_loss: Part) -> None:
    """The independently declared rounding loss must actually be absent."""
    _require_nonempty(corner_loss, "complete declared corner profile forbidden stock")
    residual = _reference_volume(_intersection(seated, corner_loss))
    report.check(
        residual < VOLUME_TOL,
        "complete declared rounded passage-corner profiles contain no stock",
        f"material inside direct independent stock/cutter loss={residual:.6g} mm³",
    )


def _receiver_requirements() -> tuple[Part, Part]:
    """Independent dimensional wall and empty-hole requirements.

    A sqrt(2) XY offset is conservative on straight/lead sections and gives
    1 mm normal width on the 45-degree bevel. Do not subtract the production
    cutter here: an oversized cutter must remove REQUIRED material and fail.
    Only the first 0.2 mm exterior bed chamfer is excluded from wall thickness.
    """
    regions = []
    for outward in (0.0, c.WALL * sqrt(2)):
        with BuildPart(mode=Mode.PRIVATE) as region:
            sections = []
            for z, inset, lead in (
                (-0.05, FOOT_C3, SOCKET_LEAD_IN),
                (SOCKET_LEAD_IN, FOOT_C3, 0.0),
                (lid.SOCKET_DEPTH - FOOT_C1, FOOT_C3, 0.0),
                (lid.SOCKET_DEPTH, FOOT_C1 + FOOT_C3, 0.0),
            ):
                with BuildSketch(Plane.XY.offset(z)) as section:
                    RectangleRounded(
                        PAD - 2 * inset + STACK_FIT + 2 * (lead + outward),
                        PAD - 2 * inset + STACK_FIT + 2 * (lead + outward),
                        CORNER_R - inset + STACK_FIT / 2 + lead + outward,
                    )
                sections.append(section.sketch)
            loft(sections=sections, ruled=True)
        regions.append(
            _require_nonempty(region.part, f"receiver reference outward={outward:g}")
        )
    wall = _require_nonempty(
        _difference(regions[1], regions[0]), "independent receiver wall"
    )
    return (
        _require_nonempty(
            _window(
                wall, 0, 0, l.EDGE_BREAK, PAD, PAD, lid.SOCKET_DEPTH - l.EDGE_BREAK
            ),
            "complete receiver wall above explicit bed lead",
        ),
        _require_nonempty(
            _window(regions[0], 0, 0, 0, PAD, PAD, lid.SOCKET_DEPTH),
            "complete nominal receiver void",
        ),
    )


def _check_sections(
    report: Report, seated: Part, clean: Part, layout: l.Layout
) -> Part:
    """Construct complete required and forbidden volumes, not sampled sections."""
    tip = l.RIM_Z - lid.SKIRT_ENGAGEMENT
    top = lid.socket_top_z(layout)
    exterior = _inset_loft(
        layout,
        (
            (l.RIM_Z, l.EDGE_BREAK),
            (l.RIM_Z + l.EDGE_BREAK, 0.0),
            (top - l.EDGE_BREAK, 0.0),
            (top, l.EDGE_BREAK),
        ),
    )
    skirt = _inset_loft(
        layout,
        (
            (tip, lid.SKIRT_OUTER_INSET + l.EDGE_BREAK),
            (tip + l.EDGE_BREAK, lid.SKIRT_OUTER_INSET),
            (l.RIM_Z, lid.SKIRT_OUTER_INSET),
        ),
    )
    cavity = _inset_loft(
        layout,
        (
            (tip, lid.SKIRT_INNER_INSET - l.EDGE_BREAK),
            (tip + l.EDGE_BREAK, lid.SKIRT_INNER_INSET),
            (l.RIM_Z, lid.SKIRT_INNER_INSET),
            (l.RIM_Z + lid.SHOULDER_RISE, c.WALL),
            (lid.ceiling_z(layout), c.WALL),
        ),
    )
    _require_nonempty(exterior, "complete exterior loft")
    _require_nonempty(skirt, "complete locating skirt loft")
    _require_nonempty(cavity, "complete interior cavity loft")
    cutter = socket_tool(PAD, PAD, lid.SOCKET_DEPTH)
    receivers = [
        as_part(lid.use_location(layout) * Pos(x * GRID, -y * GRID, 0) * cutter)
        for x, y in sorted(layout.occupied)
    ]
    with BuildPart(mode=Mode.PRIVATE) as blank:
        add([exterior, skirt])
        add(cavity, mode=Mode.SUBTRACT)
    stock = _require_nonempty(
        blank.part,
        f"body/skirt/shoulder stock after cavity; occupied cells={len(layout.occupied)}",
    )
    # Independently reconstruct passages and direct explicit cutter losses.
    # Receiver cuts remain remote from the corner tools and are applied after
    # them, in the same geometric order as the printable part.
    passages = _passage_masks(layout)
    corner_loss, corners = _passage_corner_allowance(stock, passages, layout)
    corner_loss_volume = _reference_volume(corner_loss)
    with BuildPart(mode=Mode.PRIVATE) as pristine:
        add(stock)
        add(receivers, mode=Mode.SUBTRACT)
    pristine_stock = _require_nonempty(
        pristine.part,
        f"independent stock after receivers; before={stock.volume:.9g} mm³",
    )
    with BuildPart(mode=Mode.PRIVATE) as allowed:
        add([*passages, corner_loss])
    allowed_cuts = _require_nonempty(
        allowed.part, "union of declared passages and direct explicit corner losses"
    )
    required = _require_nonempty(
        _difference(pristine_stock, allowed_cuts),
        f"complete required body/skirt/shoulder; cells={len(layout.occupied)}, "
        f"pristine={pristine_stock.volume:.9g}, declared cuts={allowed_cuts.volume:.9g}, "
        f"exact corner loss={corner_loss_volume:.9g} mm³",
    )
    for name, z, height in (
        ("locating skirt", tip, lid.SKIRT_ENGAGEMENT),
        ("shoulder", l.RIM_Z, lid.SHOULDER_RISE),
        (
            "body",
            l.RIM_Z + lid.SHOULDER_RISE,
            lid.ceiling_z(layout) - l.RIM_Z - lid.SHOULDER_RISE,
        ),
    ):
        _require_nonempty(
            _intersection(required, _slab(layout, 0.0, z, height)),
            f"complete required {name} after declared cutters",
        )
    removed_stock = _require_nonempty(
        _intersection(pristine_stock, allowed_cuts),
        "direct declared cuts in complete body/skirt/shoulder stock",
    )
    pristine_volume = _reference_volume(pristine_stock)
    required_volume = _reference_volume(required)
    removed_volume = _reference_volume(removed_stock)
    if abs(pristine_volume - required_volume - removed_volume) > VOLUME_TOL:
        raise ValueError(
            "Incomplete independent required stock after declared cutter union; "
            f"pristine={pristine_volume:.9g}, required={required_volume:.9g}, "
            f"removed={removed_volume:.9g} mm³"
        )
    missing = _reference_volume(_difference(required, seated))
    report.lines.append(
        f"  Exact declared corner allowance: {len(corners)} upright corners, "
        f"direct stock/cutter volume={corner_loss_volume:.6g} mm³; {corners}"
    )
    check_passage_corners(report, seated, corner_loss)
    report.check(
        missing < VOLUME_TOL,
        "complete body/skirt/shoulder sections outside only declared passages",
        f"missing={missing:.6g} mm³; 1 mm body, 1.2 mm skirt, joined 45-degree shoulder; ONLY declared passages and direct explicit corner-cutter loss",
    )
    report.check(
        _reference_volume(_difference(seated, pristine_stock)) < VOLUME_TOL
        and overlap_volume(seated, cavity) < VOLUME_TOL
        and overlap_volume(seated, removed_stock) < VOLUME_TOL,
        "complete cavity and exterior lead-in forbidden volumes stay empty",
        "Whole cavity/lead transition and all independently stock-clipped rack/end/corner cuts, not selected heights.",
    )
    gap_outer = _slab(layout, c.WALL, tip, lid.SKIRT_ENGAGEMENT)
    gap_inner = _slab(layout, c.WALL + lid.PLUG_FIT / 2, tip, lid.SKIRT_ENGAGEMENT)
    gap = _require_nonempty(
        _difference(gap_outer, gap_inner), "complete locating clearance band"
    )
    report.check(
        overlap_volume(seated, gap) < VOLUME_TOL,
        "entire locating skirt retains half-diametral sliding gap",
    )
    wall, void = _receiver_requirements()
    for x, y in sorted(layout.occupied):
        required_wall = as_part(Pos(x * GRID, -y * GRID, 0) * wall)
        report.check(
            _reference_volume(_difference(required_wall, clean)) < VOLUME_TOL,
            f"cell {x},{y}: complete receiver wall has at least 1 mm normal section",
            "Full curved/straight/45-degree wall volume from z0.2 to2.5; only explicit z0..0.2 bed lead excluded.",
        )
        required_void = as_part(Pos(x * GRID, -y * GRID, 0) * void)
        report.check(
            overlap_volume(clean, required_void) < VOLUME_TOL,
            f"cell {x},{y}: complete nominal receiver void and lead-in stay open",
        )
    return stock


def check_rack_caps(
    report: Report,
    seated: Part,
    actual_cutter: Part,
) -> None:
    """Measure actual terminal faces against actual finished cavity geometry."""
    tip = l.RIM_Z - lid.SKIRT_ENGAGEMENT
    caps = [
        face
        for face in cast(Shape, actual_cutter).faces()
        if face.bounding_box().size.Z < 1e-6 and face.bounding_box().min.Z >= tip - 1e-6
    ]
    report.check(bool(caps), "actual rack cutter has measurable terminal-cap faces")
    for index, face in enumerate(caps):
        z = face.bounding_box().min.Z
        report.check(
            z >= l.RIM_Z + lid.SHOULDER_RISE + l.EDGE_BREAK - 1e-6,
            f"rack cap {index}: measured endpoint is beyond shoulder and entry allowance",
            f"actual terminal-face z={z:.6f} mm",
        )
        # Extrude the REAL terminal face UP, beyond the cutter's end. A probe
        # below the face would merely resample the removed passage and could
        # not detect a cap that terminates inside the shoulder material.
        with BuildPart(mode=Mode.PRIVATE) as upward:
            add(face)
            extrude(amount=0.02, dir=(0, 0, 1))
        collision = overlap_volume(seated, upward.part)
        report.check(
            collision < VOLUME_TOL,
            f"rack cap {index}: terminal face opens into actual finished cavity",
            f"full 0.02 mm upward face prism overlaps finished stock={collision:.6g} mm³",
        )


def old_short_cap_control(
    seated: Part,
    independent_stock: Part,
    layout: l.Layout,
) -> Report:
    """Restore the real shoulder loss of the old too-short cap on grouping 5."""
    correct_cutter = lid.rack_passage_tool(layout)
    old_cutter, _ = _passage_masks(layout, old_short_caps=True)
    missing_cut = _difference(correct_cutter, old_cutter)
    restored_stock = _require_nonempty(
        _intersection(missing_cut, independent_stock),
        "actual shoulder stock restored by old short-cap negative control",
    )
    with BuildPart(mode=Mode.PRIVATE) as mutant:
        add(seated)
        add(restored_stock)
    negative = Report()
    check_rack_caps(negative, mutant.part, old_cutter)
    return negative


def _rounded_slab(width: float, radius: float, z: float, height: float) -> Part:
    with BuildPart(mode=Mode.PRIVATE) as slab:
        with BuildSketch(Plane.XY.offset(z)):
            RectangleRounded(width, width, radius)
        extrude(amount=height)
    return slab.part


def _support_model(layout: l.Layout) -> Part:
    """The agreed shared support is the sole declared sacrificial geometry."""
    prototype = socket_support(PAD, PAD, lid.SOCKET_DEPTH)
    placed = [
        as_part(Pos(x * GRID, -y * GRID, 0) * prototype)
        for x, y in sorted(layout.occupied)
    ]
    with BuildPart(mode=Mode.PRIVATE) as support:
        add(placed)
    return support.part


def check_supports(
    report: Report, supported: Part, clean: Part, layout: l.Layout
) -> None:
    """Whole-solid support requirements and full process-gap forbidden regions."""
    report.check(
        supported.is_valid
        and len(supported.solids()) == 1
        and abs(supported.bounding_box().min.Z) < 1e-6,
        "supported print is one valid connected solid on z=0",
    )
    reference = _support_model(layout)
    expected = _difference(reference, clean)
    supports = _difference(supported, clean)
    missing_clean = _reference_volume(_difference(clean, supported))
    escaped = _reference_volume(_difference(supports, expected))
    missing_support = _reference_volume(_difference(expected, supports))
    support_volume = _reference_volume(supports)
    report.check(
        missing_clean < VOLUME_TOL and support_volume > 1 and escaped < VOLUME_TOL,
        "support toggle preserves finished lid and adds only removable receiver material",
        f"missing clean={missing_clean:.6g}, globally undeclared addition={escaped:.6g} mm³",
    )
    report.check(
        missing_support < VOLUME_TOL,
        "entire declared rail/lattice/tab field exists, not only selected probes",
        f"missing sacrificial field={missing_support:.6g} mm³",
    )
    if support_volume <= 1:
        return
    inset = FOOT_C1 + FOOT_C3
    roof_width = PAD - 2 * inset + STACK_FIT
    roof_radius = CORNER_R - inset + STACK_FIT / 2
    rail_width = roof_width - 2 * SUPPORT_XY_GAP
    rail_radius = roof_radius - SUPPORT_XY_GAP
    body_top = lid.SOCKET_DEPTH - LATTICE_GAP
    tab_offset = rail_width / 2 - LATTICE_RIB / 2
    full_roof_region = _rounded_slab(roof_width, roof_radius, 0, lid.SOCKET_DEPTH)
    full_rail_envelope = _rounded_slab(rail_width, rail_radius, 0, lid.SOCKET_DEPTH)
    side_gap = _difference(full_roof_region, full_rail_envelope)
    roof_gap = _rounded_slab(roof_width, roof_radius, body_top, LATTICE_GAP)
    for x, y in sorted(layout.occupied):
        xx, yy = x * GRID, -y * GRID
        label = f"cell {x},{y} support"
        body = _window(supports, xx, yy, 0, PAD, PAD, body_top)
        required_body = _window(reference, xx, yy, 0, PAD, PAD, body_top)
        report.check(
            body.is_valid
            and len(body.solids()) == 1
            and _reference_volume(_difference(required_body, body)) < VOLUME_TOL,
            f"{label}: connected rail/lattice body is rooted on bed",
            "Every full-height rib and rounded rail required, including all bed roots.",
        )
        bed = _window(required_body, xx, yy, 0, PAD, PAD, 0.02)
        bed_area = sum(
            face.area
            for face in cast(Shape, body).faces()
            if abs(face.bounding_box().min.Z) < 1e-6
            and abs(face.bounding_box().max.Z) < 1e-6
        )
        report.check(
            _reference_volume(_difference(bed, supported)) < VOLUME_TOL
            and abs(bed_area - _reference_volume(bed) / 0.02) < 1e-4,
            f"{label}: complete rail/lattice bed-contact footprint",
            f"actual planar bed contact={bed_area:.3f} mm²",
        )
        clearance = as_part(Pos(xx, yy, 0) * side_gap)
        report.check(
            overlap_volume(supported, clearance) < VOLUME_TOL,
            f"{label}: open XY process gap to every receiver wall",
            "Complete narrowest-contour 0.6 mm offset band at every z0..2.5, including terminal bands and tabs.",
        )
        gap_region = as_part(Pos(xx, yy, 0) * roof_gap)
        actual_gap = _window(supported, xx, yy, body_top, PAD, PAD, LATTICE_GAP)
        gap_material = _intersection(actual_gap, gap_region)
        tabs = [
            _box(
                xx,
                yy + sign * tab_offset,
                body_top,
                SUPPORT_TAB_WIDTH,
                SUPPORT_TAB_DEPTH,
                LATTICE_GAP,
            )
            for sign in (-1, 1)
        ]
        with BuildPart(mode=Mode.PRIVATE) as permitted:
            add(tabs)
        illegal = _reference_volume(_difference(gap_material, permitted.part))
        report.check(
            illegal < VOLUME_TOL,
            f"{label}: roof air gap stays open away from exact declared tabs",
            f"Actual supported-solid material in COMPLETE z2.3..2.5 forbidden gap={illegal:.6g} mm³",
        )
        report.check(
            illegal < VOLUME_TOL
            and _reference_volume(_difference(permitted.part, gap_material))
            < VOLUME_TOL,
            f"{label}: entire roof gap contains material only inside declared two tabs",
            "Bidirectional whole-gap comparison, not additions-only or truncated z bands.",
        )
        necks = gap_material.solids()
        areas = [_reference_volume(solid) / LATTICE_GAP for solid in necks]
        report.check(
            len(necks) == 2
            and all(
                abs(area - SUPPORT_TAB_WIDTH * SUPPORT_TAB_DEPTH) < 1e-4
                for area in areas
            ),
            f"{label}: exactly two bounded 0.4×0.8 mm weak necks",
            f"complete-gap neck sections={areas} mm²",
        )
        for sign in (-1, 1):
            tab_y = yy + sign * tab_offset
            root = _box(
                xx,
                tab_y,
                0,
                SUPPORT_TAB_WIDTH,
                SUPPORT_TAB_DEPTH,
                lid.SOCKET_DEPTH + SUPPORT_ROOF_OVERLAP,
            )
            report.check(
                _reference_volume(_difference(root, supported)) < VOLUME_TOL,
                f"{label}: tab {sign:+d} has complete bed-to-rail-to-neck-to-roof root",
                "Entire declared 0.4×0.8 mm column to z2.52, including both interfaces.",
            )
            # Nominal 0.8×0.8×0.1 mm metal tip follows three continuous
            # translational legs. The entry lies in a 4.2×1.46 mm lattice
            # opening, not on the central rib. No cutter/handle calibration
            # is claimed; only this candidate tip's full swept set is tested.
            entry_x = xx + LATTICE_PITCH / 2
            entry_y = tab_y - sign * (LATTICE_RIB + 0.4)
            tip_width = 2 * SUPPORT_TAB_WIDTH
            tip_height = LATTICE_GAP / 2
            tip_z = body_top + (LATTICE_GAP - tip_height) / 2
            vertical = _box(
                entry_x, entry_y, -1, tip_width, tip_width, tip_z + tip_height + 1
            )
            across = _box(
                (xx + entry_x) / 2,
                entry_y,
                tip_z,
                entry_x - xx + tip_width,
                tip_width,
                tip_height,
            )
            toward = _box(
                xx,
                (entry_y + tab_y) / 2,
                tip_z,
                tip_width,
                abs(tab_y - entry_y) + tip_width,
                tip_height,
            )
            with BuildPart(mode=Mode.PRIVATE) as swept_tip:
                add([vertical, across, toward])
            target = _box(
                xx, tab_y, body_top, SUPPORT_TAB_WIDTH, SUPPORT_TAB_DEPTH, LATTICE_GAP
            )
            approach = _difference(swept_tip.part, target)
            report.check(
                overlap_volume(supported, approach) < VOLUME_TOL,
                f"{label}: tab {sign:+d} has continuous mouth-to-neck cutter-tip approach",
                "Full three-leg swept solid; only exact target-neck contact excluded. Tip/handle suitability and removal force need physical trials.",
            )
        # A complete constructive near-roof section avoids aliasing entirely:
        # every rib in BOTH axes and the entire offset rounded edge rail must
        # be present. Known 4.2 mm interior openings and 0.6 mm normal edge
        # separation are distinct; a parallel toolpath in the edge strip
        # must not be falsely described as a <=4.2 mm principal-axis bridge.
        backing = _window(required_body, xx, yy, body_top - 0.02, PAD, PAD, 0.02)
        missing_backing = _reference_volume(_difference(backing, supported))
        report.check(
            missing_backing < VOLUME_TOL,
            f"{label}: actual both-axis roof coverage includes edge strips",
            f"Whole required near-roof lattice/rounded rail missing={missing_backing:.6g} mm³; interior openings={LATTICE_PITCH - LATTICE_RIB:g}, normal edge band={SUPPORT_XY_GAP:g} mm. No sampled-grid aliasing or printer-proven bridge claim.",
        )


def _edge_bucket(edge) -> tuple:
    """Cheap candidate index only; NEVER the geometric identity decision."""
    box = edge.bounding_box()
    return (
        edge.geom_type,
        round(edge.length, 5),
        *(
            round(value, 5)
            for value in (
                box.min.X,
                box.min.Y,
                box.min.Z,
                box.max.X,
                box.max.Y,
                box.max.Z,
            )
        ),
    )


def _same_complete_curve(first, second) -> bool:
    """Full BRep curve common length, not centre/length or sparse samples."""
    if abs(first.length - second.length) > 1e-6:
        return False
    common = BRepAlgoAPI_Common(first.wrapped, second.wrapped)
    if not common.IsDone():
        raise ValueError("Cannot classify complete sacrificial edge intersection")
    properties = GProp_GProps()
    BRepGProp.LinearProperties_s(common.Shape(), properties)
    return abs(properties.Mass() - first.length) < 1e-6


def _check_edges(
    report: Report, clean: Part, supported: Part, layout: l.Layout
) -> None:
    expected = _difference(_support_model(layout), clean)
    extra = _difference(supported, clean)
    validated = (
        _reference_volume(_difference(extra, expected)) < VOLUME_TOL
        and _reference_volume(_difference(expected, extra)) < VOLUME_TOL
        and _reference_volume(_difference(clean, supported)) < VOLUME_TOL
    )
    report.check(
        validated,
        "sacrificial edge allowances require globally validated support geometry",
    )
    reference_edges: dict[tuple, list] = {}
    finished_edges: dict[tuple, list] = {}
    for edge in cast(Shape, expected).edges():
        if edge.bounding_box().max.Z <= lid.SOCKET_DEPTH - LATTICE_GAP + 1e-6:
            reference_edges.setdefault(_edge_bucket(edge), []).append(edge)
    for edge in cast(Shape, clean).edges():
        finished_edges.setdefault(_edge_bucket(edge), []).append(edge)
    eligible = set()
    for edge in cast(Shape, supported).edges():
        if (
            not validated
            or edge.bounding_box().max.Z > lid.SOCKET_DEPTH - LATTICE_GAP + 1e-6
        ):
            continue
        bucket = _edge_bucket(edge)
        matches = [
            ref
            for ref in reference_edges.get(bucket, ())
            if _same_complete_curve(edge, ref)
        ]
        finished = any(
            _same_complete_curve(edge, ref) for ref in finished_edges.get(bucket, ())
        )
        if len(matches) > 1:
            report.check(False, "sacrificial edge geometry match must be unique")
        if len(matches) == 1 and not finished:
            eligible.add(edge.wrapped)
    allow = (
        (
            lambda edge: edge.wrapped in eligible,
            "Unique whole-curve match to globally validated declared rail/lattice edges below z2.3; no finished curve or roof/neck interface eligible.",
        ),
    )
    for name, part, allowances in (
        ("finished lid", clean, ()),
        ("supported lid", supported, allow),
    ):
        survey = sharp_convex_edges(part, allow=allowances)
        report.check(
            not survey.sharp,
            f"{name}: no unexplained sharp convex edges",
            f"sharp={len(survey.sharp)}",
        )
        report.check(
            not survey.unclassifiable,
            f"{name}: all non-exempt edges classifiable",
            f"unclassifiable={len(survey.unclassifiable)}",
        )
        for predicate, reason in allowances:
            report.lines.append(
                f"  Edge exception matched={sum(predicate(edge) for edge in cast(Shape, part).edges())}: {reason}"
            )
        for edge in (*survey.sharp, *survey.unclassifiable):
            report.lines.append(
                f"  Unapproved edge: center={edge.center()}, length={edge.length:.4f}"
            )


def missing_roof_control(seated: Part, layout: l.Layout) -> Report:
    """Plausible defect: an over-deep socket/cavity pierces one roof panel."""
    x, y = sorted(layout.occupied)[0]
    hole = _box(
        x * GRID,
        y * GRID,
        lid.ceiling_z(layout) - 0.1,
        20,
        20,
        c.WALL + lid.SOCKET_DEPTH + 0.2,
    )
    mutant = _difference(seated, hole)
    negative = Report()
    check_roof(negative, mutant, layout)
    return negative


def closed_roof_gap_control(supported: Part, clean: Part, layout: l.Layout) -> Report:
    """Plausible defect: centre rib accidentally grows to the roof."""
    x, y = sorted(layout.occupied)[0]
    patch = _box(
        x * GRID,
        -y * GRID,
        lid.SOCKET_DEPTH - LATTICE_GAP - 0.01,
        LATTICE_RIB,
        2,
        LATTICE_GAP + 0.03,
    )
    with BuildPart(mode=Mode.PRIVATE) as mutant:
        add(supported)
        add(patch)
    negative = Report()
    check_supports(negative, mutant.part, clean, layout)
    return negative


def closed_end_passage_control(seated: Part, layout: l.Layout) -> Report:
    """Restore a small end-skirt panel: closed fit survives but lift snags."""
    lane = layout.columns[0].lanes[-1]
    end = -GRID / 2 + (GRID - PAD) / 2
    outer = end + c.WALL - 0.02  # Positive weld to retained outer wall.
    inner = end + lid.SKIRT_INNER_INSET
    panel = _box(
        lane.x,
        (outer + inner) / 2,
        l.RIM_Z - lid.SKIRT_ENGAGEMENT,
        lane.wrench.head_thickness,
        inner - outer,
        lid.SKIRT_ENGAGEMENT + lid.SHOULDER_RISE,
    )
    with BuildPart(mode=Mode.PRIVATE) as mutant:
        add(seated)
        add(panel)
    negative = Report()
    _check_tools(negative, mutant.part, layout)
    return negative


def _check_grouping_smoke(report: Report) -> None:
    """Exercise remaining live consumer values without rerunning the bin gate."""
    for count in (1, 2, 4):
        report.section(
            f"{count} per column — live clean/supported grouping / whole-roof smoke"
        )
        layout = l.arrange(count)
        clean = lid.create(count, support=False)
        supported = lid.create(count, support=True)
        report.check(
            supported.is_valid
            and len(supported.solids()) == 1
            and abs(supported.bounding_box().min.Z) < 1e-6,
            "grouping produces one valid supported print at z=0",
        )
        report.check(
            _reference_volume(_difference(clean, supported)) < VOLUME_TOL,
            "grouping support toggle preserves complete clean lid",
        )
        box = clean.bounding_box()
        report.check(
            clean.is_valid and len(clean.solids()) == 1 and abs(box.min.Z) < 1e-6,
            "grouping produces one valid clean print at z=0",
        )
        report.check(
            abs(box.size.X - (len(layout.columns) * GRID - (GRID - PAD))) < 1e-6
            and abs(
                box.size.Y
                - (max(col.cells for col in layout.columns) * GRID - (GRID - PAD))
            )
            < 1e-6,
            "grouping preserves its accepted stepped outside extents",
        )
        seated = as_part(lid.use_location(layout) * clean)
        roof = _slab(layout, c.WALL, lid.ceiling_z(layout), c.WALL)
        report.check(
            _reference_volume(_difference(roof, seated)) < VOLUME_TOL,
            "grouping has intact whole occupied-cell 1 mm roof",
        )
        supported_use = as_part(lid.use_location(layout) * supported)
        report.check(
            _reference_volume(_difference(roof, supported_use)) < VOLUME_TOL,
            "supported grouping has intact whole occupied-cell 1 mm roof",
        )
        tip = l.RIM_Z - lid.SKIRT_ENGAGEMENT
        occupied = _slab(layout, 0, tip, lid.socket_top_z(layout) - tip)
        report.check(
            _reference_volume(_difference(seated, occupied)) < VOLUME_TOL,
            "grouping has no material in absent cells or beyond its footprint",
        )
        report.check(
            _reference_volume(_difference(supported_use, occupied)) < VOLUME_TOL,
            "supported grouping has no material in absent cells or beyond its footprint",
        )


def run() -> Report:
    report = Report()
    for count in (6, 3, 5):
        report.section(f"{count} per column — removable stackable lid / CAD-only proof")
        layout = l.arrange(count)
        clean = lid.create(count, support=False)
        supported = lid.create(count, support=True)
        seated = lid.seated(count)
        bin_part = base.create(count)  # Do NOT rerun the expensive bin-family gate.
        _check_pose_and_seat(report, clean, seated, bin_part, layout)
        check_roof(report, seated, layout)
        _check_tools(report, seated, layout)
        independent_stock = _check_sections(report, seated, clean, layout)
        check_rack_caps(report, seated, lid.rack_passage_tool(layout))
        check_supports(report, supported, clean, layout)
        _check_edges(report, clean, supported, layout)
        if count == 6:
            roof_negative = missing_roof_control(seated, layout)
            gap_negative = closed_roof_gap_control(supported, clean, layout)
            report.check(
                "continuous full-footprint 1 mm roof below every receiver"
                in roof_negative.failures,
                "missing-roof mutant fails SAME permanent continuous-roof predicate",
                "; ".join(roof_negative.failures),
            )
            report.check(
                "cell 0,0 support: roof air gap stays open away from exact declared tabs"
                in gap_negative.failures
                and "cell 0,0 support: entire roof gap contains material only inside declared two tabs"
                in gap_negative.failures,
                "closed-roof-gap mutant fails SAME permanent release predicates",
                "; ".join(gap_negative.failures),
            )
            removal_negative = closed_end_passage_control(seated, layout)
            caught = f"{layout.columns[0].lanes[-1].wrench.label}: continuous loaded straight-up lid removal"
            report.check(
                caught in removal_negative.failures,
                "closed end-skirt passage mutant fails SAME permanent loaded-removal predicate",
                "; ".join(removal_negative.failures),
            )
        if count == 5:
            cap_negative = old_short_cap_control(seated, independent_stock, layout)
            caught_collision = any(
                not entry["passed"]
                and entry["name"].endswith(
                    "terminal face opens into actual finished cavity"
                )
                for entry in cap_negative.entries
            )
            report.check(
                caught_collision,
                "old solo-column cap fails SAME permanent actual-cavity termination predicate",
                "; ".join(cap_negative.failures),
            )
    _check_grouping_smoke(report)
    report.lines.append(
        "  Physical tool fit, sliced gap/neck survival, bridge direction, support removal/sag and loaded stacking are unverified by this CAD gate."
    )
    return report


def main() -> None:
    report = run()
    print(report.render())
    sys.exit(1 if report.failures else 0)
