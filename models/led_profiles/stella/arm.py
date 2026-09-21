"""Complete Stella profile arm in mouth-up ABS print pose."""

from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Line,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    Sketch,
    SlotOverall,
    ThreePointArc,
    add,
    extrude,
    loft,
    make_face,
)

from models.lib.edges import as_part

from . import config as c

PARAMS = []
IS_ASSEMBLY = False


def _plane_at(
    origin: tuple[float, float, float],
    normal: tuple[float, float, float],
) -> Plane:
    return Plane(origin=origin, x_dir=(0.0, 1.0, 0.0), z_dir=normal)


def _offset(
    point: tuple[float, float, float],
    direction: tuple[float, float, float],
    distance: float,
) -> tuple[float, float, float]:
    return tuple(point[i] + direction[i] * distance for i in range(3))  # type: ignore[return-value]


def _guard_solid(
    part: Part,
    label: str,
    volume_range: tuple[float, float],
    min_z_range: tuple[float, float],
    max_z_range: tuple[float, float],
) -> Part:
    """Fail beside construction when a boolean or loft stops making the intended
    solid.
    """
    bounds = part.bounding_box()
    if (
        len(part.solids()) != 1
        or not part.is_valid
        or not volume_range[0] <= part.volume <= volume_range[1]
        or not min_z_range[0] <= bounds.min.Z <= min_z_range[1]
        or not max_z_range[0] <= bounds.max.Z <= max_z_range[1]
    ):
        raise RuntimeError(
            f"{label} invalid: solids={len(part.solids())}, valid={part.is_valid}, "
            f"volume={part.volume:.3f}, z={bounds.min.Z:.6f}..{bounds.max.Z:.6f}"
        )
    return part


def _root() -> Part:
    """Broad shoulder plate plus the exact nominal key and two M3 paths."""
    centre = (c.ARM_ROOT_FACE_X, 0.0, c.ARM_ROOT_FACE_Z)
    bearing = _plane_at(centre, c.ARM_CORE_NORMAL)

    with BuildPart() as root:
        # The shoulder plate is larger than the seat and bears on the core top.
        for depth, inset in (
            (-c.ARM_BACKPLATE_DEPTH, c.SADDLE_EDGE_CHAMFER),
            (-c.ARM_BACKPLATE_DEPTH + c.SADDLE_EDGE_CHAMFER, 0.0),
            (-c.SADDLE_EDGE_CHAMFER, 0.0),
            (0.0, c.SADDLE_EDGE_CHAMFER),
        ):
            with BuildSketch(bearing.offset(depth)):
                RectangleRounded(
                    c.ARM_BACKPLATE_WIDTH - 2 * inset,
                    c.ARM_BACKPLATE_LENGTH - 2 * inset,
                    c.ARM_BACKPLATE_RADIUS - inset,
                )
        loft(ruled=True)

        # The core seat owns clearance; this key remains exactly nominal.
        for depth, inset in (
            (0.0, 0.0),
            (c.ARM_KEY_DEPTH - c.ARM_KEY_LEAD, 0.0),
            (c.ARM_KEY_DEPTH, c.ARM_KEY_LEAD),
        ):
            with BuildSketch(bearing.offset(depth)):
                RectangleRounded(
                    c.ARM_KEY_WIDTH - 2 * inset,
                    c.ARM_KEY_LENGTH - 2 * inset,
                    c.ARM_KEY_RADIUS - inset / 2,
                )
        loft(ruled=True, mode=Mode.ADD)

        # Hole positions are the core's accepted local radial offsets, ±9 mm.
        for radial_offset in (-9.0, 9.0):
            axis = _offset(centre, c.ARM_FACE_TANGENT, radial_offset)
            start = _offset(axis, c.ARM_CORE_NORMAL, c.ARM_KEY_DEPTH + 1.0)
            hole_plane = _plane_at(start, c.ARM_INWARD_NORMAL)
            add(
                as_part(
                    hole_plane.location
                    * Cylinder(
                        c.ARM_CLEAR_D / 2,
                        c.ARM_STACK + 2.0,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.PRIVATE,
                    )
                ),
                mode=Mode.SUBTRACT,
            )
            add(
                as_part(
                    hole_plane.location
                    * Cone(
                        c.ARM_CLEAR_D / 2 + c.ARM_HOLE_LEAD,
                        c.ARM_CLEAR_D / 2,
                        c.ARM_HOLE_LEAD,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.PRIVATE,
                    )
                ),
                mode=Mode.SUBTRACT,
            )
            back_axis = _offset(axis, c.ARM_INWARD_NORMAL, c.ARM_BACKPLATE_DEPTH)
            back_mouth = _plane_at(back_axis, c.ARM_CORE_NORMAL)
            add(
                as_part(
                    back_mouth.location
                    * Cone(
                        c.ARM_CLEAR_D / 2 + c.ARM_HOLE_LEAD,
                        c.ARM_CLEAR_D / 2,
                        c.ARM_HOLE_LEAD,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.PRIVATE,
                    )
                ),
                mode=Mode.SUBTRACT,
            )
    return _guard_solid(
        root.part,
        "Stella arm root",
        (10_000.0, 15_000.0),
        (0.0, 0.2),
        (40.0, 42.0),
    )


def _final_root_access_tools() -> tuple[Part, ...]:
    """Clear screw shanks and straight driver approaches after fusing the shell."""
    centre = (c.ARM_ROOT_FACE_X, 0.0, c.ARM_ROOT_FACE_Z)
    tools: list[Part] = []
    for radial_offset in (-9.0, 9.0):
        axis = _offset(centre, c.ARM_FACE_TANGENT, radial_offset)
        shank_start = _offset(axis, c.ARM_CORE_NORMAL, c.ARM_KEY_DEPTH + 1.0)
        shank_plane = _plane_at(shank_start, c.ARM_INWARD_NORMAL)
        tools.append(
            as_part(
                shank_plane.location
                * Cylinder(
                    c.ARM_CLEAR_D / 2,
                    c.ARM_STACK + 2.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            )
        )
        back = _offset(axis, c.ARM_INWARD_NORMAL, c.ARM_BACKPLATE_DEPTH)
        driver_plane = _plane_at(back, c.ARM_INWARD_NORMAL)
        tools.append(
            as_part(
                driver_plane.location
                * Cylinder(
                    (c.DRIVER_D + 2 * c.DRIVER_PATH_CLEARANCE) / 2,
                    c.HEAD_H + c.DRIVER_LENGTH + 1.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.PRIVATE,
                )
            )
        )
    return tuple(tools)


def _shell_section(
    station: float,
    outer_half_width: float,
    mouth_z: float,
    scale: float = 1.0,
    z_offset: float = 0.0,
) -> Sketch:
    """Build and prove one bounded U-section around its profile-derived cavity."""
    inner_half_width = (c.profile.WIDTH + c.PROFILE_CLEAR) / 2 * scale
    lower_arc_from_bed = (
        c.SADDLE_AXIS_Z - (c.profile.HEIGHT - c.profile.WIDTH) / 2
    ) * scale
    lower_arc_z = z_offset + lower_arc_from_bed
    outer_half_width *= scale
    mouth_z = z_offset + mouth_z * scale
    rim_r = c.SHELL_RIM_RADIUS * scale
    if outer_half_width - inner_half_width <= 2 * rim_r:
        raise RuntimeError(
            f"shell section x={station:g} has no finite rounded rim land"
        )
    bed_half_width = sqrt(outer_half_width**2 - lower_arc_from_bed**2)
    bed_angle = atan2(lower_arc_from_bed, bed_half_width)
    quarter_offset = rim_r * (1 - 1 / sqrt(2))

    with BuildSketch(Plane.YZ.offset(station)) as section_face:
        with BuildLine() as boundary:
            # Right inner flank and rounded rim.
            Line(
                (inner_half_width, lower_arc_z),
                (inner_half_width, mouth_z - rim_r),
            )
            ThreePointArc(
                (inner_half_width, mouth_z - rim_r),
                (
                    inner_half_width + quarter_offset,
                    mouth_z - quarter_offset,
                ),
                (inner_half_width + rim_r, mouth_z),
            )
            Line(
                (inner_half_width + rim_r, mouth_z),
                (outer_half_width - rim_r, mouth_z),
            )
            ThreePointArc(
                (outer_half_width - rim_r, mouth_z),
                (
                    outer_half_width - quarter_offset,
                    mouth_z - quarter_offset,
                ),
                (outer_half_width, mouth_z - rim_r),
            )

            # Profile-following outer lower arc, truncated by a finite bed line.
            Line(
                (outer_half_width, mouth_z - rim_r),
                (outer_half_width, lower_arc_z),
            )
            ThreePointArc(
                (outer_half_width, lower_arc_z),
                (
                    outer_half_width * cos(bed_angle / 2),
                    lower_arc_z - outer_half_width * sin(bed_angle / 2),
                ),
                (bed_half_width, z_offset),
            )
            Line((bed_half_width, z_offset), (-bed_half_width, z_offset))
            ThreePointArc(
                (-bed_half_width, z_offset),
                (
                    -outer_half_width * cos(bed_angle / 2),
                    lower_arc_z - outer_half_width * sin(bed_angle / 2),
                ),
                (-outer_half_width, lower_arc_z),
            )

            # Mirrored left rim and the exact lower profile cavity close the face.
            Line(
                (-outer_half_width, lower_arc_z),
                (-outer_half_width, mouth_z - rim_r),
            )
            ThreePointArc(
                (-outer_half_width, mouth_z - rim_r),
                (
                    -outer_half_width + quarter_offset,
                    mouth_z - quarter_offset,
                ),
                (-outer_half_width + rim_r, mouth_z),
            )
            Line(
                (-outer_half_width + rim_r, mouth_z),
                (-inner_half_width - rim_r, mouth_z),
            )
            ThreePointArc(
                (-inner_half_width - rim_r, mouth_z),
                (
                    -inner_half_width - quarter_offset,
                    mouth_z - quarter_offset,
                ),
                (-inner_half_width, mouth_z - rim_r),
            )
            Line(
                (-inner_half_width, mouth_z - rim_r),
                (-inner_half_width, lower_arc_z),
            )
            ThreePointArc(
                (-inner_half_width, lower_arc_z),
                (0.0, lower_arc_z - inner_half_width),
                (inner_half_width, lower_arc_z),
            )
        make_face(boundary.edges())

    section = section_face.sketch
    bounds = section.bounding_box()
    if (
        len(section.faces()) != 1
        or not section.is_valid
        or not 0.5 <= section.area <= 1_100.0
        or abs(bounds.min.Z - z_offset) > 1e-5
        or abs(bounds.max.Z - mouth_z) > 1e-5
    ):
        raise RuntimeError(
            f"shell section x={station:g} invalid: faces={len(section.faces())}, "
            f"valid={section.is_valid}, area={section.area:.3f}, "
            f"z={bounds.min.Z:.6f}..{bounds.max.Z:.6f}"
        )
    return section


def _transition_shell() -> Part:
    """Loft one hollow profile-derived shell from connector root to saddle."""
    sections = [
        _shell_section(station, half_width, mouth_z)
        for station, half_width, mouth_z in c.ARM_SHELL_SECTIONS
    ]
    with BuildPart() as transition:
        loft(sections=sections)
    return _guard_solid(
        transition.part,
        "Stella arm transition shell",
        (40_000.0, 50_000.0),
        (-1e-5, 1e-5),
        (38.0, 40.0),
    )


def _root_blend() -> Part:
    """Continue the U-shell through the shoulder, starting inside the root."""
    sections = [
        _shell_section(station, half_width, mouth_z, scale, z_offset)
        for station, half_width, mouth_z, scale, z_offset in (c.ARM_ROOT_BLEND_SECTIONS)
    ]
    with BuildPart() as blend:
        loft(sections=sections)
    return _guard_solid(
        blend.part,
        "Stella arm connector-root shell blend",
        (4_000.0, 6_000.0),
        (0.01, 0.03),
        (23.0, 24.0),
    )


def _profile_shell_root() -> Part:
    """Return the frozen connector interface already blended into the U-shell."""
    with BuildPart() as root_shell:
        add(_root())
        add(_root_blend())
        add(_transition_shell())
    return _guard_solid(
        root_shell.part,
        "Stella arm blended connector root",
        (52_000.0, 58_000.0),
        (-1e-5, 1e-5),
        (40.0, 42.0),
    )


def _saddle() -> Part:
    """Build the measured-profile trough, bearing bands and rounded mouth rims."""
    saddle_start = c.ARM_SADDLE_START - c.SADDLE_JOIN_OVERLAP
    saddle_depth = c.SADDLE_LENGTH + c.SADDLE_JOIN_OVERLAP
    trough_section = _shell_section(
        saddle_start,
        c.SADDLE_OUTER_HALF_W,
        c.SADDLE_MOUTH_Z,
    )
    with BuildPart() as saddle:
        extrude(to_extrude=trough_section, amount=saddle_depth)

        relief_length = c.SADDLE_LENGTH - 2 * c.SADDLE_BAND_LENGTH
        if relief_length > 0:
            with BuildSketch(
                Plane.YZ.offset(c.ARM_SADDLE_START + c.SADDLE_BAND_LENGTH)
            ):
                with Locations((0.0, c.SADDLE_AXIS_Z)):
                    SlotOverall(
                        c.profile.HEIGHT + c.PROFILE_CLEAR + 2 * c.SADDLE_RELIEF,
                        c.profile.WIDTH + c.PROFILE_CLEAR + 2 * c.SADDLE_RELIEF,
                        rotation=90,
                    )
            extrude(amount=relief_length, mode=Mode.SUBTRACT)

        # Boolean axial lead-in at the exposed profile-entry end.
        with BuildSketch(
            Plane.YZ.offset(
                c.ARM_SADDLE_START + c.SADDLE_LENGTH - c.SADDLE_EDGE_CHAMFER
            )
        ):
            with Locations((0.0, c.SADDLE_AXIS_Z)):
                SlotOverall(
                    c.profile.HEIGHT + c.PROFILE_CLEAR,
                    c.profile.WIDTH + c.PROFILE_CLEAR,
                    rotation=90,
                )
        with BuildSketch(Plane.YZ.offset(c.ARM_SADDLE_START + c.SADDLE_LENGTH)):
            with Locations((0.0, c.SADDLE_AXIS_Z)):
                SlotOverall(
                    c.profile.HEIGHT + c.PROFILE_CLEAR + 2 * c.SADDLE_EDGE_CHAMFER,
                    c.profile.WIDTH + c.PROFILE_CLEAR + 2 * c.SADDLE_EDGE_CHAMFER,
                    rotation=90,
                )
        loft(ruled=True, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(c.KEEPER_LAND_BASE_Z)):
            with Locations(
                (c.KEEPER_STATION, -c.KEEPER_INSERT_Y),
                (c.KEEPER_STATION, c.KEEPER_INSERT_Y),
            ):
                RectangleRounded(
                    c.KEEPER_LAND_LENGTH,
                    c.KEEPER_LAND_PAD_WIDTH,
                    c.KEEPER_LAND_RADIUS,
                )
        extrude(amount=c.KEEPER_LAND_HEIGHT)
        with Locations(
            (
                c.KEEPER_STATION,
                -c.KEEPER_INSERT_Y,
                c.KEEPER_LAND_BASE_Z + c.KEEPER_LAND_HEIGHT,
            ),
            (
                c.KEEPER_STATION,
                c.KEEPER_INSERT_Y,
                c.KEEPER_LAND_BASE_Z + c.KEEPER_LAND_HEIGHT,
            ),
        ):
            Cylinder(
                c.KEEPER_INSERT_PILOT_D / 2,
                c.KEEPER_INSERT_DEPTH,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
    return _guard_solid(
        saddle.part,
        "Stella arm saddle",
        (8_000.0, 12_000.0),
        (-1e-5, 1e-5),
        (20.7, 20.9),
    )


def seated(part: Part | None = None, angle: float = 90.0) -> Part:
    """Place a print-pose arm into one accepted core branch for review."""
    if part is None:
        part = create()
    source = _plane_at(
        (c.ARM_ROOT_FACE_X, 0.0, c.ARM_ROOT_FACE_Z),
        c.ARM_CORE_NORMAL,
    )
    theta = radians(angle)
    target = Plane(
        origin=(c.SEAT_R * cos(theta), c.SEAT_R * sin(theta), c.CORE_H),
        x_dir=(sin(theta), -cos(theta), 0.0),
        z_dir=(0.0, 0.0, -1.0),
    )
    local = source.to_local_coords(part)
    return as_part(target.from_local_coords(local))


def create() -> Part:
    """Return one continuous profile-shell arm in its mouth-up ABS print pose."""
    joined = _profile_shell_root()

    with BuildPart() as arm:
        add(joined)
        add(_saddle())
        for tool in _final_root_access_tools():
            add(tool, mode=Mode.SUBTRACT)
    part = _guard_solid(
        arm.part,
        "Stella complete profile-shell arm",
        (50_000.0, 80_000.0),
        (-1e-5, 1e-5),
        (40.0, 42.0),
    )
    part.label = "Stella continuous profile-shell arm — keeper deferred"
    part.color = Color(0.24, 0.27, 0.31)
    return part


__all__ = ["create", "seated"]
