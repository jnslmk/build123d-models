"""Lidless low-wall variant of the accepted lightweight wrench tray."""

from build123d import Part

from models.lib.checks import Report

from . import base
from . import config as c

IS_ASSEMBLY = False
PARAMS = c.PARAMS


def create(wrenches_per_column: int | float = c.DEFAULT_WRENCHES_PER_COLUMN) -> Part:
    """Keep the accepted feet, low walls and two racks per column unchanged."""
    part = base.create(wrenches_per_column)
    part.label = "WORKZONE lidless open wrench tray"
    return part


def check() -> Report:
    """Reuse the accepted tray's physical gate without a second geometry path."""
    return base.check()
