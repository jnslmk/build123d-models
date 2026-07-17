"""Gridfinity drill storage sized for a 2-10 mm metric twist-drill set plus a
10 mm hex-shank countersink.

A ready-to-print pair built on the square Gridfinity base/cover from
``drill_storage_gridfinity``: a 1x1 base holding eleven graduated drills
(2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10 mm) plus a 10 mm countersink bit with a
6.3 mm hex shank, and a matching labelled cover that snaps over it.

Hole positions are computed by ``pack_holes`` (a deterministic relaxation
solver) rather than hand-placed, so the walls always clear the mouth and top-rim
fillets and you can edit ``DRILL_DIAMS`` freely and let it re-pack. The
countersink drops into a hex socket for its shank; its 10 mm head just rests on
the top face, so that position reserves a 10 mm clear footprint.

Change ``LABEL`` to relabel the cover for your material.
"""

from build123d import Compound, Pos

from models.drill_storage_gridfinity import (
    BASE_COLOR,
    BASE_TOP_FILLET,
    BORE_MOUTH_FILLET,
    COLLAR_W,
    COVER_COLOR,
    RIB_RELIEF,
    create_base,
    create_cover,
    pack_holes,
)

LABEL = "Wood"  # material name embossed on the cover

# Diametral bore clearance (mm) at the rib tips. Wood/brad-point bits have outer
# spurs that cut a hair over the nominal shank, and FDM prints small vertical
# holes ~0.1-0.3 mm undersized, so cutting the bores at exactly nominal is a
# tight press fit. Bores are ribbed (see drill_storage_gridfinity), so the bit
# rides on three rounded contacts with this clearance and drops in cleanly.
BORE_CLEARANCE = 0.4

# Drill sizes in the set (mm). Positions are auto-placed below, so you can add
# or remove a size and the layout re-packs itself.
DRILL_DIAMS = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

# 10 mm countersink on a 6.3 mm hex shank: the socket holds the shank while the
# 10 mm head rests on the top face, so the packer reserves the head's footprint.
CSK_HEX_AF = 6.8  # 6.3 mm hex + fit clearance (between the original 6.6 and 7.0)
CSK_HEAD_D = 10.0


def _valley_r(d: float) -> float:
    """Ribbed-bore cut (valley) radius for a bit of diameter ``d`` mm."""
    return (d + BORE_CLEARANCE) / 2 + RIB_RELIEF


# Auto-placement: keep two mouth fillets of wall between holes, and one mouth
# fillet plus the top-rim fillet to the collar wall, so every fillet forms and
# the holes come out uniform. Add/remove a size above and this re-packs.
_HOLE_WALL = 2 * BORE_MOUTH_FILLET + 0.1
_COLLAR_WALL = BORE_MOUTH_FILLET + BASE_TOP_FILLET + 0.1
_FOOTPRINTS = [(f"{d:g}", _valley_r(d)) for d in DRILL_DIAMS] + [
    ("hex", CSK_HEAD_D / 2)
]
_POS = pack_holes(_FOOTPRINTS, COLLAR_W / 2, _HOLE_WALL, _COLLAR_WALL)

DRILL_BORES = [(d, *_POS[f"{d:g}"]) for d in DRILL_DIAMS]
HEX_BORES = [(CSK_HEX_AF, *_POS["hex"])]


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
