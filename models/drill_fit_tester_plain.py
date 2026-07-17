"""Plain-hole fit-test coupon -- a sibling of ``drill_fit_tester``.

Every hole is a plain cylinder at the *nominal* bit size (no ribs, no designed
clearance), so the fit is tuned purely by the slicer's X-Y hole compensation.
Print it, adjust Orca's compensation until each bit is the fit you want, and use
that compensation for the real holder. The hex socket is a plain 6.3 mm hex.
"""

from build123d import Part

from models.drill_fit_tester import _coupon
from models.drill_storage_gridfinity import cut_holes


def create() -> Part:
    """Plain nominal-size holes -- clearance 0, no ribs; bored through."""
    return _coupon(
        lambda b, h, tz, dp: cut_holes(b, h, 0.0, False, tz, dp, through=True),
        "drill_fit_tester_plain",
        "PLAIN",
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_fit_tester_plain")


if __name__ == "__main__":
    main()
