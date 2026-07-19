from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    Part,
    Pos,
    Rotation,
    chamfer,
    extrude,
    export_step,
    export_stl,
)
from ocp_vscode import show


INNER_DIA = 51.0
WALL_THICKNESS = 1.2
HEIGHT = 6.0
TOP_THICKNESS = 1.2
CHAMFER_SIZE = 0.6

# UI schema for the parametric web app. See tessellate_models.model_params().
PARAMS = [
    {
        "name": "inner_dia",
        "label": "Inner diameter (mm)",
        "type": "number",
        "min": 20.0,
        "max": 100.0,
        "step": 0.5,
        "default": INNER_DIA,
    },
    {
        "name": "wall_thickness",
        "label": "Wall thickness (mm)",
        "type": "number",
        "min": 0.8,
        "max": 4.0,
        "step": 0.1,
        "default": WALL_THICKNESS,
    },
    {
        "name": "height",
        "label": "Height (mm)",
        "type": "number",
        "min": 3.0,
        "max": 20.0,
        "step": 0.5,
        "default": HEIGHT,
    },
    {
        "name": "top_thickness",
        "label": "Top thickness (mm)",
        "type": "number",
        "min": 0.8,
        "max": 4.0,
        "step": 0.1,
        "default": TOP_THICKNESS,
    },
    {
        "name": "chamfer_size",
        "label": "Chamfer (mm)",
        "type": "number",
        "min": 0.0,
        "max": 2.0,
        "step": 0.1,
        "default": CHAMFER_SIZE,
    },
]


def create(
    inner_dia: float = INNER_DIA,
    wall_thickness: float = WALL_THICKNESS,
    height: float = HEIGHT,
    top_thickness: float = TOP_THICKNESS,
    chamfer_size: float = CHAMFER_SIZE,
) -> Part:
    """Camera lens cap; defaults to 51mm internal diameter."""
    # Keep geometry valid across the full parameter range.
    top_thickness = min(top_thickness, height - 0.2)
    outer_dia = inner_dia + 2 * wall_thickness
    max_chamfer = min(wall_thickness, height - top_thickness) - 0.05
    chamfer_size = max(0.0, min(chamfer_size, max_chamfer))

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

        # Chamfer the solid-top edges (the closed face of the cap).
        if chamfer_size > 0:
            bottom_face = builder.faces().sort_by().first
            chamfer(bottom_face.edges(), length=chamfer_size)

    # Print orientation: turn the cap upside down (closed top up, open mouth on
    # the bed) and re-seat on z=0, so it exports in the pose it prints in.
    part = Rotation(180, 0, 0) * builder.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


def main() -> None:
    part = create()
    show(part)
    export_step(part, "exports/lens_cap.step")
    export_stl(part, "exports/lens_cap.stl")


if __name__ == "__main__":
    main()
