"""Assembly views: how the mounting family actually holds a lamp.

Four scenes, one module each, every one of them a model in its own right --
``uv run show led_profiles.assemblies.triangle``, and likewise
``.stella_octangula``, ``.standing`` and ``.suspended``. That is why this is a
package rather than the single module it used to be: the site's roster
(``tessellate_models.MODELS``) and every CLI entry point address a model by its
*module* path, so each scene can be shown, exported and rendered by name.

| module | shows |
|---|---|
| ``triangle``  | 3 lamps + 3 corners closed into a flat loop, 12 straps |
| ``standing``  | 1 lamp upright in the tripod hub, legs deployed, 3 straps |
| ``suspended`` | 1 lamp hung from two eye feet at the Bessel points, 4 straps |
| ``stella_octangula`` | 12 lamps + 8 round vertex hubs, 24 slim keepers |

Every scene places the family's own finished parts rather than rebuilding them:
``endcap``, ``strap``, ``feet``, ``corner``, ``stand``, and the Stella core,
arm and keeper modules. Scene modules own only the transforms and closed-form
layout that join those parts.

Names re-exported here are what ``models.led_profiles`` and ``checks.py``
import, so ``from . import assemblies; assemblies.create_triangle()`` reads
the same as it did when this was one file.
"""

from __future__ import annotations

from .stella_octangula import create_stella_octangula
from .standing import create_standing
from .suspended import BESSEL_FRACTION, bessel_points, create_suspended
from .triangle import create_triangle, triangle_vertices

__all__ = [
    "BESSEL_FRACTION",
    "bessel_points",
    "create_standing",
    "create_suspended",
    "create_triangle",
    "create_stella_octangula",
    "triangle_vertices",
]
