"""Gridfinity drill storage sized for a 2-10 mm metric twist-drill set plus a
10 mm hex-shank countersink.

A ready-to-print pair built on the square Gridfinity base/cover from
``drill_storage_gridfinity``: a 1x1 base holding nine graduated drills
(2, 2.5, 3, 3.5, 4, 5, 6, 8, 10 mm) plus a 10 mm countersink bit with a 6.3 mm
hex shank, and a matching labelled cover that snaps over it.

The nine drills and the countersink are hand-packed into the 1x1 collar (all
positions verified to sit inside the collar with sensible walls). The
countersink drops into a hex socket for its shank; its 10 mm head just rests on
the top face, so that position reserves a 10 mm clear footprint.

Change ``LABEL`` to relabel the cover for your material.
"""

from build123d import Compound, Pos

from models.drill_storage_gridfinity import (
    BASE_COLOR,
    COVER_COLOR,
    create_base,
    create_cover,
)

LABEL = "Wood"  # material name embossed on the cover

# Diametral bore clearance (mm) at the rib tips. Wood/brad-point bits have outer
# spurs that cut a hair over the nominal shank, and FDM prints small vertical
# holes ~0.1-0.3 mm undersized, so cutting the bores at exactly nominal is a
# tight press fit. Bores are ribbed (see drill_storage_gridfinity), so the bit
# rides on three rounded contacts with this clearance and drops in cleanly.
BORE_CLEARANCE = 0.5

# Round drill bores (diameter, x, y). With 7 and 9 mm added there are 11 ribbed
# bores plus the countersink's 10 mm head footprint packed into the 39 mm
# collar, so the whole layout is repacked (relaxation solver) to keep >= ~0.8 mm
# walls everywhere; the four big features (8/9/10 mm bores + hex head) sit near
# the four corners, smalls fill the middle.
DRILL_BORES = [
    (2.0, 6.0, -6.0),
    (2.5, -6.0, -6.0),
    (3.0, 6.0, 6.0),
    (3.5, -5.0, 5.0),
    (4.0, 0.0, -13.0),
    (5.0, 0.0, 13.0),
    (6.0, 13.0, 1.0),
    (7.0, -13.0, 0.0),
    (8.0, 12.0, 12.0),
    (9.0, 12.0, -12.0),
    (10.0, -12.0, 12.0),
]

# 10 mm countersink with a 6.3 mm hex shank: a hex socket for the shank in the
# fourth corner, keeping a 10 mm clear top footprint for the head to rest on.
CSK_X, CSK_Y = -12.0, -12.0
CSK_HEX_AF = 7.0  # 6.3 mm hex + a little fit clearance, across flats
HEX_BORES = [(CSK_HEX_AF, CSK_X, CSK_Y)]


def create() -> Compound:
    """The base for the drill set + countersink, with its matching cover."""
    base = create_base(
        DRILL_BORES, hex_bores=HEX_BORES, clearance=BORE_CLEARANCE, ribbed=True
    )
    base.label = "base_2_10mm_csk"
    base.color = BASE_COLOR

    cover = create_cover(LABEL)
    cover.label = f"cover_{LABEL.lower()}"
    cover.color = COVER_COLOR

    return Compound(
        label="drill_storage_metric",
        children=[Pos(-26, 0, 0) * base, Pos(26, 0, 0) * cover],
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_storage_metric")


if __name__ == "__main__":
    main()
