"""The rigid half: an ASA Gridfinity shell that holds a TPU cartridge.

Set-agnostic: hand it a layout and it cuts that layout. The three sets each own a
thin module (``wood.shell``, ``metal.shell``, ``stone.shell``) that supplies one
from ``sets.py`` and nothing else.

Everything that has to keep its shape lives here -- the Gridfinity foot, the
body, the collar with the cover's snap groove, the engraved size legend, the
cavity the cartridge drops into, and the guide bores under it.

The shell **guides**; the TPU collar **grips**. Those are different jobs wanting
different stiffness, so they are in different parts and different materials: the
guides are cut at ``GUIDE_FIT`` (free -- they hold a drill upright over 23.2 mm
and must not rub), and the collar's land is cut at interference. Changing drill
sets is still only a cartridge reprint as far as the *grip* goes, but the guides
live here, so a genuinely different set needs both halves.

36 mm tall, not the 42 mm of a one-material base: the bores no longer come down
from the top face, so the height above the cover seat only has to hold the
collar. The seat itself stays at 24 mm, which is what keeps every cover in this
package interchangeable with every shell.

Printed foot-down, cavity up, in ASA, no supports. ASA wants an enclosure; a
42 mm footprint is small enough that it is not fussy, but a draughty room will
still lift the foot's corners.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    RegularPolygon,
    add,
    extrude,
    loft,
)

from .box import (
    BASE_H,
    COLLAR_R,
    COLLAR_W,
    CORNER_R,
    PAD,
    SNAP_GROOVE_R,
    SNAP_Z,
    WALL_LABEL_Z,
    engrave_row_legend,
    gridfinity_foot,
    rim_chamfer_tool,
    snap_ring,
)
from . import config as c
from .sets import DrillSet


def cavity_mouth_tool() -> Part:
    """A subtract tool that 45-deg-chamfers the *inner* rim of the cavity mouth.

    The cartridge's lead-in (part-joints rule 1: a lead-in on every mating
    mouth). Built as a loft-and-subtract rather than an OCC chamfer for the same
    reason ``rim_chamfer_tool`` is -- an edge op on this rim is unreliable, and a
    failed one corrupts the builder so every later one fails silently.
    """
    z_top = c.SHELL_TOTAL_H
    ch = c.CAVITY_MOUTH_CH
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_top - ch)):
            RectangleRounded(c.CAVITY_W, c.CAVITY_W, c.CAVITY_R)
        with BuildSketch(Plane.XY.offset(z_top)):
            RectangleRounded(c.CAVITY_W + 2 * ch, c.CAVITY_W + 2 * ch, c.CAVITY_R + ch)
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


def guide_bore_tool(d: float, x: float, y: float) -> Part:
    """One ASA guide bore: a free-fit cylinder with a lead-in at its top mouth.

    The guide grips nothing. Its only job is to hold a drill upright over
    ``GUIDE_H`` so the short TPU collar above does not have to, which is why it is
    cut at ``GUIDE_FIT`` (free) rather than anywhere near the collar's land -- and
    at free *plus* the undersize FDM prints a hole at, because a nominal free fit
    in a 23.2 mm bore arrives as a drag the drill has to be pushed past.

    Its mouth chamfer is ``GUIDE_MOUTH_CH``, not the base's 0.8 mm: this layout is
    packed tighter than the PETG base's, and at 0.8 two neighbouring mouths would
    intersect and leave a sharp sliver in the cavity floor.
    """
    r = (d + c.GUIDE_FIT) / 2
    with BuildPart() as tool:
        with Locations((x, y, c.GUIDE_FLOOR_Z)):
            Cylinder(r, c.GUIDE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((x, y, c.CAVITY_FLOOR_Z - c.GUIDE_MOUTH_CH)):
            Cone(
                r,
                r + c.GUIDE_MOUTH_CH,
                c.GUIDE_MOUTH_CH,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    return tool.part


def hex_guide_tool(af: float, x: float, y: float) -> Part:
    """The hex-shank equivalent of ``guide_bore_tool``.

    The mouth is a lofted hex frustum rather than a cone: a round cone cut into a
    hex hole only reaches the corners and leaves the flats unbevelled.
    """
    r = (af + c.GUIDE_FIT) / 3**0.5  # circumradius from across-flats
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(c.GUIDE_FLOOR_Z)):
            with Locations((x, y)):
                RegularPolygon(r, 6)
        extrude(amount=c.GUIDE_H)
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z - c.GUIDE_MOUTH_CH)):
            with Locations((x, y)):
                RegularPolygon(r, 6)
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            with Locations((x, y)):
                RegularPolygon(r + c.GUIDE_MOUTH_CH, 6)
        loft(ruled=True)
    return tool.part


def create_shell(
    bores: Sequence[tuple[float, float, float]] | None = None,
    hex_bores: Sequence[tuple[float, float, float]] | None = None,
    rows: Sequence[Sequence[str]] | None = None,
    hole_pos: Mapping[str, tuple[float, float]] | None = None,
) -> Part:
    """The ASA shell: Gridfinity foot, body, collar, guide bores, and the cavity.

    ``bores`` / ``hex_bores`` are the same tuples the cartridge is built from, and
    must be, because the guide below and the land above are one hole in two
    materials. They are cut at ``GUIDE_FIT`` -- loose, on purpose: the shell is
    the part that keeps a drill straight and the collar is the part that grips it,
    and a guide that gripped would fight the collar for the fit.

    ``rows`` (hole keys per row, biggest row first) and ``hole_pos``
    (``{key: (x, y)}``) come straight from ``layout_bores`` and engrave the size
    legend into the body walls. The cartridge is keyed so the legend can only ever
    be read against the layout it describes.

    Returned in print pose: foot on ``z=0``, cavity mouth up.
    """
    with BuildPart() as shell:
        add(gridfinity_foot())

        # Full-width body up to the shoulder the cover seats on. Left a flat
        # shoulder (no chamfer) so the cover's chamfered bottom rim seats flush
        # on it -- box.create_cover's COVER_SEAT_CH has the argument.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(PAD, PAD, CORNER_R)
        extrude(amount=c.SHELL_FOOT_TOP - BASE_H)

        # Collar that plugs into the cover, with the cover's snap groove.
        with BuildSketch(Plane.XY.offset(c.SHELL_FOOT_TOP)):
            RectangleRounded(COLLAR_W, COLLAR_W, COLLAR_R)
        extrude(amount=c.SHELL_COLLAR_H)
        add(
            snap_ring(COLLAR_W, COLLAR_R, c.SHELL_FOOT_TOP + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # The cartridge cavity -- only the top CAVITY_H, not the whole interior.
        # The collar drops in here and everything below it stays solid ASA.
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            RectangleRounded(c.CAVITY_W, c.CAVITY_W, c.CAVITY_R)
        extrude(amount=c.CAVITY_H, mode=Mode.SUBTRACT)

        # Guide bores, sunk from the cavity floor down to GUIDE_FLOOR_Z. A drill
        # still bottoms out at BORE_FLOOR_Z -- on ASA, never on TPU, which would
        # creep under a point load -- so the cover math is untouched.
        for d, x, y in bores or []:
            add(guide_bore_tool(d, x, y), mode=Mode.SUBTRACT)
        for af, x, y in hex_bores or []:
            add(hex_guide_tool(af, x, y), mode=Mode.SUBTRACT)

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
            rim_chamfer_tool(COLLAR_W, COLLAR_R, c.SHELL_TOTAL_H, c.SHELL_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )

        if rows and hole_pos:
            engrave_row_legend(rows, hole_pos, WALL_LABEL_Z)
    return shell.part


def create_shell_for(drill_set: DrillSet) -> Part:
    """The shell for one ``sets.DrillSet``, labelled and coloured.

    The set's ``bores``/``hex_bores`` are the same tuples ``create_insert_for``
    is handed, and must be: the guide below and the land above are one hole in
    two materials, and only one call to ``layout_bores`` ever decides where it
    is.
    """
    shell = create_shell(
        drill_set.bores,
        hex_bores=drill_set.hex_bores,
        rows=drill_set.rows,
        hole_pos=drill_set.pos,
    )
    shell.label = f"shell_asa_{drill_set.name}"
    shell.color = c.SHELL_COLOR
    return shell


__all__ = [
    "cavity_mouth_tool",
    "create_shell",
    "create_shell_for",
    "guide_bore_tool",
    "hex_guide_tool",
    "key_slot_tool",
]
