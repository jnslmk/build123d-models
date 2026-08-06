"""TPU grip-land sweep -- the coupon that settles ``drill_storage.flex``.

``flex`` grips a drill on a short plain land at the bottom of its TPU collar, and
``flex.config.LAND_FIT`` is currently ``for_material(PRESS, "tpu") -
LAND_EXTRA_GRIP`` -- i.e. 0.10 mm of modelled interference on top of whatever the
printer's own hole undersize adds. That is an argument, not a measurement: the fit
ladder in ``models/lib/fits`` models rigid-plastic *clearance* fits and says
nothing about an elastomer squeezing a steel shank, and its tightest class lands
on nominal in TPU, so the extra grip is off the end of the ladder entirely.

So this prints the same land at a range of offsets and lets a hand decide, which
is how ``RIB_GRIP`` was settled -- over three rounds, after two full holder
generations were printed on assumed numbers and both fought back (box.py:187-286).

**Print this in TPU**, flat, bores-up, no supports, with the same profile the
cartridge will use. Each bar carries its offset engraved on the back: a *positive*
offset is a wider hole (looser), negative is tighter. Push each drill in shank
first, as it sits in the holder. Judge the bar that holds the bit against a shake
but releases to a straight pull, then set ``LAND_FIT`` to
``fits.for_material(fits.PRESS, "tpu") + <that offset>`` and record the judgement
in ``flex/docs/design-notes.md``.

One bar reproduces the cartridge exactly (offset 0.00); the others shift every
hole on that bar by a fixed amount, so the correction curve can be *measured*
rather than assumed -- the same trick ``drill_fit_tester.small`` uses.
"""

from build123d import Align, Cone, Cylinder, Compound, Locations, Mode, Part, Pos

from ..drill_storage.flex import config as fc
from .frame import PLATE_H, coupon
from .sweep import BAR_GAP

# Offsets applied to LAND_FIT, one bar each -- so bar 0.00 *is* the collar. Skewed
# loose because the tight side is already covered twice over: the printer puts
# 0.1-0.3 mm of undersize on every bore, and LAND_EXTRA_GRIP adds 0.10 on top, so
# the nominal bar is expected to sit at or past the tight end of what is usable.
# In absolute terms these bars cut nominal -0.20 .. +0.20.
LAND_OFFSETS = [-0.10, 0.00, 0.10, 0.20, 0.30]


def cut_land_bores(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None,
    top_z: float,
    depth: float,
    offset: float = 0.0,
) -> None:
    """Cut the cartridge's land/relief bore profile into the active coupon.

    Matches ``drill_storage.flex.insert._cut_round_bore``: foot relief, land,
    lead-in cone, relieved guide -- so what the hand judges here is what the
    cartridge will actually do. ``top_z``/``depth`` come from the shared frame.
    """
    relief_z = fc.LAND_H + fc.LAND_LEAD_IN
    for d, x, y in bores:
        land_r = (d + fc.LAND_FIT + offset) / 2
        relief_r = (d + fc.RELIEF_FIT) / 2
        with Locations((x, y, 0.0)):
            Cylinder(
                land_r,
                fc.LAND_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
            Cone(
                land_r + fc.BORE_FOOT_RELIEF,
                land_r,
                fc.BORE_FOOT_RELIEF,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations((x, y, fc.LAND_H)):
            Cone(
                land_r,
                relief_r,
                fc.LAND_LEAD_IN,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations((x, y, relief_z)):
            Cylinder(
                relief_r,
                top_z - relief_z,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # Lead-in at the mouth, cut as a boolean cone -- never an OCC chamfer.
        with Locations((x, y, top_z - fc.CART_MOUTH_CH)):
            Cone(
                relief_r,
                relief_r + fc.CART_MOUTH_CH,
                fc.CART_MOUTH_CH,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    # Hex sockets are left out on purpose: a hex land bears on flats, wants its
    # own number (HEX_LAND_FIT), and there is only one hex tool in the set -- so
    # it is judged on the cartridge, not swept here.
    del hex_bores, depth


def bar_name(offset: float) -> str:
    """A per-bar label that survives export-filename sanitising.

    Not ``f"{offset:+.2f}"``: the exporter strips the sign and the dot, so
    ``-0.10`` and ``+0.10`` both become ``0_10`` and the second bar silently
    overwrites the first STL. Words instead of signs keep them distinct.
    """
    if offset < 0:
        return f"tight{abs(offset) * 100:03.0f}"
    if offset > 0:
        return f"loose{offset * 100:03.0f}"
    return "nominal"


def create_bar(offset: float) -> Part:
    """One coupon bar with every land shifted by ``offset`` mm diametral."""
    sign = "+" if offset >= 0 else "-"
    return coupon(
        lambda b, h, tz, dp: cut_land_bores(b, h, tz, dp, offset),
        f"drill_fit_tester.land_{bar_name(offset)}",
        f"LAND {sign}{abs(offset):.2f}",
    )


def create() -> Compound:
    """The whole sweep: one bar per offset, stacked front to back, loosest last."""
    bars = []
    for i, offset in enumerate(LAND_OFFSETS):
        bar = create_bar(offset)
        depth = bar.bounding_box().size.Y
        bars.append(Pos(0, i * (depth + BAR_GAP), 0) * bar)
    return Compound(label="drill_fit_tester.land", children=bars)


def report() -> str:
    """The land radius each bar cuts, per size -- handy when judging the prints."""
    lines = [
        f"PLATE_H {PLATE_H} mm, land {fc.LAND_H} mm, relief fit {fc.RELIEF_FIT:.2f} mm"
    ]
    for offset in LAND_OFFSETS:
        fit = fc.LAND_FIT + offset
        lines.append(f"  offset {offset:+.2f} -> bore = nominal {fit:+.2f} mm")
    return "\n".join(lines)


__all__ = [
    "LAND_OFFSETS",
    "bar_name",
    "create",
    "create_bar",
    "cut_land_bores",
    "report",
]
