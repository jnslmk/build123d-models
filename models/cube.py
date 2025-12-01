"""Simple cube model example using builder mode."""

from build123d import Box, BuildPart, Part

SIZE = 20.0


def create() -> Part:
    """Create a simple cube with 20mm sides."""
    with BuildPart() as builder:
        Box(SIZE, SIZE, SIZE)
    return builder.part
