"""The aluminium profile as a render mesh, on its own.

One of the two meshes Beamhouse's authored STAR-TENT spoke GDTF carries. GDTF
addresses a mesh per ``<Model>`` element, so the body and the diffuser have to
be separate files -- ``exports/led_profiles.previz_body.glb`` and
``exports/led_profiles.previz_diffuser.glb`` -- and not two children of one
compound. That is also why this is its own roster entry rather than a flag on
``led_profiles``: the roster is what decides which GLBs get built and
published.

Not a print job and not a B-rep of record: ``led_profiles.endcap`` and friends
are the printable parts, and ``profile.create_extrusion`` is the aluminium's
real geometry, cavity and all. This is that outline with everything a closed
tube hides taken out of it.
"""

from __future__ import annotations

from build123d import Part

from .config import LENGTH
from .profile import create_previz_shell

# A render asset, so the website offers no STL/STEP download for it.
IS_ASSEMBLY = True


def create(length: float = LENGTH) -> Part:
    return create_previz_shell(length)
