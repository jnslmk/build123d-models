"""The printed part: concentric rings on a cross, magnet-hung inside the bowl.

    uv run show salad_bowl_lamp.shade
    uv run export salad_bowl_lamp.shade      # white PLA, no supports

Five concentric rings, 23 mm tall and 2.4 mm thick, tied together by four cross
arms of the same section, hung in the mouth of the inverted bowl by eight 5 x 1
disc magnets. All of those numbers are sliders on the website (``PARAMS``); they are
the lamp this repo built, not the only lamp this module can cut. From underneath it is the sketch this was drawn from; from the side it
is a baffle -- 20 mm of vertical wall between each 16 mm of air cuts the direct
view of the bulb at anything but a steep angle, which is the job.

**Print pose is use pose**, and it is the good one either way. The outer band
follows the bowl, so it *narrows* going up: no layer is wider than the one below
it, the part is self-supporting by construction, and the widest ring -- nearly
200 mm of it -- lands flat on the bed. The notch is the one place that could
have gone wrong and does not, because it ramps back out at 45 deg rather than
stepping: a step would hang 1.3 mm of ledge over open air, at the worst possible
height for it. No supports, no turning it over.

Four decisions carry the design:

* **The seat is a taper, not a clearance.** The band's outer face is the bowl's
  own inner sphere with nothing subtracted, so the shade slides up the dome
  until it beds. Being a 10.5 deg taper it cannot jam -- a part printed oversize
  simply comes to rest a little shallower -- and unlike a clearance fit it puts
  every magnet on steel rather than near it.
* **The bulge in the mouth gets a notch, not a smaller band.** The band reaches
  down to the rim plane now, and its bottom 5.8 mm are cut back 1.3 mm -- full
  depth over the bulge, then ramped at 45 deg back onto the sphere. So the seat
  is untouched over 17 of the band's 23 mm and the magnets stay mid-band on bare
  steel. It is cut in ``_seat_envelope`` rather than in the band, which is what
  makes it a notch in *every* piece of the shade at that height, arms included.
  The condition this carries -- that the bulge is a lump rather than a ring, so
  the shade can be tilted in past it -- is on ``config.Lamp``'s ``bead_w``.
* **The magnet touches the steel.** The pocket opens outward and the magnet is
  flush with the surface, with no cap over it. Burying a magnet under 0.4--0.8 mm
  of plastic (the ``part-joints`` default) is right when it meets another magnet;
  here it meets a thin spun bowl that is a mediocre keeper already, and the force
  is wanted in shear. Air gap is the one thing that kills such a joint, so the
  plastic gets out of the way and glue does the retaining.
* **The band is one even wall wherever it matters.** Both of its faces are
  struck from the bowl's own sphere centre, so it is ``WALL`` thick along every
  pocket axis and its inside is as plain as its outside -- no bosses, no pads,
  nothing standing proud where a hand goes when the shade is lifted out. A 1 mm
  magnet in a 2.4 mm wall leaves 1.4 mm behind it. The notch is cut from the
  outside alone, so the skirt below it is genuinely thinner (1.10 mm) rather
  than pushing a matching ridge into that inside face; the argument is in
  ``config.MIN_BACKING`` and ``Lamp.band_inner_radius``.

One construction note that is easy to get wrong: everything is built oversize
and trimmed **once**, by ``_seat_envelope``, so the band's outer face and the
arms' ends are all the same spherical surface and fuse into one. Trimming each
piece separately would leave coincident faces for the boolean to reconcile,
which is how OCC returns a subtly wrong solid without raising.

Every builder below takes the ``Lamp`` it is cutting rather than reading module
constants, which is what makes the sliders safe: two lamps can be built in one
process and neither can see the other's numbers.
"""

from __future__ import annotations

from math import cos, radians, sin, sqrt

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Line,
    Mode,
    Part,
    Plane,
    Polyline,
    Rectangle,
    Rotation,
    Sketch,
    ThreePointArc,
    Vector,
    Vertex,
    add,
    chamfer,
    extrude,
    loft,
    make_face,
    revolve,
)

from ..lib.edges import as_part
from .config import DEFAULT, SHADE_PARAMS, Lamp

SHADE_COLOR = Color(0.94, 0.94, 0.92)  # white PLA

PARAMS = SHADE_PARAMS
"""Every slider that reaches this geometry: the bowl's shape, the band, the
magnets and the grille. The bowl's drilled hole is absent on purpose -- the
shade never sees it."""

TRIM_OVERSIZE = 2.0
"""How far past the seat the blanks are built before the single trim.

Only has to be bigger than any gap it is covering; nothing measures it.
"""

TOL = 1e-9
"""When a notch, a ramp or a seat is short enough to be no segment at all.

Guards the ends of ``_outer_face``: with no bulge there is no notch and no ramp
to draw, and on a band short enough for the notch to swallow it there is no seat.
"""


def _ring(lamp: Lamp, r_bottom: float, r_top: float, wall: float | None = None) -> Part:
    """One ring, revolved from a chamfered profile.

    The chamfers are cut in the 2D profile rather than on the finished solid,
    and that is not a stylistic choice: these are the part's horizontal edges,
    the house rule wants all four of them broken, and a revolve of an
    already-broken profile cannot fail the all-or-nothing way an OCC edge op on
    twenty-odd circular edges can (see the ``build123d-geometry-ops`` skill).
    """
    wall = lamp.wall if wall is None else wall
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine():
                Polyline(
                    (r_bottom, 0.0),
                    (r_top, lamp.band_h),
                    (r_top - wall, lamp.band_h),
                    (r_bottom - wall, 0.0),
                    close=True,
                )
            make_face()
            if lamp.chamfer > 0:
                chamfer(profile.vertices(), length=lamp.chamfer)
        revolve(axis=Axis.Z)
    return ring.part


def _arc(radius, low: float, high: float) -> None:
    """A three-point arc up one of the band's spherical faces, ``low`` to ``high``."""
    ThreePointArc(
        (radius(low), low),
        (radius((low + high) / 2), (low + high) / 2),
        (radius(high), high),
    )


def _outer_face(lamp: Lamp) -> None:
    """Draw the band's outer face into the caller's ``BuildLine``, bottom to top.

    Three runs where the bulge needs a notch, one where it does not: the notch
    itself (an arc on the sphere, held ``band_notch_depth()`` inside it), the
    45 deg ramp back out, and then the seat -- the bowl's own sphere, unbroken,
    all the way to the band's top edge.

    Both ends are guarded because either run can vanish. A lamp with no bulge has
    no notch and this is the single arc the band was always cut from; a band
    short enough for the notch to swallow it whole has no seat left to draw.

    Always bottom to top, whichever way round the caller's loop runs:
    ``make_face`` combines the pending edges into a wire by their endpoints, so a
    face closes on which points meet, not on the order they were drawn in. Line
    objects find their builder through build123d's context variable rather than
    the call frame, so unlike a nested *builder* (see ``_teardrop``) they can be
    drawn from a helper.
    """
    face = lamp.band_outer_radius
    notch, ramp, top = lamp.band_notch_top(), lamp.band_notch_ramp_top(), lamp.band_h
    if notch > TOL:
        _arc(face, 0.0, notch)
    if ramp - notch > TOL:
        Line((face(notch), notch), (face(ramp), ramp))
    if top - ramp > TOL:
        _arc(face, ramp, top)


def _end_corners(profile: BuildSketch, outermost: bool) -> list[Vertex]:
    """The profile's two corners at its bottom and top, on one side or the other.

    Picked by position rather than by taking the two extreme radii, because the
    notch leaves two more vertices partway up the envelope's outer face where
    its ramp starts and finishes. Those two want no chamfer: at 45 deg the ramp
    is already the treatment, leaving ~135 deg corners that ``sharp_convex_edges``
    passes for exactly that reason, and a chamfer landing on one of them would
    take a bite out of the seat while leaving a real corner raw.

    **Grouped on Y, not Z, and these profiles are drawn on ``Plane.XZ``.** A
    ``BuildSketch``'s ``vertices()`` come back in the sketch's own local frame,
    where height is Y and every Z is exactly 0 -- the workplane is only applied
    when the sketch is placed. Grouping on Z therefore does not fail, it silently
    returns *one* group holding every vertex, so both ends of the loop pick the
    same corner and the other end ships raw. That is not a hypothetical: it got
    written that way first, and what caught it was ``check_edges``, not the build.
    """
    corners = []
    for end in (profile.vertices().group_by(Axis.Y)[0], profile.vertices().group_by(Axis.Y)[-1]):
        ordered = end.sort_by(Axis.X)
        corners.append(ordered[-1] if outermost else ordered[0])
    return corners


def _break_ends(lamp: Lamp, profile: BuildSketch, outermost: bool) -> None:
    """Chamfer a band profile's bottom and top corners, each to its own size.

    Two calls rather than one, because the two ends do not have the same wall
    behind them: the notch takes 1.3 mm off the bottom of a 2.4 mm band, so the
    skirt gets ``skirt_chamfer()`` and everything above it gets the part's own
    ``chamfer``. Sized together they would either leave the skirt with a knife
    edge or the rest of the part under-broken.
    """
    bottom, top = _end_corners(profile, outermost=outermost)
    for vertex, length in ((bottom, lamp.skirt_chamfer()), (top, lamp.chamfer)):
        if length > 0:
            chamfer(vertex, length=length)


def _band(lamp: Lamp) -> Part:
    """The outer ring: the finished inside face, an oversize blank outside.

    The inside is final here and is the one face that has to be right, because
    it is what the magnet pockets bottom out in -- struck from the same centre as
    the seat, so the wall is ``wall`` thick measured along a pocket's own axis
    rather than only in plan. The outside is left long and faced off by
    ``_seat_envelope`` along with everything else, which is why only the two
    inner corners are chamfered here: the outer two do not survive the trim, and
    the envelope carries their chamfer instead.

    The inner face is a single arc over the band's whole height and takes no part
    in the notch -- see ``Lamp.band_inner_radius`` for why the notch is cut from
    one side only, and what that leaves at the bottom.
    """
    with BuildPart() as band:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine():
                Polyline(
                    (lamp.band_outer_radius(0.0) + TRIM_OVERSIZE, 0.0),
                    (lamp.band_outer_radius(lamp.band_h) + TRIM_OVERSIZE, lamp.band_h),
                    (lamp.band_inner_radius(lamp.band_h), lamp.band_h),
                )
                _arc(lamp.band_inner_radius, 0.0, lamp.band_h)
                Polyline(
                    (lamp.band_inner_radius(0.0), 0.0),
                    (lamp.band_outer_radius(0.0) + TRIM_OVERSIZE, 0.0),
                )
            make_face()
            _break_ends(lamp, profile, outermost=False)
        revolve(axis=Axis.Z)
    return band.part


def _arm(lamp: Lamp) -> Part:
    """One cross arm, from inside the hub's wall out past the seat.

    Sketched as the *cross-section* and extruded along its length, so the
    chamfers run the full length of the arm's top and bottom edges. Sketching
    the silhouette instead and extruding sideways would chamfer the four short
    ends and leave the long horizontal edges raw, which is the opposite of what
    the rule asks for.

    It starts at ``arm_root_radius`` rather than at the axis, which is what
    keeps the innermost circle a circle instead of a cross in a circle. The
    inner end is a plain flat face and never needs treating, because it is not
    a surface of the finished part: it stops inside the hub's wall and the fuse
    absorbs it.
    """
    with BuildPart() as arm:
        with BuildSketch(Plane.YZ.offset(lamp.arm_root_radius())) as section:
            Rectangle(lamp.wall, lamp.band_h, align=(Align.CENTER, Align.MIN))
            if lamp.chamfer > 0:
                chamfer(section.vertices(), length=lamp.chamfer)
        extrude(amount=lamp.arm_reach() - lamp.arm_root_radius())
    return arm.part


def _cross(lamp: Lamp) -> Part:
    """Four arms on the quarters -- a cross with its middle left out."""
    with BuildPart() as cross:
        for angle in (0.0, 90.0, 180.0, 270.0):
            add(as_part(Rotation(0.0, 0.0, angle) * _arm(lamp)))
    return cross.part


def _seat_envelope(lamp: Lamp) -> Part:
    """Everything the shade is allowed to occupy: the bowl's inside, chamfered.

    A solid of revolution reaching from the axis out to the seat, so one
    intersection faces the band and docks all four arms in a single operation.
    The two outer corners carry the chamfer that the band's own profile cannot,
    since its outer face is cut away here.

    This is also where the bulge is answered, and answering it *here* is what
    makes the answer complete: the envelope is the only thing that sets the
    shade's outside diameter, so the notch cut into this profile is a notch in
    every piece of the shade at that height at once -- band and arm ends alike --
    rather than a feature the band carries and its neighbours do not.
    """
    with BuildPart() as envelope:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine():
                _outer_face(lamp)
                Polyline(
                    (lamp.band_outer_radius(lamp.band_h), lamp.band_h),
                    (0.0, lamp.band_h),
                    (0.0, 0.0),
                    (lamp.band_outer_radius(0.0), 0.0),
                )
            make_face()
            _break_ends(lamp, profile, outermost=True)
        revolve(axis=Axis.Z)
    return envelope.part


def pad_plane(lamp: Lamp, angle: float) -> Plane:
    """The seating plane of one magnet: on the steel, square to it.

    Its origin is a point of the bowl's own inner sphere and its z axis is that
    sphere's radius pointing *inward*, so the pocket is bored normal to the
    surface the magnet has to grab -- and, because the band's inside face is a
    sphere about the same centre, square to that face as well. Local +y is
    forced upward (``y_dir.Z > 0``) because the teardrop's roof is built along
    it, and a roof pointing sideways would print no better than no roof at all.
    """
    direction = Vector(cos(radians(angle)), sin(radians(angle)), 0.0)
    contact = direction * lamp.pad_face_radius() + Vector(0, 0, lamp.pad_depth_z)
    inward = (Vector(0, 0, lamp.sphere_centre_z()) - contact).normalized()
    tangential = Vector(0, 0, 1).cross(direction)
    plane = Plane(origin=contact, x_dir=tangential, z_dir=inward)
    if plane.y_dir.Z < 0:
        plane = Plane(origin=contact, x_dir=-tangential, z_dir=inward)
    return plane


def pad_planes(lamp: Lamp = DEFAULT) -> list[Plane]:
    step = 360.0 / lamp.magnet_count
    return [pad_plane(lamp, i * step) for i in range(lamp.magnet_count)]


def _teardrop(radius: float) -> Sketch:
    """A bore of ``radius`` with a 45 deg roof, as a finished sketch.

    The roof lines are tangent to the bore, meeting at ``radius * sqrt(2)``.
    That tangency is what makes a teardrop of ``radius + d`` the exact ``d``
    offset of a teardrop of ``radius``, which is what lets the lead-in below be
    a plain loft between two of these instead of a real 2D offset.

    Returned rather than drawn into the caller's sketch, and that is a build123d
    constraint rather than a preference: a builder only adopts a nested builder
    opened in the **same Python frame** (``Builder.__enter__`` compares
    ``inspect.currentframe()``). A ``BuildLine`` opened inside a helper has no
    parent, so its edges go nowhere and ``make_face`` fails on an empty pending
    list. Building the whole sketch here keeps every builder in one frame.
    """
    with BuildSketch() as drop:
        Circle(radius)
        tangent = radius / sqrt(2)
        with BuildLine():
            Polyline(
                (-tangent, tangent),
                (0.0, radius * sqrt(2)),
                (tangent, tangent),
                close=True,
            )
        make_face()
    return drop.sketch


def _pockets(lamp: Lamp) -> Part:
    """The magnet pockets, each with a lead-in all the way round its mouth.

    Depth is exactly ``magnet_t``: a pocket deeper than its magnet lets the disc
    sit at an unpredictable depth, and hold falls off fast with any air behind it.
    What is left behind it is whatever the wall has left to give -- 0.4 mm on the
    default lamp, and the case for that number is in ``config.MIN_BACKING``.

    The lead-in runs *inward* from the tangent plane rather than outward from it,
    which is the opposite of the obvious construction and is forced by the
    curvature. The face here is a sphere, so it lies at or below its own tangent
    plane everywhere except the single point of contact -- a chamfer cone built
    outside that plane would hang in mid-air and cut nothing, leaving the square
    mouth it was there to break.
    """
    lead = lamp.pocket_lead_in
    with BuildPart() as pockets:
        for plane in pad_planes(lamp):
            if lead > 0:
                with BuildSketch(plane):
                    add(_teardrop(lamp.pocket_d / 2 + lead))
                with BuildSketch(plane.offset(lead)):
                    add(_teardrop(lamp.pocket_d / 2))
                loft()
            with BuildSketch(plane):
                add(_teardrop(lamp.pocket_d / 2))
            extrude(amount=lamp.magnet_t)
    return pockets.part


def create_band(lamp: Lamp = DEFAULT) -> Part:
    """The outer ring on its own, seated and pocketed: the shade's whole seat.

    Shared with ``fit_test`` so the test print cannot drift from the part it is
    a test of -- it is this function's output and nothing else.
    """
    with BuildPart() as band:
        add(_band(lamp))
        add(_seat_envelope(lamp), mode=Mode.INTERSECT)
        add(_pockets(lamp), mode=Mode.SUBTRACT)
    return band.part


def create_shade(lamp: Lamp = DEFAULT) -> Part:
    """The shade, in print pose: widest ring on the bed, band narrowing upward."""
    with BuildPart() as shade:
        add(_band(lamp))
        for radius in lamp.ring_radii():
            add(_ring(lamp, radius, radius))
        add(_cross(lamp))
        add(_seat_envelope(lamp), mode=Mode.INTERSECT)
        add(_pockets(lamp), mode=Mode.SUBTRACT)

    part = shade.part
    part.label = "shade"
    part.color = SHADE_COLOR
    return part


def create(**params) -> Part:
    """Entry point for ``uv run show/export/render salad_bowl_lamp.shade``."""
    return create_shade(Lamp.of(**params))


__all__ = [
    "PARAMS",
    "SHADE_COLOR",
    "TRIM_OVERSIZE",
    "create",
    "create_band",
    "create_shade",
    "pad_plane",
    "pad_planes",
]
