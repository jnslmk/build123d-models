"""Assembled and print-layout views of the enclosure.

``create()``              -- everything closed up, in use pose, contents visible
``create_open()``         -- same but with the lid off, to see the layout
``create_print_layout()`` -- the printed parts spread out, each in its print pose
``create_mocks_only()``   -- just the contents, for checking the layout

Following the dual-entry-point pattern of ``models/wall_bar_lamp.py``: the
assembled view is for understanding, the print layout is what goes to the slicer.
Note the house rule -- each printed part is *authored* in its own print pose, and
the assembled view is the thing that moves parts around, never the reverse.
"""

from __future__ import annotations

from build123d import Color, Compound, Part, Pos

from . import config as c
from . import gasket as gasket_mod
from . import lid as lid_mod
from . import mocks
from . import plate as plate_mod
from . import shelf as shelf_mod
from . import vent as vent_mod
from .tray import create_tray_finished
from .util import as_part

TRAY_COLOR = Color(0.35, 0.65, 1.0, 0.30)  # house blue, translucent to see inside
LID_COLOR = Color(0.35, 0.65, 1.0, 0.25)
DECK_COLOR = Color(0.55, 0.58, 0.62, 0.85)
VENT_COLOR = Color(0.90, 0.55, 0.20, 0.95)


def printed_parts() -> list[Part]:
    """Every printed part, each already in its own print pose."""
    tray = create_tray_finished()
    tray.color = TRAY_COLOR
    lid = lid_mod.create_lid()
    lid.color = LID_COLOR
    plate = plate_mod.create_psu_plate()
    plate.color = DECK_COLOR
    shelf = shelf_mod.create_shelf()
    shelf.color = DECK_COLOR

    parts = [tray, lid, plate, shelf]
    for name, part in vent_mod.cartridges().items():
        part.label = name
        part.color = VENT_COLOR
        parts.append(part)
    return parts


def _installed() -> list[Part]:
    """The structural parts moved into their installed positions."""
    tray = create_tray_finished()
    tray.color = TRAY_COLOR
    plate = plate_mod.seated()
    plate.color = DECK_COLOR
    shelf = shelf_mod.seated()
    shelf.color = DECK_COLOR
    vents = []
    for part in vent_mod.seated_blanks():
        part.color = VENT_COLOR
        vents.append(part)
    return [tray, plate, shelf, *vents, gasket_mod.seated()]


def create() -> Compound:
    """Closed-up assembly: shell, deck, blanked vents, lid and every component."""
    lid = lid_mod.seated()
    lid.color = LID_COLOR
    return Compound(
        label="led_psu_enclosure",
        children=[*_installed(), lid, *mocks.keepouts()],
    )


def create_open() -> Compound:
    """Same assembly with the lid removed, so the layout is readable."""
    return Compound(
        label="led_psu_enclosure_open",
        children=[*_installed(), *mocks.keepouts()],
    )


def create_print_layout() -> Compound:
    """The printed parts laid out side by side for slicing."""
    gap = 15.0
    laid: list[Part] = []
    x = 0.0
    for part in printed_parts():
        bb = part.bounding_box()
        moved = as_part(Pos(x - bb.min.X, -bb.min.Y, -bb.min.Z) * part)
        moved.label = part.label
        moved.color = part.color
        laid.append(moved)
        x += bb.size.X + gap
    return Compound(label="led_psu_enclosure_print", children=laid)


def create_mocks_only() -> Compound:
    """Just the contents -- used to sanity-check the layout before walls exist."""
    return Compound(label="led_psu_enclosure_contents", children=mocks.keepouts())


__all__ = [
    "create",
    "create_open",
    "create_print_layout",
    "create_mocks_only",
    "printed_parts",
    "c",
]
