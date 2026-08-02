"""Keep-out mock solids for the components that go inside the enclosure.

These are deliberately *not* vendor CAD. No official STEP exists for the RSP-320
(GrabCAD / 3DContentCentral / TraceParts all sit behind accounts), and for a fit
check we only need the bounding envelope, the mounting holes and the faces that
mate with a wall. Hand-rolled mocks stay parametric, licence-clean, and match the
repo's builder-mode style.

Every mock is returned in box coordinates (see ``config``) already sitting where
the real component will sit, carries a ``.label``, and is translucent so the
assembly view reads as "shell + contents".

``keepouts()`` is what the interference check in ``checks.py`` consumes.
"""

from __future__ import annotations

from build123d import (
    Align,
    Box,
    BuildPart,
    Color,
    Cylinder,
    Locations,
    Mode,
    Part,
    Pos,
    Rotation,
)

from . import config as c
from .util import as_part

# Translucent so the shell stays readable behind them.
PSU_COLOR = Color(0.72, 0.74, 0.78, 0.55)  # brushed steel
FUSE_COLOR = Color(0.15, 0.15, 0.17, 0.65)  # black nylon body
CTRL_COLOR = Color(0.10, 0.45, 0.25, 0.65)  # PCB green
CONN_COLOR = Color(0.20, 0.28, 0.55, 0.70)  # Weipu blue/black
GLAND_COLOR = Color(0.30, 0.30, 0.32, 0.70)

MIN_Z = (Align.CENTER, Align.CENTER, Align.MIN)

# --- Component placement (the layout decision, in one place) -----------------
PSU_Z0 = c.PSU_PLATE_BOSS_H + c.PSU_PLATE_T  # PSU sits on its plate
# Both moved 1 mm further from the high port than the components alone would
# need. The binding constraint is not the controller's body or even its tabs but
# its outer *bolt hole*, which has to keep a couple of millimetres of shelf
# between its edge and the bite the fan takes out of that edge. Sliding the
# controller inboard then squeezes it against the fuse block, so the fuse block
# moves with it. check_shelf_packing() holds all four margins at once.
FUSE_X_CENTER = -63.0
# The tabs overhang the controller's body by 8 mm at each end and reach further
# in X than anything else on the shelf. They stop 3 mm short of the internal fan
# and pass *through* the yoke's throat to do it -- which is what makes a 118 mm
# controller and a 40 mm fan share one 215 mm shelf at all.
CTRL_X_CENTER = 42.0
# Both are pushed back off the front wall so the connector bodies clear them.
FUSE_Y_CENTER = -c.INTERIOR_Y / 2 + c.SHELF_FRONT_KEEPOUT + c.FUSE_Y / 2
CTRL_Y_CENTER = -c.INTERIOR_Y / 2 + c.SHELF_FRONT_KEEPOUT + c.CTRL_Y / 2

FRONT_INNER_Y = -c.INTERIOR_Y / 2
FRONT_OUTER_Y = FRONT_INNER_Y - c.WALL


def _into_box(part: Part, x: float, z: float, y0: float) -> Part:
    """Place a Z-built solid so it grows along +Y (into the box) from ``y0``."""
    return as_part(Pos(x, y0, z) * Rotation(-90, 0, 0) * part)


def _out_of_box(part: Part, x: float, z: float, y0: float) -> Part:
    """Place a Z-built solid so it grows along -Y (out of the box) from ``y0``."""
    return as_part(Pos(x, y0, z) * Rotation(90, 0, 0) * part)


def psu() -> Part:
    """Mean Well RSP-320-24 envelope, with the top-cover fan marked."""
    with BuildPart() as bp:
        Box(c.PSU_X, c.PSU_Y, c.PSU_Z, align=MIN_Z)
        # Fan boss on the top cover -- a visual reminder that this face needs a
        # plenum above it and must never be covered by the shelf.
        with Locations((c.psu_fan_center_x(), 0, c.PSU_Z)):
            Cylinder(c.PSU_FAN_D / 2, 2.0, align=MIN_Z, mode=Mode.ADD)
        # Terminal block on the -X end face.
        with Locations((-c.PSU_X / 2 + 6.0, 0, 15.0)):
            Box(12.0, 60.0, 13.5, mode=Mode.ADD)

    part = Pos(0, 0, PSU_Z0) * bp.part
    part.label = "psu_rsp320"
    part.color = PSU_COLOR
    return part


def fuse_block() -> Part:
    """LXD-4P 4-way blade-fuse block, sitting on the shelf."""
    with BuildPart() as bp:
        # Mounting ears: full footprint, but thin.
        Box(c.FUSE_X, c.FUSE_Y, 6.0, align=MIN_Z)
        # Body + clear fuse cover.
        Box(65.5, c.FUSE_Y, c.FUSE_Z, align=MIN_Z, mode=Mode.ADD)

    part = Pos(FUSE_X_CENTER, FUSE_Y_CENTER, c.shelf_top_z()) * bp.part
    part.label = "fuse_block_lxd4p"
    part.color = FUSE_COLOR
    return part


def controller() -> Part:
    """Athom / IoTorero Ethernet WLED ESP32 controller, sitting on the shelf."""
    with BuildPart() as bp:
        Box(c.CTRL_X, c.CTRL_Y, c.CTRL_Z, align=MIN_Z)
        # Mounting tabs overhanging each end of the long axis.
        Box(c.CTRL_TAB_X, 16.0, 3.0, align=MIN_Z, mode=Mode.ADD)

    part = Pos(CTRL_X_CENTER, CTRL_Y_CENTER, c.shelf_top_z()) * bp.part
    part.label = "controller_athom_eth"
    part.color = CTRL_COLOR
    return part


SP17_FRONT = 10.7  # flange + shell in front of the panel
SP17_NUT_D = 22.0  # rear nut, seats in the inside counterbore


def sp1712_sockets() -> list[Part]:
    """The four LED-output connectors, mounted through the front wall.

    Three diameters, not one: the Ø25 flange outside, the Ø17 threaded neck
    through the panel, and the Ø22 rear nut inside. Modelling it as a single Ø25
    slug would "collide" with the wall everywhere around the Ø17 bore and make
    the interference check meaningless.
    """
    parts: list[Part] = []
    for i, x in enumerate(c.sp17_positions()):
        with BuildPart() as bp:
            # Built nut-end first; the whole stack then grows in -Y.
            Cylinder(SP17_NUT_D / 2, c.SP17_BEHIND, align=MIN_Z)
            with Locations((0, 0, c.SP17_BEHIND)):
                # Slightly under the cutout so a clean fit doesn't read as a clash.
                Cylinder(
                    (c.SP17_CUTOUT_D - 0.4) / 2, c.WALL, align=MIN_Z, mode=Mode.ADD
                )
            # The neck carries the same anti-rotation flat as the panel cutout.
            # Without it the mock's round neck "collides" with the flat's bridge.
            # Local +Y becomes global +Z after _out_of_box, so this is the top.
            flat_offset = c.SP17_CUTOUT_FLAT - c.SP17_CUTOUT_D / 2
            with Locations(
                (0, flat_offset + c.SP17_CUTOUT_D / 2, c.SP17_BEHIND + c.WALL / 2)
            ):
                Box(
                    c.SP17_CUTOUT_D * 2,
                    c.SP17_CUTOUT_D,
                    c.WALL,
                    mode=Mode.SUBTRACT,
                )
            with Locations((0, 0, c.SP17_BEHIND + c.WALL)):
                Cylinder(c.SP17_FLANGE_D / 2, SP17_FRONT, align=MIN_Z, mode=Mode.ADD)
        part = _out_of_box(bp.part, x, c.SP17_Z, FRONT_INNER_Y + c.SP17_BEHIND)
        part.label = f"sp1712_out{i + 1}"
        part.color = CONN_COLOR
        parts.append(part)
    return parts


def gland() -> Part:
    """M12 cable gland for the incoming mains."""
    with BuildPart() as bp:
        Cylinder(c.GLAND_PAD_D / 2, 16.0, align=MIN_Z)  # lock nut inside
    part = _into_box(bp.part, c.GLAND_X, c.GLAND_Z, FRONT_INNER_Y)
    part.label = "gland_m12"
    part.color = GLAND_COLOR
    return part


def rj45_coupler() -> Part:
    """IP68 panel-mount RJ45 through-coupler for Ethernet."""
    with BuildPart() as bp:
        Cylinder(c.RJ45_PAD_D / 2, c.RJ45_BEHIND, align=MIN_Z)
    part = _into_box(bp.part, c.RJ45_X, c.RJ45_Z, FRONT_INNER_Y)
    part.label = "rj45_bulkhead"
    part.color = GLAND_COLOR
    return part


FAN_COLOR = Color(0.12, 0.12, 0.14, 0.75)


def internal_fan() -> Part:
    """The 40 x 40 x 10 24 V exhaust fan, nosed into the high port's aperture.

    Modelled even though the fan is optional: it is the tightest thing in the
    box (a millimetre from the controller's tabs, half a millimetre from the
    shutter panel), so the interference check has to see it whether or not a
    given build fits one.
    """
    s = c.vent_high_end()
    with BuildPart() as bp:
        Box(c.VENT_FAN_T, c.VENT_FAN_SIZE, c.VENT_FAN_SIZE)
    x = s * (c.INTERIOR_X / 2 - c.VENT_FAN_T / 2)
    part = as_part(Pos(x, 0, c.VENT_HIGH_Z) * bp.part)
    part.label = "fan_40mm_24v"
    part.color = FAN_COLOR
    return part


def keepouts() -> list[Part]:
    """Every component mock, for the assembly view and the interference check."""
    return [
        psu(),
        fuse_block(),
        controller(),
        *sp1712_sockets(),
        gland(),
        rj45_coupler(),
        internal_fan(),
    ]
