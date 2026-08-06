"""Rounded L-shaped door latch that pivots around a screw hole."""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Rectangle,
    extrude,
    fillet,
)

from models.lib.checks import Report, is_solid_at, sharp_convex_edges

LATCH_LENGTH = 85.0
ARM_WIDTH = 10.0
THICKNESS = 10.0
BEND_START = 75.0
HOOK_LENGTH = 10.0
PIVOT_HOLE_DIAMETER = 3.5
PIVOT_INSET = 5.0
OUTER_FILLET_RADIUS = 4.0


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

    return builder.part


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

    r.section("pivot hole")
    hole_r = PIVOT_HOLE_DIAMETER / 2
    r.check(
        not is_solid_at(part, PIVOT_INSET, 0, 0)
        and is_solid_at(part, PIVOT_INSET + hole_r + 0.1, 0, 0)
        and not is_solid_at(part, PIVOT_INSET + hole_r - 0.1, 0, 0),
        "pivot hole is bored to PIVOT_HOLE_DIAMETER, not larger or smaller",
        f"radius {hole_r:.2f} mm at ({PIVOT_INSET}, 0)",
    )
    r.check(
        not is_solid_at(part, PIVOT_INSET, 0, -THICKNESS / 2 + 0.1)
        and not is_solid_at(part, PIVOT_INSET, 0, THICKNESS / 2 - 0.1),
        "pivot hole passes through the full thickness",
        f"probed z=+/-{THICKNESS / 2 - 0.1:.1f}",
    )
    r.check(
        PIVOT_INSET - hole_r > 0 and hole_r < ARM_WIDTH / 2,
        "pivot hole sits inside the arm, clear of its end and both long edges",
        f"inset {PIVOT_INSET} mm, radius {hole_r:.2f} mm, "
        f"arm half-width {ARM_WIDTH / 2} mm",
    )

    r.section("hook")
    r.check(
        is_solid_at(part, hook_cap_center_x, hook_center_y + hook_r - 0.1, 0)
        and not is_solid_at(part, hook_cap_center_x, hook_center_y + hook_r + 0.1, 0),
        "hook cap is centered where the stem geometry places it, at ARM_WIDTH/2 radius",
        f"center ({hook_cap_center_x:.2f}, {hook_center_y:.2f}), radius {hook_r:.2f} mm",
    )
    r.check(
        abs(BEND_START - hook_start_x) < 1e-6,
        "BEND_START still matches where the hook actually starts (LATCH_LENGTH - HOOK_LENGTH)",
        f"BEND_START={BEND_START} vs LATCH_LENGTH-HOOK_LENGTH={hook_start_x} -- "
        "BEND_START is declared but create() never reads it (it recomputes "
        "hook_start_x locally instead); this only catches the two drifting apart",
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
        f"{len(bad)} found -- fillet() only treats the vertical wall edges; "
        "the front/back faces and the pivot hole's rim are never chamfered"
        if bad
        else "none",
    )

    return r
