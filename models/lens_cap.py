"""Push-on camera lens cap: a shallow cup that slips over the front of a barrel.

A closed disc with a thin ring wall standing off it. Nothing snaps and nothing
threads -- it is held by friction against the outside of the lens barrel, which
is why the wall is deliberately thin (1.2 mm, three perimeters at a 0.4 mm
nozzle): it has to flex onto the barrel rather than hoop-stress against it.

**What it fits.** ``inner_dia`` is the cap's bore and defaults to 51 mm. Set it
to the barrel's *measured* outside diameter -- no clearance is subtracted here,
because an FDM bore already prints a few tenths under nominal and the thin wall
takes up the rest. If a cap comes out too tight to push on, raise ``inner_dia``
by 0.2 mm at a time rather than thinning the wall. ``height`` is how far it
covers the barrel; 6 mm is enough to stay put without fouling a focus ring.

Parametric on the website (see ``PARAMS``). ``create()`` clamps every input so
the geometry stays valid across the full slider range -- the top cannot swallow
the whole height, and the chamfer cannot eat the wall.

**Printing.** PETG, no supports, and it comes back already in print pose:
closed face down on the bed, mouth up. That way the disc is a solid first layer
instead of an unsupported bridge across the cavity. The chamfer sits on that
bed-side edge, so it doubles as elephant-foot relief -- which is also what keeps
the rim from catching as the cap goes on.
"""

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    Part,
    Pos,
    chamfer,
    extrude,
)


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

    # Print orientation: the builder already sits closed-face-down, open mouth
    # up — the closed disc becomes the smooth first layer on the bed instead of
    # an unsupported bridge across the cavity. Just re-seat on z=0.
    part = builder.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part
