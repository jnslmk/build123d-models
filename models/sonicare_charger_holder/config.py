"""Every number the Sonicare charger holder is cut from, with its provenance.

**Read this before printing.** The repo's other models are cut from calipered
hardware. This one is not: nobody here has held the charger. Every puck number
below is *researched* -- taken from third-party 3D-print listings that claim to
fit the round Philips Sonicare charging puck (the HX6100-family base, not the
DiamondClean glass base) -- and the cable numbers are *assumed* outright. The
evidence ledger is the ``SOURCE`` string on each constant, and the rule the
``photo-reverse-engineering`` skill states applies here in full: a number that
was never measured must say so, because a silhouette cannot see a 2% scale
error and neither can a render.

That is also why the model is parametric. ``Holder.of()`` takes the four numbers
worth re-cutting -- puck diameter, puck height, wall, cable boot -- clamps them
into a range that still builds, and derives everything else. Measuring the real
charger is therefore a one-line change to ``PUCK_DIA``/``PUCK_HEIGHT`` here, or
two slider drags on the website, and not a re-model.

Material is the repo default, **PETG**. Nothing flexes or latches: the puck
drops in and gravity holds it, so the only fit in the design is the cavity's.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from math import sqrt

from ..lib import fits

MATERIAL = "petg"

# Slider stops. These describe *a round charging puck*, which is what this model
# is for -- they are not an arbitrary span. The first version allowed a 20 mm
# puck behind a 6 mm wall, which is fifteen perimeters around something no
# Sonicare has ever shipped, and the only thing that range bought was a set of
# degenerate shapes for the parameter sweep to trip over. Wide enough to cover
# every round variant plus generous room for a mis-measurement, and no wider.
PUCK_DIA_MIN, PUCK_DIA_MAX = 35.0, 70.0
PUCK_H_MIN, PUCK_H_MAX = 10.0, 35.0
WALL_MIN, WALL_MAX = 1.6, 3.0
BOOT_MIN, BOOT_MAX = 3.0, 10.0

# --------------------------------------------------------------------------
# The charger. Researched, not measured -- see the module docstring.
# --------------------------------------------------------------------------

PUCK_DIA = 47.4
"""Outside diameter of the round charging puck.

RESEARCHED, not measured. 47.4 mm is quoted by two independent maker listings
for the same holder design (cults3d "Philips Sonicare Charger Holder | Cable
Winder" and the Printables "Philips Sonicare Round Charger Holder"), which is
corroboration between makers rather than a Philips figure -- Philips publishes
no dimensional drawing for the base. Treat it as +/- 1 mm until calipered.
"""

PUCK_HEIGHT = 19.0
"""Height of the puck body, **excluding** the central charging post.

RESEARCHED, from the same two listings ("base height 19 mm without pin"). The
post is not modelled and needs no clearance: it stands up inside the cavity's
open mouth, which is why the cavity is a plain bore.
"""

# --------------------------------------------------------------------------
# The cable. Assumed -- these are the numbers most likely to need changing.
# --------------------------------------------------------------------------

CABLE_DIA = 3.0
"""Diameter of the cord itself, away from the puck.

ASSUMED. No source quotes it; 3.0 mm is a typical low-voltage DC cord. Only the
rear groove depends on it, and the groove is oversize, so an error here costs
nothing until the cord is thicker than ~4 mm.
"""

CABLE_BOOT_DIA = 6.0
"""Diameter of the moulded strain relief where the cord leaves the puck.

ASSUMED, and **the single number most likely to be wrong.** It is what the wall
slot is sized on, because the boot -- not the bare cord -- is the widest thing
that has to pass through or nest in that opening. Sized generously for exactly
that reason. If the holder is printed and the puck will not sit down flat, this
is the constant to raise.
"""

# --------------------------------------------------------------------------
# Fits and functional gaps.
# --------------------------------------------------------------------------

PUCK_FIT = fits.SLIDING  # sliding fit, PETG baseline
"""The one real fit in the model.

Stated as a requirement first, per the ``fdm-fits-and-clearances`` procedure:
*the charger must drop into the cup by hand and lift back out, and must not
rattle once it is on the wall.* That is a sliding fit, not a free one -- FREE
would leave 0.4 mm of play against a tile, which is audible every time the
brush is set down. Diametral, and added on top of nominal because an FDM bore
already prints a couple of tenths under (that skill's Rule 4).
"""

CABLE_CLEAR = 1.0
"""Not a fit: routing gap, so the cord and its boot drop into the slot by hand
rather than being threaded. Cable routing is a functional gap and deliberately
does not borrow a fit constant.
"""

CABLE_RECESS = 0.6
"""Not a fit: how far below the tape plane the cord sits once it is in the rear
groove. The groove has to swallow the cord *completely* -- a cord standing even
0.2 mm proud would hold the tape pad off the tile along its whole length and
turn a shear joint into a peel joint.
"""

# --------------------------------------------------------------------------
# Structure.
# --------------------------------------------------------------------------

WALL = 2.4
"""Six perimeters at a 0.4 mm nozzle. Nothing here is structural in the sense of
carrying load in bending -- the tape pad does that -- so this is set by what
prints solidly rather than by a stress.
"""

FLOOR_MIN = 2.0
"""Not a fit: the thinnest the floor is allowed to be, ten layers at 0.2 mm.

A floor is usually chosen and done with. This one is derived instead -- see
``Holder.floor`` -- because the side channels have to pass *underneath* the cup,
and that turns the floor into the thing that has to be tall enough to contain
them.
"""

SEAT_BACKING = 1.2
"""Not a fit: seat that must survive above the side channels.

Three perimeters between the top of a channel and the face the charger rests on.
The channels run under the seat for the width of the cup's back, so without this
the puck would be sitting on a membrane over a void.
"""

ARM_CLEAR = 0.4
"""Not a fit: routing gap on the side arms, tighter than the channel's.

The channel has to swallow a moulded boot by hand and wants room; the arms take
only the bare cord, pressed in. Every tenth here is a tenth on the arm's height,
and the arm's height sets the floor's thickness -- which is the whole height of
the holder. So this is the one routing gap worth being mean with.
"""

# --- the brush-head pegs -------------------------------------------------
#
# All three are ASSUMED, like the cable numbers, and for the same reason: nobody
# here has held one. They are the numbers to change first if the heads do not
# sit properly.

HEAD_SOCKET_D = 5.0
"""ASSUMED. Bore up the middle of a brush head, which grips the handle's drive
shaft. The peg stands in for that shaft."""

HEAD_D = 13.0
"""RESEARCHED, no longer assumed. Envelope of a brush head at its widest.

Philips' own C3 comparison material quotes a **12.5 mm neck diameter** for the
standard head, which is the widest part of the moulding; half a millimetre is
added for the bristle field, which flares a little past it. The 14 mm this
started as was a guess, and a guess in the wrong direction -- it made the part
wider than it needed to be while still not solving the problem below.
"""

HEAD_WALL_CLEAR = 2.0
"""Not a fit: air between a head sitting on its peg and the tile.

This is the number whose absence made the pegs unusable. A head is held near its
middle, so it needs ``HEAD_D / 2`` of room *behind* the peg's axis, and the lobe
sat only its own radius (4.7 mm) off the tape plane -- so a 13 mm head fouled
the wall by 1.8 mm and simply could not be pushed on. The lobes now stand
``HEAD_D / 2 + HEAD_WALL_CLEAR`` forward instead, which is what sets the back
plate's depth.
"""

HEAD_CLEAR = 2.0
"""Not a fit: air between a stored head and the cup beside it."""

PEG_H = 10.0
"""How far the peg stands proud. Enough to hold a head upright without being
long enough to reach the bristles."""

PEG_BOSS_WALL = 2.4
"""Not a fit: material around the peg's root, which is what sets the pad it
stands on. Six perimeters -- the pad is the only thing carrying a head."""

PEG_FIT = fits.FREE  # free fit, PETG baseline
"""The peg is a *shaft*, so the fit comes off its diameter rather than a bore.

FREE and not SLIDING, deliberately. This is a wet drop-on storage peg that gets
used one-handed with the other hand full: it must never grip, and a head that
needs a tug is worse than one that rattles. The same reasoning that made the
charger's own bore SLIDING makes this one FREE.
"""

LEDGE = 3.0
"""Not a fit: radial width of the seat the charger rests on.

The floor is a ring, not a disc. A closed floor meant that once the holder was
taped to the tile there was no way to get the charger back out -- nothing to
push against, and no room to get a finger past it. Opening the middle turns
removal into pushing a finger up through the hole, and drains the cup as a side
effect, which a closed floor in a shower room never did.

3 mm leaves a narrow seat, and narrow is fine: the ring carries the charger's
own weight and nothing else. The trade it buys is the bigger hole, which is
what a finger actually needs.
"""

RIM_KEEPOUT = 1.0
"""Not a fit: the minimum height of plain, untreated wall between the cable
notch's crown and whichever rim treatment reaches furthest down.

Back, and deleted once in between. It was removed when the channel ran open to
the rim, because a channel with no crown cannot crowd anything. Closing the
channel back to a notch restores the crown and with it the failure: measured by
sweeping the boot diameter, OCC takes the notch's chamfers at 0.6 mm of
surviving wall and silently refuses two of them at 0.3 mm. This is that
threshold with a comfortable multiple on top. Bounding against the *rim*
instead does not work -- the lead-in cone starts lower than the outer chamfer.
"""

JUNCTION_STEP = 1.0
"""Not a fit: how much wider the channel is kept than the arms that meet it.

The channel carries the boot and the arms carry only the cord, so the channel is
normally the wider of the two by some margin anyway. Wind the boot slider down
to the cord's own diameter and the two come out identical, their side walls
become coplanar, and the junction degenerates into a sliver that OCC will not
treat. This keeps a step there whatever the sliders say.
"""

PLATE_BACKING = 1.6
"""Not a fit: material that must survive behind the side channels.

Four perimeters. The channels are cut into the tape face at the bar's ends,
where the bar stands clear of the cup and is the only thing there, so their
depth eats directly into a cantilever. This is what stops ``plate_t`` being
chosen independently of them.
"""

CHANNEL_OVERCUT = 0.5
"""Not a fit: how far past the bore wall the cable channel's cut reaches, so no
sliver of wall survives at its mouth. It also sets the floor of
``channel_depth`` -- see there.
"""

CHAMFER = 0.8
"""House style: chamfer horizontal edges. Also elephant's-foot relief on the
bed-side edge, which matters more than usual here -- a splayed first layer would
hold the tape pad off the tile.
"""

MOUTH_CHAMFER = 1.0
"""Lead-in on the cavity mouth, so the puck funnels in instead of catching on
the rim. Sized under WALL/2 so it cannot knife-edge the rim.
"""

CABLE_MOUTH_CHAMFER = 0.6
"""Break on all three mouths of the cable route, and the one edge treatment
here that is not house style for its own sake.

Each mouth has a job. Inside the cup, the cord bends through 90 degrees over
the slot's inner lip on its way to the tile -- a raw 90 degree edge there works
insulation against a corner every time the charger is lifted out. On the tape
plane it is the lip the foam tape has to lie down over. On the bed face it is
elephant's foot at the one opening, and a splayed first layer there is what
rocks the pad off the tile. Kept well under the cord's own radius so the
chamfers cannot meet and narrow the route.
"""


@dataclass(frozen=True)
class Holder:
    """The four numbers worth re-cutting, plus every dimension derived from them.

    Frozen and derived-by-property for the reason ``fdm-fits-and-clearances``
    Rule 7 gives: a constant that equals another dimension is a collision
    waiting to happen unless the relationship is written down. So ``plate_w``
    is an expression on ``outer_dia``, ``body_h`` is an expression on
    ``puck_height``, and there is no way to move the puck and leave a radius
    behind.
    """

    puck_dia: float = PUCK_DIA
    puck_height: float = PUCK_HEIGHT
    wall: float = WALL
    cable_boot_dia: float = CABLE_BOOT_DIA

    # -- the cup ----------------------------------------------------------
    @property
    def cavity_dia(self) -> float:
        """Bore cut for the puck: nominal plus the sliding fit."""
        return self.puck_dia + PUCK_FIT

    @property
    def cavity_r(self) -> float:
        return self.cavity_dia / 2

    @property
    def outer_dia(self) -> float:
        return self.cavity_dia + 2 * self.wall

    @property
    def outer_r(self) -> float:
        return self.outer_dia / 2

    @property
    def floor(self) -> float:
        """Floor thickness, derived from the side channels rather than chosen.

        The obvious floor is ``FLOOR_MIN`` and it does not work here. The side
        channels are cut into the tape face and have to get from the middle of
        the back out to the ends, and at the middle the cup's own wall stands
        within a couple of millimetres of that face -- so a channel deep enough
        to bury the cord would cut straight through the back wall and take a
        15 mm bite out of the seat the charger rests on, leaving it to rock.
        Running the channels *below* the cavity floor avoids that entirely, and
        the price is that the floor has to be tall enough to hold them.

        So the cup is deeper below its seat than it looks, and the rim still
        lands level with the top of the charger.
        """
        return max(FLOOR_MIN, self.side_w + SEAT_BACKING)

    @property
    def body_h(self) -> float:
        """Floor plus puck height: the rim lands level with the top of the puck.

        This is the "puck height only" front wall -- the shallowest cup that
        still hides the charger completely.
        """
        return self.floor + self.puck_height

    # -- the tape pad -----------------------------------------------------
    # -- the brush-head pegs ----------------------------------------------
    @property
    def peg_d(self) -> float:
        """Peg diameter: the head's own bore, less a free fit."""
        return HEAD_SOCKET_D - PEG_FIT

    @property
    def pad_r(self) -> float:
        """Radius of the lobe each peg stands on."""
        return self.peg_d / 2 + PEG_BOSS_WALL

    @property
    def pad_y(self) -> float:
        """How far forward of the tile a peg's axis stands.

        Set by the head that has to hang on it, not by the lobe's own size. The
        lobes used to sit tangent to the tape plane, which read as tidy -- it
        made them add pad area rather than break it -- and was unusable: it left
        a head fouling the wall by nearly 2 mm. See ``HEAD_WALL_CLEAR``.
        """
        return self.back_y - (HEAD_D / 2 + HEAD_WALL_CLEAR)

    @property
    def peg_x(self) -> float:
        """How far out each peg has to be for its head to clear the cup.

        Solved rather than chosen, and solved on the diagonal: the lobe sits a
        radius forward of the tape plane, so the distance that actually has to
        clear the cup is ``hypot(peg_x, pad_y)`` and not ``peg_x`` alone.
        Measuring it along x instead would push the pegs 7 mm further out than
        they need to be, on a part whose whole width is a wall fixture.
        """
        reach = self.outer_r + HEAD_D / 2 + HEAD_CLEAR
        return sqrt(max(reach**2 - self.pad_y**2, 1.0))

    @property
    def plate_w(self) -> float:
        """Back plate width, end to end, rounded ends included."""
        return 2 * (self.peg_x + self.pad_r)

    @property
    def arm_half(self) -> float:
        """How far out each side arm runs before it stops.

        Short of the plate's rounded ends, deliberately. An arm that ran out
        through the rounding exited *around a curve* -- a lip exactly where the
        cord bends as it leaves, and an edge OCC refused to treat under every
        grouping, ordering and size tried. The arms are open along their whole
        length at the bed face, so a cord tucked into one still leaves wherever
        it likes; it just leaves downwards instead of sideways.
        """
        return max(self.channel_w, self.peg_x - self.pad_r - 1.0)

    @property
    def plate_t(self) -> float:
        """Depth of the back plate, from the tape plane to its front face.

        Not chosen at all any more: it is exactly what it takes to reach a peg
        standing far enough forward for a head to clear the wall, plus the lobe
        that peg needs around it. The plate and the lobes used to be separate
        shapes -- a thin bar with a round lobe hung off each end -- and pushing
        the lobes forward would have left them dangling off it on a couple of
        millimetres of overlap, with an open wedge between each one and the cup.
        Making the plate deep enough to *contain* them closes both gaps at once
        and turns three shapes into one rounded slab.
        """
        return (self.back_y - self.pad_y) + self.pad_r

    @property
    def plate_corner_r(self) -> float:
        """Vertical fillet on the bar's four corners, taken in the sketch rather
        than as an OCC edge op.

        Bounded three ways, and the third was missed the first time. By half the
        bar's depth, so the rounding cannot consume the bar. Then by *both*
        corners the side channels have to exit between: the bar's end face is
        flat only over ``[front + r, back - r]``, and the channel's back face
        has to land inside that band with room to spare, or it exits around a
        curve and puts a lip where the cord bends.

        Guarding only the front corner passed at the default wall and failed at
        4 mm, where the rounding grew until the channel's back face sat exactly
        on the rear corner's tangent -- the classic zero-width sliver, which OCC
        answers by silently refusing to treat the edge at all. Found by sweeping
        the wall slider, not by looking at the default.
        """
        # The plate's ends ARE the peg lobes, so the rounding is the lobe's own
        # radius. The bounds that used to apply here were all about the side
        # arms exiting through this corner; the arms now stop short of it (see
        # ``arm_half``), which is what makes a lobe-sized rounding affordable.
        return self.pad_r

    @property
    def back_y(self) -> float:
        """The tape plane: the bar's rear face, tangent to the cup's outside."""
        return self.outer_r

    @property
    def plate_y(self) -> float:
        """Centre of the bar in Y, i.e. where its sketch rectangle is placed."""
        return self.back_y - self.plate_t / 2

    # -- the cable route --------------------------------------------------
    #
    # One channel, open from the bed to the rim. It began as two features -- a
    # closed slot through the wall, and a groove down the tape face -- and that
    # was a design error rather than a tidier decomposition: a closed slot can
    # only be *threaded*, and the end of this cord that is free to thread is
    # the one with the mains plug moulded onto it. Nobody was ever getting the
    # cable in. Open to the rim, the cord is laid in from above and the puck
    # follows it down, boot and all.
    @property
    def channel_w(self) -> float:
        """Width of the channel, at every height.

        Sized on the **boot**, not the cord: the strain relief is the widest
        thing that has to pass, and it has to pass along the *whole* height,
        because it descends with the puck rather than being fed in at the
        bottom. That is why the channel does not taper to the cord's width
        further up, which would otherwise save rim material and look tidier --
        it would also stop the puck going in.
        """
        return max(self.cable_boot_dia, CABLE_DIA + JUNCTION_STEP) + CABLE_CLEAR

    @property
    def opening_r(self) -> float:
        """Radius of the hole through the floor -- the bore less the seat."""
        return self.cavity_r - LEDGE

    @property
    def channel_top(self) -> float:
        """Crown of the notch. Round-topped, so it prints without support."""
        return self.floor + self.channel_w

    @property
    def channel_shoulder(self) -> float:
        """Where the notch's straight sides give way to its radiused crown."""
        return self.floor + self.channel_w / 2

    @property
    def side_w(self) -> float:
        """Width of the left and right arms across the tape face.

        Sized on the bare cord, not the boot: the boot never travels sideways,
        it sits in the notch. So the arms are narrower than the notch, which is
        the point -- every millimetre of arm height is taken straight off the
        tape pad.
        """
        return CABLE_DIA + ARM_CLEAR

    @property
    def side_depth(self) -> float:
        """Depth of the arms: bury the cord, and clear the bore.

        Burying the cord is the obvious half -- it has to end up below the tape
        plane going sideways for the same reason it does going down. The second
        half is a rule this model has now learned twice: a face cut in from the
        tape plane must never *land on* the bore, only stop short of it or pass
        it. At a 3.6 mm wall the arm's back face came out exactly tangent to the
        bore's cylinder, and a zero-width sliver is what OCC answers by refusing
        to chamfer the whole bed-side perimeter -- silently, taking nine edges
        with it. Passing the bore costs nothing here, because the arms run below
        the seat, where "past the bore" is just more floor ring.
        """
        return max(CABLE_DIA + CABLE_RECESS, self.wall + CHANNEL_OVERCUT)

    @property
    def rim_clear(self) -> float:
        """The highest anything may reach and still leave the rim alone.

        The rim carries two treatments and the one reaching lowest is the
        lead-in cone on the inside, not the chamfer on the outside, so the bound
        is taken against whichever is deeper -- and meeting it exactly is not
        enough, which is what ``RIM_KEEPOUT`` reserves.
        """
        return self.body_h - max(self.rim_chamfer, self.mouth_chamfer) - RIM_KEEPOUT

    @property
    def channel_depth(self) -> float:
        """How far in from the tape plane the channel is cut.

        Two requirements, and the larger wins. The cord's: bury it below the
        tape plane with room to spare, since a cord standing proud holds the
        pad off the tile. The wall's: reach at least a hair past the bore, so
        that below the floor line -- where the channel is a blind notch rather
        than an opening -- it still breaks through into the cup instead of
        stopping inside the wall and leaving a shelf. At the default 2.4 mm
        wall the cord's number is the larger one and hides the second
        requirement completely; wind the wall slider to 6 mm and it is the only
        thing keeping the notch honest, which is how the parameter sweep in
        ``checks.py`` found it in the first place.
        """
        return max(
            CABLE_DIA + CABLE_RECESS,
            self.wall + CHANNEL_OVERCUT,
            # Reach the floor opening. Below the floor line the channel has to
            # break into that hole rather than stop in the seat, because that
            # junction is the whole reason the cord can be fitted at all: it is
            # what lets the cord be dropped in from inside instead of threaded
            # through a closed hole. Measured at the channel's *edge*, not its
            # centre -- the opening is a circle, so its nearest point across a
            # 7 mm channel is half a millimetre further out than on the axis.
            self.back_y - sqrt(max(self.opening_r**2 - (self.channel_w / 2) ** 2, 0.0)),
        )

    # -- edge treatments that have to scale with the wall ------------------
    @property
    def rim_chamfer(self) -> float:
        """House chamfer, held clear of half the wall so it cannot knife-edge
        a rim that a thin-wall slider has made narrow.
        """
        return min(CHAMFER, self.wall / 2 - 0.1)

    @property
    def mouth_chamfer(self) -> float:
        """The bore's lead-in, under the same ceiling and for the same reason."""
        return min(MOUTH_CHAMFER, self.wall / 2 - 0.1)

    @property
    def route_chamfer(self) -> float:
        """Break on the cable route's mouths, bounded by both things it could
        eat: a third of the wall it passes through, and a quarter of the slot
        it would otherwise narrow.
        """
        return min(CABLE_MOUTH_CHAMFER, self.wall / 3, self.channel_w / 4)

    def validate(self) -> None:
        """Fail loudly on a combination that would build a wrong part.

        These are not clamps -- ``of()`` has already clamped -- they are the
        invariants the geometry assumes and the checks re-assert. Each one is
        an invariant that was *violated* at some point by a slider combination,
        not a hypothetical.
        """
        if self.channel_depth < self.wall + CHANNEL_OVERCUT:
            raise ValueError("cable channel would stop inside the wall")
        if self.channel_depth - self.wall >= self.cavity_r / 2:
            raise ValueError("cable channel would eat half the floor")
        if self.plate_corner_r >= self.plate_t / 2:
            raise ValueError("plate corner radius would consume the bar")
        if self.channel_w > self.cavity_r:
            raise ValueError("cable channel would stop the cup being a cup")
        if self.channel_top > self.rim_clear:
            raise ValueError("cable notch would break into the rim treatments")
        if self.opening_r <= self.channel_w / 2:
            raise ValueError("floor seat would consume the whole floor")
        if self.side_depth + PLATE_BACKING > self.plate_t:
            raise ValueError("side channels would cut through the bar")
        if self.mouth_chamfer <= 0 or self.rim_chamfer <= 0:
            raise ValueError("wall is too thin to carry its own edge treatment")

    @classmethod
    def of(cls, **params) -> "Holder":
        """Build a holder from website slider values, clamped so it always builds.

        Unknown keys are ignored rather than raising, because the website hands
        back whatever schema it was rendered with.
        """
        known = {f.name for f in fields(cls)}
        vals = {k: float(v) for k, v in params.items() if k in known and v is not None}
        h = cls(**vals)
        h = cls(
            puck_dia=min(max(h.puck_dia, PUCK_DIA_MIN), PUCK_DIA_MAX),
            puck_height=min(max(h.puck_height, PUCK_H_MIN), PUCK_H_MAX),
            wall=min(max(h.wall, WALL_MIN), WALL_MAX),
            cable_boot_dia=min(max(h.cable_boot_dia, BOOT_MIN), BOOT_MAX),
        )
        # The channel is sized on the boot, and runs the full height, so the
        # only thing left to bound it against is the cup's own radius -- a
        # channel wider than that is a gap with a bit of cup attached. Height
        # used to constrain it too, back when the slot had a crown that could
        # crowd the rim; open to the rim, there is no crown to crowd anything.
        # Two ceilings on the boot, and the lower wins: the notch must not be so
        # wide the cup stops being a cup, and its crown must clear the rim's
        # treatments. The second one is why RIM_KEEPOUT is back -- see there.
        boot_max = min(
            h.cavity_r - CABLE_CLEAR,
            h.rim_clear - h.floor - CABLE_CLEAR,
        )
        if h.cable_boot_dia > boot_max:
            h = cls(
                puck_dia=h.puck_dia,
                puck_height=h.puck_height,
                wall=h.wall,
                cable_boot_dia=max(2.0, boot_max),
            )
        h.validate()
        return h


DEFAULT = Holder()
"""The holder this repo builds, exports and checks."""

HOLDER_PARAMS = [
    {
        "name": "puck_dia",
        "label": "Charger diameter (mm)",
        "type": "number",
        "min": PUCK_DIA_MIN,
        "max": PUCK_DIA_MAX,
        "step": 0.2,
        "default": PUCK_DIA,
    },
    {
        "name": "puck_height",
        "label": "Charger height, no post (mm)",
        "type": "number",
        "min": PUCK_H_MIN,
        "max": PUCK_H_MAX,
        "step": 0.5,
        "default": PUCK_HEIGHT,
    },
    {
        "name": "wall",
        "label": "Wall thickness (mm)",
        "type": "number",
        "min": WALL_MIN,
        "max": WALL_MAX,
        "step": 0.2,
        "default": WALL,
    },
    {
        "name": "cable_boot_dia",
        "label": "Cable strain relief (mm)",
        "type": "number",
        "min": BOOT_MIN,
        "max": BOOT_MAX,
        "step": 0.5,
        "default": CABLE_BOOT_DIA,
    },
]
