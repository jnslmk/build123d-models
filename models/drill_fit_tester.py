"""Fit-test coupon for the ``drill_storage_metric`` bores.

A small flat strip carrying every drill bore (and the countersink hex socket)
from the Wood set at the *same* clearance, ribs and mouth fillet as the real
holder -- so you can print just this coupon to check bit fit and dial in
``BORE_CLEARANCE`` / ``CSK_HEX_AF`` without printing the whole base.

The bores run left-to-right in ascending size order, hex socket last. Prints
flat, bores-up, no supports.
"""

from build123d import (
    BuildPart,
    BuildSketch,
    Part,
    RectangleRounded,
    extrude,
)

from models.drill_storage_gridfinity import (
    BASE_COLOR,
    BORE_MOUTH_FILLET,
    RIB_RELIEF,
    cut_holes,
)
from models.drill_storage_metric import (
    BORE_CLEARANCE,
    CSK_HEAD_D,
    CSK_HEX_AF,
    DRILL_DIAMS,
)

TEST_DEPTH = 12.0  # bore depth in the coupon -- enough to feel the fit/grip
FLOOR = 2.0  # solid floor under the bores
PLATE_H = TEST_DEPTH + FLOOR
PLATE_R = 2.0  # coupon corner radius
HOLE_WALL = 2 * BORE_MOUTH_FILLET + 0.1  # both mouth fillets fit between holes
EDGE = BORE_MOUTH_FILLET + 1.0  # hole-to-edge margin (mouth fillet + a little)


def _valley_r(d: float) -> float:
    """Ribbed-bore cut (valley) radius for a bit of diameter ``d`` mm."""
    return (d + BORE_CLEARANCE) / 2 + RIB_RELIEF


def create() -> Part:
    """A flat coupon with one ribbed bore per drill size plus the hex socket."""
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

    plate_len = row_w + 2 * EDGE
    plate_wid = 2 * max_r + 2 * EDGE

    with BuildPart() as plate:
        with BuildSketch():
            RectangleRounded(plate_len, plate_wid, PLATE_R)
        extrude(amount=PLATE_H)
        cut_holes(plate, bores, hex_bores, BORE_CLEARANCE, True, PLATE_H, TEST_DEPTH)

    plate.part.label = "drill_fit_tester"
    plate.part.color = BASE_COLOR
    return plate.part


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester")


if __name__ == "__main__":
    main()
