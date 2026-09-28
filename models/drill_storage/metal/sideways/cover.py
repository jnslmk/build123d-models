"""Foot-down PETG side-opening cover and forward Gridfinity feet for metal drills."""

from ...sets import METAL
from ...sideways_cover import create_cover_for
from ...sideways_checks import run_cover_for

IS_ASSEMBLY = False
PARAMS = []


def create():
    return create_cover_for(METAL)


def check():
    return run_cover_for(METAL, create())
