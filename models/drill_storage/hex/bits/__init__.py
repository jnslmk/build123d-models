"""The BITS box's three printed parts, one module each.

A naming layer, not geometry: the shape, the arguments and the print notes all
live one level up in ``hex.base`` / ``hex.insert`` / ``hex.cover``, which the
ALLEN box is cut from as well. What is per-box is the socket layout (a literal
4x4 grid on shaved lead-in clearances -- see ``hex.config``), the cover height
and the blank walls, and each module here supplies exactly that.

| module | prints |
|---|---|
| ``base``   | rigid ASA base, foot down, cavity up |
| ``insert`` | TPU cartridge, flat bottom down, bores up |
| ``cover``  | translucent PETG cover, pillow top down, mouth up |

Addressed by name -- ``uv run show drill_storage.hex.bits.base`` -- which is
why the box is a package and not three ``bits_*`` modules: dots are the
hierarchy, underscores are only for multi-word single names.
"""

from __future__ import annotations

from . import base, cover, insert

__all__ = ["base", "cover", "insert"]
