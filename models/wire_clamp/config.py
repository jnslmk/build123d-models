"""Every number the wire clamp is cut from, and which of two rules set it.

This is a reconstruction of Printables 591325, *Adjustable Rope Clamp / Rope
Tensioner (Parametric)* by Twotone74 -- a cylinder with a window through it, a
ribbed floor under the window, and a thumbscrew that drives a plunger down onto
whatever is threaded through. The original is published for 3 to 12 mm rope as
ten files that are **one shape scaled ten ways**; measuring all ten against each
other is what this package is built on, and the measurements are in
``docs/reverse-engineering.md``.

**The scaling is the bug.** Every feature of the original is a fixed multiple of
the rope diameter, the thread included::

    body OD           3.00 x d          thread pitch       0.36 x d
    body height       2.50 x d          thread tooth       0.10 x d (radial)
    female minor D    2.40 x d          radial clearance   0.05 x d
    female major D    2.60 x d          wall               0.30 x d

At 6 mm rope that gives a 2.16 mm pitch and a 0.60 mm tooth, which prints. At
3 mm rope the same ratios give a **1.08 mm pitch and a 0.30 mm tooth** -- a
crest narrower than one 0.4 mm extrusion, five layers to a turn at 0.2 mm, and
0.15 mm of radial clearance for the slicer to hit. That is a thread the printer
cannot resolve rather than a thread that came out tight, which is why the 3 mm
version does not work, and why filament makes it worse rather than better: ABS's
warp pulls a 9 mm cylinder out of round by more than the whole tooth is tall.
Scaled the rest of the way down to 1 mm wire it would be a 3 mm bead with a
0.36 mm pitch -- not a part.

**So this model has two rule sets, and they never mix.**

*The wire sets the cord features.* Window height, lip depth, floor-rib pitch:
each is a multiple of ``wire_d``, because each is about the thing being clamped.
These are the ``PARAMS`` sliders.

*The nozzle sets the thread.* ``THREAD_D``, ``THREAD_PITCH``, ``THREAD_DEPTH``
and ``THREAD_CLEAR`` are absolute millimetres and do not move when ``wire_d``
does. They come from the printable-thread table in the ``fasteners-and-inserts``
skill (``references/threads.md``), which is the one place in this repo that owns
thread numbers -- a 45 degree flank (a 45 degree overhang, the house limit
exactly), crest and root flats at or above one extrusion width, at least six
layers to a pitch, and 0.50 mm of diametral clearance for a printed male in a
printed female. A 1 mm wire clamp is therefore **Ø11 x 17 mm**, and it is that
size because the thread is, not because the wire is.

**Material: ABS**, unusually for this repo -- the failure being fixed was an ABS
one, and the sizes below are the ones that survive it. It prints in PETG or PLA
unchanged; both are more forgiving than the material it was sized for.

**Clearances.** Everything that is not the thread goes through
``models.lib.fits`` by name, per the house rule. The thread does not, and that
is deliberate: ``fits.for_material(x, "abs")`` subtracts 0.15 mm because ABS
parts come off the bed undersized, and subtracting clearance is the exact
opposite of the fix this model exists for. Both halves of a printed thread
shrink together, so the shrink very nearly cancels in the fit; what does not
cancel is warp, and warp wants *more* room, not less.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..lib import fits

MATERIAL = "abs"

# ---------------------------------------------------------------------------
# The thread. Absolute millimetres, set by the nozzle. Nothing here is allowed
# to depend on the wire -- that dependency is the defect being fixed.
# ---------------------------------------------------------------------------

THREAD_D = 8.0
"""Basic major diameter: the female thread's root and the male's basic crest."""

THREAD_PITCH = 2.5
"""Coarse on purpose. ``references/threads.md``: standard pitch scales with
diameter and gets absurdly fine at the small end, so when both halves are yours,
override it. 12.5 layers per turn at 0.2 mm, against the >= 6 the same table
asks for; the original's 3 mm version manages 5.4."""

THREAD_DEPTH = 0.75
"""Radial tooth height. 1.9 extrusions at 0.4 mm, against the original 3 mm
version's 0.30 mm -- which is 0.75 of one extrusion, i.e. not printable."""

THREAD_FLAT = 0.50
"""Crest and root flat. ``references/threads.md`` puts the floor at one
extrusion width; a crest narrower than the nozzle is dropped or fattened
unpredictably by the slicer. With a 45 degree flank the profile closes as
``FLAT + 2 x DEPTH + FLAT = PITCH``, which is what fixes the pitch above."""

THREAD_CLEAR = 0.50
"""Total diametral, printed male in printed female, V profile. The "first
attempt, or PETG" row of the clearance table, kept rather than tightened: see
the module docstring on why ABS does not get the ``fits`` material discount.

On a 45 degree flank a purely radial offset opens the flanks by the same amount
along their normal, so this one number is simultaneously the radial gap at crest
and root and the axial gap on the flanks. That is the reason for the 45 degree
profile beyond its overhang: there is no second clearance to get wrong."""

THREAD_ENGAGE_MIN = 8.0
"""Floor on the female thread's length: 1.0 x D, from ``references/threads.md``.
Printed threads share load across turns much worse than cut ones. The thread is
lengthened past this when the plunger's travel demands it -- see
``Clamp.thread_engage``, which is the only number in the thread that the wire is
allowed to move, and it can only make it longer."""

MOUTH_COLLAR = 2.5
"""Plain bore above the thread, one full pitch. Two rules land on the same
millimetre here: a thread must not start at a lead-in, and a lead-in cone cut
into a bd_warehouse thread makes OCC's fuse return the thread alone and drop the
rest of the part (``build123d-geometry-ops``, gotchas 7)."""

# Derived thread radii. The male is shifted in by half the diametral clearance
# and the female is left on basic size, which is where ``references/threads.md``
# says to put it for a V profile ("shrink the major diameter of the male").
FEMALE_ROOT_R = THREAD_D / 2
FEMALE_CREST_R = FEMALE_ROOT_R - THREAD_DEPTH
MALE_CREST_R = FEMALE_ROOT_R - THREAD_CLEAR / 2
MALE_ROOT_R = MALE_CREST_R - THREAD_DEPTH
THREAD_ROOT_W = THREAD_FLAT + 2 * THREAD_DEPTH
"""Tooth width at the root. With ``THREAD_FLAT`` at the crest this is the whole
45 degree trapezoid, and it is the same trapezoid for both halves."""

CORE_R = MALE_ROOT_R
"""The screw's shank under the thread: the thread's own root radius, so the
shank and the thread are one cylinder with teeth on it rather than two."""

PLUNGER_R = FEMALE_CREST_R - fits.SLIDING / 2
"""The disc on the end of the shank, fatter than the shank itself.

Sized off the channel bore -- which is the female crest, because the plunger has
to pass through the thread to be assembled -- at ``fits.SLIDING``, the class for
something that moves along its axis while staying located. It is not run through
``fits.for_material``: ABS's -0.15 mm would take a 0.22 mm clearance to 0.07 mm,
which is a press fit for a printed bore, and the same shrink-cancels-between-two-
ABS-parts argument the thread clearance makes applies here. The gap that matters
is the one a strand could escape up, and 0.11 mm a side is well under any wire
this clamp is for."""

# ---------------------------------------------------------------------------
# The body shell. Wall and base are absolute; everything about the cord channel
# is derived from the wire in ``Clamp`` below.
# ---------------------------------------------------------------------------

WALL = 1.5
"""Over the thread's root, so it is the thinnest the shell ever gets where the
thread is: ~4 perimeters at 0.4 mm, which is what ``references/threads.md`` asks
for so that a thread is never printed into infill. The original runs 1.2 mm here
at 6 mm rope and 0.6 mm at 3 mm, i.e. 1.5 perimeters."""

WALL_Y = 1.0
"""Beside the wire passages, at the two ends of the channel. Thinner than
``WALL`` on purpose and allowed to be: it is a 1.2 mm tall band of shell at the
bottom of the channel and a 0.6 mm one at the top, and the screw's thrust runs
down the two pillars either side of the window, not through here."""

BASE_T = 1.4
"""Solid floor under the channel."""

RIB_H = 0.35
"""Height of the floor ribs, and their half-round radius: they are half
cylinders, so one number does both. 1.75 extrusions wide at the base."""

HEAD = 0.6
"""Solid ring between the top of the window and the top of the channel, so the
window is a hole with material all round it rather than a slot open at the
top."""

LIP_CHAMFER = 0.4
"""45 degree break on the channel's rim at the sill and again at the lintel --
the two edges the wire is deliberately bent over, so the two that must not be
knife edges. A break here is a bend radius for the wire and a load-spreading
foot for the plastic under it, and it costs the bend almost nothing.

Not cut as a separate tool: the channel is simply **wider over the window's
height** by this much all round, so the break is a step in the channel's own
profile rather than a frustum subtracted across it. That is not decoration. A
frustum subtracted at the sill has to have void above it everywhere it reaches,
and the window -- a stadium -- is at its *narrowest* exactly at the sill, so a
frustum sized to break the sill instead cuts a V-groove ring into the channel
wall: an undercut, in a bore, facing the wrong way for the printer. Profiled
into the channel it cannot miss, because there is nothing above it to miss."""

WINDOW_FLARE = 0.5
"""How much wider the window is where it breaks the outside than in the middle
of the wall. Cut as a loft, which breaks both mouths without asking OCC to
fillet a stadium hole in a cylinder."""

# The step from the channel slot up to the round thread bore is a 45 degree
# loft, sized in ``Clamp.step_cone``: it has to open out across the wire and
# neck *in* along it, and 45 degrees in both is what keeps every face of it
# printable and doubles it as the plunger's lead-in.

BOTTOM_CHAMFER = 0.5
TOP_CHAMFER = 0.6
MOUTH_LEAD_IN = 0.8

# ---------------------------------------------------------------------------
# The screw.
# ---------------------------------------------------------------------------

COLLAR_H = 1.0
"""Plain shank between the last thread turn and the knob's underside."""

KNOB_H = 5.0
# The knob is flush with the body, as the original is: the knob is the largest
# thing on the part and the body is the second, so making them equal means one
# diameter to clear rather than two. It is therefore ``Clamp.body_r``, not a
# constant -- the body grows with the wire, because the wire's passages do.

KNOB_LOBES = 10
KNOB_LOBE_DEPTH = 0.9
KNOB_LOBE_R = 1.2
"""Radius of the ten circles cut out of the knob's rim. Big enough that the
scallops are a grip and not a knurl -- a knurl needs a tool, and a printed one
under about 1 mm just prints as a rough cylinder."""

KNOB_TIP_R = 0.8
"""Roll on the ten tips, where the rim circle meets each scallop. Without it
those are knife edges -- a cut circle crosses the rim at an angle, so the tooth
between two scallops comes to a point. Filleted in **2D**, on the profile,
before it is lofted: the house rule wants vertical edges rounded, and rounding
the sketch is the version of that which cannot fail.

Bigger than ``KNOB_CHAMFER`` on purpose. The chamfer is a 2D offset of this same
profile, and an offset inward eats a convex radius: at 0.5 mm of offset a 0.4 mm
tip would come back as a corner and put the knife edge on the bed layer."""

KNOB_CHAMFER = 0.5
"""Break on both horizontal edges of the knob, cut as a 2D offset lofted into
the profile rather than as an OCC chamfer: the knob's outline is ten concave
scallops meeting ten convex tips, which is exactly the kind of face
``build123d-geometry-ops`` says to stop asking OCC to chamfer."""

PLUNGER_CHAMFER = 0.5
"""Lead-in on the plunger's nose, so the screw starts square into the bore."""

RING_H = 0.3
"""Half-round ridges on the plunger's face, concentric so they bite at any
rotation. The floor's ribs are straight and cross them; that pairing is the
original's, and it is what stops a strand rolling out sideways."""

RING_COUNT = 3

# ---------------------------------------------------------------------------
# Wire. The one slider, and the only thing below that moves.
# ---------------------------------------------------------------------------

WIRE_MIN, WIRE_MAX = 0.5, 2.5
"""Two strands of ``WIRE_MAX`` are 5 mm across, in a 6 mm window. Above that the
window, not the thread, becomes the limit -- and a cord that big deserves the
original's proportional scaling, which works from about 4 mm up."""

WIRE_DEFAULT = 1.0
STRANDS = 2
"""What the clamp is *for*: a loop, both legs through the same window, the way
every photo of the original shows it used."""


@dataclass(frozen=True)
class Clamp:
    """One clamp's worth of numbers, wire-driven half only.

    Everything the thread cares about is a module constant above, because it is
    the same in every instance. Everything here moves with the wire.
    """

    wire_d: float = WIRE_DEFAULT

    @classmethod
    def of(cls, wire_d: float = WIRE_DEFAULT) -> Clamp:
        """Build one with the slider clamped back into a buildable range."""
        return cls(wire_d=min(max(float(wire_d), WIRE_MIN), WIRE_MAX))

    # -- the cord channel ---------------------------------------------------

    @property
    def window_h(self) -> float:
        """Window opening height. One strand plus room to thread it by hand;
        the two strands lie side by side across the width, not stacked."""
        return self.wire_d + 1.6

    @property
    def lip(self) -> float:
        """How far the floor sits below the window's sill.

        This is the whole holding mechanism and the reason the clamp is not just
        a pinch: the wire enters level, and the plunger pushes it down past two
        sills into the channel, so it leaves bent rather than merely squeezed.
        A pinch holds by friction alone and a thin wire has very little of it.
        """
        return max(0.8, 1.2 * self.wire_d)

    @property
    def channel_h(self) -> float:
        return self.lip + self.window_h + HEAD

    @property
    def wire_pass(self) -> float:
        """Width of the gap the wire drops through, at each end of the channel.

        **This is the one place this model departs from the original, and it is
        the second fix.** In the original the plunger is a disc 0.3 mm smaller
        than a round bore, so nothing thicker than 0.3 mm can pass it: a rope is
        not clamped against the floor at all, it is nipped between the plunger's
        rim and the window sill and squashed. That works on 6 mm rope, which is
        compressible and has enough surface to hold by friction alone. A 1 mm
        wire is neither -- it is stiff, it is slippery, and a rim nip on a
        plastic part yields the plastic long before it holds the wire.

        So the channel here is a **slot**, not a bore: the plunger's width is
        the slot's width, and the slot is longer than the plunger in the wire's
        own axis by exactly this much at each end. The wire's two legs run down
        those gaps, so tightening pulls the wire *through* -- down over one
        sill, flat along the ribbed floor under the plunger, up over the other
        -- and clamps it against the floor with four bends in it. Four bends
        hold a wire; a nip does not.

        ``fits.FREE``, because nothing here is a fit: the wire has to fall
        through the gap without being threaded into it.
        """
        return self.wire_d + fits.FREE

    @property
    def channel_w(self) -> float:
        """Slot width, across the wire. The female thread's minor diameter, so
        that one number does two jobs: the plunger passes through the thread to
        be assembled, and is then guided by these two flats at ``fits.SLIDING``.
        Guided in the axis that matters -- it is what stops a strand escaping
        sideways from under the plunger."""
        return 2 * FEMALE_CREST_R

    @property
    def channel_l(self) -> float:
        """Slot length, along the wire: the plunger plus a passage at each end."""
        return self.channel_w + 2 * self.wire_pass

    @property
    def body_r(self) -> float:
        """Whichever of the two things inside is bigger, plus its own wall.

        Usually the thread. The wire passages overtake it a little above 1 mm
        wire, and from there the body grows with the wire -- which is the honest
        answer rather than a defect: a thicker wire needs a wider slot and a
        wider slot needs a wider shell. What does *not* grow is the thread.
        """
        return max(
            FEMALE_ROOT_R + WALL,
            self.channel_l / 2 + LIP_CHAMFER + WALL_Y,
        )

    @property
    def window_w(self) -> float:
        """Chord across the window, in the axis the plunger does not use.

        Wider than the channel slot *and* its sill break, and that is load
        bearing on the modelling rather than on the part: it means everything
        the window opens into is already gone above the sill, so the sill and
        lintel breaks can be plain lofted frusta around the slot. Cut them
        narrower than the window and the same frustum grooves the channel wall
        instead of breaking an edge -- an undercut, in a bore, facing the wrong
        way for the printer, which is what the first draft of this model did.
        """
        return self.channel_w + 2 * LIP_CHAMFER + 0.2

    @property
    def rib_pitch(self) -> float:
        return max(1.0, 1.2 * self.wire_d)

    # -- heights, bed upward ------------------------------------------------

    @property
    def channel_top(self) -> float:
        return BASE_T + self.channel_h

    @property
    def window_z0(self) -> float:
        return BASE_T + self.lip

    @property
    def window_z1(self) -> float:
        return self.window_z0 + self.window_h

    @property
    def step_cone(self) -> float:
        """Height of the 45 degree transition from the channel slot to the
        thread bore. Whichever of the two directions has further to go: out by
        ``FEMALE_ROOT_R - channel_w / 2`` across the wire, in by
        ``channel_l / 2 - FEMALE_ROOT_R`` along it. The second one is the one
        that grows, and it is the reason this is not a constant."""
        return max(
            FEMALE_ROOT_R - self.channel_w / 2,
            self.channel_l / 2 - FEMALE_ROOT_R,
        )

    @property
    def thread_engage(self) -> float:
        """Female thread length.

        ``THREAD_ENGAGE_MIN`` normally, but never less than the plunger's travel
        plus a full pitch -- so that a screw backed right out to where the wire
        runs free still has a whole turn holding it, and cannot be dropped and
        lost. Travel is wire-driven; this is the one way the wire is allowed to
        touch the thread, and it can only ask for more of it.
        """
        return max(THREAD_ENGAGE_MIN, self.travel + THREAD_PITCH)

    @property
    def thread_z0(self) -> float:
        """First turn of the female thread, above the channel's 45 degree step."""
        return self.channel_top + self.step_cone

    @property
    def thread_z1(self) -> float:
        return self.thread_z0 + self.thread_engage

    @property
    def body_h(self) -> float:
        return self.thread_z1 + MOUTH_COLLAR

    # -- the screw, positioned off the body ---------------------------------

    @property
    def closed_z(self) -> float:
        """Where the plunger's ridge tips sit when the knob is home.

        On the rib tops, which is the *empty* clamp. Any wire at all keeps the
        knob proud of the body, so the knob can never bottom out and steal the
        clamping force -- and a knob that has gone flush is the tell that
        nothing is in there.
        """
        return BASE_T + RIB_H

    @property
    def clamped_z(self) -> float:
        """Where the plunger stops on a wire of this size.

        One wire diameter above ``closed_z``, which is the empty-clamp stop --
        so a wire is what holds the knob proud of the body, and how proud says
        how much is in there. Nothing depends on this but the assembly view and
        the checks that read it; the part has no stop at this height and does
        not need one.
        """
        return self.closed_z + self.wire_d

    @property
    def open_z(self) -> float:
        """Where the plunger has to get to for the wire to run free: clear of
        the top of the window."""
        return self.window_z1

    @property
    def plunger_len(self) -> float:
        """Ridge tips to the first male thread turn.

        Set so that "knob home" and "male thread starts exactly where the female
        one does" are the same position. That is an identity here rather than a
        coincidence, and ``checks.py`` asserts it: the male thread must never be
        driven below the female's first turn, because the bore under it is the
        channel and the channel is a whole tooth narrower.
        """
        return self.thread_z0 - self.closed_z

    @property
    def male_len(self) -> float:
        """Male thread length, from "the knob seats when the plunger is home"::

            body_h == closed_z + plunger_len + male_len + COLLAR_H
        """
        return self.body_h - COLLAR_H - self.plunger_len - self.closed_z

    @property
    def travel(self) -> float:
        return self.open_z - self.closed_z

    @property
    def open_engagement(self) -> float:
        """Thread still engaged with the plunger backed clear of the window.

        The screw must not be able to fall out of a clamp that is merely open,
        so this wants to stay above a full turn.
        """
        return self.thread_z1 - (self.open_z + self.plunger_len)

    # -- fits ---------------------------------------------------------------

    @property
    def plunger_slack(self) -> float:
        """Diametral slack of the plunger in the channel bore -- ``fits.SLIDING``
        by construction of ``PLUNGER_R``, restated here so a check can measure
        the built geometry against the class it claims rather than against the
        constant it was cut from."""
        return 2 * (FEMALE_CREST_R - PLUNGER_R)


DEFAULT = Clamp()
