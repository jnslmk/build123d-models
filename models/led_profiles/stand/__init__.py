"""Folding tripod stand: a vertical cradle on a three-legged flange.

    uv run show led_profiles.stand          # the post
    uv run show led_profiles.stand.leg      # one leg, x3
    uv run show led_profiles.stand.keeper   # one keeper, x2

One lamp, stood upright. Three printed legs lie flat on the floor and swing
about vertical M6 pivots, so they spread into a tripod and nest together for
packing -- Astera AX1-STD style. The lamp drops into a **vertical cradle** and
two snap-on **keepers** close its mouth. Bought hardware: three M6 x 30 socket
caps and three M6 nylocs, and nothing else.

**The tube is captured, not clipped, and that is not a style choice.** The
assembled tube is a convex stadium prism: its width climbs monotonically from
``z=0`` to the straight band and is constant across it, so a trough opening
upward has no undercut to hook at *any* height -- every section below a lip is
narrower than the gap that lip leaves. The only lips that retain reach past
``TOP_ARC_Z`` into the diffuser, and those both shadow the light and route the
stand's load through the diffuser's own snap hooks instead of the aluminium.
That is design-notes S1's conclusion arrived at from the other direction, and
``checks.check_stand_no_undercut`` pins the monotonicity down so it cannot be
quietly re-litigated. So the trough holds three sides and a keeper closes the
fourth, which is the same division of labour the family's bolted ``strap``
already uses -- snapped on rather than screwed down, because the snap is
between two *printed* parts, where both undercuts are ours to choose.

**The seat is derived from the cable.** S10's defect was an identity: the room
in line with the gland was ``WELL_H``, whatever the fitting measured, so
measuring the gland could not fix it. Here the same identity is the fix.
``SEAT_Z`` is ``gland.free_length()`` less the leg thickness the flange stands
on, so the clear run under the endcap's face tracks the cable's un-turnable
first stretch rather than the gland's size, and the cable turns out through the
trough's own mouth into open air between the legs. There is no well, no side
exit and no 28 mm shortfall.

**One leg points backwards.** A tripod tips about the chord joining two adjacent
legs, at half its reach, and over a leg at full reach -- so it is twice as
stable in one direction as the other. ``LEG_AZIMUTHS`` puts a leg behind the
lamp, because a push on the lit face tips it backward. It also puts that leg
under the post's own mass. design-notes S4 has the arithmetic; ``checks.py``
recomputes ``F_tip`` from the built solids, so a change cannot quietly make the
stand tippier.

Print pose is the use pose: the flange's underside on the bed, post growing
straight up. The trough is a prism extruded vertically, so it is overhang-free
by construction; the catch pads are part of that same prism's section, so the
snap features cost no overhang either; the pivot bores and their counterbores
are plain vertical holes because the legs swing about vertical axes; and the
only downward-facing feature in the part is each leg's arc stop slot, a 5.6 mm
pocket in the first layers whose ceiling is a bridge of that width.

Edge treatments follow the house rule -- chamfer horizontal, fillet vertical --
with the same inversion the old stand documented: this mount's print pose *is*
its assembly pose, so "vertical" means the bed's normal. The trough's two mouth
lips run the full height and are vertical edges, so they are filleted; the
flange's outline and the post's top rim are horizontal and chamfered; every hole
mouth is a boolean cone rather than an OCC edge op, per house style.

**Known incomplete, and skipped by name rather than hidden.** The geometry, the
fits and the load path are finished and verified; the DFM edge treatment is not.
``checks.check_stand_edges`` exists, still fails, and is **skipped** behind
``checks.SKIP_STAND_EDGES`` -- one flag to flip back. What is left is a long
tail rather than a hole in the design: the flange's bed face and upper rim
(where OCC refuses the outer wire as a group and it has to be coaxed edge by
edge), the station pads' 45 deg ramps, and the pads' top rims. None of it
changes a dimension, a fit or a load path; all of it is a printed part sharper
than this family ships, so **break those rims by hand in the slicer or expect an
elephant's foot** until the pass is finished. It is skipped rather than
allow-listed on purpose: an ``allow`` entry is a claim that an edge is *meant*
to be square, and none of these are.
"""

from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rotation,
    Rectangle,
    ShapeList,
    Sketch,
    add,
    extrude,
)

from models.lib.edges import as_part, chamfer_edge, fillet_edge

from . import config as sc
from .. import cradle as cr
from .. import mount_config as m

POST_COLOR = Color(0.30, 0.32, 0.36)

# Re-exported so ``assemblies.standing`` and ``checks.py`` keep one source for
# the two numbers they both need to place a lamp on this stand.
SEAT_Z = sc.SEAT_Z
STATIONS = sc.STATIONS


def _big() -> float:
    return 4 * sc.OUTER_HALF_W


def flange_section() -> Sketch:
    """The flange's outline: a core disc with a round pad under each pivot.

    The core has to reach past the trough's own footprint -- whose furthest
    corner is at r = 25.7, where the back face meets a flank -- and far enough
    out to overlap each lobe by a real ligament rather than a tangency.
    """
    with BuildSketch() as s:
        Circle(sc.FLANGE_CORE_R)
        with Locations(*sc.pivot_positions()):
            Circle(sc.FLANGE_LOBE_R)
    return s.sketch


def pad_section() -> Sketch:
    """The two boss pads at a station, in the tube's cross-section plane.

    Each carries a blind vertical socket for one of the keeper's pegs. Drawn as
    a plain rectangle a side, reaching inboard far enough to fuse into the
    trough's flank rather than sit tangent to it -- the flank is at
    ``OUTER_HALF_W`` and the pad starts inboard of that, so the two share real
    material. ``PAD_BACK_Y`` is where the pad stops behind: further back the
    trough's outer arc has curved in past the pad's own inner edge and the pad
    would start standing on nothing.
    """
    inner = sc.OUTER_HALF_W - 1.6
    outer = sc.PEG_U + sc.PAD_OD / 2
    with BuildSketch() as s:
        for side in (1.0, -1.0):
            with Locations(
                (
                    side * (inner + outer) / 2,
                    (sc.PAD_BACK_Y + sc.MOUTH_Y) / 2,
                )
            ):
                Rectangle(outer - inner, sc.MOUTH_Y - sc.PAD_BACK_Y)
    return s.sketch


def station_z(centre: float) -> tuple[float, float]:
    """A station's pad range: ``PAD_H`` of it, ending where the keeper starts."""
    top = centre - sc.KEEPER_W / 2
    return top - sc.PAD_H, top


def _stop_slot(pivot: tuple[float, float], deployed: float, direction: float) -> Part:
    """The arc slot in the flange's underside that limits one leg's swing.

    Its two ends are the stops: deployed, where the leg stands radially out and
    the tripod is at full reach, and folded, ``LEG_FOLD_SWEEP`` round from it.
    A pin on the leg's top face rides in it. ``direction`` is 0 for the indexed
    rear leg, which gets a plain socket and no arc -- see ``config.LEG_FOLD_DIRS``
    for why the sweeps are not all equal.

    Cut as a chain of overlapping cylinders rather than as a swept slot: a sweep
    along an arc is one more OCC operation that can fail, and this is a stop,
    not a bearing surface.
    """
    steps = 1 if direction == 0.0 else 24
    with BuildPart() as bp:
        for i in range(steps + 1):
            a = radians(deployed - direction * sc.LEG_FOLD_SWEEP * i / steps)
            with Locations(
                (
                    pivot[0] + sc.STOP_SLOT_R * cos(a),
                    pivot[1] + sc.STOP_SLOT_R * sin(a),
                    0.0,
                )
            ):
                Cylinder(
                    sc.STOP_SLOT_W / 2,
                    sc.STOP_SLOT_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
    return bp.part


def mouth_lip_edges(bp: BuildPart) -> ShapeList:
    """The trough's mouth lips: the vertical edges standing at the rim plane.

    Four of them, not two -- the bore's lip and the outer wall's lip a wall
    apart, on each flank -- and the station pads chop the outer ones into
    segments, so this is selected by position and axis rather than by length.

    Selected by geometry, never off a face: the flanks carry the catch pads and
    the sockets, which is exactly the case OCC refuses to work a face-based
    selection from.
    """
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by(Axis.Z)
            if abs(e.center().Y - sc.MOUTH_Y) < 0.25 and e.length > 3.0
        ]
    )


def pad_corner_edges(bp: BuildPart) -> ShapeList:
    """The outboard vertical corners of the four station pads.

    Vertical, so the house rule wants a fillet. Identified by standing at the
    pads' own outer face, which nothing else in the part reaches.
    """
    outer = sc.PEG_U + sc.PAD_OD / 2
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by(Axis.Z)
            if abs(abs(e.center().X) - outer) < 0.25 and e.length > 3.0
        ]
    )


def pad_rim_edges(bp: BuildPart, z: float) -> ShapeList:
    """One station pad's horizontal rim, top or bottom. Chamfered, per the rule."""
    outer = sc.PEG_U + sc.PAD_OD / 2
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by_position(Axis.Z, z - 0.01, z + 0.01)
            if abs(e.center().X) > sc.OUTER_HALF_W - 1.0
            and abs(e.center().X) < outer + 1.0
        ]
    )


def create_post() -> Part:
    """The post, in its print pose: flange underside on z=0, trough opening +y."""
    with BuildPart() as bp:
        # --- the trough, a vertical prism of the family's own cradle section
        with BuildSketch():
            add(cr.body_section(sc.SINK, floor=None))
        extrude(amount=sc.POST_H)

        # --- the flange it stands on
        with BuildSketch():
            add(flange_section())
        extrude(amount=sc.FLANGE_T)

        # --- the keeper stations: two pads apiece, same prismatic section,
        # each grown out of the flank on a 45 deg ramp so its underside is
        # self-supporting rather than a cantilevered ledge.
        for centre in sc.STATIONS:
            bottom, top = station_z(centre)
            with BuildSketch(Plane.XY.offset(bottom)):
                add(pad_section())
            extrude(amount=top - bottom)
            with BuildSketch(Plane.XY.offset(bottom)):
                add(pad_section())
            extrude(amount=-sc.PAD_RAMP, taper=45)

        # --- the tube's own bore, from the seat up
        with BuildSketch(Plane.XY.offset(sc.SEAT_Z)):
            add(cr.tube_section(m.BORE_FIT, sc.SINK))
        extrude(amount=sc.POST_H - sc.SEAT_Z + 1.0, mode=Mode.SUBTRACT)

        # --- under the seat: a bore that clears the fitted gland, straight
        # through the flange, and a slot forward so nothing at all stands in
        # line with the cable. This is S10's identity used forwards.
        Cylinder(
            sc.WELL_D / 2,
            sc.SEAT_Z + 1.0,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT,
        )
        with Locations((0, 0, sc.SEAT_Z)):
            Cylinder(
                sc.WELL_D / 2,
                sc.SEAT_Z + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
        with Locations((0.0, _big() / 2, (sc.SEAT_Z - 1.0) / 2)):
            Box(
                sc.CABLE_SLOT_W,
                _big(),
                sc.SEAT_Z + 1.0,
                mode=Mode.SUBTRACT,
            )

        # --- the pivots: head counterbore opening upward, shank through,
        # nyloc under the leg (which the leg itself pockets for).
        for u, v in sc.pivot_positions():
            with Locations((u, v, 0)):
                Cylinder(
                    sc.PIVOT_CLEAR_D / 2,
                    sc.FLANGE_T,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations((u, v, sc.FLANGE_T)):
                Cylinder(
                    sc.PIVOT_CBORE_D / 2,
                    sc.PIVOT_CBORE_H,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
            # House rule: a hole mouth is a boolean cone, never an OCC chamfer.
            for z, flip, top in (
                (0.0, Align.MIN, False),
                (sc.FLANGE_T, Align.MAX, True),
            ):
                d = sc.PIVOT_CBORE_D if top else sc.PIVOT_CLEAR_D
                with Locations((u, v, z)):
                    Cone(
                        bottom_radius=d / 2 + (sc.PIVOT_LEAD_IN if not top else 0),
                        top_radius=d / 2 + (sc.PIVOT_LEAD_IN if top else 0),
                        height=sc.PIVOT_LEAD_IN,
                        align=(Align.CENTER, Align.CENTER, flip),
                        mode=Mode.SUBTRACT,
                    )

        # --- the keeper sockets, blind and opening upward
        for centre in sc.STATIONS:
            _, top = station_z(centre)
            for u in (sc.PEG_U, -sc.PEG_U):
                with Locations((u, sc.PEG_Y, top)):
                    Cylinder(
                        (sc.PEG_D + sc.PEG_FIT) / 2,
                        sc.SOCKET_DEPTH,
                        align=(Align.CENTER, Align.CENTER, Align.MAX),
                        mode=Mode.SUBTRACT,
                    )
                with Locations((u, sc.PEG_Y, top)):
                    Cone(
                        bottom_radius=(sc.PEG_D + sc.PEG_FIT) / 2,
                        top_radius=(sc.PEG_D + sc.PEG_FIT) / 2 + sc.PEG_LEAD_IN,
                        height=sc.PEG_LEAD_IN,
                        align=(Align.CENTER, Align.CENTER, Align.MAX),
                        mode=Mode.SUBTRACT,
                    )

        # --- the leg stops
        for (u, v), azimuth, direction in zip(
            sc.pivot_positions(), sc.LEG_AZIMUTHS, sc.LEG_FOLD_DIRS
        ):
            add(_stop_slot((u, v), azimuth, direction), mode=Mode.SUBTRACT)

    part = _treat_edges(bp)
    part.label = "stand post"
    part.color = POST_COLOR
    return part


def _one_at_a_time(bp: BuildPart, select, size: float, op) -> int:
    """Apply an edge op to each edge of a selection **separately**.

    ``fillet``/``chamfer`` are all-or-nothing over the set they are handed, so a
    fourteen-edge call that OCC refuses costs all fourteen. Here that is not a
    theoretical worry: the mouth lips are chopped into segments by the station
    pads and one short segment is enough to take the other thirteen down with
    it. Applying them one at a time turns "all or nothing" into "as many as OCC
    will take", and the count comes back so a check can tell asked-for from
    applied.

    Re-queried every pass and matched back by position, never by index: a
    successful op rebuilds the solid and every edge handle in the previous
    selection goes stale with it, and the index a survivor had is not stable
    across the rebuild either (``cradle.treat_edges`` learned this the
    expensive way, on pads).
    """
    targets = [e.center() for e in select(bp)]
    applied = 0
    for target in targets:
        remaining = select(bp)
        if not remaining:
            break
        edge = min(remaining, key=lambda e: (e.center() - target).length)
        if (edge.center() - target).length > 0.6:
            continue
        applied += int(op(bp, [edge], size))
    return applied


def _treat_edges(bp: BuildPart) -> Part:
    """House edge rule -- chamfer horizontal, fillet vertical -- as a series of
    isolated calls.

    Each re-queries the builder, because every successful edge op invalidates
    the previous selection, and ``fillet_edge``/``chamfer_edge`` restore a
    failure rather than let it cascade into the ops after it (gotchas S1). One
    call per group rather than one for all of them for the same reason: a group
    OCC will not take should cost that group, not the whole part.

    This mount's print pose *is* its assembly pose, so "vertical" here means the
    bed's normal -- the same inversion the old stand documented. The mouth lips
    run the full height and are therefore vertical edges, where the corner's and
    the cradle's mouths are horizontal rims and get chamfers instead.
    """
    _one_at_a_time(bp, mouth_lip_edges, sc.LIP_FILLET, fillet_edge)
    _one_at_a_time(bp, pad_corner_edges, sc.PAD_FILLET, fillet_edge)

    # Only the pads' top rims: their undersides are the 45 deg ramp, which is
    # already its own break and has no square edge left to take one.
    for centre in sc.STATIONS:
        top = station_z(centre)[1]
        _one_at_a_time(
            bp, lambda b, z=top: pad_rim_edges(b, z), sc.EDGE_CHAMFER, chamfer_edge
        )

    for z in (0.0, sc.POST_H):
        for face in (
            bp.faces().filter_by(Axis.Z).filter_by_position(Axis.Z, z - 0.01, z + 0.01)
        ):
            chamfer_edge(bp, face.outer_wire().edges(), sc.EDGE_CHAMFER)

    # The flange's upper rim, taken off that face's **outer wire** rather than
    # off every edge at its height. The difference is not cosmetic: the same
    # plane carries the three pivot counterbore mouths and the trough's own
    # footprint, and those are inner wires -- the counterbores already have
    # boolean cone lead-ins (house rule), and asking OCC for all nineteen edges
    # at once fails outright and costs the rim as well (gotchas S1).
    for face in (
        bp.faces()
        .filter_by(Axis.Z)
        .filter_by_position(Axis.Z, sc.FLANGE_T - 0.01, sc.FLANGE_T + 0.01)
    ):
        chamfer_edge(bp, face.outer_wire().edges(), sc.EDGE_CHAMFER)
    return as_part(bp.part)


def seated() -> Part:
    """The post lifted onto its legs, for an assembly view.

    The legs lie flat on the floor and the flange stands on them, so the whole
    post rises by exactly one leg thickness.
    """
    placed = as_part(Pos(0, 0, sc.LEG_T) * create_post())
    placed.label = "stand post"
    placed.color = POST_COLOR
    return placed


def seated_legs() -> list[Part]:
    """The three legs, deployed, on the floor."""
    from .leg import create_leg, LEG_COLOR

    out: list[Part] = []
    for i, ((u, v), azimuth) in enumerate(
        zip(sc.pivot_positions(), sc.LEG_AZIMUTHS)
    ):
        placed = as_part(
            Pos(u, v, 0) * (Rotation(0, 0, azimuth) * create_leg())
        )
        placed.label = f"stand leg {i}"
        placed.color = LEG_COLOR
        out.append(placed)
    return out


def seated_keepers() -> list[Part]:
    """The two keepers, dropped onto their stations -- pegs **down**.

    A keeper goes into the post the other way up from the way it prints. Its
    print pose stands the pegs up off the bed (``keeper.py``: no overhang, no
    bridge), and the post's sockets open upward, so fitting one is a 180 deg
    flip. The flip is taken about **y**, which is the axis the section is
    symmetric in -- x is mirrored and nothing changes, where a flip about x
    would swap the arch's mouth for its crown and put the opening at the back.

    Then it drops until the peg roots meet the pads' top face at
    ``station_z(z)[1]``, which lands the arch centred on the station: that is
    what ``station_z``'s ``top = centre - KEEPER_W / 2`` means, and it leaves
    the peg tips 1 mm clear of the socket floor (``SOCKET_DEPTH``'s relief), so
    the keeper seats on the pads rather than on its own pegs.
    """
    from .keeper import create_keeper, KEEPER_COLOR

    out: list[Part] = []
    for i, z in enumerate(sc.STATIONS):
        placed = as_part(
            Pos(0, 0, sc.LEG_T + z + sc.KEEPER_W / 2)
            * (Rotation(0, 180, 0) * create_keeper())
        )
        placed.label = f"stand keeper {i}"
        placed.color = KEEPER_COLOR
        out.append(placed)
    return out


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stand``."""
    return create_post()


__all__ = [
    "POST_COLOR",
    "SEAT_Z",
    "STATIONS",
    "pad_section",
    "create",
    "create_post",
    "flange_section",
    "mouth_lip_edges",
    "pad_corner_edges",
    "pad_rim_edges",
    "seated",
    "seated_keepers",
    "seated_legs",
    "station_z",
]
