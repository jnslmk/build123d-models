"""The ASA shell for the metal set.

Rigid half: Gridfinity foot, collar, cover snap groove, the engraved size legend,
and the guide bores that keep a bit upright. Grips nothing -- that is the
cartridge's job. Shape, argument and print notes are in ``drill_storage.shell``;
the set it is cut for is ``sets.METAL``.

Printed foot down, cavity up, in ASA, no supports.
"""

from __future__ import annotations

from build123d import Part

from ..sets import METAL as SET
from ..shell import create_shell_for


def create() -> Part:
    """Model entry point: the ASA shell for the metal set."""
    return create_shell_for(SET)


__all__ = ["SET", "create"]
