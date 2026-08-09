"""Wall holder for the round Philips Sonicare charging puck, stuck to tile.

A closed round cup, wall thickness of plastic all the way round, with the
charger dropped into it face-up so the brush stands vertically out of the top.
The back of the cup carries a flat bar -- that is the tape pad, and it is the
only thing holding the holder up. The cable is the one opening: it leaves the
puck through a round-topped slot in the back wall, turns down a channel sunk
into the tape face, and drops out at the bottom edge to run down the tile.

    uv run show sonicare_charger_holder
    uv run export sonicare_charger_holder   # the STL to print
    uv run check sonicare_charger_holder

**Closed in front.** There is no cutout, no finger scallop and no drain in the
front or the sides: from the room the holder reads as a plain round cup with a
toothbrush standing in it, and the charger is invisible. Everything that is not
solid is on the back, against the tile.

**Mounting.** Double-sided foam tape (VHB-class) on the flat bar, straight onto
the tile. The bar is deliberately wider than it is tall and its rear face is a
single unbroken plane apart from the cable channel, because the failure mode of
a taped bracket is peel at one edge, not shear. The cord is sunk *below* that
plane rather than run over it -- a cord standing proud would hold the pad off
the tile along its whole length and turn the joint into a peel joint. Clean the
tile with alcohol first and press for 30 s; foam tape reaches full strength
after about a day.

**What it fits.** The round HX6100-family puck, nominally 47.4 mm across and
19 mm tall. Those numbers are *researched, not measured* -- see ``config.py``,
which records the provenance of every one of them, and ``README.md``, which
says what to do if the printed cup does not fit. The model is parametric on the
website for exactly that reason.

**Printing.** PETG, no supports, and it comes back already in print pose: floor
flat on the bed, cup mouth up, tape face standing vertical. That is the pose the
holder is used in as well, which is a coincidence worth stating -- it is chosen
because it makes the floor a solid first layer and leaves every wall vertical.
The only overhang in the part is the crown of the cable slot, which is radiused
rather than square so it self-supports.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Edge,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    extrude,
)

from ..lib.edges import as_part, chamfer_edge
from . import config
from .config import DEFAULT, FLOOR, HOLDER_PARAMS, SLOT_OVERCUT, Holder

PARAMS = HOLDER_PARAMS

# Cuts that leave the part through its back face run this far past it, so the
# cut face is never coincident with the tape plane (a coincident face is what
# leaves OCC a zero-thickness sliver to argue about).
BACK_OVERCUT = 1.0


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
        with BuildSketch():
            Circle(h.outer_r)
            with Locations((0, h.plate_y)):
                RectangleRounded(h.plate_w, h.plate_t, h.plate_corner_r)
        extrude(amount=h.body_h)

        # -- the bore the charger drops into --------------------------------
        with BuildSketch(Plane.XY.offset(FLOOR)):
            Circle(h.cavity_r)
        extrude(amount=h.puck_height, mode=Mode.SUBTRACT)

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

        # -- the cable route: slot through the wall, then down the tape face --
        with BuildSketch(_back_plane(h.cavity_r - SLOT_OVERCUT)):
            with Locations((0, FLOOR + h.slot_w / 4)):
                Rectangle(h.slot_w, h.slot_w / 2)
            with Locations((0, h.slot_shoulder)):
                Circle(h.slot_w / 2)
        extrude(
            amount=h.back_y - (h.cavity_r - SLOT_OVERCUT) + BACK_OVERCUT,
            mode=Mode.SUBTRACT,
        )

        with BuildSketch(_back_plane(h.back_y - h.groove_depth)):
            with Locations((0, h.slot_shoulder / 2)):
                Rectangle(h.groove_w, h.slot_shoulder)
        extrude(amount=h.groove_depth + BACK_OVERCUT, mode=Mode.SUBTRACT)

        # -- break every mouth of the cable route ----------------------------
        treatments.update(_chamfer_route(builder, h))

    # Already built floor-down; re-seat on z = 0 so the assertion is a fact
    # about the returned part rather than about the builder's history.
    part = builder.part
    return as_part(Pos(0, 0, -part.bounding_box().min.Z) * part), treatments


def _outer_at(builder: BuildPart, z: float, h: Holder):
    """Edges lying in the plane ``z`` that belong to the body's outer boundary.

    Selected by predicate, never by index into a sort: at the rim, two loops
    tie for "topmost edge" -- the outer profile and the cavity mouth -- and
    ``sort_by(Axis.Z)[-1]`` would treat whichever OCC happened to list first
    and ship the other one raw. The two are separated on radius instead, and
    the threshold sits midway between them so neither a fat wall nor a thin one
    can close the gap.
    """
    split = (h.cavity_r + h.outer_r) / 2

    def selected(edge: Edge) -> bool:
        bb = edge.bounding_box()
        if bb.min.Z < z - 1e-6 or bb.max.Z > z + 1e-6:
            return False
        reach = max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y))
        return reach > split

    # edges()/filter_by(predicate) is correct at runtime; see the same
    # suppression in models/door_latch.py and models/lib/checks.py.
    return builder.edges().filter_by(selected)  # ty: ignore[invalid-argument-type]


def _mouth_at(builder: BuildPart, z: float, h: Holder):
    """The cavity mouth's own edge, by the same predicate rule, inverted.

    Kept even though the lead-in is now a boolean: this is the predicate that
    proves the two rim loops are separable on radius at all, and ``checks.py``
    re-derives the same split to confirm the lead-in landed on the bore wall.
    """
    split = (h.cavity_r + h.outer_r) / 2

    def selected(edge: Edge) -> bool:
        bb = edge.bounding_box()
        if bb.min.Z < z - 1e-6 or bb.max.Z > z + 1e-6:
            return False
        reach = max(abs(bb.min.X), abs(bb.max.X), abs(bb.min.Y), abs(bb.max.Y))
        return reach <= split

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
    half = h.slot_w / 2 + 0.05
    front = h.back_y - h.groove_depth - 0.05

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


def _on_cavity_floor(pts, _h: Holder) -> bool:
    """In the plane of the cup's floor -- the lip the cord comes to rest on."""
    return all(abs(pt.Z - FLOOR) < 1e-6 for pt in pts)


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
    ("tape plane", _on_tape_plane),
    ("bed", _on_bed),
)


def _chamfer_route(builder: BuildPart, h: Holder) -> dict[str, bool]:
    """Break every mouth of the cable route -- one call per face, not one call.

    Separate calls because an OCC edge op is all-or-nothing: bundled together,
    one refusal at the bore wall (the awkward one, where a spline meets a
    cylinder) would take the three easy planar mouths down with it and leave
    every one of them raw. Each call re-queries ``builder.edges()`` because the
    preceding success invalidated the previous selection.
    """
    return {
        name: chamfer_edge(
            builder, _route_edges(builder, h, where), h.route_chamfer
        )
        for name, where in ROUTE_MOUTHS
    }


__all__ = ["DEFAULT", "PARAMS", "ROUTE_MOUTHS", "Holder", "build", "config", "create"]
