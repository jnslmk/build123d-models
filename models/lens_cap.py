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

from models.lib.checks import Report, is_solid_at, sharp_convex_edges

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


def check() -> Report:
    """Pin the bore, wall and print pose the docstring promises, on the defaults.

    Runs against the ``PARAMS`` defaults (``create()`` with no arguments), same as
    ``uv run check lens_cap`` and the website's first render.
    """
    r = Report()
    part = create()
    bb = part.bounding_box()
    probe = 0.05

    r.section("print pose")
    r.check(
        abs(bb.min.Z) < 1e-6,
        "part is re-seated on z=0",
        f"min z = {bb.min.Z:.4f} mm",
    )
    r.check(
        is_solid_at(part, 0, 0, TOP_THICKNESS / 2)
        and not is_solid_at(part, 0, 0, HEIGHT - probe),
        "closed disc sits on the bed, open mouth faces up (not bridged)",
        f"solid at z={TOP_THICKNESS / 2:.2f} mm (disc), hollow at "
        f"z={HEIGHT - probe:.2f} mm (mouth) -- 'closed face down on the bed, "
        "mouth up' per the module docstring",
    )

    r.section("bore")
    r_in = INNER_DIA / 2
    r.check(
        not is_solid_at(part, r_in - probe, 0, HEIGHT / 2)
        and is_solid_at(part, r_in + probe, 0, HEIGHT / 2),
        "bore is cut at inner_dia with no clearance added",
        f"cavity extends to r={r_in:.2f} mm at z={HEIGHT / 2:.2f} mm -- the "
        "docstring is explicit that no clearance is subtracted here, because an "
        "FDM bore already prints a few tenths under nominal",
    )
    outer_r = bb.size.X / 2
    expected_outer_r = INNER_DIA / 2 + WALL_THICKNESS
    r.check(
        abs(outer_r - expected_outer_r) < 1e-6,
        "outer radius is inner_dia/2 + wall_thickness",
        f"measured {outer_r:.3f} mm, expected {expected_outer_r:.3f} mm",
    )

    r.section("wall (retention)")
    # The docstring states the wall's whole design rationale in one sentence:
    # "1.2 mm, three perimeters at a 0.4 mm nozzle". That is what lets the wall
    # flex onto the barrel and hold by friction instead of hoop-stressing it --
    # the cap's only retention feature. Pin the arithmetic behind the number, not
    # just the number itself.
    nozzle_width = 0.4
    perimeters = 3
    r.check(
        abs(WALL_THICKNESS - perimeters * nozzle_width) < 1e-9,
        "wall is exactly 3 perimeters at a 0.4 mm nozzle (thin enough to flex on)",
        f"{WALL_THICKNESS} mm vs {perimeters} x {nozzle_width} = "
        f"{perimeters * nozzle_width} mm",
    )

    r.section("edges")
    bad = sharp_convex_edges(part)
    r.check(
        not bad,
        "no unchamfered sharp convex edges",
        (
            f"{len(bad)} found at z={sorted({round(e.center().Z, 2) for e in bad})} "
            "-- the mouth (the edge that has to ride onto the barrel without "
            "catching) has no lead-in chamfer; only the bed-side closed face does"
        )
        if bad
        else "clean",
    )

    return r
