"""The strap: the one part every mount in the family shares.

An arch that bolts down onto a cradle's two boss lands and holds the tube in.
Two per station, and it is the *only* thing in the whole family that crosses
above the rim -- so its 18 mm width is the entire optical cost of mounting a
lamp, and two screws take it off when a strip needs replacing.

**It touches nothing.** That is a correction to the original design, which had
two compliant lips gripping the aluminium flank. There is no aluminium flank to
grip: at the rim the extrusion presents only two ~0.5 mm wall edges (the channel
wall at u ~9.5-10 and the shell at u ~12.5-13), and everything above the rim is
diffuser. Pressing on either edge dents it, and pressing on the diffuser pops
it. So the strap arches clear of the whole tube by ``DIFFUSER_CLEAR`` and simply
captures it: the cradle locates the tube by shape, the strap stops it lifting
out, and the tube keeps that much vertical play. Nothing is clamped.

The feet bottom on solid boss lands with the bolt axis through the middle of
each, so the bolt is in pure compression against a stop and over-torque squashes
a pad rather than the tube: *tighten until it bottoms, plus a quarter turn*.
Neither ``FOOT_H`` nor ``BOSS_U`` is a free number: the arch's own flank is what
the bolt head has to stand clear of, so the foot is tall enough for that flank
to have curved in and the bolt far enough out to miss what is left. Both are
derived in ``mount_config``, which records what happens when they are not.
Where the play matters -- a lamp that travels, or one overhead -- a strip of
self-adhesive foam under the crown takes it up, which is a bought consumable
rather than geometry that could crush a 0.5 mm wall.

Print pose: feet on the bed, arch up. The arch's underside is the only overhang,
and -- correcting what this docstring used to claim -- it is **not** a 45 deg
one. The bore is the tube's stadium offset by ``DIFFUSER_CLEAR``, so it leaves
the bed vertical, passes 45 deg at |x| = R/sqrt(2) = 10.25, and is flat over the
crown: the middle 20.5 mm of it is a bridge, thrown across the strap's own 18 mm
width under a ``STRAP_T`` crown. That bridges without support at this width and
is why nothing here is worth supporting, but it is the number to watch if
``STRAP_W`` ever grows. Every face the edge treatments below add is at or above
45 deg, bar the bed chamfer where it runs onto the bore's lower arc and comes
out at 44.6 -- 0.8 mm tall, on the first layers, and not worth splitting a
chamfer over.

Measured off the built solid, not just this formula: the crown face is a true
cylinder, its normal is exactly straight down at the apex (0 deg from
horizontal -- genuinely flat, not merely close), and point-sampling the void
boundary at eight heights up the arc matches the predicted circle (centre
z = CROWN_Z - BORE_HALF_W, radius BORE_HALF_W) to bisection precision at every
one, including exactly at the predicted 45 deg crossing, x = 10.2530. The
bridge prints because every layer near the crown is the standard
horizontal-round-bore case: it overhangs the one below it by a small,
continuously increasing amount *in x*, converging to a point at the apex --
a mechanism that is layer-by-layer in x and does not care how long
``STRAP_W`` is, so a longer run just repeats the same x-profile more times.
``checks.check_bore_crown_bridge`` still bounds the run against the chord it
closes (``sqrt(2) * BORE_HALF_W`` ~= 20.5 mm), but as a deliberately
conservative sanity check -- not a claim that this is a flat-bridge problem
of the kind ``fdm-fits-and-clearances`` sizes at 5-10 mm, which does not
apply in that form here -- so a design change that grows ``STRAP_W`` past the
one scale this feature has been measured at has to re-justify itself rather
than pass silently. Checked in closed form and by point-sampling the solid at
the predicted crossing, so this paragraph cannot go quietly stale if
``STRAP_W`` grows or the bore geometry moves. The DFM reasoning for the
family as a whole, including why this used to be miswritten as "every face
is >= 45 deg", is recorded in ``docs/design-notes.md`` S6.

Edge treatments are five isolated calls at the end of ``create_strap``, not one,
and every one of them selects **by geometry, not off a face**: both faces they
meet -- the bed and the foot's land -- carry a bolt hole, which is precisely the
case OCC refuses to work off (see ``models/lib/edges.py``). They are the feet's
four vertical corners (filleted), both bed faces, both lands, the arch's outer
silhouette on the two end faces and its bore mouth on the same two (all
chamfered). The bolt holes keep their boolean lead-in cones, which is the
pattern any further hole in this family should reuse; the concave root where the
arch springs off the land is deliberately left raw, because a treatment there
adds material into an M4 head clearance that cost ``FOOT_H`` and ``BOSS_U`` to
win.

Strap-local z is measured from the land, i.e. ``mount_config.CRADLE_DEPTH``
below the mount's own z.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
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

# The tube's axis, seen from the land the strap bolts to. Shared with the bolt
# circle, which is derived from this arch -- see mount_config.
AXIS_Z = m.STRAP_AXIS_Z  # -1.8
INNER_CLEAR = 2 * m.DIFFUSER_CLEAR  # diametral
CROWN_Z = AXIS_Z + (c.HEIGHT + INNER_CLEAR) / 2  # 14.7 -- inner face at the top
OUTER_Z = CROWN_Z + m.STRAP_T  # 19.7 -- overall height
# Half the cleared tube across, which is also the radius of the bore's two arcs
# -- the stadium is taller than it is wide, so its caps are half its width. That
# is what the bore mouth's chamfer is selected by.
BORE_HALF_W = (c.WIDTH + INNER_CLEAR) / 2  # 14.5

# The family's printed grey, the same value corner.py, stand.py and feet.py each
# declare for their own part (CORNER_COLOR / STAND_COLOR / FOOT_COLOR). Only
# ``labelled`` below applies it: a strap on its own is shown as what comes off
# the bed, and the grey only means something standing next to the aluminium.
STRAP_COLOR = Color(0.30, 0.32, 0.36)


def _big() -> float:
    return 4 * c.HEIGHT


def _clip_below(y: float) -> None:
    """Remove everything under ``y`` from the sketch under construction."""
    with Locations((0, y)):
        Rectangle(_big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)


def arch_section() -> Sketch:
    """The strap's cross-section, in the plane across the tube."""
    with BuildSketch() as s:
        # Arch: the tube's envelope plus clearance, walled by STRAP_T.
        with Locations((0, AXIS_Z)):
            SlotOverall(
                c.HEIGHT + INNER_CLEAR + 2 * m.STRAP_T,
                c.WIDTH + INNER_CLEAR + 2 * m.STRAP_T,
                rotation=90,
            )
        # Feet, out to the bolt bosses.
        with Locations((-m.BOSS_U, 0), (m.BOSS_U, 0)):
            Rectangle(m.BOSS_OD, m.FOOT_H, align=(Align.CENTER, Align.MIN))
        _clip_below(0.0)
        # The bore is a straight clearance offset of the tube -- nothing reaches
        # in to touch it. See the module docstring for why there is no lip here.
        with Locations((0, AXIS_Z)):
            SlotOverall(
                c.HEIGHT + INNER_CLEAR,
                c.WIDTH + INNER_CLEAR,
                rotation=90,
                mode=Mode.SUBTRACT,
            )
    return s.sketch


def create_strap() -> Part:
    """One strap, in its print pose: feet on z=0, arch up."""
    with BuildPart() as bp:
        # Plane.XZ's normal is -Y, so the sketch starts at +STRAP_W/2 and the
        # extrusion runs back through zero: the strap ends up centred on its
        # own origin, which is what seated() assumes.
        with BuildSketch(Plane.XZ.offset(-m.STRAP_W / 2)):
            add(arch_section())
        extrude(amount=m.STRAP_W)

        with Locations(
            (-m.BOSS_U, 0, 0),
            (m.BOSS_U, 0, 0),
        ):
            Cylinder(
                m.BOLT_CLEAR_D / 2,
                m.FOOT_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # Lead-ins at both mouths of both bolt holes, cut as boolean cones --
        # house style, and an OCC chamfer on a thin foot is exactly the flaky case.
        for z, flip in ((0.0, Align.MIN), (m.FOOT_H, Align.MAX)):
            for u in (-m.BOSS_U, m.BOSS_U):
                with Locations((u, 0, z)):
                    Cone(
                        bottom_radius=m.BOLT_CLEAR_D / 2
                        + (m.BOLT_LEAD_IN if flip is Align.MIN else 0),
                        top_radius=m.BOLT_CLEAR_D / 2
                        + (0 if flip is Align.MIN else m.BOLT_LEAD_IN),
                        height=m.BOLT_LEAD_IN,
                        align=(Align.CENTER, Align.CENTER, flip),
                        mode=Mode.SUBTRACT,
                    )

        # Edge treatments, house rule: fillet vertical, chamfer horizontal.
        # Five isolated calls rather than one, each re-querying the builder,
        # because a successful edge op invalidates the previous selection and a
        # failed one would otherwise take every later op down with it. Every
        # selection is by geometry -- position, length, arc radius -- and never
        # off a face: both faces the treatments meet (the bed and the foot's
        # land) carry a bolt hole, which is the case OCC will not work off.
        #
        # This replaces a single `faces().sort_by(Axis.Z)[0].outer_wire()` call
        # at 0.5 mm. Both feet's bed faces are coplanar at z=0, so that
        # selection quietly chamfered *one* of them; the size is now the
        # family's own EDGE_CHAMFER, since nothing here wanted a private number.
        #
        # EDGE_FILLET is 2.5, sized for the corner's arms; the foot has only
        # 11.3 mm of exposed land across, so the radius walks down if OCC (or
        # the geometry) refuses it. It must also stay clear of the M4 head's
        # swept circle -- see _foot_corners.
        for radius in (m.EDGE_FILLET, 1.6, 1.0):
            if fillet_edge(bp, _foot_corners(bp), radius):
                break
        chamfer_edge(bp, _bed_edges(bp), m.EDGE_CHAMFER)
        chamfer_edge(bp, _land_edges(bp), m.EDGE_CHAMFER)
        chamfer_edge(bp, _end_arcs(bp, m.ARCH_HALF_W), m.EDGE_CHAMFER)
        chamfer_edge(bp, _end_arcs(bp, BORE_HALF_W), m.EDGE_CHAMFER)

    part = bp.part
    part.label = "strap"
    return part


def _arc_radius(edge) -> float | None:
    """An edge's radius, or None if it is straight.

    ``Edge.radius`` raises on a line rather than returning None, and every
    selection below is a mix of lines and arcs.
    """
    try:
        return edge.radius
    except Exception:  # noqa: BLE001 -- "not a circle" is the answer, not an error
        return None


def _is_bolt_mouth(edge) -> bool:
    """Either circle of a bolt hole's lead-in cone, at either end.

    The mouths are already broken by the boolean cones cut in ``create_strap``,
    which is the pattern any further hole in this family should reuse, so they
    are filtered out of the two face-wide chamfers that would otherwise catch
    them and cut a second lead-in into the first.
    """
    r = _arc_radius(edge)
    if r is None:
        return False
    mouth = m.BOLT_CLEAR_D / 2
    return abs(r - mouth) < 0.05 or abs(r - (mouth + m.BOLT_LEAD_IN)) < 0.05


def _foot_corners(bp: BuildPart) -> ShapeList:
    """The four outboard vertical corners of the two feet.

    The only genuinely vertical edges the part has, and the ones a hand meets
    first -- this is the part that comes off with two screws every time a strip
    is replaced. Selected by *position* (the foot's outer face, at either end
    of the strap's width) rather than by ``filter_by(Axis.Z)`` alone, because
    each bolt bore contributes a 7 mm vertical seam edge that is also Z-parallel
    and must not be filleted.

    The radius is bounded by the M4 head as well as by OCC: at ``EDGE_FILLET``
    the nearest material the cut removes is 5.46 mm from the bolt axis, so a
    3.5 mm head keeps 1.96 mm of seat. Much past 4 mm and the fillet starts
    eating the seat instead of the corner.
    """
    u = m.BOSS_U + m.BOSS_OD / 2  # the foot's outer face
    v = m.STRAP_W / 2
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by(Axis.Z)
            if abs(abs(e.center().X) - u) < 1e-3 and abs(abs(e.center().Y) - v) < 1e-3
        ]
    )


def _bed_edges(bp: BuildPart) -> ShapeList:
    """Everything on the two bed faces bar the bolt mouths.

    Both feet, deliberately: they are coplanar at z=0, so any selection that
    picks *a* bottom face picks one of them. The bore-side edge of each is in
    here too -- it is the tube's lead-in as the strap drops on, and the chamfer
    runs up over the tangent onto the bore's lower arc, which is fine because it
    only ever removes material and the strap must touch nothing.
    """
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by_position(Axis.Z, -0.01, 0.01)
            if not _is_bolt_mouth(e)
        ]
    )


def _land_edges(bp: BuildPart) -> ShapeList:
    """The foot's top face, less the bolt mouth and less the arch's root.

    Two deliberate exclusions. The mouth already has its cone. The root -- the
    concave edge at ``arch_half_width(FOOT_H)``, where the arch springs off the
    land -- is left raw, and that is a decision rather than an oversight: a
    fillet or chamfer on a *concave* edge **adds** material, and all that stands
    between this flank and the M4 head's swept circle is ``BOLT_HEAD_CLEAR``,
    0.75 mm, which is how ``BOSS_U`` was derived in the first place. The root
    opens at 113.6 deg, so a fillet reaches 0.655 R back onto the land -- a
    1 mm one would take 0.65 of the 0.75. FDM leaves a nozzle-radius fillet in
    an internal corner anyway, and the strap's load path is bolt-to-land
    compression rather than bending in this root, so the modelled fillet would
    buy little for what it spends.
    """
    flank = m.arch_half_width(m.FOOT_H)
    return ShapeList(
        [
            e
            for e in bp.edges().filter_by_position(
                Axis.Z, m.FOOT_H - 0.01, m.FOOT_H + 0.01
            )
            if not _is_bolt_mouth(e) and abs(abs(e.center().X) - flank) > 0.01
        ]
    )


def _end_arcs(bp: BuildPart, radius: float) -> ShapeList:
    """The arch's outline of the given radius, on both end faces.

    Two of them: the outer silhouette at ``ARCH_HALF_W``, which is the longest
    sharp edge on the part and the one a hand wraps round, and the bore mouth at
    half the cleared tube, which is what the tube passes on the way in. Both are
    plane curves that run from vertical at the springing to horizontal over the
    crown, so neither is a "vertical edge" or a "horizontal edge" -- they get
    the chamfer, which is the treatment that prints cleanly in both attitudes
    and, unlike a fillet, cannot add material towards the tube.
    """
    v = m.STRAP_W / 2
    return ShapeList(
        [
            e
            for e in bp.edges()
            if (r := _arc_radius(e)) is not None
            and abs(r - radius) < 0.05
            and abs(abs(e.center().Y) - v) < 1e-3
        ]
    )


def seated(x: float = 0.0) -> Part:
    """A strap moved onto a cradle, centred on ``x`` along the tube.

    Strap-local x is across the tube and y along it; the mount has those the
    other way round, so this is a quarter turn about z. The strap is symmetric
    on both axes, so the direction of the turn does not matter.
    """
    from build123d import Pos, Rotation

    from models.lib.edges import as_part

    placed = as_part(Pos(x, 0, m.CRADLE_DEPTH) * (Rotation(0, 0, 90) * create_strap()))
    placed.label = "strap"
    return placed


def labelled(placed: Part, tag: str) -> Part:
    """A strap already moved into place, labelled with ``tag`` and coloured.

    Every assembly view stacks at least one more transform on top of
    ``seated`` (onto the stand's vertical socket, out along a triangle's arm),
    and ``Location * Part`` drops both the label and the colour, so this is
    the one place that puts them back rather than repeating the two lines at
    each of the family's dozen-odd strap placements. ``tag`` says *which*
    strap -- which foot, which station, which edge -- because a scene holds up
    to twelve of them and ``checks.py`` picks parts out of a scene by label.
    """
    placed.label = f"strap ({tag})"
    placed.color = STRAP_COLOR
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.strap``."""
    return create_strap()


__all__ = ["arch_section", "create", "create_strap", "labelled", "seated"]
