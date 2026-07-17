"""Tapered-hole fit-test coupon -- a sibling of ``drill_fit_tester``.

Every hole (including the hex socket) is a slight taper: a little clearance at
the top and slightly undersized at the bottom. A bit slides in from the top and
wedges / self-centres at the depth where the taper matches its true diameter --
so the fit self-adjusts to the bit and to print variation, no ribs needed. Bored
through, so a bit that runs deep just pokes out the bottom.
"""

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cone,
    Locations,
    Mode,
    Part,
    Plane,
    RegularPolygon,
    add,
    loft,
)

from models.drill_fit_tester import _coupon

TAPER_TOP = 0.1  # diametral clearance at the top of each hole
TAPER_BOTTOM = 0.1  # diametral undersize at the bottom of each hole
_EXT = 1.0  # extend the cut past both faces for a clean through-cut


def _hex_frustum(
    af: float, x: float, y: float, floor: float, top_z: float, depth: float
) -> Part:
    """A tapered hex prism (subtract tool): AF-TAPER_BOTTOM at the bottom,
    AF+TAPER_TOP at the top, extended past both faces."""
    r_bot = (af - TAPER_BOTTOM) / 3**0.5  # circumradius at the bottom
    r_top = (af + TAPER_TOP) / 3**0.5
    slope = (r_top - r_bot) / depth
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(floor - _EXT)):
            with Locations((x, y)):
                RegularPolygon(r_bot - slope * _EXT, 6)
        with BuildSketch(Plane.XY.offset(top_z + _EXT)):
            with Locations((x, y)):
                RegularPolygon(r_top + slope * _EXT, 6)
        loft()
    return tool.part


def _cut_tapered(bores, hex_bores, top_z: float, depth: float) -> None:
    """Cut a tapered cone (round) / frustum (hex) for every hole."""
    floor = top_z - depth
    for d, x, y in bores:
        r_bot = (d - TAPER_BOTTOM) / 2
        r_top = (d + TAPER_TOP) / 2
        slope = (r_top - r_bot) / depth
        with Locations((x, y, floor - _EXT)):
            Cone(
                r_bot - slope * _EXT,
                r_top + slope * _EXT,
                depth + 2 * _EXT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    for af, x, y in hex_bores or []:
        add(_hex_frustum(af, x, y, floor, top_z, depth), mode=Mode.SUBTRACT)


def create() -> Part:
    """Tapered holes -- clearance at top, undersized at bottom; bored through."""
    return _coupon(_cut_tapered, "drill_fit_tester_taper", "TAPER")


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester_taper")


if __name__ == "__main__":
    main()
