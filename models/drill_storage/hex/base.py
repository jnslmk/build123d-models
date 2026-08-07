"""The rigid half of a hex-bit box: a Gridfinity base with a cavity + guide bores.

The family's ``shell``, cut to this package's own heights. The argument is the
same as ``drill_storage.shell`` -- the base **guides** a bit upright through
8.2 mm of rigid bore, and the TPU cartridge **grips** it; the guide never
touches the land's job. What differs is the geometry: a 30 mm base instead of
the family's 36 (a bit needs none of a drill's depth). Both boxes share the
family's 1x1 envelopes; the only per-box numbers are the guide's size and
mouth chamfer, passed in (``config.box_fits`` says which box gets which -- the
BITS box shaves both, see ``config``).

Printed foot down, cavity up, in black ASA, no supports. ASA wants an
enclosure; a 41.5 mm footprint is small enough that it is not fussy, but a
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
    COLLAR_R,
    SNAP_GROOVE_R,
    SNAP_Z,
    create_body,
    engrave_row_legend,
    gridfinity_foot,
    rim_chamfer_tool,
    snap_ring,
)
from ..shell import key_slot_tool
from . import config as c


def hex_guide_tool(guide_af: float, x: float, y: float, mouth_ch: float) -> Part:
    """One hex guide bore: a free-fit hex prism with a lead-in at its top mouth.

    ``shell.hex_guide_tool``, re-cut at this package's heights. The guide grips
    nothing -- its only job is to hold a bit upright over ``GUIDE_H`` so the
    short TPU collar above does not have to. It is cut at the box's own guide
    across-flats: ``HEX_AF + GUIDE_FIT`` (free) for ALLEN, the old one-material
    drop-in socket (``BITS_GUIDE_AF``) for BITS -- ``config.box_fits`` is the
    one place that decides.
    """
    r = guide_af / 3**0.5  # circumradius from across-flats
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(c.GUIDE_FLOOR_Z)):
            with Locations((x, y)):
                RegularPolygon(r, 6)
        extrude(amount=c.GUIDE_H)
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z - mouth_ch)):
            with Locations((x, y)):
                RegularPolygon(r, 6)
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            with Locations((x, y)):
                RegularPolygon(r + mouth_ch, 6)
        loft(ruled=True)
    return tool.part


def cavity_mouth_tool() -> Part:
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
            RectangleRounded(c.CAVITY_W, c.CAVITY_W, c.CAVITY_R)
        with BuildSketch(Plane.XY.offset(z_top)):
            RectangleRounded(c.CAVITY_W + 2 * ch, c.CAVITY_W + 2 * ch, c.CAVITY_R + ch)
        loft(ruled=True)
    return tool.part


def create_base(
    hex_bores: Sequence[tuple[float, float, float]],
    guide_af: float,
    guide_mouth_ch: float,
    rows: Sequence[Sequence[str]] | None = None,
    hole_pos: Mapping[str, tuple[float, float]] | None = None,
) -> Part:
    """The rigid base: Gridfinity foot, body, collar, cavity, guide bores.

    ``hex_bores`` are ``(across_flats, x, y)`` -- the same tuples the cartridge
    is built from, and must be, because the guide below and the land above are
    one hole in two materials (``config.socket_layout`` is the one call that
    decides where they are).

    ``guide_af`` is the across-flats the guides are cut at (loose, on purpose:
    the base keeps a bit straight and the cartridge grips it) and
    ``guide_mouth_ch`` their mouth chamfer -- both per box, from
    ``config.box_fits``. The horizontal envelope is the family's 1x1 set for
    both boxes (``config``); the heights and corner radii are shared too.
    ``rows`` and ``hole_pos`` come from ``config.socket_layout`` and engrave
    the size legend into the body walls; pass ``None`` for a box with no
    legend (BITS).

    Returned in print pose: foot on ``z=0``, cavity mouth up.
    """
    with BuildPart() as base:
        add(gridfinity_foot())

        # Full-width body up to the shoulder the cover seats on -- BODY_W wide,
        # so the base and the cover are one flush silhouette, and left a flat
        # shoulder for the cover's chamfered rim to land on. See box.create_body.
        add(create_body(c.BASE_FOOT_TOP))

        # Collar that plugs into the cover, with the cover's snap groove.
        with BuildSketch(Plane.XY.offset(c.BASE_FOOT_TOP)):
            RectangleRounded(c.COLLAR_W, c.COLLAR_W, COLLAR_R)
        extrude(amount=c.BASE_COLLAR_H)
        add(
            snap_ring(c.COLLAR_W, COLLAR_R, c.BASE_FOOT_TOP + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # The cartridge cavity -- only the top CAVITY_H, not the whole interior.
        # The cartridge drops in here and everything below it stays solid.
        with BuildSketch(Plane.XY.offset(c.CAVITY_FLOOR_Z)):
            RectangleRounded(c.CAVITY_W, c.CAVITY_W, c.CAVITY_R)
        extrude(amount=c.CAVITY_H, mode=Mode.SUBTRACT)

        # Guide bores, sunk from the cavity floor down to GUIDE_FLOOR_Z. A bit
        # bottoms out there -- on the rigid base, never on TPU, which would
        # creep under a point load -- so the cover math uses the same floor.
        for _af, x, y in hex_bores:
            add(hex_guide_tool(guide_af, x, y, guide_mouth_ch), mode=Mode.SUBTRACT)

        # Round groove that receives the cartridge's retention bead. Deliberately
        # far from the cover's groove so the two never thin the same ring of
        # collar wall -- GROOVE_SEPARATION pins that, like the family's.
        add(
            snap_ring(c.CAVITY_W, c.CAVITY_R, c.BEAD_Z, c.SHELL_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        add(key_slot_tool(c), mode=Mode.SUBTRACT)
        add(cavity_mouth_tool(), mode=Mode.SUBTRACT)
        add(
            rim_chamfer_tool(c.COLLAR_W, COLLAR_R, c.BASE_TOTAL_H, c.SHELL_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )

        if rows and hole_pos:
            engrave_row_legend(rows, hole_pos, c.LEGEND_Z, c.LEGEND_LINE_H)
    return base.part


__all__ = [
    "cavity_mouth_tool",
    "create_base",
    "hex_guide_tool",
]
