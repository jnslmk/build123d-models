"""Fit-test coupons for the ``drill_storage`` bores.

Printing a whole holder to find out a bore is 0.1 mm tight is an eight-hour
answer to a question a flat strip settles in twenty minutes. Every coupon here is
that strip: the real bore geometry at the real engagement depth, carrying every
size in the set, so you drop the actual bits in and feel the fit.

Two families, and they answer different questions.

**Single-value coupons** ask "which way of cutting a hole works?" -- one strip
per strategy, all sharing the frame in ``frame.py``:

    uv run show drill_fit_tester          # ribbed: the holder's real geometry
    uv run show drill_fit_tester.plain    # nominal holes, no ribs
    uv run show drill_fit_tester.taper    # slightly tapered, self-centring

**Sweep coupons** ask "which *number* is right?" -- several bars on one plate,
each cut at a different interference, so you pick a winner by hand:

    uv run show drill_fit_tester.sweep    # 5 flat grip values, all sizes on each
    uv run show drill_fit_tester.small    # the 2-5 mm compensation table
    uv run show drill_fit_tester.full     # the whole wood set, 5 offsets

``.sweep`` sweeps a flat grip; ``.small`` and ``.full`` sweep an *offset applied
to the production law* (``drill_storage.box.grip_for``), which is the only way to
test a law that is no longer a constant. What these coupons measured is what
``grip_for`` now is -- read ``box.RIB_GRIP_SMALL`` for the resulting table.

All of them print flat, bores-up, no supports, and each bar of a sweep exports as
its own STL so you can print one, a few, or all.
"""

from . import frame
from .frame import EDGE, HOLE_WALL, LABEL_PITCH, PLATE_H, coupon, engrave, layout_r
from .ribbed import create

__all__ = [
    "EDGE",
    "HOLE_WALL",
    "LABEL_PITCH",
    "PLATE_H",
    "coupon",
    "create",
    "engrave",
    "frame",
    "layout_r",
]
