"""The cradle: the shape every mount in this family grips the tube with.

Shared here rather than repeated, the same way ``profile.py`` shares the
extrusion's sketches. A cradle is an open trough that stops exactly at the
profile's rim, so the tube drops into it sideways and lifts back out -- see
``docs/design-notes.md`` S1 for why that beats a collar.

Built lying along +X with its near end on x=0, sitting on z=0 (the bed), mouth
opening +Z. Feet in this package position it; they never rebuild it.

Edge treatments follow the house rule -- fillet vertical, chamfer horizontal --
and go through ``treat_edges``: a series of isolated calls, each re-querying the
builder, because a successful edge op invalidates the previous selection and a
failed one would otherwise take every later op with it. Every selection is made
**by geometry, not off a face**: the rim carries the four insert holes, which is
precisely the case OCC will not chamfer from (see ``models/lib/edges.py``). The
selectors -- ``vertical_corners``, ``rim_edges``, ``bed_pads`` -- and
``treat_edges`` itself are public because ``feet.py`` bolts new pads onto this
body and has to treat them the same way rather than re-deriving the rules.

Two edges are left raw on purpose:

* **the insert mouths**, because a printed lead-in removes the material the
  heat-set has to melt into (the exception this family makes everywhere);
* **the trough's own footprint on the bed**, a 2.2 mm sliver where the outer
  arc is clipped 0.035 mm below its lowest point. Its "corner" is already a
  ~4 deg tangency, so there is nothing there to break and a chamfer would only
  turn a shallow edge into a knife edge. The pads standing beside it on proper
  vertical walls do get their elephant's-foot relief.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    ShapeList,
    Sketch,
    SlotOverall,
    add,
    extrude,
)

from models.lib.edges import chamfer_edge, fillet_edge

from . import config as c
from . import mount_config as m


def _big() -> float:
    return 3 * c.HEIGHT


def tube_section(clearance: float = 0.0, lift: float = 0.0) -> Sketch:
    """The tube's stadium, grown by ``clearance`` diametrally, in mount-local z.

    ``lift`` raises it, for feet that stand their cradle on a plinth -- the
    corner does, so its floor can clear the gland hanging below the tube.
    """
    with BuildSketch() as s:
        with Locations((0, m.TUBE_AXIS_Z + lift)):
            SlotOverall(c.HEIGHT + clearance, c.WIDTH + clearance, rotation=90)
    return s.sketch


def body_section(lift: float = 0.0, floor: float | None = 0.0) -> Sketch:
    """The cradle's outer profile: the bore plus a wall, cut off at the rim.

    ``floor`` flattens the back at that height, which is what gives a
    bed-facing cradle its first layer. Pass ``None`` for a cradle that is not
    lying on the bed -- the stand's is extruded vertically, and clipping it at
    zero there would slice the trough off at the tube's axis and leave two fins.
    """
    with BuildSketch() as s:
        with Locations((0, m.TUBE_AXIS_Z + lift)):
            SlotOverall(
                c.HEIGHT + m.BORE_FIT + 2 * m.CRADLE_WALL,
                c.WIDTH + m.BORE_FIT + 2 * m.CRADLE_WALL,
                rotation=90,
            )
        with Locations((0, m.CRADLE_DEPTH + lift)):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MIN), mode=Mode.SUBTRACT
            )
        if floor is not None:
            with Locations((0, floor)):
                Rectangle(
                    _big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.SUBTRACT
                )
    return s.sketch


def outer_half_width() -> float:
    """Half the cradle's overall width, at the mouth."""
    return m.CRADLE_OUTER_HALF_W


def back_z(lift: float = 0.0) -> float:
    """Height of the cradle body's outermost back face."""
    return m.TUBE_AXIS_Z + lift - (c.HEIGHT + m.BORE_FIT) / 2 - m.CRADLE_WALL


def boss_pad_section(lift: float = 0.0, base: float = 0.0) -> Sketch:
    """Cross-section of the two strap bosses, merged into the cradle walls.

    ``base`` is where the pad's underside sits. A cradle lying on the bed runs
    its pads all the way down to it; the stand's socket is vertical, so its pads
    stop at the cradle's own back face (``back_z``) instead of at zero.
    """
    top = m.CRADLE_DEPTH + lift
    with BuildSketch() as s:
        with Locations((-m.BOSS_U, top), (m.BOSS_U, top)):
            Rectangle(m.BOSS_OD, top - base, align=(Align.CENTER, Align.MAX))
    return s.sketch


def arc_radius(edge) -> float | None:
    """An edge's radius, or None if it is straight.

    ``Edge.radius`` raises on a line rather than returning None, and every
    selection below is a mix of lines and arcs.
    """
    try:
        return edge.radius
    except Exception:  # noqa: BLE001 -- "not a circle" is the answer, not an error
        return None


def is_insert_mouth(edge) -> bool:
    """The one mouth in this family that must stay raw.

    A printed lead-in removes the material the heat-set insert has to melt
    into, so ``INSERT_D`` holes are filtered out of every chamfer selection.
    """
    r = arc_radius(edge)
    return r is not None and abs(r - m.INSERT_D / 2) < 0.05


def vertical_corners(bp: BuildPart, top_z: float = m.CRADLE_DEPTH) -> ShapeList:
    """The body's own full-height vertical corners, for a fillet.

    On a bare cradle those are the four boss pads' outboard steps; a foot adds
    its bolt pads' corners to the same set, which is why this is public.

    Selected by geometry rather than off a face, because the rim they all reach
    carries the insert holes -- exactly the case where OCC refuses to work off a
    face at all. The length test is what separates a real corner of the body
    from the short verticals inside the trough's stadium, at the bore's relief
    step, and down the seam of every bore and counterbore, none of which may be
    rounded.
    """
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by(Axis.Z)
            if e.length > 0.6 * top_z and abs(e.bounding_box().max.Z - top_z) < 1e-6
        ]
    )


def rim_edges(
    bp: BuildPart,
    top_z: float = m.CRADLE_DEPTH,
    skip_radii: tuple[float, ...] = (),
) -> ShapeList:
    """Everything at the rim except the mouths that get their own lead-in.

    The rim carries the outer silhouette, the pads' outlines and both flanks of
    the trough's mouth, and all of it wants a chamfer -- the trough ones are the
    tube's lead-in as it drops in sideways. The insert mouths are the deliberate
    exception (``is_insert_mouth``); ``skip_radii`` takes the bolt-hole and
    counterbore mouths a caller has already coned as booleans, per the house
    rule that a hole mouth is a boolean and not an OCC edge op. A fillet arc
    left by ``vertical_corners`` is ``EDGE_FILLET``, well clear of either test.
    """
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by_position(Axis.Z, top_z - 0.01, top_z + 0.01)
            if not is_insert_mouth(e) and not _matches_radius(e, skip_radii)
        ]
    )


def _matches_radius(edge, radii: tuple[float, ...]) -> bool:
    r = arc_radius(edge)
    return r is not None and any(abs(r - want) < 0.05 for want in radii)


def bed_pads(bp: BuildPart) -> ShapeList:
    """Every pad standing on the bed, in a stable order.

    The trough's own bed face is excluded, and that is the deliberate raw edge
    the module docstring describes -- a 2.2 mm sliver of a clipped R17 arc that
    meets the arc at about 4 deg, so there is no corner there to break. The test
    needs no threshold: the sliver straddles the tube's centre line and no pad
    ever does.

    Sorted only so the caller's iteration order is reproducible. It is **not**
    an identity: chamfering a pad insets its outline and nudges its centroid,
    which was enough to swap two entries between passes and chamfer one pad
    twice (1.6 mm off its footprint) while its mirror went untouched -- and the
    call still returned True both times. ``treat_edges`` therefore addresses a
    pad by where it was before any of this ran, not by index.
    """
    bed = bp.faces().filter_by(Axis.Z).filter_by_position(Axis.Z, -0.01, 0.01)
    pads = [f for f in bed if f.bounding_box().min.Y > 0 or f.bounding_box().max.Y < 0]
    return ShapeList(sorted(pads, key=lambda f: (f.center().X, f.center().Y)))


def treat_edges(
    bp: BuildPart,
    top_z: float = m.CRADLE_DEPTH,
    skip_radii: tuple[float, ...] = (),
) -> list[bool]:
    """Apply the house edge rule to a cradle-shaped body under construction.

    Two isolated calls plus one per bed pad, each re-querying the builder --
    every successful edge op invalidates the previous selection, and a failure
    inside ``fillet_edge``/``chamfer_edge`` is restored rather than left to
    cascade into the ops after it. One call per pad rather than one for all of
    them because ``chamfer`` is all-or-nothing over the set it is given: a pad
    OCC will not take should cost that pad, not every pad.

    Run **once** per body, after every feature exists -- ``feet.py`` therefore
    builds its cradle with ``treat=False`` and calls this itself. Chamfering a
    rim that already carries a chamfer cuts a second wedge out of it, and on the
    trough's mouth that is 1.6 mm of the tube's seat rather than 0.8.

    Returns each call's result so a check can tell "asked for" from "applied".
    """
    took = [
        fillet_edge(bp, vertical_corners(bp, top_z), m.EDGE_FILLET),
        chamfer_edge(bp, rim_edges(bp, top_z, skip_radii), m.EDGE_CHAMFER),
    ]
    for target in [face.center() for face in bed_pads(bp)]:
        # Re-queried each pass -- the chamfer before this one rebuilt the solid
        # and every face in the previous selection went stale with it -- and
        # then matched back to where the pad was, because the index it had is
        # not stable across a chamfer. Pads are tens of mm apart and a chamfer
        # moves a centroid by hundredths, so nearest wins unambiguously.
        pad = min(bed_pads(bp), key=lambda f: (f.center() - target).length)
        took.append(chamfer_edge(bp, pad.outer_wire().edges(), m.EDGE_CHAMFER))
    return took


def create_cradle(
    length: float = m.CRADLE_LEN,
    stations: tuple[float, ...] | None = None,
    treat: bool = True,
) -> Part:
    """A trough for one tube end, near end on x=0, running +X.

    ``stations`` are the strap centres along the length, defaulting to half a
    strap in from each end -- far enough that the boss pads stay on the cradle,
    close enough that the clamp lands over the two contact bands.

    ``treat=False`` hands back the body with its edges still raw, for a caller
    that is going to weld more geometry onto it and run ``treat_edges`` once
    over the finished silhouette. ``feet.py`` is that caller; see ``treat_edges``
    for why running it twice is not the same thing.
    """
    if stations is None:
        stations = m.STRAP_STATIONS

    with BuildPart() as bp:
        with BuildSketch(Plane.YZ):
            add(body_section())
        extrude(amount=length)

        # Strap bosses, merged into the walls.
        for x in stations:
            with BuildSketch(Plane.YZ.offset(x - m.STRAP_W / 2)):
                add(boss_pad_section())
            extrude(amount=m.STRAP_W)

        # Bore, full length at the nominal fit...
        with BuildSketch(Plane.YZ):
            add(tube_section(m.BORE_FIT))
        extrude(amount=length, mode=Mode.SUBTRACT)

        # ...then relieved everywhere except the two end bands, so the middle
        # cannot bind on a 1.5 m extrusion and the joint keeps its compliance.
        relief_len = length - 2 * m.BAND_LEN
        if relief_len > 0:
            with BuildSketch(Plane.YZ.offset(m.BAND_LEN)):
                add(tube_section(m.BORE_FIT + 2 * m.BAND_RELIEF))
            extrude(amount=relief_len, mode=Mode.SUBTRACT)

        # Insert bosses. No lead-in chamfer -- deliberate exception, the
        # insert's own chamfer guides it and a printed one removes the material
        # it has to melt into.
        for x in stations:
            with Locations(
                (x, -m.BOSS_U, m.CRADLE_DEPTH),
                (x, m.BOSS_U, m.CRADLE_DEPTH),
            ):
                Cylinder(
                    m.INSERT_D / 2,
                    m.INSERT_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )

        add_drains(length)

        # House rule: fillet vertical, chamfer horizontal. See treat_edges and
        # the module docstring for what is selected and what is left raw.
        if treat:
            treat_edges(bp)

    return bp.part


def trough_floor_lift(offset: float, length: float) -> float:
    """How far the trough floor's lowest point sits below its nominal depth,
    ``offset`` in from the trough's own near end.

    Zero inside the two ``BAND_LEN`` contact bands; ``BAND_RELIEF`` through the
    relieved middle -- growing the bore's radius by that much on every side
    (see ``create_cradle``) pushes the arc's lowest point down by exactly the
    same amount. A drain's inside-mouth funnel has to know which one it is
    landing on: sized for the wrong floor it either stops short of the real
    surface (still under a band) or the taper never reaches any material at
    all (still assuming a band while actually in the relief).
    """
    relieved = m.BAND_LEN < offset < length - m.BAND_LEN
    return m.BAND_RELIEF if relieved else 0.0


def add_drains(length: float, count: int = 2) -> None:
    """Punch drains through a cradle floor.

    The trough opens upward in every print pose in this family, so outdoors it
    is a gutter. Must be called inside an open ``BuildPart``, which it cuts into
    via the ambient builder context. See ``docs/design-notes.md`` S5.
    """
    spacing = length / (count + 1)
    for i in range(1, count + 1):
        with Locations((i * spacing, 0, 0)):
            Cylinder(
                m.DRAIN_D / 2,
                m.TUBE_UNDER_Z + 1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    # Lead-in at each drain's bed-face mouth, cut as a boolean cone rather than
    # edge-chamfered -- the house rule for a bore mouth, and the same call
    # ``corner._add_drains`` makes. It also takes the elephant's foot off the
    # one part of the first layer that is a hole rather than a perimeter.
    for i in range(1, count + 1):
        with Locations((i * spacing, 0, 0)):
            Cone(
                bottom_radius=m.DRAIN_D / 2 + m.EDGE_CHAMFER,
                top_radius=m.DRAIN_D / 2,
                height=m.EDGE_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    # And a funnel at each drain's *upper* mouth, where it actually drains
    # from -- the trough's own floor, which is the bore's curved underside,
    # not a flat pad like the bed. A sharp lip there holds water on surface
    # tension no matter how clean the bed-side lead-in is. The cone is the
    # same size and shape as the bed one, mirrored (wide end at the floor,
    # narrow end EDGE_CHAMFER below it); it stays safe on a curved floor
    # because a boolean cut can only ever remove material that is actually
    # there, so it cannot cut deeper than the true surface allows, and its
    # narrow end always sits exactly at the drain's own nominal radius, so the
    # throat is broken cleanly regardless. What it *can* get wrong is where
    # its wide end lands relative to the surface -- ``trough_floor_lift`` is
    # what keeps that funnel from stopping short of a raised (banded) floor
    # while assuming the lower, relieved one.
    for i in range(1, count + 1):
        offset = i * spacing
        floor_z = m.TUBE_UNDER_Z - trough_floor_lift(offset, length)
        with Locations((offset, 0, floor_z - m.EDGE_CHAMFER)):
            Cone(
                bottom_radius=m.DRAIN_D / 2,
                top_radius=m.DRAIN_D / 2 + m.EDGE_CHAMFER,
                height=m.EDGE_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )


def strap_land_z() -> float:
    """Height of the face a strap's feet bolt down onto."""
    return m.CRADLE_DEPTH


def create() -> Part:
    """Entry point for ``uv run show led_profiles.cradle``."""
    return create_cradle()


__all__ = [
    "add_drains",
    "arc_radius",
    "bed_pads",
    "body_section",
    "boss_pad_section",
    "create",
    "create_cradle",
    "is_insert_mouth",
    "outer_half_width",
    "rim_edges",
    "strap_land_z",
    "treat_edges",
    "trough_floor_lift",
    "tube_section",
    "vertical_corners",
]
