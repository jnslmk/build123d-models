"""The snap-in COB diffuser on its own, in its clipped-in position.

The render pair's emissive half -- ``uv run show
led_profiles.previz.diffuser``. Downstream the pixel texture lands on this
shell while ``led_profiles.previz.body`` stays dark.
"""

from __future__ import annotations

from build123d import Part

from .. import config as c
from ..profile import create_diffuser

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True


def create(length: float = c.LENGTH) -> Part:
    """The diffuser, exactly where ``previz.body`` leaves the opening for it."""
    return create_diffuser(length)


__all__ = ["IS_ASSEMBLY", "create"]
