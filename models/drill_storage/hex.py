"""Gridfinity storage for a 16-piece 1/4" hex-shank bit set -- 8 long + 8 short.

The one **one-material** holder left in this package. The drill sets are an ASA
shell plus a TPU cartridge, because a drill has to be gripped; a 25 mm driver bit
standing 10 mm proud of a socket does not. So this is still a plain PETG base
from ``box.create_base``, and every hole is a hex socket rather than a round
bore: the bits all share the same 6.35 mm (1/4") across-flats shank, so they drop
straight into a pocket and are held by the flats and their own weight.

Two boxes, one per bit family:

* **ALLEN** -- the 50 mm hex-key bits, sizes 1.5 / 2 / 2.5 / 3 / 4 / 5 / 6 / 8.
  Those sizes are engraved into the body walls, laid out in rows largest ->
  smallest like the drill variants, so the set reads as an ordered grid.
* **BITS** -- the 25 mm driver bits (Torx, Phillips, Pozidriv, slotted, ...).
  A mixed bag with no single size scale to engrave, so the walls stay blank and
  you read the tip itself -- which is exactly what's left standing proud.

The split isn't a styling choice: a 6.5 mm socket reserves a 3.75 mm
circumradius, so the 39.2 mm collar takes at most 3 per row and ~3 rows -- 8
holes. Asking ``pack_rows`` for all 16 silently overlaps them (it only warns
about *horizontal* overpacking), so 8 per box is the real ceiling.

Sockets are only ``SOCKET_DEPTH`` (15 mm) deep -- enough to hold a bit upright
and no more -- which lets the base itself come down to 28 mm (4U) instead of the
family's 42 mm, and leaves every bit standing well proud to pinch out:

    ALLEN (50 mm bits): floor at z=13, 35 mm proud, 52 mm cover -> 70 mm (10U)
    BITS  (25 mm bits): floor at z=13, 10 mm proud, 24 mm cover -> 42 mm (6U)
"""

from build123d import BuildSketch, Compound, Pos, Text

from .box import (
    BASE_COLOR,
    BASE_H,
    CORNER_R,
    COVER_COLOR,
    COVER_W,
    LABEL_SIZE,
    TOP_FILLET,
    WALL_LABEL_SIZE,
    cover_height_for,
    create_base,
    create_cover,
    layout_bores,
)

# 1/4" hex shank. Nothing here is compliant, so the fit lives entirely in this
# across-flats clearance: enough that a bit drops in and lifts out one-handed, not
# so much that it rattles. (A drill set cannot be held this way, which is what the
# TPU cartridge next door exists for -- but a driver bit only has to stand up.)
HEX_SHANK_AF = 6.35  # nominal 1/4" across-flats
# Diametral allowance (added straight across the flats, like a bore-diameter
# formula -- not doubled, so it's already the total gap). Sits between
# fits.SNUG (0.10 mm, PETG baseline) and fits.SLIDING (0.22 mm, PETG
# baseline), closer to SNUG. Deliberately tighter than a round SLIDING bore
# would need: a hex socket's flat sides don't suffer the concave-arc
# undersizing a round bore does (fdm-fits-and-clearances Rule 4 -- the nozzle
# dragging the inner perimeter inward is an arc effect), so less allowance
# still drops a bit in and lifts it out one-handed without rattling.
HEX_CLEARANCE = 0.15  # across-flats allowance -> slip fit
HEX_AF = HEX_SHANK_AF + HEX_CLEARANCE

# A bit only needs enough socket to stand up straight and not tip; past that the
# hole is just swallowing the tool. 15 mm is a little over two shank widths --
# plenty of guidance -- and shallow bores are what let the base be short.
SOCKET_DEPTH = 15.0

# Base: 28 mm (4U) rather than the family's 42 mm, since nothing is buried deep.
# That is as low as this base goes while keeping everything it needs:
#   * 13 mm of solid under the socket floor, so the bores stop above the foot;
#   * a collar whose snap groove (SNAP_Z = 6 above the shoulder) still has
#     several mm of rim above it rather than sitting at the edge;
#   * a body wall tall enough to carry the three-row ALLEN size legend at the
#     house minimum glyph height -- this is the binding constraint. Dropping to
#     3U (21 mm) would leave ~7.6 mm of wall, too little for three rows, so the
#     sizes would have to come off the wall entirely.
BASE_FOOT_TOP = 18.0  # shoulder the cover seats on
BASE_COLLAR_H = 10.0  # collar that plugs into the cover
BASE_TOTAL_H = BASE_FOOT_TOP + BASE_COLLAR_H
SOCKET_FLOOR_Z = BASE_TOTAL_H - SOCKET_DEPTH

# The legend has to be re-fitted to the shortened body: centred on the wall
# (BASE_H..BASE_FOOT_TOP) and with the rows pitched just far enough apart that
# three of them fit between the foot and the shoulder.
LEGEND_MARGIN = 0.6  # clear space kept above/below the block of rows
LEGEND_ROWS = 3
LEGEND_GLYPH_H = 0.75 * WALL_LABEL_SIZE  # build123d renders digits at ~0.75 * size
LEGEND_Z = (BASE_H + BASE_FOOT_TOP) / 2
LEGEND_LINE_H = ((BASE_FOOT_TOP - BASE_H - 2 * LEGEND_MARGIN) - LEGEND_GLYPH_H) / (
    LEGEND_ROWS - 1
)

# Pick each cover on the true minimum Gridfinity unit (see ``drill_storage.wood``):
# ask only for a tip clearance rather than the generic headroom, so the 7 mm
# quantisation isn't pushed up a whole unit by slack it doesn't need.
COVER_TIP_CLEARANCE = 1.0

MARGIN = 0.9  # fraction of a face a label may span, so it never runs to the edge

# Metric hex-key sizes in the 50 mm set, largest first -- the packer deals them
# into rows in this order, so the biggest land in the back row like the drill
# variants. The 25 mm driver bits are a mixed bag (Torx/PH/PZ/slotted) with no
# common scale, so that box carries no legend.
ALLEN_SIZES = [8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5]
BITS_PER_BOX = len(ALLEN_SIZES)

# (cover label, bit length, wall-legend keys or None)
BOXES = [
    ("ALLEN", 50.0, [f"{s:g}" for s in ALLEN_SIZES]),
    ("BITS", 25.0, None),
]


def _sockets(keys: list[str] | None):
    """Eight evenly spread hex sockets; returns ``(hex_bores, rows, positions)``.

    All eight are identical, so the shared packer just spreads them over the
    collar. ``keys`` names them for the wall legend; without it they get
    placeholder names and no legend is engraved.
    """
    names = keys or [f"H{i}" for i in range(BITS_PER_BOX)]
    _, hex_bores, rows, pos = layout_bores(
        [], hex_tools=[(n, HEX_AF, HEX_AF / 3**0.5) for n in names]
    )
    return hex_bores, rows, pos


def _label_fit(cover_h: float, text: str) -> tuple[float, float, bool]:
    """Glyph size, vertical centre and orientation for a label on a cover face.

    Returns the largest the word can be printed, trying it both ways round: the
    family's default reads *up* the face, which suits a tall cover, but a short
    one is wider than it is tall, so turning the word to read *across* buys a far
    bigger glyph (on the 24 mm BITS cover, 13 mm instead of ~7 mm). Whichever
    orientation allows the larger font wins, capped at the family's ``LABEL_SIZE``.

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
    width = COVER_W - 2 * CORNER_R  # flat face between the rounded corners
    up = MARGIN * height / run  # reading up the face
    across = min(MARGIN * width / run, MARGIN * height / thick)  # reading across
    return min(LABEL_SIZE, max(up, across)), (bottom + top) / 2, across > up


def create() -> Compound:
    """Both hex-bit boxes: a base + matching cover for each bit family."""
    children = []
    for i, (label, bit_len, keys) in enumerate(BOXES):
        hex_bores, rows, pos = _sockets(keys)
        x = -26 + 52 * i

        base = create_base(
            [],
            hex_bores=hex_bores,
            rows=rows if keys else None,
            hole_pos=pos if keys else None,
            bore_depth=SOCKET_DEPTH,
            foot_top=BASE_FOOT_TOP,
            collar_h=BASE_COLLAR_H,
            label_z=LEGEND_Z,
            label_line_h=LEGEND_LINE_H,
        )
        base.label = f"base_{label.lower()}"
        base.color = BASE_COLOR

        cover_h = cover_height_for(
            bit_len,
            headroom=COVER_TIP_CLEARANCE,
            bore_floor_z=SOCKET_FLOOR_Z,
            foot_top=BASE_FOOT_TOP,
        )
        label_size, label_z, horizontal = _label_fit(cover_h, label)
        cover = create_cover(
            label,
            cover_h=cover_h,
            label_size=label_size,
            label_z=label_z,
            label_horizontal=horizontal,
        )
        cover.label = f"cover_{label.lower()}"
        cover.color = COVER_COLOR

        children += [Pos(x, -30, 0) * base, Pos(x, 30, 0) * cover]

    return Compound(label="drill_storage.hex", children=children)
