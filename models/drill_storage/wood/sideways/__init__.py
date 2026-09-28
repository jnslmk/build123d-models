"""Horizontal wood holder: ASA/TPU/PETG inspection scene, not a print job."""

from ...sets import WOOD
from ...sideways import create_closed_for

IS_ASSEMBLY = True
PARAMS = []


def create():
    return create_closed_for(WOOD)
