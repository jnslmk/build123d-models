"""The lamp's closed tube for the renderer: extrusion, endcaps, glands, cables.

Everything visible with the diffuser lifted off, each part in its installed
place -- ``uv run show led_profiles.previz.body``. The diffuser itself is
``led_profiles.previz.diffuser``; downstream it renders emissive while this
half stays dark.
"""

from __future__ import annotations

from build123d import Compound

from .. import config as c
from ..assembly import previz_parts

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True


def create(length: float = c.LENGTH) -> Compound:
    """The finished lamp without diffuser and strip, ready to hang."""
    assembly = Compound(children=previz_parts(length))
    assembly.label = f"T8 lamp previz body ({length:.0f} mm)"
    return assembly


__all__ = ["IS_ASSEMBLY", "create"]
