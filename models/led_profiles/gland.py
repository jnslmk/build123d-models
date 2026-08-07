"""Cable gland and cable stub: bought hardware, MOCKED for assembly views.

**Nothing here is printed.** The endcap carries a printed M12 x 1.5 *female*
thread (``endcap.GLAND_MAJOR_D``); the gland itself is a bought nylon fitting
screwed into it, and this module is a stand-in for one so an assembly view can
show the volume it occupies. It must never appear in
``assembly.printed_parts()``.

The reason it exists is that ``mount_config.GLAND_ENV_D`` and ``GLAND_PROUD``
-- both load-bearing -- were until now only ever *consumed*, by
``corner.gland_setback`` and by ``stand.WELL_D`` / ``WELL_H``. Every mount
reserved a hole for a gland nobody had drawn, so no view could show whether the
thing actually clears what is around it. Drawing it turns those two numbers
into geometry a scene can be looked at -- and drawing it is what got them
measured, which took the envelope from an assumed 24 to 18.71 and the
protrusion from an assumed 30 to 18.8.

Every dimension below now comes from ``mount_config``'s measured block. Only
two things here are still assumed, and both are marked: ``THREAD_L``, the male
thread's own length, and the reading that the nut's round-over is a quarter
circle whose radius is its own length.

Local frame: the gland's axis is +Z and **z = 0 is the endcap's outer face**,
which is the datum both consumers already measure from. So the stem runs down
into the cap (negative z, buried in the printed thread), and everything from
z = 0 to z = ``m.GLAND_PROUD`` is the part standing out in the open:

* the **body hex**, ``GLAND_BODY_AF`` across flats -- the spanner flats, and
  the wider of the two, so it is what sets ``GLAND_ENV_D``;
* the **compression nut**, ``GLAND_NUT_AF`` across flats, in two parts --
  ``GLAND_NUT_HEX_H`` of hex and then ``GLAND_NUT_ROUND_H`` of round-over.

The round-over is a **fillet, not a taper**: a quarter circle tangent to the
nut's flats at the bottom and to the horizontal at the top, so its radius is
the round's own length and the tip lands at ``NOSE_TIP_D``. A cone was the
first shape here and is the wrong one; the real nut's end is round.

The cable stub
--------------

``CABLE_STUB`` of cable leaves the nose along the same axis. It is not decor:
``m.CABLE_BEND_R`` is 26.8 mm (4 x OD, fixed installation), so a cable leaving
this gland cannot have turned anywhere meaningful within the first ~27 mm of
its run. Modelling that as a straight stub of about a bend radius is the
conservative reading of it -- a real cable starts curving at the nose, but at
R26.8 the first 30 mm of centreline departs from the axis by only ~17 mm, and
in the direction the installer chooses, not one the model can know. What the
stub asserts is the honest part: **this much space in front of the cap has to
be free before the cable can be considered turned.** Deducting it from a mount
is what a fit check is for.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Color,
    Cylinder,
    Line,
    Locations,
    Part,
    Plane,
    Pos,
    RegularPolygon,
    Rotation,
    add,
    extrude,
    make_face,
    revolve,
)

from models.lib.edges import as_part

from . import config as c
from . import mount_config as m
from .endcap import CAP_T, GLAND_THREAD_D

# ------------------------------------------------------------------ the stem

# The bought gland's own male thread. A stock M12 gland carries ~8 mm of it,
# which is what sets ``endcap.CAP_T``: the flange is exactly this thick, so the
# thread engages over its whole length and the gland's flange seals on the cap's
# face. A thicker cap would be bore the gland cannot reach and screw length the
# two cap screws could not spend in the aluminium.
THREAD_D = GLAND_THREAD_D  # 12.0
THREAD_L = 8.0

# ------------------------------------------------------------ what stands out

# All measured -- see ``mount_config``'s gland block. Aliased rather than
# re-typed so there is exactly one place a caliper reading lands.
BODY_AF = m.GLAND_BODY_AF  # 16.2 across flats; 18.71 across corners = the envelope
BODY_H = m.GLAND_BODY_H  # 4.4
NUT_AF = m.GLAND_NUT_AF  # 16.1
NUT_HEX_H = m.GLAND_NUT_HEX_H  # 10.0
NOSE_H = m.GLAND_NUT_ROUND_H  # 4.4, the nut's rounded end

# The round-over, read as a quarter circle: tangent to the nut's flat at the
# bottom, tangent to horizontal at the top, so its radius is its own length and
# the tip is the nut's half-flat less that radius. That lands at 7.30 mm
# against a 6.70 mm cable -- the seal closed down onto it, which is what the
# shape is for. ASSUMED only in the sense that a caliper measured the length
# and not the radius; any other radius would leave the round non-tangent at one
# end or the other, which is not what a moulded nut looks like.
NOSE_R = NOSE_H
NOSE_TIP_D = NUT_AF - 2 * NOSE_R  # 7.30

# ------------------------------------------------------------------ the cable

# ~= m.CABLE_BEND_R (26.8), rounded up to a round number. See the module
# docstring for why a straight stub of about a bend radius is the right mock.
CABLE_STUB = 30.0

GLAND_COLOR = Color(0.10, 0.10, 0.12)  # black nylon
CABLE_COLOR = Color(0.22, 0.22, 0.25)  # black sheath, lifted so it reads apart


def free_length() -> float:
    """Clear space needed in front of an endcap's outer face, along its axis.

    The gland's reach plus the cable's un-turnable first run. A mount that
    leaves less than this in line with the gland does not fit the cable, however
    well it clears the gland itself.
    """
    return m.GLAND_PROUD + CABLE_STUB


def create_gland() -> Part:
    """One fitted gland, axis on +Z, the cap's outer face on z = 0.

    Two hex prisms, a revolved round-over and the buried stem, in one builder.
    Both hexes are drawn on ``major_radius=False`` so the measured *flats* go in
    directly and the across-corners envelope falls out of the geometry rather
    than being converted by hand at the call site.

    The round-over is revolved rather than filleted. An OCC fillet whose radius
    equals the whole height of the face it is cutting back is the all-or-nothing
    edge op at its least reliable (gotchas S1), and there is nothing to gain by
    asking: the arc is known exactly, so it can be drawn.
    """
    with BuildPart() as bp:
        # The stem, buried in the cap's printed thread. Drawn even though it is
        # never visible from outside, so a scene can be asked whether the
        # engagement is really there rather than assumed.
        Cylinder(
            THREAD_D / 2,
            THREAD_L,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )

        with BuildSketch():
            RegularPolygon(BODY_AF / 2, 6, major_radius=False)
        extrude(amount=BODY_H)

        # Clocked 30 deg off the body, the way a nut tightened onto a held hex
        # ends up: it makes the two read as separate pieces in a shaded view.
        with BuildSketch(Plane.XY.offset(BODY_H)):
            RegularPolygon(NUT_AF / 2, 6, rotation=30, major_radius=False)
        extrude(amount=NUT_HEX_H)

        add(_nut_round_over())

    part = bp.part
    part.color = GLAND_COLOR
    part.label = "cable gland (bought, mock)"
    return part


def _nut_round_over() -> Part:
    """The nut's rounded end: a quarter arc revolved about the gland's axis.

    Drawn on ``Plane.XZ`` -- sketch-local (u, v) is global (x, 0, z), so the
    sketch's own y *is* the height above the cap's face and every constant goes
    in unconverted. The profile is a rectangle with its outer-top corner
    replaced by the arc, closed back to the axis so ``revolve`` gets a face that
    touches the axis instead of straddling it.

    Its outer radius is the nut's *inradius* (half the flats), not half the
    across-corners circle: a round-over on a hex nut is turned, so it meets the
    flats tangentially and cuts the corners off short. That is why the tip lands
    on ``NOSE_TIP_D`` rather than on anything derived from the envelope.
    """
    r0 = NUT_AF / 2  # 8.05 -- where the flats are
    z0 = BODY_H + NUT_HEX_H  # 14.4 -- the hex stops here
    r1 = r0 - NOSE_R  # 3.65 -- the flat left at the tip

    with BuildPart() as bp:
        with BuildSketch(Plane.XZ) as prof:
            with BuildLine():
                Line((0, z0), (r0, z0))
                CenterArc((r1, z0), NOSE_R, 0, 90)
                Line((r1, z0 + NOSE_R), (0, z0 + NOSE_R))
                Line((0, z0 + NOSE_R), (0, z0))
            make_face()
        revolve(profiles=prof.sketch.faces(), axis=Axis.Z)
    return bp.part


def create_cable(length: float = CABLE_STUB) -> Part:
    """``length`` of cable leaving the gland's nose, on the same local axis.

    Starts at ``m.GLAND_PROUD``, the nose's tip -- so the cable's own local z
    is still measured from the cap face, and a scene never has to add the two
    together to know where the run begins.
    """
    with BuildPart() as bp:
        with Locations((0, 0, m.GLAND_PROUD)):
            Cylinder(
                m.CABLE_OD / 2,
                length,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    part = bp.part
    part.color = CABLE_COLOR
    part.label = f"cable ({length:.0f} mm, ~1 bend radius)"
    return part


def seated(
    at_far_end: bool = False,
    length: float = c.LENGTH,
    cable: bool = True,
) -> list[Part]:
    """The gland (and its cable) on one end of a tube, in tube-local coordinates.

    Tube-local is ``config``'s own convention -- x along the tube from its near
    end, y = u, z = height from the underside -- which is the frame every
    assembly in this package places a lamp part from.

    The axis is ``endcap.GLAND_Z`` above the underside and on the tube's
    centre line, and it starts at the cap's *outer* face, which
    ``endcap.seated`` puts at x = -``CAP_T`` at the near end and at
    x = ``length + CAP_T`` at the far one. Local +Z is the direction the gland
    points, so it maps to -x at the near end and +x at the far end; a Y
    rotation is the whole of it, since the gland is a solid of revolution about
    that axis and its clocking carries no meaning.
    """
    from .endcap import GLAND_Z

    pieces = [create_gland()]
    if cable:
        pieces.append(create_cable())

    if not at_far_end:
        place = Pos(-CAP_T, 0, GLAND_Z) * Rotation(0, -90, 0)
        tag = "near"
    else:
        place = Pos(length + CAP_T, 0, GLAND_Z) * Rotation(0, 90, 0)
        tag = "far"

    out: list[Part] = []
    for piece in pieces:
        moved = as_part(place * piece)
        moved.color = piece.color
        moved.label = f"{piece.label} ({tag})"
        out.append(moved)
    return out


__all__ = [
    "CABLE_COLOR",
    "CABLE_STUB",
    "GLAND_COLOR",
    "create_cable",
    "create_gland",
    "free_length",
    "seated",
]
