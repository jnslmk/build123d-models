"""One lamp upright in the tripod hub, legs deployed.

    uv run show led_profiles.assemblies.standing
    uv run export led_profiles.assemblies.standing

The tripod is studio-class, not load-bearing: ~85 g of push at the top topples
it (``docs/design-notes.md`` section 4). This view is what that number is
about -- the whole 1.5 m stick standing on three folded flat bars.
"""

from __future__ import annotations

from build123d import Compound, Part, Pos, Rotation

from models.lib.edges import as_part

from .. import config as c
from .. import mount_config as m
from .. import stand as stand_mod
from .. import strap as strap_mod
from ..assembly import PARAMS, parts as lamp_parts
from ..endcap import CAP_T

# Rotates a tube-local part (config's own convention: x along the tube from
# its near end, y = u, z = height from the underside, centred at HEIGHT / 2)
# so the tube's length axis becomes vertical. Verified against unit vectors:
# local +X -> global +Z, local +Y -> global +X, local +Z -> global +Y.
STAND_UPRIGHT = Rotation(0, -90, 0) * Rotation(-90, 0, 0)


def _to_socket(part: Part) -> Part:
    """A tube-local part onto the stand's vertical socket.

    x (0 at the aluminium's near end) becomes global Z, landing on
    ``stand.SEAT_Z + CAP_T`` -- exactly where the hub's own tube bore starts
    (``stand.create_stand_hub``), so x=-CAP_T (an endcap's outer face) lands
    on ``SEAT_Z`` itself: the seat. y and z (height, centred on HEIGHT / 2)
    become global X and Y, which is what puts the tube's own axis on the
    hub's vertical axis -- see ``stand.SINK``.
    """
    return as_part(
        Pos(0, -c.HEIGHT / 2, stand_mod.SEAT_Z + CAP_T) * (STAND_UPRIGHT * part)
    )


def _mount_to_socket(part: Part) -> Part:
    """A mount-local part (bed frame, see ``mount_config``) onto the same socket."""
    return _to_socket(as_part(Pos(0, 0, -m.TUBE_UNDER_Z) * part))


def create_standing(length: float = c.LENGTH) -> Compound:
    """One lamp standing vertically in the tripod hub, legs deployed.

    The lamp is rotated onto the hub's vertical socket axis by ``_to_socket``;
    the offset baked into that transform is what lands the lower endcap's
    outer face exactly on the hub's seat, not merely somewhere in the bore.
    Straps go on at all three of the stand's own strap stations
    (``stand.STATIONS``, which are global heights -- back-solved to the
    tube-local x that ``strap.seated`` wants).
    """
    hub = stand_mod.seated()
    legs = stand_mod.seated_legs()

    lamp: list[Part] = []
    for part in lamp_parts(length):
        moved = _to_socket(part)
        moved.label = part.label
        moved.color = part.color
        lamp.append(moved)

    straps: list[Part] = []
    for i, z in enumerate(stand_mod.STATIONS):
        local_station = z - (stand_mod.SEAT_Z + CAP_T)
        moved = _mount_to_socket(strap_mod.seated(local_station))
        straps.append(strap_mod.labelled(moved, f"station {i}"))

    assembly = Compound(children=[hub, *legs, *lamp, *straps])
    assembly.label = f"standing lamp ({length:.0f} mm, tripod stand)"
    return assembly


def create(length: float = c.LENGTH) -> Compound:
    """Entry point for ``uv run show led_profiles.assemblies.standing``."""
    return create_standing(length)


__all__ = ["PARAMS", "STAND_UPRIGHT", "create", "create_standing"]
