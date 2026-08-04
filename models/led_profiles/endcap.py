"""Endcap: closes the profile, carries the M12 cable gland, screws to the ports.

One design, used at both ends -- every lamp has an input and an output pigtail,
so both caps are glanded.

Two facts about the extrusion dictate nearly everything here.

**The gland very nearly does not fit.** An M12x1.5 gland needs a ~12.3 mm bore,
and the largest circle that fits inside the wiring cavity is 12.6 mm. So the
bore has to be placed, not centred: pushed up to ``GLAND_Z`` it keeps 2.85 mm of
plastic between it and the outside of the cap, while its centre still opens into
the cavity so the cable has somewhere to go. Its upper crescent looks at the
aluminium floor web, which costs nothing -- only the middle of the bore carries
cable. A gland locknut is not an option at all: the cavity is 12.6 mm tall and
an M12 locknut is ~17 mm across, so the thread is printed into the cap instead.

**The screw ports sit 2 mm from the outer surface.** At z = 14.7 the profile is
at its full 26 mm, so a port at u = +/-11 leaves only 2.0 mm of face outboard of
it. A recessed head does not fit in that: an M2 counterbore is 4.6 mm across and
would break out through the side of the cap. So the cap is ``CAP_PROUD`` bigger
than the tube all round -- a deliberate collar, chamfered so it reads as one --
and the screws are pan-head, seated on the face rather than sunk into it.

Print pose: outer face down on the bed, lip up. That puts the gland thread on a
vertical axis (the only axis worth printing a thread on), gives the largest
possible first layer, and leaves no overhang anywhere -- the lip grows *out of*
the flange rather than hanging off it.
"""

from __future__ import annotations

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cone,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    Rotation,
    Sketch,
    SlotOverall,
    add,
    chamfer,
    extrude,
)

from models.lib import fits
from models.lib.edges import as_part

from . import config as c
from .profile import _big, _loc

# ------------------------------------------------------------------ the cap

# The collar. Driven by the screw heads, not by taste: see the module docstring.
CAP_PROUD = 0.6
CAP_W = c.WIDTH + 2 * CAP_PROUD
CAP_H = c.HEIGHT + 2 * CAP_PROUD

# Thickness is set by the thread: the printed-thread rule is an engagement of at
# least 1.0 x D, and D is 12. A stock gland's own thread is usually only ~8 mm,
# so it will engage the first 8 of these 12 and seal on its flange against the
# face; the extra depth costs 2 mm and accepts a long-thread gland too.
CAP_T = 12.0
EDGE_CHAMFER = 0.8

# ------------------------------------------------------------------ the lip

# A ring that enters the wiring cavity: it takes the rocking moment off the two
# screws and keeps the cap square. SLIDING, not SNUG -- it has to go together
# against a 1.5 m aluminium extrusion's straightness, not a printed hole.
LIP_DEPTH = 6.0
LIP_T = 1.2
LIP_FIT = fits.SLIDING
LIP_TOP_GAP = 0.4  # clears the screw bosses bulging out of the cavity ceiling

# ---------------------------------------------------------------- the gland

GLAND_THREAD_D = 12.0  # M12 x 1.5, the size the README specifies
GLAND_PITCH = 1.5
# Printed female against a real metal gland: +0.30 mm on the female major
# diameter. IsoThread emits the basic profile with zero allowance, so every bit
# of printing clearance has to be added here.
THREAD_CLEARANCE = 0.30
GLAND_MAJOR_D = GLAND_THREAD_D + THREAD_CLEARANCE

# One full pitch of plain bore below the thread, chamfered, per the printed-
# thread rule against starting a thread at z=0. It also keeps the mouth's
# lead-in cone clear of the thread: cut the two into each other and OCC's fuse
# quietly returns the thread alone instead of the cap. Measured -- set this to 0
# and the part goes from 7254 mm3 to 254, with no error raised.
GLAND_COLLAR = GLAND_PITCH
GLAND_THREAD_L = CAP_T - GLAND_COLLAR
GLAND_LEAD_IN = 0.8

# Bore centre height. Not the cavity's centre: pushed up until the wall to the
# outside of the cap is thick enough to print, which check_gland() verifies.
GLAND_Z = 9.0

# ---------------------------------------------------------------- the screws

SCREW_CLEAR_D = 2.65  # M2 normal clearance + the FDM adder
SCREW_LEAD_IN = 0.5

CAP_COLOR = Color(0.25, 0.27, 0.30)


def _cap_outline() -> Sketch:
    """The collar: the profile's stadium, grown by CAP_PROUD all round."""
    with BuildSketch() as s:
        SlotOverall(CAP_H, CAP_W, rotation=90)
    return s.sketch


def _cavity_outline(inset: float, top_gap: float) -> Sketch:
    """The wiring cavity's cross-section, shrunk by ``inset`` all round.

    Shrinking a stadium is exact -- both overall dimensions lose ``2 * inset``,
    the straight section is untouched -- so this needs no offset operation.
    """
    with BuildSketch() as s:
        SlotOverall(
            c.HEIGHT - 2 * c.WALL - 2 * inset,
            c.WIDTH - 2 * c.WALL - 2 * inset,
            rotation=90,
        )
        with Locations((0, _loc(c.CAVITY_TOP_Z - top_gap))):
            Rectangle(
                _big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.INTERSECT
            )
    return s.sketch


def lip_section() -> Sketch:
    """The register lip: a ring following the cavity wall."""
    with BuildSketch() as s:
        add(_cavity_outline(LIP_FIT / 2, LIP_TOP_GAP))
        add(
            _cavity_outline(LIP_FIT / 2 + LIP_T, LIP_TOP_GAP + LIP_T),
            mode=Mode.SUBTRACT,
        )
    return s.sketch


def create_endcap() -> Part:
    """The endcap, in its print pose: outer face on z=0, lip pointing up.

    Cap-local axes map to the profile's as x -> u and y -> z, so every constant
    from ``config`` can be used directly through ``_loc``.
    """
    # Built *before* the BuildPart is opened, deliberately. IsoThread is a
    # BasePartObject with mode=Mode.ADD, so constructing it inside a builder
    # auto-adds it at the origin; the add() below would then be a *second* copy,
    # leaving a stray thread buried at (0, 0, 0) -- 7322 mm3 instead of 7254,
    # same bounding box, no error. (Put the origin on a bore mouth that has a
    # lead-in and the same stray copy takes the entire part with it; see
    # GLAND_COLLAR.) Construct it outside, add it once, in one place.
    thread = IsoThread(
        major_diameter=GLAND_MAJOR_D,
        pitch=GLAND_PITCH,
        length=GLAND_THREAD_L,
        external=False,
        end_finishes=("fade", "fade"),
    )

    with BuildPart() as bp:
        with BuildSketch():
            add(_cap_outline())
        extrude(amount=CAP_T)

        with BuildSketch(Plane.XY.offset(CAP_T)):
            add(lip_section())
        extrude(amount=LIP_DEPTH)

        # Kill the elephant's foot on the bed-facing perimeter, and do it before
        # anything is drilled so a failure here cannot cascade through the rest.
        bottom = bp.faces().sort_by(Axis.Z)[0]
        chamfer(bottom.outer_wire().edges(), length=EDGE_CHAMFER)

        # Gland bore, then the thread fused into it.
        with BuildSketch():
            with Locations((0, _loc(GLAND_Z))):
                Circle(GLAND_MAJOR_D / 2)
        extrude(amount=CAP_T, mode=Mode.SUBTRACT)

        # Screw clearance holes. Through the flange only -- there is no lip this
        # high up, the ports sit above the cavity.
        with BuildSketch():
            with Locations(*_screw_centres()):
                Circle(SCREW_CLEAR_D / 2)
        extrude(amount=CAP_T, mode=Mode.SUBTRACT)

        # Lead-ins at every bed-facing hole mouth, cut as boolean cones rather
        # than edge chamfers -- house style, and OCC chamfers are flaky next to
        # a thread.
        for u, v in _screw_centres():
            with Locations((u, v, 0)):
                Cone(
                    bottom_radius=SCREW_CLEAR_D / 2 + SCREW_LEAD_IN,
                    top_radius=SCREW_CLEAR_D / 2,
                    height=SCREW_LEAD_IN,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        with Locations((0, _loc(GLAND_Z), 0)):
            Cone(
                bottom_radius=GLAND_MAJOR_D / 2 + GLAND_LEAD_IN,
                top_radius=GLAND_MAJOR_D / 2,
                height=GLAND_LEAD_IN,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Sits on top of the plain collar, so it never meets the lead-in above.
        with Locations((0, _loc(GLAND_Z), GLAND_COLLAR)):
            add(thread)

    part = bp.part
    part.color = CAP_COLOR
    part.label = "endcap"
    return part


def _screw_centres() -> list[tuple[float, float]]:
    """Cap-local centres of the two screw holes, on the profile's ports."""
    return [
        (-c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z)),
        (c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z)),
    ]


def seated(at_far_end: bool = False, length: float = c.LENGTH) -> Part:
    """The cap moved from its print pose into place on the profile.

    House rule: the part is authored in the pose it prints in, and the assembly
    is what moves it. Cap-local +z is the insertion direction, so it maps to the
    profile's +x at the near end and -x at the far end.
    """
    cap = create_endcap()
    # cap (x, y, z) -> profile (y, z, x). Composed explicitly rather than as a
    # single Rotation(90, 0, 90): build123d's three-angle form does not apply
    # them in the order that reads, and lands the cap on its side.
    upright = Rotation(0, 0, 90) * Rotation(90, 0, 0) * cap
    if not at_far_end:
        placed = as_part(Pos(-CAP_T, 0, c.HEIGHT / 2) * upright)
    else:
        placed = as_part(
            Pos(length + CAP_T, 0, c.HEIGHT / 2) * (Rotation(0, 0, 180) * upright)
        )
    placed.color = CAP_COLOR
    placed.label = "endcap (far)" if at_far_end else "endcap (near)"
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.endcap``."""
    return create_endcap()


__all__ = ["create", "create_endcap", "seated"]
