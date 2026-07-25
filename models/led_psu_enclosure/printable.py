"""Printable parts only -- no component mocks.

``uv run export led_psu_enclosure`` exports the *assembled* view, which includes
the PSU/connector mock solids as children. Those are keep-out models, not things
to print, and ``export.py`` happily writes an STL per child. Use this entry point
instead when you want files for the slicer:

    uv run export led_psu_enclosure.printable
    uv run show led_psu_enclosure.printable
"""

from __future__ import annotations

from build123d import Compound

from .assembly import create_print_layout


def create() -> Compound:
    """The printed parts, laid out side by side, each in its own print pose."""
    return create_print_layout()


__all__ = ["create"]
