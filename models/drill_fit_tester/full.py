"""Full-set fit coupons: every hole in the wood holder, at five grip offsets.

``drill_fit_tester.small`` only carried 2-5 mm, because that is where the print
compensation lives. But the calibration history says the *baseline* deserves a
look too: every size below 5 mm has been revised upward at least once, and 4 mm
reversed a judgement it had already passed twice. The 0.22 baseline for 6-10 mm
has never been tested against anything except flat sweep bars at 0.14/0.22/0.30,
where a true optimum near 0.26 would still have picked 0.22 as the winner.

So this coupon carries **exactly what the wood base carries** -- all of
``DRILL_DIAMS`` plus the countersink's hex socket -- with each bar shifting the
whole production law (``grip_for`` and ``HEX_GRIP``) by a fixed offset. One
family settles the entire holder, small bores and baseline together.

If the winning bar is the same across every size, that offset goes straight into
RIB_GRIP. If the small bores want one bar and the big bores another, the split
tells you which part is wrong: the table (below 5 mm) or the baseline (above).

Bar thickness is ``RIB_ZONE_H``, matching the holder's rib band, so the feel
transfers. Bits go in SHANK first. Prints flat, bores-up, no supports.
"""

from build123d import Compound

from ..drill_storage.wood import DRILL_DIAMS
from .sweep import create_offset_family, report_offsets

# Everything the wood base holds.
FULL_DIAMS = sorted(DRILL_DIAMS)
FULL_HEX = True

# Same step as the small coupon: 0.04 is about the finest difference still
# perceptible by hand, and +-0.08 brackets a plausible error in the law.
FULL_OFFSETS = [-0.08, -0.04, 0.0, 0.04, 0.08]


def create() -> Compound:
    """All offset bars, laid out side by side (each exports as its own STL)."""
    return create_offset_family(
        FULL_OFFSETS, FULL_DIAMS, FULL_HEX, "drill_fit_tester.full"
    )


def report() -> None:
    """Print the coupon's key: the grip each bar cuts at each size."""
    report_offsets(FULL_DIAMS, FULL_OFFSETS, FULL_HEX)


__all__ = ["FULL_DIAMS", "FULL_HEX", "FULL_OFFSETS", "create", "report"]
