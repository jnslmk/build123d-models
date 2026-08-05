"""Cable gland and cable stub: bought hardware, MOCKED for assembly views.

**Nothing here is printed.** The endcap carries a printed M12 x 1.5 *female*
thread (``endcap.GLAND_MAJOR_D``); the gland itself is a bought nylon fitting
screwed into it, and this module is a stand-in for one so an assembly view can
show the volume it occupies. It must never appear in
``assembly.printed_parts()``.

The reason it exists is that ``mount_config.GLAND_ENV_D`` and
``GLAND_PROUD`` -- both ASSUMED, both load-bearing -- were until now only ever
*consumed*, by ``corner.gland_setback`` and by ``stand.WELL_D`` / ``WELL_H``.
Every mount reserved a hole for a gland nobody had drawn, so no view could show
whether the thing actually clears what is around it. Drawing it turns those two
numbers into geometry a scene can be looked at.

Local frame: the gland's axis is +Z and **z = 0 is the endcap's outer face**,
which is the datum both consumers already measure from. So the stem runs down
into the cap (negative z, buried in the printed thread), and everything from
z = 0 to z = ``m.GLAND_PROUD`` is the part standing out in the open. Split
three ways, summing to ``GLAND_PROUD`` by construction rather than by three
typed numbers that could drift out of it:

* ``BODY_H`` -- the hex the spanner goes on, ``GLAND_ENV_D`` across corners,
  i.e. exactly the envelope every mount was cut to clear.
* ``NUT_H`` -- the compression nut, a little smaller across.
* ``NOSE_H`` -- the strain-relief nose tapering onto the cable.

The proportions inside that 30 mm are representative, not measured; the two
things that *are* held to the design are the overall reach and the widest
diameter, because those are the two numbers the mounts were built against.
Measure a real gland before printing anything that depends on them -- see
``mount_config``'s own warning.

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
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Locations,
    Part,
    Plane,
    Pos,
    RegularPolygon,
    Rotation,
    extrude,
)

from models.lib.edges import as_part

from . import config as c
from . import mount_config as m
from .endcap import CAP_T, GLAND_THREAD_D

# ------------------------------------------------------------------ the stem

# The bought gland's own male thread. A stock M12 gland carries ~8 mm of it,
# which is why ``endcap.CAP_T`` is 12: the first 8 engage and the flange seals
# on the cap's face, and the extra depth accepts a long-thread gland too.
THREAD_D = GLAND_THREAD_D  # 12.0
THREAD_L = 8.0

# ------------------------------------------------------------ what stands out

BODY_ENV_D = m.GLAND_ENV_D  # 24.0 across the hex's corners -- *the* envelope
NUT_ENV_D = 0.85 * BODY_ENV_D  # 20.4
BODY_H = 10.0
NUT_H = 12.0
NOSE_H = m.GLAND_PROUD - BODY_H - NUT_H  # 8.0 -- the remainder, never a literal

NOSE_BASE_D = 0.70 * NUT_ENV_D  # 14.28, comfortably inside the nut's flats
NOSE_TIP_D = m.CABLE_OD + 1.6  # 8.3 -- the seal closed onto the cable

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

    Built as three stacked prisms plus the buried stem, in one builder: it is a
    mock of a bought part, so there are no edge treatments to isolate and
    nothing here can fail the way an OCC edge op can.
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
            RegularPolygon(BODY_ENV_D / 2, 6)
        extrude(amount=BODY_H)

        # Clocked 30 deg off the body, the way a nut tightened onto a held hex
        # ends up: it makes the two read as separate pieces in a shaded view.
        with BuildSketch(Plane.XY.offset(BODY_H)):
            RegularPolygon(NUT_ENV_D / 2, 6, rotation=30)
        extrude(amount=NUT_H)

        with Locations((0, 0, BODY_H + NUT_H)):
            Cone(
                bottom_radius=NOSE_BASE_D / 2,
                top_radius=NOSE_TIP_D / 2,
                height=NOSE_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    part = bp.part
    part.color = GLAND_COLOR
    part.label = "cable gland (bought, mock)"
    return part


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
