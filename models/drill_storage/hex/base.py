"""The rigid half of a hex-bit box: a Gridfinity base with a cavity + guide bores.

The family's ``shell``, cut to this package's own heights and footprints. The
argument is the same as ``drill_storage.shell`` -- the base **guides** a bit
upright through 8.2 mm of rigid bore, and the TPU cartridge **grips** it; the
guide is cut at ``GUIDE_FIT`` (free) and never touches the land's job. What
differs is the geometry: a 30 mm base instead of the family's 36 (a bit needs
none of a drill's depth), and two footprints -- 1x1 for the ALLEN box, 2x2 for
the BITS box. The corner radii, the grooves, the cavity and the key slot are
the family's; only the widths are passed in.

Printed foot down, cavity up, in black ASA, no supports. ASA wants an
enclosure; a 41.5-83.5 mm footprint is small enough that it is not fussy, but a
draughty room will still lift a corner.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from build123d import (
    BuildPart,
    BuildSketch,
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

from ..box import (
    BASE_H,
    COLLAR_R,
    CORNER_R,
    FOOT_C1,
    FOOT_C3,
    FOOT_STRAIGHT,
    SNAP_GROOVE_R,
    SNAP_Z,
    engrave_row_legend,
    rim_chamfer_tool,
    snap_ring,
)
from . import config as c


def gridfinity_foot(pad: float, corner_r: float) -> Part:
    """The standard Gridfinity foot profile, at any pad size.

    ``box.gridfinity_foot`` cut from its 1x1 constant; a 2x2 pad gets the same
    chamfered profile (0.7/1.8/1.9 mm steps) around the longer perimeter.
    """
    bottom = pad - 2 * (FOOT_C1 + FOOT_C3)
    mid = pad - 2 * FOOT_C3
    r_bottom = corner_r - (FOOT_C1 + FOOT_C3)
    r_mid = corner_r - FOOT_C3
    with BuildPart() as foot:
        for size, radius, z in [
            (bottom, r_bottom, 0.0),
            (mid, r_mid, FOOT_C1),
            (mid, r_mid, FOOT_C1 + FOOT_STRAIGHT),
            (pad, corner_r, BASE_H),
        ]:
            with BuildSketch(Plane.XY.offset(z)):
                RectangleRounded(size, size, radius)
        loft(ruled=True)
    return foot.part


def hex_guide_tool(af: float, x: float, y: float) -> Part:
    """One hex guide bore: a free-fit hex prism with a lead-in at its top mouth.

    ``shell.hex_guide_tool``, re-cut at this package's heights. The guide grips
    nothing -- its only job is to hold a bit upright over ``GUIDE_H`` so the
    short TPU collar above does not have to -- which is why it is cut at
    ``GUIDE_FIT`` (free) rather than anywhere near the collar's land.
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


def cavity_mouth_tool(cavity_w: float) -> Part:
    """A subtract tool that 45-deg-chamfers the *inner* rim of the cavity mouth.

    The cartridge's lead-in (part-joints rule 1: a lead-in on every mating
    mouth), built as a loft-and-subtract rather than an OCC chamfer for the same
    reason ``rim_chamfer_tool`` is -- an edge op on this rim is unreliable, and
    a failed one corrupts the builder so every later one fails silently.
    """
    z_top = c.BASE_TOTAL_H
    ch = c.CAVITY_MOUTH_CH
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z_top - ch)):
            RectangleRounded(cavity_w, cavity_w, c.CAVITY_R)
        with BuildSketch(Plane.XY.offset(z_top)):
            RectangleRounded(cavity_w + 2 * ch, cavity_w + 2 * ch, c.CAVITY_R + ch)
        loft(ruled=True)
    return tool.part


def key_slot_tool(cavity_w: float) -> Part:
    """The slot in the +X cavity wall that receives the cartridge's key rib.

    Runs the full cavity height so the rib slides past the retention bead, and
    reaches ``KEY_D`` into the wall. It cuts a 2.0 mm wall down to 1.0 mm over a
    ``KEY_W`` arc on the one face that carries no legend.
    """
    over = 0.5  # start inside the cavity so the boolean has no coincident face
    depth = c.KEY_D + over
    x_mid = cavity_w / 2 + c.KEY_D / 2 - over / 2
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            with Locations((x_mid, 0)):
                # Rounded, so the slot leaves the cavity wall filleted vertical
                # edges rather than two raw corners.
                RectangleRounded(depth, c.KEY_W + c.KEY_SLIP, c.KEY_FILLET)
        extrude(amount=c.CAVITY_H)
    return tool.part


def create_base(
    hex_bores: Sequence[tuple[float, float, float]],
    pad: float,
    collar_w: float,
    cavity_w: float,
    rows: Sequence[Sequence[str]] | None = None,
    hole_pos: Mapping[str, tuple[float, float]] | None = None,
) -> Part:
    """The rigid base: Gridfinity foot, body, collar, cavity, guide bores.

    ``hex_bores`` are ``(across_flats, x, y)`` -- the same tuples the cartridge
    is built from, and must be, because the guide below and the land above are
    one hole in two materials (``config.socket_layout`` is the one call that
    decides where they are). They are cut at ``GUIDE_FIT`` -- loose, on purpose:
    the base is the part that keeps a bit straight and the cartridge is the part
    that grips it.

    ``pad`` / ``collar_w`` / ``cavity_w`` are the box's horizontal envelope
    (``ALLEN_*`` or ``BITS_*`` in ``config``); the heights and corner radii are
    shared by both boxes and live in ``config``. ``rows`` and ``hole_pos`` come
    from ``config.socket_layout`` and engrave the size legend into the body
    walls; pass ``None`` for a box with no legend (BITS).

    Returned in print pose: foot on ``z=0``, cavity mouth up.
    """
    with BuildPart() as base:
        add(gridfinity_foot(pad, CORNER_R))

        # Full-width body up to the shoulder the cover seats on. Left a flat
        # shoulder (no chamfer) so the cover's chamfered bottom rim seats flush
        # on it -- box.create_cover's COVER_SEAT_CH has the argument.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(pad, pad, CORNER_R)
        extrude(amount=c.BASE_FOOT_TOP - BASE_H)

        # Collar that plugs into the cover, with the cover's snap groove.
        with BuildSketch(Plane.XY.offset(c.BASE_FOOT_TOP)):
            RectangleRounded(collar_w, collar_w, COLLAR_R)
        extrude(amount=c.BASE_COLLAR_H)
        add(
            snap_ring(collar_w, COLLAR_R, c.BASE_FOOT_TOP + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # The cartridge cavity -- only the top CAVITY_H, not the whole interior.
        # The cartridge drops in here and everything below it stays solid.
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            RectangleRounded(cavity_w, cavity_w, c.CAVITY_R)
        extrude(amount=c.CAVITY_H, mode=Mode.SUBTRACT)

        # Guide bores, sunk from the cavity floor down to GUIDE_FLOOR_Z. A bit
        # bottoms out there -- on the rigid base, never on TPU, which would
        # creep under a point load -- so the cover math uses the same floor.
        for af, x, y in hex_bores:
            add(hex_guide_tool(af, x, y), mode=Mode.SUBTRACT)

        # Round groove that receives the cartridge's retention bead. Deliberately
        # far from the cover's groove so the two never thin the same ring of
        # collar wall -- GROOVE_SEPARATION pins that, like the family's.
        add(
            snap_ring(cavity_w, c.CAVITY_R, c.BEAD_Z, c.SHELL_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        add(key_slot_tool(cavity_w), mode=Mode.SUBTRACT)
        add(cavity_mouth_tool(cavity_w), mode=Mode.SUBTRACT)
        add(
            rim_chamfer_tool(collar_w, COLLAR_R, c.BASE_TOTAL_H, c.SHELL_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )

        if rows and hole_pos:
            engrave_row_legend(rows, hole_pos, c.LEGEND_Z, c.LEGEND_LINE_H)
    return base.part


__all__ = [
    "cavity_mouth_tool",
    "create_base",
    "gridfinity_foot",
    "hex_guide_tool",
    "key_slot_tool",
]
