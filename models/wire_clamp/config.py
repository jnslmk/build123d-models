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

THREAD_ENGAGE_RATIO = 0.75
"""Female thread length as a fraction of its diameter.

``fasteners-and-inserts``/``references/threads.md`` says 1.0 x D and prefers
1.5-2.0, and this is a deliberate departure from it, so here is the arithmetic
rather than a shrug. That rule is written for a thread carrying a *structural*
load, where printed threads share it across turns far worse than cut ones. This
one carries finger torque on a knurled knob:

* ``HAND_TORQUE`` 0.4 Nm, generous for finger and thumb on a 12 mm rim;
* into axial force through a high-friction printed thread,
  ``F = T / (K x d)`` with ``K`` 0.30 -- 167 N at the default size;
* shearing the female teeth off at their root, over ``pi x minor x root-flat``
  per turn, which at 0.75 x D is 2.4 turns and 24.5 mm2;
* 6.8 MPa, against roughly 20 MPa for ABS *across* layers, which is the plane
  that actually fails here.

Call it a factor of three. ``checks.py`` computes that number at every slider
position and fails under a factor of two, so this is a measured departure with a
gate on it rather than a rounded-down rule -- and 0.75 x D is still more than
twice the 0.32 x D the model this reconstructs uses at every size."""

HAND_TORQUE = 0.4
"""Nm, finger-tight on a knurled knob. Upper end of what a finger and thumb
manage on a rim this size."""

TORQUE_COEFF = 0.30
"""``F = T / (K x d)``. 0.30 rather than the ~0.16 quoted for lubricated steel:
a printed thread against a printed thread has a high friction coefficient, so
most of the torque is spent on friction rather than on axial force. Using the
steel figure here would over-state the load by nearly 2x -- in the safe
direction for the thread, but it is the wrong number."""

ABS_SHEAR = 20.0
"""MPa, ABS in shear *across* printed layers. The female thread's failure
surface is the cylinder at its minor diameter, which is a stack of layer
boundaries loaded along Z -- so the interlayer figure is the one that applies,
not the bulk one."""

SHEAR_SAFETY = 2.0
"""What ``checks.py`` demands of the margin above."""

THREAD_D_MIN = 8.0
"""Floor on the thread's major diameter, and the value it holds at for any wire
up to about 2.9 mm.

Not a printability floor -- a bigger thread prints more easily, not less -- but
a *strength* one: the screw's core is this less two tooth heights, and below
8 mm that core starts to twist before the clamp bites. It is also what keeps the
part sensibly proportioned when the wire is very thin, which is the case this
model was written for."""

NOTCH_SHOULDER = 1.2
"""Bore either side of a notch, and the reason the thread is not sized to the
strands alone.

The plunger can only cover the opening if there is opening either side of the
notch for it to cover, so the bore has to be wider than the notch by this much
at each side. Sized as three perimeters: enough to hold a strand down where it
turns into the notch, and enough that the notch's corners are not *nearly*
tangent to the bore.

That second one is not fastidiousness. Sized to the strands exactly -- which is
what ``thread_d`` did before this constant existed -- the notch came out 12.8 mm
wide in a 13.0 mm bore at 6 mm of cord, so the two outlines crossed at a glancing
angle and their union had four near-zero-width slivers in it. OCC does not raise
on that, it **segfaults**, and it did: every build above about 2.9 mm of wire
died with exit 139."""

THREAD_D_STEP = 0.5
"""The diameter is rounded up to a multiple of this. Nothing depends on a round
number, but a clamp whose thread is 10.5 mm is easier to talk about than one
whose thread is 10.2803 mm, and rounding *up* can only add clearance."""

MOUTH_LEAD_IN = 0.8
"""Depth of the cone that breaks the bore's mouth, so a screw starts square."""

MOUTH_COLLAR = MOUTH_LEAD_IN + THREAD_PITCH
"""Plain bore above the thread: the lead-in, **plus** a full pitch beneath it.

``build123d-geometry-ops``, gotchas 7, is specific -- one full pitch of plain
bore between the lead-in and the thread's first turn, because a cone cut into a
bd_warehouse thread makes OCC's fuse return the thread alone and silently drop
the rest of the part. Written as ``2.5`` this was 2.5 mm *total*, which left only
1.7 mm under the cone: two thirds of the rule, working but on the wrong side of
it, and the failure it guards against is silent. Written as a sum it cannot drift
again."""

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

BASE_T_MIN = 1.2
"""Floor on the floor: the solid disc under the channel, when the ribs standing
on it are small enough not to set it themselves. See ``Clamp.base_t``."""

RIB_BED = 0.8
"""Solid floor that must remain *under* the deepest point of a rib.

A rib is a cylinder centred on the floor's top face, so its lower half is buried
-- which is the point, because a half-round sitting *on* a flat floor would meet
it tangentially and print as a feather edge, where a buried one meets it at 90
degrees. The consequence is that the floor has to be thicker than the rib is
tall, and once the ribs scale with the cord, so must the floor. ``models.lib.fits.MIN_WALL``:
two perimeters at a 0.4 mm nozzle.

Left implicit, this is a real defect rather than a cosmetic one, and it shipped:
at 4 mm of cord the rib was exactly as tall as the 1.4 mm floor and tangent to
the underside of the part, and any larger cord pushed it *through* -- a part
whose bounding box started below the bed, with five half-cylinders sticking out
of its first layer. ``checks.py``'s print-pose assertion is what caught it."""

HEAD = 0.5
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

EDGE_CHAMFER_MIN = 0.8
EDGE_CHAMFER_RATIO = 0.08
"""Break on the body's top and bottom rims -- ``Clamp.edge_chamfer``.

One number for both ends, and bigger than the 0.5/0.6 it replaces. Two reasons.
Functionally the bottom one is elephant's-foot relief and wants to clear the
squish of the first layer, which is a fixed thing; visually 0.5 mm on a 12 mm
cylinder is 4% of the diameter and reads as a sharp edge next to the knob's
lobed, lofted chamfer sitting right above it. Scaled off the body with a floor,
so the two ends of a big clamp do not go back to looking square."""


# ---------------------------------------------------------------------------
# The screw.
# ---------------------------------------------------------------------------

COLLAR_H = 1.0
"""Plain shank between the last thread turn and the knob's underside."""

KNOB_H = 4.0
"""Fixed: a knob is turned with fingertips on its rim, so what a bigger clamp
needs is a bigger *diameter*, which it gets -- the knob is always flush with the
body. Height only has to be enough to get a finger and thumb on, and 4 mm of a
ten-lobed rim is plenty; it was 5, and that millimetre was the cheapest one in
the whole stack to give back."""

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

WIRE_MIN, WIRE_MAX = 0.5, 6.0
"""What one model covers: picture wire, beading wire and trimmer line at the
bottom; 2 mm guyline, 3 mm shock cord, 4 mm paracord and 6 mm tarp cord on the
way up. The thread steps up at about 2.9 mm, where two strands stop fitting
under an 8 mm thread's plunger.

**Why it stops at 6 and not higher.** Nothing breaks above it -- the geometry
stays valid to 12 mm and beyond -- so the limit is judgement, and it is this:
past about 6 mm the clamp stops being the right tool rather than stopping
working.

* *Size.* The wire passages cost a cord diameter at each end of the slot, so
  the body runs about ``4 x d + 4.4`` across against the original's ``3 x d``,
  and taller still. At 6 mm that is Ø29 x 36 mm and 23 g of filament -- a
  chunky but reasonable tarp toggle. At 12 mm it is Ø53 x 63 mm and about 150 g
  to hold a rope the original holds with Ø36 x 30 mm.
* *Diminishing returns.* The body-to-cord ratio has already flattened out by
  6 mm (4.8x, against 5.2x at 4 mm and 4.4x at 12 mm), so going bigger buys
  almost no proportional improvement -- only absolute bulk.
* *The mechanism stops being necessary.* Four bends through a slot are what a
  thin, stiff, slippery line needs, because a rim-nip yields the plastic before
  it holds the wire. Rope that thick is compressible and has surface area to
  spare, which is exactly the case the original's nip was designed for -- and
  its published files already cover 3 to 12 mm, five times smaller.

So: below 6 mm this model is the better tool, above it the original is. That is
a nicer place to draw the line than an arbitrary number, and it is where the two
designs actually cross over."""

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
        """How wide the bore has to be: the notch, plus a shoulder either side.

        The notch is what the strands need (``notch_w``); the shoulders are what
        the plunger needs in order to be covering anything. Together they are
        what sizes the thread.
        """
        return self.notch_w + 2 * NOTCH_SHOULDER

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
    def notch_w(self) -> float:
        """Width of the two notches the wire runs down, across the wire.

        **This is what stops a strand wandering off sideways.** The channel used
        to be a slot as wide as the plunger all the way along, which let the
        wire sit anywhere across it and let the plunger's round edge push it
        further out as it came down. Now the channel is a *bore* the plunger
        fills, and the only way past the plunger is a notch at each end that is
        no wider than the strands need. Everywhere else the plunger covers the
        opening completely, and where it does not, the notch walls do the job
        instead.

        ``fits.FREE`` at each side, because the strands are dropped in by hand.
        """
        return STRANDS * self.wire_d + 2 * fits.FREE

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
        return self.wire_d + 1.3

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

        Two things set it, and both are about the breaks rather than about the
        cord.

        *Wider than the bore*, so the window opens the channel rather than
        pinching it.

        *Wider than the notch, its break and the window's own rounded end.* The
        window is a stadium, so its ends curve back in; where the notch's widened
        wall runs into that curve it leaves a sharp vertical edge on the inside
        of the window, four of them, right where a strand turns into the notch.
        Keeping the notch inside the window's straight portion is what removes
        them, and it is why this is a ``max`` of two terms rather than one.
        """
        return max(
            self.channel_w + 0.2,
            self.notch_w + 2 * LIP_CHAMFER + self.window_h,
        )

    @property
    def base_t(self) -> float:
        """Solid floor under the channel: whichever is thicker, the floor's own
        minimum or what the ribs standing on it need beneath them."""
        return max(BASE_T_MIN, self.rib_h + RIB_BED)

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
    def bottom_chamfer(self) -> float:
        """Break on the body's bed-facing rim. See ``EDGE_CHAMFER_MIN``.

        The generous one, because nothing else is competing for that face: it is
        a solid disc.
        """
        return max(EDGE_CHAMFER_MIN, EDGE_CHAMFER_RATIO * self.body_r)

    @property
    def top_chamfer(self) -> float:
        """Break on the body's mouth-facing rim.

        The same, unless the top face cannot afford it. That face is an annulus
        only ``WALL`` wide, and the bore's lead-in cone is already eating at it
        from the inside -- run both at full size on a small clamp and they meet
        in the middle, leaving a knife-edge ring instead of two chamfers and a
        land between them. So this one yields, keeping 0.4 mm of flat.
        """
        land = self.body_r - self.female_root_r - MOUTH_LEAD_IN - 0.4
        return min(self.bottom_chamfer, max(0.3, land))

    @property
    def thread_shear(self) -> float:
        """MPa in the female thread's roots at ``HAND_TORQUE``.

        The number ``THREAD_ENGAGE_RATIO`` is justified by, computed rather than
        asserted so a check can fail on it. Conservative twice over: only the
        root flat is counted as carrying, and the interlayer shear figure is
        used rather than the bulk one.
        """
        force = HAND_TORQUE * 1000.0 / (TORQUE_COEFF * self.thread_d)
        turns = self.thread_engage / THREAD_PITCH
        area = 3.141592653589793 * (2 * self.female_crest_r) * THREAD_FLAT * turns
        return force / area

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
        return self.base_t + self.channel_h

    @property
    def window_z0(self) -> float:
        return self.base_t + self.lip

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
        return max(THREAD_ENGAGE_RATIO * self.thread_d, self.travel + THREAD_PITCH)

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
        return self.base_t + self.rib_h

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
