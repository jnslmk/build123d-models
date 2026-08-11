"""One lamp upright on the folding tripod stand, legs deployed.

    uv run show led_profiles.assemblies.standing
    uv run export led_profiles.assemblies.standing

The whole stand is in this view: the post, three printed legs spread at 120
degrees on the floor, and the two keepers dropped into their sockets. The
tripod is studio-class, not load-bearing -- ``docs/design-notes.md`` section 4
has the number, and printing the legs instead of buying flat steel bar costs
about a third of it. This is what that number is about: 1.5 m of stick standing
on three plastic bars.

The lamp is rotated onto the post's vertical trough by ``_to_socket``, whose
offset lands the lower endcap's outer face exactly on the seat -- not merely
somewhere in the bore. The legs lie on the floor, so everything on the post is
one leg thickness up from it.
"""

from __future__ import annotations

from build123d import Compound, Part, Pos, Rotation

from models.lib.edges import as_part

from .. import config as c
from .. import stand as stand_mod
from ..assembly import PARAMS, parts as lamp_parts
from ..endcap import CAP_T
from ..stand import config as sc

# A scene, not a print job -- see tessellate_models.model_is_assembly.
IS_ASSEMBLY = True

# Rotates a tube-local part (config's own convention: x along the tube from
# its near end, y = u, z = height from the underside, centred at HEIGHT / 2)
# so the tube's length axis becomes vertical. Verified against unit vectors:
# local +X -> global +Z, local +Y -> global +X, local +Z -> global +Y.
STAND_UPRIGHT = Rotation(0, -90, 0) * Rotation(-90, 0, 0)


def _to_socket(part: Part) -> Part:
    """A tube-local part onto the post's vertical trough.

    x (0 at the aluminium's near end) becomes global Z, landing on
    ``LEG_T + SEAT_Z + CAP_T`` -- so x = -CAP_T, an endcap's outer face, lands
    on the seat itself. y and z (height, centred on HEIGHT / 2) become global X
    and Y, which is what puts the tube's own axis on the post's vertical axis;
    see ``stand.config.SINK``. The ``LEG_T`` term is the legs the flange stands
    on, and it is the one thing here that is *not* part-local.
    """
    return as_part(
        Pos(0, -c.HEIGHT / 2, sc.LEG_T + sc.SEAT_Z + CAP_T) * (STAND_UPRIGHT * part)
    )


def create_standing(length: float = c.LENGTH) -> Compound:
    """One lamp standing vertically on the tripod stand, legs deployed."""
    stand_parts: list[Part] = [
        stand_mod.seated(),
        *stand_mod.seated_legs(),
        *stand_mod.seated_keepers(),
    ]

    lamp: list[Part] = []
    for part in lamp_parts(length):
        moved = _to_socket(part)
        moved.label = part.label
        moved.color = part.color
        lamp.append(moved)

    assembly = Compound(children=[*stand_parts, *lamp])
    assembly.label = f"standing lamp ({length:.0f} mm, tripod stand)"
    return assembly


def create(length: float = c.LENGTH) -> Compound:
    """Entry point for ``uv run show led_profiles.assemblies.standing``."""
    return create_standing(length)


__all__ = ["IS_ASSEMBLY", "PARAMS", "STAND_UPRIGHT", "create", "create_standing"]
