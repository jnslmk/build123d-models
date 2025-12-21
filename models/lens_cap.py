from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    Part,
    chamfer,
    extrude,
    export_step,
    export_stl,
)
from ocp_vscode import show


def create() -> Part:
    """Camera lens cap with 51mm internal diameter."""
    inner_dia = 51.0
    wall_thickness = 1.2
    height = 6.0
    top_thickness = 1.2
    chamfer_size = 0.6

    outer_dia = inner_dia + 2 * wall_thickness

    with BuildPart() as builder:
        # Solid cylinder for the cap
        with BuildSketch():
            Circle(outer_dia / 2)
        extrude(amount=top_thickness)

        # Wall ring
        with BuildSketch(builder.faces().sort_by().last):
            Circle(outer_dia / 2)
            Circle(inner_dia / 2, mode=Mode.SUBTRACT)
        extrude(amount=height - top_thickness)

        # Chamfer bottom edges (print bed side at z=0)
        bottom_face = builder.faces().sort_by().first
        chamfer(bottom_face.edges(), length=chamfer_size)

    return builder.part


def main() -> None:
    part = create()
    show(part)
    export_step(part, "exports/lens_cap.step")
    export_stl(part, "exports/lens_cap.stl")


if __name__ == "__main__":
    main()
