"""Interchangeable vent cartridges -- the "click it on when the PSU runs hot" part.

Both end walls carry an identical 62 x 40 port. Three cartridges fit either one:

``blank``   sealed plug. The default, and what makes the box a sealed box.
``louvre``  chevron labyrinth: no straight-line path from outside to inside, so
            water thrown at it cannot get through, but air can. ~IP54.
``fan``     mount for a 40 x 40 x 10 fan behind a louvre, for forced cross-flow.

Why this exists: the RSP-320-24 sheds ~40 W at full load and derates from 50 C
ambient. Sealed, the box is comfortable up to roughly half rated load; past that
it needs air. Rather than guess now, the port is built once and the decision
stays swappable.

Retention is a **snap** -- one cantilever latch on the top edge that passes
through the aperture and grabs the inner face -- **plus two M3 screws**. The latch
makes it click in and hold itself; the screws are what actually compress the
gasket. A snap alone cannot crush a gasket (the lid gets away with one because
its joint only needs to be a splash seal), and screws alone would make swapping
one in the dark annoying.

The latch is on the top edge only, and singular, because the PSU passes within
6.5 mm of the end walls across z=10..42: side latches would foul it and a bottom
latch has nowhere to go.

All three are returned flange-down, which is their print pose: the flange face is
the sealing face and wants to be the smooth first layer.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Compound,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    Rotation,
    add,
    extrude,
)

from . import config as c
from . import penetrations as pen
from .util import as_part

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

FLANGE_T = c.VENT_RECESS_D  # fills the tray's recess, so the cartridge is flush
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

# ONE latch, on the top edge only. The PSU passes within 6.5 mm of the end walls
# and spans z=10..42, so side latches would foul it and a bottom latch has
# nowhere to go. Above the aperture there is clear air in both ports.
GASKET_GROOVE_W = 2.6  # for a 2 mm cord, or an RTV bead
GASKET_GROOVE_D = 1.5

FLANGE_X = c.VENT_W + 2 * c.VENT_RECESS_MARGIN_Y - 0.6  # 0.3 clearance each side
FLANGE_Y = c.VENT_H + 2 * c.VENT_RECESS_MARGIN_Z - 0.6
PLUG_X = c.VENT_W - 2 * c.VENT_CLEAR
PLUG_Y = c.VENT_H - 2 * c.VENT_CLEAR


def _flange() -> Part:
    """Common flange: seats in the tray recess, carries the gasket and screws."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(FLANGE_X, FLANGE_Y, 5.5)
        extrude(amount=FLANGE_T)

        # Gasket groove on the sealing face, inboard of the screws.
        half = GASKET_GROOVE_W / 2
        inset = 4.0
        with BuildSketch(Plane.XY):
            RectangleRounded(
                c.VENT_W + 2 * inset + half * 2, c.VENT_H + 2 * inset + half * 2, 5.0
            )
            RectangleRounded(
                c.VENT_W + 2 * inset - half * 2,
                c.VENT_H + 2 * inset - half * 2,
                4.0,
                mode=Mode.SUBTRACT,
            )
        extrude(amount=GASKET_GROOVE_D, mode=Mode.SUBTRACT)

        # M3 clearance holes matching the tray's blind inserts.
        for y, z in pen.vent_screw_positions(0.0):
            with Locations((y, z, 0)):
                Cylinder(3.4 / 2, FLANGE_T, align=MIN_Z, mode=Mode.SUBTRACT)
                # Shallow head recess so nothing stands proud in the weather.
                Cylinder(6.4 / 2, 1.2, align=MIN_Z, mode=Mode.SUBTRACT)
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
    """Sealed blanking plug. This is what ships in both ports by default."""
    with BuildPart() as bp:
        add(_flange())
        add(_plug_body(open_center=False))
        add(_latches())
    part = bp.part
    part.label = "vent_blank"
    return part


def _louvre_blades() -> Part:
    """The tilted blade stack, built in its own builder.

    Built separately on purpose: creating a ``Box`` inside a ``Locations``
    context of an open ``BuildPart`` places it at that location *first*, so a
    subsequent ``Rotation * box`` would swing the already-translated blade about
    the world origin and fling it out of the part.
    """
    n = c.VENT_LOUVRE_COUNT
    ang = math.radians(c.VENT_LOUVRE_ANGLE)
    pitch = (PLUG_Y - 6.0) / n
    blade_w = pitch / math.cos(ang) + 1.2  # overlap so no line of sight remains
    z_mid = FLANGE_T + PLUG_T / 2

    with BuildPart() as bp:
        for i in range(n):
            y = -((n - 1) / 2 - i) * pitch
            blade = Rotation(c.VENT_LOUVRE_ANGLE, 0, 0) * Box(
                PLUG_X - 4.0,
                blade_w,
                1.6,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.PRIVATE,
            )
            add(as_part(Pos(0, y, z_mid) * blade), mode=Mode.ADD)
    return bp.part


def create_louvre() -> Part:
    """Chevron labyrinth: air gets through, thrown water does not.

    Each blade is set at ``VENT_LOUVRE_ANGLE`` and overlaps its neighbour in
    projection, so there is no straight line from the outside to the inside. The
    angle is also the print angle -- at 45 the blades self-support.
    """
    with BuildPart() as bp:
        add(_flange())
        add(_plug_body(open_center=True))
        add(_louvre_blades(), mode=Mode.ADD)
        # Trim the blades back to the plug envelope -- sideways and along the
        # insertion axis. This must happen BEFORE the latches go on, or it would
        # shear the hooks off (they deliberately stand proud of the plug).
        with BuildSketch(Plane.XY.offset(FLANGE_T)):
            RectangleRounded(PLUG_X + 60, PLUG_Y + 60, 1.0)
            RectangleRounded(PLUG_X, PLUG_Y, 3.6, mode=Mode.SUBTRACT)
        extrude(amount=PLUG_T, mode=Mode.SUBTRACT)
        with Locations((0, 0, FLANGE_T + PLUG_T)):
            Box(PLUG_X + 60, PLUG_Y + 60, 40.0, align=MIN_Z, mode=Mode.SUBTRACT)
        add(_latches())

    part = bp.part
    part.label = "vent_louvre"
    return part


def create_fan() -> Part:
    """Mount for a 40 x 40 x 10 fan, for when convection is not enough."""
    bolt = c.VENT_FAN_BOLT / 2
    with BuildPart() as bp:
        add(_flange())
        add(_plug_body(open_center=True))
        add(_latches())
        # Fan bulkhead sitting just inside the plug mouth.
        plate_z = FLANGE_T + PLUG_T - 3.0
        with BuildSketch(Plane.XY.offset(plate_z)):
            RectangleRounded(PLUG_X, PLUG_Y, 3.6)
            RectangleRounded(
                c.VENT_FAN_SIZE - 4.0, c.VENT_FAN_SIZE - 4.0, 4.0, mode=Mode.SUBTRACT
            )
        extrude(amount=3.0)
        # Fan screw holes on the standard 32 mm pattern.
        for sx in (-1, 1):
            for sy in (-1, 1):
                with Locations((sx * bolt, sy * bolt, plate_z)):
                    Cylinder(3.4 / 2, 3.0, align=MIN_Z, mode=Mode.SUBTRACT)

    part = bp.part
    part.label = "vent_fan"
    return part


def cartridges() -> dict[str, Part]:
    """All three cartridges, keyed by name, each in print pose."""
    return {
        "vent_blank": create_blank(),
        "vent_louvre": create_louvre(),
        "vent_fan": create_fan(),
    }


def seated_blanks() -> list[Part]:
    """A blank fitted in each port, for the closed assembly view.

    A bare ``Rotation`` will not do this: the cartridge's local X spans VENT_W
    (which is the box's **Y**) and its local Y spans VENT_H (the box's **Z**),
    while local +Z is the insertion direction. Naming the frame outright is far
    less error-prone than composing two rotations and hoping.
    """
    from build123d import Plane

    out: list[Part] = []
    for i, (z, s) in enumerate(pen.vent_ports()):
        # Origin is the flange's OUTER face, which sits flush with the wall --
        # local z then runs inward through the recess and the aperture.
        frame = Plane(
            origin=(s * (c.INTERIOR_X / 2 + c.WALL), 0, z),
            x_dir=(0, -s, 0),  # local X -> box Y
            z_dir=(-s, 0, 0),  # local Z -> inward, so local Y -> box +Z
        )
        placed = as_part(frame.location * create_blank())
        placed.label = f"vent_blank_{i + 1}"
        out.append(placed)
    return out


def create() -> Compound:
    """Entry point for ``uv run show led_psu_enclosure.vent`` -- all three."""
    parts: list[Part] = []
    x = 0.0
    for part in cartridges().values():
        bb = part.bounding_box()
        parts.append(as_part(Pos(x - bb.min.X, 0, 0) * part))
        x += bb.size.X + 12.0
    return Compound(label="vent_cartridges", children=parts)


__all__ = [
    "create",
    "create_blank",
    "create_louvre",
    "create_fan",
    "cartridges",
    "seated_blanks",
]
