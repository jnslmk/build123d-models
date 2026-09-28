"""Physical gate for the removable support and 1×1 Gridfinity stacking interface."""

from build123d import Align, Box, BuildPart, Mode, Part, Pos, Rotation, add

from ..lib.checks import Report, is_solid_at
from .box import (
    CAP_H,
    HEIGHT_UNIT,
    PAD,
    FOOT_C3,
    STACK_SOCKET_DEPTH,
    STACK_FIT,
    gridfinity_foot,
)


def check_cover(
    cover: Part, foot_top: float, tool_tip_z: float, tip_clear: float
) -> Report:
    """Prove the foot fits after breaking out the grid, without relying on a view."""
    r = Report()
    r.section("stackable cover: foot interface and integral support")
    bb = cover.bounding_box()
    h = bb.size.Z
    r.check(
        abs(bb.min.Z) < 0.02
        and abs(bb.size.X - PAD) < 0.02
        and abs(bb.size.Y - PAD) < 0.02,
        "print pose is on the bed and inside the 1x1 footprint",
        f"z={bb.min.Z:.3f}, width={bb.size.X:.2f} x {bb.size.Y:.2f}",
    )
    r.check(
        abs((foot_top + h) % HEIGHT_UNIT) < 0.02,
        "assembled cover height is a whole Gridfinity unit",
        f"{foot_top + h:.2f} mm",
    )
    r.check(
        foot_top + h - STACK_SOCKET_DEPTH - CAP_H - tool_tip_z >= tip_clear - 0.02,
        "longest tool clears the solid ceiling below the stacking socket",
        f"tip at {tool_tip_z:.2f}, ceiling at {foot_top + h - STACK_SOCKET_DEPTH - CAP_H:.2f}",
    )
    # The support is a single solid with the cover, but a tool can enter below
    # the lattice ribs and the center void remains removable after nib cutting.
    r.check(
        len(cover.solids()) == 1
        and is_solid_at(cover, 0, 0, 0.5)
        and not is_solid_at(cover, 2.5, 2.5, 0.5),
        "breakaway support is attached and has open lattice cells",
        f"{len(cover.solids())} solid(s), rib at center and adjacent open cell",
    )
    # Simulate snipping the lattice below the socket floor, then seat the actual
    # shared foot in the upright lid. An intersection means it cannot stack.
    with BuildPart() as trimmed:
        add(cover)
        Box(
            34,
            34,
            STACK_SOCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    clean = trimmed.part
    r.check(
        not is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH - 0.1)
        and is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH + CAP_H / 2)
        and not is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH + CAP_H + 0.1),
        "removal exposes the socket floor with a solid cap beneath it",
        f"socket floor z={STACK_SOCKET_DEPTH:.2f} in print pose; cap={CAP_H:.2f}",
    )
    # On a flat side, the straight section of the foot has 0.11 mm of radial
    # PETG sliding clearance. Probe each side of the actual socket wall,
    # below the mouth funnel but above the lower bevel.
    wall_x = (PAD - 2 * FOOT_C3 + STACK_FIT) / 2
    r.check(
        not is_solid_at(clean, wall_x - 0.05, 0, 0.8)
        and is_solid_at(clean, wall_x + 0.05, 0, 0.8),
        "socket wall locates the foot on a calibrated sliding fit",
        f"flat-side wall at x={wall_x:.2f}, gap={STACK_FIT / 2:.2f} mm radial",
    )
    upright = Pos(0, 0, h) * Rotation(180, 0, 0) * clean
    foot = Pos(0, 0, h - STACK_SOCKET_DEPTH) * gridfinity_foot()
    r.check(
        upright.intersect(foot).volume < 0.01,
        "real Gridfinity foot enters the cleared socket without collision",
        "foot placed on the socket floor, all 1x1 bevels included",
    )
    lower_foot = Pos(0, 0, h - STACK_SOCKET_DEPTH - 0.3) * gridfinity_foot()
    r.check(
        upright.intersect(lower_foot).volume > 1.0,
        "socket floor actually supports the foot rather than leaving a through-hole",
        "foot driven 0.3 mm into the floor must intersect",
    )
    return r
