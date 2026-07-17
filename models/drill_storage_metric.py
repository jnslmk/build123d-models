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
    BASE_TOP_CHAMFER,
    BORE_MOUTH_CHAMFER,
    COLLAR_R,
    COLLAR_W,
    COVER_COLOR,
    create_base,
    create_cover,
    pack_holes,
    ribbed_valley_r,
)

LABEL = "Wood"  # material name embossed on the cover

# Drill sizes in the set (mm). Positions are auto-placed below, so you can add
# or remove a size and the layout re-packs itself. Bores are ribbed: the ribs
# grip a fixed *fraction* under each bit (see RIB_UNDERSIZE), so the grip is
# proportional across sizes -- no per-bore clearance to set here.
DRILL_DIAMS = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

# 10 mm countersink on a 6.3 mm hex shank: the socket holds the shank while the
# 10 mm head rests on the top face, so the packer reserves the head's footprint.
CSK_HEX_AF = 6.4  # 6.3 mm shank + ~0.1 mm across-flats clearance (snug drop-in)
CSK_HEAD_D = 10.0

# Auto-placement: keep two mouth fillets of wall between holes, and one mouth
# fillet plus the top-rim fillet to the collar wall, so every fillet forms and
# the holes come out uniform. Add/remove a size above and this re-packs.
_HOLE_WALL = 2 * BORE_MOUTH_CHAMFER + 0.1
# Extra margin past (mouth + rim fillet) so the one-piece rim fillet reliably
# forms even with every perimeter hole pinned to the same wall gap.
_COLLAR_WALL = BORE_MOUTH_CHAMFER + BASE_TOP_CHAMFER + 0.4
_FOOTPRINTS = [(f"{d:g}", ribbed_valley_r(d)) for d in DRILL_DIAMS] + [
    ("hex", CSK_HEAD_D / 2)
]
_POS = pack_holes(_FOOTPRINTS, COLLAR_W / 2, COLLAR_R, _HOLE_WALL, _COLLAR_WALL)

DRILL_BORES = [(d, *_POS[f"{d:g}"]) for d in DRILL_DIAMS]
HEX_BORES = [(CSK_HEX_AF, *_POS["hex"])]


def create() -> Compound:
    """The base for the drill set + countersink, with its matching cover."""
    base = create_base(DRILL_BORES, hex_bores=HEX_BORES, clearance=0.0, ribbed=True)
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
