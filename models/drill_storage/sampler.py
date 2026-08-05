"""The engine's own demo set: three labelled covers and two graduated bases.

Not a tool set anyone owns -- a sampler of what ``box.create_base`` and
``box.create_cover`` produce, kept so the engine is showable on its own without
first picking a drill collection. The real holders are ``drill_storage.wood``,
``.metal`` and ``.hex``.

Printed standing (cover) / bores-up (base) in PETG, no supports.
"""

from build123d import Compound, Pos

from .box import (
    BASE_COLOR,
    COVER_COLOR,
    create_base,
    create_cover,
    layout_bores,
)

# Demo drill sets -- just the sizes; ``layout_bores`` solves the positions. A
# small graduated set and a large-bit set, to show both ends of the range.
DEMO_DIAMS_SMALL = [3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 9.5]
DEMO_DIAMS_LARGE = [6.0, 8.0, 10.0, 12.0]


def create() -> Compound:
    """Full set: three labelled square covers with two Gridfinity bases."""
    covers = []
    for label, x in [("Metal", -52), ("Stone", 0), ("Wood", 52)]:
        c = create_cover(label)
        c.label = f"cover_{label.lower()}"
        c.color = COVER_COLOR
        covers.append(Pos(x, 30, 0) * c)

    bores9, _, rows9, pos9 = layout_bores(DEMO_DIAMS_SMALL)
    base9 = create_base(bores9, ribbed=True, rows=rows9, hole_pos=pos9)
    base9.label = "base_9_bore"
    base9.color = BASE_COLOR
    bores4, _, rows4, pos4 = layout_bores(DEMO_DIAMS_LARGE)
    base4 = create_base(bores4, ribbed=True, rows=rows4, hole_pos=pos4)
    base4.label = "base_4_bore"
    base4.color = BASE_COLOR

    return Compound(
        label="drill_storage",
        children=[
            *covers,
            Pos(-26, -30, 0) * base9,
            Pos(26, -30, 0) * base4,
        ],
    )


__all__ = ["DEMO_DIAMS_LARGE", "DEMO_DIAMS_SMALL", "create"]
