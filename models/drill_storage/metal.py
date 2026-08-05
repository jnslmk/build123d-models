"""Gridfinity drill storage sized for a 1-10 mm metal (HSS twist) drill set plus
a 10 mm hex-shank insert.

A sibling of ``drill_storage.wood`` built on the very same square Gridfinity
base/cover engine from ``drill_storage.box`` -- only the inputs differ: a
1x1 base holding ten graduated drills (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10 mm)
plus a 10 mm across-flats hex-shank insert dropping into a hex socket, and a
matching labelled cover that snaps over it.

Holes are laid out in rows by ``pack_rows`` -- largest -> smallest, with each row
holding smaller bits than the one behind it -- so the set reads as an ordered
grid. Each row's sizes are engraved as a legend into the four body walls, so you
can read the sizes from any side. Edit ``DRILL_DIAMS`` and it re-packs.

The cover height is derived in the engine from ``MAX_DRILL_LEN`` (132 mm), so the
assembled holder already encloses a 132 mm drill standing on the bore floor --
no length change needed here.

Change ``LABEL`` to relabel the cover for your material.
"""

from build123d import Compound, Pos

from .box import (
    BASE_COLOR,
    COVER_COLOR,
    create_base,
    create_cover,
    layout_bores,
)

LABEL = "Metal"  # material name embossed on the cover

# Drill sizes in the set (mm). Positions are auto-placed below, so you can add
# or remove a size and the layout re-packs itself. Bores are ribbed: the ribs
# grip a fixed absolute interference under every bit (see RIB_GRIP), and hold it
# on the plain shank near the bore floor -- no per-bore clearance to set here.
DRILL_DIAMS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]

# 10 mm across-flats hex-shank tap: the shank drops straight into a hex socket.
# A touch of across-flats clearance for a snug drop-in fit. Labelled "TAP" on the
# walls (this hex tool is a tap in the metal set, not a plain hex insert).
HEX_AF = 10.1  # 10 mm hex shank + ~0.1 mm across-flats clearance
HEX_LABEL = "TAP"  # wall legend for the hex socket

# Positions are solved by the shared ``layout_bores``. The hex socket's footprint
# is just its circumradius (af / sqrt(3)) -- there is no wider head resting on top,
# unlike the countersink in ``drill_storage.wood``. Add/remove a size above and it
# re-packs.
DRILL_BORES, HEX_BORES, _ROWS, _POS = layout_bores(
    DRILL_DIAMS,
    hex_tools=[(HEX_LABEL, HEX_AF, HEX_AF / 3**0.5)],
)


def create() -> Compound:
    """The base for the metal drill set + hex insert, with its matching cover."""
    base = create_base(
        DRILL_BORES,
        hex_bores=HEX_BORES,
        clearance=0.0,
        ribbed=True,
        rows=_ROWS,
        hole_pos=_POS,
    )
    base.label = "base_1_10mm_hex"
    base.color = BASE_COLOR

    cover = create_cover(LABEL)
    cover.label = f"cover_{LABEL.lower()}"
    cover.color = COVER_COLOR

    return Compound(
        label="drill_storage.metal",
        children=[Pos(-26, 0, 0) * base, Pos(26, 0, 0) * cover],
    )
