"""Fit-test coupon for the ``drill_storage_metric`` bores.

A small flat strip carrying every drill bore (and the countersink hex socket)
from the Wood set at the *same* clearance, ribs and mouth chamfer as the real
holder -- so you can print just this coupon to check bit fit and dial in
``BORE_CLEARANCE`` / ``CSK_HEX_AF`` without printing the whole base. Each hole is
labelled (raised text) with its size, and it's kept shallow (about half the
holder's bore depth) to save filament.

Prints flat, bores-up, no supports.
"""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Locations,
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
LABEL_TEXT = 3.5  # label glyph height
LABEL_HEIGHT = 0.6  # raised (embossed) -- reads better than a shallow engrave
LABEL_PITCH = 7.5  # min hole centre spacing so the size labels don't crowd
LABEL_GAP = 1.5  # gap between a hole's bottom and its label


def _valley_r(d: float) -> float:
    """Ribbed-bore cut (valley) radius for a bit of diameter ``d`` mm."""
    return (d + BORE_CLEARANCE) / 2 + RIB_RELIEF


def create() -> Part:
    """A flat, labelled coupon with one ribbed bore per drill size + the hex."""
    items = [(f"{d:g}", _valley_r(d)) for d in sorted(DRILL_DIAMS)]
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

    # Holes sit at y=0; labels run in a band below. Size the plate to enclose both.
    label_y = -(max_r + LABEL_GAP + LABEL_TEXT / 2)
    top = max_r + EDGE
    bottom = label_y - LABEL_TEXT / 2 - EDGE
    plate_len = (max_x - min_x) + 2 * EDGE

    with BuildPart() as plate:
        with BuildSketch():
            with Locations((0, (top + bottom) / 2)):
                RectangleRounded(plate_len, top - bottom, PLATE_R)
        extrude(amount=PLATE_H)
        # Chamfer top + bottom outer edges; the bottom chamfer doubles as
        # elephant-foot relief since the coupon prints floor-down.
        chamfer(plate.edges().group_by(Axis.Z)[0], PLATE_CH)
        chamfer(plate.edges().group_by(Axis.Z)[-1], PLATE_CH)

        # Ribbed bores + hex socket + mouth chamfers -- identical to the holder,
        # but bored all the way through (no floor).
        cut_holes(
            bores, hex_bores, BORE_CLEARANCE, True, PLATE_H, PLATE_H, through=True
        )

        # Raised size label under each hole (embossed reads better than engraved).
        with BuildSketch(Plane.XY.offset(PLATE_H)):
            for text, lx in labels:
                with Locations((lx, label_y)):
                    Text(text, LABEL_TEXT)
        extrude(amount=LABEL_HEIGHT)

    plate.part.label = "drill_fit_tester"
    plate.part.color = BASE_COLOR
    return plate.part


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester")


if __name__ == "__main__":
    main()
