"""The rigid half: an ASA Gridfinity shell that holds a TPU cartridge.

Everything that has to keep its shape lives here -- the Gridfinity foot, the
body, the collar with the cover's snap groove, the engraved size legend and the
cavity the cartridge drops into. It has no drill bores at all: gripping a drill
is the cartridge's whole job, and the two are separated so that changing drill
sets is a cartridge reprint rather than a whole base reprint.

Printed foot-down, cavity up, in ASA, no supports. ASA wants an enclosure; a
42 mm footprint is small enough that it is not fussy, but a draughty room will
still lift the foot's corners.
"""

from __future__ import annotations

from build123d import (
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    add,
    extrude,
    loft,
)

from ..box import (
    BASE_H,
    BASE_TOTAL_H,
    COLLAR_H,
    COLLAR_R,
    COLLAR_W,
    CORNER_R,
    FOOT_TOP,
    PAD,
    SNAP_GROOVE_R,
    SNAP_Z,
    WALL_LABEL_Z,
    engrave_row_legend,
    gridfinity_foot,
    layout_bores,
    rim_chamfer_tool,
    snap_ring,
)
from ..wood import CSK_HEAD_D, CSK_HEX_AF, DRILL_DIAMS
from . import config as c


def cavity_mouth_tool() -> Part:
    """A subtract tool that 45-deg-chamfers the *inner* rim of the cavity mouth.

    The cartridge's lead-in (part-joints rule 1: a lead-in on every mating
    mouth). Built as a loft-and-subtract rather than an OCC chamfer for the same
    reason ``rim_chamfer_tool`` is -- an edge op on this rim is unreliable, and a
    failed one corrupts the builder so every later one fails silently.
    """
    z_top = c.BASE_TOTAL_H
    ch = c.CAVITY_MOUTH_CH
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_top - ch)):
            RectangleRounded(c.CAVITY_W, c.CAVITY_W, c.CAVITY_R)
        with BuildSketch(Plane.XY.offset(z_top)):
            RectangleRounded(
                c.CAVITY_W + 2 * ch, c.CAVITY_W + 2 * ch, c.CAVITY_R + ch
            )
        loft(ruled=True)
    return tool.part


def key_slot_tool() -> Part:
    """The slot in the +X cavity wall that receives the cartridge's key rib.

    Runs the full cavity height so the rib slides past the retention bead, and
    reaches ``KEY_D`` into the wall. It cuts a 2.0 mm wall down to 1.0 mm over a
    ``KEY_W`` arc on the one face that carries no legend.
    """
    over = 0.5  # start inside the cavity so the boolean has no coincident face
    depth = c.KEY_D + over
    x_mid = c.CAVITY_W / 2 + c.KEY_D / 2 - over / 2
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            with Locations((x_mid, 0)):
                # Rounded, so the slot leaves the cavity wall filleted vertical
                # edges rather than two raw corners.
                RectangleRounded(depth, c.KEY_W + c.KEY_SLIP, c.KEY_FILLET)
        extrude(amount=c.CAVITY_H)
    return tool.part


def create_shell(
    rows: list[list[str]] | None = None,
    hole_pos: dict[str, tuple[float, float]] | None = None,
) -> Part:
    """The ASA shell: Gridfinity foot, body, collar, and an open cartridge cavity.

    ``rows`` (hole keys per row, biggest row first) and ``hole_pos``
    (``{key: (x, y)}``) come straight from ``layout_bores`` and engrave the size
    legend into the body walls, so the shell still tells you what is in each
    column even though it holds none of the drills itself. The cartridge is keyed
    so the legend can only ever be read against the layout it describes.

    Returned in print pose: foot on ``z=0``, cavity mouth up.
    """
    with BuildPart() as shell:
        add(gridfinity_foot())

        # Full-width body up to the shoulder the cover seats on. Left a flat
        # shoulder (no chamfer) so the cover's chamfered bottom rim seats flush
        # on it -- box.py:1052-1054 has the argument.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(PAD, PAD, CORNER_R)
        extrude(amount=FOOT_TOP - BASE_H)

        # Collar that plugs into the cover, with the cover's snap groove.
        with BuildSketch(Plane.XY.offset(FOOT_TOP)):
            RectangleRounded(COLLAR_W, COLLAR_W, COLLAR_R)
        extrude(amount=COLLAR_H)
        add(
            snap_ring(COLLAR_W, COLLAR_R, FOOT_TOP + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # The cartridge cavity, open to the top. Its floor is BORE_FLOOR_Z, so a
        # drill still bottoms out at the same height it does on the PETG base --
        # on ASA, never on TPU, which would creep under a point load.
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            RectangleRounded(c.CAVITY_W, c.CAVITY_W, c.CAVITY_R)
        extrude(amount=c.CAVITY_H, mode=Mode.SUBTRACT)

        # Round groove that receives the cartridge's retention bead. Deliberately
        # far from the cover's groove (z=30) so the two never thin the same ring
        # of collar wall.
        add(
            snap_ring(c.CAVITY_W, c.CAVITY_R, c.BEAD_Z, c.SHELL_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        add(key_slot_tool(), mode=Mode.SUBTRACT)
        add(cavity_mouth_tool(), mode=Mode.SUBTRACT)
        add(
            rim_chamfer_tool(COLLAR_W, COLLAR_R, BASE_TOTAL_H, c.SHELL_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )

        if rows and hole_pos:
            engrave_row_legend(rows, hole_pos, WALL_LABEL_Z)
    return shell.part


# The wood set's layout, packed into the *cartridge's* envelope rather than the
# collar's, and by the relieved bore each drill really cuts. Shared with
# ``insert`` so the two halves cannot disagree about where a hole is.
DRILL_BORES, HEX_BORES, ROWS, POS = layout_bores(
    DRILL_DIAMS,
    hex_tools=[("CSK", CSK_HEX_AF, CSK_HEAD_D / 2)],
    swap=[("CSK", "10")],
    footprint_r=c.relieved_bore_r,
    half_w=c.PACK_HALF_W,
    corner_r=c.PACK_CORNER_R,
    hole_wall=c.PACK_HOLE_WALL,
    wall_clearance=c.PACK_WALL_CLEARANCE,
)


def create() -> Part:
    """Model entry point: the ASA shell for the wood drill set."""
    shell = create_shell(rows=ROWS, hole_pos=POS)
    shell.label = "shell_asa"
    shell.color = c.SHELL_COLOR
    return shell


__all__ = [
    "DRILL_BORES",
    "HEX_BORES",
    "POS",
    "ROWS",
    "cavity_mouth_tool",
    "create",
    "create_shell",
    "key_slot_tool",
]
