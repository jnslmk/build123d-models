"""Gridfinity drill storage sized for a 2-10 mm wood/brad-point drill set plus a
10 mm hex-shank countersink.

A ready-to-print pair built on the square Gridfinity base/cover from
``drill_storage_gridfinity``: a 1x1 base holding eleven graduated drills
(2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10 mm) plus a 10 mm countersink bit with a
6.3 mm hex shank, and a matching labelled cover that snaps over it.

Holes are laid out in rows by ``pack_rows`` -- largest -> smallest, with each row
holding smaller bits than the one behind it -- so the set reads as an ordered
grid. Each row's sizes are engraved as a legend into the four body walls, so you
can read the sizes from any side. Edit ``DRILL_DIAMS`` and it re-packs. The
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
    pack_rows,
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
CSK_HEX_AF = 6.3  # 6.3 mm shank, no clearance -> a tighter grip on the hex shank
CSK_HEAD_D = 10.0

# Row layout: minimum spacing used to grade holes into rows, and the minimum
# clearance every hole keeps to the collar wall (a mouth chamfer + the top-rim
# chamfer + margin, so both lead-ins still form). Holes are then spread out to
# fill the collar. Add/remove a size above and this re-packs.
_HOLE_WALL = 2 * BORE_MOUTH_CHAMFER + 0.1
_WALL_CLEARANCE = BORE_MOUTH_CHAMFER + BASE_TOP_CHAMFER + 0.4
_ITEMS = [(f"{d:g}", ribbed_valley_r(d)) for d in DRILL_DIAMS] + [
    ("CSK", CSK_HEAD_D / 2)
]
_POS, _ROWS = pack_rows(_ITEMS, COLLAR_W / 2, COLLAR_R, _HOLE_WALL, _WALL_CLEARANCE)

# Swap the countersink and the 10 mm drill so the CSK sits at the row edge and
# the 10 mm bore takes the centre slot. Their footprints are within 0.2 mm
# (10 -> 5.2, CSK head -> 5.0), so trading places keeps every wall clearance.
_POS["CSK"], _POS["10"] = _POS["10"], _POS["CSK"]

DRILL_BORES = [(d, *_POS[f"{d:g}"]) for d in DRILL_DIAMS]
HEX_BORES = [(CSK_HEX_AF, *_POS["CSK"])]


def create() -> Compound:
    """The base for the drill set + countersink, with its matching cover."""
    base = create_base(
        DRILL_BORES,
        hex_bores=HEX_BORES,
        clearance=0.0,
        ribbed=True,
        rows=_ROWS,
        hole_pos=_POS,
    )
    base.label = "base_2_10mm_csk"
    base.color = BASE_COLOR

    cover = create_cover(LABEL)
    cover.label = f"cover_{LABEL.lower()}"
    cover.color = COVER_COLOR

    return Compound(
        label="drill_storage_wood",
        children=[Pos(-26, 0, 0) * base, Pos(26, 0, 0) * cover],
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_storage_wood")


if __name__ == "__main__":
    main()
