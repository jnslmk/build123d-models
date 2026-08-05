"""Assembly views: how the mounting family actually holds a lamp.

Three scenes, one module each, every one of them a model in its own right --
``uv run show led_profiles.assemblies.triangle``, and likewise ``.standing``
and ``.suspended``. That is why this is a package rather than the single
module it used to be: the site's roster (``tessellate_models.MODELS``) and
every CLI entry point address a model by its *module* path, so a view that
only existed as ``create_standing()`` inside one module could not be shown,
exported or rendered by name. Splitting them costs nothing -- the three
scenes never shared geometry, only the strap helper that now lives with the
strap (``strap.labelled``) -- and buys all three a place on the page.

| module | shows |
|---|---|
| ``triangle``  | 3 lamps + 3 corners closed into a flat loop, 12 straps |
| ``standing``  | 1 lamp upright in the tripod hub, legs deployed, 3 straps |
| ``suspended`` | 1 lamp hung from two eye feet at the Bessel points, 4 straps |

Every mount in all three is placed with the family's own ``seated()``
helpers -- ``endcap.seated``, ``strap.seated``, ``feet.seated``,
``corner.seated``, ``stand.seated`` / ``seated_legs`` -- nothing here
re-derives a transform those already own. The only genuinely new placements
are the triangle's vertex geometry (see ``triangle.triangle_vertices``) and
the stand's tube-to-vertical rotation (see ``standing._to_socket``).

Names re-exported here are what ``models.led_profiles`` and ``checks.py``
import, so ``from . import assemblies; assemblies.create_triangle()`` reads
the same as it did when this was one file.
"""

from __future__ import annotations

from .standing import create_standing
from .suspended import BESSEL_FRACTION, bessel_points, create_suspended
from .triangle import create_triangle, triangle_vertices

__all__ = [
    "BESSEL_FRACTION",
    "bessel_points",
    "create_standing",
    "create_suspended",
    "create_triangle",
    "triangle_vertices",
]
