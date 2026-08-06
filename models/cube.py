"""Simple cube model example using builder mode."""

import math

from build123d import Axis, Box, BuildPart, Part, Pos, chamfer, fillet

from models.lib.checks import Report, sharp_convex_edges
from models.lib.edges import as_part

SIZE = 20.0

# Edge break, proportionate to SIZE and capped so a large cube doesn't get an
# oversized bevel. A plain box's edges are a clean prism with nothing else on
# the face, so a direct OCC fillet/chamfer is safe (see build123d-geometry-ops).
EDGE_FRACTION = 0.08
EDGE_MAX = 2.0

# UI schema for the parametric web app. See tessellate_models.model_params().
PARAMS = [
    {
        "name": "size",
        "label": "Size (mm)",
        "type": "number",
        "min": 5.0,
        "max": 100.0,
        "step": 0.5,
        "default": SIZE,
    },
]


def create(size: float = SIZE) -> Part:
    """Create a simple cube with the given side length (default 20mm)."""
    edge = min(size * EDGE_FRACTION, EDGE_MAX)
    with BuildPart() as builder:
        Box(size, size, size)
        # Chamfer horizontal (top/bottom) edges first, fillet vertical edges
        # second: the vertical corners are still full straight lines once the
        # top/bottom bevels are cut, while doing it the other way round would
        # leave the fillet's own tangent seams to be picked up as "horizontal".
        chamfer(builder.edges().filter_by(Axis.Z, reverse=True), length=edge)
        fillet(builder.edges().filter_by(Axis.Z), radius=edge)
    part = Pos(0, 0, -builder.part.bounding_box().min.Z) * builder.part
    return as_part(part)


def _expected_volume(size: float) -> float:
    """Predict the treated cube's volume from SIZE and the edge break alone.

    Independent of ``create()``'s actual output -- this is what a *correctly
    sized* cube should weigh in at, derived from the same geometry a plain
    chamfer+fillet produces, so the check can still catch a wrong SIZE (or a
    wrong edge size) rather than only ever comparing a value against itself.

    The chamfer treats the top and bottom rims first, each removing a
    frustum-shaped collar of height ``edge`` (side tapering linearly from
    ``size`` down to ``d = size - 2*edge``, i.e. volume ``(size**3 - d**3)/6``
    per collar). What is left is a plain d-tall prism of the *original*
    cross-section between them. The fillet then rounds that prism's 4
    vertical corners over its full height ``d``, each corner removing a
    square-minus-quarter-circle sliver of area ``edge**2 * (1 - pi/4)``.

    This slightly overestimates the true volume (by a few tenths of a percent
    at most, growing with edge size): OCC blends the fillet smoothly into the
    chamfer at the collar/prism seam rather than stopping abruptly there, and
    that blend removes a hair more material than this flat model accounts
    for. ``VOLUME_TOLERANCE_FRACTION`` covers exactly that -- not a fudge for
    "close enough", but the one geometric effect not modelled above.
    """
    edge = min(size * EDGE_FRACTION, EDGE_MAX)
    d = size - 2 * edge
    chamfered = size**2 * d + (size**3 - d**3) / 3  # two collars, (S^3-d^3)/6 each
    return chamfered - edge**2 * (4 - math.pi) * d


# How far _expected_volume's flat-collar model may miss the real (blended)
# volume, as a fraction of size**3. Measured error tops out around 0.008% of
# size**3 across SIZE = 5..100 (the full PARAMS range); this leaves a >6x
# margin so it never chases numerical noise, while staying two to three
# orders of magnitude tighter than the volume error even a 1% SIZE mistake
# would cause.
VOLUME_TOLERANCE_FRACTION = 0.0005


def check() -> Report:
    """Pin the default cube's dimensions, volume, print pose and edge treatment.

    Runs against the ``PARAMS`` default (``create()`` with no arguments), since
    that is what ``uv run check cube`` and the website both exercise first.
    """
    r = Report()
    part = create()
    bb = part.bounding_box()

    r.section("dimensions")
    r.check(
        abs(bb.size.X - SIZE) < 1e-6
        and abs(bb.size.Y - SIZE) < 1e-6
        and abs(bb.size.Z - SIZE) < 1e-6,
        "cube measures SIZE on every axis",
        f"{bb.size.X:.3f} x {bb.size.Y:.3f} x {bb.size.Z:.3f} mm (SIZE={SIZE})",
    )
    expected_volume = _expected_volume(SIZE)
    tolerance = VOLUME_TOLERANCE_FRACTION * SIZE**3
    r.check(
        abs(part.volume - expected_volume) < tolerance,
        "volume matches SIZE**3 minus the chamfer/fillet break (not SIZE**3 "
        "itself -- a real edge treatment always removes some material)",
        f"{part.volume:.3f} mm^3 vs {expected_volume:.3f} mm^3 expected "
        f"(+/-{tolerance:.3f}), vs {SIZE**3:.3f} mm^3 for an untreated cube",
    )

    r.section("print pose")
    r.check(
        abs(bb.min.Z) < 1e-6,
        "part sits on the build plate (min z = 0)",
        f"min z = {bb.min.Z:.3f} mm -- Box() is CENTER-aligned on all axes and "
        "create() never re-seats it, so this fails against AGENTS.md's "
        "print-pose rule",
    )

    r.section("sharp edges")
    bad = sharp_convex_edges(part)
    r.check(
        not bad,
        "no unexplained sharp convex edges (chamfer horizontal, fillet vertical)",
        f"{len(bad)} found -- a plain Box() has no edge treatment at all, so "
        "every one of its 12 edges is raw"
        if bad
        else "none",
    )
    return r
