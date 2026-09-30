"""Physical gate for the matching 36-socket TPU cartridge, in print pose.

``check_sockets(report, part)`` accepts altered solids for the filled-socket and
misregistration mutation proofs. Dimensions come from the accepted rectangular
layout and the unchanged BITS grip, mouth, key and retention interfaces.
"""

from itertools import combinations
from math import cos, pi, sin, sqrt

from build123d import (
    Edge,
    Face,
    GeomType,
    Mode,
    Part,
    Plane,
    Pos,
    Rot,
    Shape,
    ShapeList,
    section,
)

from models.drill_storage.hex import config as h
from models.drill_storage.hex.insert import key_rib
from models.lib.checks import Report, adjacent_faces, is_flush_seam, sharp_convex_edges
from models.lib.edges import as_part
from models.lib.fits import MIN_WALL

from . import config as c
from .base import create_blank
from .insert import create

PROBE = 0.025
GEOMETRY_TOL = 1e-5
FLATS = tuple((cos((2 * k + 1) * pi / 6), sin((2 * k + 1) * pi / 6)) for k in range(6))


def _socket_radius(z: float) -> float:
    """Expected boundary, including both independent hex lead-ins."""
    land = (h.HEX_AF + h.HEX_LAND_FIT) / sqrt(3)
    relief = (h.HEX_AF + h.RELIEF_FIT) / sqrt(3)
    if z < h.BORE_FOOT_RELIEF:
        return land + h.BORE_FOOT_RELIEF - z
    if z <= h.LAND_H:
        return land
    if z < h.LAND_H + h.LAND_LEAD_IN:
        return land + (relief - land) * (z - h.LAND_H) / h.LAND_LEAD_IN
    return relief + max(0.0, z - (h.CART_H - h.BITS_CART_MOUTH_CH))


def _check_section(
    report: Report, part: Part, z: float, name: str, gap_floor: float, wall_floor: float
) -> None:
    """Measure actual hole contours, not conservative circumscribed circles."""
    cut = section(part, section_by=Plane.XY.offset(z), mode=Mode.PRIVATE)
    faces = [
        shape for shape in Shape.get_shape_list(cut, "Face") if isinstance(shape, Face)
    ]
    holes = [wire for face in faces for wire in face.inner_wires()]
    report.check(
        len(faces) == 1 and len(holes) == 36,
        f"{name}: exactly 36 separate socket openings in one connected section",
        f"z={z:.4f}; {len(faces)} material faces, {len(holes)} holes",
    )
    if len(faces) != 1 or len(holes) != 36:
        return
    gap = min(a.distance_to(b) for a, b in combinations(holes, 2))
    wall = min(wire.distance_to(faces[0].outer_wire()) for wire in holes)
    report.check(
        gap >= gap_floor - 1e-3,
        f"{name}: actual hex neighbours retain their BITS material floor",
        f"{gap:.4f} mm; require {gap_floor:.4f} mm",
    )
    report.check(
        wall >= wall_floor - 1e-3,
        f"{name}: actual hex contours retain their outer-wall budget",
        f"{wall:.4f} mm; require {wall_floor:.4f} mm",
    )


def check_sockets(report: Report, part: Part) -> None:
    """Gate all 36 physical through sockets and their complete axial profiles."""
    report.section("36 TPU socket profiles and actual material lands")
    heights = (
        ("foot relief", h.BORE_FOOT_RELIEF / 2),
        ("short grip land", h.BORE_FOOT_RELIEF + h.EFFECTIVE_LAND_H / 2),
        ("land lead-in", h.LAND_H + h.LAND_LEAD_IN / 2),
        (
            "upper relief",
            (h.LAND_H + h.LAND_LEAD_IN + h.CART_H - h.BITS_CART_MOUTH_CH) / 2,
        ),
        ("hex mouth", h.CART_H - h.BITS_CART_MOUTH_CH / 2),
    )
    for index, (label, x, y) in enumerate(c.SOCKETS, 1):
        name = f"socket {index} ({label}, x={x:.3f}, y={y:.3f})"
        report.check(
            all(
                not report.solid_at(part, x, y, z)
                for z in (PROBE, *(z for _, z in heights), h.CART_H - PROBE)
            ),
            f"{name}: open through the print bed and top",
        )
        for stage, z in heights:
            apothem = _socket_radius(z) * sqrt(3) / 2
            report.check(
                all(
                    not report.solid_at(
                        part, x + (apothem - PROBE) * dx, y + (apothem - PROBE) * dy, z
                    )
                    and report.solid_at(
                        part, x + (apothem + PROBE) * dx, y + (apothem + PROBE) * dy, z
                    )
                    for dx, dy in FLATS
                ),
                f"{name}: six flats at {stage}",
                f"z={z:.3f}, across flats={2 * apothem:.4f} mm",
            )
    # Inspect both ends of the short land as well as its midpoint. A full-height
    # grip or a prematurely relieved land must not pass the midpoint samples.
    land_af = h.HEX_AF + h.HEX_LAND_FIT
    report.check(
        all(
            not report.solid_at(
                part, x + (land_af / 2 - PROBE) * dx, y + (land_af / 2 - PROBE) * dy, z
            )
            and report.solid_at(
                part, x + (land_af / 2 + PROBE) * dx, y + (land_af / 2 + PROBE) * dy, z
            )
            for _, x, y in c.SOCKETS
            for z in (h.BORE_FOOT_RELIEF + PROBE, h.LAND_H - PROBE)
            for dx, dy in FLATS
        ),
        "every short land retains the full inherited effective grip height",
        f"z={h.BORE_FOOT_RELIEF:.3f}..{h.LAND_H:.3f}, height={h.EFFECTIVE_LAND_H:.3f}",
    )
    _check_section(report, part, heights[1][1], "grip land", MIN_WALL, h.CART_WALL)
    _check_section(
        report,
        part,
        heights[3][1],
        "relief",
        h.BITS_RELIEF_GAP_FLOOR,
        h.CART_WALL + h.BITS_CART_MOUTH_CH,
    )
    # The inherited outer .4 mm bevel also spends wall at the actual top edge.
    # Unlike a centre-to-wall budget, this contour distance charges BOTH bevels.
    _check_section(
        report, part, h.CART_H - 1e-4, "top rim", 0.1, h.CART_WALL - h.SHELL_TOP_CHAMFER
    )


def _check_envelope(report: Report, part: Part) -> None:
    report.section("Print pose and keyed rectangular envelope")
    report.check(
        part.is_valid and len(part.solids()) == 1, "insert is one valid printable solid"
    )
    bounds = part.bounding_box()
    expected = (
        -c.CART_X / 2 - h.CART_BEAD,
        c.CART_X / 2 + max(h.KEY_D, h.CART_BEAD),
        -c.CART_Y / 2 - h.CART_BEAD,
        c.CART_Y / 2 + h.CART_BEAD,
        0.0,
        h.CART_H,
    )
    actual = (
        bounds.min.X,
        bounds.max.X,
        bounds.min.Y,
        bounds.max.Y,
        bounds.min.Z,
        bounds.max.Z,
    )
    report.check(
        all(abs(a - b) < GEOMETRY_TOL for a, b in zip(actual, expected)),
        "true print-pose bounds include the +X key and four-sided retention bead",
        f"actual {actual}; expected {expected}",
    )
    report.check(
        all(
            report.solid_at(part, sign * (c.CART_X / 2 - PROBE), 0, 0.8)
            for sign in (-1, 1)
        )
        and all(
            report.solid_at(part, 0, sign * (c.CART_Y / 2 - PROBE), 0.8)
            for sign in (-1, 1)
        ),
        "35.68 × 77.68 mm rectangular body remains behind its edge reliefs",
    )


def _overlap_volume(first: Part, second: Part) -> float:
    """OCC may return no shape, one shape, or disconnected common shapes."""
    common = first.intersect(second)
    if common is None:
        return 0.0
    return (
        sum(shape.volume for shape in common)
        if isinstance(common, ShapeList)
        else common.volume
    )


def _check_registration(report: Report, part: Part, base: Part) -> None:
    report.section("Accepted base registration and retention")
    placed = as_part(Pos(0, 0, c.CAVITY_FLOOR_Z) * part)
    overlap = _overlap_volume(placed, base)
    report.check(
        overlap < 1e-4,
        "seated cartridge has no unwanted rigid overlap",
        f"base.create_blank() overlap {overlap:.6f} mm³",
    )
    report.check(
        all(
            not report.solid_at(base, x, y, c.CAVITY_FLOOR_Z - PROBE)
            and not report.solid_at(placed, x, y, c.CAVITY_FLOOR_Z + PROBE)
            for _, x, y in c.SOCKETS
        ),
        "all 36 through sockets register with the accepted rigid guides",
        f"assembly translation z={c.CAVITY_FLOOR_Z:.3f}; top z={placed.bounding_box().max.Z:.3f}",
    )
    key_x = c.CART_X / 2 + h.KEY_D / 2
    report.check(
        report.solid_at(part, key_x, 0, 0.8)
        and not report.solid_at(part, -key_x, 0, 0.8)
        and not report.solid_at(base, key_x, 0, c.CAVITY_FLOOR_Z + 0.8),
        "actual +X/y=0 key enters the unchanged receiver, not the opposite wall",
    )
    wrong_way = as_part(Pos(0, 0, c.CAVITY_FLOOR_Z) * Rot(0, 0, 180) * part)
    wrong_overlap = _overlap_volume(wrong_way, base)
    report.check(
        wrong_overlap > 0.01,
        "key physically rejects reversed assembly registration",
        f"180° rigid overlap {wrong_overlap:.4f} mm³",
    )
    z0 = h.CART_BELOW_BEAD
    stations = (("x", -1), ("y", -1), ("y", 1), ("x", 1))
    # Avoid the key at +X: it intentionally projects farther than the bead.
    for axis, sign in stations:
        along = h.KEY_W + h.KEY_FILLET if axis == "x" and sign == 1 else 0.0
        half = (c.CART_X if axis == "x" else c.CART_Y) / 2
        for z, reach in (
            (
                (z0 - h.BEAD_LEAD_IN + z0 - h.BEAD_TIP_FLAT / 2) / 2,
                h.CART_BEAD / 2,
            ),
            (z0, h.CART_BEAD),
            (
                (z0 + h.BEAD_TIP_FLAT / 2 + z0 + h.BEAD_BACK) / 2,
                h.CART_BEAD / 2,
            ),
        ):

            def point(offset):
                radial = sign * (half + reach + offset)
                return (radial, along, z) if axis == "x" else (along, radial, z)

            inside = point(-PROBE)
            outside = point(PROBE)
            report.check(
                report.solid_at(part, *inside)
                and not report.solid_at(part, *outside)
                and not report.solid_at(
                    base, inside[0], inside[1], z + c.CAVITY_FLOOR_Z
                ),
                f"{sign:+}{axis}: actual insertion ramp, bead tip and retention ramp fit receiver at z={z:.3f}",
                f"outward reach {reach:.3f} mm",
            )
    # A bead that merely clears the cavity is not retention. The seated solid
    # must clear, while withdrawal past the receiver roof costs TPU deflection.
    lifted = as_part(
        Pos(0, 0, c.CAVITY_FLOOR_Z + h.GROOVE_ROOF + h.BEAD_TIP_FLAT / 2) * part
    )
    catch = _overlap_volume(lifted, base)
    report.check(
        catch > 0.01,
        "outward bead mechanically catches the rigid receiver on withdrawal",
        f"withdrawal overlap {catch:.4f} mm³; nominal engagement {h.CART_BEAD - h.CART_SLIP / 2:.3f} mm",
    )


def _edge_allow(part: Part) -> tuple:
    """Exact functional curves/faces only; neither a Z band nor a key box."""
    reference_key_edges = tuple(
        shape
        for shape in Shape.get_shape_list(key_rib(), "Edge")
        if isinstance(shape, Edge)
    )

    def socket_corner(edge):
        points = [edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)]
        if any(p.Z < -GEOMETRY_TOL or p.Z > h.CART_H + GEOMETRY_TOL for p in points):
            return False
        for _, x, y in c.SOCKETS:
            for k in range(6):
                dx, dy = cos(k * pi / 3), sin(k * pi / 3)
                if all(
                    abs(p.X - x - _socket_radius(p.Z) * dx) < GEOMETRY_TOL
                    and abs(p.Y - y - _socket_radius(p.Z) * dy) < GEOMETRY_TOL
                    for p in points
                ):
                    return True
        return False

    def ramp_datum(edge):
        b = edge.bounding_box()
        if not any(
            abs(b.min.Z - z) < GEOMETRY_TOL and abs(b.max.Z - z) < GEOMETRY_TOL
            for z in (
                h.CART_BELOW_BEAD - h.BEAD_LEAD_IN,
                h.CART_BELOW_BEAD + h.BEAD_BACK,
            )
        ):
            return False
        # If the buried .01 mm annular overlap leaves a horizontal datum face,
        # match that actual narrow face, not every edge at these heights.
        for face in adjacent_faces(part, edge):
            fb = face.bounding_box()
            if (
                face.geom_type == GeomType.PLANE
                and abs(face.normal_at().Z) > 0.999
                and abs(fb.min.Z - b.min.Z) < GEOMETRY_TOL
                and abs(fb.max.Z - b.max.Z) < GEOMETRY_TOL
                and face.area <= 0.02 * 2 * (c.CART_X + c.CART_Y)
            ):
                points = [edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)]
                if all(
                    abs(
                        sqrt(
                            max(abs(p.X) - (c.CART_X / 2 - h.CART_R), 0) ** 2
                            + max(abs(p.Y) - (c.CART_Y / 2 - h.CART_R), 0) ** 2
                        )
                        + min(
                            max(
                                abs(p.X) - (c.CART_X / 2 - h.CART_R),
                                abs(p.Y) - (c.CART_Y / 2 - h.CART_R),
                            ),
                            0,
                        )
                        - h.CART_R
                    )
                    <= 0.01 + GEOMETRY_TOL
                    for p in points
                ):
                    return True
        return False

    def reused_key(edge):
        points = [edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)]
        return any(
            all(reference.distance_to(p) < GEOMETRY_TOL for p in points)
            for reference in reference_key_edges
        )

    def key_flush(edge):
        # An actual tangent seam is not a corner; restrict it to the reused
        # rib's surfaces so unrelated unclassifiable edges cannot hide here.
        b = edge.bounding_box()
        return (
            b.min.X >= c.CART_X / 2 - GEOMETRY_TOL
            and b.max.X <= c.CART_X / 2 + h.KEY_D + GEOMETRY_TOL
            and max(abs(b.min.Y), abs(b.max.Y)) <= h.KEY_W / 2 + GEOMETRY_TOL
            and is_flush_seam(part, edge)
        )

    return (
        (
            socket_corner,
            "exact six vertex curves of the functional hex socket profile; flats and mouth rims remain audited",
        ),
        (
            ramp_datum,
            "actual narrow horizontal retention-ramp datum faces; ramp faces remain audited",
        ),
        (
            reused_key,
            "sharp edges belonging to the unchanged public hex.insert.key_rib geometry",
        ),
        (
            key_flush,
            "only measured 180° tangent seams where the reused key joins the body/bead",
        ),
    )


def run() -> Report:
    """Check this insert anchor against the accepted blank base, not a scene."""
    part = create()
    report = Report()
    _check_envelope(report, part)
    check_sockets(report, part)
    _check_registration(report, part, create_blank())
    report.section("Sharp and unclassifiable convex edge audit")
    allowances = _edge_allow(part)
    survey = sharp_convex_edges(part, allow=allowances)
    for _, reason in allowances:
        report.lines.append(f"  allowed: {reason}")
    for bucket, edges in (
        ("sharp", survey.sharp),
        ("unclassifiable", survey.unclassifiable),
    ):
        detail = "; ".join(
            f"{edge.center()} length={edge.length:.3f}" for edge in edges
        )
        report.check(
            not edges,
            f"insert has no unexplained {bucket} convex edges",
            f"{len(edges)}: {detail}" if edges else "0",
        )
    return report
