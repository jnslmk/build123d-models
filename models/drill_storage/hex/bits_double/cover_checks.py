"""Physical gate for the matching pillow-down PETG cover, without a scene.

``check_shell(report, usecover)`` and ``check_fit(report, usecover, base,
insert)`` accept altered solids for cap-missing, bad-pose and bead-wrong-reach
negative proofs. Fit poses are local to this gate; the accepted anchors are not
changed. The inherited short-span snap estimate is nominal, not a local-strain
bound, force prediction or proof of a particular printed spool's fatigue life.
"""

from math import hypot, sqrt

import fontfix  # noqa: F401 -- the model's registered sans font
from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    CenterOf,
    Edge,
    Face,
    FontStyle,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rot,
    Shape,
    ShapeList,
    Text,
    Vector,
    add,
    extrude,
    section,
)

from models.drill_storage.box import (
    CAP_FILLET,
    CAP_H,
    CORNER_R,
    COVER_SEAT_CH,
    COVER_WALL,
    INNER_R,
    MOUTH_CH,
    SNAP_BACK,
    SNAP_GROOVE_ROOF,
    SNAP_LEAD_IN,
    SNAP_TIP_FLAT,
    SNAP_Z,
    TOP_FILLET,
)
from models.drill_storage.hex import config as h
from models.drill_storage.hex.cover import label_fit
from models.lib.checks import Report, sharp_convex_edges
from models.lib.edges import as_part

from . import config as c

PROBE = 0.025
GEOMETRY_TOL = 1e-5


def _overlap_volume(first: Part, second: Part) -> float:
    """OCC common may be absent, a shape, or a disconnected ShapeList."""
    common = first.intersect(second)
    if common is None:
        return 0.0
    if isinstance(common, ShapeList):
        return sum(shape.volume for shape in common)
    return common.volume


def _contour_distance(
    point: Vector, width: float, length: float, radius: float
) -> float:
    """Signed distance from the exact rounded-rectangle boundary."""
    dx = abs(point.X) - (width / 2 - radius)
    dy = abs(point.Y) - (length / 2 - radius)
    return hypot(max(dx, 0), max(dy, 0)) + min(max(dx, dy), 0) - radius


def _stations(width: float, length: float, radius: float):
    """Four flat normals and four corner bisectors, all on the same contour."""
    yield width / 2, 0.0, 1.0, 0.0
    yield -width / 2, 0.0, -1.0, 0.0
    yield 0.0, length / 2, 0.0, 1.0
    yield 0.0, -length / 2, 0.0, -1.0
    diagonal = 1 / sqrt(2)
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        yield (
            sx * (width / 2 - radius + radius * diagonal),
            sy * (length / 2 - radius + radius * diagonal),
            sx * diagonal,
            sy * diagonal,
        )


def _boundary_samples(
    report: Report, part: Part, z: float, inset: float, probe: float = PROBE
) -> bool:
    """Both sides of the cavity/bead boundary, including every rounded corner."""
    return all(
        report.solid_at(part, x + probe * nx, y + probe * ny, z)
        and not report.solid_at(part, x - probe * nx, y - probe * ny, z)
        for x, y, nx, ny in _stations(
            c.COVER_INNER_X - 2 * inset,
            c.COVER_INNER_Y - 2 * inset,
            INNER_R - inset,
        )
    )


def _section_faces(part: Part, z: float) -> list[Face]:
    cut = section(part, section_by=Plane.XY.offset(z), mode=Mode.PRIVATE)
    return [
        shape for shape in Shape.get_shape_list(cut, "Face") if isinstance(shape, Face)
    ]


def _transition(report: Report, part: Part, point, low: float, high: float) -> float:
    """Locate one bracketed material transition, without assuming its position."""
    initial = report.solid_at(part, *point(low))
    if initial == report.solid_at(part, *point(high)):
        return float("nan")
    for _ in range(24):
        middle = (low + high) / 2
        if report.solid_at(part, *point(middle)) == initial:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def check_shell(report: Report, usecover: Part) -> None:
    """Check the completed use-pose shell, including its actual cap and bead."""
    report.section("Use pose, uniform tube, cap and required fillets")
    bounds = usecover.bounding_box()
    actual = (
        bounds.min.X,
        bounds.max.X,
        bounds.min.Y,
        bounds.max.Y,
        bounds.min.Z,
        bounds.max.Z,
    )
    expected = (
        -c.COVER_X / 2,
        c.COVER_X / 2,
        -c.COVER_Y / 2,
        c.COVER_Y / 2,
        0.0,
        c.COVER_H,
    )
    report.check(
        usecover.is_valid and len(usecover.solids()) == 1,
        "cover is one valid completed solid",
    )
    report.check(
        all(abs(a - b) < GEOMETRY_TOL for a, b in zip(actual, expected)),
        "true use-pose envelope has its open mouth at z=0 and cap above",
        f"actual {actual}; expected {expected}",
    )
    ceiling = c.COVER_H - CAP_H
    report.check(
        not report.solid_at(usecover, 0, 0, PROBE)
        and not report.solid_at(usecover, 0, 0, ceiling - PROBE)
        and report.solid_at(usecover, 0, 0, ceiling + PROBE)
        and report.solid_at(usecover, 0, 0, c.COVER_H - PROBE)
        and not report.solid_at(usecover, 0, 0, c.COVER_H + PROBE),
        "open tube closes with an actual 1 mm central cap, not a blind block or missing cap",
    )
    cap_start = _transition(
        report, usecover, lambda z: (0, 0, z), ceiling - 0.5, ceiling + 0.5
    )
    report.check(
        abs(c.COVER_H - cap_start - CAP_H) < GEOMETRY_TOL,
        "measured central cap thickness is inherited CAP_H",
        f"{c.COVER_H - cap_start:.5f} mm",
    )
    # The first section is above both mouth lead-ins but below the snap/ink;
    # the second is above the ink but below either cap fillet.
    for z in (MOUTH_CH + 0.2, c.COVER_H - TOP_FILLET - 1):
        faces = _section_faces(usecover, z)
        holes = [wire for face in faces for wire in face.inner_wires()]
        thickness = (
            holes[0].distance_to(faces[0].outer_wire())
            if len(faces) == 1 and len(holes) == 1
            else float("nan")
        )
        report.check(
            len(faces) == 1
            and len(holes) == 1
            and abs(thickness - COVER_WALL) < GEOMETRY_TOL
            and _boundary_samples(report, usecover, z, 0),
            f"actual rounded tube at z={z:g} has one cavity and uniform .95 mm flat/corner wall",
            f"minimum contour wall {thickness:.5f} mm",
        )
    # Circle equations for both required blends; +/- probes distinguish a true
    # radius from a sharp cap, a skipped fillet or an arbitrary bevel.
    for drop in (0.5, 1.0):
        pillow_x = (
            c.COVER_X / 2 - TOP_FILLET + sqrt(TOP_FILLET**2 - (TOP_FILLET - drop) ** 2)
        )
        inner_inset = CAP_FILLET - sqrt(CAP_FILLET**2 - (CAP_FILLET - drop) ** 2)
        report.check(
            report.solid_at(usecover, pillow_x - PROBE, 0, c.COVER_H - drop)
            and not report.solid_at(usecover, pillow_x + PROBE, 0, c.COVER_H - drop),
            f"actual 2.5 mm pillow fillet at {drop:g} mm below cap top",
        )
        report.check(
            _boundary_samples(report, usecover, ceiling - drop, inner_inset),
            f"actual 1.5 mm concave cap-to-wall fillet on all flats/corners at {drop:g} mm below ceiling",
        )

    report.section("Rounded-rectangle lead-ins and actual flat seating rim")
    for z in (PROBE, MOUTH_CH / 2):
        inner_outset = MOUTH_CH - z
        report.check(
            _boundary_samples(report, usecover, z, -inner_outset),
            f"inner rounded-rectangle mouth lead-in at z={z:.3f}",
        )
    z = COVER_SEAT_CH / 2
    inset = COVER_SEAT_CH - z
    report.check(
        all(
            report.solid_at(usecover, x - PROBE * nx, y - PROBE * ny, z)
            and not report.solid_at(usecover, x + PROBE * nx, y + PROBE * ny, z)
            for x, y, nx, ny in _stations(
                c.COVER_X - 2 * inset, c.COVER_Y - 2 * inset, CORNER_R - inset
            )
        ),
        "outer .2 mm seating chamfer follows the whole rounded rectangle",
    )
    rim = COVER_WALL - MOUTH_CH - COVER_SEAT_CH
    report.check(
        abs(rim - 0.45) < GEOMETRY_TOL
        and all(
            report.solid_at(usecover, x, y, 0)
            for x, y, _, _ in _stations(
                c.COVER_X - 2 * (COVER_SEAT_CH + rim / 2),
                c.COVER_Y - 2 * (COVER_SEAT_CH + rim / 2),
                CORNER_R - COVER_SEAT_CH - rim / 2,
            )
        ),
        "actual mouth retains the .45 mm flat-on-flat seating land at all flats/corners",
        f"{rim:.3f} mm",
    )

    report.section(
        "Internal rectangular snap: original ramps, tip and zero-reach roots"
    )
    reach = h.cover_snap_protrusion("bits")
    stages = (
        ("insertion ramp", SNAP_Z - (SNAP_LEAD_IN + SNAP_TIP_FLAT / 2) / 2, reach / 2),
        ("tip flat", SNAP_Z, reach),
        ("retention ramp", SNAP_Z + (SNAP_BACK + SNAP_TIP_FLAT / 2) / 2, reach / 2),
        ("lower zero-reach root", SNAP_Z - SNAP_LEAD_IN, 0.0),
        ("upper zero-reach root", SNAP_Z + SNAP_BACK, 0.0),
    )
    for name, z, inset in stages:
        report.check(
            _boundary_samples(report, usecover, z, inset, probe=0.002),
            f"{name}: actual inner contour on four flats and four corners",
            f"z={z:.3f}; inward reach={inset:.3f} mm",
        )


def check_fit(report: Report, usecover: Part, base: Part, insert: Part) -> None:
    """Pose the three real solids only for clearance and withdrawal proof."""
    report.section("Accepted-anchor seated fit and mechanical retention")
    seated = as_part(Pos(0, 0, c.SEAT_Z) * usecover)
    cartridge = as_part(Pos(0, 0, c.CAVITY_FLOOR_Z) * insert)
    for name, other in (("base", base), ("TPU insert", cartridge)):
        overlap = _overlap_volume(seated, other)
        report.check(
            overlap < GEOMETRY_TOL,
            f"seated cover has zero unwanted overlap with the accepted {name}",
            f"{overlap:.8f} mm³",
        )
    lifted = as_part(
        Pos(0, 0, c.SEAT_Z + SNAP_GROOVE_ROOF + SNAP_TIP_FLAT / 2) * usecover
    )
    catch = _overlap_volume(lifted, base)
    report.check(
        catch > 0.01,
        "actual cover bead catches the collar on withdrawal, not merely a friction fit",
        f"withdrawal interference {catch:.5f} mm³",
    )
    engagements = []
    for axis, collar, inner in (
        ("X", c.COLLAR_X / 2, c.COVER_INNER_X / 2),
        ("Y", c.COLLAR_Y / 2, c.COVER_INNER_Y / 2),
    ):

        def point(value, z):
            return (value, 0, z) if axis == "X" else (0, value, z)

        tip = _transition(
            report,
            usecover,
            lambda value: point(value, SNAP_Z),
            inner - h.cover_snap_protrusion("bits") - 0.2,
            inner + 0.2,
        )
        collar_surface = _transition(
            report,
            base,
            lambda value: point(value, c.SEAT_Z + SNAP_Z + SNAP_GROOVE_ROOF + 0.5),
            collar - 0.2,
            collar + 0.2,
        )
        engagement = collar_surface - tip
        engagements.append(engagement)
        report.check(
            abs(engagement - 0.15) < GEOMETRY_TOL,
            f"measured {axis} snap engagement remains .15 mm after diametral slip",
            f"collar={collar_surface:.5f}; tip={tip:.5f}; engagement={engagement:.5f} mm",
        )
    strain = 2 * max(engagements) / c.COLLAR_X
    report.check(
        0 < strain < 0.01,
        "inherited nominal short-span snap sizing estimate is below repeated-use PETG 1%",
        f"2 × measured engagement / {c.COLLAR_X:g} = {strain:.3%}; not a local-strain bound, force prediction or physical-print claim",
    )

    report.section("Actual clearance above all 36 seated 25 mm short-bit tips")
    tip_z = c.GUIDE_FLOOR_Z + h.BITS_BIT_LEN
    for index, (label, x, y) in enumerate(c.SOCKETS, 1):
        ceiling = _transition(
            report,
            usecover,
            lambda z: (x, y, z),
            tip_z - c.SEAT_Z,
            c.COVER_H,
        )
        gap = ceiling + c.SEAT_Z - tip_z
        report.check(
            gap >= 1.0 - GEOMETRY_TOL,
            f"bit {index} {label}: true ceiling clears the world-z{tip_z:g} tip by at least 1 mm",
            f"x={x:.3f}; y={y:.3f}; actual vertical clearance {gap:.5f} mm",
        )
    faces = _section_faces(usecover, tip_z - c.SEAT_Z)
    holes = [wire for face in faces for wire in face.inner_wires()]
    # A circumscribed disk around an 8 mm AF hex is deliberately conservative:
    # it is a design envelope, not a manufacturer's claim about individual tips.
    tip_radius = 8.0 / sqrt(3)
    clearance = (
        min(
            holes[0].distance_to(Vector(x, y, tip_z - c.SEAT_Z)) - tip_radius
            for _, x, y in c.SOCKETS
        )
        if len(holes) == 1
        else float("nan")
    )
    report.check(
        clearance > 0,
        "all tips retain positive wall clearance inside a conservative 8 mm AF circumscribed envelope",
        f"minimum {clearance:.5f} mm at tip height; not manufacturer geometry",
    )


def _glyph_point(report: Report, tool: Part, glyph, y: float):
    center = glyph.center(CenterOf.MASS)
    if report.solid_at(tool, center.X, y, center.Z):
        return center.X, center.Z
    bounds = glyph.bounding_box()
    for ix in range(1, 20):
        for iz in range(1, 20):
            x = bounds.min.X + bounds.size.X * ix / 20
            z = bounds.min.Z + bounds.size.Z * iz / 20
            if report.solid_at(tool, x, y, z):
                return x, z
    return None


def _check_label(report: Report, usecover: Part, tool: Part) -> None:
    report.section("Full BITS engraving: true bold glyphs, depth, backing and no holes")
    bounds = tool.bounding_box()
    glyphs = list(tool.solids())
    wall = c.COVER_Y / 2
    report.check(
        tool.is_valid
        and abs(bounds.max.Y - wall) < GEOMETRY_TOL
        and abs(bounds.min.Y - (wall - h.LABEL_DEPTH)) < GEOMETRY_TOL
        and abs((bounds.min.X + bounds.max.X) / 2) < GEOMETRY_TOL
        and bounds.min.X > -c.COVER_X / 2 + CORNER_R
        and bounds.max.X < c.COVER_X / 2 - CORNER_R
        and bounds.min.Z > 1
        and bounds.max.Z < c.COVER_H - TOP_FILLET,
        "whole true glyph envelope lies across the flat short +Y wall at exact .5 mm depth",
        f"X={bounds.min.X:.3f}..{bounds.max.X:.3f}; Z={bounds.min.Z:.3f}..{bounds.max.Z:.3f}",
    )
    # Font size is inferred from true ink height, but the word, reading
    # direction, centering and wall plane are independent of the supplied tool.
    # Comparing a bag of glyph sizes would accept anagrams such as STIB.
    with BuildSketch() as unit_ink:
        Text("BITS", font_size=1, font_style=FontStyle.BOLD)
    size = bounds.size.Z / unit_ink.sketch.bounding_box().size.Y
    with BuildSketch() as reference_ink:
        Text("BITS", font_size=size, font_style=FontStyle.BOLD)
    center = reference_ink.sketch.bounding_box().center()
    _, label_z, _ = label_fit(c.COVER_H, "BITS")
    reference_plane = Plane(
        origin=(0, wall, label_z), x_dir=(-1, 0, 0), z_dir=(0, 1, 0)
    )
    with BuildPart() as reference_tool:
        with BuildSketch(reference_plane):
            with Locations((-center.X, -center.Y)):
                add(reference_ink.sketch)
        extrude(amount=-h.LABEL_DEPTH)
    # Local text +X runs toward world -X when read from the exterior +Y side.
    expected = sorted(
        reference_tool.part.solids(),
        key=lambda glyph: glyph.bounding_box().center().X,
        reverse=True,
    )
    actual = sorted(
        glyphs, key=lambda glyph: glyph.bounding_box().center().X, reverse=True
    )
    matches = len(actual) == len(expected) == 4

    def boundary_matches(first, second) -> bool:
        first_edges = [
            shape
            for shape in Shape.get_shape_list(first, "Edge")
            if isinstance(shape, Edge)
        ]
        second_edges = [
            shape
            for shape in Shape.get_shape_list(second, "Edge")
            if isinstance(shape, Edge)
        ]
        return all(
            any(
                all(
                    reference.distance_to(edge.position_at(t)) < 1e-4
                    for t in (0, 0.25, 0.5, 0.75, 1)
                )
                for reference in second_edges
            )
            for edge in first_edges
        )

    for got, want in zip(actual, expected):
        gb, wb = got.bounding_box(), want.bounding_box()
        positioned = all(
            abs(a - b) < 1e-4
            for a, b in zip(
                (gb.min.X, gb.max.X, gb.min.Z, gb.max.Z),
                (wb.min.X, wb.max.X, wb.min.Z, wb.max.Z),
            )
        )
        # Bounds alone cannot distinguish a mirrored asymmetric glyph. Match
        # every complete boundary curve in both directions, including counters.
        # A common boolean on near-coincident B curves can incorrectly return
        # empty, so use geometric curve identity instead of intersection volume.
        same_ink = (
            boundary_matches(got, want)
            and boundary_matches(want, got)
            and abs(got.volume - want.volume) <= 0.002 * want.volume
        )
        matches &= positioned and same_ink
    report.check(
        matches,
        "actual glyph order, position and oriented ink match independently placed bold BITS",
    )
    height = min((glyph.bounding_box().size.Z for glyph in glyphs), default=0)
    report.check(
        height >= 3.0,
        "each actual bold glyph exceeds the 3 mm readable character-height floor",
        f"minimum actual ink height {height:.3f} mm; bold geometry verified above",
    )
    leftover = _overlap_volume(usecover, tool)
    report.check(
        leftover < GEOMETRY_TOL,
        "the complete exact engraving tool is removed from the actual cover",
        f"remaining glyph-cut material {leftover:.8f} mm³",
    )
    # Verify backing behind the ENTIRE true ink footprint, not just centroids.
    # Translate the exact tool into the residual wall and clip off .002 mm
    # at each boundary so contact tolerances cannot conceal a through-hole.
    backing_width = COVER_WALL - h.LABEL_DEPTH - 0.004
    backing_glyph = as_part(Pos(0, -h.LABEL_DEPTH, 0) * tool)
    with BuildPart() as backing_slab:
        with Locations(
            (
                0,
                (c.COVER_INNER_Y / 2 + wall - h.LABEL_DEPTH) / 2,
                c.COVER_H / 2,
            )
        ):
            Box(c.COVER_X + 2, backing_width, c.COVER_H + 2)
    with BuildPart() as backing:
        add(backing_glyph)
        add(backing_slab.part, mode=Mode.INTERSECT)
    missing = backing.part.volume - _overlap_volume(usecover, backing.part)
    report.check(
        abs(missing) < GEOMETRY_TOL,
        "the entire actual glyph footprint retains uninterrupted blind backing",
        f"{backing_width:.3f} mm interior backing slab; missing material {missing:.8f} mm³",
    )
    backed = True
    for glyph in glyphs:
        point = _glyph_point(report, tool, glyph, wall - h.LABEL_DEPTH / 2)
        if point is None:
            backed = False
            continue
        x, z = point
        backed &= (
            not report.solid_at(usecover, x, wall - h.LABEL_DEPTH + PROBE, z)
            and report.solid_at(usecover, x, wall - h.LABEL_DEPTH - PROBE, z)
            and not report.solid_at(usecover, x, c.COVER_INNER_Y / 2 - PROBE, z)
        )
    report.check(
        bool(glyphs) and backed,
        "every actual glyph cuts to .5 mm and retains .45 mm backing without through-holes",
    )


def _edge_allow(tool: Part) -> tuple:
    """Geometrically keyed snap profiles and exact glyph cuts, never Z bands."""
    reach = h.cover_snap_protrusion("bits")

    def snap_tip(edge):
        points = [edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)]
        return any(
            all(
                abs(p.Z - z) < GEOMETRY_TOL
                and abs(
                    _contour_distance(
                        p,
                        c.COVER_INNER_X - 2 * reach,
                        c.COVER_INNER_Y - 2 * reach,
                        INNER_R - reach,
                    )
                )
                < GEOMETRY_TOL
                for p in points
            )
            for z in (SNAP_Z - SNAP_TIP_FLAT / 2, SNAP_Z + SNAP_TIP_FLAT / 2)
        )

    # References are the cut solids' actual edges, including their inward
    # extrusions. Membership avoids exempting unrelated edges within ink bounds.
    glyph_edges = tuple(
        shape for shape in Shape.get_shape_list(tool, "Edge") if isinstance(shape, Edge)
    )

    def glyph_cut(edge):
        points = [edge.position_at(t) for t in (0, 0.25, 0.5, 0.75, 1)]
        return any(
            all(reference.distance_to(p) < GEOMETRY_TOL for p in points)
            for reference in glyph_edges
        )

    return (
        (
            snap_tip,
            "exact two rounded-rectangle tip-flat transition contours of the functional retention bead",
        ),
        (
            glyph_cut,
            "exact edges of the actual BITS cut tool; breaking them would erase readable ink",
        ),
    )


def run() -> Report:
    """Check a printable cover and the completed accepted anchors, not a scene."""
    # Runtime imports avoid cover.check() importing this gate back into itself.
    from .base import create_blank
    from .cover import create, label_tool
    from .insert import create as create_insert

    report = Report()
    printable = create()
    # Fixed inverse of the public print contract: do not reseat or normalize
    # altered geometry, and do not verify a separate create_use_pose() solid.
    usecover = as_part(Pos(0, 0, c.COVER_H) * Rot(180, 0, 0) * printable)
    tool = label_tool()
    check_shell(report, usecover)
    report.section("Actual pillow-down, mouth-up print pose")
    bounds = printable.bounding_box()
    report.check(
        printable.is_valid
        and len(printable.solids()) == 1
        and abs(bounds.min.Z) < GEOMETRY_TOL
        and abs(bounds.max.Z - c.COVER_H) < GEOMETRY_TOL
        and abs(bounds.size.X - c.COVER_X) < GEOMETRY_TOL
        and abs(bounds.size.Y - c.COVER_Y) < GEOMETRY_TOL
        and report.solid_at(printable, 0, 0, CAP_H / 2)
        and not report.solid_at(printable, 0, 0, c.COVER_H - PROBE),
        "true print envelope is one valid cap-down solid on z=0 with its mouth upward",
        f"bounds {bounds}",
    )
    check_fit(report, usecover, create_blank(), create_insert())
    _check_label(report, usecover, tool)
    report.section("Sharp and unclassifiable edge audit")
    allowances = _edge_allow(tool)
    survey = sharp_convex_edges(usecover, allow=allowances)
    for _, reason in allowances:
        report.lines.append(f"  allowed: {reason}")
    for bucket, edges in (
        ("sharp", survey.sharp),
        ("unclassifiable", survey.unclassifiable),
    ):
        report.check(
            not edges,
            f"cover has no unexplained {bucket} convex edges",
            "; ".join(f"{edge.center()} length={edge.length:.3f}" for edge in edges)
            or "0",
        )
    return report
