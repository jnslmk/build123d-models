"""Plain-hole fit-test coupon -- a sibling of ``drill_fit_tester``.

Every hole is a plain cylinder, no ribs, sized a fixed *percentage*
(``PLAIN_UNDERSIZE``) under the bit for a light friction grip. Using a percentage
rather than a fixed mm compensates the way small holes print tighter than large
ones (a fixed undersize leaves the small holes too tight and the big ones loose).
Fine-tune per-printer with the slicer's X-Y hole compensation.
"""

from build123d import Part

from ..drill_storage.box import cut_holes
from .frame import coupon

PLAIN_UNDERSIZE = 0.03  # holes this fraction of the bit under size -> light grip


def create() -> Part:
    """Plain round holes, undersized a fixed % of the bit; no ribs, bored through."""
    return coupon(
        lambda b, h, tz, dp: cut_holes(
            b, h, 0.0, False, tz, dp, through=True, undersize_frac=PLAIN_UNDERSIZE
        ),
        "drill_fit_tester.plain",
        "PLAIN",
    )
