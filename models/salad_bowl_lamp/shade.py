"""The printed part: concentric rings on a cross, magnet-hung inside the bowl.

    uv run show salad_bowl_lamp.shade
    uv run export salad_bowl_lamp.shade      # white PLA, no supports

Five concentric rings, 20 mm tall and 2.6 mm thick, tied together by four cross
arms of the same section, hung in the mouth of the inverted bowl by eight disc
magnets. From underneath it is the sketch this was drawn from; from the side it
is a baffle -- 20 mm of vertical wall between each 16 mm of air cuts the direct
view of the bulb at anything but a steep angle, which is the job.

**Print pose is use pose**, and it is the good one either way. The outer band
follows the bowl, so it *narrows* going up: every layer is smaller than the one
below it, the part is self-supporting by construction, and the widest ring --
200 mm of it -- lands flat on the bed. No supports, no turning it over.

Three decisions carry the design:

* **The seat is a taper, not a clearance.** The band's outer face is the bowl's
  own inner sphere with nothing subtracted, so the shade slides up the dome
  until it beds. Being a 10.5 deg taper it cannot jam -- a part printed oversize
  simply comes to rest a little shallower -- and unlike a clearance fit it puts
  every magnet on steel rather than near it.
* **The magnet touches the steel.** The pocket opens outward and the magnet is
  flush with the surface, with no cap over it. Burying a magnet under 0.4--0.8 mm
  of plastic (the ``part-joints`` default) is right when it meets another magnet;
  here it meets a thin spun bowl that is a mediocre keeper already, and the force
  is wanted in shear. Air gap is the one thing that kills such a joint, so the
  plastic gets out of the way and glue does the retaining.
* **The band is one even wall, inside and out.** Both of its faces are struck
  from the bowl's own sphere centre, so it is ``WALL`` thick along every pocket
  axis and its inside is as plain as its outside -- no bosses, no pads, nothing
  standing proud where a hand goes when the shade is lifted out. A 2 mm magnet
  in a 2.6 mm wall is what makes that possible; the argument is in
  ``config.pad_backing`` and ``config.band_inner_radius``.

One construction note that is easy to get wrong: everything is built oversize
and trimmed **once**, by ``_seat_envelope``, so the band's outer face and the
arms' ends are all the same spherical surface and fuse into one. Trimming each
piece separately would leave coincident faces for the boolean to reconcile,
which is how OCC returns a subtly wrong solid without raising.
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
    Mode,
    Part,
    Plane,
    Polyline,
    Rectangle,
    Rotation,
    Sketch,
    ThreePointArc,
    Vector,
    add,
    chamfer,
    extrude,
    loft,
    make_face,
    revolve,
)

from ..lib.edges import as_part
from . import config as c

SHADE_COLOR = Color(0.94, 0.94, 0.92)  # white PLA

TRIM_OVERSIZE = 2.0
"""How far past the seat the blanks are built before the single trim.

Only has to be bigger than any gap it is covering; nothing measures it.
"""


def _ring(r_bottom: float, r_top: float, wall: float = c.WALL) -> Part:
    """One ring, revolved from a chamfered profile.

    The chamfers are cut in the 2D profile rather than on the finished solid,
    and that is not a stylistic choice: these are the part's horizontal edges,
    the house rule wants all four of them broken, and a revolve of an
    already-broken profile cannot fail the all-or-nothing way an OCC edge op on
    twenty-odd circular edges can (see the ``build123d-geometry-ops`` skill).
    """
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine():
                Polyline(
                    (r_bottom, 0.0),
                    (r_top, c.BAND_H),
                    (r_top - wall, c.BAND_H),
                    (r_bottom - wall, 0.0),
                    close=True,
                )
            make_face()
            chamfer(profile.vertices(), length=c.CHAMFER)
        revolve(axis=Axis.Z)
    return ring.part


def _band() -> Part:
    """The outer ring: an arc inside, an oversize blank outside.

    The inside is final here and is the one face that has to be right, because
    it is what the magnet pockets bottom out in -- an arc struck from the same
    centre as the seat, so the wall is ``WALL`` thick measured along a pocket's
    own axis rather than only in plan. The outside is left long and faced off by
    ``_seat_envelope`` along with everything else, which is why only the two
    inner corners are chamfered here: the outer two do not survive the trim, and
    the envelope carries their chamfer instead.
    """
    with BuildPart() as band:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine():
                Polyline(
                    (c.band_outer_radius(0.0) + TRIM_OVERSIZE, 0.0),
                    (c.band_outer_radius(c.BAND_H) + TRIM_OVERSIZE, c.BAND_H),
                    (c.band_inner_radius(c.BAND_H), c.BAND_H),
                )
                ThreePointArc(
                    (c.band_inner_radius(c.BAND_H), c.BAND_H),
                    (c.band_inner_radius(c.BAND_H / 2), c.BAND_H / 2),
                    (c.band_inner_radius(0.0), 0.0),
                )
                Polyline(
                    (c.band_inner_radius(0.0), 0.0),
                    (c.band_outer_radius(0.0) + TRIM_OVERSIZE, 0.0),
                )
            make_face()
            chamfer(profile.vertices().sort_by(Axis.X)[:2], length=c.CHAMFER)
        revolve(axis=Axis.Z)
    return band.part


def _arm() -> Part:
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
        with BuildSketch(Plane.YZ.offset(c.arm_root_radius())) as section:
            Rectangle(c.WALL, c.BAND_H, align=(Align.CENTER, Align.MIN))
            chamfer(section.vertices(), length=c.CHAMFER)
        extrude(amount=c.arm_reach() - c.arm_root_radius())
    return arm.part


def _cross() -> Part:
    """Four arms on the quarters -- a cross with its middle left out."""
    with BuildPart() as cross:
        for angle in (0.0, 90.0, 180.0, 270.0):
            add(as_part(Rotation(0.0, 0.0, angle) * _arm()))
    return cross.part


def _seat_envelope() -> Part:
    """Everything the shade is allowed to occupy: the bowl's inside, chamfered.

    A solid of revolution reaching from the axis out to the seat, so one
    intersection faces the band and docks all four arms in a single operation.
    The two outer corners carry the chamfer that the band's own profile cannot,
    since its outer face is cut away here.
    """
    with BuildPart() as envelope:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine():
                ThreePointArc(
                    (c.band_outer_radius(0.0), 0.0),
                    (c.band_outer_radius(c.BAND_H / 2), c.BAND_H / 2),
                    (c.band_outer_radius(c.BAND_H), c.BAND_H),
                )
                Polyline(
                    (c.band_outer_radius(c.BAND_H), c.BAND_H),
                    (0.0, c.BAND_H),
                    (0.0, 0.0),
                    (c.band_outer_radius(0.0), 0.0),
                )
            make_face()
            chamfer(profile.vertices().sort_by(Axis.X)[-2:], length=c.CHAMFER)
        revolve(axis=Axis.Z)
    return envelope.part


def pad_plane(angle: float) -> Plane:
    """The seating plane of one magnet: on the steel, square to it.

    Its origin is a point of the bowl's own inner sphere and its z axis is that
    sphere's radius pointing *inward*, so the pocket is bored normal to the
    surface the magnet has to grab -- and, because the band's inside face is a
    sphere about the same centre, square to that face as well. Local +y is
    forced upward (``y_dir.Z > 0``) because the teardrop's roof is built along
    it, and a roof pointing sideways would print no better than no roof at all.
    """
    direction = Vector(cos(radians(angle)), sin(radians(angle)), 0.0)
    contact = direction * c.pad_face_radius() + Vector(0, 0, c.PAD_DEPTH_Z)
    inward = (Vector(0, 0, c.sphere_centre_z()) - contact).normalized()
    tangential = Vector(0, 0, 1).cross(direction)
    plane = Plane(origin=contact, x_dir=tangential, z_dir=inward)
    if plane.y_dir.Z < 0:
        plane = Plane(origin=contact, x_dir=-tangential, z_dir=inward)
    return plane


def pad_planes() -> list[Plane]:
    step = 360.0 / c.MAGNET_COUNT
    return [pad_plane(i * step) for i in range(c.MAGNET_COUNT)]


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


def _pockets() -> Part:
    """The magnet pockets, each with a lead-in all the way round its mouth.

    Depth is exactly ``MAGNET_T``: a pocket deeper than its magnet lets the disc
    sit at an unpredictable depth, and hold falls off fast with any air behind it.
    What is left behind it is whatever the wall has left to give -- 0.6 mm, and
    the case for that number is in ``config.pad_backing``.

    The lead-in runs *inward* from the tangent plane rather than outward from it,
    which is the opposite of the obvious construction and is forced by the
    curvature. The face here is a sphere, so it lies at or below its own tangent
    plane everywhere except the single point of contact -- a chamfer cone built
    outside that plane would hang in mid-air and cut nothing, leaving the square
    mouth it was there to break.
    """
    lead = c.POCKET_LEAD_IN
    with BuildPart() as pockets:
        for plane in pad_planes():
            with BuildSketch(plane):
                add(_teardrop(c.POCKET_D / 2 + lead))
            with BuildSketch(plane.offset(lead)):
                add(_teardrop(c.POCKET_D / 2))
            loft()
            with BuildSketch(plane):
                add(_teardrop(c.POCKET_D / 2))
            extrude(amount=c.MAGNET_T)
    return pockets.part


def create_band() -> Part:
    """The outer ring on its own, seated and pocketed: the shade's whole seat.

    Shared with ``fit_test`` so the test print cannot drift from the part it is
    a test of -- it is this function's output and nothing else.
    """
    with BuildPart() as band:
        add(_band())
        add(_seat_envelope(), mode=Mode.INTERSECT)
        add(_pockets(), mode=Mode.SUBTRACT)
    return band.part


def create_shade() -> Part:
    """The shade, in print pose: widest ring on the bed, band narrowing upward."""
    with BuildPart() as shade:
        add(_band())
        for radius in c.ring_radii():
            add(_ring(radius, radius))
        add(_cross())
        add(_seat_envelope(), mode=Mode.INTERSECT)
        add(_pockets(), mode=Mode.SUBTRACT)

    part = shade.part
    part.label = "shade"
    part.color = SHADE_COLOR
    return part


def create() -> Part:
    """Entry point for ``uv run show/export/render salad_bowl_lamp.shade``."""
    return create_shade()


__all__ = [
    "SHADE_COLOR",
    "TRIM_OVERSIZE",
    "create",
    "create_band",
    "create_shade",
    "pad_plane",
    "pad_planes",
]
