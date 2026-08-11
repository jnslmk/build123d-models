"""Shared edge-treatment helpers.

Two ways to put a chamfer on a part, and the choice is not stylistic:

* ``chamfer_edge`` (and ``fillet_edge``) wrap the OCC edge op with
  snapshot/restore, so a failure is isolated instead of corrupting the builder
  and silently killing every *later* chamfer too.
* ``top_chamfer_tool`` builds a **boolean** chamfer instead -- an oversized slab
  minus a lofted keep-frustum. Booleans cannot fail the way OCC edge ops do.

Use the boolean whenever the face carries anything besides its own perimeter.
The worked example was the old screw-down lid: OCC refused to chamfer its
perimeter at any length once 14 countersinks existed on the same face, even
though they were 5 mm clear of it. The boolean cannot fail that way.
"""

from __future__ import annotations

from typing import Any, cast

from build123d import (
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Rotation,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
)


def as_part(shape: Any) -> Part:
    """Narrow a placement result back to ``Part``.

    ``Location * Shape`` (which is what ``Pos(...) * part`` and
    ``Rotation(...) * part`` are) is typed as returning a generic ``Shape``, but
    for a solid operand the result is always a solid. This keeps the narrowing in
    one documented place instead of scattering ignores through every module.
    """
    return cast(Part, shape)


def reseat_on_bed(part: Part, flip: bool = False) -> Part:
    """Seat a part on the bed: translate so ``bounding_box().min.Z`` is z=0.

    The repo's print-pose rule (AGENTS.md, "Design Guidelines"): parts print
    bottom-to-top and a model IS its print orientation, so a part must come
    out already sitting on the bed -- Z+ is the print direction. Lids and
    caps built closed-top-up get flipped 180 deg about X (``flip=True``) so
    the open mouth faces up, then re-seated on z=0. This is the
    one-line-to-three-line idiom that prose documents; the transform is
    rigid, so it never changes the part, only how it lies on the bed.
    """
    flipped = as_part(Rotation(180, 0, 0) * part) if flip else part
    return as_part(Pos(0, 0, -flipped.bounding_box().min.Z) * flipped)


def chamfer_edge(builder: BuildPart, edges, size: float) -> bool:
    """Chamfer edges, isolating an OCC failure so it cannot cascade.

    Returns True if it took. A bare try/except would leave you believing one
    edge went unchamfered when in fact every subsequent one failed as well.
    """
    saved = builder.part
    try:
        chamfer(edges, length=size)
        return True
    except Exception as exc:  # noqa: BLE001 -- OCC edge ops are flaky
        builder.part = saved  # ty: ignore[invalid-assignment]
        print(f"warning: chamfer skipped ({exc})")
        return False


def fillet_edge(builder: BuildPart, edges, radius: float) -> bool:
    """Fillet edges, isolating an OCC failure so it cannot cascade.

    The companion to ``chamfer_edge``, for the vertical edges the house rule
    wants rounded rather than chamfered. Same contract: returns True if it took,
    and restores the builder if it did not, because OCC's fillet fails the same
    all-or-nothing way -- and unlike a chamfer it also fails whenever the radius
    does not fit the narrowest adjacent face, which is a size problem rather
    than a topology one. Walk a decreasing ladder if the radius is negotiable.
    """
    saved = builder.part
    try:
        fillet(edges, radius=radius)
        return True
    except Exception as exc:  # noqa: BLE001 -- OCC edge ops are flaky
        builder.part = saved  # ty: ignore[invalid-assignment]
        print(f"warning: fillet skipped ({exc})")
        return False


def top_chamfer_tool(
    size_x: float,
    size_y: float,
    corner_r: float,
    z_top: float,
    ch: float,
) -> Part:
    """A subtractable 45 chamfer for the top outer edge of a rounded-rect prism."""
    inner_r = max(corner_r - ch, 0.5)
    with BuildPart() as keep:
        with BuildSketch(Plane.XY.offset(z_top - ch)):
            RectangleRounded(size_x, size_y, corner_r)
        with BuildSketch(Plane.XY.offset(z_top)):
            RectangleRounded(size_x - 2 * ch, size_y - 2 * ch, inner_r)
        with BuildSketch(Plane.XY.offset(z_top + ch + 1)):
            RectangleRounded(size_x - 2 * ch, size_y - 2 * ch, inner_r)
        loft(ruled=True)

    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_top - ch)):
            Rectangle(size_x + 40, size_y + 40)
        extrude(amount=ch + 1)
        add(keep.part, mode=Mode.SUBTRACT)
    return tool.part


def bottom_chamfer_tool(
    size_x: float,
    size_y: float,
    corner_r: float,
    z_bottom: float,
    ch: float,
) -> Part:
    """A subtractable 45 chamfer for the bottom outer edge (elephant's-foot relief)."""
    inner_r = max(corner_r - ch, 0.5)
    with BuildPart() as keep:
        with BuildSketch(Plane.XY.offset(z_bottom - ch - 1)):
            RectangleRounded(size_x - 2 * ch, size_y - 2 * ch, inner_r)
        with BuildSketch(Plane.XY.offset(z_bottom)):
            RectangleRounded(size_x - 2 * ch, size_y - 2 * ch, inner_r)
        with BuildSketch(Plane.XY.offset(z_bottom + ch)):
            RectangleRounded(size_x, size_y, corner_r)
        loft(ruled=True)

    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_bottom - 1)):
            Rectangle(size_x + 40, size_y + 40)
        extrude(amount=ch + 1)
        add(keep.part, mode=Mode.SUBTRACT)
    return tool.part
