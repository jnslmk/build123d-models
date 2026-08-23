"""The clamp's thumbscrew: knob, thread, plunger.

    uv run export wire_clamp.screw

**Print pose is upside down from the use pose**, and that is the whole reason
this module ends with a flip. Knob down, the first layer is a 12 mm disc and
everything above it gets narrower; plunger down, the first layer is a 6 mm disc
and the knob arrives 13 mm up as a 3 mm unsupported ledge all the way round.
The concentric ridges on the plunger's face therefore print as *top* features,
which is where a 0.3 mm bump is crispest.

The thread starts 6 mm above the bed either way, which satisfies
``references/threads.md``'s "never start a thread at z = 0" without a collar
being added for it: the knob and the shank collar are already there.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Cylinder,
    Kind,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Pos,
    Torus,
    add,
    fillet,
    loft,
    offset,
)

from ..lib.edges import as_part, reseat_on_bed
from . import thread as tp
from .config import (
    COLLAR_H,
    DEFAULT,
    KNOB_CHAMFER,
    KNOB_H,
    KNOB_LOBES,
    PLUNGER_CHAMFER,
    RING_COUNT,
    RING_H,
    WIRE_DEFAULT,
    WIRE_MAX,
    WIRE_MIN,
    Clamp,
)

_BASE = (Align.CENTER, Align.CENTER, Align.MIN)


def ring_radii(c: Clamp) -> list[float]:
    """Where the concentric ridges sit on the plunger's face.

    Spread evenly from the axis out to the last radius that still clears the
    nose chamfer. Concentric rather than straight because the plunger arrives at
    whatever rotation the thread stops it at, and a feature that only grips at
    one angle grips at none.
    """
    outer = c.plunger_r - PLUNGER_CHAMFER - RING_H
    step = outer / RING_COUNT
    return [step * (i + 1) for i in range(RING_COUNT)]


def knob_profile(c: Clamp, shrink: float = 0.0):
    """The knob's ten-lobed outline, optionally offset inwards.

    ``shrink`` is a real 2D offset, not a scale: scaling a lobed profile changes
    how deep the lobes are, and the chamfer this feeds would then be a different
    depth on the tips than in the scallops.
    """
    with BuildSketch() as sk:
        Circle(c.body_r)
        with PolarLocations(
            c.body_r - c.knob_lobe_depth + c.knob_lobe_r, KNOB_LOBES
        ):
            Circle(c.knob_lobe_r, mode=Mode.SUBTRACT)
        fillet(sk.vertices(), c.knob_tip_r)
        if shrink:
            offset(amount=-shrink, kind=Kind.INTERSECTION, mode=Mode.REPLACE)
    return sk.sketch


def build_upright(c: Clamp = DEFAULT) -> Part:
    """The screw in its **use** pose: ridge tips on z=0, knob uppermost.

    This is the frame every height in ``config`` is written in, which is why it
    is a separate function: the assembly places this one straight onto the body
    at ``closed_z`` or ``open_z`` and the arithmetic reads off. ``build`` turns
    it over for the bed.
    """
    # Outside the builder, once -- see ``body.build`` and gotchas 6.
    thread = tp.male(c, c.male_len)

    z_thread = c.plunger_len
    z_collar = z_thread + c.male_len
    z_knob = z_collar + COLLAR_H

    # Built nose-down (the use pose) and flipped at the end, because every
    # height in ``config`` is measured from the plunger's own tips: the
    # kinematics read straight off the model this way round.
    with BuildPart() as bp:
        # Plunger, bottom up: the ridges hang below its face, so the face sits
        # one ridge height off the datum and the tips land on z=0 -- which is
        # where every height in ``config`` is measured from.
        with Locations((0, 0, RING_H)):
            Cone(
                c.plunger_r - PLUNGER_CHAMFER,
                c.plunger_r,
                PLUNGER_CHAMFER,
                align=_BASE,
            )
        neck = c.plunger_r - c.male_root_r
        with Locations((0, 0, RING_H + PLUNGER_CHAMFER)):
            Cylinder(
                c.plunger_r,
                z_thread - PLUNGER_CHAMFER - RING_H - neck,
                align=_BASE,
            )
        # 45 degrees off the plunger down to the thread's core rather than a
        # step: the step would be 0.14 mm of raw ledge, which is both a sharp
        # edge and an overhang once the part is turned over to print.
        with Locations((0, 0, z_thread - neck)):
            Cone(c.plunger_r, c.male_root_r, neck, align=_BASE)
        with Locations((0, 0, z_thread)):
            Cylinder(c.male_root_r, c.male_len + COLLAR_H, align=_BASE)

        add(as_part(Pos(0, 0, z_thread) * thread))

        # Knob: chamfered both ends by lofting through an offset outline, so
        # neither horizontal edge is left raw and OCC is never asked to chamfer
        # ten scallops at once.
        for z, shrink in (
            (z_knob, KNOB_CHAMFER),
            (z_knob + KNOB_CHAMFER, 0.0),
            (z_knob + KNOB_H - KNOB_CHAMFER, 0.0),
            (z_knob + KNOB_H, KNOB_CHAMFER),
        ):
            with BuildSketch(Plane.XY.offset(z)):
                add(knob_profile(c, shrink))
        loft(ruled=True)

        # The ridges last: they are additive features on a face every earlier
        # step could have moved. Each is a torus centred on the face plane, so
        # its lower half stands proud and its tip is exactly tangent to z=0.
        for r in ring_radii(c):
            with Locations((0, 0, RING_H)):
                Torus(r, RING_H)

    return bp.part


def build(c: Clamp = DEFAULT) -> Part:
    """The screw in **print pose**: knob flat on the bed, plunger uppermost."""
    return reseat_on_bed(build_upright(c), flip=True)


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
"""The same one slider the assembly carries. It has to be repeated per module:
the website reads ``PARAMS`` off whichever model is on screen, and this is one
of the two you download an STL from -- so a screw built at one setting can never
be handed out beside a body built at another."""


def create(wire_d: float = WIRE_DEFAULT) -> Part:
    """The thumbscrew, print pose, knob on the bed."""
    return build(Clamp.of(wire_d))
