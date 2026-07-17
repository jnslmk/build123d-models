"""Plain-hole fit-test coupon -- a sibling of ``drill_fit_tester``.

Every hole is a plain cylinder, no ribs, sized ``PLAIN_CLEARANCE`` under the bit
for a light friction grip. The fit is then tuned by the slicer's X-Y hole
compensation: print it, adjust Orca's compensation until each bit is the fit you
want, and use that compensation for the real holder.
"""

from build123d import Part

from models.drill_fit_tester import _coupon
from models.drill_storage_gridfinity import cut_holes

PLAIN_CLEARANCE = -0.1  # holes this far under the bit -> light friction fit


def create() -> Part:
    """Plain round holes, slightly undersized; no ribs, bored through."""
    return _coupon(
        lambda b, h, tz, dp: cut_holes(
            b, h, PLAIN_CLEARANCE, False, tz, dp, through=True
        ),
        "drill_fit_tester_plain",
        "PLAIN",
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester_plain")


if __name__ == "__main__":
    main()
