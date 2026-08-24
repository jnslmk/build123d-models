"""The one thread profile, built once for whichever half asks for it.

Both halves of this clamp are the *same* 45 degree trapezoid -- flat crest, flat
root, flanks at 45 degrees from the perpendicular -- shifted radially by half
the diametral clearance and nothing else. That is the property the 45 degree
flank is chosen for, over and above its overhang: on a 45 degree flank a radial
shift moves the flanks apart along their own normal by the same amount, so one
clearance number sets the radial gap at crest and root *and* the axial gap on
the flanks. There is no second clearance to get wrong, and no way for the thread
to end up loose on one axis and binding on the other -- the failure
``fasteners-and-inserts``' ``references/threads.md`` warns is what you get when
clearance is applied on the wrong axis for the profile.

``bd_warehouse``'s general ``Thread`` takes exactly this shape as four numbers:
a radius and a width at the crest, a radius and a width at the root. Everything
else about it is the same for both halves.

The four radii come from the ``Clamp`` because the thread's **diameter** follows
the wire; the two *widths* and the pitch are module constants because the
profile does not. That split is the whole model -- see ``config.py``.
"""

from __future__ import annotations

from typing import Literal

from bd_warehouse.thread import Thread
from build123d import Part

from .config import THREAD_FLAT, THREAD_PITCH, THREAD_ROOT_W, Clamp

WHOLE_TURN_EPS = 1e-6
"""How close to a whole number of turns counts as *on* it.

``bd_warehouse`` builds a thread as a stack of whole loops plus one partial
loop, and decides whether the partial one exists with a bare
``if self.thread_loops % 1 > 0.0`` (``bd_warehouse/thread.py``, in ``Thread``).
An exact multiple of the pitch is therefore fine -- the partial loop is skipped
-- and so is any honest fraction. What is not fine is a length a *hair over* a
multiple: ``15.000000000000004 / 2.5`` leaves a remainder of 1.8e-15, the guard
passes, and it builds a helix four femtometres tall. OCC's ``GCPnts_AbscissaPoint``
raises ``Standard_ConstructionError`` sampling it, and the whole model fails to
build.

Which side of that line a length lands on is float noise, not design: at 5.6 mm
of wire this model wants a 15 mm male thread and gets 15.000000000000004. So the
lengths are snapped onto the exact multiple below, which moves them by about
1e-15 mm -- nothing geometrically, and the difference between a part and an
exception. ``checks.py`` sweeps the whole slider for it."""


def _whole_turn_safe(length: float) -> float:
    """A thread length that cannot land a hair off a whole number of turns.

    Reproduces ``Thread``'s own arithmetic rather than guessing at it: with both
    ends faded it builds ``(length - pitch) / pitch`` loops, so that is the
    quantity whose fractional part has to stay away from zero. Lengths that are
    not near a whole turn are returned untouched.
    """
    loops = (length - THREAD_PITCH) / THREAD_PITCH
    frac = loops % 1
    if frac < WHOLE_TURN_EPS or frac > 1 - WHOLE_TURN_EPS:
        return round(loops) * THREAD_PITCH + THREAD_PITCH
    return length


EndFinish = Literal["raw", "square", "fade", "chamfer"]


def _thread(
    apex_r: float, root_r: float, length: float, top: EndFinish = "fade"
) -> Part:
    """One thread, faded at both ends, built **outside** any builder.

    ``Thread`` is a ``BasePartObject``: constructing one inside a ``BuildPart``
    adds it to that builder there and then, at the origin. Every caller here is
    expected to build it out of scope and place it once -- see
    ``build123d-geometry-ops``, gotchas 6, and ``models/led_profiles/endcap.py``
    for the version of this that cost a session.

    The bottom end always fades: that is the modelling rule from
    ``references/threads.md``, because a thread starting at a knife edge curls
    off whatever it was printed on and then gets dragged around by the nozzle.
    ``top`` is ``"fade"`` for the male thread and ``"chamfer"`` for the female
    one -- see ``female``.
    """
    return Thread(
        apex_radius=apex_r,
        apex_width=THREAD_FLAT,
        root_radius=root_r,
        root_width=THREAD_ROOT_W,
        pitch=THREAD_PITCH,
        length=_whole_turn_safe(length),
        end_finishes=("fade", top),
    )


def female(c: Clamp, length: float) -> Part:
    """Internal thread: teeth pointing in from a bore of ``c.female_root_r``.

    **Chamfered at the top rather than faded, and that is worth 3.3 mm of body.**
    A bore's mouth needs a lead-in so the screw starts square, and the house way
    to cut one is a boolean cone -- which then has to be kept a full pitch clear
    of the thread's first turn, because a cone cut *into* a bd_warehouse thread
    makes OCC's fuse hand back the thread and drop the rest of the part. Cone
    plus pitch is 3.3 mm of plain bore above the thread, and the male thread has
    to be that much longer to cross it.

    ``end_finishes``' own ``"chamfer"`` does the same job from the inside: it
    clips the last turn conically instead of tapering it to nothing, so the
    thread *is* the lead-in and the bore can end where the thread does. No cone,
    no collar, no gotcha to keep clear of.
    """
    return _thread(c.female_crest_r, c.female_root_r, length, top="chamfer")


def male(c: Clamp, length: float) -> Part:
    """External thread: teeth standing out from a shank of ``c.male_root_r``."""
    return _thread(c.male_crest_r, c.male_root_r, length)
