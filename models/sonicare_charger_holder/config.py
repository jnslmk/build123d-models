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

from ..lib import fits

MATERIAL = "petg"

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

FLOOR = 2.0
"""Ten layers at 0.2 mm. The floor is the first layer and the bed-side face, and
it is closed: the only opening in this model is the cable route.
"""

PLATE_INSET = 3.0
"""Not a fit: how far each end of the tape bar stops short of the cup's own
silhouette, so that from the front the holder reads as a plain round cup and the
bar is not visible past it.
"""

SLOT_OVERCUT = 0.5
"""Not a fit: how far inside the bore the wall slot's cut begins, so no sliver
of wall survives at the mouth of the cable route. It also sets the floor of
``groove_depth`` -- see there.
"""

RIM_KEEPOUT = 1.0
"""Not a fit: the minimum height of plain, untreated wall that must survive
between the cable slot's crown and whichever rim treatment reaches furthest
down.

Measured, not guessed. Winding the puck height to its 6 mm stop drives the slot
up until only a sliver of wall separates its crown from the lead-in cone, and
OCC then refuses to chamfer the slot's mouths -- silently, and two of them at
once. Sweeping the boot diameter puts the cliff between 0.3 mm (refused) and
0.6 mm (taken), so this is that threshold with a comfortable multiple on top.
Bounding against the *rim* instead was the first attempt and it does not work:
the lead-in cone starts lower than the outer chamfer does.
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
    def body_h(self) -> float:
        """Floor plus puck height: the rim lands level with the top of the puck.

        This is the "puck height only" front wall -- the shallowest cup that
        still hides the charger completely.
        """
        return FLOOR + self.puck_height

    # -- the tape pad -----------------------------------------------------
    @property
    def plate_w(self) -> float:
        """Bar width, derived from the cup so it always hides behind it."""
        return self.outer_dia - 2 * PLATE_INSET

    @property
    def plate_t(self) -> float:
        """Bar depth. Two walls: thick enough that the cantilevered ends resist
        peeling in their own plane, thin enough not to push the cup off the tile.
        """
        return 2 * self.wall

    @property
    def plate_corner_r(self) -> float:
        """Vertical fillet on the bar's four corners, taken in the sketch rather
        than as an OCC edge op. Held under half the bar depth so the rounding
        cannot consume the bar.
        """
        return self.plate_t / 2 - 0.4

    @property
    def back_y(self) -> float:
        """The tape plane: the bar's rear face, tangent to the cup's outside."""
        return self.outer_r

    @property
    def plate_y(self) -> float:
        """Centre of the bar in Y, i.e. where its sketch rectangle is placed."""
        return self.back_y - self.plate_t / 2

    # -- the cable route --------------------------------------------------
    @property
    def slot_w(self) -> float:
        """Width of the opening through the back wall.

        Sized on the **boot**, not the cord: the strain relief is the widest
        thing that has to get through, and it is the part that decides whether
        the puck can sit flat on the floor.
        """
        return self.cable_boot_dia + CABLE_CLEAR

    @property
    def slot_top(self) -> float:
        """Top of the round-topped slot, measured from z = 0."""
        return FLOOR + self.slot_w

    @property
    def slot_shoulder(self) -> float:
        """Where the slot's straight sides give way to its radiused top."""
        return FLOOR + self.slot_w / 2

    @property
    def groove_w(self) -> float:
        """Width of the channel down the tape face: the **slot's** width, not
        the cord's.

        Sizing it to the cord (4 mm against the slot's 7) read as the tidier
        choice and was wrong. The slot's own floor then survived as a
        7 x 3.6 mm horizontal ledge inside the cup with the groove punched
        through it -- three sharp convex edges in the one place the cord bends
        and rubs, and a shelf for water to sit on directly under the charger.
        Matching the two widths deletes that face rather than decorating it,
        and the whole cable route becomes a single continuous opening. Found by
        point-sampling the solid, not by looking at it: the ledge is invisible
        in every projection, because the cup's wall stands in front of it.
        """
        return self.slot_w

    @property
    def groove_depth(self) -> float:
        """Depth of that channel: whichever is greater of what the cord needs
        and what the slot needs.

        The cord's requirement is the obvious half -- bury it below the tape
        plane with room to spare. The second half is the same ledge bug that
        ``groove_w`` describes, reappearing in the other axis: the slot's floor
        is a horizontal face spanning the full wall, so a groove shallower than
        the wall leaves the outer part of that floor standing as a shelf inside
        the cup. At the default 2.4 mm wall the cord's number is the larger one
        and hides the problem completely; wind the wall slider to 6 mm and the
        shelf reappears, which is exactly how the parameter sweep in
        ``checks.py`` found it. Taking the max means the groove always clears
        the slot's floor, at every wall thickness.
        """
        return max(CABLE_DIA + CABLE_RECESS, self.wall + SLOT_OVERCUT)

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
        return min(CABLE_MOUTH_CHAMFER, self.wall / 3, self.slot_w / 4)

    def validate(self) -> None:
        """Fail loudly on a combination that would build a wrong part.

        These are not clamps -- ``of()`` has already clamped -- they are the
        invariants the geometry assumes and the checks re-assert. Each one is
        an invariant that was *violated* at some point by a slider combination,
        not a hypothetical.
        """
        if self.groove_depth < self.wall + SLOT_OVERCUT:
            raise ValueError("cable groove would leave the slot's floor as a ledge")
        if self.groove_depth - self.wall >= self.cavity_r / 2:
            raise ValueError("cable groove would eat half the floor")
        if self.plate_corner_r >= self.plate_t / 2:
            raise ValueError("plate corner radius would consume the bar")
        if self.slot_top > self.rim_clear:
            raise ValueError("cable slot would break into the rim chamfer")
        if self.mouth_chamfer <= 0 or self.rim_chamfer <= 0:
            raise ValueError("wall is too thin to carry its own edge treatment")

    @property
    def rim_clear(self) -> float:
        """The highest anything may reach and still leave the rim alone.

        ``slot_top < body_h`` was the obvious bound and it was wrong twice
        over. The rim carries two treatments, and the one that reaches lowest
        is the lead-in cone on the *inside*, not the chamfer on the outside --
        so the bound is taken against whichever is deeper. And meeting it
        exactly is not enough: what OCC objects to is the sliver of wall left
        between, which is what ``RIM_KEEPOUT`` reserves.
        """
        return self.body_h - max(self.rim_chamfer, self.mouth_chamfer) - RIM_KEEPOUT

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
            puck_dia=min(max(h.puck_dia, 20.0), 120.0),
            puck_height=min(max(h.puck_height, 6.0), 60.0),
            wall=min(max(h.wall, 1.2), 6.0),
            cable_boot_dia=min(max(h.cable_boot_dia, 2.0), 12.0),
        )
        # The slot is sized on the boot, and must still clear the rim chamfer.
        # ``rim_clear``, not ``body_h``: see that property for what went wrong
        # when this bounded against the rim itself.
        if h.slot_top > h.rim_clear:
            h = cls(
                puck_dia=h.puck_dia,
                puck_height=h.puck_height,
                wall=h.wall,
                cable_boot_dia=max(2.0, h.rim_clear - FLOOR - CABLE_CLEAR),
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
        "min": 20.0,
        "max": 120.0,
        "step": 0.2,
        "default": PUCK_DIA,
    },
    {
        "name": "puck_height",
        "label": "Charger height, no post (mm)",
        "type": "number",
        "min": 6.0,
        "max": 60.0,
        "step": 0.5,
        "default": PUCK_HEIGHT,
    },
    {
        "name": "wall",
        "label": "Wall thickness (mm)",
        "type": "number",
        "min": 1.2,
        "max": 6.0,
        "step": 0.2,
        "default": WALL,
    },
    {
        "name": "cable_boot_dia",
        "label": "Cable strain relief (mm)",
        "type": "number",
        "min": 2.0,
        "max": 12.0,
        "step": 0.5,
        "default": CABLE_BOOT_DIA,
    },
]
