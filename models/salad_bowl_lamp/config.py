"""Every measured and derived number for the salad-bowl lamp, in one place.

**Material is white PLA**, not the repo's PETG default (``AGENTS.md`` asks a
model that deviates to say so). Nothing here flexes, latches or carries load in
service -- the shade hangs from magnets and is otherwise decorative -- so PLA's
brittleness costs nothing and its dimensional tightness is why ``MAGNET_FIT``
below comes out where it does.

Two coordinate systems, and keeping them apart is the whole trick:

* **Bowl (upright).** ``z = 0`` at the outside of the bottom pole, ``z = BOWL_H``
  at the rim plane. This is the bowl as a bowl, and it is what ``BOWL_R`` is
  solved in.
* **Lamp (inverted).** The bowl is turned over to be the shade, so the rim plane
  is at the *bottom*. ``depth`` throughout this module means millimetres
  measured **up from the rim plane, into the dome** -- the direction the printed
  shade is inserted. ``bowl_inner_radius(depth)`` is the only bridge between the
  two, and every shade dimension is derived through it.

The bowl is a **spherical cap**, and that is not a modelling assumption laid on
top of the measurements -- it is forced by them. One sphere passes through a
200 mm rim circle and touches a plane 95 mm below it, and there is only one:
``BOWL_R`` solves ``(D/2)^2 + (H - R)^2 = R^2``. It lands at 100.13 mm, a hair
over the rim's own 100 mm radius, which is the same as saying the bowl is very
slightly shallower than a true hemisphere. That matches the photographs.
"""

from __future__ import annotations

from math import radians, sqrt, tan

from ..lib import fits

MATERIAL = "pla"

# --- The bought bowl ---------------------------------------------------------
# IKEA stainless salad bowl, as measured, plus the hole drilled through its
# bottom for the lamp holder. Only BOWL_HOLE_D is free of consequence: it is
# where the flex and the socket pass, and the shade never sees it.
BOWL_D = 200.0
BOWL_H = 95.0
BOWL_WALL = 0.8  # spun sheet; nominal, and the shade only cares that it exists
BOWL_HOLE_D = 42.0

BOWL_R = ((BOWL_D / 2) ** 2 + BOWL_H**2) / (2 * BOWL_H)
"""Outside radius of the spherical cap. Solved, not measured -- see the module docstring."""

BOWL_R_IN = BOWL_R - BOWL_WALL
"""Inside radius. The shade fits *this* sphere, which is the one 0.8 mm of steel smaller."""

RIM_DROP = BOWL_R - BOWL_H
"""How far the sphere's centre sits beyond the rim plane (5.13 mm), always positive.

Upright that is *above* the rim; inverted it is *below* it. It is the term that
turns a depth into a distance from the centre, so it appears in every radius
below and in the shade's pad normals.
"""


def bowl_inner_radius(depth: float) -> float:
    """Inside radius of the inverted bowl, ``depth`` mm above the rim plane.

    ``depth = 0`` is the rim itself (99.20 mm, *not* 100 -- the steel is on the
    outside of that number). It shrinks by 3.7 mm over the shade's 20 mm, which
    is why the shade's outer band follows an arc rather than being a cylinder --
    3.7 mm of taper is far too much to absorb in a clearance.
    """
    dz = depth + RIM_DROP
    if abs(dz) >= BOWL_R_IN:
        raise ValueError(f"depth {depth} is past the top of the dome")
    return sqrt(BOWL_R_IN**2 - dz**2)


def bowl_outer_height(radius: float) -> float:
    """Height above the rim plane of the bowl's *outside* at ``radius``, inverted.

    The dome's own profile. Only ``checks.py`` uses it, to put a probe on the
    steel near the lampholder hole rather than in the air above it -- at 25 mm
    out the dome has already dropped 3 mm from its apex, which is more than the
    wall is thick.
    """
    return sqrt(BOWL_R**2 - radius**2) - RIM_DROP


# --- The printed shade -------------------------------------------------------
BAND_H = 20.0  # "about 2 cm high": every ring and both cross arms
WALL = 3.0  # "3 mm thick": radial on a ring, tangential on a cross arm
CHAMFER = 0.6  # every horizontal edge, cut in the revolved profile

RIM_INSET = 3.0
"""How far above the bowl's rim the shade's underside sits.

Not decoration: a spun rim is rolled or hemmed over its last millimetre or two,
so the inside radius right at the lip is neither round nor equal to
``bowl_inner_radius(0)``. Starting 3 mm up puts the whole band on plain
spherical wall, and reads as a deliberate reveal from below rather than as a
part that failed to sit flush.
"""

SEAT_CLEAR = 0.0
"""Radial gap between the band and the bowl. There isn't one, and that is the design.

The band's outer face *is* ``bowl_inner_radius``, over its whole 20 mm, which
makes this a taper seat rather than a clearance fit -- and a taper seat is the
one kind that cannot jam. The mating surfaces converge at 10.5 deg, so a shade
printed a few tenths oversize does not bind, it comes to rest a couple of
millimetres shallower; one printed undersize sits deeper. Either way every
magnet lands on steel, which a clearance fit cannot promise: hold force
collapses with air gap, and a spun bowl is out of round by more than any gap
worth leaving.

Kept as a named constant at zero rather than deleted, because "no clearance
here" is a decision that ``checks.py`` asserts and a later reader is owed.
"""

EYE_D = 45.0
"""The open circle at the middle. Sized to pass an E27 lampholder shell, so a
bulb that hangs below the rim has somewhere to go; see README."""

RING_COUNT = 5
"""Concentric rings, counting the outer band and the hub. The cross is separate."""

# --- Magnets -----------------------------------------------------------------
# Round N42-class discs, glued into pockets around the outer band, meeting the
# steel face-on with nothing between them.
MAGNET_D = 8.0
MAGNET_T = 3.0
MAGNET_COUNT = 8

MAGNET_FIT = fits.for_material(fits.FREE, MATERIAL)
"""0.30 mm diametral. FREE, not SNUG, and not a press fit at all.

The part-joints skill wants +0.2--0.3 mm for a magnet pocket, and FREE-in-PLA
lands exactly on the top of that band. A sintered magnet chips rather than
deforms, so the pocket must never be the thing holding it. Glue is.
"""

POCKET_D = MAGNET_D + MAGNET_FIT
POCKET_LEAD_IN = 0.5  # 45 deg all round the mouth, lofted, per the house rule

PAD_BACKING = 3.0
"""Material left behind a seated magnet: four perimeters at a 0.4 mm nozzle.

This is what forces the bosses to exist at all. The band is 3 mm thick and the
magnet is 3 mm deep, so a pocket cut into the plain band would come straight out
the other side.
"""

BOSS_R = 9.0
"""Radius of a magnet boss where it leaves the band's outer face.

Bounded on both sides, and not by much. Below about 8 mm the pocket's own
teardrop breaks out through the boss's taper at the pocket floor; above 10 mm the
boss -- centred at mid-height -- runs past the top and bottom of a 20 mm band and
dies out in a feather edge instead of landing on a face. 9 mm leaves ~2.4 mm of
material around the pocket's mouth, ~1 mm around the teardrop's peak at the
floor, and ~1.2 mm of band above and below the boss.
"""

BOSS_TAPER = 35.0
"""Half-angle of the boss, from its own axis.

The rim where the boss's flank meets its end face measures ``90 + BOSS_TAPER``
through the material, so this is the constant that decides whether that rim is a
broken edge or a square one. 30 deg lands on exactly 120, which is the *inside*
of ``sharp_convex_edges``' ``max_interior`` -- it reported all eight rims, and
was right to: 120 is where the rule stops complaining, not where the edge starts
being blunt. 35 deg clears it by five, at the cost of a smaller end face, the boss still leaves ~1 mm of material around the
teardrop's peak at the pocket floor. The boss meets the band *concavely*, so the
junction that killed the first design -- a 45 deg flank in plan, which dies into
the band's inner face at an acute 34 deg -- does not arise here at all. Printing
does not constrain this: the flank's underside lands ~25 deg above horizontal
over a 3 mm run, a small overhang on an internal face, no support anywhere.
"""

PAD_DEPTH_Z = BAND_H / 2
"""Height of the pocket axis. Mid-band, so the eight magnets pull on a single
circle through the part's own centre of mass and nothing tips."""


def boss_depth() -> float:
    """How deep a boss reaches along its own axis: the magnet, then its backing."""
    return MAGNET_T + PAD_BACKING


def boss_end_radius() -> float:
    """Radius of the boss's flat end face, after the taper has run its course."""
    return BOSS_R - boss_depth() * tan(radians(BOSS_TAPER))


def band_outer_radius(z: float) -> float:
    """The band's outer face, ``z`` mm up from the shade's underside.

    The bowl's own inner sphere, less ``SEAT_CLEAR`` -- which is zero. A revolved
    arc, not a chord: a straight cone between the same two ends would sag 0.5 mm
    away from the steel at mid-height, turning a seat that beds down over 20 mm
    into one that touches at two rims.
    """
    return bowl_inner_radius(RIM_INSET + z) - SEAT_CLEAR


def pad_face_radius() -> float:
    """Radius at which a magnet meets the steel: the band's face, at pad height.

    The magnet is flush with the tangent plane there, and the spherical face
    around it falls away from that plane by 0.09 mm across the magnet's own
    8 mm. So the magnet -- not the plastic -- is what touches, which is the
    whole point of putting the pocket here rather than under a printed cap.
    """
    return band_outer_radius(PAD_DEPTH_Z)


def sphere_centre_z() -> float:
    """The bowl's sphere centre in *shade-local* coordinates -- below z = 0.

    A boss's axis is a radius of this point, which is what makes each pocket
    square to the steel rather than merely near it, and each magnet's face
    tangent to it rather than merely close.
    """
    return -(RIM_INSET + RIM_DROP)


def ring_gap() -> float:
    """Radial air between neighbouring rings, and it is one number by choice.

    Evenly spaced reads as concentric; anything else reads as a mistake. The
    The band's inner radius at the *bottom* is the datum because that is where
    the band is widest, so that is where the gap is largest -- it closes by
    3.7 mm over the height, which is invisible from below and is the price of a
    band that follows the bowl.
    """
    span = band_outer_radius(0.0) - WALL - hub_outer_radius()
    inner_rings = RING_COUNT - 2
    return (span - inner_rings * WALL) / (inner_rings + 1)


def hub_outer_radius() -> float:
    return EYE_D / 2 + WALL


def ring_radii() -> list[float]:
    """Outer radii of every ring *except* the band, widest first, hub last."""
    gap = ring_gap()
    start = band_outer_radius(0.0) - WALL
    radii = [
        start - (i + 1) * gap - i * WALL for i in range(RING_COUNT - 2)
    ]
    return [*radii, hub_outer_radius()]


def arm_reach() -> float:
    """Half-length of a cross arm before the seat envelope trims it back."""
    return band_outer_radius(0.0) + 1.0
