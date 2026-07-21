"""Grip-sweep coupons: one bar per candidate rib interference, all sizes on each.

The single-value fit tester answers "is *this* number right?". After two full
holders came back wrong in opposite directions, that is the wrong question --
what we actually need is to see the whole grip curve at once, in one print, with
the real bits in hand.

Each bar carries the same representative drill sizes (``SWEEP_DIAMS``) bored with
the production rib geometry, but a *different* ``RIB_GRIP`` (``SWEEP_GRIPS``).
The grip value is engraved on the back of each bar and the sizes on the front.
Print the bars, drop the bits in, and pick the bar that feels right -- then set
``RIB_GRIP`` in ``drill_storage_gridfinity`` to that number and the whole holder
follows. If no single bar is right across all sizes, the *pattern* of which bar
wins per size tells you whether the rib geometry (not the number) is still wrong.

Bar thickness is ``RIB_ZONE_H``, i.e. exactly the holder's rib band, so a bar
reproduces the real engagement length rather than a fraction of it -- the feel
transfers directly. Bits go in SHANK first, the same way they sit in the holder.

Each bar exports as its own STL, so you can print one, a few, or all -- and the
same file can be run in PLA/PETG and again in TPU to compare materials.

Prints flat, bores-up, no supports.
"""

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Compound,
    Part,
    Pos,
    RectangleRounded,
    chamfer,
    extrude,
)

from models.drill_fit_tester import (
    EDGE,
    HOLE_WALL,
    LABEL_PITCH,
    PLATE_CH,
    PLATE_R,
    _engrave,
)
from models.drill_storage_gridfinity import (
    BASE_COLOR,
    RIB_GRIP,
    RIB_ZONE_H,
    _rib_tip_r,
    _rib_relief,
    cut_holes,
)
from models.drill_storage_wood import CSK_HEAD_D, CSK_HEX_AF

# Representative sizes spanning the set. Both ends matter: the small bores are
# where the old law went too tight and the big ones where it went too loose.
SWEEP_DIAMS = [2.0, 4.0, 6.0, 8.0, 10.0]

# The countersink's hex socket rides on the same RIB_GRIP as the round bores, so
# it belongs on the same coupon -- one bar settles the whole tray, hex included.
SWEEP_HEX = True

# Candidate interferences (mm on diameter), bracketing the current RIB_GRIP.
# Spaced 0.08 apart -- fine enough to pick a winner, coarse enough that the
# difference between neighbouring bars is actually perceptible by hand.
SWEEP_GRIPS = [0.14, 0.22, 0.30, 0.38, 0.46]

PLATE_H = RIB_ZONE_H  # bar thickness == the holder's rib band, so the feel matches
BAR_GAP = 6.0  # spacing between bars when shown/exported as one assembly


def _valley_r(d: float, grip: float) -> float:
    """Cut footprint of a bore at a given grip -- used for spacing the row."""
    return _rib_tip_r(d, grip) + _rib_relief(d, grip)


def create_bar(grip: float) -> Part:
    """One coupon bored at ``grip`` (diametral interference), all sweep sizes."""
    # Space the row on the sweep's *smallest* grip, which is its widest cut, so
    # every bar shares one hole layout -- bars stay comparable and stack neatly.
    layout_grip = min(SWEEP_GRIPS)
    placed: list[list] = []
    c = 0.0
    prev_r = None
    keys = [(f"{d:g}", d, _valley_r(d, layout_grip)) for d in SWEEP_DIAMS]
    if SWEEP_HEX:
        # Packed on the head, which overhangs the socket and rests on the face.
        keys.append(("hex", CSK_HEX_AF, CSK_HEAD_D / 2))
    for key, d, r in keys:
        if prev_r is not None:
            c += max(prev_r + r + HOLE_WALL, LABEL_PITCH)
        placed.append([key, d, c, r])
        prev_r = r
    min_x = placed[0][2] - placed[0][3]
    max_x = placed[-1][2] + placed[-1][3]
    mid_x = (min_x + max_x) / 2
    for e in placed:
        e[2] -= mid_x
    max_r = max(r for _, _, _, r in placed)

    half_w = max_r + EDGE
    bar_len = (max_x - min_x) + 2 * EDGE
    z_mid = PLATE_H / 2

    with BuildPart() as bar:
        with BuildSketch():
            RectangleRounded(bar_len, 2 * half_w, PLATE_R)
        extrude(amount=PLATE_H)
        chamfer(bar.edges().group_by(Axis.Z)[0], PLATE_CH)
        chamfer(bar.edges().group_by(Axis.Z)[-1], PLATE_CH)

        # Through-bored so a bit can be pushed back out from underneath, with the
        # production rib geometry at this bar's grip.
        cut_holes(
            [(d, px, 0.0) for k, d, px, _ in placed if k != "hex"],
            [(d, px, 0.0) for k, d, px, _ in placed if k == "hex"],
            0.0,
            True,
            PLATE_H,
            PLATE_H,
            through=True,
            grip=grip,
        )

        for key, d, px, _ in placed:
            _engrave(key, (px, -half_w, z_mid), (1, 0, 0), (0, -1, 0))
        _engrave(f"{grip:.2f}", (0, half_w, z_mid), (-1, 0, 0), (0, 1, 0))

    bar.part.label = f"grip_{grip:.2f}".replace(".", "p")
    bar.part.color = BASE_COLOR
    return bar.part


def create() -> Compound:
    """All sweep bars, laid out side by side (each exports as its own STL)."""
    bars = [create_bar(g) for g in SWEEP_GRIPS]
    pitch = max(b.bounding_box().size.Y for b in bars) + BAR_GAP
    y0 = -pitch * (len(bars) - 1) / 2
    return Compound(
        label="drill_fit_tester_sweep",
        children=[Pos(0, y0 + i * pitch, 0) * b for i, b in enumerate(bars)],
    )


def main() -> None:
    from export import display_and_export

    print(f"grip sweep {SWEEP_GRIPS} (current RIB_GRIP = {RIB_GRIP})")
    display_and_export(create(), "drill_fit_tester_sweep")


if __name__ == "__main__":
    main()
