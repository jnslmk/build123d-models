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

from bd_warehouse.thread import Thread
from build123d import Part

from .config import THREAD_FLAT, THREAD_PITCH, THREAD_ROOT_W, Clamp


def _thread(apex_r: float, root_r: float, length: float) -> Part:
    """One thread, faded at both ends, built **outside** any builder.

    ``Thread`` is a ``BasePartObject``: constructing one inside a ``BuildPart``
    adds it to that builder there and then, at the origin. Every caller here is
    expected to build it out of scope and place it once -- see
    ``build123d-geometry-ops``, gotchas 6, and ``models/led_profiles/endcap.py``
    for the version of this that cost a session.

    ``end_finishes=("fade", "fade")`` is the modelling rule from
    ``references/threads.md``: a thread that starts at a knife edge curls off
    whatever it was printed on and then gets dragged around by the nozzle.
    """
    return Thread(
        apex_radius=apex_r,
        apex_width=THREAD_FLAT,
        root_radius=root_r,
        root_width=THREAD_ROOT_W,
        pitch=THREAD_PITCH,
        length=length,
        end_finishes=("fade", "fade"),
    )


def female(c: Clamp, length: float) -> Part:
    """Internal thread: teeth pointing in from a bore of ``c.female_root_r``."""
    return _thread(c.female_crest_r, c.female_root_r, length)


def male(c: Clamp, length: float) -> Part:
    """External thread: teeth standing out from a shank of ``c.male_root_r``."""
    return _thread(c.male_crest_r, c.male_root_r, length)
