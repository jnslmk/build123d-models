"""Small feet: the same cradle, different backs.

``create_eye_foot()``  -- two Ø6.6 holes for bought M6 eye bolts, for wire
                          suspension. **Through-bolts, not heat-set inserts**:
                          an insert pulls out under a shock load and a
                          through-bolt with a penny washer and a nyloc cannot.
``create_wall_foot()`` -- two Ø5.5 holes for M5 screws into a wall or ceiling.

Both carry two holes rather than one, deliberately. A single hang point offset
to one side twists the tube about its own axis and turns the beam; a symmetric
pair holds it square. Either take one wire each side in a V, or bolt through
both.

The pads sit outboard of ``13.5`` mm, which is clear of the bore at every
height, so a vertical hole through them can never break into the tube's space.

Print pose, both: back on the bed, cradle opening up. Same as everything else
in the family.

Edges follow the house rule through ``cradle.treat_edges``, which is why the
cradle underneath is built with ``treat=False``: a foot's pads change the
silhouette the rim chamfer has to follow, and chamfering a rim twice cuts two
wedges out of it rather than one. So the body is welded up first and treated
once, at the end, over everything. The bolt holes are the exception the house
rule already makes for a bore mouth -- boolean ``Cone`` lead-ins, as
``strap.create_strap`` cuts for the same clearance holes, never an OCC chamfer
off a bed face that also carries every pad's outer wire.

Two edges are left raw here, both on purpose. The insert mouths, as everywhere
in this family (``cradle.is_insert_mouth``). And the **counterbore mouths**: an
0.8 lead-in there would eat half of ``PAD_WALL``, which is the only thing
between an M6 nyloc and open air on a foot rated for 20 kg of shock, and the
nut is dropped in by hand from the open side rather than found blind.
"""

from __future__ import annotations

from build123d import (
    Align,
    Box,
    BuildPart,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Pos,
    add,
)

from models.lib.edges import as_part

from . import cradle as cr
from . import mount_config as m

PAD_U_IN = 13.5  # clear of the bore, whose widest half is 13.04
PAD_LEN = 22.0
HOLE_U = 20.0

EYE_HOLE_D = 6.6  # M6 eye bolt
EYE_CBORE_D = 12.0  # nyloc + washer, reached from the open side
WALL_HOLE_D = 5.5  # M5 into the wall
WALL_CBORE_D = 10.0

# NOT A FREE NUMBER, and it used to be the wrong one. The pocket's outboard
# wall is whatever is left of the pad once the counterbore is sunk into it, so
# this is derived from the deeper of the two counterbores rather than typed.
#
# It was 26.0 -- and ``HOLE_U + EYE_CBORE_D / 2`` is 26.0 *exactly*, so the eye
# foot's nyloc pocket was tangent to its own pad face with zero wall between
# them: a slit down the side of the pocket, on the one part in this family
# designed for 20 kg of shock. It is also what stopped OCC chamfering the pad's
# rim at all, since a tangent-continuous outline poisons the whole wire.
#
# The same smell as ``mount_config.BOSS_U``, which was ``ARCH_HALF_W`` exactly:
# **a typed constant that happens to equal a derived dimension is the bug, not
# a coincidence.** Twice in one package is a pattern worth naming.
PAD_WALL = 1.6  # four perimeters at 0.4 mm
PAD_U_OUT = HOLE_U + max(EYE_CBORE_D, WALL_CBORE_D) / 2 + PAD_WALL  # 27.6

CBORE_DEPTH = m.CRADLE_DEPTH * 0.45  # 9.36, leaving 11.44 of through-bolt land

FOOT_COLOR = Color(0.30, 0.32, 0.36)


def _create_foot(hole_d: float, cbore_d: float, label: str) -> Part:
    """A cradle with two bolt pads on its flanks."""
    base = cr.create_cradle(treat=False)
    mid = m.CRADLE_LEN / 2

    with BuildPart() as bp:
        add(base)
        pad_w = PAD_U_OUT - PAD_U_IN
        for side in (-1, 1):
            with Locations((mid, side * (PAD_U_IN + pad_w / 2), 0)):
                Box(
                    PAD_LEN,
                    pad_w,
                    m.CRADLE_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        for side in (-1, 1):
            with Locations((mid, side * HOLE_U, 0)):
                Cylinder(
                    hole_d / 2,
                    m.CRADLE_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        # House rule, over the finished silhouette -- and deliberately *before*
        # the counterbores are sunk. That ordering was originally forced: the
        # eye foot's Ø12 pocket used to be exactly tangent to its pad's outboard
        # face, and OCC's chamfer builder answers "only 2 faces" at a tangency --
        # not just for the edge it touches but for the whole tangent-continuous
        # pad outline, arcs and flanks alike, at every length down to 0.24.
        # ``PAD_WALL`` has since put a real wall there, so the tangency is gone
        # and this order is now a choice rather than a rescue. It is kept
        # because a boolean cut afterwards cannot fail the way an edge op can,
        # which is the house doctrine. The bolt holes are skipped here because a
        # bore mouth takes a boolean cone, below.
        cr.treat_edges(bp, skip_radii=(hole_d / 2,))

        for side in (-1, 1):
            # Counterbore from the open side, so the nut is reachable with the
            # tube out and the bolt head lands on the back face against the wall.
            with Locations((mid, side * HOLE_U, m.CRADLE_DEPTH)):
                Cylinder(
                    cbore_d / 2,
                    CBORE_DEPTH,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                    mode=Mode.SUBTRACT,
                )
            # Lead-in at both ends of the clearance hole, cut as boolean cones:
            # the bed mouth (where the head seats against the wall, and where a
            # first-layer hole would otherwise carry an elephant's foot) and the
            # counterbore floor (where the bolt has to find the hole blind, from
            # inside the pocket). Same instrument and same size as the strap's.
            #
            # The two mouths open opposite ways, so each cone has to widen the
            # way its own mouth faces: down at the bed, up into the pocket. The
            # floor one used to sit *above* the floor, wide end up -- entirely
            # inside the counterbore's own void, where a boolean subtract has
            # nothing to remove. The pocket floor therefore kept a square 90 deg
            # shoulder right round the hole (the raw-edge audit's "counterbore
            # floor step"), and the check meant to catch that sampled a point in
            # the same empty pocket, so it passed either way. It does not now.
            #
            # Neither cone widens to the full counterbore: the flat left between
            # it and the counterbore wall is what an M5/M6 nyloc and its washer
            # bear on, and a bolt rated for 20 kg of shock wants that seat flat.
            for z, up in ((0.0, False), (m.CRADLE_DEPTH - CBORE_DEPTH, True)):
                base = z - m.BOLT_LEAD_IN if up else z
                with Locations((mid, side * HOLE_U, base)):
                    Cone(
                        bottom_radius=hole_d / 2 + (0.0 if up else m.BOLT_LEAD_IN),
                        top_radius=hole_d / 2 + (m.BOLT_LEAD_IN if up else 0.0),
                        height=m.BOLT_LEAD_IN,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )

    part = bp.part
    part.color = FOOT_COLOR
    part.label = label
    return part


def create_eye_foot() -> Part:
    """Suspension foot: two M6 through-holes for bought eye bolts."""
    return _create_foot(EYE_HOLE_D, EYE_CBORE_D, "eye foot")


def create_wall_foot() -> Part:
    """Wall or ceiling foot: two M5 clearance holes."""
    return _create_foot(WALL_HOLE_D, WALL_CBORE_D, "wall foot")


def seated(x: float = 0.0, foot: Part | None = None) -> Part:
    """A foot moved onto a tube running along +X, near end of its cradle at ``x``.

    House rule: the foot is authored in its print pose (back on the bed,
    cradle opening +Z, near end on its own x=0); the assembly is what moves
    it. Mount-local z is measured from the bed and the tube's underside sits
    ``mount_config.TUBE_UNDER_Z`` above that -- the same convention
    ``checks.py::_mount_pose`` uses -- so dropping onto the tube is a plain
    z-shift; the cradle already runs along +X, so nothing has to turn.
    Defaults to the eye foot, the one used for the common case (suspension).
    """
    if foot is None:
        foot = create_eye_foot()
    placed = as_part(Pos(x, 0, -m.TUBE_UNDER_Z) * foot)
    placed.color = foot.color
    placed.label = foot.label
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.feet``."""
    return create_eye_foot()


__all__ = ["create", "create_eye_foot", "create_wall_foot", "seated"]
