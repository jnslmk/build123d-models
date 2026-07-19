"""Simple cube model example using builder mode."""

from build123d import Box, BuildPart, Part

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
