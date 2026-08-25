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
* **The window is as narrow as the notch allows** -- wider than the notch and
  its edge breaks, so the sill and lintel breaks can be plain lofted steps in
  the channel's own profile, but no wider: at the small sizes that leaves it
  narrower than the plunger, so the plunger standing in the bore covers the
  opening completely and the only daylight through the clamp is the notch.
  ``config.Clamp.window_w`` has the argument.
* **The window's top is a bridge**, over the flat of its stadium, which is
  ``window_w - window_h`` wide -- 3.6 mm at 1 mm wire. Every other downward
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
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    Sketch,
    SlotOverall,
    add,
    extrude,
    fillet,
    loft,
)

from ..lib.edges import as_part, chamfer_edge, fillet_edge
from . import thread as tp
from .config import (
    DEFAULT,
    LIP_CHAMFER,
    WIRE_DEFAULT,
    WIRE_MAX,
    WIRE_MIN,
    Clamp,
)

_BASE = (Align.CENTER, Align.CENTER, Align.MIN)

MOUTH_FILLET_FRACTIONS = (0.20, 0.14, 0.10, 0.07)
"""Radii tried on the two window mouths, as fractions of the window's height.

Proportional rather than absolute because the mouth's own end radius is half the
window height, and a fillet is refused once it approaches that -- so a ladder in
millimetres is either too coarse at the small end of the slider or pointlessly
timid at the large one.

A rolled mouth rather than a chamfered one because a wire bears on it: this is
the edge the strand crosses on its way in, every time the clamp is opened, and
it is the only edge on the part a moving wire touches. The ladder is the house
pattern for an OCC edge op whose exact size does not matter as long as *some*
break lands (``build123d-geometry-ops``) -- the mouth is a stadium hole through
a curved wall, which is a shape OCC is entitled to refuse.
"""


NOTCH_CORNER_R = 0.4
"""2D fillet where each notch's outline crosses the bore's.

A rectangle laid across a circle meets it at four glancing corners, and a corner
in the *void* is a sharp edge in the *material* -- four vertical ones running the
height of the channel, right where the wire turns into the notch. Rolled in the
sketch rather than on the solid: a 2D fillet is a curve operation on a closed
wire and does not have OCC's edge-op failure modes, and this is exactly the
"fillet vertical edges" half of the house rule.
"""


def channel_section(c: Clamp, grow: float = 0.0) -> Sketch:
    """The channel's cross-section: a bore the plunger fills, plus two notches.

    **The bore is the point.** The plunger is round, because it has to pass down
    through the female thread to be assembled, and a circle is the largest thing
    that fits through a circle -- so if the plunger is to cover the opening, the
    opening has to be that circle. Everything the plunger does not cover is then
    deliberate: one notch at each end, ``notch_w`` wide, which is the wire's way
    past it. A strand cannot wander sideways out of a notch that is only as wide
    as the strands, and it cannot wander anywhere else because the plunger is
    sitting on it.

    This replaces a slot as wide as the plunger for its whole length, which left
    a strand free to sit anywhere across it -- and left the plunger's round edge
    free to push it further out on the way down.

    ``grow`` widens **only the notch**, for the 45 degree breaks at the sill and
    the lintel. Not the bore: the wire crosses the notch's rim and never the
    bore's, and a bore that steps in and out again over the window's height
    collides with the window's own rounded ends and leaves four sharp edges
    there. Left alone it is one cylinder from floor to channel top, with no rim
    to break in the first place.

    Built in its own sketch so the corners can be rolled before any caller
    extrudes it.
    """
    with BuildSketch() as section:
        Circle(c.female_crest_r)
        Rectangle(c.notch_w + 2 * grow, c.channel_l + 2 * grow)
        fillet(section.vertices(), NOTCH_CORNER_R)
    return section.sketch


def window_tool(c: Clamp) -> Part:
    """The cord window: a stadium prism straight through, in the wire's axis.

    Deliberately a plain prism. A lofted flare would break the mouths for free
    on a *flat* wall, but this wall is a cylinder: the mouth's own radius runs
    from the pillar's at the window's ends out to the body's at its centre, so a
    flare cut along the wire's axis is inside the material at one end of the
    mouth and outside it at the other, and chamfers neither. The mouths get a
    real fillet instead, above.
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
            add(channel_section(c))
        extrude(amount=c.window_z0 - LIP_CHAMFER - c.base_t)

        with BuildSketch(Plane.XY.offset(c.window_z0 - LIP_CHAMFER)):
            add(channel_section(c))
        with BuildSketch(Plane.XY.offset(c.window_z0)):
            add(channel_section(c, LIP_CHAMFER))
        loft(ruled=True)

        with BuildSketch(Plane.XY.offset(c.window_z0)):
            add(channel_section(c, LIP_CHAMFER))
        extrude(amount=c.window_h)

        with BuildSketch(Plane.XY.offset(c.window_z1)):
            add(channel_section(c, LIP_CHAMFER))
        with BuildSketch(Plane.XY.offset(c.window_z1 + LIP_CHAMFER)):
            add(channel_section(c))
        loft(ruled=True)

        with BuildSketch(Plane.XY.offset(c.window_z1 + LIP_CHAMFER)):
            add(channel_section(c))
        extrude(amount=c.channel_top - c.window_z1 - LIP_CHAMFER)

        with BuildSketch(Plane.XY.offset(c.channel_top)):
            add(channel_section(c))
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
        chamfer_edge(bp, bp.faces().sort_by(Axis.Z)[0].edges(), c.bottom_chamfer)
        chamfer_edge(bp, bp.faces().sort_by(Axis.Z)[-1].edges(), c.top_chamfer)

        add(channel, mode=Mode.SUBTRACT)
        add(as_part(Pos(0, 0, c.thread_z0) * thread))

        # No lead-in cone here: the female thread's top turn is clipped
        # conically by its own end finish, which is the same lead-in without a
        # boolean that has to be kept a pitch clear of the thread. See
        # ``thread.female`` -- that is where the body's 3.3 mm of plain collar
        # went.

        add(window, mode=Mode.SUBTRACT)

        # Roll the two window mouths. Selected by *predicate*, never by index
        # into a sorted list, because the two mouths tie on every axis a sort
        # could use (gotchas 9): the wall they pierce is the largest face that
        # has holes in it.
        #
        # Not "the largest cylindrical face", which is what this asked for
        # first. That reads as a safe description of a round body's outside
        # wall, and at one slider position in six OCC hands back a wall that is
        # not a cylinder at all and the selection raises on an empty sequence --
        # taking the whole build with it, for the sake of an edge treatment that
        # is optional by construction. So: no geom_type in the predicate, and a
        # miss skips the fillet rather than ending the part.
        pierced = [f for f in bp.faces() if f.inner_wires()]
        if pierced:
            outer = max(pierced, key=lambda f: f.area)
            mouths = [e for w in outer.inner_wires() for e in w.edges()]
            for fraction in MOUTH_FILLET_FRACTIONS:
                if fillet_edge(bp, mouths, fraction * c.window_h):
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
