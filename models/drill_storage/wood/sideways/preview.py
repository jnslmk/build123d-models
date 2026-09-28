"""Wood sideways guide with seated TPU cartridge and exposed bits."""

from ...sets import WOOD
from ...sideways import create_preview_for

IS_ASSEMBLY = True
PARAMS = []


def create():
    return create_preview_for(WOOD)
