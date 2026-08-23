"""Half-sections, corner breaks, and the revolve that turns one into a part.

Both adapters in this package are the same kind of object: a closed (radius,
height) polyline, revolved about Z. Only the corners differ -- one ends in a
socket that goes *into* the duster's outlet, the other in a cap that goes *over*
its tail -- so the machinery for cutting the corners and spinning the loop lives
here and the two models contribute nothing but their own lists of points.

**Every break in this package is cut into the profile, never chamfered onto the
solid afterwards.** That is the ``build123d-geometry-ops`` rule taken at its
word: an OCC edge op is all-or-nothing and can cascade-corrupt a ``BuildPart``
after a single failure, while a corner trimmed in 2D before the revolve has no
selector to miss and nothing to fail -- it is just two points where there was
one. ``cable_spool``'s hub is the worked precedent.
"""

from __future__ import annotations

from math import atan2, degrees

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Part,
    Plane,
    Polyline,
    make_face,
    revolve,
)

from ..lib.edges import reseat_on_bed

Point = tuple[float, float]
"""One corner of a half-section: ``(radius, height)``, both in mm."""


def trim(points: list[Point], sizes: dict[int, float]) -> list[Point]:
    """Replace each named corner with a straight break across it.

    ``sizes`` maps an index in ``points`` to the length of the break to cut
    there; corners it does not name come through untouched. Each size is
    clamped to a third of the shorter adjacent segment, so a slider dragged to
    its stop shortens a break instead of inverting it into a self-crossing
    profile that would revolve into a solid nobody asked for.
    """
    n = len(points)
    out: list[Point] = []
    for i, corner in enumerate(points):
        size = sizes.get(i)
        if size is None:
            out.append(corner)
            continue
        prev_pt, next_pt = points[(i - 1) % n], points[(i + 1) % n]
        out.extend(
            [step_toward(corner, prev_pt, size), step_toward(corner, next_pt, size)]
        )
    return out


def step_toward(corner: Point, toward: Point, size: float) -> Point:
    """A point ``size`` away from ``corner`` along the segment to ``toward``."""
    dr, dz = toward[0] - corner[0], toward[1] - corner[1]
    length = (dr * dr + dz * dz) ** 0.5
    if length <= 0:
        return corner
    reach = min(size, length / 3)
    return (corner[0] + dr * reach / length, corner[1] + dz * reach / length)


def revolve_section(points: list[Point]) -> Part:
    """Revolve a closed half-section about Z and seat the result on the bed."""
    with BuildPart() as builder:
        with BuildSketch(Plane.XZ) as section:
            with BuildLine():
                Polyline(*points, close=True)
            make_face()
        _ = section
        revolve(axis=Axis.Z)
    return reseat_on_bed(builder.part)


def local_half_angle(bore: list[Point], z: float) -> float:
    """Angle from the Z axis, in degrees, of the bore segment spanning ``z``.

    The wall checks measure horizontally and have to divide by the cosine of
    the surface's own slope to get a thickness normal to it. Reading that slope
    off the profile rather than naming it per part is what lets one check cover
    a bore made of two cones and a bore made of four.
    """
    for (r0, z0), (r1, z1) in zip(bore, bore[1:], strict=False):
        if z0 - 1e-9 <= z <= z1 + 1e-9 and z1 > z0:
            return abs(degrees(atan2(r1 - r0, z1 - z0)))
    return 0.0
