"""Horizontal metal drill set: printable TPU grip cartridge."""

from ...sets import METAL
from ...sideways_insert import create_insert_for
from ...sideways_checks import run_insert_for

IS_ASSEMBLY = False
PARAMS = []


def create():
    return create_insert_for(METAL)


def check():
    return run_insert_for(METAL, create())
