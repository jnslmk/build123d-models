"""Folding tripod hub: stands one lamp vertically, Astera AX1-STD style.

Three bought flat bars bolt to the underside of a printed hub and swing about
their M6 pivots, so they spread into a tripod and nest together for packing.
There is no ballast. The stability number is small and the doc states it
plainly rather than hiding behind a tip *angle*:

    m     = tube 0.45 + hub ~0.2 + 3 legs x 0.118        ~1.0 kg
    r_eff = leg reach x cos 60 deg  (a tripod tips about
            the line joining two legs, at half its reach)  ~134 mm
    F_tip = m g r / h                                      ~0.9 N

**About 90 g of push at the top topples it.** That is what this class of stand
is; it gets sandbagged in use. ``checks.py`` recomputes it from the real part
volume, so a change cannot quietly make it worse.

Three things the endcap forces on the geometry:

* The gland points straight down and stands ``GLAND_PROUD`` proud of the cap,
  so the hub needs a well that deep before the cap can land on anything.
* **The gland axis is 6 mm off the tube axis** (``GLAND_Z`` 9.0 against a tube
  centre at 15.0), so that well is offset, not concentric. A concentric one
  does not clear it, and it is the easiest thing here to get wrong.
* The cap collar is 27.2 x 31.2, wider than the tube, so the cradle's bore is
  opened out over the collar's height.

Print pose: standing on the flange, cradle channel vertical and opening
sideways. The cradle is a prism extruded straight up, so it is overhang-free by
construction, and the pivot counterbores open upward.
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
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rotation,
    add,
    extrude,
)

from models.lib.edges import as_part, chamfer_edge

from . import config as c
from . import cradle as cr
from . import mount_config as m
from .endcap import CAP_H, CAP_T, CAP_W

# The cradle section is drawn with the tube's underside a wall above zero; drop
# it so the tube's axis lands on the hub's own axis, where the mass wants it.
SINK = -m.TUBE_AXIS_Z

FLANGE_D = 90.0
FLANGE_T = 12.0
PIVOT_R = 30.0
PIVOT_CLEAR_D = 6.6  # M6 through-bolt into the leg, nyloc underneath
PIVOT_CBORE_D = 11.5
PIVOT_CBORE_H = 6.0
LEG_COUNT = 3

# Bought legs: flat bar, hole one end. Reach drives the whole tip-force sum.
LEG_W = 20.0
LEG_T = 3.0
LEG_LEN = 250.0
LEG_HOLE_INSET = 12.0
LEG_DENSITY = 7.85e-3  # g/mm^3, steel

WELL_H = m.GLAND_PROUD + 2.0
WELL_D = m.GLAND_ENV_D + 2.0
GLAND_OFFSET = 9.0 - c.HEIGHT / 2  # -6.0: the gland axis, relative to the tube's

PEDESTAL_D = 48.0
SEAT_Z = FLANGE_T + WELL_H
SOCKET_DEPTH = 100.0
TOP_Z = SEAT_Z + CAP_T + SOCKET_DEPTH

CABLE_SLOT_W = m.CABLE_OD + 2.0
STAND_COLOR = Color(0.30, 0.32, 0.36)
LEG_COLOR = Color(
    0.62, 0.64, 0.67
)  # a distinct metallic grey -- reads as steel, not printed ASA

STATIONS = (SEAT_Z + CAP_T + 15.0, SEAT_Z + CAP_T + 55.0, SEAT_Z + CAP_T + 90.0)


def leg_reach() -> float:
    """Pivot centre to leg tip, i.e. the tripod's radius."""
    return PIVOT_R + LEG_LEN - LEG_HOLE_INSET


def leg_mass() -> float:
    """One bought leg, in grams."""
    return LEG_W * LEG_T * LEG_LEN * LEG_DENSITY


def tip_force(hub_mass_g: float, tube_mass_g: float = 450.0) -> float:
    """Horizontal push at the top of the tube that tips the stand, in newtons.

    A tripod tips about the line joining two adjacent legs, which is at
    ``reach * cos(60 deg)`` -- half the reach. Quoting the full reach, or a tip
    angle, flatters it by a factor of two.
    """
    mass_kg = (hub_mass_g + tube_mass_g + LEG_COUNT * leg_mass()) / 1000.0
    r_eff = leg_reach() * cos(radians(60.0)) / 1000.0
    return mass_kg * 9.81 * r_eff / (c.LENGTH / 1000.0)


def _pivot_positions() -> list[tuple[float, float]]:
    return [
        (PIVOT_R * cos(radians(90 + 120 * i)), PIVOT_R * sin(radians(90 + 120 * i)))
        for i in range(LEG_COUNT)
    ]


def create_stand_hub() -> Part:
    """The hub, in its print pose: flange on z=0, socket opening +Y."""
    with BuildPart() as bp:
        with BuildSketch():
            Circle(FLANGE_D / 2)
        extrude(amount=FLANGE_T)

        with BuildSketch(Plane.XY.offset(FLANGE_T)):
            Circle(PEDESTAL_D / 2)
        extrude(amount=WELL_H)

        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            add(cr.body_section(lift=SINK, floor=None))
        extrude(amount=TOP_Z - SEAT_Z)

        # Bore for the tube, and a wider one over the endcap collar's height.
        with BuildSketch(Plane.XY.offset(SEAT_Z + CAP_T)):
            add(cr.tube_section(m.BORE_FIT, lift=SINK))
        extrude(amount=TOP_Z - SEAT_Z - CAP_T, mode=Mode.SUBTRACT)
        collar = max(CAP_W - c.WIDTH, CAP_H - c.HEIGHT) + 1.0
        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            add(cr.tube_section(collar, lift=SINK))
        extrude(amount=CAP_T, mode=Mode.SUBTRACT)

        # The gland well -- offset, because the gland axis is not the tube's.
        with Locations((0, GLAND_OFFSET, FLANGE_T)):
            Cylinder(
                WELL_D / 2,
                WELL_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Cable out of the back of the well, and a drain under it. Cut as a box
        # rather than an extruded sketch: Plane.XZ faces -Y, so offsetting it
        # walks the sketch out past the part instead of through it.
        with Locations((0, -PEDESTAL_D / 2, FLANGE_T + 1)):
            Box(
                CABLE_SLOT_W,
                PEDESTAL_D,
                CABLE_SLOT_W,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations((0, GLAND_OFFSET, 0)):
            Cylinder(
                m.DRAIN_D / 2,
                FLANGE_T,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Leg pivots: bolt down through the flange into the leg, nyloc beneath.
        with Locations(*[(x, y, 0) for x, y in _pivot_positions()]):
            Cylinder(
                PIVOT_CLEAR_D / 2,
                FLANGE_T,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations(*[(x, y, FLANGE_T) for x, y in _pivot_positions()]):
            Cylinder(
                PIVOT_CBORE_D / 2,
                PIVOT_CBORE_H,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )

        # Strap bosses up the socket, then their inserts.
        for z in STATIONS:
            with BuildSketch(Plane.XY.offset(z - m.STRAP_W / 2)):
                add(cr.boss_pad_section(lift=SINK, base=cr.back_z(SINK)))
            extrude(amount=m.STRAP_W)
        _drill_strap_inserts()
        chamfer_edge(
            bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), m.EDGE_CHAMFER
        )

    part = bp.part
    part.color = STAND_COLOR
    part.label = "stand hub"
    return part


def _drill_strap_inserts() -> None:
    """Insert holes at each strap station up the socket.

    ``rotation=(90, 0, 0)`` turns the cylinder's axis onto -Y, so ``Align.MIN``
    is what drives it *into* the boss from the mouth face; ``MAX`` would drill
    outward into the air and cut nothing.
    """
    for z in STATIONS:
        for side in (-1, 1):
            with Locations((side * m.BOSS_U, m.CRADLE_DEPTH + SINK, z)):
                Cylinder(
                    m.INSERT_D / 2,
                    m.INSERT_DEPTH,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )


def seated() -> Part:
    """The hub, in the pose a tripod assembly wants -- which is unchanged.

    Every other mount in this family prints lying on its back and needs
    ``seated()`` to stand it up onto the tube. The stand is the opposite: it
    *prints* standing on the flange, socket opening +Y, and ``SINK`` already
    lands the socket's tube axis on the hub's own vertical (Z) axis at
    x=0, y=0 -- see the module docstring. So the print pose already is the
    assembly pose, and a tube dropped in from above along +Z lands on-axis
    with no further placement. This still goes through its own function
    rather than a bare re-export of ``create_stand_hub``, so a caller
    assembling the family can rely on ``stand.seated()`` existing the way
    ``corner.seated()`` and ``feet.seated()`` do, and so a future change to
    the print pose has one obvious place to add the now-missing transform.
    """
    hub = create_stand_hub()
    hub.label = "stand hub (seated)"
    return hub


def create_leg() -> Part:
    """A bought flat-bar leg, MOCKED for assembly views only.

    **Not a printed part.** Real hardware: LEG_W x LEG_T mild-steel flat bar,
    LEG_LEN long, with a single PIVOT_CLEAR_D clearance hole LEG_HOLE_INSET
    from the pivot end for the M6 through-bolt (see the module docstring and
    ``leg_mass``). This mock exists so an assembly view can show *something*
    where the leg goes; it must never appear in ``assembly.printed_parts()``.

    Local frame: the pivot hole sits on the Z axis at the origin, so placing
    a leg is a Z rotation plus an XY translation with no compensating offset
    -- see ``seated_legs``. The bar extends from the hole out to the tip
    along +X, and sits *under* the flange plane: top face at z=0, thickness
    running down to z=-LEG_T, matching the through-bolt that goes down
    through the flange and into the leg (see ``create_stand_hub``).
    """
    with BuildPart() as bp:
        with Locations((-LEG_HOLE_INSET, 0, -LEG_T)):
            Box(LEG_LEN, LEG_W, LEG_T, align=(Align.MIN, Align.CENTER, Align.MIN))
        with Locations((0, 0, 0)):
            Cylinder(
                PIVOT_CLEAR_D / 2,
                LEG_T,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )

    part = bp.part
    part.color = LEG_COLOR
    part.label = "leg (bought, mock)"
    return part


def seated_legs(splay_deg: float = 0.0) -> list[Part]:
    """Three bought legs, bolted on their pivots and splayed for a stance.

    The pivots are already 120 deg apart (``_pivot_positions``); a leg's
    default bearing is straight out along that same radial line, i.e. it
    points directly away from the hub centre through its own pivot, which is
    the fully-deployed, evenly-spread stance. ``splay_deg`` rotates all three
    legs together, off that radial reference -- 0 is deployed-radial, and
    driving it away from 0 sweeps the legs round their pivots in step, which
    is what a caller wants to animate folding the tripod for packing.

    Each leg's local origin is its own pivot hole (see ``create_leg``), so
    placing one is just rotate-then-translate to the pivot's (x, y) -- no
    offset to compensate for.
    """
    legs = []
    for i, (px, py) in enumerate(_pivot_positions()):
        bearing = 90.0 + 120.0 * i + splay_deg
        leg = as_part(Pos(px, py, 0) * (Rotation(0, 0, bearing) * create_leg()))
        leg.color = LEG_COLOR
        leg.label = f"leg {i}"
        legs.append(leg)
    return legs


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stand``."""
    return create_stand_hub()


__all__ = [
    "create",
    "create_leg",
    "create_stand_hub",
    "leg_mass",
    "leg_reach",
    "seated",
    "seated_legs",
    "tip_force",
]
