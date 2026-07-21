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
    COVER_COLOR,
    cover_height_for,
    create_base,
    create_cover,
    layout_bores,
)

LABEL = "Wood"  # material name embossed on the cover

# Drill sizes in the set (mm). Positions are auto-placed below, so you can add
# or remove a size and the layout re-packs itself. Bores are ribbed: the ribs
# grip a fixed absolute interference under every bit (see RIB_GRIP), and hold it
# on the plain shank near the bore floor -- no per-bore clearance to set here.
DRILL_DIAMS = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

# Longest brad-point drill in this set (the 10 mm), overall length in mm. The
# cover is sized to the *smallest* whole Gridfinity Z unit that still swallows a
# drill this long standing on the bore floor (see ``cover_height_for``): it just
# fits, and a longer drill would need one more 7 mm unit. We ask for only a tiny
# tip clearance (not the generic 6 mm headroom) so it lands on the true minimum
# unit -- 19U -- rather than wasting a whole unit on slack; the 7 mm quantisation
# then leaves ~3 mm above the tip anyway.
MAX_WOOD_DRILL_LEN = 121.0
COVER_TIP_CLEARANCE = 1.0  # min gap wanted above the longest tip when picking the unit
COVER_H_WOOD = cover_height_for(MAX_WOOD_DRILL_LEN, headroom=COVER_TIP_CLEARANCE)
#                                                  -> 109 mm cover, 19U assembled

# 10 mm countersink on a 6.3 mm hex shank: the socket holds the shank while the
# 10 mm head rests on the top face, so the packer reserves the head's footprint.
CSK_HEX_AF = 6.3  # measured across flats on the tool; the socket adds HEX_SLIP
#                   on top of that and grips on ribs at the bottom instead
CSK_HEAD_D = 10.0

# Positions are solved by the shared ``layout_bores``: the CSK is packed by its
# 10 mm head footprint but bored as a 6.3 mm hex socket, and swapped with the
# 10 mm drill so the CSK sits at a row edge while the 10 mm bore takes the centre
# slot. Their footprints are within 0.2 mm (10 -> 5.2, CSK head -> 5.0), so the
# trade keeps every wall clearance. Add/remove a size above and it re-packs.
DRILL_BORES, HEX_BORES, _ROWS, _POS = layout_bores(
    DRILL_DIAMS,
    hex_tools=[("CSK", CSK_HEX_AF, CSK_HEAD_D / 2)],
    swap=[("CSK", "10")],
)


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

    cover = create_cover(LABEL, cover_h=COVER_H_WOOD)
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
