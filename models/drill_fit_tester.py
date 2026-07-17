"""Fit-test coupons for the ``drill_storage_metric`` bores.

A small flat, through-bored strip carrying every drill size (and the countersink
hex socket) so you can dial in fit by printing just the coupon instead of the
whole holder. Each hole is labelled (engraved) with its size and the coupon
carries an engraved variant title.

This module holds the shared ``_coupon`` frame plus the **ribbed** variant
(``create``). Two siblings reuse the frame:

* ``drill_fit_tester_plain``  -- nominal holes, no ribs (tune via slicer comp).
* ``drill_fit_tester_taper``  -- every hole slightly tapered (self-centring).

Prints flat, bores-up, no supports.
"""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    RectangleRounded,
    Text,
    chamfer,
    extrude,
)

from models.drill_storage_gridfinity import (
    BASE_COLOR,
    BORE_MOUTH_CHAMFER,
    RIB_RELIEF,
    cut_holes,
)
from models.drill_storage_metric import (
    BORE_CLEARANCE,
    CSK_HEAD_D,
    CSK_HEX_AF,
    DRILL_DIAMS,
)

PLATE_H = 7.5  # coupon thickness -- bores go all the way through (no floor)
PLATE_R = 2.0  # coupon corner radius
PLATE_CH = 0.5  # chamfer on the top + bottom plate edges (bottom = foot relief)
HOLE_WALL = 2 * BORE_MOUTH_CHAMFER + 0.1  # both mouth chamfers fit between holes
EDGE = BORE_MOUTH_CHAMFER + 1.0  # hole/label-to-edge margin
LABEL_TEXT = 4.5  # label glyph height (big enough to read when engraved)
LABEL_DEPTH = 0.8  # engraved (recessed) -- raised thin text gets slicer-dropped
LABEL_PITCH = 8.5  # min hole centre spacing so the size labels don't crowd


def _layout_r(d: float) -> float:
    """Layout footprint radius per size -- the ribbed valley, so all three
    coupons share one hole layout regardless of how they cut the holes."""
    return (d + BORE_CLEARANCE) / 2 + RIB_RELIEF


def _engrave(text: str, origin, x_dir, z_dir) -> None:
    """Engrave ``text`` ``LABEL_DEPTH`` into the active part's face at ``origin``,
    reading along ``x_dir`` with outward face normal ``z_dir``."""
    with BuildSketch(Plane(origin=origin, x_dir=x_dir, z_dir=z_dir)) as sk:
        Text(text, LABEL_TEXT)
    extrude(sk.sketch, amount=-LABEL_DEPTH, mode=Mode.SUBTRACT)


def _coupon(cut_fn, part_label: str, title: str) -> Part:
    """Build a labelled, through-bored fit-test coupon.

    ``cut_fn(bores, hex_bores, top_z, depth)`` cuts the holes into the active
    part (each variant supplies its own); the frame, labels and title are shared.
    """
    items = [(f"{d:g}", _layout_r(d)) for d in sorted(DRILL_DIAMS)]
    items.append(("hex", CSK_HEAD_D / 2))

    # Place hole centres left-to-right: at least a mouth-chamfer wall apart, and
    # at least LABEL_PITCH apart so each size label has room beneath it.
    placed: list[list] = []
    c = 0.0
    prev_r = None
    for key, r in items:
        if prev_r is not None:
            c += max(prev_r + r + HOLE_WALL, LABEL_PITCH)
        placed.append([key, c, r])
        prev_r = r
    min_x = placed[0][1] - placed[0][2]
    max_x = placed[-1][1] + placed[-1][2]
    mid_x = (min_x + max_x) / 2
    for e in placed:
        e[1] -= mid_x  # centre the row on the origin
    max_r = max(r for _, _, r in placed)

    bores = [(float(k), px, 0.0) for k, px, r in placed if k != "hex"]
    hex_bores = [(CSK_HEX_AF, px, 0.0) for k, px, r in placed if k == "hex"]
    labels = [("6.3" if k == "hex" else k, px) for k, px, r in placed]

    # Narrow strip: holes at y=0, text engraved on the long side faces to save
    # space -- size labels on the front (-Y), the variant title on the back (+Y).
    half_w = max_r + EDGE
    plate_len = (max_x - min_x) + 2 * EDGE
    z_mid = PLATE_H / 2

    with BuildPart() as plate:
        with BuildSketch():
            RectangleRounded(plate_len, 2 * half_w, PLATE_R)
        extrude(amount=PLATE_H)
        # Chamfer top + bottom outer edges; the bottom chamfer doubles as
        # elephant-foot relief since the coupon prints floor-down.
        chamfer(plate.edges().group_by(Axis.Z)[0], PLATE_CH)
        chamfer(plate.edges().group_by(Axis.Z)[-1], PLATE_CH)

        cut_fn(bores, hex_bores, PLATE_H, PLATE_H)

        # Engraved (a recess always prints; thin raised text gets slicer-dropped).
        for text, lx in labels:
            _engrave(text, (lx, -half_w, z_mid), (1, 0, 0), (0, -1, 0))
        _engrave(title, (0, half_w, z_mid), (-1, 0, 0), (0, 1, 0))

    plate.part.label = part_label
    plate.part.color = BASE_COLOR
    return plate.part


def create() -> Part:
    """Ribbed variant -- the holder's real geometry (3 ribs grip the bit)."""
    return _coupon(
        lambda b, h, tz, dp: cut_holes(
            b, h, BORE_CLEARANCE, True, tz, dp, through=True
        ),
        "drill_fit_tester",
        "RIBBED",
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester")


if __name__ == "__main__":
    main()
