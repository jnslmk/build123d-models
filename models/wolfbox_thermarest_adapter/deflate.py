"""Adapter that lets the same air duster *empty* a Therm-a-Rest pad.

    uv run show wolfbox_thermarest_adapter.deflate
    uv run export wolfbox_thermarest_adapter.deflate   # the STL to print
    uv run check wolfbox_thermarest_adapter

The package's headline part hangs a funnel off the duster's **outlet** and
blows the pad up. This one hangs the same funnel off its **intake** and sucks
the pad down. Nothing about the tool changes and no vacuum mode is needed: a
fan that blows out of one end is pulling in at the other the whole time, and
all this part does is decide where that air comes from.

**The two ends of a blower are not the same kind of thing, and that is the
whole design.** The outlet is a port with a bayonet collar, so the inflate
adapter pushes a socket *into* it. The intake is a fixed grille around the fan
disc -- nothing to push into, nothing to twist onto -- so this one is a cap
that swallows the tail of the baton and seals on the barrel's *outside*. Cover
the grille and every cubic centimetre the fan draws has to come up the cup:
the pad empties through the duster instead of past it.

**Suction makes this the easy end.** On the inflate adapter the blower's own
thrust is trying to push the socket off the port and the cup off the valve, and
hand pressure is what resists it. Here the pressure difference runs the other
way -- it seats the cap harder onto the barrel and the cup harder onto the
valve for as long as the fan is running. Nothing has to hold on; it only has to
not leak. That is also why this part latches no more than the other one does:
let go and it falls off, which is the correct behaviour for a thing pressed
against an air mattress.

**Four cones and a neck.** Tail cap, 45 degree shoulder, straight throat,
45 degree flare, valve cup -- and every diameter in that chain is assumed
rather than measured, exactly as ``config.py`` says. The cap covers barrels
from 34 to 46 mm and the cup valves from 22 to 34 mm; six sliders move both.

**Printing.** PETG, no supports, already in print pose: the cap's mouth flat on
the bed, the cup's mouth up. The bore's steepest downward-facing surface is the
45 degree shoulder off the tail cone, which is the limit that prints dry. The
cup wall stays 1.2 mm because it is still the sealing face; the neck is 2.8 mm
because a 160 mm baton hanging off a 46 mm cap is a lever and the neck is its
root. TPU 95A seals better here too, and gives up nothing but that stiffness.

**It is a duct, not a nozzle, so keep the runs short.** Sealing the intake
means the motor's cooling air is now coming through the pad. Emptying a
sleeping pad is a half-minute job and nothing gets warm; leaving the duster
running on a sealed cap is not something this part is designed for.
"""

from __future__ import annotations

from build123d import Part

from . import config
from .config import (
    BED_CHAMFER,
    BODY_MOUTH_MAX,
    BODY_MOUTH_MIN,
    BODY_SEAT_MAX,
    BODY_SEAT_MIN,
    CAP_DEPTH_MAX,
    CAP_DEPTH_MIN,
    CUP_DEPTH_MAX,
    CUP_DEPTH_MIN,
    INTAKE_DEFAULT,
    MOUTH_CHAMFER,
    NECK_WALL,
    RIM_CHAMFER,
    VALVE_MOUTH_MAX,
    VALVE_MOUTH_MIN,
    VALVE_SEAT_MAX,
    VALVE_SEAT_MIN,
    IntakeAdapter,
)
from .profile import Point, revolve_section, trim

# Index of each corner in the raw section, so the break table reads as a place
# rather than a number. The loop is drawn the same way round as the inflate
# adapter's: up the inside from the bed, across the rim, down the outside, and
# back across the bed.
MOUTH_INNER = 0  # bed-side mouth of the tail cap, on the bore
RIM_INNER = 5  # cup rim, on the bore
RIM_OUTER = 6  # cup rim, on the outside
MOUTH_OUTER = 11  # bed-side mouth of the tail cap, on the outside


def bore_profile(a: IntakeAdapter) -> list[Point]:
    """The inside of the part, bed to rim, as ``(radius, height)`` corners.

    Public because it is what the checks measure against: the bore here is four
    surfaces rather than the inflate adapter's two, so "where should the wall
    be at this height" is a question about *this list* and not about a pair of
    named cones.
    """
    return [
        (a.body_mouth_r, 0.0),  # MOUTH_INNER
        (a.body_seat_r, a.z_cap),
        (a.throat_r, a.z_throat),
        (a.throat_r, a.z_throat_top),
        (a.seat_r, a.z_seat),
        (a.rim_r, a.z_rim),  # RIM_INNER
    ]


def _section(a: IntakeAdapter) -> list[Point]:
    """The closed half-section, before any corner is broken.

    The outside is a chain of offsets from the bore rather than a shape of its
    own: cap wall around the tail cone, neck wall around the throat and the
    shoulder between them, cup wall around the cup. Each offset is horizontal
    but sized from the cone's own slope (``_normal_offset`` in ``config``), so
    what the print actually gets is the wall measured normal to the surface.
    """
    cap = a.cap_wall_offset()
    cup = a.cup_wall_offset()
    return [
        *bore_profile(a),
        (a.rim_r + cup, a.z_rim),  # RIM_OUTER
        (a.seat_r + cup, a.z_seat),
        (a.throat_r + NECK_WALL, a.z_throat_top),
        (a.throat_r + NECK_WALL, a.z_throat),
        (a.body_seat_r + cap, a.z_cap),
        (a.body_mouth_r + cap, 0.0),  # MOUTH_OUTER
    ]


def _breaks() -> dict[int, float]:
    """Which corners get broken, and by how much.

    The same four the inflate adapter breaks, in the same places and for the
    same reasons: the two mouths the part is pushed onto something by, and the
    two lips of the rim it is pressed down by. Every other corner in the loop
    is either concave or already blunt -- the sharpest convex one left is the
    145 degree kink where the tail cone meets its shoulder, well clear of the
    120 the sharp-edge check calls sharp, and ``check_edges`` is what holds
    that claim to account rather than this comment.
    """
    return {
        MOUTH_INNER: MOUTH_CHAMFER,  # lead-in: the cap has to start on the tail
        RIM_INNER: RIM_CHAMFER,
        RIM_OUTER: RIM_CHAMFER,
        MOUTH_OUTER: BED_CHAMFER,  # elephant's-foot relief
    }


def build(a: IntakeAdapter = INTAKE_DEFAULT) -> Part:
    """The deflate adapter as one revolved solid, seated on the bed."""
    return revolve_section(trim(_section(a), _breaks()))


# UI schema for the parametric web app. See tessellate_models.model_params().
PARAMS = [
    {
        "name": "body_mouth_dia",
        "label": "Tail cap mouth (mm)",
        "type": "number",
        "min": BODY_MOUTH_MIN,
        "max": BODY_MOUTH_MAX,
        "step": 0.5,
        "default": INTAKE_DEFAULT.body_mouth_dia,
    },
    {
        "name": "body_seat_dia",
        "label": "Tail cap seat (mm)",
        "type": "number",
        "min": BODY_SEAT_MIN,
        "max": BODY_SEAT_MAX,
        "step": 0.5,
        "default": INTAKE_DEFAULT.body_seat_dia,
    },
    {
        "name": "cap_depth",
        "label": "Tail cap depth (mm)",
        "type": "number",
        "min": CAP_DEPTH_MIN,
        "max": CAP_DEPTH_MAX,
        "step": 1.0,
        "default": INTAKE_DEFAULT.cap_depth,
    },
    {
        "name": "valve_mouth_dia",
        "label": "Valve cup rim (mm)",
        "type": "number",
        "min": VALVE_MOUTH_MIN,
        "max": VALVE_MOUTH_MAX,
        "step": 0.5,
        "default": INTAKE_DEFAULT.valve_mouth_dia,
    },
    {
        "name": "valve_seat_dia",
        "label": "Valve cup seat (mm)",
        "type": "number",
        "min": VALVE_SEAT_MIN,
        "max": VALVE_SEAT_MAX,
        "step": 0.5,
        "default": INTAKE_DEFAULT.valve_seat_dia,
    },
    {
        "name": "cup_depth",
        "label": "Valve cup depth (mm)",
        "type": "number",
        "min": CUP_DEPTH_MIN,
        "max": CUP_DEPTH_MAX,
        "step": 0.5,
        "default": INTAKE_DEFAULT.cup_depth,
    },
]


def create(
    body_mouth_dia: float = INTAKE_DEFAULT.body_mouth_dia,
    body_seat_dia: float = INTAKE_DEFAULT.body_seat_dia,
    cap_depth: float = INTAKE_DEFAULT.cap_depth,
    valve_mouth_dia: float = INTAKE_DEFAULT.valve_mouth_dia,
    valve_seat_dia: float = INTAKE_DEFAULT.valve_seat_dia,
    cup_depth: float = INTAKE_DEFAULT.cup_depth,
) -> Part:
    """WOLFBOX MF100 intake to Therm-a-Rest WingLock deflation adapter."""
    return build(
        IntakeAdapter.of(
            body_mouth_dia=body_mouth_dia,
            body_seat_dia=body_seat_dia,
            cap_depth=cap_depth,
            valve_mouth_dia=valve_mouth_dia,
            valve_seat_dia=valve_seat_dia,
            cup_depth=cup_depth,
        )
    )


__all__ = [
    "INTAKE_DEFAULT",
    "PARAMS",
    "IntakeAdapter",
    "bore_profile",
    "build",
    "config",
    "create",
]
