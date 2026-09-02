"""The bought parts of a lamp: the aluminium profile, its diffuser, its strip.

None of this is printed. It exists so the printed parts -- endcaps first -- have
a datum to be designed against and a way to be checked for interference, and so
the cross-section can be looked at in the viewer instead of re-measured off a
photo every time.

The cross-section is drawn once, in ``config``'s ``(u, z)`` convention, and
extruded along +X in the lamp's use pose: LED channel up, profile lying flat.

Cross-section, top to bottom::

    z=30   _-------_
         /           \\        diffuser: caps the whole upper half-circle,
        /             \\       26 mm at its base, so the tube reads as one
    z=16.8|===========|        unbroken outline. Aluminium stops here.
        | |__19 wide_| |       <- shallow recess, 1.4 deep
    z=14.1|_ |_10_| _|         <- strip slot, 10 x 1.3
        |  (o)   (o)  |        <- screw ports, straddling the shelf
    z=13.1|___________|        <- floor web; cavity ceiling
        |               |
        |  wiring cavity |     <- ~12.6 x 25, the 24 V bus and the PCB
    z=0   \\_____________/

The channel is genuinely shallow. Nearly all the tube is cavity, which is what
makes the ESP32 + bus fit at all.
"""

from __future__ import annotations

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
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
)

from . import config as c

ALU_COLOR = Color(0.72, 0.74, 0.77)
DIFFUSER_COLOR = Color(0.93, 0.94, 0.91, 0.45)  # translucent, so the strip shows
PCB_COLOR = Color(0.95, 0.95, 0.92)
EMITTER_COLOR = Color(1.00, 0.93, 0.72)  # warm, i.e. lit


def _loc(z: float) -> float:
    """Absolute height above the profile's underside -> sketch-local y.

    The stadium primitives are all centred on the origin, so every height in
    ``config`` has to be shifted by half the profile before it can be used as a
    sketch coordinate. Doing it in one place keeps ``config`` readable as real
    measurements instead of offsets.
    """
    return z - c.HEIGHT / 2


def _big() -> float:
    """A dimension comfortably larger than the section, for clipping shapes."""
    return 3 * c.HEIGHT


def _screw_port_centres() -> list[tuple[float, float]]:
    """Sketch-local centres of the two endcap screw ports."""
    return [
        (-c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z)),
        (c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z)),
    ]


# --------------------------------------------------------------- sub-sketches


def _channel_void() -> Sketch:
    """The two-step channel: shallow recess, with the strip slot inside it."""
    with BuildSketch() as s:
        with Locations((0, _loc(c.RIM_Z))):
            Rectangle(c.CHANNEL_W, c.RECESS_H, align=(Align.CENTER, Align.MAX))
        with Locations((0, _loc(c.STRIP_FLOOR_Z))):
            Rectangle(c.STRIP_SLOT_W, c.STRIP_SLOT_H, align=(Align.CENTER, Align.MIN))
    return s.sketch


def _corner_pockets() -> Sketch:
    """The voids between the recess walls and the shell, up at shelf level."""
    with BuildSketch() as s:
        SlotOverall(c.HEIGHT - 2 * c.WALL, c.WIDTH - 2 * c.WALL, rotation=90)
        with Locations((0, _loc((c.STRIP_FLOOR_Z + c.RIM_Z) / 2))):
            Rectangle(_big(), c.RIM_Z - c.STRIP_FLOOR_Z, mode=Mode.INTERSECT)
        Rectangle(c.CHANNEL_W + 2 * c.CHANNEL_WALL, _big(), mode=Mode.SUBTRACT)
    return s.sketch


def _voids() -> Sketch:
    """Everything hollow inside the extrusion, as one sketch.

    Built as a single shape on purpose. The screw bosses straddle the shelf --
    they hang out of the cavity ceiling and into the corner pockets at once --
    so they can only be left standing by punching them out of the *combined*
    void, not out of each void separately.
    """
    with BuildSketch() as s:
        # The wiring cavity: the shell's inside, below the floor web.
        SlotOverall(c.HEIGHT - 2 * c.WALL, c.WIDTH - 2 * c.WALL, rotation=90)
        with Locations((0, _loc(c.CAVITY_TOP_Z))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.INTERSECT
            )
        add(_corner_pockets())
        # Leave the bosses solid before the channel goes in, so the recess keeps
        # its full CHANNEL_W and the bosses cannot bulge into it.
        with Locations(*_screw_port_centres()):
            Circle(c.BOSS_OD / 2, mode=Mode.SUBTRACT)
        add(_channel_void())
    return s.sketch


# ------------------------------------------------------------- cross-sections


def aluminium_section() -> Sketch:
    """The extrusion's cross-section, in sketch-local coordinates."""
    with BuildSketch() as s:
        SlotOverall(c.HEIGHT, c.WIDTH, rotation=90)
        # Everything above the rim is diffuser, not aluminium.
        with Locations((0, _loc(c.RIM_Z))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MIN), mode=Mode.SUBTRACT
            )
        add(_voids(), mode=Mode.SUBTRACT)
        with Locations(*_screw_port_centres()):
            Circle(c.SCREW_PILOT_D / 2, mode=Mode.SUBTRACT)
    return s.sketch


def diffuser_section() -> Sketch:
    """The snap-in COB diffuser's cross-section.

    Its outer face continues the stadium exactly, so the assembled tube reads as
    one unbroken outline. The inner face is a separate circle, not an offset of
    the outer one -- see ``config._inner_arc``.
    """
    with BuildSketch() as s:
        SlotOverall(c.HEIGHT, c.WIDTH, rotation=90)
        with Locations((0, _loc(c.RIM_Z))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MIN), mode=Mode.INTERSECT
            )
        with Locations((0, _loc(c.DIFFUSER_INNER_Z))):
            Circle(c.DIFFUSER_INNER_R, mode=Mode.SUBTRACT)
    return s.sketch


def strip_sections() -> tuple[Sketch, Sketch]:
    """The COB strip's carrier and its emitting band, as two cross-sections."""
    with BuildSketch() as carrier:
        with Locations((0, _loc(c.STRIP_FLOOR_Z))):
            Rectangle(c.STRIP_W, c.STRIP_T, align=(Align.CENTER, Align.MIN))
    with BuildSketch() as emitter:
        with Locations((0, _loc(c.STRIP_FLOOR_Z + c.STRIP_T))):
            Rectangle(
                c.STRIP_EMITTER_W, c.STRIP_EMITTER_T, align=(Align.CENTER, Align.MIN)
            )
    return carrier.sketch, emitter.sketch


# -------------------------------------------------------------------- parts


def _extruded(section: Sketch, length: float) -> Part:
    """Run a cross-section along +X for ``length``, seated on z=0.

    The sections are drawn centred on the origin, because that is what the
    stadium primitives give you; ``_loc`` undoes the shift on the way in and
    this undoes it on the way out, so every part lands in the ``config``
    convention with the profile's underside at z=0.
    """
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ):
            add(section)
        extrude(amount=length)
    return Pos(0, 0, c.HEIGHT / 2) * bp.part


def create_extrusion(length: float = c.LENGTH) -> Part:
    """The bare aluminium profile, sitting on z=0 and running along +X."""
    part = _extruded(aluminium_section(), length)
    part.color = ALU_COLOR
    part.label = "aluminium profile"
    return part


def create_diffuser(length: float = c.LENGTH) -> Part:
    """The snap-in COB diffuser, in its clipped-in position."""
    part = _extruded(diffuser_section(), length)
    part.color = DIFFUSER_COLOR
    part.label = "diffuser"
    return part


def create_strip(length: float = c.LENGTH) -> list[Part]:
    """The 24 V COB strip, seated in its slot: carrier plus emitting band."""
    carrier_s, emitter_s = strip_sections()
    carrier = _extruded(carrier_s, length)
    carrier.color = PCB_COLOR
    carrier.label = "COB strip"
    emitter = _extruded(emitter_s, length)
    emitter.color = EMITTER_COLOR
    emitter.label = "COB emitter"
    return [carrier, emitter]


# ------------------------------------------------------------------- previz

# The two solids Beamhouse's GDTF profile ships as meshes, one per GDTF
# ``<Model>``. See ADR-0022 rule 9 in ``jnslmk/beamhouse``: the simplification
# is a *modelling* decision -- which features are invisible once the tube is
# closed -- so it belongs here, next to the constants that express it, and not
# downstream as mesh decimation guessing at intent.
#
# Everything removed is behind aluminium or behind the diffuser on a closed
# tube: the wiring cavity, the corner pockets, the screw bosses and their pilot
# ports (32 B-rep faces down to 6), and the diffuser's inner bore. What is kept
# is the outline, which is the whole point -- the stadium is what an audience
# sees and what the GDTF's ``PrimitiveType="Cube"`` fallback can only
# approximate.
#
# The COB strip is not here. It sits at z ~= 15.1 mm under a translucent
# diffuser and is not visible through it; the diffuser is the emissive surface.


def previz_shell_section() -> Sketch:
    """The aluminium's outline with nothing hollowed out of it.

    ``aluminium_section()`` minus every void: the same stadium, truncated at
    the rim, as one solid face.
    """
    with BuildSketch() as s:
        SlotOverall(c.HEIGHT, c.WIDTH, rotation=90)
        with Locations((0, _loc(c.RIM_Z))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MIN), mode=Mode.SUBTRACT
            )
    return s.sketch


def previz_diffuser_section() -> Sketch:
    """The diffuser's outline, solid -- ``diffuser_section()`` less its bore.

    The bore is the diffuser's inside face. Nothing sees it: the aluminium
    stops at the rim and the strip below it is the only thing that could look
    through, and it faces the other way.
    """
    with BuildSketch() as s:
        SlotOverall(c.HEIGHT, c.WIDTH, rotation=90)
        with Locations((0, _loc(c.RIM_Z))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MIN), mode=Mode.INTERSECT
            )
    return s.sketch


def create_previz_shell(length: float = c.LENGTH) -> Part:
    """The aluminium as a render mesh: outer shell only."""
    part = _extruded(previz_shell_section(), length)
    part.color = ALU_COLOR
    part.label = "previz body"
    return part


def create_previz_diffuser(length: float = c.LENGTH) -> Part:
    """The diffuser as a render mesh: solid, no bore."""
    part = _extruded(previz_diffuser_section(), length)
    part.color = DIFFUSER_COLOR
    part.label = "previz diffuser"
    return part
