"""Vent ports -- a sliding shutter you can throttle without opening the box.

Both end walls carry an identical 62 x 40 port, and what sits in it is a
**sliding shutter**: screwed in once and adjusted in place, in two printed parts.

``vent_shutter``  the fixed panel. It seats in the tray's recess on a gasket and
                  two M3s hold it down. Its slot field is a louvre -- the slots
                  climb up-and-in at ``VENT_SLOT_TILT`` through the 3 mm panel,
                  so there is no straight-line path from outside to inside and
                  thrown water has to run uphill to get in.
``vent_slider``   a slotted plate riding in a T-channel on the panel's outer
                  face. Let it down and its slots line up with the louvre (wide
                  open); push it up half a pitch and its bars cover them (shut).

Why sliding rather than a swapped cartridge: the RSP-320-24 sheds ~40 W at full
load and derates from 50 C ambient, but the load that actually matters is the
installation's, and it moves with the season. A shutter is a thumb push on a
closed box; the old blank/louvre swap meant unscrewing a cartridge to change
your mind about it.

The shutter is held by the two screws alone -- the old snap latch is gone with
the cartridge it existed for. A latch made a part you swap in the dark click
into place; a part you fit once and then never remove does not need one, and the
screws were always what compressed the gasket.

Travel is bounded at both ends by the panel: the block closing the top of the
channel is the shut stop, and a detent rod across the mouth is the open stop.
The rod doubles as the retainer -- the slider has to be lifted ``VENT_DETENT``
out of plane to pass it, which is a deliberate push, not something gravity does.
Failure is toward *open*: shut is the position you have to push it into.

``vent_fan_yoke``  the carrier for an internal 40 mm 24 V exhaust fan, screwed to
                   the high port's frame from *inside*. This is the recommended
                   way to force air: the fan sits behind the louvre, so forced
                   ventilation costs nothing in weatherproofing. It is also the
                   part that decides how tall the box is -- see the note on its
                   screw positions in ``create_fan_yoke``.

Two optional cartridges still fit the same port and the same two screws:
``vent_blank`` for a genuinely sealed box (a shut shutter is weather-tight, not
airtight) and ``vent_fan``, the original wall-mounted fan cartridge. ``vent_fan``
is superseded by the yoke -- it works, but it replaces the louvre it sits in --
and a ``vent_blank`` cannot share the high port with the internal fan, since the
plug body and the fan want the same volume.

**Frames.** Every part is authored in its own print pose, per the house rule,
and the two families print opposite ways up:

* the shutter panel and its slider print **outer face up**: local z = 0 is the
  face that beds down (the panel's gasket face, the slider's running face) and
  local +Z points *outward*, away from the box;
* the blank/fan cartridges print **flange face down with the plug standing up**:
  local z = 0 is the outer face and local +Z points *inward*, the way they insert.

``seated_shutters()``/``seated_blanks()`` encode each mapping so no call site
has to.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Rotation,
    add,
    chamfer,
    extrude,
)

from . import config as c
from . import penetrations as pen
from .util import as_part

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

FLANGE_T = c.VENT_RECESS_D  # fills the tray's recess, so the part is flush
# Measured from the recess floor, not the outer face: the recess has already
# eaten VENT_RECESS_D of wall. This lands the hook exactly on the frame's
# inner face.
PLUG_T = c.WALL + c.VENT_FRAME_T - c.VENT_RECESS_D
LATCH_T = 2.0  # cantilever thickness (the direction it flexes)
LATCH_W = 30.0  # how wide the latch is across the top edge
LATCH_OVERHANG = 1.0  # how far the hook grabs the frame's inner face
# The arm runs on past the hook so it is long enough to actually bend. A
# cantilever only as long as the plug (5.5 mm) would need ~10 % strain to deflect
# 1 mm -- it would snap, not click. At 12.5 mm the strain is ~1.9 %, which ASA
# takes happily. The tail doubles as the finger tab for releasing it.
LATCH_TAIL = 7.0

GASKET_GROOVE_W = 2.6  # for a 2 mm cord, or an RTV bead
GASKET_GROOVE_D = 1.5
GASKET_INSET = 4.0  # groove centre line, out from the aperture edge

FLANGE_X = c.VENT_W + 2 * c.VENT_RECESS_MARGIN_Y - 0.6  # 0.3 clearance each side
FLANGE_Y = c.VENT_H + 2 * c.VENT_RECESS_MARGIN_Z - 0.6
PLUG_X = c.VENT_W - 2 * c.VENT_CLEAR
PLUG_Y = c.VENT_H - 2 * c.VENT_CLEAR

SCREW_CLEAR_D = 3.4
SCREW_HEAD_D = 6.4
SCREW_HEAD_DEPTH = 1.2

# --- Sliding shutter, all derived from the slot pitch -------------------------

PANEL_T = c.VENT_RECESS_D  # the panel IS the flange: 3 mm, flush in the recess
PITCH = c.VENT_SLOT_H + c.VENT_SLOT_BAR
TRAVEL = PITCH / 2  # open -> shut is exactly half a pitch, by definition

FIELD_H = c.VENT_SLOT_COUNT * PITCH - c.VENT_SLOT_BAR  # slot field, top to bottom
# One more bar than there are slots, so the slider still covers the field's top
# and bottom edge after it has travelled.
SLIDER_H = FIELD_H + 2 * c.VENT_SLOT_BAR

# Rails land on the flange just outboard of the aperture, where the recess floor
# is behind them -- not on the part of the panel that bridges the opening.
CHANNEL_W = c.VENT_W - 2.0
CHANNEL_D = c.VENT_SLIDER_T + c.VENT_SLIDER_LIFT
FIELD_W = CHANNEL_W - 2 * c.VENT_LIP  # slots stop where the lips start
SLIDER_W = CHANNEL_W - 2 * c.VENT_SLIDER_CLEAR
COL_W = (FIELD_W - c.VENT_MULLION_W) / 2  # one of the two slot columns
COL_X = (c.VENT_MULLION_W + COL_W) / 2
# The slider's own columns are cut 0.5 mm short of the panel's at each side. The
# strip left outside them is all that ties its bars together AND all the lip has
# to hold, and at the panel's width that strip would be one lip's worth (1.2 mm)
# of material. Half a millimetre of open area buys a 1.7 mm strip.
SLIDER_COL_W = COL_W - 1.0

# Where the detent rod breaks the surface of the channel floor. The slider rests
# against that line, so the rod's *emergence* -- not its centre -- is what sets
# the open position, and the channel is sized from it.
DETENT_RISE = math.sqrt(c.VENT_DETENT_R**2 - (c.VENT_DETENT_R - c.VENT_DETENT) ** 2)
CHANNEL_H = SLIDER_H + TRAVEL + c.VENT_DETENT_R + DETENT_RISE
CHANNEL_TOP = CHANNEL_H / 2
DETENT_Y = -CHANNEL_TOP + c.VENT_DETENT_R

OPEN_BOTTOM = DETENT_Y + DETENT_RISE
OPEN_CENTER = OPEN_BOTTOM + SLIDER_H / 2  # slider centre, wide open
SHUT_CENTER = OPEN_CENTER + TRAVEL  # slider centre, shut against the top block

# Slot centre lines on the panel's OUTER face -- the face the slider covers. The
# cut climbs inward from there, so the inner opening sits PANEL_T * tan(tilt)
# higher up.
SLOT_ROWS = [
    (i - (c.VENT_SLOT_COUNT - 1) / 2) * PITCH for i in range(c.VENT_SLOT_COUNT)
]
SLOT_RISE = PANEL_T * math.tan(math.radians(c.VENT_SLOT_TILT))
# Wide open, per port, measured on the face: the slider's columns are the
# narrower pair, so they are what the air actually gets through. The throat is
# this times cos(tilt) -- a tilted slot is narrower than its opening.
OPEN_AREA = c.VENT_SLOT_COUNT * c.VENT_SLOT_H * 2 * SLIDER_COL_W


# --- Shared flange features ---------------------------------------------------


def _gasket_groove(z: float) -> Part:
    """Cord groove tool for the sealing face lying at ``z``, cutting upward.

    The groove belongs on the face that beds against the recess floor -- put it
    on the weather side and it seals nothing. (Which is what the cartridges used
    to do: the groove was cut from z = 0, the *outer* face.)
    """
    half = GASKET_GROOVE_W / 2
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(z)):
            RectangleRounded(
                c.VENT_W + 2 * GASKET_INSET + 2 * half,
                c.VENT_H + 2 * GASKET_INSET + 2 * half,
                5.0,
            )
            RectangleRounded(
                c.VENT_W + 2 * GASKET_INSET - 2 * half,
                c.VENT_H + 2 * GASKET_INSET - 2 * half,
                4.0,
                mode=Mode.SUBTRACT,
            )
        extrude(amount=GASKET_GROOVE_D)
    return bp.part


def _screw_holes(head_z: float, through: float) -> Part:
    """M3 clearance holes matching the tray's blind pilots, heads sunk at ``head_z``."""
    with BuildPart() as bp:
        for y, z in pen.vent_screw_positions(0.0):
            with Locations((y, z, 0)):
                Cylinder(SCREW_CLEAR_D / 2, through, align=MIN_Z)
            # Shallow head recess so nothing stands proud in the weather.
            with Locations((y, z, head_z - SCREW_HEAD_DEPTH)):
                Cylinder(SCREW_HEAD_D / 2, SCREW_HEAD_DEPTH, align=MIN_Z)
    return bp.part


# --- The sliding shutter ------------------------------------------------------


def create_shutter() -> Part:
    """The fixed panel: louvre field, slider channel, gasket and screws.

    Built in its print pose -- gasket face on the bed at z = 0, everything the
    weather sees growing upward. The channel's lips are the only overhang and
    they reach ``VENT_LIP`` (1.5 mm) off a rail, which is an anchored bridge, not
    a droop.
    """
    tilt = c.VENT_SLOT_TILT
    with BuildPart() as bp:
        # The plate, chamfered top and bottom while it is still a plain prism --
        # edge ops are reliable here and nowhere else on this part.
        with BuildSketch(Plane.XY):
            RectangleRounded(FLANGE_X, FLANGE_Y, 5.5)
        extrude(amount=PANEL_T)
        rings = bp.edges().group_by(Axis.Z)
        saved = bp.part
        try:
            chamfer(rings[0] + rings[-1], length=0.5)
        except Exception:  # pragma: no cover - geometry-dependent
            bp.part = saved

        add(_gasket_groove(0.0), mode=Mode.SUBTRACT)
        add(_screw_holes(head_z=PANEL_T, through=PANEL_T), mode=Mode.SUBTRACT)

        # Louvre slots. Each is a slab tilted about local X: rotating a +Z-long
        # box by +tilt sends its axis to (0, -sin, cos), so the opening moves
        # DOWN as it comes out through the weather face -- water would have to
        # climb SLOT_RISE to get in.
        w_perp = c.VENT_SLOT_H * math.cos(math.radians(tilt))
        for y in SLOT_ROWS:
            slab = Rotation(tilt, 0, 0) * Box(FIELD_W, w_perp, 60.0, mode=Mode.PRIVATE)
            add(
                as_part(Pos(0, y + SLOT_RISE / 2, PANEL_T / 2) * slab),
                mode=Mode.SUBTRACT,
            )

        # Centre mullion, put back after the cuts: it halves every bar's span,
        # and it sits behind the strip between the slider's two columns, so it
        # costs no open area.
        with Locations((0, 0, 0)):
            Box(c.VENT_MULLION_W, FIELD_H + 4.0, PANEL_T, align=MIN_Z)

        # Slider channel: two rails with lips reaching back over the plate.
        for sx in (-1, 1):
            with Locations((sx * (CHANNEL_W + c.VENT_RAIL_W) / 2, 0, PANEL_T)):
                Box(
                    c.VENT_RAIL_W,
                    CHANNEL_H,
                    CHANNEL_D + c.VENT_LIP_T,
                    align=MIN_Z,
                )
            with Locations(
                (
                    sx * (CHANNEL_W - c.VENT_LIP) / 2,
                    0,
                    PANEL_T + CHANNEL_D,
                )
            ):
                Box(c.VENT_LIP, CHANNEL_H, c.VENT_LIP_T, align=MIN_Z)

        # Block closing the top of the channel -- the shut stop, and what ties
        # the two rails together.
        with Locations((0, CHANNEL_TOP + c.VENT_END_WALL / 2, PANEL_T)):
            Box(
                CHANNEL_W + 2 * c.VENT_RAIL_W,
                c.VENT_END_WALL,
                CHANNEL_D + c.VENT_LIP_T,
                align=MIN_Z,
            )

        # Detent rod across the mouth: the open stop, the click, and the reason
        # the slider cannot fall out of the open end of its own channel.
        with Locations((0, DETENT_Y, PANEL_T - (c.VENT_DETENT_R - c.VENT_DETENT))):
            Cylinder(c.VENT_DETENT_R, CHANNEL_W, rotation=(0, 90, 0))

    part = bp.part
    part.label = "vent_shutter"
    return part


def create_slider() -> Part:
    """The plate that throttles the louvre.

    Prints flat, tab up, no supports. Its slots are offset from its own centre by
    ``OPEN_CENTER`` so that when it is sitting on the detent they land exactly on
    the panel's slot rows.
    """
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(SLIDER_W, SLIDER_H, 2.0)
        extrude(amount=c.VENT_SLIDER_T)
        # Relief on the running face, which is the bed face: a squashed first
        # layer here would bind in the channel instead of sliding in it.
        saved = bp.part
        try:
            chamfer(bp.edges().group_by(Axis.Z)[0], length=0.4)
        except Exception:  # pragma: no cover - geometry-dependent
            bp.part = saved

        for y in SLOT_ROWS:
            for sx in (-1, 1):
                with Locations((sx * COL_X, y - OPEN_CENTER, 0)):
                    Box(
                        SLIDER_COL_W,
                        c.VENT_SLOT_H,
                        c.VENT_SLIDER_T,
                        align=MIN_Z,
                        mode=Mode.SUBTRACT,
                    )

        # Thumb tab, in the margin below the slots. It stands proud of the rail
        # lips, which is what makes it findable without looking.
        tab_y = -SLIDER_H / 2 + 0.6 + c.VENT_TAB_H / 2
        with Locations((0, tab_y, c.VENT_SLIDER_T)):
            Box(c.VENT_TAB_W, c.VENT_TAB_H, c.VENT_TAB_PROUD, align=MIN_Z)
        # Grip grooves run across the tab, i.e. across the direction it is
        # pushed, so a wet thumb has something to bite on.
        for i in (-1, 0, 1):
            with Locations((0, tab_y + i * 1.1, c.VENT_SLIDER_T + c.VENT_TAB_PROUD)):
                Cylinder(
                    0.5,
                    c.VENT_TAB_W,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )

    part = bp.part
    part.label = "vent_slider"
    return part


# --- Internal fan yoke (high port only) ---------------------------------------

YOKE_HALF_Y = c.vent_yoke_half_y()
YOKE_HALF_Z = c.vent_yoke_half_z()
YOKE_RAIL_H = c.vent_yoke_rail_h()


def create_fan_yoke() -> Part:
    """Carrier for the 40 x 40 x 10 24 V exhaust fan, inside the high port.

    A plate that sits BEHIND the fan and stands off the vent frame's inner face
    on two rails, so the fan's outer face ends up flush with the inner wall face,
    blowing straight through the aperture and out through the louvre. That is the
    point of mounting the fan inside rather than swapping in ``vent_fan``: the
    tilted-slot labyrinth stays in front of the blades, so forced ventilation
    costs nothing in weatherproofing.

    Four M3 self-tappers hold the fan (into its own housing, as fan screws do)
    and four more hold the yoke to the frame -- in the frame's *side* bands, at
    the same radius as the shutter's own screws but offset in Z. Putting them
    above and below the fan instead would push the port up about 7 mm, and the
    port's height sets the height of the whole box (``config.interior_z``).

    Printed plate-down, rails up: no overhangs, no supports.
    """
    total = c.VENT_YOKE_T + YOKE_RAIL_H
    bolt = c.VENT_FAN_BOLT / 2
    screw_y = c.vent_yoke_screw_y()

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(2 * YOKE_HALF_Y, 2 * YOKE_HALF_Z, 4.0)
        extrude(amount=c.VENT_YOKE_T)
        # Bed-face ring only: the rails have to seat flat on the other side.
        saved = bp.part
        try:
            chamfer(bp.edges().group_by(Axis.Z)[0], length=0.5)
        except Exception:  # pragma: no cover - geometry-dependent
            bp.part = saved

        # Rails: they bridge back to the frame's inner face and are what the
        # yoke screws pass through, so they run the plate's full height.
        for sx in (-1, 1):
            with Locations((sx * screw_y, 0, c.VENT_YOKE_T)):
                Box(c.VENT_YOKE_RAIL_W, 2 * YOKE_HALF_Z, YOKE_RAIL_H, align=MIN_Z)

        # Throat. Sized to clear the blades while leaving the bolt pads solid --
        # the 32 mm pattern sits at radius 22.6, outside this bore.
        with Locations((0, 0, 0)):
            Cylinder(
                c.VENT_FAN_BORE_D / 2, c.VENT_YOKE_T, align=MIN_Z, mode=Mode.SUBTRACT
            )

        # Fan screws: clearance only, they thread into the fan's own housing.
        for sx in (-1, 1):
            for sy in (-1, 1):
                with Locations((sx * bolt, sy * bolt, 0)):
                    Cylinder(
                        SCREW_CLEAR_D / 2,
                        c.VENT_YOKE_T,
                        align=MIN_Z,
                        mode=Mode.SUBTRACT,
                    )

        # Yoke screws, through plate and rail into the frame's blind pilots.
        # Heads are sunk so they do not eat into the controller's clearance.
        for sx in (-1, 1):
            for sy in (-1, 1):
                with Locations((sx * screw_y, sy * c.VENT_YOKE_SCREW_DZ, 0)):
                    Cylinder(SCREW_CLEAR_D / 2, total, align=MIN_Z, mode=Mode.SUBTRACT)
                    Cylinder(
                        SCREW_HEAD_D / 2,
                        SCREW_HEAD_DEPTH,
                        align=MIN_Z,
                        mode=Mode.SUBTRACT,
                    )

    part = bp.part
    part.label = "vent_fan_yoke"
    return part


# --- Optional cartridges (same port, same two screws) -------------------------


def _flange() -> Part:
    """Cartridge flange: seats in the tray recess, carries the gasket and screws."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(FLANGE_X, FLANGE_Y, 5.5)
        extrude(amount=FLANGE_T)
        # Sealing face is the INNER one here -- these print outer-face-down.
        add(_gasket_groove(FLANGE_T - GASKET_GROOVE_D), mode=Mode.SUBTRACT)
        add(_screw_holes(head_z=SCREW_HEAD_DEPTH, through=FLANGE_T), mode=Mode.SUBTRACT)
    return bp.part


def _latches() -> Part:
    """The cantilever snap that clicks behind the inner face of the vent frame.

    Local +Y becomes box +Z once seated, so this sits on the cartridge's top edge.
    """
    arm_len = PLUG_T + LATCH_TAIL
    y_arm = PLUG_Y / 2 - LATCH_T / 2
    with BuildPart() as bp:
        with Locations((0, y_arm, FLANGE_T + arm_len / 2)):
            Box(LATCH_W, LATCH_T, arm_len, mode=Mode.ADD)
        # The hook sits just PAST the frame's inner face (FLANGE_T + PLUG_T), so
        # its underside bears on that face and pulling out bites. Half a hook
        # earlier would bury it in the frame and the cartridge could never seat.
        with Locations(
            (0, y_arm + LATCH_OVERHANG / 2, FLANGE_T + PLUG_T + LATCH_OVERHANG / 2)
        ):
            Box(LATCH_W, LATCH_T + LATCH_OVERHANG, LATCH_OVERHANG, mode=Mode.ADD)
    return bp.part


def _plug_body(open_center: bool) -> Part:
    """The section that passes through the aperture. Hollow for the vented ones."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(FLANGE_T)):
            RectangleRounded(PLUG_X, PLUG_Y, 3.6)
        extrude(amount=PLUG_T)
        if open_center:
            with BuildSketch(Plane.XY.offset(FLANGE_T)):
                RectangleRounded(PLUG_X - 2 * 2.4, PLUG_Y - 2 * 2.4, 2.0)
            extrude(amount=PLUG_T, mode=Mode.SUBTRACT)
    return bp.part


def create_blank() -> Part:
    """Sealed blanking plug -- the only way to make a port genuinely airtight."""
    with BuildPart() as bp:
        add(_flange())
        add(_plug_body(open_center=False))
        add(_latches())
    part = bp.part
    part.label = "vent_blank"
    return part


def create_fan() -> Part:
    """Mount for a 40 x 40 x 10 fan, for when convection is not enough."""
    bolt = c.VENT_FAN_BOLT / 2
    guard = c.VENT_FAN_SIZE - 4.0
    with BuildPart() as bp:
        add(_flange())
        add(_plug_body(open_center=True))
        add(_latches())
        # The flange has to be opened up or the fan blows against a solid plate.
        # Two bars across it keep fingers out of the blades.
        with BuildSketch(Plane.XY):
            RectangleRounded(guard, min(guard, PLUG_Y - 2 * 2.4), 3.0)
        extrude(amount=FLANGE_T, mode=Mode.SUBTRACT)
        for sy in (-1, 1):
            with Locations((0, sy * guard / 6, 0)):
                Box(guard, 3.0, FLANGE_T, align=MIN_Z)

        # Fan bulkhead sitting just inside the plug mouth.
        plate_z = FLANGE_T + PLUG_T - 3.0
        with BuildSketch(Plane.XY.offset(plate_z)):
            RectangleRounded(PLUG_X, PLUG_Y, 3.6)
            RectangleRounded(guard, guard, 4.0, mode=Mode.SUBTRACT)
        extrude(amount=3.0)
        # Fan screw holes on the standard 32 mm pattern.
        for sx in (-1, 1):
            for sy in (-1, 1):
                with Locations((sx * bolt, sy * bolt, plate_z)):
                    Cylinder(SCREW_CLEAR_D / 2, 3.0, align=MIN_Z, mode=Mode.SUBTRACT)

    part = bp.part
    part.label = "vent_fan"
    return part


# --- Placement ----------------------------------------------------------------


def cartridges() -> dict[str, Part]:
    """Every printed vent part, keyed by name, each in print pose."""
    return {
        "vent_shutter": create_shutter(),
        "vent_slider": create_slider(),
        "vent_fan_yoke": create_fan_yoke(),
        "vent_blank": create_blank(),
        "vent_fan": create_fan(),
    }


def _outward_frame(z: float, s: int) -> Plane:
    """Frame for a part authored outer-face-up, sitting on the recess floor.

    Local +Z runs OUT of the box, local +Y is box +Z, local +X spans the port's
    width. Naming the frame outright beats composing two rotations and hoping.
    """
    return Plane(
        origin=(s * (c.INTERIOR_X / 2 + c.WALL - c.VENT_RECESS_D), 0.0, z),
        x_dir=(0.0, float(s), 0.0),
        z_dir=(float(s), 0.0, 0.0),
    )


def _inward_frame(z: float, s: int) -> Plane:
    """Frame for a cartridge authored flange-down, inserting inward.

    Origin is the flange's OUTER face, which sits flush with the wall -- local z
    then runs inward through the recess and the aperture.
    """
    return Plane(
        origin=(s * (c.INTERIOR_X / 2 + c.WALL), 0.0, z),
        x_dir=(0.0, float(-s), 0.0),
        z_dir=(float(-s), 0.0, 0.0),
    )


def seated_shutters(shut: bool = False) -> list[Part]:
    """A shutter fitted in each port, sliders open (or shut), for the assembly."""
    out: list[Part] = []
    y = SHUT_CENTER if shut else OPEN_CENTER
    for i, (z, s) in enumerate(pen.vent_ports()):
        frame = _outward_frame(z, s)
        panel = as_part(frame.location * create_shutter())
        panel.label = f"vent_shutter_{i + 1}"
        slider = as_part(frame.location * Pos(0, y, PANEL_T) * create_slider())
        slider.label = f"vent_slider_{i + 1}"
        out += [panel, slider]
    return out


def _yoke_frame(z: float, s: int) -> Plane:
    """Frame for the fan yoke, authored plate-down with its rails facing the wall.

    Origin is the plate's INBOARD face -- the deepest the fan assembly reaches
    into the box -- so local +Z runs outward through the rails to the frame.
    """
    return Plane(
        origin=(s * c.vent_yoke_back_x(), 0.0, z),
        x_dir=(0.0, float(s), 0.0),
        z_dir=(float(s), 0.0, 0.0),
    )


def seated_fan_yoke() -> Part:
    """The fan yoke fitted in the high port, for the assembly and the checks."""
    s = c.vent_high_end()
    part = as_part(_yoke_frame(c.VENT_HIGH_Z, s).location * create_fan_yoke())
    part.label = "vent_fan_yoke"
    return part


def seated_blanks() -> list[Part]:
    """A blanking plug fitted in each port -- the sealed configuration."""
    out: list[Part] = []
    for i, (z, s) in enumerate(pen.vent_ports()):
        placed = as_part(_inward_frame(z, s).location * create_blank())
        placed.label = f"vent_blank_{i + 1}"
        out.append(placed)
    return out


def create() -> Compound:
    """Entry point for ``uv run show led_psu_enclosure.vent`` -- every vent part."""
    parts: list[Part] = []
    x = 0.0
    for part in cartridges().values():
        bb = part.bounding_box()
        parts.append(as_part(Pos(x - bb.min.X, 0, 0) * part))
        x += bb.size.X + 12.0
    return Compound(label="vent_parts", children=parts)


__all__ = [
    "create",
    "create_shutter",
    "create_slider",
    "create_fan_yoke",
    "create_blank",
    "create_fan",
    "cartridges",
    "seated_shutters",
    "seated_fan_yoke",
    "seated_blanks",
]
