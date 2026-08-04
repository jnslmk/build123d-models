"""Just the printed parts, laid out for the slicer.

``uv run export led_profiles`` exports the assembled lamp and writes an STL per
child, which would include the aluminium extrusion and the bought diffuser.
This is the entry point that gives you only what actually goes on a bed.

    uv run show led_profiles.printable
    uv run export led_profiles.printable
"""

from __future__ import annotations

from build123d import Compound

from .assembly import create_print_layout


def create() -> Compound:
    """Entry point for ``uv run show/export led_profiles.printable``."""
    return create_print_layout()


__all__ = ["create"]
