"""The clamp's body: the part with the window in it.

    uv run export wire_clamp.body

Print pose is the use pose -- it stands on its base and the screw goes in from
the top, which is also the only way it prints without support. Four things
follow, and they are most of the file:

* **The channel is a slot, not a bore.** Its width is the plunger's, so the
  plunger is guided by two flats and a strand cannot escape sideways from under
  it; its length is the plunger plus a wire-sized passage at each end, so the
  wire's two legs can run *past* the plunger and be clamped underneath it rather
  than nipped at its rim. ``config.Clamp.wire_pass`` argues that at length; it
  is the one place this model departs from the shape it reconstructs.
* **The window is wider than the channel and its edge breaks.** That is what
  lets the sill and lintel breaks be plain lofted frusta: everything above the
  sill is already gone across the whole width, so a frustum there breaks an edge
  instead of grooving a wall.
* **The window's top is a bridge**, over the flat of its stadium, which is
  ``window_w - window_h`` wide -- 4.9 mm at 1 mm wire. Every other downward
  facing surface inside the part is at 45 degrees: the step from the channel up
  to the thread bore, the lintel break, and the thread's own lower flanks.
* **The floor ribs are added last**, after every cut, because they are the only
  additive feature that lives inside a hole.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Cylinder,
    GeomType,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    SlotOverall,
    add,
    extrude,
    loft,
)

from ..lib.edges import as_part, chamfer_edge, fillet_edge
from . import thread as tp
from .config import (
    BOTTOM_CHAMFER,
    DEFAULT,
    LIP_CHAMFER,
    MOUTH_LEAD_IN,
    TOP_CHAMFER,
    WIRE_DEFAULT,
    WIRE_MAX,
    WIRE_MIN,
    Clamp,
)

_BASE = (Align.CENTER, Align.CENTER, Align.MIN)

MOUTH_FILLET_LADDER = (0.5, 0.4, 0.3, 0.2)
"""Radii tried on the two window mouths, largest first.

A rolled mouth rather than a chamfered one because a wire bears on it: this is
the edge the strand crosses on its way in, every time the clamp is opened, and
it is the only edge on the part a moving wire touches. The ladder is the house
pattern for an OCC edge op whose exact size does not matter as long as *some*
break lands (``build123d-geometry-ops``) -- the mouth is a stadium hole through
a curved wall, which is a shape OCC is entitled to refuse.
"""


def _slot(c: Clamp, grow: float = 0.0):
    """The channel's cross-section, optionally grown by ``grow`` all round.

    Long axis along Y, which is the wire's axis: ``SlotOverall`` lays its length
    along X, so it is turned a quarter turn rather than given a height larger
    than its width, which is not a slot.
    """
    return SlotOverall(c.channel_l + 2 * grow, c.channel_w + 2 * grow, rotation=90)


def window_tool(c: Clamp) -> Part:
    """The cord window: a stadium prism straight through, in the wire's axis.

    Deliberately a plain prism. A lofted flare would break the mouths for free
    on a *flat* wall, but this wall is a cylinder: the mouth's own radius runs
    from 4.2 mm at the window's ends out to 5.65 mm at its centre, so a flare
    cut along the wire's axis is inside the material at one end of the mouth and
    outside it at the other, and chamfers neither. The mouths get a real fillet
    instead, above.
    """
    zc = (c.window_z0 + c.window_z1) / 2
    reach = c.body_r + 1.0
    with BuildPart() as tool:
        for y in (-reach, reach):
            with BuildSketch(Plane.XZ.offset(y)):
                with Locations((0, zc)):
                    SlotOverall(c.window_w, c.window_h)
        loft(ruled=True)
    return tool.part


def channel_tool(c: Clamp) -> Part:
    """Everything the screw and the wire share, as one solid void.

    Bottom to top, in the channel's own profile rather than as separate cuts:

    * the slot, from the floor up to the sill;
    * a 45 degree flare out to ``LIP_CHAMFER`` oversize, which is the break the
      wire bends over on its way in;
    * the oversize slot across the whole height of the window;
    * the same flare inverted at the lintel, back to the slot;
    * a 45 degree step out to the round thread bore -- out across the wire, in
      along it, in one loft;
    * the bore itself, up through the top of the part.

    Profiled rather than subtracted piecewise because the two breaks have to
    land exactly on the channel's rim: see ``config.LIP_CHAMFER`` for what
    happens to a frustum that tries to reach the sill from outside it.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(c.base_t)):
            _slot(c)
        extrude(amount=c.window_z0 - LIP_CHAMFER - c.base_t)

        with BuildSketch(Plane.XY.offset(c.window_z0 - LIP_CHAMFER)):
            _slot(c)
        with BuildSketch(Plane.XY.offset(c.window_z0)):
            _slot(c, LIP_CHAMFER)
        loft(ruled=True)

        with BuildSketch(Plane.XY.offset(c.window_z0)):
            _slot(c, LIP_CHAMFER)
        extrude(amount=c.window_h)

        with BuildSketch(Plane.XY.offset(c.window_z1)):
            _slot(c, LIP_CHAMFER)
        with BuildSketch(Plane.XY.offset(c.window_z1 + LIP_CHAMFER)):
            _slot(c)
        loft(ruled=True)

        with BuildSketch(Plane.XY.offset(c.window_z1 + LIP_CHAMFER)):
            _slot(c)
        extrude(amount=c.channel_top - c.window_z1 - LIP_CHAMFER)

        with BuildSketch(Plane.XY.offset(c.channel_top)):
            _slot(c)
        with BuildSketch(Plane.XY.offset(c.thread_z0)):
            Circle(c.female_root_r)
        loft(ruled=True)

        with BuildSketch(Plane.XY.offset(c.thread_z0)):
            Circle(c.female_root_r)
        extrude(amount=c.body_h - c.thread_z0)
    return tool.part


def rib_tool(c: Clamp) -> Part:
    """Half-round ridges across the channel floor, at right angles to the wire.

    Straight ribs here, concentric rings on the plunger that comes down on them:
    the pairing is the original's, measured off its 6 mm file. Straight ribs
    resist the wire sliding the way it is actually pulled; rings bite whatever
    rotation the screw happens to stop at. Either alone is half a clamp.

    Spaced ``rib_pitch`` apart, which is the one grip dimension that scales with
    the wire -- ribs finer than the thing they grip only polish it.
    """
    span = c.channel_l / 2 - c.rib_h
    count = int(span // c.rib_pitch)
    reach = c.channel_w + 1.0
    with BuildPart() as tool:
        for i in range(-count, count + 1):
            with Locations((0, i * c.rib_pitch, c.base_t)):
                Cylinder(c.rib_h, reach, rotation=(0, 90, 0))
    return tool.part


def build(c: Clamp = DEFAULT) -> Part:
    """The body, in print pose: base on z=0, bore mouth up."""
    # Outside the builder, once: ``Thread`` is a ``BasePartObject`` and would
    # otherwise add itself at the origin as well as where it is placed --
    # ``build123d-geometry-ops``, gotchas 6. The origin here is the middle of
    # the channel floor, so a stray copy would sit right under the plunger.
    thread = tp.female(c, c.thread_engage)
    channel = channel_tool(c)
    window = window_tool(c)
    ribs = rib_tool(c)

    with BuildPart() as bp:
        Cylinder(c.body_r, c.body_h, align=_BASE)

        # Both outer chamfers now, while the shell is a bare cylinder and every
        # face they select from is clean. An edge op OCC refuses on a bare
        # cylinder was never going to work later.
        chamfer_edge(bp, bp.faces().sort_by(Axis.Z)[0].edges(), BOTTOM_CHAMFER)
        chamfer_edge(bp, bp.faces().sort_by(Axis.Z)[-1].edges(), TOP_CHAMFER)

        add(channel, mode=Mode.SUBTRACT)
        add(as_part(Pos(0, 0, c.thread_z0) * thread))

        # Lead-in at the mouth. A full pitch of plain bore separates it from the
        # thread's last turn; cutting the two into each other is what makes
        # OCC's fuse hand back the thread and drop the body.
        with Locations((0, 0, c.body_h - MOUTH_LEAD_IN)):
            Cone(
                c.female_root_r,
                c.female_root_r + MOUTH_LEAD_IN,
                MOUTH_LEAD_IN,
                align=_BASE,
                mode=Mode.SUBTRACT,
            )

        add(window, mode=Mode.SUBTRACT)

        # Roll the two window mouths. Selected as the inner wires of the outer
        # wall -- by *predicate*, never by index into a sorted list, because the
        # two mouths tie on every axis a sort could use (gotchas 9).
        outer = max(
            (f for f in bp.faces() if f.geom_type == GeomType.CYLINDER),
            key=lambda f: f.area,
        )
        mouths = [e for w in outer.inner_wires() for e in w.edges()]
        for radius in MOUTH_FILLET_LADDER:
            if fillet_edge(bp, mouths, radius):
                break

        add(ribs)

    return bp.part


PARAMS = [
    {
        "name": "wire_d",
        "label": "Wire diameter (mm)",
        "type": "number",
        "min": WIRE_MIN,
        "max": WIRE_MAX,
        "step": 0.1,
        "default": WIRE_DEFAULT,
    },
]
"""The same one slider the assembly carries, repeated here because the website
reads ``PARAMS`` per module and this is the module you download an STL from. A
slider on a scene nobody can print is a slider nobody can use."""


def create(wire_d: float = WIRE_DEFAULT) -> Part:
    """The clamp body, print pose, base on the bed."""
    return build(Clamp.of(wire_d))
