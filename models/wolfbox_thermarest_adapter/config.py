"""Every number the blower-to-mattress adapter is cut from, with its provenance.

**Read this before printing.** Nothing here was calipered. Nobody in this repo
has held a WOLFBOX MF100 or a Therm-a-Rest WingLock valve, and neither
manufacturer publishes a dimensioned drawing of the interface -- so every
diameter below is *researched* or *assumed*, in the sense the
``photo-reverse-engineering`` skill uses those words, and each constant says
which it is. The same rule that model states applies here in full: a number
that was never measured must say so.

That is also why no end of either adapter is a copy of anything. Every end
is a **tapered socket**, and a taper is the answer to not knowing a diameter:
it seats wherever its cone happens to meet the port, so one part covers a whole
range instead of one number. The ``part-joints`` rule "lead-ins and compliant
features beat tight tolerances" is the general form of that argument -- here it
is taken to its limit, because the tolerance is not merely tight, it is
unknown.

**What the taper ranges have to cover**

* *Blower end.* The MF100's nozzles mount on a quarter-turn bayonet with
  locking tabs, which this deliberately does **not** reproduce: cloning a
  bayonet needs the lug geometry, and getting it wrong gives a part that cannot
  be fitted at all, where getting a taper wrong only moves where it seats. The
  socket pushes onto the bare outlet port with the stock nozzle removed -- and,
  further in, onto the body of a stock nozzle if one is left on. Stock nozzles
  are quoted by makers who calipered them at a 6 mm round jet and a 12 x 3 mm
  flat jet, so the nozzle *bodies* are the small end of the range and the bare
  port is the large end.
* *Valve end.* Every WingLock pump-sack adapter in the wild works by pressing
  or snapping **over** the valve. EXPED's own WingLock adapter is quoted at
  28 mm outside / 24 mm inside diameter, and a bore of 24 mm is what puts a
  number on the valve's raised barrel; a Backpacking Light thread describes
  1/2" poly tubing pressed over the same barrel, which is the same ballpark.
  DIY pump-sack builds cut a 25-30 mm hole for it. So: something near 24 mm to
  seal on, inside a valve body in the low thirties to clear.

* *Intake end.* The deflate adapter's, and the only end that is not a port at
  all: reviews describe the MF100's rear as a fixed grille around the fan disc,
  so there is nothing to push into and nothing to twist onto. It is capped from
  outside instead, over a barrel that retail listings bound at 39.9 mm -- the
  device measures 1.57 x 1.57 x 6.3 in, so nothing on it is wider than that.
  A cap covering 34 to 46 mm brackets it either way.

None of that is a measurement, which is why both parts are parametric. Six
numbers each, all sliders on the website: change one and re-export, do not
re-model. ``README.md`` says which slider to move for which symptom.

**One file, two parts.** Everything from the throat up is shared -- both
adapters press the same cup onto the same valve, and only the machine end of
the funnel differs -- so the valve-end numbers below are written once and
consumed by both through ``_CupEnd``. Dial the cup in for one and it is dialled
in for the other.

Material is the repo default, **PETG**. Nothing latches and nothing is
load-bearing -- the seal is hand or suction pressure on a cone -- so the only material
argument is compliance, and that is what ``CUP_WALL`` buys. TPU 95A prints the
same geometry and seals better; see ``README.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees, hypot

from ..lib import fits

MATERIAL = "petg"

# --------------------------------------------------------------------------
# Slider stops. These describe *the two ports this adapter is for*, plus room
# for the mis-measurement the ledger above admits to -- they are not an
# arbitrary span. Wide enough that a caliper reading can always be dialled in,
# narrow enough that every position still builds a sane funnel.
# --------------------------------------------------------------------------

BLOWER_MOUTH_MIN, BLOWER_MOUTH_MAX = 18.0, 40.0
BLOWER_THROAT_MIN, BLOWER_THROAT_MAX = 8.0, 30.0
SOCKET_DEPTH_MIN, SOCKET_DEPTH_MAX = 12.0, 40.0
VALVE_MOUTH_MIN, VALVE_MOUTH_MAX = 22.0, 48.0
VALVE_SEAT_MIN, VALVE_SEAT_MAX = 12.0, 36.0
CUP_DEPTH_MIN, CUP_DEPTH_MAX = 6.0, 28.0

# The deflate adapter's own three. Its cap goes *over* a 40 mm baton rather
# than *into* a port, so its stops sit a whole size class above the socket's
# -- but they are picked the same way, wide enough to swallow a caliper
# reading and narrow enough that every position is still a funnel.
BODY_MOUTH_MIN, BODY_MOUTH_MAX = 30.0, 70.0
BODY_SEAT_MIN, BODY_SEAT_MAX = 22.0, 62.0
CAP_DEPTH_MIN, CAP_DEPTH_MAX = 10.0, 45.0

# --------------------------------------------------------------------------
# The blower end. RESEARCHED range, ASSUMED numbers -- see the docstring.
# --------------------------------------------------------------------------

BLOWER_MOUTH_DIA = 27.0
"""Bore where the socket meets the bed: the widest port it can swallow.

ASSUMED. The MF100's outlet with its nozzle twisted off is a round port in the
low twenties; 27 mm is that plus room, so the cone always seats on its *side*
rather than bottoming out on its rim. Erring wide is free -- a port narrower
than this just seats deeper -- while erring narrow makes the adapter refuse to
go on at all, which is the asymmetry every number on this end is picked by.
"""

BLOWER_THROAT_DIA = 16.0
"""Bore at the deep end of the socket cone, and the adapter's flow path.

ASSUMED, but bounded by physics rather than by the blower: this is the
narrowest section air passes through, so it is as *large* as the taper allows
rather than as small as it can be. A duster is a high-velocity, low-static-
pressure source and a restriction costs volume flow, which is the thing being
traded for inflation time. 16 mm is at or above the bore of every stock MF100
nozzle (the round one is quoted at 6 mm), so the adapter never becomes the
narrowest thing in the path.
"""

SOCKET_DEPTH = 24.0
"""Axial length of the socket cone, mouth to throat.

ASSUMED. With the two diameters above this sets the half-angle to about 13
degrees -- shallow enough to wedge and hold under hand pressure, steep enough
to release without a tool. Deep also means *long contact*, which is what does
the sealing here: there is no gasket, only a band of cone touching a cylinder.
"""

# --------------------------------------------------------------------------
# The intake end. The whole of the deflate adapter's difference: everything
# below the throat, where the inflate adapter has its socket. RESEARCHED
# range, ASSUMED numbers -- see the docstring.
# --------------------------------------------------------------------------

BODY_MOUTH_DIA = 46.0
"""Bore where the tail cap meets the bed: the widest body it can swallow.

ASSUMED, off a RESEARCHED bounding box. Retail listings give the MF100 as
1.57 x 1.57 x 6.3 in, so its widest section is at most 39.9 mm and the barrel
is something at or under that. 46 mm is that plus 6 mm of room, so the cone
always seats on its flank rather than stubbing on the tail's rim -- the same
err-wide asymmetry the socket end is picked by, for the same reason.
"""

BODY_SEAT_DIA = 34.0
"""Bore at the deep end of the tail cone: the narrowest body it can grip.

ASSUMED. With the mouth above this covers every barrel from 34 to 46 mm, which
brackets the 40 mm the listing implies by 6 mm either way, and puts the
half-angle at about 15 degrees -- a shade steeper than the socket's 13, still
firmly in wedge territory. A 40 mm body seats about 11 mm in, leaving the rest
of the depth as reserve for a barrel that turns out fatter.
"""

CAP_DEPTH = 22.0
"""Axial length of the tail cone, mouth to seat.

ASSUMED, and the one number here with a job beyond fit: the cap has to cover
the intake, not merely grip near it. Reviews describe the MF100's rear as a
fixed grille around the fan disc -- an end face, not a port -- so a cap that
swallows the last 22 mm of the baton covers that grille and any vent slotted
into the barrel behind it, and still has 10 mm of cone in contact once a 40 mm
body has seated.
"""

INTAKE_THROAT_DIA = 18.0
"""Bore of the deflate adapter's throat, and its flow path.

ASSUMED, and larger than the inflate adapter's 16 mm because nothing on this
end argues for restraint: there is no nozzle bore to stay clear of, only the
cup seat above, and ``IntakeAdapter.of`` shrinks this to keep the flare
flaring whenever a slider pulls the seat down near it. Derived rather than
exposed -- the deflate part keeps the same six sliders as the inflate one, and
none of them is worth spending on a number with only one sensible value.
"""

# --------------------------------------------------------------------------
# The valve end. Shared: both adapters press the same cup onto the same valve,
# and only the machine end of the funnel differs.
# RESEARCHED range, ASSUMED numbers -- see the docstring.
# --------------------------------------------------------------------------

VALVE_SEAT_DIA = 22.0
"""Bore at the bottom of the cup: the smallest thing the cone can seal on.

ASSUMED, from EXPED's 24 mm adapter bore. Sitting 2 mm under that is
deliberate -- the cone must *reach past* the barrel it seals on, so contact
happens on the cone's flank a little way up, not on a rim that would rock.
"""

VALVE_MOUTH_DIA = 34.0
"""Bore at the cup's rim: the largest valve body it will drop over.

ASSUMED. DIY pump-sack builds cut a 25-30 mm hole for a WingLock, so the valve
body plus its wings is a low-thirties object; 34 mm swallows that and lets the
cup find the valve without being aimed.
"""

CUP_DEPTH = 14.0
"""Axial depth of the cup, seat to rim.

ASSUMED. Enough that the cone spans the whole 22-34 mm range at a workable
angle (about 25 degrees), and shallow enough that the wings do not foul the
bottom of the cup before the cone touches.
"""

# --------------------------------------------------------------------------
# Structure. These are the numbers that are *not* about the two ports, and the
# only ones here that are chosen rather than guessed.
# --------------------------------------------------------------------------

SOCKET_WALL = 2.4
"""Six perimeters at a 0.4 mm nozzle, around the blower socket.

The socket is what the hand grips and what the blower's thrust reacts against,
so it is the structural end. It is also the end that must *not* flex: a socket
that spreads under load walks off the port.
"""

CUP_WALL = 1.2
"""Three perimeters, around the valve cup. Thin on purpose.

This is the seal. A cone pressed onto a moulded valve seals by conforming to
it, and at 1.2 mm a PETG cone of this diameter still gives a little where a
2.4 mm one would stand off on the high spots -- the same argument as
``lens_cap``'s deliberately thin wall, and the reason TPU is worth a spool here
if you have one.
"""

CAP_WALL = 2.4
"""Six perimeters around the deflate adapter's tail cap.

The same argument as ``SOCKET_WALL`` and then some: this skirt is what the
whole 366 g duster hangs from while the cup is held down on the valve, and a
skirt that spreads under that load walks off the barrel.
"""

NECK_WALL = 2.8
"""Seven perimeters around the deflate adapter's neck, between the two cones.

Thicker than anything on the inflate part, because the neck is the only place
this one is loaded in bending: a 160 mm baton on the end of a 46 mm cap is a
lever, and its root is the throat. Cheap insurance -- at this diameter the
extra 0.4 mm is well under a gram.
"""

THROAT_LEN = 6.0
"""Straight section between the two cones.

Not a fit and not decoration: two cones meeting at a point would put the
socket's deepest seat and the cup's shallowest one at the same height, so a
port pushed hard would bear on the cup's seat from below. The straight section
separates them, and gives the flow a moment of parallel wall before it opens
out.
"""

FLARE_ANGLE = 45.0
"""Angle of both 45 degree steps in the bore, in degrees from vertical.

Not one constraint but two, pointing opposite ways, and only one of them is
about printing:

* The **flare**, throat bore up to cup seat, is on both parts. It *widens* as
  it rises, so it is not an overhang at all -- every layer is set back from the
  one under it. 45 degrees is chosen instead to keep the step short, so the
  part stays low, and to give the flow a ramp rather than a square ledge.
* The **shoulder**, cap seat down to throat bore, is on the deflate adapter
  only, and is the mirror image: it *narrows* as it rises, which makes it a
  genuine downward-facing internal surface -- 45 degrees is the steepest one of
  those can be and still print dry. It is the one angle in either part with a
  real limit behind it, which is why ``checks.py`` measures the bore's steepest
  narrowing segment rather than taking this constant's word for it.

Both are built by construction rather than read from here: the geometry gives
each step a rise equal to its radial run, which is what 45 degrees means.
"""

MOUTH_CHAMFER = 0.8
"""Lead-in at the socket's mouth, per the ``part-joints`` rule that every
mating mouth gets one. It is what lets the adapter start onto a port that is
not perfectly aligned, instead of stubbing on the rim."""

RIM_CHAMFER = 0.35
"""Break on both corners of the cup's rim. Small, because ``CUP_WALL`` is
1.2 mm and two of these plus a printable flat have to fit across it."""

BED_CHAMFER = 0.5
"""Elephant's-foot relief on the outer bed edge. The first layer of a funnel
this tall is a narrow ring and squishes wide; this is what keeps the socket
from arriving 0.3 mm undersize where it matters most."""

MIN_WALL = fits.MIN_WALL
"""The floor every wall in the part is checked against: 0.8 mm, two
perimeters. Below it a wall does not slice as a wall at all."""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class _CupEnd:
    """The valve end of a funnel: the half both adapters have in common.

    Inflating and deflating a pad are the same problem at the mattress -- press
    a cone onto a moulded valve and hold it -- so the cup, its seat, its rim
    and the wall that has to conform to the valve are identical on both parts,
    and only the machine end of the funnel differs. Sharing them here is what
    makes that a fact of the code rather than a claim in a README: change
    ``CUP_DEPTH`` and both parts move.

    A plain mixin rather than a dataclass base, because the two adapters do not
    agree on field *order* -- each puts its own machine end first -- and a
    dataclass base would impose one on both.
    """

    valve_mouth_dia: float
    valve_seat_dia: float
    cup_depth: float

    @property
    def seat_r(self) -> float:
        return self.valve_seat_dia / 2

    @property
    def rim_r(self) -> float:
        return self.valve_mouth_dia / 2

    @property
    def cup_half_angle(self) -> float:
        """Half-angle of the cup cone, degrees from the axis."""
        return degrees(atan2(self.rim_r - self.seat_r, self.cup_depth))

    def cup_wall_offset(self) -> float:
        return _normal_offset(CUP_WALL, self.rim_r - self.seat_r, self.cup_depth)


@dataclass(frozen=True)
class Adapter(_CupEnd):
    """One buildable set of the six numbers, with the geometry derived off them.

    Built through ``Adapter.of``, never by hand: the constructor takes whatever
    the sliders hand it, and ``of`` is what turns that into something that
    still describes a funnel -- a throat narrower than its mouth, a seat wider
    than the throat, a rim wider than the seat.
    """

    blower_mouth_dia: float = BLOWER_MOUTH_DIA
    blower_throat_dia: float = BLOWER_THROAT_DIA
    socket_depth: float = SOCKET_DEPTH
    valve_mouth_dia: float = VALVE_MOUTH_DIA
    valve_seat_dia: float = VALVE_SEAT_DIA
    cup_depth: float = CUP_DEPTH

    @classmethod
    def of(
        cls,
        blower_mouth_dia: float = BLOWER_MOUTH_DIA,
        blower_throat_dia: float = BLOWER_THROAT_DIA,
        socket_depth: float = SOCKET_DEPTH,
        valve_mouth_dia: float = VALVE_MOUTH_DIA,
        valve_seat_dia: float = VALVE_SEAT_DIA,
        cup_depth: float = CUP_DEPTH,
    ) -> Adapter:
        """Clamp six slider values into a set that still builds a funnel.

        The ordering constraints are applied after the individual stops and in
        one direction only -- each diameter is pushed away from its neighbour
        rather than the neighbour being pulled -- so dragging any one slider to
        either stop leaves the others where the user put them wherever that is
        still legal.
        """
        mouth = _clamp(blower_mouth_dia, BLOWER_MOUTH_MIN, BLOWER_MOUTH_MAX)
        throat = _clamp(blower_throat_dia, BLOWER_THROAT_MIN, BLOWER_THROAT_MAX)
        # A socket with no taper is a plain bore: it grips one diameter and
        # nothing else, which is the whole failure this design exists to avoid.
        throat = min(throat, mouth - 2 * MIN_TAPER_DROP)
        seat = _clamp(valve_seat_dia, VALVE_SEAT_MIN, VALVE_SEAT_MAX)
        # The cup's seat has to stand proud of the throat bore, or the flare
        # inverts and the cup drains into a lip that would catch the valve.
        seat = max(seat, throat + 2 * MIN_SEAT_STEP)
        rim = _clamp(valve_mouth_dia, VALVE_MOUTH_MIN, VALVE_MOUTH_MAX)
        rim = max(rim, seat + 2 * MIN_TAPER_DROP)
        return cls(
            blower_mouth_dia=mouth,
            blower_throat_dia=throat,
            socket_depth=_clamp(socket_depth, SOCKET_DEPTH_MIN, SOCKET_DEPTH_MAX),
            valve_mouth_dia=rim,
            valve_seat_dia=seat,
            cup_depth=_clamp(cup_depth, CUP_DEPTH_MIN, CUP_DEPTH_MAX),
        )

    # --- radii ----------------------------------------------------------
    @property
    def mouth_r(self) -> float:
        return self.blower_mouth_dia / 2

    @property
    def throat_r(self) -> float:
        return self.blower_throat_dia / 2

    # --- heights --------------------------------------------------------
    @property
    def z_throat(self) -> float:
        """Top of the socket cone, where the straight throat starts."""
        return self.socket_depth

    @property
    def z_throat_top(self) -> float:
        return self.z_throat + THROAT_LEN

    @property
    def z_seat(self) -> float:
        """Bottom of the cup, after the 45 degree flare off the throat."""
        return self.z_throat_top + (self.seat_r - self.throat_r)

    @property
    def z_rim(self) -> float:
        return self.z_seat + self.cup_depth

    # --- what the tapers actually promise -------------------------------
    @property
    def socket_half_angle(self) -> float:
        """Half-angle of the blower cone, degrees from the axis."""
        return degrees(atan2(self.mouth_r - self.throat_r, self.socket_depth))

    def socket_wall_offset(self) -> float:
        """Horizontal offset that leaves ``SOCKET_WALL`` measured normal to the
        cone. A cone offset sideways by its wall is thinner than that wall by
        the cosine of its angle, which at 13 degrees is 2% and at the slider
        stops is 20% -- enough to walk a nominal 2.4 mm wall under the floor.
        """
        return _normal_offset(SOCKET_WALL, self.mouth_r - self.throat_r, self.socket_depth)


MIN_TAPER_DROP = 1.5
"""Smallest radial drop a cone may have and still be a taper rather than a bore.
Applied by ``Adapter.of`` at both ends."""

MIN_SEAT_STEP = 1.0
"""Smallest radial step from throat bore to cup seat, so the flare always
flares."""


def _normal_offset(wall: float, dr: float, dz: float) -> float:
    """Horizontal offset of a parallel surface ``wall`` away from a sloped one."""
    if dz <= 0:
        return wall
    return wall * hypot(dr, dz) / dz


DEFAULT = Adapter.of()
"""The numbers at the top of this file, clamped -- what ``create()`` builds."""


@dataclass(frozen=True)
class IntakeAdapter(_CupEnd):
    """The deflate adapter's numbers: the same cup, on the duster's other end.

    A blower has two ports, and only one of them is a port. The outlet takes a
    nozzle on a bayonet; the intake is a fixed grille around the fan disc, with
    nothing to push into and nothing to twist onto. So this end does not seat
    *in* anything -- it is a cap that swallows the tail of the baton and seals
    on the barrel's outside, which turns the whole rear of the tool into one
    duct. Cover the grille and every cubic centimetre the fan draws has to come
    through the cup, which is the entire trick: the pad empties through the
    duster instead of past it.

    Suction is also what makes this end *easier* than the outlet end. On the
    inflate adapter the blower's thrust is trying to push the socket off the
    port and the cup off the valve, and hand pressure is what resists it. Here
    the pressure difference runs the other way: it seats the cap harder onto
    the barrel and the cup harder onto the valve, the whole time it is working.
    Nothing here has to hold on -- it only has to not leak.

    Built through ``IntakeAdapter.of``, never by hand, for the reason
    ``Adapter.of`` gives.
    """

    body_mouth_dia: float = BODY_MOUTH_DIA
    body_seat_dia: float = BODY_SEAT_DIA
    cap_depth: float = CAP_DEPTH
    valve_mouth_dia: float = VALVE_MOUTH_DIA
    valve_seat_dia: float = VALVE_SEAT_DIA
    cup_depth: float = CUP_DEPTH
    throat_dia: float = INTAKE_THROAT_DIA

    @classmethod
    def of(
        cls,
        body_mouth_dia: float = BODY_MOUTH_DIA,
        body_seat_dia: float = BODY_SEAT_DIA,
        cap_depth: float = CAP_DEPTH,
        valve_mouth_dia: float = VALVE_MOUTH_DIA,
        valve_seat_dia: float = VALVE_SEAT_DIA,
        cup_depth: float = CUP_DEPTH,
    ) -> IntakeAdapter:
        """Clamp six slider values into a set that still builds a funnel.

        Six, the same six the inflate adapter exposes, because the throat is
        the one number here with only one sensible answer: as wide as the two
        cones either side of it leave room for. So it is *derived* -- pulled
        down whenever a slider drags the cup's seat or the cap's seat near it,
        and never exposed as a seventh control nobody would know how to set.
        """
        mouth = _clamp(body_mouth_dia, BODY_MOUTH_MIN, BODY_MOUTH_MAX)
        seat = _clamp(body_seat_dia, BODY_SEAT_MIN, BODY_SEAT_MAX)
        # A cap with no taper grips one barrel and nothing else -- the same
        # failure ``Adapter.of`` guards the socket against.
        seat = min(seat, mouth - 2 * MIN_TAPER_DROP)
        valve_seat = _clamp(valve_seat_dia, VALVE_SEAT_MIN, VALVE_SEAT_MAX)
        rim = _clamp(valve_mouth_dia, VALVE_MOUTH_MIN, VALVE_MOUTH_MAX)
        rim = max(rim, valve_seat + 2 * MIN_TAPER_DROP)
        # Wide as it can be, and no wider: the flare above has to flare and the
        # shoulder below has to step down.
        throat = min(
            INTAKE_THROAT_DIA,
            valve_seat - 2 * MIN_SEAT_STEP,
            seat - 2 * MIN_SEAT_STEP,
        )
        return cls(
            body_mouth_dia=mouth,
            body_seat_dia=seat,
            cap_depth=_clamp(cap_depth, CAP_DEPTH_MIN, CAP_DEPTH_MAX),
            valve_mouth_dia=rim,
            valve_seat_dia=valve_seat,
            cup_depth=_clamp(cup_depth, CUP_DEPTH_MIN, CUP_DEPTH_MAX),
            throat_dia=throat,
        )

    # --- radii ----------------------------------------------------------
    @property
    def body_mouth_r(self) -> float:
        return self.body_mouth_dia / 2

    @property
    def body_seat_r(self) -> float:
        return self.body_seat_dia / 2

    @property
    def throat_r(self) -> float:
        return self.throat_dia / 2

    # --- heights --------------------------------------------------------
    @property
    def z_cap(self) -> float:
        """Deep end of the tail cone, where the 45 degree shoulder starts."""
        return self.cap_depth

    @property
    def z_throat(self) -> float:
        """Bottom of the straight throat, after the shoulder."""
        return self.z_cap + (self.body_seat_r - self.throat_r)

    @property
    def z_throat_top(self) -> float:
        return self.z_throat + THROAT_LEN

    @property
    def z_seat(self) -> float:
        """Bottom of the cup, after the 45 degree flare off the throat."""
        return self.z_throat_top + (self.seat_r - self.throat_r)

    @property
    def z_rim(self) -> float:
        return self.z_seat + self.cup_depth

    # --- what the tapers actually promise -------------------------------
    @property
    def cap_half_angle(self) -> float:
        """Half-angle of the tail cone, degrees from the axis."""
        return degrees(atan2(self.body_mouth_r - self.body_seat_r, self.cap_depth))

    def cap_wall_offset(self) -> float:
        return _normal_offset(
            CAP_WALL, self.body_mouth_r - self.body_seat_r, self.cap_depth
        )


INTAKE_DEFAULT = IntakeAdapter.of()
"""The intake-end numbers above, clamped -- what ``deflate.create()`` builds."""
