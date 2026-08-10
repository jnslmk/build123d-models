"""The third printed part of a hex-bit box: the labelled translucent cover.

``box.create_cover`` at the family's 42 mm width: the same pillow-top, the
same snap bead, the same engraved label. Both boxes share the cover envelope
(41.5 mm, the pad itself, flush with the base) -- only the label, the height and the
glyph orientation differ, which is what the parameters are for.

``label_fit`` sizes the engraving, exactly as the old one-material hex module
did: the family's default reads *up* the face, which suits a tall cover, but a
short one is wider than it is tall, so turning the word to read *across* buys a
far bigger glyph. Whichever orientation allows the larger font wins, capped at
the family's ``LABEL_SIZE``.

Printed pillow-top down, mouth up, in translucent PETG, no supports.
"""

from __future__ import annotations

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Rotation,
    Text,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
)

from ...lib.edges import chamfer_edge
from ..box import (
    CAP_FILLET,
    CAP_H,
    COVER_SEAT_CH,
    COVER_WALL,
    INNER_R,
    MOUTH_CH,
    SNAP_PROTRUSION,
    SNAP_Z,
    TOP_FILLET,
    snap_bead_ring,
)
from . import config as c


def label_fit(cover_h: float, text: str) -> tuple[float, float, bool]:
    """Glyph size, vertical centre and orientation for a label on a cover face.

    Returns the largest the word can be printed, trying it both ways round: the
    family's default reads *up* the face, which suits a tall cover, but a short
    one is wider than it is tall, so turning the word to read *across* buys a far
    bigger glyph. Whichever orientation allows the larger font wins, capped at
    the family's ``LABEL_SIZE``.

    The word is measured rather than estimated from a characters-times-width rule
    -- glyph widths vary enough (a "1" against a "W") that a rule of thumb either
    overflows the face or wastes it.
    """
    probe = 10.0
    with BuildSketch() as sk:
        Text(text, font_size=probe)
    box = sk.sketch.bounding_box()
    run, thick = box.size.X / probe, box.size.Y / probe  # per 1 mm of font size

    bottom, top = 1.0, cover_h - TOP_FILLET  # flat face, under the pillow fillet
    height = top - bottom
    width = c.COVER_W - 2 * c.CORNER_R  # flat face between the rounded corners
    up = c.MARGIN * height / run  # reading up the face
    across = min(c.MARGIN * width / run, c.MARGIN * height / thick)  # reading across
    return min(c.LABEL_SIZE, max(up, across)), (bottom + top) / 2, across > up


def create_cover(
    label: str,
    cover_h: float,
    label_size: float,
    label_z: float,
    label_horizontal: bool = False,
    snap_protrusion: float = SNAP_PROTRUSION,
) -> Part:
    """A rounded-square cover with a pillow top and an engraved label.

    ``box.create_cover`` at the shared 41.5 mm width: the same bore, snap
    bead, mouth lead-in and label machinery. ``cover_h`` is the wall height --
    pass ``config.cover_h_for(bit_len)``. ``label_size`` / ``label_z`` /
    ``label_horizontal`` come from ``label_fit``.

    The label reads *up* the face by default, which is what a tall tube wants;
    ``label_horizontal`` turns it a quarter so it reads across the face instead.

    ``snap_protrusion`` is how far the snap bead stands into the bore, and it is
    a parameter because a *short* cover is a harder cover to open: the family's
    bead is levered off by a hand gripping a tall tube well above the mouth,
    while the 24 mm BITS cover can only be pinched right over the snap. Pass
    ``config.cover_snap_protrusion(name)`` -- the default is the family's, so the
    ALLEN cover and every base groove in the package are untouched.
    """
    inner_w = c.COVER_W - 2 * COVER_WALL
    with BuildPart() as cover:
        with BuildSketch():
            RectangleRounded(c.COVER_W, c.COVER_W, c.CORNER_R)
        extrude(amount=cover_h)
        # Round the top over into a pillow.
        fillet(cover.edges().group_by(Axis.Z)[-1], TOP_FILLET)
        # Chamfer the bottom outer edge so the open rim seats flush on the flat
        # base shoulder rather than overhanging the body edge (the cover is a
        # touch wider than the body). Doubles as elephant-foot relief, since the
        # cover prints open-end-down.
        chamfer(cover.edges().group_by(Axis.Z)[0], COVER_SEAT_CH)

        # Hollow: a single uniform bore (no step), open bottom to the solid cap.
        with BuildSketch():
            RectangleRounded(inner_w, inner_w, INNER_R)
        extrude(amount=cover_h - CAP_H, mode=Mode.SUBTRACT)
        # Small internal fillet where the bore ceiling meets the walls: relieves
        # stress at the cap join and eases the overhang printed under the cap.
        ceiling = cover.edges().filter_by_position(
            Axis.Z, cover_h - CAP_H, cover_h - CAP_H
        )
        if ceiling:
            fillet(ceiling, CAP_FILLET)

        # Lead-in at the mouth -- the *inner* rim of the open end, which is the
        # one edge on this part that ``chamfer(edges().group_by(Axis.Z)[0])``
        # above can never reach: it runs before the hollow is cut, so the only
        # bottom rim in existence then is the solid outer rectangle. Cut as a
        # lofted frustum rather than an OCC chamfer for the reasons recorded on
        # box.create_cover.
        with BuildSketch():
            RectangleRounded(
                inner_w + 2 * MOUTH_CH, inner_w + 2 * MOUTH_CH, INNER_R + MOUTH_CH
            )
        with BuildSketch(Plane.XY.offset(MOUTH_CH)):
            RectangleRounded(inner_w, inner_w, INNER_R)
        loft(ruled=True, mode=Mode.SUBTRACT)

        # Snap bead: a chamfered (ramped) ridge just inside the opening that
        # slides on gently and clicks into the groove on the base collar. Only
        # the protrusion is per-box; the ramp and the retention face keep the
        # family's runs, because what a withdrawal actually climbs is the
        # *groove's* 45 deg roof and that lives on the shared base.
        add(snap_bead_ring(inner_w, INNER_R, SNAP_Z, protrusion=snap_protrusion))

        # Engraved label on the +Y flat face -- reading up it, or across it when
        # ``label_horizontal``. Same plane logic as box.create_cover, so the
        # text never comes out mirrored.
        text_plane = Plane(
            origin=(0, c.COVER_W / 2, label_z),
            x_dir=(-1, 0, 0) if label_horizontal else (0, 0, 1),
            z_dir=(0, 1, 0),
        )
        with BuildSketch(text_plane):
            Text(label, font_size=label_size)
        extrude(amount=-c.LABEL_DEPTH, mode=Mode.SUBTRACT)
        # Chamfer the engraved mouths, best-effort -- the engraving stands on
        # its own if it fails (see the note on box.create_cover).
        mouth = (
            cover.edges()
            .filter_by_position(Axis.Y, c.COVER_W / 2, c.COVER_W / 2)
            .filter_by(lambda e: e.length < 30.0)
        )
        if mouth:
            chamfer_edge(cover, mouth, c.LABEL_CHAMFER)
    # Print orientation: flip the cover upside down (pillow top on the bed, open
    # mouth up) and re-seat on z=0 so it exports in the pose it prints in.
    part = Rotation(180, 0, 0) * cover.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


__all__ = ["create_cover", "label_fit"]
