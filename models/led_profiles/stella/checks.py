"""Finished-core geometry and limited net-section screens, never a load rating."""

from __future__ import annotations

import sys
from math import cos, hypot, pi, radians, sin, sqrt

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Edge,
    GeomType,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Rot,
    ShapeList,
    Solid,
    add,
    extrude,
    loft,
    section,
)
from OCP.BRepGProp import BRepGProp  # ty: ignore[unresolved-import]
from OCP.GProp import GProp_GProps  # ty: ignore[unresolved-import]

from models.lib.checks import (
    Report,
    fastener_clearance,
    periodic_seams,
    sharp_convex_edges,
)
from models.lib.edges import as_part

from . import config as c
from . import core

# Numerical proof tolerances, not manufacturing clearances.
_VOLUME_TOL = 1e-4
_EPS = 1e-5
_BEARING_LAYER = 0.5  # Finite bearing-surface witness, not a full-blank reservation.


def _volume(shape) -> float:
    if shape is None:
        return 0.0
    if isinstance(shape, (list, ShapeList)):
        return sum(item.volume for item in shape)
    return shape.volume


def _contained(part: Part, tool, r: Report, label: str) -> None:
    missing = max(0.0, _volume(tool) - _volume(part.intersect(tool)))
    r.check(
        missing <= _VOLUME_TOL,
        label,
        f"missing {missing:.6f} of {_volume(tool):.3f} mm^3",
    )


def _clear(part: Part, tool, r: Report, label: str) -> None:
    fouled = _volume(part.intersect(tool))
    r.check(fouled <= _VOLUME_TOL, label, f"core collision {fouled:.6f} mm^3")


def _rounded(
    width: float, height: float, radius: float, z: float, depth: float
) -> Part:
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z)):
            RectangleRounded(width, height, radius)
        extrude(amount=depth)
    return tool.part


def _cylinder(radius: float, z: float, depth: float) -> Part:
    with BuildPart() as tool:
        with Locations((0, 0, z)):
            Cylinder(radius, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return tool.part


def _xy(angle: float, radial: float) -> tuple[float, float]:
    return radial * cos(radians(angle)), radial * sin(radians(angle))


def _capsule(
    centre_spacing: float,
    radius: float,
    z: float,
    depth: float,
) -> Part:
    """Rounded-rectangle capsule; tiny excess avoids RectangleRounded's equality ban."""
    return _rounded(
        centre_spacing + 2 * radius,
        2 * radius + _EPS,
        radius,
        z,
        depth,
    )


def _radial_sweep(
    start: float,
    end: float,
    diameter: float,
    z: float,
    depth: float,
) -> Part:
    """Exact planar sweep of an upright round envelope translated radially."""
    radius = diameter / 2
    with BuildPart() as tool:
        with Locations(((start + end) / 2, 0, z)):
            Box(
                end - start,
                diameter,
                depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        for radial in (start, end):
            with Locations((radial, 0, z)):
                Cylinder(
                    radius,
                    depth,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
    return tool.part


def _slice_area(part: Part, z: float, thickness: float = 0.1) -> float:
    bounds = part.bounding_box()
    with BuildPart() as slab:
        with Locations((bounds.center().X, bounds.center().Y, z)):
            Box(
                bounds.size.X + 2,
                bounds.size.Y + 2,
                thickness,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    return _volume(part.intersect(slab.part)) / thickness


def _outline(part: Part, r: Report) -> None:
    r.section("Continuous full-height organic outline and height budget")
    bounds = part.bounding_box()
    r.check(
        abs(bounds.size.Z - c.CORE_H) < _EPS,
        "outline actual overall height",
        f"{bounds.size.Z:.3f} mm; target {c.CORE_H_TARGET:g} mm, "
        f"implemented departure +{c.CORE_H - c.CORE_H_TARGET:g} mm",
    )
    hardware_min = c.INSERT_DEPTH + c.INSERT_FLOOR + c.SEAT_DEPTH
    r.check(
        c.CORE_H >= hardware_min,
        "outline insert relief, retained floor and keyed-seat stack",
        f"{c.INSERT_DEPTH:g} + {c.INSERT_FLOOR:g} + {c.SEAT_DEPTH:g} "
        f"= {hardware_min:g} mm <= {c.CORE_H:g} mm",
    )
    lower_z = max(c.EDGE_CHAMFER, c.SUSPENSION_CONTACT_R) + 0.2
    upper_z = c.SEAT_Z - c.INSERT_DEPTH - 0.2
    r.check(
        upper_z > lower_z,
        "outline has two feature-free interior comparison levels",
        f"z={lower_z:.3f} and {upper_z:.3f} mm",
    )
    if upper_z > lower_z:
        lower = _slice_area(part, lower_z)
        upper = _slice_area(part, upper_z)
        r.check(
            abs(lower - upper) <= 1e-3,
            "outline section is unchanged below functional seat and pilot cuts",
            f"areas {lower:.3f}/{upper:.3f} mm^2; "
            f"difference {abs(lower - upper):.6f} mm^2",
        )


def _seats(part: Part, r: Report) -> None:
    r.section("Seat bearing, closed keys, blind insert hosts and service tools")
    floor_blank = _rounded(
        c.SEAT_LENGTH,
        c.SEAT_WIDTH,
        c.SEAT_RADIUS,
        c.SEAT_Z - _BEARING_LAYER,
        _BEARING_LAYER,
    )
    with BuildPart() as bearing:
        add(as_part(Pos(c.SEAT_R, 0, 0) * floor_blank))
        for radial in c.INSERT_RADII:
            with Locations((radial, 0, c.SEAT_Z - _BEARING_LAYER - _EPS)):
                Cylinder(
                    c.INSERT_PILOT_D / 2,
                    _BEARING_LAYER + 2 * _EPS,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
    floor = bearing.part
    seat_air = Pos(c.SEAT_R, 0, 0) * _rounded(
        c.SEAT_LENGTH,
        c.SEAT_WIDTH,
        c.SEAT_RADIUS,
        c.SEAT_Z + _EPS,
        c.CORE_H - c.SEAT_Z,
    )
    # Independently built loft verifies the actual entry, not the tool in core.py.
    with BuildPart() as lead:
        for z, expansion in ((c.CORE_H - c.SEAT_LEAD, 0), (c.CORE_H, c.SEAT_LEAD)):
            with BuildSketch(Plane.XY.offset(z)):
                with Locations((c.SEAT_R, 0)):
                    RectangleRounded(
                        c.SEAT_LENGTH + 2 * expansion,
                        c.SEAT_WIDTH + 2 * expansion,
                        c.SEAT_RADIUS + expansion,
                    )
        loft(ruled=True)
    chamfer_air = lead.part
    shoulder_z = c.SEAT_Z + _EPS
    shoulder_h = c.CORE_H - c.SEAT_LEAD - shoulder_z
    shoulder_outer = _rounded(
        c.SEAT_LENGTH + 2 * c.INSERT_WALL,
        c.SEAT_WIDTH + 2 * c.INSERT_WALL,
        c.SEAT_RADIUS + c.INSERT_WALL,
        shoulder_z,
        shoulder_h,
    )
    shoulder_inner = _rounded(
        c.SEAT_LENGTH,
        c.SEAT_WIDTH,
        c.SEAT_RADIUS,
        shoulder_z - _EPS,
        shoulder_h + 2 * _EPS,
    )
    with BuildPart() as shoulder:
        add(as_part(Pos(c.SEAT_R, 0, 0) * shoulder_outer))
        add(as_part(Pos(c.SEAT_R, 0, 0) * shoulder_inner), mode=Mode.SUBTRACT)
    shoulders = shoulder.part
    for angle in c.BRANCH_ANGLES:
        pose = Rot(0, 0, angle)
        label = f"seat {angle:g} deg"
        _contained(
            part, pose * floor, r, f"{label}: entire keyed bearing floor minus pilots"
        )
        _contained(
            part,
            pose * shoulders,
            r,
            f"{label}: closed {c.INSERT_WALL:g} mm locating shoulders",
        )
        _clear(part, pose * seat_air, r, f"{label}: keyed drop-in air")
        _clear(
            part, pose * chamfer_air, r, f"{label}: {c.SEAT_LEAD:g} mm entry chamfer"
        )
        for radial in c.INSERT_RADII:
            x, y = _xy(angle, radial)
            pilot = Pos(x, y, 0) * _cylinder(
                c.INSERT_PILOT_D / 2 - _EPS,
                c.SEAT_Z - c.INSERT_DEPTH + _EPS,
                c.INSERT_DEPTH - _EPS,
            )
            prefix = f"{label}, insert r={radial:g}"
            _clear(
                part,
                pilot,
                r,
                f"{prefix}: full blind pilot depth {c.INSERT_DEPTH:g} mm",
            )
            with BuildPart() as annulus:
                with Locations((x, y, c.SEAT_Z - c.INSERT_DEPTH)):
                    Cylinder(
                        c.INSERT_OD / 2 + c.INSERT_WALL,
                        c.INSERT_DEPTH,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                with Locations((x, y, c.SEAT_Z - c.INSERT_DEPTH - _EPS)):
                    Cylinder(
                        c.INSERT_PILOT_D / 2,
                        c.INSERT_DEPTH + 2 * _EPS,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
            host = annulus.part
            _contained(
                part,
                host,
                r,
                f"{prefix}: >= {c.INSERT_WALL:g} mm radial host outside installed OD {c.INSERT_OD:g}",
            )
            bottom = Pos(x, y, 0) * _cylinder(
                c.INSERT_OD / 2 + c.INSERT_WALL,
                c.SEAT_Z - c.INSERT_DEPTH - c.INSERT_FLOOR,
                c.INSERT_FLOOR,
            )
            _contained(
                part, bottom, r, f"{prefix}: >= {c.INSERT_FLOOR:g} mm blind floor"
            )
            iron = fastener_clearance(
                part,
                (x, y, c.SEAT_Z),
                c.IRON_TIP_D,
                c.IRON_TIP_LENGTH,
                driver_d=c.IRON_BODY_D,
                driver_len=c.IRON_BODY_LENGTH,
            )
            r.check(
                iron <= _VOLUME_TOL,
                f"{prefix}: installation iron before arm",
                f"tip/body collision {iron:.6f} mm^3",
            )
            washer_z = c.SEAT_Z + c.ARM_STACK
            washer = fastener_clearance(part, (x, y, washer_z), c.WASHER_D, c.WASHER_T)
            head = fastener_clearance(
                part,
                (x, y, washer_z + c.WASHER_T),
                c.HEAD_D,
                c.HEAD_H,
                driver_d=c.DRIVER_D,
                driver_len=c.DRIVER_LENGTH,
            )
            r.check(
                washer + head <= _VOLUME_TOL,
                f"{prefix}: washer/head/driver above arm stack",
                f"{c.ARM_STACK:g} mm reserved arm; collision {washer + head:.6f} mm^3",
            )
    engagement = c.SCREW_LENGTH - c.ARM_STACK - c.WASHER_T
    bottom_relief = c.INSERT_DEPTH - engagement
    r.check(
        c.SCREW_D <= engagement <= c.INSERT_LENGTH and bottom_relief >= c.INSERT_PITCH,
        "seat screw engagement and bottom relief",
        f"M{c.SCREW_D:g} x {c.SCREW_LENGTH:g}, stack {c.ARM_STACK:g} + washer {c.WASHER_T:g}: "
        f"engagement {engagement:.3f}, bottom relief {bottom_relief:.3f} mm; not pull-out capacity",
    )


def _cables(part: Part, r: Report) -> None:
    r.section("Solid valleys and local external terminated-cable service corridors")
    with BuildPart() as valley_band:
        with Locations(
            (
                (c.VALLEY_SOLID_INNER_R + c.VALLEY_SOLID_OUTER_R) / 2,
                0,
                c.EDGE_CHAMFER,
            )
        ):
            Box(
                c.VALLEY_SOLID_OUTER_R - c.VALLEY_SOLID_INNER_R,
                c.CABLE_ENVELOPE_D,
                c.CORE_H - 2 * c.EDGE_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    cable_sweep = _radial_sweep(
        c.CABLE_SERVICE_R,
        c.SERVICE_OUTER_R,
        c.CABLE_ENVELOPE_D,
        0,
        c.CORE_H,
    )
    connector_sweep = _radial_sweep(
        c.CONNECTOR_SERVICE_R,
        c.SERVICE_OUTER_R,
        c.CONNECTOR_D,
        0,
        c.CONNECTOR_COUPLED_LENGTH,
    )
    hand_sweep = _radial_sweep(
        c.COUPLING_SERVICE_R,
        c.SERVICE_OUTER_R,
        c.COUPLING_HAND_D,
        0,
        c.CONNECTOR_COUPLED_LENGTH + c.COUPLING_STROKE,
    )
    cable_bend = Solid.make_torus(
        c.CABLE_BEND_R,
        c.CABLE_ENVELOPE_D / 2,
        plane=Plane(
            origin=(c.CABLE_SERVICE_R + c.CABLE_BEND_R, 0, c.CORE_H),
            x_dir=(-1, 0, 0),
            z_dir=(0, 1, 0),
        ),
        major_angle=90,
    )
    for angle in c.BRANCH_ANGLES:
        valley_angle = (angle + 60) % 360
        pose = Rot(0, 0, valley_angle)
        label = f"external cable valley {valley_angle:g} deg"
        _contained(
            part,
            pose * valley_band.part,
            r,
            f"{label}: uninterrupted solid band; no core cable notch",
        )
        _clear(
            part,
            pose * cable_sweep,
            r,
            f"{label}: side-open sleeved cable corridor from r={c.CABLE_SERVICE_R:g}",
        )
        _clear(
            part,
            pose * cable_bend,
            r,
            f"{label}: external fixed-install bend R{c.CABLE_BEND_R:g}",
        )
        _clear(
            part,
            pose * connector_sweep,
            r,
            f"{label}: coupled connector side corridor from r={c.CONNECTOR_SERVICE_R:g}",
        )
        _clear(
            part,
            pose * hand_sweep,
            r,
            f"{label}: hand/unplug corridor from r={c.COUPLING_SERVICE_R:g}",
        )
    r.lines.append(
        "  Core-only external corridors do not prove the deferred arm, connector "
        "variant, full bend path, cable retention or lamp-extraction sequence."
    )


def _sling(part: Part, r: Report) -> None:
    r.section(
        "Two-hole closed cord loop: passage, rounded contact, bridge and ligaments"
    )
    hole_r = c.SUSPENSION_HOLE_D / 2
    mouth_r = hole_r + c.SUSPENSION_CONTACT_R
    for x in c.SUSPENSION_HOLE_CENTRES:
        required_bore = Pos(x, 0, 0) * _cylinder(
            hole_r - _EPS,
            -_EPS,
            c.CORE_H + 2 * _EPS,
        )
        _clear(
            part,
            required_bore,
            r,
            f"suspension hole x={x:g}: full Ø{c.SUSPENSION_HOLE_D:g} passage",
        )

    with BuildPart() as under_bridge:
        with Locations((0, 0, -c.CORD_D)):
            Box(
                c.SUSPENSION_HOLE_SPACING + c.CORD_D,
                c.CORD_D,
                c.CORD_D,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    _clear(
        part,
        under_bridge.part,
        r,
        f"suspension nominal Ø{c.CORD_D:g} route remains open below bridge",
    )

    throat_inner = _capsule(
        c.SUSPENSION_HOLE_SPACING,
        hole_r,
        c.SUSPENSION_CONTACT_R,
        c.SUSPENSION_EFFECTIVE_H,
    )
    throat_outer = _capsule(
        c.SUSPENSION_HOLE_SPACING,
        hole_r + c.SUSPENSION_MIN_LIGAMENT,
        c.SUSPENSION_CONTACT_R,
        c.SUSPENSION_EFFECTIVE_H,
    )
    with BuildPart() as throat_ring:
        add(throat_outer)
        add(throat_inner, mode=Mode.SUBTRACT)
    _contained(
        part,
        throat_ring.part,
        r,
        f"suspension >= {c.SUSPENSION_MIN_LIGAMENT:g} mm outer ligament "
        "through straight throat",
    )
    with BuildPart() as throat_bridge:
        with Locations((0, 0, c.SUSPENSION_CONTACT_R)):
            Box(
                c.SUSPENSION_BRIDGE_THROAT - 2 * _EPS,
                c.SUSPENSION_HOLE_D,
                c.SUSPENSION_EFFECTIVE_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    _contained(
        part,
        throat_bridge.part,
        r,
        f"suspension {c.SUSPENSION_BRIDGE_THROAT:g} mm throat bridge",
    )

    mouth_band_h = 0.5
    for name, z in (
        ("lower", c.EDGE_CHAMFER),
        ("upper", c.CORE_H - c.EDGE_CHAMFER - mouth_band_h),
    ):
        mouth_inner = _capsule(
            c.SUSPENSION_HOLE_SPACING,
            mouth_r,
            z,
            mouth_band_h,
        )
        mouth_outer = _capsule(
            c.SUSPENSION_HOLE_SPACING,
            mouth_r + c.SUSPENSION_MIN_LIGAMENT,
            z,
            mouth_band_h,
        )
        with BuildPart() as mouth_ring:
            add(mouth_outer)
            add(mouth_inner, mode=Mode.SUBTRACT)
        _contained(
            part,
            mouth_ring.part,
            r,
            f"suspension {name} mouth keeps {c.SUSPENSION_MIN_LIGAMENT:g} mm "
            "outer material band",
        )
        with BuildPart() as mouth_bridge:
            with Locations((0, 0, z)):
                Box(
                    c.SUSPENSION_BRIDGE_MOUTH - 2 * _EPS,
                    2 * mouth_r,
                    mouth_band_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        _contained(
            part,
            mouth_bridge.part,
            r,
            f"suspension {name} mouth keeps {c.SUSPENSION_BRIDGE_MOUTH:g} mm bridge",
        )

    for x in c.SUSPENSION_HOLE_CENTRES:
        for top in (False, True):
            rounded = []
            for face in part.faces():  # ty: ignore[invalid-argument-type]
                if face.geom_type != GeomType.TORUS or face.radii is None:
                    continue
                bb = face.bounding_box()
                if abs(bb.center().X - x) > _EPS or abs(bb.center().Y) > _EPS:
                    continue
                if top and bb.min.Z < c.CORE_H - c.SUSPENSION_CONTACT_R - _EPS:
                    continue
                if not top and bb.max.Z > c.SUSPENSION_CONTACT_R + _EPS:
                    continue
                major, minor = face.radii
                if (
                    abs(major - mouth_r) < _EPS
                    and abs(minor - c.SUSPENSION_CONTACT_R) < _EPS
                ):
                    rounded.append(face)
            name = "upper" if top else "lower"
            r.check(
                len(rounded) == 1,
                f"suspension hole x={x:g}: {name} actual "
                f"R{c.SUSPENSION_CONTACT_R:g} toroidal contact",
                f"{len(rounded)} matching faces",
            )
    r.lines.append(
        "  The clear top approach leaves the joining knot visible and reachable, "
        "but geometry does not qualify knot capacity, tail length, movement, "
        "equal sharing or abrasion life."
    )


def _net_screen(
    part: Part,
    r: Report,
    label: str,
    station: float,
    axial: float,
    shear: float,
    load_z: float,
    load_r: float,
    handling: float,
) -> None:
    net = section(
        part,
        section_by=Plane(origin=(station, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)),
        mode=Mode.PRIVATE,
    )
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(net.wrapped, props)
    area = props.Mass()
    if area <= _EPS:
        r.check(False, f"{label}: actual net section", f"area {area:.6f} mm^2")
        return
    centroid = props.CentreOfMass()
    inertia = props.MatrixOfInertia()
    iy = inertia.Value(2, 2)  # integral (z-zbar)^2 dA
    iz = inertia.Value(3, 3)  # integral (t-tbar)^2 dA
    product = -inertia.Value(2, 3)  # OCC inertia off-diagonal is minus integral t*z.
    determinant = iy * iz - product * product
    r.check(
        determinant > _EPS,
        f"{label}: nondegenerate actual net section",
        f"A={area:.3f} mm^2, (tbar,zbar)=({centroid.Y():.3f},{centroid.Z():.3f}) mm; "
        f"Itt={iy:.3f}, Izz={iz:.3f}, integral(tz)={product:.3f} mm^4",
    )
    if determinant <= _EPS:
        return
    bounds = net.bounding_box()
    corners = [
        (t - centroid.Y(), z - centroid.Z())
        for t in (bounds.min.Y, bounds.max.Y)
        for z in (bounds.min.Z, bounds.max.Z)
    ]
    for name, factor, limit, extra in (
        ("sustained", c.SUSTAINED_FACTOR, c.ABS_SUSTAINED_MPA, 0.0),
        ("short event", c.EVENT_FACTOR, c.ABS_EVENT_MPA, handling),
    ):
        force = factor * axial
        transverse = factor * shear
        my = abs(transverse * (load_r - station)) + abs(force * (load_z - centroid.Z()))
        mz = abs(force * centroid.Y())
        # The rectangular bounds enclose every point of the ACTUAL net section.
        # Linear normal stress reaches its bound at a corner. Cauchy-Schwarz
        # bounds one arbitrary handling moment vector, not two full moments.
        normal = 0.0
        for t, z in corners:
            ky = (iz * z - product * t) / determinant
            kz = (iy * t - product * z) / determinant
            normal = max(
                normal,
                abs(force) / area + abs(ky) * my + abs(kz) * mz + extra * hypot(ky, kz),
            )
        tau = 1.5 * abs(transverse) / area
        stress = c.LOCAL_STRESS_FACTOR * sqrt(normal * normal + 3 * tau * tau)
        r.check(
            stress <= limit,
            f"{label}: {name} limited beam screen",
            f"sigma_bound={normal:.3f}, tau_bound={tau:.3f}, local VM={stress:.3f} "
            f"<= {limit:.3f} MPa; N={force:.2f}, V={transverse:.2f} N; "
            f"|My|<={my:.2f}, |Mz|<={mz:.2f}, handling vector {extra:.2f} N mm",
        )


def _sections(part: Part, r: Report) -> None:
    r.section(
        "Actual cut-section ABS screen: limited beam estimate, not frame stiffness, creep or rating"
    )
    r.lines.append(
        f"  Flat-web +Z print; {c.PART_TEMPERATURE_C:g} C, {c.DURATION_DAYS:g} days; "
        f"assumed process/temperature/duration factors {c.PROCESS_FACTOR:g}/"
        f"{c.TEMPERATURE_FACTOR:g}/{c.DURATION_FACTOR:g}, local stress factor {c.LOCAL_STRESS_FACTOR:g}. "
        "Ideal axial-member force directions; unsolved rigid-frame redistribution excluded."
    )
    axial = c.MEMBER_STATIC_N / sqrt(3)
    shear = c.MEMBER_STATIC_N * sqrt(2 / 3)
    for angle in c.BRANCH_ANGLES:
        local = as_part(Rot(0, 0, -angle) * part)
        for station in c.ROOT_STATIONS:
            _net_screen(
                local,
                r,
                f"section branch {angle:g} deg r={station:g}",
                station,
                axial,
                shear,
                c.LOAD_Z,
                c.SEAT_R,
                c.HANDLING_MOMENT_NMM,
            )
    # Two orthogonal central cuts include both bores and the real material bridge.
    # The line load is bounded entirely as transverse shear; unequal hole sharing
    # is handled again by the one-ligament and one-bridge screens below.
    for angle in (0.0, 90.0):
        local = as_part(Rot(0, 0, -angle) * part)
        _net_screen(
            local,
            r,
            f"section suspension region {angle:g} deg",
            0,
            0.0,
            c.LINE_STATIC_N,
            c.CORE_H,
            0.0,
            0.0,
        )
    for section_name, width in (
        ("one outer ligament", c.SUSPENSION_MIN_LIGAMENT),
        ("central bridge at rounded mouth", c.SUSPENSION_BRIDGE_MOUTH),
    ):
        area = width * c.SUSPENSION_EFFECTIVE_H
        for name, factor, limit in (
            ("sustained", c.SUSTAINED_FACTOR, c.ABS_SUSTAINED_MPA),
            ("short event", c.EVENT_FACTOR, c.ABS_EVENT_MPA),
        ):
            stress = (
                c.LOCAL_STRESS_FACTOR * sqrt(3) * 1.5 * factor * c.LINE_STATIC_N / area
            )
            r.check(
                stress <= limit,
                f"suspension {section_name} {name} shear screen",
                f"entire line load on proved A>={area:.3f} mm^2; "
                f"local VM={stress:.3f} <= {limit:.3f} MPa; "
                "no cord/contact qualification",
            )
    spacing = abs(c.INSERT_RADII[1] - c.INSERT_RADII[0])
    for name, factor, handling in (
        ("sustained", c.SUSTAINED_FACTOR, 0.0),
        ("short event", c.EVENT_FACTOR, c.HANDLING_MOMENT_NMM),
    ):
        moment = factor * axial * abs(c.LOAD_Z - c.SEAT_Z) + handling
        tension = factor * shear / 2 + moment / spacing + c.PRELOAD_N
        shear_demand = factor * axial / 2
        r.lines.append(
            f"  seat insert {name}: unqualified retention demand {tension:.2f} N/insert "
            f"including illustrative {c.PRELOAD_N:g} N preload; pair spacing {spacing:g} mm, "
            f"moment {moment:.2f} N mm, transverse shear demand {shear_demand:.2f} N/insert. "
            "No pull-out, torque-out, preload retention or printed-ABS capacity is proved."
        )


def _edge_detail(edges) -> str:
    return f"{len(edges)} edges" + (
        ": "
        + "; ".join(
            f"{edge.geom_type} L={edge.length:.3f} at "
            f"{tuple(round(v, 3) for v in edge.bounding_box().center())}"
            for edge in edges
        )
        if edges
        else ""
    )


def _edges(part: Part, r: Report) -> None:
    r.section("Sharp and unclassifiable edge survey: exact exceptions only")
    centres = [
        _xy(angle, radial) for angle in c.BRANCH_ANGLES for radial in c.INSERT_RADII
    ]
    seam = periodic_seams(part)

    def pilot_mouth(edge: Edge) -> bool:
        if edge.geom_type != GeomType.CIRCLE:
            return False
        centre = edge.arc_center
        return (
            abs(centre.Z - c.SEAT_Z) < _EPS
            and abs(edge.radius - c.INSERT_PILOT_D / 2) < _EPS
            and abs(edge.length - pi * c.INSERT_PILOT_D) < _EPS
            and any(hypot(centre.X - x, centre.Y - y) < _EPS for x, y in centres)
        )

    def pilot_seam(edge: Edge) -> bool:
        if edge.geom_type != GeomType.LINE or not seam(edge):
            return False
        bb = edge.bounding_box()
        return (
            abs(bb.min.Z - (c.SEAT_Z - c.INSERT_DEPTH)) < _EPS
            and abs(bb.max.Z - c.SEAT_Z) < _EPS
            and bb.size.X < _EPS
            and bb.size.Y < _EPS
            and any(
                abs(hypot(bb.min.X - x, bb.min.Y - y) - c.INSERT_PILOT_D / 2) < _EPS
                for x, y in centres
            )
        )

    def suspension_bore_seam(edge: Edge) -> bool:
        if not seam(edge):
            return False
        bb = edge.bounding_box()
        if edge.geom_type == GeomType.LINE:
            return (
                abs(edge.length - c.SUSPENSION_EFFECTIVE_H) < _EPS
                and abs(bb.min.Z - c.SUSPENSION_CONTACT_R) < _EPS
                and abs(bb.max.Z - (c.CORE_H - c.SUSPENSION_CONTACT_R)) < _EPS
                and bb.size.X < _EPS
                and bb.size.Y < _EPS
                and any(
                    abs(bb.center().X - (x + c.SUSPENSION_HOLE_D / 2)) < _EPS
                    and abs(bb.center().Y) < _EPS
                    for x in c.SUSPENSION_HOLE_CENTRES
                )
            )
        if edge.geom_type != GeomType.CIRCLE:
            return False
        centre = edge.arc_center
        return (
            abs(edge.radius - c.SUSPENSION_CONTACT_R) < _EPS
            and abs(edge.length - pi * c.SUSPENSION_CONTACT_R / 2) < _EPS
            and abs(centre.Y) < _EPS
            and any(
                abs(centre.X - (x + c.SUSPENSION_HOLE_D / 2 + c.SUSPENSION_CONTACT_R))
                < _EPS
                for x in c.SUSPENSION_HOLE_CENTRES
            )
            and (
                abs(centre.Z - c.SUSPENSION_CONTACT_R) < _EPS
                or abs(centre.Z - (c.CORE_H - c.SUSPENSION_CONTACT_R)) < _EPS
            )
        )

    allow = (
        (
            pilot_mouth,
            "raw heat-set pilot mouth preserves melt stock; insert supplies its own lead-in",
        ),
        (
            pilot_seam,
            "exact blind pilot's periodic cylindrical seam has no physical corner",
        ),
        (
            suspension_bore_seam,
            "exact suspension bore cylinder/torus seam has no physical corner",
        ),
    )
    for predicate, reason in allow:
        matches = [
            edge
            for edge in part.edges()  # ty: ignore[invalid-argument-type]
            if predicate(edge)
        ]
        r.lines.append(f"  edge exception: {reason}: {_edge_detail(matches)}")
    survey = sharp_convex_edges(part, allow=allow)
    r.check(
        not survey.sharp,
        "edge no unexplained sharp convex edges",
        _edge_detail(survey.sharp),
    )
    r.check(
        not survey.unclassifiable,
        "edge no unexplained unclassifiable edges",
        _edge_detail(survey.unclassifiable),
    )


def check_core(r: Report, part: Part | None = None) -> None:
    """Check final supplied geometry; defect probes never rebuild an unbroken core."""
    if part is None:
        part = core.create()
    r.section("Functional Stella core: topology and flat-body print pose")
    count = len(part.solids())
    valid = part.is_valid
    r.check(count == 1, "core one connected solid", f"{count} solids")
    r.check(valid, "core valid B-rep")
    if count != 1 or not valid:
        return
    bounds = part.bounding_box()
    r.check(abs(bounds.min.Z) < _EPS, "core bed at z=0", f"min z={bounds.min.Z:.6f} mm")
    bed_area = sum(
        face.area
        for face in part.faces()  # ty: ignore[invalid-argument-type]
        if face.geom_type == GeomType.PLANE
        and abs(face.bounding_box().min.Z) < _EPS
        and abs(face.bounding_box().max.Z) < _EPS
    )
    r.check(bed_area > _EPS, "core planar bed contact", f"{bed_area:.3f} mm^2")
    _outline(part, r)
    _seats(part, r)
    _cables(part, r)
    _sling(part, r)
    _sections(part, r)
    _edges(part, r)


def run() -> Report:
    r = Report()
    check_core(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
