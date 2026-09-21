"""Complete Stella profile arm in mouth-up ABS print pose."""

from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Rectangle,
    RectangleRounded,
    SlotOverall,
    add,
    extrude,
    loft,
)

from models.lib.edges import (
    as_part,
    bottom_chamfer_tool,
    chamfer_edge,
    top_chamfer_tool,
)

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
    return root.part


def _final_root_access_tools() -> tuple[Part, ...]:
    """Clear screw shanks and straight driver approaches after every web is fused."""
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


def _core_side_tool() -> Part:
    """Half-space removing support webs from the accepted core/key side."""
    bearing = _plane_at(
        (c.ARM_ROOT_FACE_X, 0.0, c.ARM_ROOT_FACE_Z),
        c.ARM_CORE_NORMAL,
    )
    with BuildPart() as tool:
        with BuildSketch(bearing):
            Rectangle(300.0, 300.0)
        extrude(amount=100.0)
    return tool.part


def _rib() -> Part:
    """Printable triangular web carrying the sloped root into the beam."""
    with BuildPart() as rib:
        with BuildSketch(Plane.XZ):
            Polygon(
                (c.ARM_BEAM_START - 4.0, 0.0),
                (32.0, 0.0),
                (27.0, 31.0),
                (18.0, 12.0),
                align=(Align.MIN, Align.MIN),
            )
        extrude(amount=c.ARM_RIB_WIDTH / 2, both=True)
        chamfer_edge(
            rib,
            [edge for edge in rib.edges() if edge not in rib.edges().filter_by(Axis.Z)],
            c.SADDLE_EDGE_CHAMFER,
        )
    return rib.part


def _beam() -> Part:
    """Continuous low beam from the root webs to the saddle floor."""
    length = c.ARM_SADDLE_START - c.ARM_BEAM_START
    with BuildPart() as beam:
        with BuildSketch():
            with Locations((c.ARM_BEAM_START, 0.0)):
                RectangleRounded(
                    length,
                    c.ARM_BEAM_WIDTH,
                    3.0,
                    align=(Align.MIN, Align.CENTER),
                )
        extrude(amount=c.ARM_BEAM_HEIGHT)
        add(
            bottom_chamfer_tool(
                length,
                c.ARM_BEAM_WIDTH,
                3.0,
                0.0,
                c.SADDLE_EDGE_CHAMFER,
            ).moved(Plane(origin=(c.ARM_BEAM_START + length / 2, 0.0, 0.0)).location),
            mode=Mode.SUBTRACT,
        )
        add(
            top_chamfer_tool(
                length,
                c.ARM_BEAM_WIDTH,
                3.0,
                c.ARM_BEAM_HEIGHT,
                c.SADDLE_EDGE_CHAMFER,
            ).moved(Plane(origin=(c.ARM_BEAM_START + length / 2, 0.0, 0.0)).location),
            mode=Mode.SUBTRACT,
        )
    return beam.part


def _rails() -> Part:
    """Twin rounded webs taper smoothly into the profile-following saddle."""
    with BuildPart() as rails:
        for y in (-c.ARM_RAIL_Y, c.ARM_RAIL_Y):
            for station, height in c.ARM_RAIL_SECTIONS:
                with BuildSketch(Plane.YZ.offset(station)):
                    with Locations((y, 0.0)):
                        RectangleRounded(
                            c.ARM_RAIL_WIDTH,
                            height,
                            min(c.ARM_RAIL_WIDTH / 2 - 0.1, height / 2 - 0.1),
                            align=(Align.CENTER, Align.MIN),
                        )
            loft()
    return rails.part


def _saddle() -> Part:
    """Open trough supporting aluminium below the rim, never the diffuser."""
    with BuildPart() as saddle:
        outer_h = c.profile.HEIGHT + c.PROFILE_CLEAR + 2 * c.SADDLE_WALL
        outer_w = c.profile.WIDTH + c.PROFILE_CLEAR + 2 * c.SADDLE_WALL
        with BuildSketch(Plane.YZ.offset(c.ARM_SADDLE_START)):
            with Locations((0.0, c.SADDLE_AXIS_Z)):
                SlotOverall(outer_h, outer_w, rotation=90)
            with Locations((0.0, c.SADDLE_MOUTH_Z)):
                Rectangle(
                    100.0, 100.0, align=(Align.CENTER, Align.MIN), mode=Mode.SUBTRACT
                )
            with Locations((0.0, 0.0)):
                Rectangle(
                    100.0, 100.0, align=(Align.CENTER, Align.MAX), mode=Mode.SUBTRACT
                )
        extrude(amount=c.SADDLE_LENGTH)
        with BuildSketch(Plane.YZ.offset(c.ARM_SADDLE_START)):
            with Locations((0.0, c.SADDLE_AXIS_Z)):
                SlotOverall(
                    c.profile.HEIGHT + c.PROFILE_CLEAR,
                    c.profile.WIDTH + c.PROFILE_CLEAR,
                    rotation=90,
                )
        extrude(amount=c.SADDLE_LENGTH, mode=Mode.SUBTRACT)

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
        with BuildPart() as mouth:
            with BuildSketch(Plane.YZ.offset(c.ARM_SADDLE_START)):
                bore_half = (c.profile.WIDTH + c.PROFILE_CLEAR) / 2
                for sign in (-1.0, 1.0):
                    Polygon(
                        (sign * bore_half, c.SADDLE_MOUTH_Z),
                        (sign * (bore_half + c.SADDLE_EDGE_CHAMFER), c.SADDLE_MOUTH_Z),
                        (sign * bore_half, c.SADDLE_MOUTH_Z - c.SADDLE_EDGE_CHAMFER),
                    )
            extrude(amount=c.SADDLE_LENGTH)
        add(mouth.part, mode=Mode.SUBTRACT)

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
    return saddle.part


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
    """Return one complete arm in its support-minimizing mouth-up print pose."""
    rib = _rib()
    with BuildPart() as supports:
        add(_beam())
        add(_rails())
        for y in (-c.ARM_RAIL_Y, c.ARM_RAIL_Y):
            add(as_part(Plane(origin=(0.0, y, 0.0)).location * rib))
        add(_saddle())
        add(_core_side_tool(), mode=Mode.SUBTRACT)
        for tool in _final_root_access_tools():
            add(tool, mode=Mode.SUBTRACT)

    with BuildPart() as arm:
        add(_root())
        add(supports.part)
    part = arm.part
    if len(part.solids()) != 1 or not part.is_valid:
        raise RuntimeError("Stella arm must be one valid connected solid")
    part.label = "Stella complete profile arm — keeper deferred"
    part.color = Color(0.24, 0.27, 0.31)
    return part


__all__ = ["create", "seated"]
