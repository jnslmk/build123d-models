"""Simple cube model example using builder mode."""

from build123d import BuildPart, Box, Part, export_step, export_stl
from ocp_vscode import show

# Cube dimensions in mm
SIZE = 20.0


def create_cube(size: float = SIZE) -> Part:
    """Create a simple cube with the given side length."""
    with BuildPart() as builder:
        Box(size, size, size)
    return builder.part


def main() -> None:
    """Build and export the cube model."""
    cube = create_cube()

    show(cube)

    export_step(cube, "exports/cube.step")
    export_stl(cube, "exports/cube.stl")
    print(f"Exported cube ({SIZE}mm) to exports/")


if __name__ == "__main__":
    main()
