"""Rounded L-shaped door latch that pivots around a screw hole."""

from typing import cast

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Face,
    Kind,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    add,
    extrude,
    fillet,
    loft,
    offset,
)

from models.lib.checks import Report, is_solid_at, sharp_convex_edges
from models.lib.edges import as_part

LATCH_LENGTH = 85.0
ARM_WIDTH = 10.0
THICKNESS = 10.0
HOOK_LENGTH = 10.0
PIVOT_HOLE_DIAMETER = 3.5
PIVOT_INSET = 5.0
OUTER_FILLET_RADIUS = 4.0
RIM_CHAMFER = 0.3  # house edge rule, horizontal edges: front/back face rim.
# Small relative to OUTER_FILLET_RADIUS -- the rim tool (see _rim_chamfer_tool)
# has to shrink-loft the *whole* front/back face, hook cap included, and only
# a modest chamfer clears that curve without self-intersecting.


def _rim_chamfer_tool(part: Part, z_face: float, chamfer: float) -> Part:
    """A subtractable 45-deg chamfer for one flat (front or back) face's rim.

    Unlike ``models.lib.edges.top_chamfer_tool`` this does not assume a
    rounded-rect footprint -- the latch's outline is an L with a hook and a
    through-hole, so the "keep" loft is built from the face's *actual*
    boundary (via ``offset``) rather than a re-derived rectangle. Boolean,
    per build123d-geometry-ops: this face carries a hole and an
    already-filleted vertical rim, exactly the case that face carries
    "anything besides its own perimeter" and an OCC edge chamfer keeps
    refusing (see create()).
    """
    sign = 1 if z_face > 0 else -1

    def _is_the_face(f: Face) -> bool:
        return abs(f.normal_at().Z - sign) < 1e-4 and abs(f.center().Z - z_face) < 1e-4

    # Part.faces()/filter_by(predicate) is correct at runtime; see the same
    # suppression in models/lib/checks.py.
    faces = part.faces()  # ty: ignore[invalid-argument-type]
    face = faces.filter_by(_is_the_face)[0]  # ty: ignore[invalid-argument-type]
    shrunk = offset(face, amount=-chamfer, kind=Kind.INTERSECTION)
    full_start = cast(Face, Pos(0, 0, -sign * chamfer) * face)
    shrunk_ext = cast(Face, Pos(0, 0, sign * (chamfer + 1)) * shrunk)
    with BuildPart() as keep:
        add(full_start)
        add(shrunk)
        add(shrunk_ext)
        loft(ruled=True)

    bb = part.bounding_box()
    cx, cy = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2
    pad = 60
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_face - sign * chamfer)):
            with Locations((cx, cy)):
                Rectangle(bb.size.X + pad, bb.size.Y + pad)
        extrude(amount=sign * (chamfer + 1))
        add(keep.part, mode=Mode.SUBTRACT)
    return tool.part


def create() -> Part:
    """Create a printable rounded L-shaped pivoting door latch."""
    with BuildPart() as builder:
        # Main latch footprint with a rounded cap on the short hook end.
        hook_start_x = LATCH_LENGTH - HOOK_LENGTH
        hook_center_y = ARM_WIDTH
        hook_stem_length = max(HOOK_LENGTH - ARM_WIDTH / 2, 0)
        hook_stem_center_x = hook_start_x + hook_stem_length / 2
        hook_cap_center_x = hook_start_x + hook_stem_length

        with BuildSketch():
            with Locations((LATCH_LENGTH / 2, 0)):
                Rectangle(LATCH_LENGTH, ARM_WIDTH)
            if hook_stem_length > 0:
                with Locations((hook_stem_center_x, hook_center_y)):
                    Rectangle(hook_stem_length, ARM_WIDTH)
            with Locations((hook_cap_center_x, hook_center_y)):
                Circle(ARM_WIDTH / 2)
        extrude(amount=THICKNESS / 2, both=True)

        # Through-hole for pivot screw.
        with BuildSketch():
            with Locations((PIVOT_INSET, 0)):
                Circle(PIVOT_HOLE_DIAMETER / 2)
        extrude(amount=THICKNESS, both=True, mode=Mode.SUBTRACT)

        # Round external vertical corners for a softer latch profile.
        vertical_edges = list(builder.edges().filter_by(Axis.Z))
        fillet_edges = []
        for edge in vertical_edges:
            center = edge.center()
            # Exclude stem-to-cap transition edges; they are not valid for this fillet.
            if abs(center.X - hook_cap_center_x) < 1e-7:
                continue
            fillet_edges.append(edge)
        if fillet_edges:
            fillet(fillet_edges, radius=OUTER_FILLET_RADIUS)

        # Edge treatment, house rule: chamfer horizontal edges. (Vertical
        # edges are already filleted above.) The front/back faces carry the
        # pivot hole and the just-filleted outer rim, so this is a boolean
        # rim chamfer rather than a direct OCC edge chamfer -- see
        # _rim_chamfer_tool's docstring and build123d-geometry-ops.
        add(
            _rim_chamfer_tool(builder.part, THICKNESS / 2, RIM_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        add(
            _rim_chamfer_tool(builder.part, -THICKNESS / 2, RIM_CHAMFER),
            mode=Mode.SUBTRACT,
        )

    part = Pos(0, 0, -builder.part.bounding_box().min.Z) * builder.part
    return as_part(part)


def check() -> Report:
    """Geometry assertions beyond ``tests/test_door_latch_model.py``.

    That suite only confirms ``create()`` doesn't raise and that its source
    text uses certain build123d calls -- it never samples the actual solid.
    This adds what it doesn't cover: the built envelope against the module's
    own constants, the pivot hole's real diameter and position (point-sampled,
    not just "a circle was requested"), the hook cap's position, print pose,
    and the house edge rule.
    """
    r = Report()
    part = create()
    bb = part.bounding_box()

    hook_start_x = LATCH_LENGTH - HOOK_LENGTH
    hook_stem_length = max(HOOK_LENGTH - ARM_WIDTH / 2, 0)
    hook_cap_center_x = hook_start_x + hook_stem_length
    hook_center_y = ARM_WIDTH
    hook_r = ARM_WIDTH / 2

    r.section("envelope")
    r.check(
        abs(bb.size.X - LATCH_LENGTH) < 1e-6,
        "latch spans LATCH_LENGTH along X",
        f"{bb.size.X:.3f} mm",
    )
    r.check(
        abs(bb.size.Z - THICKNESS) < 1e-6,
        "latch is THICKNESS thick",
        f"{bb.size.Z:.3f} mm",
    )

    # Z probes are expressed relative to bb.min.Z/bb.max.Z -- the build-plate
    # contact face and the top face -- not the pre-reseat, THICKNESS-centered
    # z=0 this module's own constants would suggest. create() re-seats the
    # part (print pose, house idiom), so the part now spans
    # bb.min.Z .. bb.min.Z + THICKNESS, not the centered -THICKNESS/2 ..
    # +THICKNESS/2 a centered part would use. Each probe below still samples
    # the same physical feature (same hole, same cap) -- only the z origin
    # moved: z_mid is still mid-thickness, z_bottom/z_top are still each face.
    z_mid = bb.min.Z + THICKNESS / 2
    z_bottom = bb.min.Z
    z_top = bb.max.Z

    r.section("pivot hole")
    hole_r = PIVOT_HOLE_DIAMETER / 2
    r.check(
        not is_solid_at(part, PIVOT_INSET, 0, z_mid)
        and is_solid_at(part, PIVOT_INSET + hole_r + 0.1, 0, z_mid)
        and not is_solid_at(part, PIVOT_INSET + hole_r - 0.1, 0, z_mid),
        "pivot hole is bored to PIVOT_HOLE_DIAMETER, not larger or smaller",
        f"radius {hole_r:.2f} mm at ({PIVOT_INSET}, 0), z={z_mid:.1f}",
    )
    r.check(
        not is_solid_at(part, PIVOT_INSET, 0, z_bottom + 0.1)
        and not is_solid_at(part, PIVOT_INSET, 0, z_top - 0.1),
        "pivot hole passes through the full thickness",
        f"probed z={z_bottom + 0.1:.1f} and z={z_top - 0.1:.1f}",
    )
    r.check(
        PIVOT_INSET - hole_r > 0 and hole_r < ARM_WIDTH / 2,
        "pivot hole sits inside the arm, clear of its end and both long edges",
        f"inset {PIVOT_INSET} mm, radius {hole_r:.2f} mm, "
        f"arm half-width {ARM_WIDTH / 2} mm",
    )

    r.section("hook")
    r.check(
        is_solid_at(part, hook_cap_center_x, hook_center_y + hook_r - 0.1, z_mid)
        and not is_solid_at(
            part, hook_cap_center_x, hook_center_y + hook_r + 0.1, z_mid
        ),
        "hook cap is centered where the stem geometry places it, at ARM_WIDTH/2 radius",
        f"center ({hook_cap_center_x:.2f}, {hook_center_y:.2f}), "
        f"radius {hook_r:.2f} mm, z={z_mid:.1f}",
    )

    r.section("print pose")
    r.check(
        abs(bb.min.Z) < 1e-6,
        "part sits on the build plate (min z = 0)",
        f"min z = {bb.min.Z:.3f} mm -- create() never re-seats it after "
        "the symmetric extrude",
    )

    r.section("sharp edges")
    bad = sharp_convex_edges(part)
    r.check(
        not bad,
        "no unexplained sharp convex edges (chamfer horizontal, fillet vertical)",
        f"{len(bad)} found -- KNOWN, UNRESOLVED: two mirrored pairs (front and "
        "back) right where _rim_chamfer_tool's shrink-loft meets the hook "
        "cap's R(ARM_WIDTH/2) curve. Every OCC chamfer/fillet retry on just "
        "these edges failed down to 0.02 mm, and every RIM_CHAMFER in the "
        "0.06-1.0 mm range leaves exactly this residue -- only a "
        "sub-printable ~0.02-0.04 mm rim chamfer clears it, which is not a "
        "real edge treatment, so this stays failing rather than being "
        "faked or allow-listed. See the implementer report for the full "
        "search."
        if bad
        else "none",
    )

    return r
