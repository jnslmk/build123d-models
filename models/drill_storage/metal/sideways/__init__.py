"""Horizontal metal holder: assembled scene with separate printable base and cover."""

from ...sets import METAL
from ...sideways import create_closed_for

IS_ASSEMBLY = True
PARAMS = []


def create():
    return create_closed_for(METAL)
