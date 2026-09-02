"""The snap-in diffuser as a render mesh, on its own.

The other half of the pair ``led_profiles.previz_body`` documents. This is the
one that matters optically: ADR-0022 rule 8 in ``jnslmk/beamhouse`` puts the
per-pixel emission on the diffuser rather than on the COB band underneath it,
because the band is not visible through the translucent cap and what an
audience sees is the diffuser glowing across its full 26 mm.
"""

from __future__ import annotations

from build123d import Part

from .config import LENGTH
from .profile import create_previz_diffuser

# A render asset, so the website offers no STL/STEP download for it.
IS_ASSEMBLY = True


def create(length: float = LENGTH) -> Part:
    return create_previz_diffuser(length)
