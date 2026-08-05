"""Ribbed fit-test coupon -- the holder's real geometry, on one flat strip.

Three compliant ribs grip the bit at the production interference (``grip_for``),
exactly as ``drill_storage.box`` cuts them, so what the coupon feels like is what
the holder will feel like. This is the coupon to print first; ``.plain`` and
``.taper`` are the alternatives it is measured against.

Prints flat, bores-up, no supports.
"""

from build123d import Part

from ..drill_storage.box import cut_holes
from .frame import coupon


def create() -> Part:
    """Ribbed variant -- the holder's real geometry (3 ribs grip the bit)."""
    return coupon(
        lambda b, h, tz, dp: cut_holes(b, h, 0.0, True, tz, dp, through=True),
        "drill_fit_tester",
        "RIBBED",
    )


__all__ = ["create"]
