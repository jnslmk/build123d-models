"""Grip-sweep coupons: one bar per candidate rib interference, all sizes on each.

The single-value fit tester answers "is *this* number right?". After two full
holders came back wrong in opposite directions, that is the wrong question --
what we actually need is to see the whole grip curve at once, in one print, with
the real bits in hand.

Each bar carries the same representative drill sizes (``SWEEP_DIAMS``) bored with
the production rib geometry, but a *different* ``RIB_GRIP`` (``SWEEP_GRIPS``).
The grip value is engraved on the back of each bar and the sizes on the front.
Print the bars, drop the bits in, and pick the bar that feels right -- then set
``RIB_GRIP`` in ``drill_storage.box`` to that number and the whole holder
follows. If no single bar is right across all sizes, the *pattern* of which bar
wins per size tells you whether the rib geometry (not the number) is still wrong.

Bar thickness is ``RIB_ZONE_H``, i.e. exactly the holder's rib band, so a bar
reproduces the real engagement length rather than a fraction of it -- the feel
transfers directly. Bits go in SHANK first, the same way they sit in the holder.

Each bar exports as its own STL, so you can print one, a few, or all -- and the
same file can be run in PLA/PETG and again in TPU to compare materials.

Prints flat, bores-up, no supports.
"""

from collections.abc import Callable

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

from .frame import (
    EDGE,
    HOLE_WALL,
    LABEL_PITCH,
    PLATE_CH,
    PLATE_R,
    engrave,
)
from ..drill_storage.box import (
    BASE_COLOR,
    HEX_GRIP,
    RIB_GRIP,
    grip_for,
    RIB_ZONE_H,
    rib_tip_r,
    rib_relief,
    cut_holes,
)
from ..drill_storage.wood import CSK_HEAD_D, CSK_HEX_AF

# A bar's grip is either one flat interference for every bore, or a law that
# varies it per diameter.
GripLaw = float | Callable[[float], float]

# Never cut a bore looser than this, whatever an offset would ask for -- below
# it the ribs stop touching the bit at all and the coupon reads nothing.
MIN_GRIP = 0.05

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
    return rib_tip_r(d, grip) + rib_relief(d, grip)


def create_bar(
    grip: GripLaw,
    diams: list[float] | None = None,
    layout_grip: GripLaw | None = None,
    title: str | None = None,
    label: str | None = None,
    with_hex: bool | None = None,
    hex_grip: float | None = None,
) -> Part:
    """One coupon of through-bored test holes.

    ``grip`` is either a single diametral interference for every bore, or a
    callable ``d -> grip`` when the bar tests a *law* rather than a flat value
    (that is how the small-bore coupon varies grip per size). A callable has no
    single number to stamp on the bar, so it needs an explicit ``title`` and
    ``label``. ``layout_grip`` is the grip the hole spacing is computed from --
    pass the loosest grip in the whole family so every bar shares one layout and
    stays comparable.

    ``hex_grip`` sets the socket on its own. Left None the hex takes the same
    law as the round bores, which is what a flat sweep wants: one raw value
    across every hole. A bar testing the *production* law must pass it, because
    the socket's production value is ``HEX_GRIP``, not ``grip_for()``.
    """
    diams = SWEEP_DIAMS if diams is None else diams
    with_hex = SWEEP_HEX if with_hex is None else with_hex
    if callable(grip):
        if title is None or label is None:
            raise ValueError("a callable grip needs an explicit title and label")
    else:
        title = title or f"{grip:.2f}"
        label = label or f"grip_{grip:.2f}".replace(".", "p")
    grip_of = grip if callable(grip) else (lambda _d, _g=grip: _g)
    if layout_grip is None:
        layout_grip = min(SWEEP_GRIPS)
    layout_of = (
        layout_grip if callable(layout_grip) else (lambda _d, _g=layout_grip: _g)
    )

    placed: list[list] = []
    c = 0.0
    prev_r = None
    keys = [(f"{d:g}", d, _valley_r(d, layout_of(d))) for d in diams]
    if with_hex:
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
        # production rib geometry at this bar's grip. cut_holes takes one grip
        # per call, so a per-size law is cut one bore at a time.
        for key, d, px, _ in placed:
            is_hex = key == "hex"
            bore_grip = hex_grip if is_hex and hex_grip is not None else grip_of(d)
            cut_holes(
                [] if is_hex else [(d, px, 0.0)],
                [(d, px, 0.0)] if is_hex else None,
                0.0,
                True,
                PLATE_H,
                PLATE_H,
                through=True,
                grip=bore_grip,
            )

        for key, d, px, _ in placed:
            engrave(key, (px, -half_w, z_mid), (1, 0, 0), (0, -1, 0))
        engrave(title, (0, half_w, z_mid), (-1, 0, 0), (0, 1, 0))

    bar.part.label = label
    bar.part.color = BASE_COLOR
    return bar.part


def lay_out(bars: list[Part], label: str) -> Compound:
    """Stack bars side by side; each child exports as its own STL."""
    pitch = max(b.bounding_box().size.Y for b in bars) + BAR_GAP
    y0 = -pitch * (len(bars) - 1) / 2
    return Compound(
        label=label,
        children=[Pos(0, y0 + i * pitch, 0) * b for i, b in enumerate(bars)],
    )


def create() -> Compound:
    """All sweep bars, laid out side by side (each exports as its own STL)."""
    return lay_out([create_bar(g) for g in SWEEP_GRIPS], "drill_fit_tester.sweep")


# --- Offset families ----------------------------------------------------------
# A second style of coupon: instead of sweeping a flat grip value, shift the
# *production law* by a fixed offset per bar. Once grip_for() stopped being a
# constant, a flat sweep could no longer answer "is the law right?" -- only a
# shifted law can. Used by drill_fit_tester.small and drill_fit_tester.full.


def grip_shifted(offset: float) -> Callable[[float], float]:
    """The round-bore production law, shifted by ``offset``, floored at MIN_GRIP."""
    return lambda d: max(MIN_GRIP, grip_for(d) + offset)


def hex_grip_shifted(offset: float) -> float:
    """The hex socket's production grip, shifted by ``offset``.

    The socket does NOT ride on ``grip_for()`` -- it has its own ``HEX_GRIP``
    (flats, not a curved wall). Shifting the round-bore law instead would cut
    every socket 0.03 loose, so the ``+0.00`` bar would really be a ``-0.03``
    bar and reading it would push HEX_GRIP the wrong way.
    """
    return max(MIN_GRIP, HEX_GRIP + offset)


def create_offset_bar(
    offset: float, diams: list[float], offsets: list[float], with_hex: bool
) -> Part:
    """One coupon cut with the production law shifted by ``offset``."""
    return create_bar(
        grip_shifted(offset),
        diams=diams,
        # Space every bar on the family's loosest grip so they share one hole
        # layout and stay directly comparable side by side.
        layout_grip=grip_shifted(min(offsets)),
        title=f"{offset:+.2f}",
        label=f"off_{offset:+.2f}".replace(".", "p")
        .replace("+", "p")
        .replace("-", "m"),
        with_hex=with_hex,
        hex_grip=hex_grip_shifted(offset),
    )


def create_offset_family(
    offsets: list[float], diams: list[float], with_hex: bool, label: str
) -> Compound:
    """A whole family of offset coupons, laid out side by side."""
    return lay_out(
        [create_offset_bar(o, diams, offsets, with_hex) for o in offsets], label
    )


def report_offsets(
    diams: list[float], offsets: list[float], with_hex: bool = False
) -> None:
    """Print the grip each bar will cut at each size -- the coupon's key."""
    for d in diams:
        shifted = ", ".join(f"{o:+.2f}->{grip_shifted(o)(d):.2f}" for o in offsets)
        print(f"{d:>5g} mm  production {grip_for(d):.2f}   bars: {shifted}")
    if with_hex:
        shifted = ", ".join(f"{o:+.2f}->{hex_grip_shifted(o):.2f}" for o in offsets)
        print(f"{'hex':>5} mm  production {HEX_GRIP:.2f}   bars: {shifted}")


def report() -> None:
    """Print the coupon's key: which grip each bar is cut at."""
    print(f"grip sweep {SWEEP_GRIPS} (current RIB_GRIP = {RIB_GRIP})")
