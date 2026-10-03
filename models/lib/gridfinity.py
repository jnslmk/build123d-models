"""Standard Gridfinity dimensions and reusable solid/lightweight foot profiles.

Feet are centred in XY with their print-bed face at z=0 and pad top at
``BASE_H``. The ruled sections retain the drill-storage family's existing
profile; cover and stacking-socket geometry remains in that family.
"""

from build123d import (
    BuildPart,
    BuildSketch,
    Locations,
    Part,
    Plane,
    RectangleRounded,
    loft,
)

GRID = 42.0
TOLERANCE = 0.5
PAD = GRID - TOLERANCE  # 41.5 mm pad top
CORNER_R = 4.0  # Gridfinity top corner radius
FOOT_C1 = 0.7  # bottom chamfer (45 deg)
FOOT_STRAIGHT = 1.8  # vertical section
FOOT_C3 = 1.9  # top chamfer (45 deg)
BASE_H = FOOT_C1 + FOOT_STRAIGHT + FOOT_C3  # 4.4 mm foot profile
HEIGHT_UNIT = 7.0  # Gridfinity Z unit


def gridfinity_foot(size_x: float = PAD, size_y: float = PAD) -> Part:
    """Full or half-grid foot with the standard four-section bevel profile."""
    with BuildPart() as foot:
        sections = []
        for z, inset in (
            (0, FOOT_C1 + FOOT_C3),
            (FOOT_C1, FOOT_C3),
            (FOOT_C1 + FOOT_STRAIGHT, FOOT_C3),
            (BASE_H, 0),
        ):
            with BuildSketch(Plane.XY.offset(z)) as profile:
                RectangleRounded(
                    size_x - 2 * inset, size_y - 2 * inset, CORNER_R - inset
                )
            sections.append(profile.sketch)
        loft(sections=sections, ruled=True)
    return foot.part


def gridfinity_foot_cavity(
    size_x: float,
    size_y: float,
    wall: float,
    bottom: float,
    seams: tuple[bool, bool, bool, bool],
    seam_chamfer: float = 0.2,
) -> Part:
    """Open the foot above a bed plate; soften only its interior cell seams.

    ``bottom`` is the plate's top Z; ``wall`` offsets the foot's profile inward.
    ``seams`` selects the internal boundaries in -X, +X, -Y, +Y order. The tool
    reaches 0.05 mm above ``BASE_H + wall`` to join the bin's main cavity.
    """
    transition = FOOT_C1 + FOOT_STRAIGHT

    def inset_at(z: float) -> float:
        if z < FOOT_C1:
            return FOOT_C3 + FOOT_C1 - z
        if z < transition:
            return FOOT_C3
        if z < BASE_H:
            return BASE_H - z
        return 0.0

    with BuildPart() as cavity:
        sections = []
        floor_z = BASE_H + wall
        levels = (
            bottom,
            *(z for z in (FOOT_C1, transition, BASE_H) if z > bottom),
            floor_z - seam_chamfer,
            floor_z,
            floor_z + 0.05,
        )
        for z in levels:
            inset = inset_at(z) + wall
            # Bevel only internal cell boundaries, never the outer side walls.
            seam_bevel = max(0, min(seam_chamfer, z - floor_z + seam_chamfer))
            x_low, x_high, y_low, y_high = (seam_bevel if seam else 0 for seam in seams)
            with BuildSketch(Plane.XY.offset(z)) as profile:
                with Locations(((x_high - x_low) / 2, (y_high - y_low) / 2)):
                    RectangleRounded(
                        size_x - 2 * inset + x_low + x_high,
                        size_y - 2 * inset + y_low + y_high,
                        max(0.4, CORNER_R - inset),
                    )
            sections.append(profile.sketch)
        loft(sections=sections, ruled=True)
    return cavity.part
