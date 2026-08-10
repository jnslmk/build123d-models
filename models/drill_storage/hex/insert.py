"""The compliant half of a hex-bit box: a short black TPU cartridge of hex sockets.

The family's ``insert``, cut to this package's width. The argument is exactly
``drill_storage.insert``'s: a **collar**, not a block -- ``CART_H`` of TPU that
reaches as far below its retention bead as it stands above it -- and every hex
socket is cut by the family's own ``insert.hex_bore_tool``, so the land at the
bottom grips on ``HEX_LAND_FIT`` and the relief above it clears on
``RELIEF_FIT``, exactly as a countersink's or a step drill's shank is held in
the drill sets -- except that the land is this package's own, tightened by
``HEX_LAND_TIGHTEN`` because a socket here is named by ``HEX_AF`` rather than
by a shank (``config``'s "The grip"). The base guides a bit over its rigid bore
(14.2 mm ALLEN, 8.2 BITS); this grips it over 3.5 mm of land, which is the
whole point of the split.

Both boxes share the family's 35.68 mm cartridge; the only per-box number is
the socket mouths' lead-in chamfer, passed in (``config.box_fits`` says which
box gets which -- BITS shaves it from the family's 0.5 to 0.2, see
``config``).

Printed flat-bottom down, bores up, in black TPU, no supports. Every socket is
a through hole -- bits pass clean through into the base's guide below -- so
there is nothing to bridge and nothing to drain.
"""

from __future__ import annotations

from collections.abc import Sequence

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

from ...lib.edges import bottom_chamfer_tool
from ..box import hex_mouth_tool, rim_chamfer_tool, snap_bead_ring
from ..insert import hex_bore_tool as _family_hex_bore_tool
from . import config as c


def key_rib() -> Part:
    """The keying rib on the +X face.

    It stands *outside* the cartridge body, so it can never collide with a
    socket however the layout deals them, and rides in a matching slot in the
    base. Its whole job is to make the engraved legend on the base truthful: a
    rounded square would otherwise go in four ways and be right in one -- and a
    BITS cartridge is keyed too, because the socket grid and the base's guide
    bores have to agree on the same rotation.

    Its vertical edges are rounded and its bottom is lofted back to a lead-in --
    house rule, chamfer horizontal edges and fillet vertical ones, and the
    bottom is the end that goes in first.
    """
    depth = c.KEY_D + c.KEY_ROOT  # KEY_ROOT is buried in the cartridge wall
    x_mid = c.CART_W / 2 + c.KEY_D / 2 - c.KEY_ROOT / 2
    lead = c.KEY_LEAD_IN

    # Written out rather than factored into a helper: BuildSketch finds its
    # parent BuildPart by walking the call stack, so a sketch built inside a
    # nested function never lands in pending_faces and the loft gets no sections.
    with BuildPart() as rib:
        with BuildSketch(Plane.XY):
            with Locations((x_mid, 0)):
                RectangleRounded(
                    depth - 2 * lead,
                    c.KEY_W - 2 * lead,
                    max(c.KEY_FILLET - lead, 0.2),
                )
        with BuildSketch(Plane.XY.offset(lead)):
            with Locations((x_mid, 0)):
                RectangleRounded(depth, c.KEY_W, c.KEY_FILLET)
        loft(ruled=True)
        with BuildSketch(Plane.XY.offset(lead)):
            with Locations((x_mid, 0)):
                RectangleRounded(depth, c.KEY_W, c.KEY_FILLET)
        extrude(amount=c.CART_H - lead)
    return rib.part


def create_insert(
    hex_bores: Sequence[tuple[float, float, float]],
    mouth_ch: float,
) -> Part:
    """The TPU cartridge: a keyed collar of hex sockets, land at the bottom.

    ``hex_bores`` are ``(across_flats, x, y)`` in the base's coordinates -- pass
    the same tuples ``create_base`` was given, or the guides and the lands
    disagree about where a bit is. ``mouth_ch`` is the lead-in chamfer at the
    socket mouths on the top face (``CART_MOUTH_CH`` for ALLEN, the shaved
    ``BITS_CART_MOUTH_CH`` for BITS -- ``config.box_fits``). The cartridge
    width is the family's ``CART_W`` for both boxes.

    The sockets are cut by the family's ``insert.hex_bore_tool``: foot relief,
    land, lead-in, ``RELIEF_FIT`` relief. The one number it is not given
    straight is the land, which is this package's tightened ``HEX_LAND_FIT``
    (``config``'s "The grip") -- a socket here is named by ``HEX_AF``, not by a
    shank, so the family's fit would arrive carrying ``HEX_CLEARANCE`` on top.
    The mouth gets the family's hex frustum lead-in.

    Returned in print pose, flat bottom on ``z=0``. The cartridge's own z=0 is
    the base's ``CAVITY_FLOOR_Z``, so a feature at world z appears here at
    ``z - CAVITY_FLOOR_Z`` -- the bead included, which lands on
    ``CART_BELOW_BEAD`` and is therefore exactly halfway up.
    """
    with BuildPart() as cart:
        with BuildSketch(Plane.XY):
            RectangleRounded(c.CART_W, c.CART_W, c.CART_R)
        extrude(amount=c.CART_H)
        add(key_rib())

        # Retention bead: outward, so the compliant part carries it and seating
        # costs a squeeze rather than deflecting the rigid wall. Asymmetric ramp
        # (long lead-in below, short retention face above) for the reason in
        # box.snap_bead_ring -- a half-round bump fights the user going on.
        add(
            snap_bead_ring(
                c.CART_W,
                c.CART_R,
                c.CART_BELOW_BEAD,
                protrusion=c.CART_BEAD,
                lead_in=c.BEAD_LEAD_IN,
                back=c.BEAD_BACK,
                tip_flat=c.BEAD_TIP_FLAT,
                outward=True,
            )
        )

        # Chamfer the outer edges before the bores are cut, so both tools only
        # ever see the plain prism.
        add(
            rim_chamfer_tool(c.CART_W, c.CART_R, c.CART_H, c.SHELL_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        add(
            bottom_chamfer_tool(c.CART_W, c.CART_W, c.CART_R, 0.0, 0.4),
            mode=Mode.SUBTRACT,
        )

        for af, x, y in hex_bores:
            add(
                _family_hex_bore_tool(af, x, y, land_fit=c.HEX_LAND_FIT),
                mode=Mode.SUBTRACT,
            )

        # Lead-in at every mouth on the top face -- a *hex* frustum, not a cone.
        # A round cone cut into a hex hole only reaches the corners, leaving the
        # flats barely bevelled and a scalloped sharp rim between them. Note
        # what the shared tool takes: a circumradius, where a bore here is named
        # by its across-flats.
        for af, x, y in hex_bores:
            add(
                hex_mouth_tool((af + c.RELIEF_FIT) / 3**0.5, x, y, c.CART_H, mouth_ch),
                mode=Mode.SUBTRACT,
            )
    return cart.part


__all__ = ["create_insert", "key_rib"]
