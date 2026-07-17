"""Fit-test coupon for the ``drill_storage_metric`` bores.

A small flat strip carrying every drill bore (and the countersink hex socket)
from the Wood set at the *same* clearance, ribs and mouth fillet as the real
holder -- so you can print just this coupon to check bit fit and dial in
``BORE_CLEARANCE`` / ``CSK_HEX_AF`` without printing the whole base. Each hole is
labelled with its size, and it's kept shallow (about half the holder's bore
depth) to save filament.

Prints flat, bores-up, no supports.
"""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Locations,
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

TEST_DEPTH = 6.0  # bore depth -- ~half the holder's, still enough to feel the fit
FLOOR = 1.5  # solid floor under the bores
PLATE_H = TEST_DEPTH + FLOOR  # 7.5 mm total
PLATE_R = 2.0  # coupon corner radius
PLATE_CH = 0.5  # chamfer on the top + bottom plate edges (bottom = foot relief)
HOLE_WALL = 2 * BORE_MOUTH_CHAMFER + 0.1  # both mouth fillets fit between holes
EDGE = BORE_MOUTH_CHAMFER + 1.0  # hole/label-to-edge margin
LABEL_TEXT = 2.5  # engraved label glyph height
LABEL_DEPTH = 0.4  # engrave depth
LABEL_GAP = 1.2  # gap between a hole's bottom and its label


def _valley_r(d: float) -> float:
    """Ribbed-bore cut (valley) radius for a bit of diameter ``d`` mm."""
    return (d + BORE_CLEARANCE) / 2 + RIB_RELIEF


def create() -> Part:
    """A flat, labelled coupon with one ribbed bore per drill size + the hex."""
    # (key, footprint radius) in a row, ascending size, hex last.
    items = [(f"{d:g}", _valley_r(d)) for d in sorted(DRILL_DIAMS)]
    items.append(("hex", CSK_HEAD_D / 2))

    # Lay out along X with fillet-aware pitch, then centre the row on the origin.
    xs: list[tuple[str, float, float]] = []
    x = 0.0
    for key, r in items:
        xs.append((key, x + r, r))
        x += 2 * r + HOLE_WALL
    row_w = x - HOLE_WALL
    shift = row_w / 2
    max_r = max(r for _, _, r in xs)

    bores = [(float(key), px - shift, 0.0) for key, px, r in xs if key != "hex"]
    hex_bores = [(CSK_HEX_AF, px - shift, 0.0) for key, px, r in xs if key == "hex"]
    # Label the hex with its across-flats size, the rest with the drill diameter.
    labels = [("6.3" if key == "hex" else key, px - shift) for key, px, r in xs]

    # Holes sit at y=0; labels run in a band below. Size the plate to enclose both.
    label_y = -(max_r + LABEL_GAP + LABEL_TEXT / 2)
    top = max_r + EDGE
    bottom = label_y - LABEL_TEXT / 2 - EDGE
    plate_len = row_w + 2 * EDGE

    with BuildPart() as plate:
        with BuildSketch():
            with Locations((0, (top + bottom) / 2)):
                RectangleRounded(plate_len, top - bottom, PLATE_R)
        extrude(amount=PLATE_H)
        # Chamfer top + bottom outer edges; the bottom chamfer doubles as
        # elephant-foot relief since the coupon prints floor-down.
        chamfer(plate.edges().group_by(Axis.Z)[0], PLATE_CH)
        chamfer(plate.edges().group_by(Axis.Z)[-1], PLATE_CH)

        # Ribbed bores + hex socket + mouth fillets -- identical to the holder.
        cut_holes(bores, hex_bores, BORE_CLEARANCE, True, PLATE_H, TEST_DEPTH)

        # Engrave the size under each hole.
        with BuildSketch(Plane.XY.offset(PLATE_H)):
            for text, lx in labels:
                with Locations((lx, label_y)):
                    Text(text, LABEL_TEXT)
        extrude(amount=-LABEL_DEPTH, mode=Mode.SUBTRACT)

    plate.part.label = "drill_fit_tester"
    plate.part.color = BASE_COLOR
    return plate.part


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester")


if __name__ == "__main__":
    main()
