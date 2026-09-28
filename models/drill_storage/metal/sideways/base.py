"""1×4×5U ASA anchor: horizontal guides for all metal bits."""

from ...sets import METAL
from ...sideways import create_base_for
from ...sideways_checks import run_for

IS_ASSEMBLY = False
PARAMS = []


def create():
    return create_base_for(METAL)


def check():
    return run_for(METAL, create())
