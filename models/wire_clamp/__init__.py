"""A screw clamp for 1 mm wire: reconstruction of Printables 591325, resized.

    uv run show wire_clamp                # the assembled clamp, with wire
    uv run export wire_clamp.printable    # both parts, one plate
    uv run check wire_clamp

A cylinder with a window through it, a slot under the window, and a thumbscrew
that drives a plunger down into the slot. Thread a loop of wire in through one
side and out the other, turn the knob, and the plunger pulls the wire down over
one sill, flat along a ribbed floor, and back up over the other -- so what holds
it is four bends and a squeeze, not a squeeze alone. Back the knob off and the
wire runs free again, which is what makes it a tensioner rather than a knot.

**The original is Twotone74's, and it is a good design.** It is published for 3
to 12 mm rope as ten files, and the ten are one shape scaled ten ways: every
feature, thread included, is a fixed multiple of the rope diameter. Measuring
all ten against each other is where this package's numbers come from --
``docs/reverse-engineering.md`` has the ratios and how they were read off.

**Two things had to change to get to 1 mm wire, and they are the whole point.**

*The thread's profile does not scale.* At 6 mm rope the original's thread has a
2.16 mm pitch and a 0.60 mm tooth and prints beautifully. At 3 mm rope the same
ratios give a 1.08 mm pitch and a **0.30 mm tooth** -- a crest narrower than one
0.4 mm extrusion and five layers to a turn -- so it does not come out tight, it
does not come out at all, and in ABS the warp on a 9 mm cylinder is larger than
the whole tooth. Scaled the rest of the way to 1 mm it would be a 3 mm bead with
a 0.36 mm pitch.

So the thread here is split in two. **Pitch, tooth height, crest flat and
clearance are absolute** -- 2.5 mm, 0.75 mm, 0.5 mm, 0.5 mm, at 45 degrees --
and are the same at every position of the slider, because those four are what a
nozzle has to resolve and each of them has a floor. The thread's **diameter**
does follow the wire, from an 8 mm floor upward, because that is the one thread
dimension with no floor to fall through: the plunger has to pass through the
thread to be assembled, so the thread caps how wide a pair of strands can be,
and a bigger thread is strictly easier to print than a smaller one. The original
scales the numbers a printer has to hit; this scales the number a printer does
not care about.

*The plunger lets the wire past.* The original's plunger is a disc 0.3 mm
smaller than a round bore, so nothing thicker than 0.3 mm gets under it -- a
rope is nipped between the plunger's rim and the window sill and squashed, which
works fine on something compressible with a lot of surface. A 1 mm wire is stiff
and slippery and a rim nip on plastic yields the plastic first. So the channel
here is a **slot**: as wide as the plunger, which guides it and stops a strand
escaping sideways, and longer than the plunger by a wire's width at each end, so
the wire's two legs run down past it and get clamped against the ribbed floor
with four bends in them.

Everything else is the original's: the proportions of the window, the ribbed
floor, the concentric ridges on the plunger's face that cross those ribs, the
ten-lobed knob flush with the body.

**Printing.** ABS, which is what the failure being fixed was printed in; PETG
and PLA print the same files and are both more forgiving. Both parts are in
print pose already: the body stands on its base, the screw lies **knob down**,
and neither needs support. 4 perimeters, 0.2 mm layers or finer -- the thread
wants at least six layers to a turn and 2.5 mm of pitch gives twelve. Nothing
overhangs past 45 degrees except the top of the window, which is a 4.9 mm
bridge.

**Assembling it.** Screw the knob in from the top. It cannot be put in wrong and
cannot fall out of an open clamp: with the plunger backed up clear of the
window, a full turn and a half of thread is still engaged.

**Parametric, in one number.** ``wire_d``, 0.5 to 4.0 mm, and it sizes the whole
clamp: window, sill, slot, floor ribs, plunger, knob lobes, thread diameter,
body diameter and body height all follow it. A 0.5 mm clamp is 11 x 16 mm; a
4 mm one is 21 x 27 mm.

The slider is on the assembly *and* on all three printable models, because the
website reads ``PARAMS`` off whichever model is on screen -- a slider declared
only on the scene would be a slider on the one page with no download button.
``wire_clamp.printable`` is the one to take if you want a guaranteed matched
pair: both parts come off the same setting.

What the slider cannot reach is the thread's profile, which is the entire lesson
of the model. So it is safe in a way the original's is not: **no position of it
can produce a thread the printer cannot resolve.** Above 4 mm the original's own
files are the better answer -- rope that thick is compressible enough that its
rim-nip works -- and they start at 3.1 mm.
"""

from __future__ import annotations

from build123d import Compound, Part, Pos, Rot

from ..lib.edges import as_part
from . import body, config, screw
from .config import (
    STRANDS,
    THREAD_D_MIN,
    THREAD_PITCH,
    WIRE_DEFAULT,
    WIRE_MAX,
    WIRE_MIN,
    Clamp,
    DEFAULT,
)
from .wire import wire_strands

IS_ASSEMBLY = True
"""A scene, not a print job: it is two parts and a wire in their use pose. The
things you print are ``wire_clamp.body``, ``wire_clamp.screw`` and
``wire_clamp.printable``."""

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


def screw_turn(c: Clamp, at: float) -> float:
    """Rotation, in degrees, that puts the screw's thread in the body's at ``at``.

    A thread is a helix, so height and angle are the same variable: the male and
    female profiles here are the *same* trapezoid, generated in phase, so at
    ``closed_z`` with no rotation each male tooth would sit exactly where a
    female tooth already is. Half a pitch of rotation puts it in the groove
    instead, and every millimetre of travel from there is another
    ``360 / pitch`` degrees.

    ``checks.py`` uses this to assert the two solids never intersect anywhere in
    the travel, which is the only honest test of a printed thread's clearance --
    a clearance that is right at one height and wrong at another is a thread
    that binds, and no single-position check can see it.
    """
    return 180.0 + 360.0 * (at - c.closed_z) / THREAD_PITCH


def screw_at(c: Clamp, at: float) -> Part:
    """The screw, posed on the body with its ridge tips at height ``at``."""
    return as_part(Pos(0, 0, at) * (Rot(0, 0, screw_turn(c, at)) * screw.build_upright(c)))


def build(c: Clamp = DEFAULT) -> Compound:
    """The clamp closed on a loop of wire, in its use pose."""
    at = c.clamped_z
    parts = [body.build(c), screw_at(c, at), *wire_strands(c)]
    return Compound(children=parts)


def create(wire_d: float = WIRE_DEFAULT) -> Compound:
    """The assembled wire clamp, clamped on ``STRANDS`` strands of wire."""
    return build(Clamp.of(wire_d))


__all__ = [
    "DEFAULT",
    "IS_ASSEMBLY",
    "PARAMS",
    "STRANDS",
    "THREAD_D_MIN",
    "Clamp",
    "body",
    "build",
    "config",
    "create",
    "screw",
    "screw_at",
    "screw_turn",
    "wire_strands",
]
