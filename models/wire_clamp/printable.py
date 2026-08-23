"""Both parts on one plate, in print pose.

    uv run export wire_clamp.printable

The headline ``wire_clamp`` is a scene and has no STL; this is the thing to
send to a slicer if you want the whole clamp in one job. The parts are laid out
the way each of them prints on its own -- body on its base, screw knob down --
just moved apart, so there is nothing here that the two per-part models do not
already say.
"""

from __future__ import annotations

from build123d import Compound, Pos

from ..lib.edges import as_part
from . import body, screw
from .config import DEFAULT, WIRE_DEFAULT, WIRE_MAX, WIRE_MIN, Clamp

GAP = 3.0
"""Between the two footprints. Enough for a brim to have somewhere to go without
the two brims meeting."""


def build(c: Clamp = DEFAULT) -> Compound:
    pitch = 2 * c.body_r + GAP
    return Compound(
        children=[
            as_part(Pos(-pitch / 2, 0, 0) * body.build(c)),
            as_part(Pos(pitch / 2, 0, 0) * screw.build(c)),
        ]
    )


PARAMS = [
    {
        "name": "wire_d",
        "label": "Wire diameter (mm)",
        "type": "number",
        "min": WIRE_MIN,
        "max": WIRE_MAX,
        "step": 0.1,
        "default": WIRE_DEFAULT,
    },
]
"""The one slider again. This is the module that guarantees a matched pair:
both parts come off the same ``Clamp``, so whatever the slider says, the screw
on the plate fits the body next to it."""


def create(wire_d: float = WIRE_DEFAULT) -> Compound:
    """Body and screw, side by side on the bed."""
    return build(Clamp.of(wire_d))
