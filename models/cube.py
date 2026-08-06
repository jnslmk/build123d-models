"""Simple cube model example using builder mode."""

from build123d import Box, BuildPart, Part

from models.lib.checks import Report, sharp_convex_edges

SIZE = 20.0

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
    with BuildPart() as builder:
        Box(size, size, size)
    return builder.part


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
    r.check(
        abs(part.volume - SIZE**3) < 1e-3,
        "volume equals SIZE**3",
        f"{part.volume:.3f} mm^3 vs {SIZE**3:.3f} mm^3 expected",
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
