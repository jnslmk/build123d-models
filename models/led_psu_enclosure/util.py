"""Back-compatible view of the shared edge helpers.

These four moved to ``models.lib.edges`` once a second model wanted them. The
names stay importable from here so the enclosure's own modules -- and anything
else that already reached for ``.util`` -- keep working unchanged. New code
should import from ``models.lib.edges`` directly.
"""

from __future__ import annotations

from ..lib.edges import (
    as_part as as_part,
    bottom_chamfer_tool as bottom_chamfer_tool,
    chamfer_edge as chamfer_edge,
    top_chamfer_tool as top_chamfer_tool,
)

__all__ = ["as_part", "bottom_chamfer_tool", "chamfer_edge", "top_chamfer_tool"]
