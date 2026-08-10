"""Wall holder for the round Philips Sonicare charging puck, stuck to tile.

A round cup, closed in front, with the charger dropped into it face-up so the
brush stands vertically out of the top. The back carries a flat bar -- that is
the tape pad, and it is the only thing holding the holder up.

    uv run show sonicare_charger_holder
    uv run export sonicare_charger_holder   # the STL to print
    uv run check sonicare_charger_holder

**The floor is a ring, not a disc.** A big hole through the middle, and the
charger rests on a 3 mm seat around it. That is not weight saving: with a closed
floor and the holder taped to the tile there is no way to get the charger back
out again -- nothing to push against and no room to get a finger past it. The
hole turns removal into pushing a finger up through it, and drains the cup as a
side effect, which a closed floor in a shower room never did.

**Two brush-head pegs.** The bar runs past the cup on both sides and ends in a
lobe carrying a peg, which a spare head drops onto stem-down. The peg stands in
for the handle's own drive shaft and is sized by a *free* fit, not a sliding
one: it is used wet and one-handed, so it must never grip. The bar giving up
its old property -- hiding behind the cup so the holder read as a plain circle
from the front -- was the price, and it was paid deliberately.

**The cable route is one channel and two arms.** The channel is a notch through
the back wall, closed at the top so the rim stays unbroken, and *open at the
bottom into the floor hole*. That junction is the whole design: a notch closed
at both ends can only be threaded, and the free end of this cord has a mains
plug moulded onto it, so an earlier version of this model could not be assembled
at all while passing every geometric check written for it. Open at the bottom,
the cord goes in from inside the cup and the charger follows it down.

The arms run left and right across the tape face and out through both ends of
the bar, so the cord can be tucked away toward an outlet on either side. They
sit *below* the cavity floor rather than beside it, and that is why the floor is
derived rather than chosen: at this depth, at the middle of the back, an arm
level with the cup would cut through the back wall and take a bite out of the
seat, leaving the charger to rock. ``config.Holder.floor`` is
``side_w + SEAT_BACKING``, which is as thin as a 3 mm cord allows -- the cable,
not the structure, is what sets this holder's height.

**Blended, not butted.** The bar meets the cup, and the lobes meet the bar,
through fillets taken in the profile sketch. Left as drawn each is a re-entrant
notch with the ends hanging off it as cantilevers.

**Closed in front.** No cutout, no finger scallop, no drain in the front or the
sides: from the room the holder reads as a plain round cup with a toothbrush
standing in it, and the charger is invisible. Everything that is not solid faces
the tile or the floor.

**Mounting.** Double-sided foam tape (VHB-class) on the flat bar, straight onto
tile. The cord is sunk *below* that plane rather than run over it -- a cord
standing proud would hold the pad off the tile along its whole length and turn a
shear joint into a peel joint. Clean the tile with alcohol first and press for
30 s; foam tape reaches full strength after about a day.

**What it fits.** The round HX6100-family puck, nominally 47.4 mm across and
19 mm tall. Those numbers are *researched, not measured* -- see ``config.py``,
which records the provenance of each, and ``README.md`` for what to do if the
printed cup does not fit. The model is parametric for that reason, and its
slider stops describe a round charging puck rather than an arbitrary span.

**Printing.** PETG, no supports, already in print pose: floor flat on the bed,
cup mouth up, tape face standing vertical. That is also the pose it is used in,
but it is chosen for the print -- it leaves every wall vertical. The only
overhang is the notch's crown, which is radiused rather than square so it
self-supports.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Cylinder,
    Edge,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    add,
    extrude,
    fillet,
    loft,
)

from ..lib.edges import as_part, chamfer_edge, fillet_edge
from . import config
from .config import DEFAULT, HOLDER_PARAMS, PEG_H, Holder

PARAMS = HOLDER_PARAMS

# Cuts that leave the part through its back face run this far past it, so the
# cut face is never coincident with the tape plane (a coincident face is what
# leaves OCC a zero-thickness sliver to argue about).
BACK_OVERCUT = 1.0


# Fractions of the geometrically-available blend radius to try, largest first.
# The spacing between two junctions bounds the blend, but not tightly enough:
# each fillet also has to fit against the *arc* on its other side, and OCC's
# answer when it does not is to abort the sketch outright -- a hard
# StdFail_NotDone, not a silent skip. Rebuilding the sketch a rung down is the
# whole recovery, and the last rung is no blend at all, which leaves a concave
# corner rather than no part.
BLEND_LADDER = (1.0, 0.7, 0.5, 0.35, 0.0)


def _profile(h: Holder):
    """The body's outline: the cup, the bar, the two peg lobes, blended.

    Left unblended, every junction on the bar's front face is a re-entrant
    notch: the bar arrives at the cup's curve as a corner, and the lobes hang
    off the bar's ends as cantilevers over a void. They are filleted in the
    *sketch* rather than as an OCC edge op, which cannot half-apply the way this
    repo's 3D fillets can, and which carries the blend the full height of the
    part for free.

    Every junction sits on the bar's front face, so they are found by that line
    rather than by solving each intersection -- the bar meets the cup at two and
    each lobe meets the bar at one more, and all four move with the wall, the
    bar's depth and the lobe size.
    """
    front_y = h.back_y - h.plate_t
    for fraction in BLEND_LADDER:
        try:
            with BuildSketch() as sk:
                Circle(h.outer_r)
                with Locations((0, h.plate_y)):
                    RectangleRounded(h.plate_w, h.plate_t, h.plate_corner_r)
                # A lobe at each end for a brush-head peg to stand on, tangent
                # to the tape plane so it adds pad area instead of breaking it.
                with Locations((-h.peg_x, h.pad_y), (h.peg_x, h.pad_y)):
                    Circle(h.pad_r)
                corners = [v for v in sk.vertices() if abs(v.Y - front_y) < 1e-6]
                xs = sorted(v.X for v in corners)
                gap = min(
                    (b - a for a, b in zip(xs, xs[1:]) if b - a > 0.05), default=0.0
                )
                radius = min(h.plate_t, gap / 2 - 0.4) * fraction
                if len(corners) >= 2 and radius > 0.2:
                    fillet(corners, radius=radius)
            return sk.sketch, radius
        except Exception:  # noqa: BLE001,S112 -- OCC aborts the sketch; retry smaller
            continue
    raise RuntimeError("could not build the body profile at any blend radius")


def _arm_mouth_tool(h: Holder, span: float) -> Part:
    """A lofted collar that bevels the arms' top lip as the cut is made."""
    # 45 degrees, and the arithmetic has to be done at the *outer* section
    # rather than at the tape plane. Lofting from the overcut plane to the
    # nominal chamfer height silently halves the slope -- the bevel came out at
    # 20 degrees, which reads as chamfered and still leaves an edge the sharp-
    # edge audit flags, because 110 degrees of interior angle is not blunt.
    chamfer_size = h.route_chamfer
    rise = chamfer_size + BACK_OVERCUT
    with BuildPart() as tool:
        with BuildSketch(_back_plane(h.back_y + BACK_OVERCUT)):
            with Locations((0, (h.side_w + rise) / 2)):
                Rectangle(span, h.side_w + rise)
        with BuildSketch(_back_plane(h.back_y - chamfer_size)):
            with Locations((0, h.side_w / 2)):
                Rectangle(span, h.side_w)
        loft()
    return tool.part


def _peg_tips(builder: BuildPart, h: Holder):
    """The top rim of each peg -- a lead-in, so a head drops on rather than
    catching."""
    top = h.body_h + PEG_H

    def selected(edge: Edge) -> bool:
        if not _at_plane(edge, top):
            return False
        return all(
            abs(((pt.X - sx) ** 2 + (pt.Y - h.pad_y) ** 2) ** 0.5 - h.peg_d / 2) < 0.05
            for sx in (h.peg_x, -h.peg_x)
            for pt in [edge.position_at(0.5)]
        ) or any(
            all(
                abs(((pt.X - sx) ** 2 + (pt.Y - h.pad_y) ** 2) ** 0.5 - h.peg_d / 2)
                < 0.05
                for pt in (edge.position_at(t) for t in (0.0, 0.3, 0.6, 0.9))
            )
            for sx in (h.peg_x, -h.peg_x)
        )

    return builder.edges().filter_by(selected)  # ty: ignore[invalid-argument-type]


def _back_plane(y: float) -> Plane:
    """A sketch plane facing the tile, at ``y``, extruding toward it.

    ``x_dir`` is deliberately ``-X`` so that the plane's own Y axis comes out
    as world ``+Z``: sketch coordinates on this plane then read as (across,
    height above the bed), which is how every dimension in ``config`` is
    written. The X mirroring is invisible because everything drawn here is
    symmetric about the cup's axis.
    """
    return Plane(origin=(0, y, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))


def create(**params) -> Part:
    """The holder, in print pose: floor on z = 0, mouth up, tape face at +Y.

    Takes the website's sliders (see ``PARAMS``) and clamps them through
    ``Holder.of()``, so no combination reachable from the UI can build a part
    that does not print.
    """
    return build(Holder.of(**params))[0]


def build(h: Holder) -> tuple[Part, dict[str, bool]]:
    """The part, **and** whether each edge treatment actually took.

    ``create()`` throws the second half away; ``checks.py`` asserts on it. It
    exists because "no warning was printed" and "every chamfer applied" are
    different claims, and only the second one is worth having: a length ladder
    prints a warning on every failing rung even when a later rung succeeds, so
    scanning the log cannot tell a recovered failure from a real one. The
    return value can.
    """
    treatments: dict[str, bool] = {}

    with BuildPart() as builder:
        # -- body: the cup, with the tape bar across its back ---------------
        outline, blend_r = _profile(h)
        with BuildSketch():
            add(outline)
        extrude(amount=h.body_h)
        treatments["front-face blends"] = blend_r > 0.2

        # -- the bore the charger drops into --------------------------------
        with BuildSketch(Plane.XY.offset(h.floor)):
            Circle(h.cavity_r)
        extrude(amount=h.puck_height, mode=Mode.SUBTRACT)

        # -- the hole through the floor --------------------------------------
        #
        # The charger rests on a ring, not a disc. With a closed floor and the
        # holder taped to tile there is no way to get the charger back out
        # again: nothing to push against and no room to get a finger past it.
        # Opening the middle turns removal into pushing a finger up through the
        # hole. It also drains the cup, which a closed floor in a shower room
        # never did.
        with BuildSketch():
            Circle(h.opening_r)
        extrude(amount=h.floor, mode=Mode.SUBTRACT)

        # -- edge treatment, before the cable route is cut -------------------
        #
        # Order matters and is the whole reason the cable comes last. Chamfered
        # first, every face an OCC edge op has to touch is plain: the bed-side
        # face is one solid region with a single outer loop, and the rim is a
        # clean annulus. That is the case the geometry-ops skill says edge ops
        # are actually reliable on. Cut the slot and groove first and the same
        # calls would be running along a loop that has been broken open by a
        # hole -- the documented way to lose every later chamfer in the builder
        # to one silent failure.
        #
        # The cable route's own edges are then left raw on purpose: a channel
        # cut into a face meets it concavely, so there is no sharp *convex*
        # edge to break, and checks.py asserts that rather than assuming it.
        treatments["bed-side perimeter"] = _chamfer_bottom(builder, h)
        treatments["rim perimeter"] = _chamfer_rim_outer(builder, h)

        # The mouth's lead-in is a **boolean**, not an edge op, and that is not
        # a stylistic choice: OCC refused this one edge outright ("Failed
        # creating a chamfer, try a smaller length value(s)") while the two
        # calls above succeeded on the same solid. The geometry-ops skill
        # routes a round bore's lead-in to a subtracted frustum for exactly
        # this reason, and the rule it states -- do not tune a length to coax
        # an edge op, switch -- is why no smaller value was tried. A cone
        # matches the bore's own cross-section, so the bevel starts on the bore
        # wall instead of ringing the mouth with a counterbore ledge.
        with Locations((0, 0, h.body_h - h.mouth_chamfer)):
            Cone(
                bottom_radius=h.cavity_r,
                top_radius=h.cavity_r + h.mouth_chamfer,
                height=h.mouth_chamfer,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # -- the cable notch --------------------------------------------------
        #
        # Closed at the top, and open at the bottom into the floor hole. That
        # junction is the whole design: a notch closed at *both* ends can only
        # be threaded, and the free end of this cord has a mains plug moulded
        # onto it, so an earlier version of this model could not be assembled at
        # all. Open at the bottom, the cord is dropped in from inside the cup
        # and never threaded -- while from the room it still reads as a small
        # hole rather than a slot running up to the rim.
        #
        # Round-topped rather than square so the crown needs no support, and
        # ``channel_depth`` is what guarantees it actually reaches the hole.
        with BuildSketch(_back_plane(h.back_y - h.channel_depth)):
            with Locations((0, h.channel_shoulder / 2)):
                Rectangle(h.channel_w, h.channel_shoulder)
            with Locations((0, h.channel_shoulder)):
                Circle(h.channel_w / 2)
        extrude(amount=h.channel_depth + BACK_OVERCUT, mode=Mode.SUBTRACT)

        # -- the side arms ----------------------------------------------------
        #
        # One groove straight across the tape face, running off both ends of the
        # bar, so the cord can be tucked away to the left or the right depending
        # on which side the outlet is. It sits *below* the cavity floor rather
        # than beside it, which is not a detail: at this depth, at the middle of
        # the back, a groove level with the cup would cut through the back wall
        # and take a bite out of the seat the charger rests on. See
        # ``config.Holder.floor``, which is derived from this.
        span = h.plate_w + 2 * h.pad_r + 2 * BACK_OVERCUT
        with BuildSketch(_back_plane(h.back_y - h.side_depth)):
            with Locations((0, h.side_w / 2)):
                Rectangle(span, h.side_w)
        extrude(amount=h.side_depth + BACK_OVERCUT, mode=Mode.SUBTRACT)

        # The arms' mouth on the tape plane is chamfered by a **boolean**, not
        # an edge op, and that is the geometry-ops table's answer rather than a
        # workaround. The mouth runs the whole width of the bar and then out
        # through a round lobe at each end, so the edge is part straight and
        # part curved -- OCC refused it as one group, refused it split left and
        # right, and refused the lobes on their own. A lofted collar cuts the
        # bevel as part of the cut instead, follows whatever surface it emerges
        # through, and cannot fail. Only the top lip needs it: the bottom of the
        # arm is the bed face, and there is nothing below it to break.
        add(_arm_mouth_tool(h, span), mode=Mode.SUBTRACT)

        # -- break every mouth of the cable route ----------------------------
        treatments.update(_chamfer_route(builder, h))

        # -- the brush-head pegs, last, on top of their lobes ----------------
        with Locations((-h.peg_x, h.pad_y, h.body_h), (h.peg_x, h.pad_y, h.body_h)):
            Cylinder(h.peg_d / 2, PEG_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        treatments["peg tips"] = chamfer_edge(
            builder, _peg_tips(builder, h), h.route_chamfer
        )

    # Already built floor-down; re-seat on z = 0 so the assertion is a fact
    # about the returned part rather than about the builder's history.
    part = builder.part
    return as_part(Pos(0, 0, -part.bounding_box().min.Z) * part), treatments


def _at_plane(edge: Edge, z: float) -> bool:
    bb = edge.bounding_box()
    return bb.min.Z >= z - 1e-6 and bb.max.Z <= z + 1e-6


def _radii(edge: Edge):
    return [
        (pt.X**2 + pt.Y**2) ** 0.5
        for pt in (edge.position_at(t) for t in (0.0, 0.25, 0.5, 0.75, 1.0))
    ]


def _outer_at(builder: BuildPart, z: float, h: Holder):
    """Edges in the plane ``z`` belonging to the body's outer profile.

    Selected by predicate, never by index into a sort: at the rim two loops tie
    for "topmost edge", and ``sort_by(Axis.Z)[-1]`` would treat whichever OCC
    listed first and ship the other raw.

    The two circular features are identified by *their own* radii and everything
    else is the outer profile. An earlier version split them on the midpoint
    between bore and outside, which reads as equivalent and is not: wind the
    wall slider up and the tape bar's corners fall below that midpoint, so half
    the bed-side perimeter got filed under "bore mouth" and OCC was handed a
    broken loop to chamfer. It refused, silently, and 9 raw edges shipped. The
    parameter sweep in ``checks.py`` is what found it.
    """

    def selected(edge: Edge) -> bool:
        if not _at_plane(edge, z):
            return False
        radii = _radii(edge)
        if all(abs(rr - h.cavity_r) < 0.05 for rr in radii):
            return False
        return not all(abs(rr - h.opening_r) < 0.05 for rr in radii)

    return builder.edges().filter_by(selected)  # ty: ignore[invalid-argument-type]


def _mouth_at(builder: BuildPart, z: float, h: Holder):
    """The bore's own mouth: the one edge in the plane that lies at cavity_r."""

    def selected(edge: Edge) -> bool:
        return _at_plane(edge, z) and all(
            abs(rr - h.cavity_r) < 0.05 for rr in _radii(edge)
        )

    return builder.edges().filter_by(selected)  # ty: ignore[invalid-argument-type]


def _chamfer_bottom(builder: BuildPart, h: Holder) -> bool:
    """Break the bed-side edge. Elephant's-foot relief, and it earns its keep
    here beyond house style: a splayed first layer would rock the tape pad off
    the tile.
    """
    return chamfer_edge(builder, _outer_at(builder, 0.0, h), h.rim_chamfer)


def _chamfer_rim_outer(builder: BuildPart, h: Holder) -> bool:
    """Break the rim's outer loop. The mouth's own lead-in is cut separately,
    as a boolean -- see ``create``.
    """
    return chamfer_edge(builder, _outer_at(builder, h.body_h, h), h.rim_chamfer)


def _route_edges(builder: BuildPart, h: Holder, where):
    """Cable-route edges matching ``where``, selected by geometry alone.

    An edge counts as the route's only if *every* sampled point along it lies
    inside the route's footprint, which is what keeps the body's own chamfer
    loops out: the bed-side chamfer runs the whole perimeter and merely passes
    through the route's width, so a centre-point test would claim it and a
    single chamfer call would then try to treat the entire outline.
    """
    half = h.channel_w / 2 + 0.05
    front = h.back_y - h.channel_depth - 0.05

    def selected(edge: Edge) -> bool:
        pts = [edge.position_at(t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        if not all(abs(pt.X) <= half and pt.Y >= front for pt in pts):
            return False
        return where(pts, h)

    return builder.edges().filter_by(selected)  # ty: ignore[invalid-argument-type]


def _on_tape_plane(pts, h: Holder) -> bool:
    return all(pt.Y > h.back_y - 1e-6 for pt in pts)


def _on_bed(pts, _h: Holder) -> bool:
    return all(abs(pt.Z) < 1e-6 for pt in pts)


def _feature_edges(builder: BuildPart, h: Holder, where):
    """Edges matching ``where``, with no cable-route footprint pre-filter.

    ``_route_edges`` narrows to the channel's own width first, which is right
    for the channel and useless for the two features that are not in it -- the
    floor's opening, which is a 41 mm circle, and the side arms, which run the
    whole width of the bar. Those predicates carry their own bounds instead.
    """

    def selected(edge: Edge) -> bool:
        return where([edge.position_at(t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)], h)

    return builder.edges().filter_by(selected)  # ty: ignore[invalid-argument-type]


def _on_opening_bed(pts, h: Holder) -> bool:
    """The floor opening where a finger goes in, on the bed face."""
    return all(
        abs(pt.Z) < 1e-6 and abs((pt.X**2 + pt.Y**2) ** 0.5 - h.opening_r) < 0.05
        for pt in pts
    )


def _on_opening_seat(pts, h: Holder) -> bool:
    """The same hole where it breaks the seat the charger rests on."""
    return all(
        abs(pt.Z - h.floor) < 1e-6
        and abs((pt.X**2 + pt.Y**2) ** 0.5 - h.opening_r) < 0.05
        for pt in pts
    )


def _on_arms(pts, h: Holder) -> bool:
    """Anything belonging to the side arms: low, and near the tape plane.

    Both bounds are needed. Height alone would claim the body's whole bed-side
    perimeter, which also lives at z = 0; depth alone would claim the channel's
    tape-face mouth all the way up to its crown.
    """
    return all(
        pt.Z <= h.side_w + 0.05 and pt.Y >= h.back_y - h.side_depth - 0.05
        for pt in pts
    )


def _on_arm_bed(pts, h: Holder) -> bool:
    """The arms where they open on the bed face."""
    return _on_arms(pts, h) and all(abs(pt.Z) < 1e-6 for pt in pts)


def _on_arm_tape(pts, h: Holder) -> bool:
    """The arms where they open on the tape plane -- the lip tape lies over."""
    return _on_arms(pts, h) and all(abs(pt.Y - h.back_y) < 1e-6 for pt in pts)


def _on_arm_junction(pts, h: Holder) -> bool:
    """Where an arm meets the central channel: the corner the cord turns over."""
    return _on_arms(pts, h) and all(
        abs(abs(pt.X) - h.channel_w / 2) < 1e-6 for pt in pts
    )


def _on_arm_end(pts, h: Holder) -> bool:
    """Where an arm runs out through the rounded end of the bar.

    Bounded on the arm's own back face rather than through ``_on_arms``: this
    edge follows the bar's corner rounding and so climbs a little above the
    arm's ceiling, which the height bound there would reject.
    """
    return all(
        abs(pt.Y - (h.back_y - h.side_depth)) < 1e-6
        and abs(pt.X) > h.plate_w / 2 - h.plate_corner_r - 1.0
        for pt in pts
    )


def _on_lobe(pt, h: Holder) -> bool:
    return any(
        abs(((pt.X - sx) ** 2 + (pt.Y - h.pad_y) ** 2) ** 0.5 - h.pad_r) < 0.1
        for sx in (h.peg_x, -h.peg_x)
    )


def _on_arm_lobe_ceiling(pts, h: Holder) -> bool:
    """Where an arm's ceiling emerges through a peg lobe's curved wall."""
    return all(abs(pt.Z - h.side_w) < 1e-6 and _on_lobe(pt, h) for pt in pts)


def _on_channel_front(pts, h: Holder) -> bool:
    """The channel's forward face, down where it breaks into the floor hole."""
    return all(abs(pt.Y - (h.back_y - h.channel_depth)) < 1e-6 for pt in pts)


def _on_cavity_floor(pts, h: Holder) -> bool:
    """In the plane of the cup's seat -- the lip the cord comes to rest on."""
    return all(abs(pt.Z - h.floor) < 1e-6 for pt in pts)


def _on_bore_wall(pts, h: Holder) -> bool:
    """On the cavity's cylindrical face -- the slot's inner mouth.

    Radius, not position: the mouth is where two planes and a cylinder meet, so
    its edges are a pair of lines and a spline that share nothing but lying at
    ``cavity_r`` from the axis.
    """
    return all(abs((pt.X**2 + pt.Y**2) ** 0.5 - h.cavity_r) < 0.05 for pt in pts)


# The four faces the cable route breaks out through, **in the order they are
# treated, which is load-bearing**. The cavity floor's lip must go first: with
# the bore wall chamfered ahead of it, OCC refuses that one edge outright, and
# it is the edge the cord actually rests its weight on. The fix was the order,
# not a smaller length -- no smaller length was tried, per the geometry-ops
# rule that two lengths is already one too many and the answer is to change the
# problem instead. Reordering costs nothing: the four mouths are disjoint, so
# the finished part is identical whichever sequence succeeds.
#
# Named rather than inlined so ``checks.py`` can assert that every one of them
# came back True, instead of trusting the absence of a warning -- not the same
# claim, and the distinction that skill draws.
ROUTE_MOUTHS = (
    ("cavity floor", _on_cavity_floor),
    ("bore wall", _on_bore_wall),
    ("channel front", _on_channel_front),
    ("tape plane", _on_tape_plane),
    ("bed", _on_bed),
)

# The two features that are not part of the cable channel, and so are selected
# without its footprint filter. Sized separately: the bed side of the opening is
# what a finger presses into, so it gets the full house chamfer, while the seat
# side gets the smaller one because every tenth taken off there is a tenth off
# the ring the charger actually rests on.
# The arms are four passes, not one, and that is the geometry-ops rule about
# one feature per call taken literally. As a single group of twelve edges OCC
# refused the lot; split left/right it refused both halves; split by the face
# each edge lies on, every pass takes. No length was lowered to get there --
# three groupings were tried and the fourth is the one that works, which is the
# documented order of moves (change the problem, not the number).
BODY_MOUTHS = (
    ("floor opening, bed side", _on_opening_bed, lambda h: h.rim_chamfer),
    ("floor opening, seat side", _on_opening_seat, lambda h: h.route_chamfer),
    ("arm mouths, bed side", _on_arm_bed, lambda h: h.route_chamfer),
    ("arm junctions with the channel", _on_arm_junction, lambda h: h.route_chamfer),
)

# The arm ends are the exception, and they are filleted on a ladder rather than
# chamfered flat. Two reasons, and they are different from each other. House
# style rounds a *vertical* edge, and this is one. And OCC refuses this edge
# under every treatment tried at full size -- chamfer and fillet alike, in every
# ordering of the passes around it -- but ``fillet_edge``'s own contract says a
# fillet fails on *radius fit* rather than topology, and to walk the radius
# down. It does fit, at a third of the nominal. The web behind the channel is
# only ``PLATE_BACKING`` thick here, so a third of a chamfer is what there is
# room for; a fifth of a millimetre still breaks the corner the cord leaves over.
# Treatments that need the largest size that fits, rather than a fixed one.
# Each is a junction between the cable route and a curved surface, and every one
# of them OCC refuses outright at nominal while taking a smaller one -- which is
# exactly the failure mode ``fillet_edge``'s contract calls a *radius fit*
# problem and tells you to walk down. Judged by return value: each failing rung
# prints a warning even when a later one succeeds, so counting warnings would
# read every success here as a failure.
LADDER = (1.0, 2 / 3, 1 / 2, 1 / 3, 1 / 4, 1 / 6)

LADDER_MOUTHS = (
    ("arm junctions with the channel", _on_arm_junction, chamfer_edge),
    ("arm ceilings at the lobes", _on_arm_lobe_ceiling, chamfer_edge),
    # A vertical edge, so house style rounds it rather than chamfering it.
    ("arm ends", _on_arm_end, fillet_edge),
)


def _chamfer_route(builder: BuildPart, h: Holder) -> dict[str, bool]:
    """Break every mouth of the cable route -- one call per face, not one call.

    Separate calls because an OCC edge op is all-or-nothing: bundled together,
    one refusal at the bore wall (the awkward one, where a spline meets a
    cylinder) would take the three easy planar mouths down with it and leave
    every one of them raw. Each call re-queries ``builder.edges()`` because the
    preceding success invalidated the previous selection.
    """
    took = {
        name: chamfer_edge(builder, _route_edges(builder, h, where), h.route_chamfer)
        for name, where in ROUTE_MOUTHS
    }
    took.update(
        {
            name: chamfer_edge(builder, _feature_edges(builder, h, where), size(h))
            for name, where, size in BODY_MOUTHS
        }
    )
    for name, where, op in LADDER_MOUTHS:
        took[name] = _largest_that_fits(builder, h, where, op)
    return took


def _largest_that_fits(builder: BuildPart, h: Holder, where, op) -> bool:
    """Walk the ladder down until OCC accepts, and report whether it ever did.

    An empty selection counts as done, not failed. Some slider positions simply
    do not produce the junction this treats -- a lobe can swallow it, or a wall
    thickness can move it -- and "there was nothing here to break" is a
    different claim from "there was something and it was left raw". Conflating
    them would make the treatments report unfalsifiable in exactly the direction
    that matters.
    """
    if not _feature_edges(builder, h, where):
        return True
    for fraction in LADDER:
        if op(builder, _feature_edges(builder, h, where), h.route_chamfer * fraction):
            return True
    return False


__all__ = ["DEFAULT", "PARAMS", "ROUTE_MOUTHS", "Holder", "build", "config", "create"]
