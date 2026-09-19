"""Vertex core for the tetrahedron shifted outward at profile crossings."""

from __future__ import annotations

from build123d import Part

from . import stella_config as s
from .stella_core import create_core


def create() -> Part:
    """The four larger cores for the outward crossing layer."""
    part = create_core(s.EDGE_OFFSET)
    part.label = "stella offset vertex core"
    return part


__all__ = ["create"]
