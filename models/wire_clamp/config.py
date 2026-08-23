"""Every number the wire clamp is cut from, and which of two rules set it.

This is a reconstruction of Printables 591325, *Adjustable Rope Clamp / Rope
Tensioner (Parametric)* by Twotone74 -- a cylinder with a window through it, a
ribbed floor under the window, and a thumbscrew that drives a plunger down onto
whatever is threaded through. The original is published for 3 to 12 mm rope as
ten files that are **one shape scaled ten ways**; measuring all ten against each
other is what this package is built on, and the measurements are in
``docs/reverse-engineering.md``.

**Uniform scaling is the bug.** Every feature of the original is a fixed
multiple of the rope diameter, the thread included::

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
warp on a 9 mm cylinder pulls it out of round by more than the whole tooth is
tall.

**So this model splits the thread in two, and only one half may move.**

*The nozzle owns the profile.* ``THREAD_PITCH``, ``THREAD_DEPTH``,
``THREAD_FLAT`` and ``THREAD_CLEAR`` are absolute millimetres and are **the same
at every position of the slider**. They come from the printable-thread table in
the ``fasteners-and-inserts`` skill (``references/threads.md``), which is the one
place in this repo that owns thread numbers: a 45 degree flank (a 45 degree
overhang, the house limit exactly), crest and root flats at or above one
extrusion width, at least six layers to a pitch, and 0.50 mm of diametral
clearance for a printed male in a printed female. These four are what a nozzle
has to resolve, and every one of them has a floor.

*The wire owns the diameter.* ``Clamp.thread_d`` is whatever the strands need to
lie side by side under the plunger, and never less than ``THREAD_D_MIN``. A
diameter has no resolution floor -- a bigger thread is strictly easier to print
than a smaller one -- so letting it grow costs nothing and is the only way one
slider can size the whole clamp. It never shrinks below the floor, so no slider
position can reproduce the original's defect.

That is the difference in one line: the original scales the numbers a printer
has to hit, and this scales the numbers a printer does not care about.

**Everything else follows the wire too.** Window, sill, slot, floor ribs, body
diameter, body height, plunger, knob lobes -- all of them are properties of
``Clamp`` below and all of them move with ``wire_d``. What stays put is the
short list a *printer* sets rather than the part: the thread profile above, wall
thicknesses, edge breaks, and the height of the ridges on the plunger's face.

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
from math import ceil

from ..lib import fits

MATERIAL = "abs"

# ---------------------------------------------------------------------------
# The thread profile. Absolute millimetres, set by the nozzle, identical at
# every position of the slider. Nothing here is allowed to depend on the wire --
# that dependency is the defect being fixed.
# ---------------------------------------------------------------------------

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

THREAD_ROOT_W = THREAD_FLAT + 2 * THREAD_DEPTH
"""Tooth width at the root. With ``THREAD_FLAT`` at the crest this is the whole
45 degree trapezoid, and it is the same trapezoid for both halves and at every
diameter."""

THREAD_D_MIN = 8.0
"""Floor on the thread's major diameter, and the value it holds at for any wire
up to about 2.9 mm.

Not a printability floor -- a bigger thread prints more easily, not less -- but
a *strength* one: the screw's core is this less two tooth heights, and below
8 mm that core starts to twist before the clamp bites. It is also what keeps the
part sensibly proportioned when the wire is very thin, which is the case this
model was written for."""

THREAD_D_STEP = 0.5
"""The diameter is rounded up to a multiple of this. Nothing depends on a round
number, but a clamp whose thread is 10.5 mm is easier to talk about than one
whose thread is 10.2803 mm, and rounding *up* can only add clearance."""

MOUTH_COLLAR = 2.5
"""Plain bore above the thread, one full pitch. Two rules land on the same
millimetre here: a thread must not start at a lead-in, and a lead-in cone cut
into a bd_warehouse thread makes OCC's fuse return the thread alone and drop the
rest of the part (``build123d-geometry-ops``, gotchas 7)."""

# ---------------------------------------------------------------------------
# Walls and edge breaks. Also absolute, and for the same kind of reason: a wall
# is a number of perimeters and a break is a fraction of a layer, so both are
# set by the machine rather than by what is being clamped.
# ---------------------------------------------------------------------------

WALL = 1.5
"""Over the thread's root, so it is the thinnest the shell ever gets where the
thread is: ~4 perimeters at 0.4 mm, which is what ``references/threads.md`` asks
for so that a thread is never printed into infill. The original runs 1.2 mm here
at 6 mm rope and 0.6 mm at 3 mm, i.e. 1.5 perimeters."""

WALL_Y = 1.0
"""Beside the wire passages, at the two ends of the channel. Thinner than
``WALL`` on purpose and allowed to be: it is a short band of shell at the bottom
of the channel and another at the top, and the screw's thrust runs down the two
pillars either side of the window, not through here."""

BASE_T = 1.4
"""Solid floor under the channel. Fixed, because what stands on it is the
plunger and the plunger's thrust is a hand on a knob at any wire size."""

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

BOTTOM_CHAMFER = 0.5
TOP_CHAMFER = 0.6
MOUTH_LEAD_IN = 0.8

# ---------------------------------------------------------------------------
# The screw.
# ---------------------------------------------------------------------------

COLLAR_H = 1.0
"""Plain shank between the last thread turn and the knob's underside."""

KNOB_H = 5.0
"""Fixed: a knob is turned with fingertips on its rim, so what a bigger clamp
needs is a bigger *diameter*, which it gets -- the knob is always flush with the
body. Height only has to be enough to get two fingers on."""

KNOB_LOBES = 10
KNOB_LOBE_DEPTH_RATIO = 0.15
"""Scallop depth as a fraction of the knob's radius, so the grip stays the same
*shape* as the clamp grows rather than turning into a fine knurl on a big
knob. At the 1 mm wire size this is 0.91 mm."""

KNOB_LOBE_R_RATIO = 0.20
"""Radius of each of the ten circles cut out of the rim, likewise as a fraction.
Big enough that the scallops are a grip and not a knurl -- a knurl needs a tool,
and a printed one under about 1 mm just prints as a rough cylinder."""

KNOB_TIP_R_RATIO = 0.13
"""Roll on the ten tips, where the rim circle meets each scallop. Without it
those are knife edges -- a cut circle crosses the rim at an angle, so the tooth
between two scallops comes to a point. Filleted in **2D**, on the profile,
before it is lofted: the house rule wants vertical edges rounded, and rounding
the sketch is the version of that which cannot fail.

Kept above ``KNOB_CHAMFER`` at every size, which ``checks.py`` asserts. The
chamfer is a 2D offset of this same profile, and an offset inward eats a convex
radius: a tip smaller than the offset comes back as a corner and puts the knife
edge on the bed layer."""

KNOB_CHAMFER = 0.5
"""Break on both horizontal edges of the knob, cut as a 2D offset lofted into
the profile rather than as an OCC chamfer: the knob's outline is ten concave
scallops meeting ten convex tips, which is exactly the kind of face
``build123d-geometry-ops`` says to stop asking OCC to chamfer."""

PLUNGER_CHAMFER = 0.5
"""Lead-in on the plunger's nose, so the screw starts square into the bore."""

RING_H = 0.3
"""Half-round ridges on the plunger's face, concentric so they bite at any
rotation. Fixed rather than scaled: this is a surface texture, and 0.3 mm of
relief digs into anything this clamp holds. Scaling it up on a big clamp would
only crowd the rings into each other."""

RING_COUNT = 3

RIB_H_MIN = 0.35
"""Floor on the floor ribs' height, which is also their half-round radius: they
are half cylinders, so one number does both. 1.75 extrusions wide at the base."""

# ---------------------------------------------------------------------------
# Wire. The one slider, and the thing every property below is written in terms
# of.
# ---------------------------------------------------------------------------

WIRE_MIN, WIRE_MAX = 0.5, 4.0
"""What one model covers: picture wire and trimmer line at the bottom, 4 mm
shock cord and paracord at the top. The thread steps up on the way, at about
2.9 mm, where two strands stop fitting under an 8 mm thread's plunger.

Above 4 mm the original's own files are the better answer and they start at
3.1 mm -- a rope that thick is compressible enough that its rim-nip works, and
this model's wire passages would make the body wider than it needs to be."""

WIRE_DEFAULT = 1.0
STRANDS = 2
"""What the clamp is *for*: a loop, both legs through the same window, the way
every photo of the original shows it used. It is also what sizes the thread --
see ``Clamp.strand_room``."""


@dataclass(frozen=True)
class Clamp:
    """One clamp's worth of numbers, all of them derived from the wire.

    The module constants above are the ones a *printer* sets. Everything here is
    set by what is being clamped, including -- unlike the original -- the
    thread's diameter, which is the one thread dimension that can move without
    asking the nozzle for something it cannot do.
    """

    wire_d: float = WIRE_DEFAULT

    @classmethod
    def of(cls, wire_d: float = WIRE_DEFAULT) -> Clamp:
        """Build one with the slider clamped back into a buildable range."""
        return cls(wire_d=min(max(float(wire_d), WIRE_MIN), WIRE_MAX))

    # -- the thread ---------------------------------------------------------

    @property
    def strand_room(self) -> float:
        """How wide the slot has to be for the strands to lie side by side.

        ``fits.FREE`` at each side: the strands are dropped in through a window
        by hand, so nothing here is a fit -- it wants room to spare.
        """
        return STRANDS * self.wire_d + 2 * fits.FREE

    @property
    def thread_d(self) -> float:
        """Thread major diameter: the one thread dimension the wire may move.

        The plunger has to pass *through* the female thread to be assembled, so
        the thread's minor diameter is the widest the plunger can ever be, and
        the plunger is what the strands lie under. Run that backwards and the
        thread's diameter is set by the wire: minor >= ``strand_room``, and
        major is minor plus a tooth at each side.

        Held at ``THREAD_D_MIN`` until the strands overtake it, which happens at
        about 2.9 mm of wire. Rounded up to ``THREAD_D_STEP``.

        Growing a diameter is safe in a way that shrinking a pitch is not: every
        number a nozzle has to resolve -- pitch, tooth, crest flat, clearance --
        is a module constant and is untouched by this.
        """
        needed = self.strand_room + 2 * THREAD_DEPTH
        return max(THREAD_D_MIN, ceil(needed / THREAD_D_STEP) * THREAD_D_STEP)

    @property
    def female_root_r(self) -> float:
        return self.thread_d / 2

    @property
    def female_crest_r(self) -> float:
        return self.female_root_r - THREAD_DEPTH

    @property
    def male_crest_r(self) -> float:
        """The male is shifted in by half the diametral clearance and the female
        is left on basic size, which is where ``references/threads.md`` says to
        put it for a V profile: "shrink the major diameter of the male"."""
        return self.female_root_r - THREAD_CLEAR / 2

    @property
    def male_root_r(self) -> float:
        return self.male_crest_r - THREAD_DEPTH

    @property
    def core_r(self) -> float:
        """The screw's shank under the thread: the thread's own root radius, so
        the shank and the thread are one cylinder with teeth on it rather than
        two."""
        return self.male_root_r

    @property
    def plunger_r(self) -> float:
        """The disc on the end of the shank, fatter than the shank itself.

        Sized off the channel bore -- which is the female crest, because the
        plunger has to pass through the thread to be assembled -- at
        ``fits.SLIDING``, the class for something that moves along its axis
        while staying located. It is not run through ``fits.for_material``:
        ABS's -0.15 mm would take a 0.22 mm clearance to 0.07 mm, which is a
        press fit for a printed bore, and the same shrink-cancels-between-two-
        ABS-parts argument the thread clearance makes applies here. The gap that
        matters is the one a strand could escape up, and 0.11 mm a side is well
        under any wire this clamp is for.
        """
        return self.female_crest_r - fits.SLIDING / 2

    @property
    def plunger_slack(self) -> float:
        """Diametral slack of the plunger in the channel bore -- ``fits.SLIDING``
        by construction of ``plunger_r``, restated here so a check can measure
        the built geometry against the class it claims rather than against the
        expression it was cut from."""
        return 2 * (self.female_crest_r - self.plunger_r)

    # -- the cord channel ---------------------------------------------------

    @property
    def wire_pass(self) -> float:
        """Width of the gap the wire drops through, at each end of the channel.

        **This is the one place this model departs from the original's shape,
        and it is the second fix.** In the original the plunger is a disc 0.3 mm
        smaller than a round bore, so nothing thicker than 0.3 mm can pass it: a
        rope is not clamped against the floor at all, it is nipped between the
        plunger's rim and the window sill and squashed. That works on 6 mm rope,
        which is compressible and has enough surface to hold by friction alone.
        A 1 mm wire is neither -- it is stiff, it is slippery, and a rim nip on a
        plastic part yields the plastic long before it holds the wire.

        So the channel here is a **slot**, not a bore: the plunger's width is the
        slot's width, and the slot is longer than the plunger in the wire's own
        axis by exactly this much at each end. The wire's two legs run down those
        gaps, so tightening pulls the wire *through* -- down over one sill, flat
        along the ribbed floor under the plunger, up over the other -- and clamps
        it against the floor with four bends in it. Four bends hold a wire; a nip
        does not.

        ``fits.FREE``, because nothing here is a fit: the wire has to fall
        through the gap without being threaded into it.
        """
        return self.wire_d + fits.FREE

    @property
    def channel_w(self) -> float:
        """Slot width, across the wire: the female thread's minor diameter.

        One number doing two jobs -- the plunger passes through the thread to be
        assembled, and is then guided by these two flats at ``fits.SLIDING``.
        Guided in the axis that matters: it is what stops a strand escaping
        sideways from under the plunger. ``thread_d`` is chosen so that this is
        always at least ``strand_room``.
        """
        return 2 * self.female_crest_r

    @property
    def channel_l(self) -> float:
        """Slot length, along the wire: the plunger plus a passage at each end."""
        return self.channel_w + 2 * self.wire_pass

    @property
    def body_r(self) -> float:
        """Whichever of the two things inside is bigger, plus its own wall.

        The thread at the thin end of the slider, the wire passages from about
        1 mm up. Both grow with the wire, so the body does too -- which is the
        honest answer rather than a defect: a thicker wire needs a wider slot,
        and a wider slot needs a wider shell.
        """
        return max(
            self.female_root_r + WALL,
            self.channel_l / 2 + LIP_CHAMFER + WALL_Y,
        )

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

        Half the wire, so its underside clears the sill, plus 0.7 mm of actual
        bend. Deliberately *not* a straight multiple: the bend that turns a
        sliding wire into a held one is a fixed thing, so a rope four times as
        thick does not need four times as much of it -- and paying for it in
        height four times over is how the body ends up twice as tall as it needs
        to be at the top of the slider.
        """
        return self.wire_d / 2 + 0.7

    @property
    def channel_h(self) -> float:
        return self.lip + self.window_h + HEAD

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
    def rib_h(self) -> float:
        """Height of the floor ribs, and their half-round radius.

        Scaled with the wire above 1 mm and floored below it: a rib has to dent
        what it grips, and 0.35 mm of relief that bites a 1 mm wire only polishes
        a 4 mm cord.
        """
        return max(RIB_H_MIN, 0.35 * self.wire_d)

    @property
    def rib_pitch(self) -> float:
        """Spacing of the floor ribs along the wire. Ribs finer than the thing
        they grip only polish it."""
        return max(1.0, 1.2 * self.wire_d)

    # -- the knob -----------------------------------------------------------

    @property
    def knob_lobe_depth(self) -> float:
        return KNOB_LOBE_DEPTH_RATIO * self.body_r

    @property
    def knob_lobe_r(self) -> float:
        return KNOB_LOBE_R_RATIO * self.body_r

    @property
    def knob_tip_r(self) -> float:
        return KNOB_TIP_R_RATIO * self.body_r

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
        ``female_root_r - channel_w / 2`` across the wire, in by
        ``channel_l / 2 - female_root_r`` along it. The second one is the one
        that grows."""
        return max(
            self.female_root_r - self.channel_w / 2,
            self.channel_l / 2 - self.female_root_r,
        )

    @property
    def thread_engage(self) -> float:
        """Female thread length.

        1.0 x D, the floor in ``references/threads.md`` -- printed threads share
        load across turns much worse than cut ones -- but never less than the
        plunger's travel plus a full pitch, so that a screw backed right out to
        where the wire runs free still has a whole turn holding it and cannot be
        dropped and lost.
        """
        return max(self.thread_d, self.travel + THREAD_PITCH)

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
        return BASE_T + self.rib_h

    @property
    def clamped_z(self) -> float:
        """Where the plunger stops on a wire of this size.

        One wire diameter above ``closed_z``. Nothing depends on this but the
        assembly view and the checks that read it; the part has no stop at this
        height and does not need one.
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


DEFAULT = Clamp()
