"""Constraint-based 2D sketch editor for build123d.

One JSON document on disk (``<name>.sketch.json``) is the single source of truth.
Two editors mutate it through the *same* command API (``sketch.commands``):

* a human, via a canvas UI (or by editing the JSON), and
* an agent, via the MCP server (``sketch.mcp_server``).

A pure-Python constraint solver (``sketch.solver``) keeps the geometry consistent
after every edit, and ``sketch.codegen`` emits a real ``models/<name>.py`` in the
repo's ``create()`` builder-mode pattern.
"""

from sketch.model import Sketch

__all__ = ["Sketch"]
