"""1×3×5U ASA anchor: horizontal guides for all wood bits."""

from ...sets import WOOD
from ...sideways import create_base_for
from ...sideways_checks import run_for

IS_ASSEMBLY = False
PARAMS = []


def create():
    return create_base_for(WOOD)


def check():
    return run_for(WOOD, create())
