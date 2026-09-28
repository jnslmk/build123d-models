"""Wood sideways guide with horizontally posed bits; not a print job."""

from ...sets import WOOD
from ...sideways import create_preview_for

IS_ASSEMBLY = True
PARAMS = []


def create():
    return create_preview_for(WOOD)
