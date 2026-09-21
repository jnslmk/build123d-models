"""Functional unshifted Stella core, web-down in ABS; geometry acceptance pending."""

from math import cos, radians, sin, sqrt

from build123d import (
    Align,
    Axis,
    Bezier,
    BuildLine,
    BuildPart,
    BuildSketch,
    Color,
    Cylinder,
    Kind,
    Line,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    Sketch,
    ThreePointArc,
    add,
    loft,
    make_face,
    offset,
    revolve,
)

from models.lib.edges import as_part

from . import config as c

PARAMS = []
IS_ASSEMBLY = False


def _xy(radial: float, tangent: float, angle: float) -> tuple[float, float]:
    theta = radians(angle)
    return (
        radial * cos(theta) - tangent * sin(theta),
        radial * sin(theta) + tangent * cos(theta),
    )


def _profile(tip_radius: float, root_handle: float, inset: float = 0.0) -> Sketch:
    """Round seat hosts joined by tangent cubics, not pointed blank-body tips."""
    with BuildSketch() as profile:
        with BuildLine() as boundary:
            for angle in c.BRANCH_ANGLES:
                ThreePointArc(
                    _xy(c.TIP_CENTRE_R, -tip_radius, angle),
                    _xy(c.TIP_CENTRE_R + tip_radius, 0, angle),
                    _xy(c.TIP_CENTRE_R, tip_radius, angle),
                )
                Bezier(
                    _xy(c.TIP_CENTRE_R, tip_radius, angle),
                    _xy(root_handle, tip_radius, angle),
                    _xy(root_handle, -tip_radius, angle + 120),
                    _xy(c.TIP_CENTRE_R, -tip_radius, angle + 120),
                )
        make_face(boundary.edges())
        if inset:
            offset(amount=-inset, kind=Kind.INTERSECTION, mode=Mode.REPLACE)
    if len(profile.sketch.faces()) != 1 or not profile.sketch.is_valid:
        raise RuntimeError("Stella outline must remain one valid face")
    return profile.sketch


def _body() -> Part:
    """One smooth organic outline through the complete structural height."""
    outline = _profile(c.OUTLINE_TIP_RADIUS, c.OUTLINE_ROOT_HANDLE)
    inset = _profile(
        c.OUTLINE_TIP_RADIUS,
        c.OUTLINE_ROOT_HANDLE,
        c.EDGE_CHAMFER,
    )
    with BuildPart() as body:
        for z, sketch in (
            (0.0, inset),
            (c.EDGE_CHAMFER, outline),
            (c.CORE_H - c.EDGE_CHAMFER, outline),
            (c.CORE_H, inset),
        ):
            with BuildSketch(Plane.XY.offset(z)):
                add(sketch)
        loft(ruled=True)
    return body.part


def _seat_tool() -> Part:
    """Matching flat pocket and 45-degree entry; no bevel on bearing floor."""
    with BuildPart() as tool:
        for z, expansion in (
            (c.SEAT_Z, 0.0),
            (c.CORE_H - c.SEAT_LEAD, 0.0),
            (c.CORE_H, c.SEAT_LEAD),
            (c.CORE_H + 1, c.SEAT_LEAD),
        ):
            with BuildSketch(Plane.XY.offset(z)):
                RectangleRounded(
                    c.SEAT_LENGTH + 2 * expansion,
                    c.SEAT_WIDTH + 2 * expansion,
                    c.SEAT_RADIUS + expansion,
                )
        loft(ruled=True)
    return tool.part


def _suspension_bore_tool() -> Part:
    """Through bore with explicit R2 toroidal contact at both cord mouths."""
    bore_r = c.SUSPENSION_HOLE_D / 2
    contact_r = c.SUSPENSION_CONTACT_R
    quadrant = contact_r / sqrt(2)
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ):
            with BuildLine() as boundary:
                Line((0, -1), (bore_r + contact_r, -1))
                Line((bore_r + contact_r, -1), (bore_r + contact_r, 0))
                ThreePointArc(
                    (bore_r + contact_r, 0),
                    (
                        bore_r + contact_r - quadrant,
                        contact_r - quadrant,
                    ),
                    (bore_r, contact_r),
                )
                Line((bore_r, contact_r), (bore_r, c.CORE_H - contact_r))
                ThreePointArc(
                    (bore_r, c.CORE_H - contact_r),
                    (
                        bore_r + contact_r - quadrant,
                        c.CORE_H - contact_r + quadrant,
                    ),
                    (bore_r + contact_r, c.CORE_H),
                )
                Line(
                    (bore_r + contact_r, c.CORE_H),
                    (bore_r + contact_r, c.CORE_H + 1),
                )
                Line((bore_r + contact_r, c.CORE_H + 1), (0, c.CORE_H + 1))
                Line((0, c.CORE_H + 1), (0, -1))
            make_face(boundary.edges())
        revolve(axis=Axis.Z)
    return tool.part


def create() -> Part:
    """One core only: keyed seats, blind insert pilots and two cord holes."""
    body = _body()
    seat_tool = _seat_tool()
    suspension_bore = _suspension_bore_tool()
    with BuildPart() as core:
        add(body)
        for x in c.SUSPENSION_HOLE_CENTRES:
            add(
                as_part(Location((x, 0, 0)) * suspension_bore),
                mode=Mode.SUBTRACT,
            )

        for angle in c.BRANCH_ANGLES:
            x, y = _xy(c.SEAT_R, 0, angle)
            add(
                as_part(Location((x, y, 0), (0, 0, angle)) * seat_tool),
                mode=Mode.SUBTRACT,
            )
            for radial in c.INSERT_RADII:
                x, y = _xy(radial, 0, angle)
                with Locations((x, y, c.SEAT_Z - c.INSERT_DEPTH)):
                    Cylinder(
                        c.INSERT_PILOT_D / 2,
                        c.INSERT_DEPTH,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )

    part = core.part
    if len(part.solids()) != 1 or not part.is_valid:
        raise RuntimeError("Stella core must be one valid connected solid")
    part.label = "Stella functional organic-Y core — review candidate"
    part.color = Color(0.24, 0.43, 0.62)
    return part
