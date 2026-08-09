"""Geometry assertions for the ALLEN box.

    uv run check drill_storage.allen

The assertions themselves live in ``drill_storage.hex.checks``, which builds
and verifies **both** hex boxes: the ALLEN box keeps the family's clearances
outright, the BITS box shaves three of them, and the two share the geometry
modules this package names. Running the same suite here means the ALLEN box's
own assertions (socket layout, engraved legend, envelope) are always part of
this package's check, exactly as the wood/metal/stone variants forward to the
family's shared checks.
"""

from __future__ import annotations

import sys

from ..hex.checks import run


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
