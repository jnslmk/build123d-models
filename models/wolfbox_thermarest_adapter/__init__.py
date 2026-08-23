"""Adapter that lets a WOLFBOX MF100 air duster inflate a Therm-a-Rest pad.

A funnel with a socket on the bottom: the narrow end pushes onto the blower's
outlet, the wide end presses over the mattress valve, and the air goes from one
to the other instead of past it.

    uv run show wolfbox_thermarest_adapter
    uv run export wolfbox_thermarest_adapter   # the STL to print
    uv run check wolfbox_thermarest_adapter

**Both ends are tapers, and that is the design.** Neither the blower's bayonet
nor the WingLock's snap groove is reproduced here, because nobody in this repo
has measured either one -- ``config.py`` records exactly what is researched and
what is assumed, and the answer is that every diameter is assumed. A cone is
what you build when you do not know a diameter: it seats wherever it happens to
meet the port, so the socket covers everything from 16 to 27 mm and the cup
everything from 22 to 34 mm, and a mis-guess moves *where* it seats rather than
whether it fits at all. Cloning the bayonet would have inverted that: a lug
0.5 mm out is a part that cannot be fitted.

**It is a friction seal, not a gasket.** Push the socket on, press the cup down
on the valve, and hold it there -- the blower's own thrust helps, and the
WingLock's one-way flap keeps what goes in. Nothing latches, so nothing has to
be released afterwards either; the adapter comes off with a pull.

**The duster's other end empties the pad.** A fan that blows out of one port
is pulling in at the other, so ``wolfbox_thermarest_adapter.deflate`` is the
same funnel with the same cup, hung off the intake instead of the outlet -- a
cap over the tail of the baton rather than a socket into its mouth, because the
intake is a fixed grille and not a port. Both parts share ``config.py``'s valve
end, so a cup dialled in for one is dialled in for the other.

**Nothing is the narrowest thing in the path.** The throat is 16 mm, at or
above the bore of every stock MF100 nozzle. A duster is a high-velocity,
low-static-pressure source, so a restriction anywhere costs volume flow, which
is the thing being traded for inflation time; the adapter is sized so that the
blower, not the adapter, stays the limit.

**Parametric, and meant to be.** Six sliders, all of them a diameter or a depth
of one of the two ports (see ``PARAMS``). Because the ledger is honest about
being unmeasured, dialling one in is the *expected* workflow rather than a
failure -- ``README.md`` maps each symptom to the slider that fixes it.
``Adapter.of`` clamps every combination back into something that still
describes a funnel, so no slider position can produce a bore wider than its
mouth or a cup that drains the wrong way.

**Printing.** PETG, no supports, already in print pose: the socket's mouth flat
on the bed, the cup's mouth up. Every internal surface is either vertical or
leans out as it rises, so the bore self-supports; the one downward-facing
internal face is the 45 degree flare off the throat. The cup wall is 1.2 mm on
purpose -- it is the sealing face and wants to give a little. TPU 95A prints
the same file and seals better if you have a spool.
"""

from __future__ import annotations

from build123d import Part

from . import config
from .config import (
    BED_CHAMFER,
    BLOWER_MOUTH_MAX,
    BLOWER_MOUTH_MIN,
    BLOWER_THROAT_MAX,
    BLOWER_THROAT_MIN,
    CUP_DEPTH_MAX,
    CUP_DEPTH_MIN,
    DEFAULT,
    MOUTH_CHAMFER,
    RIM_CHAMFER,
    SOCKET_DEPTH_MAX,
    SOCKET_DEPTH_MIN,
    VALVE_MOUTH_MAX,
    VALVE_MOUTH_MIN,
    VALVE_SEAT_MAX,
    VALVE_SEAT_MIN,
    Adapter,
)
from .profile import Point, revolve_section, trim

# Index of each corner in the raw section, so the chamfer table below reads as
# a place rather than a number. The section is drawn as a closed loop: up the
# inside from the bed, across the rim, down the outside, and back across the
# bed.
MOUTH_INNER = 0  # bed-side mouth of the socket, on the bore
RIM_INNER = 4  # cup rim, on the bore
RIM_OUTER = 5  # cup rim, on the outside
MOUTH_OUTER = 9  # bed-side mouth of the socket, on the outside


def bore_profile(a: Adapter) -> list[Point]:
    """The inside of the part, bed to rim, as ``(radius, height)`` corners.

    Public because it is what ``checks.py`` measures against, for this part and
    for ``deflate`` alike: "where should the wall be at this height" is a
    question about this list, so one set of checks covers a bore of two cones
    and a bore of four without knowing which it has.
    """
    return [
        (a.mouth_r, 0.0),  # MOUTH_INNER
        (a.throat_r, a.z_throat),
        (a.throat_r, a.z_throat_top),
        (a.seat_r, a.z_seat),
        (a.rim_r, a.z_rim),  # RIM_INNER
    ]


def _section(a: Adapter) -> list[Point]:
    """The half-section as (radius, height) corners, before any edge breaks.

    Drawn rather than derived from primitives because every break in this part
    is a break in *this* profile, and a revolved profile carries them for free
    -- see ``profile.py``, which does the trimming and the revolving for both
    adapters in this package. The outside is a chain of offsets from the bore
    above, each sized from its own cone's slope.
    """
    sock = a.socket_wall_offset()
    cup = a.cup_wall_offset()
    return [
        *bore_profile(a),
        (a.rim_r + cup, a.z_rim),  # RIM_OUTER
        (a.seat_r + cup, a.z_seat),
        (a.throat_r + sock, a.z_throat_top),
        (a.throat_r + sock, a.z_throat),
        (a.mouth_r + sock, 0.0),  # MOUTH_OUTER
    ]


def _breaks() -> dict[int, float]:
    """Which corners of the section get broken, and by how much.

    Four, and every one of them is a corner a hand or a mating port touches:
    the two mouths the adapter is pushed onto something by, and the two lips of
    the rim it is pressed down by. The rest of the loop is either concave (the
    bore's own steps) or already blunt -- the outside is a chain of cones whose
    largest kink is about 33 degrees, which leaves an interior angle well past
    the 120 the sharp-edge check calls sharp.
    """
    return {
        MOUTH_INNER: MOUTH_CHAMFER,  # lead-in: the socket has to start on-port
        RIM_INNER: RIM_CHAMFER,
        RIM_OUTER: RIM_CHAMFER,
        MOUTH_OUTER: BED_CHAMFER,  # elephant's-foot relief
    }


def build(a: Adapter = DEFAULT) -> Part:
    """The adapter as one revolved solid, seated on the bed."""
    return revolve_section(trim(_section(a), _breaks()))


# UI schema for the parametric web app. See tessellate_models.model_params().
PARAMS = [
    {
        "name": "blower_mouth_dia",
        "label": "Blower socket mouth (mm)",
        "type": "number",
        "min": BLOWER_MOUTH_MIN,
        "max": BLOWER_MOUTH_MAX,
        "step": 0.5,
        "default": DEFAULT.blower_mouth_dia,
    },
    {
        "name": "blower_throat_dia",
        "label": "Blower socket throat (mm)",
        "type": "number",
        "min": BLOWER_THROAT_MIN,
        "max": BLOWER_THROAT_MAX,
        "step": 0.5,
        "default": DEFAULT.blower_throat_dia,
    },
    {
        "name": "socket_depth",
        "label": "Blower socket depth (mm)",
        "type": "number",
        "min": SOCKET_DEPTH_MIN,
        "max": SOCKET_DEPTH_MAX,
        "step": 1.0,
        "default": DEFAULT.socket_depth,
    },
    {
        "name": "valve_mouth_dia",
        "label": "Valve cup rim (mm)",
        "type": "number",
        "min": VALVE_MOUTH_MIN,
        "max": VALVE_MOUTH_MAX,
        "step": 0.5,
        "default": DEFAULT.valve_mouth_dia,
    },
    {
        "name": "valve_seat_dia",
        "label": "Valve cup seat (mm)",
        "type": "number",
        "min": VALVE_SEAT_MIN,
        "max": VALVE_SEAT_MAX,
        "step": 0.5,
        "default": DEFAULT.valve_seat_dia,
    },
    {
        "name": "cup_depth",
        "label": "Valve cup depth (mm)",
        "type": "number",
        "min": CUP_DEPTH_MIN,
        "max": CUP_DEPTH_MAX,
        "step": 0.5,
        "default": DEFAULT.cup_depth,
    },
]


def create(
    blower_mouth_dia: float = DEFAULT.blower_mouth_dia,
    blower_throat_dia: float = DEFAULT.blower_throat_dia,
    socket_depth: float = DEFAULT.socket_depth,
    valve_mouth_dia: float = DEFAULT.valve_mouth_dia,
    valve_seat_dia: float = DEFAULT.valve_seat_dia,
    cup_depth: float = DEFAULT.cup_depth,
) -> Part:
    """WOLFBOX MF100 to Therm-a-Rest WingLock inflation adapter."""
    return build(
        Adapter.of(
            blower_mouth_dia=blower_mouth_dia,
            blower_throat_dia=blower_throat_dia,
            socket_depth=socket_depth,
            valve_mouth_dia=valve_mouth_dia,
            valve_seat_dia=valve_seat_dia,
            cup_depth=cup_depth,
        )
    )


__all__ = [
    "DEFAULT",
    "PARAMS",
    "Adapter",
    "bore_profile",
    "build",
    "config",
    "create",
]
