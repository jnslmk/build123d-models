"""Geometry assertions for the aluminium profile assembly.

The two-step channel, the wall thickness, the screw ports and the diffuser's
seat are all invisible in a projection -- they are interior geometry seen
end-on. So they get point-sampled instead of eyeballed, per the house rule.

This is a model of a *bought* part, so the assertions are doing something
slightly unusual: they hold the reconstruction to the measurements it was built
from. If a caliper reading in ``config`` is corrected and the section stops
making sense, this is what says so.

    uv run check led_profiles
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from math import cos, hypot, radians, sin, sqrt

from build123d import (
    Align,
    Compound,
    Cylinder,
    GeomType,
    Part,
    Pos,
    Rotation,
)

from models.lib import fits
from models.lib.checks import (
    Report,
    interior_angle,
    is_periodic_seam,
    is_solid_at,
    is_vertical_seam,
    sharp_convex_edges,
)
from models.lib.edges import as_part

from . import assemblies
from . import config as c
from . import corner as corner_mod
from . import endcap as e
from . import endcap_wired as ew
from . import feet as feet_mod
from . import gland as gl
from . import gland as gland_mod
from . import mount_config as mc
from . import stand as stand_mod
from .stand import config as sc
from .stand import keeper as keeper_mod
from .stand import leg as leg_mod
from . import strap as strap_mod
from .assembly import create_bare
from .assembly import parts as lamp_parts
from .endcap import CAP_W
from . import cradle as cradle_mod
from .cradle import (
    create_cradle,
    outer_half_width,
    trough_floor_arc_r,
    trough_floor_z,
)
from .profile import _loc, create_diffuser, create_extrusion, create_strip

# Sample well inside the ends, so a face never lands on a sample point.
X = c.SECTION_LENGTH / 2

# The smaller of the two printers this repo targets, and ASA's density.
BED = 256.0
ASA_DENSITY = 1.07e-3  # g/mm^3

# Every bought part, in every assembly view, is labelled with one of these
# prefixes (a suffix like " (lamp 0)" or " (near)" may follow, hence a prefix
# match rather than an exact one). Everything else in a scene is a printed
# mount -- endcap, strap, foot, corner, stand hub -- except the mocks listed in
# MOCK_LABEL_PREFIXES, which are bought hardware too but stand in for it rather
# than measure it.
BOUGHT_LABEL_PREFIXES = ("aluminium profile", "diffuser", "COB strip", "COB emitter")

# Bought hardware that is *mocked*, not reconstructed: a tripod leg
# (``stand.create_leg``), and the gland and its cable (``gland.py``). Each of
# those modules is explicit that its geometry is representative, so they belong
# on neither side of the printed-vs-bought clearance check -- holding a printed
# mount clear of a shape nobody has measured would be asserting the mock, not
# the design. What the gland's envelope *does* have to clear is checked against
# the numbers directly, in ``check_stand_gland_cable``.
MOCK_LABEL_PREFIXES = ("leg ", "cable gland", "cable (")


def check_outline(alu: Part, r: Report) -> None:
    """The stadium: 26 wide, two R13 arcs, 4 mm of straight flank between them."""
    r.section("Outer shape")
    bb = alu.bounding_box()
    r.check(
        abs(bb.size.Y - c.WIDTH) < 0.01,
        "profile width",
        f"{bb.size.Y:.2f} mm, want {c.WIDTH}",
    )
    r.check(abs(bb.min.Z) < 0.01, "sits on z=0", f"min z {bb.min.Z:.3f}")
    r.check(
        abs(bb.max.Z - c.RIM_Z) < 0.01,
        "aluminium stops at the rim",
        f"{bb.max.Z:.2f} mm, want {c.RIM_Z}",
    )
    # Sample the flank where it is genuinely single-wall: above the lower arc
    # (z > RADIUS, so the section is straight-sided) but still below the floor
    # web, which spans the full width and would read as wall.
    z_flank = (c.RADIUS + c.CAVITY_TOP_Z) / 2
    r.check(is_solid_at(alu, X, c.WIDTH / 2 - 0.25, z_flank), "flank wall present")
    r.check(
        not is_solid_at(alu, X, c.WIDTH / 2 - c.WALL - 0.2, z_flank),
        "flank wall is only WALL thick",
        f"hollow {c.WALL + 0.2:.1f} mm in",
    )
    r.check(is_solid_at(alu, X, 0, c.WALL / 2), "bottom wall present")


def check_wiring_cavity(alu: Part, r: Report) -> None:
    """The hollow the 24 V bus and the ESP32 PCB have to fit into."""
    r.section("Wiring cavity")
    r.check(
        not is_solid_at(alu, X, 0, c.CAVITY_TOP_Z - 0.5),
        "cavity is open below the floor web",
    )
    r.check(
        not is_solid_at(alu, X, 0, c.CAVITY_TOP_Z / 2),
        "cavity is open through its depth",
    )
    r.check(is_solid_at(alu, X, 0, c.CAVITY_TOP_Z + c.FLOOR_T / 2), "floor web present")
    depth = c.CAVITY_TOP_Z - c.WALL
    r.check(depth > 10.0, "cavity depth", f"{depth:.1f} mm under the strip floor")
    r.check(
        depth * 2 > c.HEIGHT * 0.6,
        "cavity is most of the tube",
        f"{100 * depth / c.HEIGHT:.0f}% of the height",
    )


def check_channel(alu: Part, r: Report) -> None:
    """The two-step channel: shallow recess, with the strip slot inside it."""
    r.section("LED channel")
    z_recess = c.RIM_Z - c.RECESS_H / 2
    r.check(not is_solid_at(alu, X, 0, z_recess), "recess is open")
    r.check(
        is_solid_at(alu, X, c.CHANNEL_W / 2 + c.CHANNEL_WALL / 2, z_recess),
        "recess wall present",
    )
    r.check(
        not is_solid_at(alu, X, c.CHANNEL_W / 2 - 0.2, z_recess),
        "recess is CHANNEL_W wide",
        f"open out to {c.CHANNEL_W / 2 - 0.2:.2f} from centre",
    )

    z_slot = c.STRIP_FLOOR_Z + c.STRIP_SLOT_H / 2
    r.check(not is_solid_at(alu, X, 0, z_slot), "strip slot is open")
    r.check(
        not is_solid_at(alu, X, c.STRIP_SLOT_W / 2 - 0.2, z_slot),
        "slot is STRIP_SLOT_W wide",
    )
    r.check(
        is_solid_at(alu, X, 0, c.STRIP_FLOOR_Z - 0.2), "floor is solid under the slot"
    )

    # The step itself: material beside the slot, hollow directly above it.
    u_step = (c.STRIP_SLOT_W / 2 + c.CHANNEL_W / 2) / 2
    r.check(is_solid_at(alu, X, u_step, z_slot), "ledge beside the slot")
    r.check(
        not is_solid_at(alu, X, u_step, z_recess),
        "and the recess runs over that ledge",
        f"the {c.RECESS_H:.1f} mm step the user flagged as missing",
    )


def check_screw_ports(alu: Part, r: Report) -> None:
    """The two lengthwise ports an endcap screws into."""
    r.section("Endcap screw ports")
    u = c.SCREW_SPACING / 2
    z = c.SCREW_BOSS_Z
    r.check(not is_solid_at(alu, X, u, z), "port bore is open (+u)")
    r.check(
        not is_solid_at(alu, -X + c.SECTION_LENGTH, -u, z), "port bore is open (-u)"
    )
    ring = (c.SCREW_PILOT_D / 2 + c.BOSS_OD / 2) / 2
    r.check(is_solid_at(alu, X, u, z + ring), "boss material around the bore")
    r.check(is_solid_at(alu, X, u - ring, z), "boss material inboard of the bore")

    # The shell curves in above and below the straight band; make sure the bore
    # has not been pushed somewhere it breaks out through the outside.
    arc_z = c.TOP_ARC_Z if z > c.TOP_ARC_Z else (c.BOT_ARC_Z if z < c.BOT_ARC_Z else z)
    skin = c.RADIUS - hypot(u, z - arc_z) - c.SCREW_PILOT_D / 2
    r.check(
        skin > 0.5,
        "aluminium outboard of the bore",
        f"{skin:.2f} mm to the outer surface",
    )

    # The user's correction: the bosses hang below the shelf, not above it.
    r.check(
        z - c.BOSS_OD / 2 < c.STRIP_FLOOR_Z,
        "boss hangs below the shelf",
        f"reaches down to z={z - c.BOSS_OD / 2:.2f}, shelf at {c.STRIP_FLOOR_Z}",
    )


def check_diffuser(alu: Part, diffuser: Part, r: Report) -> None:
    """Flush outer face, 26 across the outside, 25 inside, 1.0 at the crown."""
    r.section("Diffuser")
    bb = diffuser.bounding_box()
    r.check(
        abs(bb.max.Z - c.HEIGHT) < 0.01,
        "diffuser completes the outline",
        f"apex at {bb.max.Z:.2f} mm, want {c.HEIGHT}",
    )
    r.check(
        abs(bb.size.Y - c.WIDTH) < 0.02,
        "diffuser is WIDTH across the outside",
        f"{bb.size.Y:.2f} mm, want {c.WIDTH}",
    )
    r.check(abs(bb.min.Z - c.RIM_Z) < 0.01, "seats on the rim", f"z {bb.min.Z:.2f}")

    r.check(
        is_solid_at(diffuser, X, 0, c.HEIGHT - c.DIFFUSER_T / 2), "crown wall present"
    )
    r.check(
        not is_solid_at(diffuser, X, 0, c.HEIGHT - c.DIFFUSER_T - 0.15),
        "crown is DIFFUSER_T thick",
        f"{c.DIFFUSER_T} mm",
    )
    # Inner width just above the rim -- the second of the two measurements.
    z_probe = c.RIM_Z + 0.15
    r.check(
        not is_solid_at(diffuser, X, c.DIFFUSER_INNER_W / 2 - 0.3, z_probe),
        "hollow to DIFFUSER_INNER_W just above the rim",
        f"{c.DIFFUSER_INNER_W} mm inside",
    )
    r.check(
        is_solid_at(diffuser, X, c.DIFFUSER_INNER_W / 2 + 0.2, z_probe),
        "and solid outboard of that",
    )

    overlap = _shared_volume(alu, diffuser)
    r.check(
        overlap < 0.01,
        "diffuser does not clash with the profile",
        f"{overlap:.4f} mm^3",
    )


def check_strip(alu: Part, strip: Part, r: Report) -> None:
    """The COB strip drops into its slot without being pinched."""
    r.section("COB strip")
    bb = strip.bounding_box()
    side = (c.STRIP_SLOT_W - bb.size.Y) / 2
    r.check(side > 0.02, "strip clears the slot walls", f"{side:.2f} mm per side")
    r.check(
        abs(bb.min.Z - c.STRIP_FLOOR_Z) < 0.01,
        "strip sits on the slot floor",
        f"z {bb.min.Z:.2f}",
    )
    overlap = _shared_volume(alu, strip)
    r.check(
        overlap < 0.01, "strip does not clash with the profile", f"{overlap:.4f} mm^3"
    )


def check_endcap(cap: Part, r: Report) -> None:
    """The cap itself: flush flange, gland thread, screw pockets, plug."""
    r.section("Endcap")
    bb = cap.bounding_box()
    r.check(
        abs(bb.size.X - e.CAP_W) < 0.01 and abs(bb.size.Y - e.CAP_H) < 0.01,
        "flange size",
        f"{bb.size.X:.2f} x {bb.size.Y:.2f} mm, {e.CAP_PROUD} proud of the tube",
    )
    # The correction that made the cap flush: it used to be CAP_PROUD = 0.6 all
    # round and measured 0.55 mm too wide per side against the real extrusion.
    r.check(
        abs(e.CAP_W - c.WIDTH) < 0.001 and abs(e.CAP_H - c.HEIGHT) < 0.001,
        "flush with the tube -- no collar",
        f"cap {e.CAP_W} x {e.CAP_H} against tube {c.WIDTH} x {c.HEIGHT}",
    )
    r.check(
        abs(bb.min.Z) < 0.01, "outer face on z=0 (print pose)", f"min z {bb.min.Z:.3f}"
    )
    r.check(
        abs(bb.size.Z - (e.CAP_T + e.PLUG_DEPTH)) < 0.01,
        "overall depth",
        f"{bb.size.Z:.2f} mm = {e.CAP_T} flange + {e.PLUG_DEPTH} plug",
    )
    r.check(len(cap.solids()) == 1, "one solid", f"{len(cap.solids())}")

    # The flange used to be exactly the gland's thread length, and this used to
    # assert that. The strap slot took over sizing it, so the claim splits in
    # two: the *printed thread* is still the gland's own male thread, and the
    # flange is now at least that, which is all the gland ever needed -- it
    # seals on its flange against the cap's face, and the face has not moved.
    r.check(
        abs(e.GLAND_MALE_L - gland_mod.THREAD_L) < 0.001,
        "printed thread is sized off the gland's own male thread",
        f"GLAND_MALE_L {e.GLAND_MALE_L} mm vs gland.THREAD_L "
        f"{gland_mod.THREAD_L} mm -- one source, aliased not restated",
    )
    r.check(
        e.CAP_T >= e.GLAND_MALE_L,
        "...and the flange is deep enough for all of it",
        f"{e.CAP_T} mm of flange for {e.GLAND_MALE_L} mm of male thread; "
        f"the {e.CAP_T - e.GLAND_MALE_L:.2f} mm behind it is plain bore",
    )
    # The flange is the strap slot plus its two walls, and nothing else. Stated
    # so that a change to CAP_T has to come through the slot rather than be
    # typed over the top of it.
    r.check(
        abs(e.CAP_T - (e.STRAP_SLOT_W + 2 * e.STRAP_WALL)) < 0.001,
        "flange is derived from the strap slot",
        f"{e.STRAP_SLOT_W} slot + 2 x {e.STRAP_WALL} wall = {e.CAP_T} mm",
    )
    r.check(
        e.PLUG_DEPTH > e.CAP_T,
        "the plug, not the flange, is what holds the cap square",
        f"{e.PLUG_DEPTH} mm into the cavity behind a {e.CAP_T} mm flange -- "
        f"and the flange now carries a strap pulling on that lever arm",
    )


def check_screw_pockets(cap: Part, r: Report) -> None:
    """The sunk screw heads, and the scallop sinking them costs.

    The screws are short, so each head is counterbored down to ``SCREW_FLOOR_T``
    of the aluminium and the whole of the screw's length goes into the port. A
    4.4 mm head needs more room outboard of the port than a flush cap has, so
    the pocket cuts out through the flank -- deliberate, and bounded here so it
    cannot quietly grow into something that weakens the flank.
    """
    r.section("Endcap screw pockets")
    u = c.SCREW_SPACING / 2
    v = _loc(c.SCREW_BOSS_Z)

    r.check(
        e.SCREW_SEAT_D > e.SCREW_HEAD_D,
        "seat swallows the head",
        f"{e.SCREW_SEAT_D:.2f} mm rim for a {e.SCREW_HEAD_D} mm taper head "
        f"({fits.for_material(fits.FREE, 'asa'):.2f} FREE for ASA, plus "
        f"2 x {e.SCREW_HEAD_SINK} of deliberate sink)",
    )
    r.check(
        not is_solid_at(cap, u, v, 0.05),
        "seat is open at the outer face",
    )
    # The taper: a 90 deg head is 45 deg per side, so at any depth into the seat
    # the cone's radius has dropped by exactly that depth. Sampled either side of
    # the cone's own wall at two depths -- a cylindrical pocket would be solid
    # outside the wall at both, and a cone that came out at the wrong angle would
    # fail one of them.
    for depth in (0.25, 0.75):
        radius = e.SCREW_SEAT_D / 2 - depth
        r.check(
            not is_solid_at(cap, u - (radius - 0.15), v, depth),
            f"seat is still open {depth} mm down, out to r={radius:.2f}",
        )
        r.check(
            is_solid_at(cap, u - (radius + 0.15), v, depth),
            "...and closed again just outside it -- 45 deg, not a counterbore",
        )
    r.check(
        abs(e.SCREW_SEAT_DEPTH - (e.SCREW_SEAT_D - e.SCREW_CLEAR_D) / 2) < 0.001,
        "seat bottoms out exactly where the clearance hole starts",
        f"{e.SCREW_SEAT_DEPTH:.3f} mm deep for a {e.SCREW_SEAT_D:.2f} -> "
        f"{e.SCREW_CLEAR_D} taper, which is what 45 deg per side means",
    )
    # There is no flat pocket floor left to print out over. That was the point of
    # the change, so it is asserted rather than assumed: a counterbore would
    # leave material at the old floor depth just outside the clearance hole.
    # No flat annular floor. Stated as the cone arriving at exactly the
    # clearance hole: just above the seat's bottom it is open a hair wider than
    # the hole, and just outside that it is closed. A counterbore would be open
    # all the way out to its own radius at the same depth. (The first version of
    # this probed *below* the seat and outside the hole and asserted "not solid"
    # there, which is wrong -- that is the floor, and it is meant to be solid.)
    r.check(
        not is_solid_at(cap, u - e.SCREW_CLEAR_D / 2, v, e.SCREW_SEAT_DEPTH - 0.05),
        "seat arrives at the clearance hole",
    )
    r.check(
        is_solid_at(cap, u - e.SCREW_CLEAR_D / 2 - 0.25, v, e.SCREW_SEAT_DEPTH - 0.05),
        "...with no flat annular floor around it",
        "a pan-head counterbore left a 1.075 mm ring of unsupported ceiling here",
    )
    r.check(
        is_solid_at(cap, u - e.SCREW_CLEAR_D / 2 - 0.4, v, e.CAP_T - 0.3),
        "material alongside the clearance hole is solid",
        f"{e.SCREW_FLOOR_T:.2f} mm between the seat and the aluminium -- it was "
        f"1.2, and the port is a continuous channel so nothing caps it",
    )
    r.check(
        abs(e.SCREW_SEAT_DEPTH + e.SCREW_FLOOR_T - e.CAP_T) < 0.001,
        "seat plus floor is the whole flange",
        f"{e.SCREW_SEAT_DEPTH:.3f} + {e.SCREW_FLOOR_T:.3f} = {e.CAP_T}",
    )
    r.check(
        not is_solid_at(cap, u, v, e.CAP_T - 0.2),
        "clearance hole carries on through to the aluminium",
    )
    # ...and the screw actually gets there. Nothing checked this before, and the
    # floor grew twelvefold in this design, so it is precisely the thing that
    # could have quietly stopped being true.
    r.check(
        e.screw_reach() > 3.0,
        "screw still reaches the aluminium",
        f"{e.screw_reach():.2f} mm into the port -- an M2 x {e.SCREW_LEN:.0f} "
        f"countersunk (length measured overall, head included) spending "
        f"{e.SCREW_FLOOR_T:.2f} mm of itself in plastic first",
    )

    # The breakout. Asserted as a bounded range, not merely allowed: below zero
    # the pocket has stopped reaching the flank (someone widened the cap again),
    # above ~0.5 it is eating enough of a 0.5 mm-wall tube's seat to matter.
    breakout = e.screw_breakout()
    r.check(
        0.2 < breakout < 0.5,
        "seat breaks out through the flank, by a bounded amount",
        f"{breakout:.2f} mm past a half-width of "
        f"{e.cap_half_width(c.SCREW_BOSS_Z):.2f} mm",
    )
    half = e.cap_half_width(c.SCREW_BOSS_Z)
    r.check(
        not is_solid_at(cap, half - 0.1, v, e.SCREW_SEAT_DEPTH / 2),
        "...and the scallop is really cut, not just arithmetic",
    )
    r.check(
        is_solid_at(cap, half - 0.1, v, e.CAP_T - 0.2),
        "...but the flank below it is whole",
        "the bite stops where the seat does, 1.10 mm in, so the 14.75 mm of "
        "flank under it is unbroken -- it used to stop 14.65 mm in",
    )
    # The seams the breakout leaves are filleted now. They used to be a stated
    # exception ("breaking those would only widen the bite"); that argument is
    # retired. screw_seam_edges returns what is still sharp in the seat's
    # neighbourhood, so an empty result IS the assertion that the fillet took --
    # and it went red at 0.25, where the roll ran below the bed plane.
    still_sharp = e.screw_seam_edges(cap)
    slivers = [x for x in still_sharp if interior_angle(cap, x) is None]
    r.check(
        len(still_sharp) == len(slivers),
        "every measurable seam at the seats is broken",
        f"{len(still_sharp)} sharp edges left, {len(slivers)} of them slivers "
        f"no probe can measure; {e.SCREW_SEAM_FILLET} mm fillet",
    )
    r.check(
        len(slivers) <= 2 and all(x.length < 1.0 for x in slivers),
        "...and the slivers are the tail of the breakout, nothing more",
        f"{[round(x.length, 3) for x in slivers]} mm long -- where the seat's "
        f"cone leaves the flank all but tangentially, one per side. OCC will "
        f"not roll these; they are named here rather than left unexplained",
    )


def check_gland(cap: Part, r: Report) -> None:
    """The M12 bore: on the cap's own centre, and driven clear through."""
    r.section("Gland bore")
    z_mid = e.CAP_T / 2
    # Cap-local x is the profile's u; cap-local y is the profile's z. The gland
    # is on the cap's centre now, so that is (0, 0).
    r.check(
        abs(e.GLAND_Z - c.HEIGHT / 2) < 0.001,
        "bore is on the cap's centre",
        f"z {e.GLAND_Z} = HEIGHT / 2",
    )
    r.check(not is_solid_at(cap, 0, _loc(e.GLAND_Z), z_mid), "bore is open")
    r.check(
        is_solid_at(cap, 0, _loc(e.GLAND_Z) - e.GLAND_MAJOR_D / 2 - 1.0, z_mid),
        "solid below the bore",
    )

    # Wall to the outside of the cap, measured to the nearest arc centre.
    arc_z = c.BOT_ARC_Z if e.GLAND_Z < c.BOT_ARC_Z else c.TOP_ARC_Z
    reach = hypot(0, e.GLAND_Z - arc_z) + e.GLAND_MAJOR_D / 2
    wall = (c.WIDTH / 2 + e.CAP_PROUD) - reach
    r.check(wall > 1.6, "wall outboard of the bore", f"{wall:.2f} mm")

    # Nothing is left standing in the bore, over the *whole* part rather than
    # just the flange. The bore is driven through the flange and the plug's
    # hollow carries the axis on from there -- so this stays true for a reason
    # it did not used to have, and would go on passing if the hollow closed up
    # behind it, which is what check_plug_shell is for. This is the instruction
    # "don't put any material in the way of the M12 hole", read off the solid.
    total = e.CAP_T + e.PLUG_DEPTH
    # Derived rather than a hand-written list of tenths: the flange doubled when
    # the strap slot arrived, and a fixed list would have quietly stopped
    # sampling the plug at all while still reporting ten open stations.
    stations = [
        0.2,
        e.GLAND_COLLAR,
        e.GLAND_MALE_L / 2,
        e.GLAND_MALE_L + 0.2,
        e.CAP_T / 2,
        sum(e.strap_slot_z()) / 2,
        e.CAP_T - 0.2,
        e.CAP_T + 0.2,
        e.CAP_T + e.PLUG_DEPTH / 2,
        total - 0.2,
    ]
    blocked = [z for z in stations if is_solid_at(cap, 0, _loc(e.GLAND_Z), z)]
    r.check(
        not blocked,
        "bore axis is clear end to end, flange and plug alike",
        f"blocked at z={blocked}" if blocked else f"{len(stations)} stations, all open",
    )
    # Sampled off-axis too, at 80% of the bore radius on the plug's side --
    # that is where a plug that merely dodged the bore would still show up.
    plug_probe = e.CAP_T + e.PLUG_DEPTH / 2
    r.check(
        not is_solid_at(
            cap, 0, _loc(e.GLAND_Z) - 0.8 * e.GLAND_MAJOR_D / 2, plug_probe
        ),
        "...including the crescent the plug would otherwise fill",
        f"probed {0.8 * e.GLAND_MAJOR_D / 2:.2f} mm below the axis, mid-plug",
    )

    # What the centred axis costs, stated as a number rather than left implicit:
    # the cavity's ceiling is below the bore, so only a slot of the bore looks
    # into the tube, and that slot is narrower than the cable the gland seals
    # on. The gland is a fitting on a centred axis; it is not a cable route.
    slot = e.cavity_slot_h()
    r.check(
        slot < mc.CABLE_OD,
        "bore does NOT open a cable route into the wiring cavity",
        f"{slot:.2f} mm of the bore looks into the cavity, against a "
        f"{mc.CABLE_OD} mm cable -- see endcap.py's module docstring",
    )

    # Thread engagement. The rule of thumb wants 1.0 x D of printed thread; the
    # gland's own male thread is 8 mm, so 1.0 x D was never reachable and the
    # flange is sized to the gland instead. GLAND_COLLAR eats one pitch of that.
    ratio = e.GLAND_THREAD_L / e.GLAND_THREAD_D
    r.check(
        e.GLAND_THREAD_L > 4 * e.GLAND_PITCH,
        "thread engagement",
        f"{e.GLAND_THREAD_L} mm = {ratio:.2f} x D = "
        f"{e.GLAND_THREAD_L / e.GLAND_PITCH:.1f} turns; the gland's own thread "
        f"is {gland_mod.THREAD_L} mm and it seals on its flange",
    )
    r.check(
        abs(e.GLAND_THREAD_L + e.GLAND_COLLAR - e.GLAND_MALE_L) < 0.001,
        "...and it fills the gland's reach behind the collar",
        f"{e.GLAND_COLLAR} plain + {e.GLAND_THREAD_L} cut = {e.GLAND_MALE_L} "
        f"of male thread (not {e.CAP_T} of flange -- the rest is plain bore)",
    )
    # And the bore behind the thread really is plain, rather than the thread
    # having quietly followed the flange when it got deeper. Sampled at the
    # crest radius, where a thread would show and a plain bore cannot -- and
    # inside ``POCKET_COLLAR``, which is all the plain bore there is now: the
    # relief pocket takes the rest of that column out, so a probe at the old
    # station (midway to CAP_T) would stand in the pocket and report "not
    # threaded" about a place with no bore wall at all.
    r.check(
        not is_solid_at(
            cap,
            e.GLAND_MAJOR_D / 2 - 1.0825 * e.GLAND_PITCH / 2 + 0.25,
            _loc(e.GLAND_Z),
            e.GLAND_MALE_L + e.POCKET_COLLAR / 2,
        ),
        "...and the bore behind it is plain, not threaded",
        f"probed at z={e.GLAND_MALE_L + e.POCKET_COLLAR / 2:.2f}, inside the "
        f"{e.POCKET_COLLAR} mm of plain bore between the thread and the "
        f"pocket's chamfer",
    )
    # Cable has to fit through the thread's crests.
    minor = e.GLAND_MAJOR_D - 1.0825 * e.GLAND_PITCH
    r.check(
        minor > 7.5,
        "cable clears the thread crests",
        f"minor dia {minor:.2f} mm vs {mc.CABLE_OD} cable",
    )
    # The thread is really cut, not merely constructed: walk the crest radius up
    # the flange and expect material at pitch intervals. A thread that failed to
    # fuse leaves the bore a plain cylinder, which no envelope check would see.
    r_crest = e.GLAND_MAJOR_D / 2 - 1.0825 * e.GLAND_PITCH / 2 + 0.25
    # Bounded by where the thread actually stops, not by the flange: the two
    # were the same number until the strap slot deepened the cap, and walking
    # past GLAND_MALE_L only samples plain bore and reports missing crests.
    thread_top = e.GLAND_COLLAR + e.GLAND_THREAD_L
    turns = [
        z
        for z in [
            e.GLAND_COLLAR + 0.25 + 0.25 * i for i in range(int(4 * e.GLAND_MALE_L))
        ]
        if z < thread_top and is_solid_at(cap, r_crest, _loc(e.GLAND_Z), z)
    ]
    r.check(
        len(turns) >= 3 * int(e.GLAND_THREAD_L / e.GLAND_PITCH),
        "thread crests are actually in the bore",
        f"{len(turns)} sampled stations carry material at r={r_crest:.2f}",
    )


def _stadium_clearance(x: float, y: float, half_w: float, half_h: float) -> float:
    """Perpendicular distance from a point to a stadium's boundary, from inside.

    Not the half-width at that height, which is the tempting shortcut and
    overstates the margin badly anywhere off the straight band: at the top of
    the pocket the horizontal reach to the flank is 11.2 mm while the wall
    actually left is 6.4. Measured to the nearest arc centre instead, which is
    what the wall is.
    """
    band = half_h - half_w
    return half_w - (abs(x) if abs(y) <= band else hypot(x, abs(y) - band))


def check_gland_pocket(cap: Part, r: Report) -> None:
    """The relief pocket: what it took out, and what it left standing.

    Read off the outline and off the solid, because the two can disagree in
    both directions -- a pocket whose sketch is right but whose cut never
    reached the plug leaves the part heavier than the constants claim, and a
    pocket that closed on the strap slot leaves a part that is lighter than it
    should be and broken where it matters.
    """
    r.section("Endcap relief pocket")

    # --- the outline, against every neighbour it could reach ----------------
    #
    # Sampled off the real wire rather than off the three constants, so the
    # corner fillets and the arc between the flats are included: a margin that
    # only holds at the flats is not the margin.
    # ty reads Sketch.wires()'s own self as Mixin1D and rejects the call; the
    # same suppression is already on part.edges() elsewhere in this family.
    wire = e.pocket_section().wires()[0]  # ty: ignore[invalid-argument-type]
    pts = [wire @ (i / 720) for i in range(720)]

    v = _loc(c.SCREW_BOSS_Z)
    screw = (
        min(hypot(abs(p.X) - c.SCREW_SPACING / 2, p.Y - v) for p in pts)
        - e.SCREW_CLEAR_D / 2
    )
    r.check(
        screw >= e.POCKET_CLEAR - 1e-6,
        "pocket keeps its clearance to the screw holes",
        f"{screw:.2f} mm of wall to a {e.SCREW_CLEAR_D} mm clearance hole, "
        f"against {e.POCKET_CLEAR} asked for",
    )

    slot_roof = e.STRAP_SLOT_Y + e.STRAP_SLOT_H / 2
    web = min(p.Y for p in pts) - slot_roof
    r.check(
        web >= e.POCKET_WEB - 1e-6,
        "...and more than that to the strap slot's roof",
        f"{web:.2f} mm above a slot whose roof is at y={slot_roof:.2f}; the "
        f"slot spans the full width, so this is the one that binds below",
    )
    # ...and the web is paid for by the slot's own position rather than out of
    # the pocket. Asserted because the two moved together and only the pair is
    # right: STRAP_ROOF opened up by exactly what the pocket needed over the
    # slot, and check_strap_slot holds the floor that paid for it at 3 mm.
    r.check(
        e.strap_roof() >= e.POCKET_WEB,
        "...and the slot moved down to pay for that web, not the pocket",
        f"STRAP_ROOF {e.strap_roof():.2f} mm between the slot and the bore, of "
        f"which {e.POCKET_WEB} is full-depth flange under the pocket; "
        f"{e.strap_floor():.2f} mm left below the slot",
    )

    # The floor keeps a landing outboard of the chamfer's rim. This is the
    # tangency check: the danger is not the bore itself but its lead-in, and a
    # pocket wall that creeps in to meet that rim leaves a feather edge rather
    # than a floor. Measured at the outline's closest approach to the axis,
    # which is the bottom edge -- the one POCKET_WEB moves.
    rim = e.GLAND_MAJOR_D / 2 + e.POCKET_LEAD
    landing = min(hypot(p.X, p.Y) for p in pts) - rim
    r.check(
        landing >= 0.5,
        "floor keeps a landing outboard of the chamfer's rim",
        f"{landing:.2f} mm of flat at the tightest point, past a rim at "
        f"r={rim:.2f} -- and the pocket surrounds the bore rather than "
        f"grazing it",
    )

    outside = min(_stadium_clearance(p.X, p.Y, e.CAP_W / 2, e.CAP_H / 2) for p in pts)
    r.check(
        outside >= e.POCKET_WALL - 1e-6,
        "...and POCKET_WALL of shell to the outside of the flange",
        f"{outside:.2f} mm at the tightest point of the outline, against "
        f"{e.POCKET_WALL} asked for -- this one is a wall, not a gap: it is "
        f"what the screws clamp against the extrusion",
    )

    # The plug is narrower than the flange, so it gets its own pass -- over the
    # part of the outline that is actually inside it.
    y_chord = _loc(e.plug_top_z())
    plug_pts = [p for p in pts if p.Y <= y_chord]
    plug = min(
        _stadium_clearance(
            p.X,
            p.Y,
            (c.WIDTH - 2 * c.WALL - e.PLUG_FIT) / 2,
            (c.HEIGHT - 2 * c.WALL - e.PLUG_FIT) / 2,
        )
        for p in plug_pts
    )
    r.check(
        plug >= e.POCKET_CLEAR - 1e-6,
        "...and at least POCKET_CLEAR to the outside of the plug",
        f"{plug:.2f} mm, over the {len(plug_pts)} sampled points below the "
        f"plug's flat top at y={y_chord:.2f}. Held to the clearance and not to "
        f"POCKET_WALL on purpose: the plug is narrower than the flange by "
        f"{(e.CAP_W - (c.WIDTH - 2 * c.WALL - e.PLUG_FIT)) / 2:.2f} mm a side "
        f"and stands inside the tube, clamping nothing",
    )

    # --- the floor ----------------------------------------------------------
    r.check(
        abs(e.POCKET_FLOOR_Z - (e.GLAND_MALE_L + e.POCKET_COLLAR + e.POCKET_LEAD))
        < 1e-9
        and e.POCKET_COLLAR >= e.GLAND_PITCH,
        "floor stops a collar and a lead-in above the thread",
        f"thread ends at z={e.GLAND_MALE_L}, chamfer starts at "
        f"{e.POCKET_FLOOR_Z - e.POCKET_LEAD:.2f}, floor at {e.POCKET_FLOOR_Z:.2f} "
        f"-- {e.POCKET_COLLAR} mm of plain bore between the two, the same rule "
        f"GLAND_COLLAR follows at the other end",
    )
    r.check(
        e.pocket_depth() > 0,
        "and it takes real depth out of the flange",
        f"{e.pocket_depth():.2f} mm of {e.CAP_T} mm flange, plus the whole "
        f"{e.PLUG_DEPTH} mm of plug where the pocket runs through it",
    )

    # --- and the same thing, read off the solid ------------------------------
    y_probe = e.GLAND_MAJOR_D / 2 + 0.5  # clear of the bore, inside the pocket
    r.check(
        not is_solid_at(cap, 0.0, y_probe, e.CAP_T - 0.2)
        and not is_solid_at(cap, 0.0, y_probe, e.POCKET_FLOOR_Z + 0.2),
        "pocket is open, floor to the flange's inner face",
        f"probed on the bore's axis at y={y_probe:.2f}",
    )
    r.check(
        is_solid_at(cap, 0.0, y_probe, e.POCKET_FLOOR_Z - 0.3),
        "...and the floor under it is solid",
    )
    y_web = e.POCKET_Y_LOW - e.POCKET_WEB / 2
    r.check(
        is_solid_at(cap, 0.0, y_web, e.CAP_T - 0.2)
        and is_solid_at(cap, 0.0, y_web, e.POCKET_FLOOR_Z + 0.2),
        "web to the strap slot is really there",
        f"material at y={y_web:.2f}, midway between the pocket's bottom edge "
        f"and the slot's roof, at both the flange's inner face and the floor",
    )
    r.check(
        is_solid_at(
            cap,
            e.POCKET_X + e.POCKET_CLEAR / 2,
            _loc(c.SCREW_BOSS_Z),
            e.CAP_T - 0.2,
        ),
        "...and so is the wall between the pocket and a screw hole",
    )

    # The lead-in chamfer at the floor's inner rim: inside the cone is air, and
    # a hair outboard of it, at the same height, is not.
    z_cone = e.POCKET_FLOOR_Z - e.POCKET_LEAD / 2
    r_cone = e.GLAND_MAJOR_D / 2 + e.POCKET_LEAD / 2
    r.check(
        not is_solid_at(cap, r_cone - 0.15, 0.0, z_cone)
        and is_solid_at(cap, r_cone + 0.15, 0.0, z_cone),
        "floor's rim into the bore is chamfered, not left square",
        f"{e.POCKET_LEAD} mm cone, probed at r={r_cone:.2f}, z={z_cone:.2f}",
    )
    # ...and it is a ring, all the way round, rather than the part of one that
    # a cone clipped to a pocket smaller than itself would leave. Probed on the
    # bore's low side, which is where the pocket's own boundary is nearest.
    r.check(
        not is_solid_at(cap, 0.0, -(r_cone - 0.15), z_cone)
        and is_solid_at(cap, 0.0, -(r_cone + 0.15), z_cone),
        "...and the chamfer runs right round the rim",
        f"same pair of probes on the bore's low side, where the pocket wall is "
        f"{min(hypot(p.X, p.Y) for p in pts) - e.GLAND_MAJOR_D / 2:.2f} mm out",
    )


def check_plug_shell(cap: Part, r: Report) -> None:
    """The plug is a wall of ``PLUG_WALL``, and everything inboard of it is air.

    Read off the solid throughout, and in more than one place, because this is
    exactly the claim an outline cannot make: the hollow's sketch being right
    says nothing about whether the cut reached the plug, and the part stays a
    valid single solid either way. The bottom of the arc is the probe that
    matters -- it is where the old solid plug was thickest, and where a hollow
    that quietly stopped at the relief pocket's own floor would leave it.
    """
    r.section("Endcap plug shell")

    y_chord = _loc(e.plug_top_z())
    x_seam = e.plug_void_half_width()
    z_plug = e.CAP_T + e.PLUG_DEPTH / 2
    # The plug's outer surface, bottom of the arc: cavity less the running fit.
    plug_bot = -(c.HEIGHT - 2 * c.WALL - e.PLUG_FIT) / 2

    r.check(
        e.plug_bore_half_width() < x_seam,
        "the hollow is wider than the bore's crescent through the plug",
        f"seams at {x_seam:.2f} mm, where the bore alone would leave them at "
        f"{e.plug_bore_half_width():.2f} -- so the bore never reaches the "
        f"plug's wall and the crescent is a clean {e.PLUG_WALL} mm all round",
    )
    y_plug = y_chord - 0.3
    r.check(
        not is_solid_at(cap, 0.0, y_plug, z_plug)
        and not is_solid_at(cap, x_seam - 0.5, y_plug, z_plug)
        and is_solid_at(cap, x_seam + e.PLUG_WALL / 2, y_plug, z_plug),
        "plug is hollow, and the wall starts where the seams are",
        f"open on the axis and at x={x_seam - 0.5:.2f}, solid at "
        f"x={x_seam + e.PLUG_WALL / 2:.2f}, mid-plug at z={z_plug:.2f}",
    )
    r.check(
        is_solid_at(cap, 0.0, plug_bot + e.PLUG_WALL / 2, z_plug)
        and not is_solid_at(cap, 0.0, plug_bot + e.PLUG_WALL + 0.5, z_plug),
        f"...and it is {e.PLUG_WALL} mm at the bottom of the arc",
        f"solid at y={plug_bot + e.PLUG_WALL / 2:.2f}, open at "
        f"y={plug_bot + e.PLUG_WALL + 0.5:.2f}. This column was solid from "
        f"y={plug_bot:.2f} up to the pocket's floor at y={e.POCKET_Y_LOW}, "
        f"{e.POCKET_Y_LOW - plug_bot:.2f} mm of it, before the plug was a shell",
    )
    # The hollow stops at CAP_T on purpose -- that face is the seat the screws
    # clamp against the aluminium, and it is not the relief pocket's to take.
    r.check(
        is_solid_at(cap, 0.0, plug_bot + e.PLUG_WALL + 0.5, e.CAP_T - 0.3),
        "...and it stops at the flange's seat face, which stays solid",
        f"material at z={e.CAP_T - 0.3:.2f} directly under the hollow, where "
        f"the flange beds against the extrusion's {c.WALL} mm wall",
    )
    # The tip keeps a land: PLUG_LEAD_IN comes out of PLUG_WALL, so the two are
    # one number split, and a lead-in typed independently would eat the wall.
    r.check(
        abs((e.PLUG_LEAD_IN + e.PLUG_TIP_LAND) - e.PLUG_WALL) < 1e-9
        and e.PLUG_TIP_LAND >= 1.2,
        "tip's lead-in is taken out of the wall, not out of thin air",
        f"{e.PLUG_LEAD_IN} mm of chamfer leaves {e.PLUG_TIP_LAND} mm of land "
        f"on a {e.PLUG_WALL} mm wall -- 3 perimeters at 0.4 mm",
    )
    # ...and the land is really there. The chamfer is taken on the *outer*
    # wire, so it eats the wall from the outside in: at ``d`` below the tip the
    # outer surface has already come in by PLUG_LEAD_IN - d, and the land is
    # what is left between that facet and the hollow's inside. Probing at the
    # outer surface's nominal position would land in the chamfer's own air,
    # which is the mistake this comment exists to stop being made again.
    tip = e.CAP_T + e.PLUG_DEPTH
    d = 0.15
    plug_in = plug_bot + e.PLUG_WALL
    facet = plug_bot + (e.PLUG_LEAD_IN - d)
    r.check(
        is_solid_at(cap, 0.0, (facet + plug_in) / 2, tip - d)
        and not is_solid_at(cap, 0.0, facet - 0.2, tip - d),
        "...and the land is really there at the tip",
        f"solid at y={(facet + plug_in) / 2:.2f} and air at y={facet - 0.2:.2f}, "
        f"{d} mm below the tip -- the lead-in's facet has come in to "
        f"y={facet:.2f} by there, leaving {plug_in - facet:.2f} mm standing",
    )


def check_strap_slot(cap: Part, r: Report, section: str = "Endcap strap slot") -> None:
    """The 12 mm velcro strap goes through, and takes nothing with it.

    Runs against the wired cap too (``section`` keeps the two report blocks
    apart): its outer 15.85 mm is the standard cap's flange verbatim, so the
    slot sits at the same coordinates and every probe here transfers -- the
    "closed toward the seat" wall is simply deeper there.

    Read off the solid rather than off the constants, because the slot is cut on
    ``Plane.YZ`` and a section built on that plane instead of returned local
    gets its transform applied twice -- which cuts the slot cleanly *outside*
    the part and leaves a valid solid, the right bounding box and no slot. That
    shipped once during this feature's own development, so the first thing here
    is a probe that a plain envelope check cannot pass by accident.
    """
    r.section(section)
    z_lo, z_hi = e.strap_slot_z()
    z_mid = (z_lo + z_hi) / 2
    y = e.STRAP_SLOT_Y
    half_lo, half_hi = e.strap_mouth_half_width()

    r.check(
        abs((z_hi - z_lo) - e.STRAP_SLOT_W) < 0.001,
        "slot takes the strap's width along the tube",
        f"{z_hi - z_lo:.2f} mm for a {e.STRAP_W} mm strap "
        f"({fits.for_material(fits.FREE, 'asa'):.2f} FREE for ASA)",
    )
    r.check(not is_solid_at(cap, 0.0, y, z_mid), "slot is open on the centre line")

    # Open all the way across, sampled at eight stations rather than at the
    # middle: a slot that failed to reach one flank is still open at x=0.
    span = [
        -half_lo + 0.3,
        -7.0,
        -4.0,
        -1.5,
        1.5,
        4.0,
        7.0,
        half_lo - 0.3,
    ]
    blocked = [x for x in span if is_solid_at(cap, x, y, z_mid)]
    r.check(
        not blocked,
        "...and open flank to flank, so the strap threads through",
        f"blocked at x={blocked}" if blocked else f"{len(span)} stations, all open",
    )

    # Closed at both ends along the cap's axis. This is what keeps the strap
    # captive and what leaves the tube's wall seat at CAP_T unbroken.
    r.check(
        is_solid_at(cap, 0.0, y, z_lo - e.STRAP_WALL / 2),
        "closed toward the outer face",
        f"{e.STRAP_WALL} mm of wall, slot starts at z={z_lo:.2f}",
    )
    r.check(
        is_solid_at(cap, 0.0, y, z_hi + e.STRAP_WALL / 2),
        "...and toward the seat, so the tube's wall still beds on solid",
        f"{e.STRAP_WALL} mm of wall, slot stops at z={z_hi:.2f} of {e.CAP_T}",
    )

    # The loaded member: the web between the slot's roof and the gland bore.
    r.check(
        e.strap_roof() >= 2.5,
        "web between the slot and the gland bore",
        f"{e.strap_roof():.2f} mm -- what the strap pulls on",
    )
    r.check(
        is_solid_at(cap, 0.0, y + e.STRAP_SLOT_H / 2 + 0.3, z_mid)
        and is_solid_at(cap, 0.0, -e.GLAND_MAJOR_D / 2 - 0.3, z_mid),
        "...and it is really there, top and bottom",
    )
    r.check(
        e.strap_floor() >= 3.0,
        "material below the slot",
        f"{e.strap_floor():.2f} mm to the bottom of the shell",
    )
    r.check(
        is_solid_at(cap, 0.0, y - e.STRAP_SLOT_H / 2 - 0.3, z_mid),
        "...and it is really there too",
    )

    # Nowhere near either screw feature -- asserted rather than eyeballed off a
    # drawing, since both are driven from config and could move.
    gap = (y + e.STRAP_SLOT_H / 2) - (_loc(c.SCREW_BOSS_Z) - e.SCREW_SEAT_D / 2)
    r.check(
        gap < -1.0,
        "slot clears the screw pockets",
        f"{-gap:.2f} mm below the lowest point of a pocket",
    )
    r.check(
        is_solid_at(cap, c.SCREW_SPACING / 2, y, z_mid) is False
        or not is_solid_at(cap, c.SCREW_SPACING / 2, _loc(c.SCREW_BOSS_Z), z_mid),
        "...and the screw hole is still its own hole",
    )

    # The mouths. The slot breaks out through a *curved* flank, so the two are
    # not at one half-width -- which is why they get an OCC fillet rather than a
    # boolean frustum, no single frustum being able to break both evenly.
    r.check(
        half_hi > half_lo,
        "mouths sit on the shell's arc, not on a flat",
        f"half-width runs {half_lo:.2f} to {half_hi:.2f} mm up the mouth",
    )
    r.check(
        not is_solid_at(cap, half_lo - 0.2, y, z_mid)
        and not is_solid_at(cap, -(half_lo - 0.2), y, z_mid),
        "slot really breaks out through both flanks",
    )
    # The fillet, measured as an angle rather than by point probes. Both mouths
    # sit *on* the shell, which curves away from them, so every point a probe
    # could stand at just outside a nominal corner is either already inside the
    # slot or already outside the part: the first version of this check probed
    # 0.9 mm beyond the shell and failed for that reason rather than for any
    # fault in the geometry. The angle is the property that actually matters and
    # it is not marginal -- raw, the floor edge is where the slot's flat wall
    # meets a flank curving away from it and measures about 50 deg; filleted, it
    # is tangency.
    mouth = e.strap_mouth_edges(cap)
    angles = [interior_angle(cap, ed) for ed in mouth]
    measured = [a for a in angles if a is not None]
    sharpest = f"{min(measured):.1f} deg" if measured else "nothing measurable"

    r.check(
        len(mouth) >= 4,
        "mouth edges are where the slot says they are",
        f"{len(mouth)} edges inside the slot's own y/z envelope, out at a flank",
    )
    # The unmeasurable ones are the whole point, and this is the check that
    # names *which* edges and *why* when nothing else could. Left raw, the
    # slot's floor meets a flank curving away from it at about 50 deg, and
    # ``interior_angle`` cannot stand a probe inside a wedge that thin: it
    # returns None. ``sharp_convex_edges`` now reports a None edge too, in its
    # ``unclassifiable`` bucket rather than dropping it -- but only as "an
    # edge somewhere on this part could not be measured"; it has no idea this
    # is the strap mouth, or that six of the eight raw mouth edges are the
    # ones responsible. That specificity is this check's job, not the
    # audit's. A treated mouth measures cleanly either way.
    r.check(
        not [a for a in angles if a is None],
        "...and every one is blunt enough to measure at all",
        f"{len(measured)} of {len(angles)} measurable; a feather edge comes "
        f"back None here just as it would from sharp_convex_edges' own "
        f"unclassifiable bucket, only with this check's mouth-specific detail",
    )
    r.check(
        bool(angles) and all(a is not None and a > 120.0 for a in angles),
        "both mouths are broken, not left raw",
        f"sharpest mouth edge {sharpest} after a {e.STRAP_MOUTH_R} mm fillet "
        f"-- the strap drags over these every time it is threaded",
    )


def check_endcap_edges(cap: Part, r: Report) -> None:
    """The cap's two chamfers are broken, not merely asked for.

    ``chamfer_edge`` swallows an OCC refusal by design, and a chamfer that never
    applied is invisible in a projection, so each treatment is read back off the
    solid: one sample inside the material it should have removed, one just
    beyond that must still be solid. An op that ran too small fails the first,
    one that ate the part fails the second.

    There were three. The collar chamfer is gone with the collar: the cap is
    flush with the tube now, so there is no step at ``CAP_T`` to break, and a
    chamfer there would only open a gap the extrusion's 0.5 mm wall has to span.
    """
    r.section("Endcap edges")
    half_h = e.CAP_H / 2
    ch, li = e.EDGE_CHAMFER, e.PLUG_LEAD_IN

    # Bed face, sampled down the bottom arc -- clear of both screw pockets.
    r.check(
        not is_solid_at(cap, 0.0, -(half_h - 0.25 * ch), 0.25 * ch),
        "bed face chamfered -- no elephant's foot",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(cap, 0.0, -(half_h - 2 * ch), 0.25 * ch),
        "...and no more than that",
    )

    # The cap face at CAP_T is square, and has to stay square: it is the seat
    # the extrusion's 0.5 mm wall stands on, edge to edge now that the cap is
    # flush. An absence check, because a chamfer here would pass silently.
    r.check(
        is_solid_at(cap, e.CAP_W / 2 - 0.1, 0.0, e.CAP_T - 0.05),
        "cap face is square at the flank -- the tube's wall seat",
        "flush cap: the whole face is seat, so nothing up here gets a bevel",
    )

    # The plug's lead-in, down the bottom of its arc. Shrinking a stadium leaves
    # its arc centres where they were, so the plug's lower arc is still the
    # profile's, at _loc(BOT_ARC_Z).
    tip = e.CAP_T + e.PLUG_DEPTH
    arc_cy = _loc(c.BOT_ARC_Z)
    plug_r = c.RADIUS - c.WALL - e.PLUG_FIT / 2
    r.check(
        not is_solid_at(cap, 0.0, arc_cy - (plug_r - 0.25 * li), tip - 0.25 * li),
        "plug's leading edge has a lead-in",
        f"{li} mm, vs {e.PLUG_FIT / 2:.2f} mm of radial clearance",
    )
    r.check(
        is_solid_at(cap, 0.0, arc_cy - (plug_r - 2 * li), tip - 0.25 * li),
        "...and the plug's tip is still there",
    )
    # The corners that lead-in leaves where its facets meet. At 0.4 they were
    # sub-millimetre; at 2.0 they are 2-3 mm and there are four of them, so
    # they are rolled rather than named. Read back with the same selector that
    # fed the fillet: an empty answer is the assertion that it took. This is a
    # ladder (0.5 is refused here, 0.3 takes), and it is the ladder that makes
    # the check worth having -- a silent drop to a smaller radius is fine, a
    # silent skip of every rung is not, and both look identical in a render.
    corners = e.plug_tip_corner_edges(cap)
    r.check(
        not corners,
        "...and the corners its facets leave are rolled, not raw",
        "nothing sharp left in the chamfer's own band"
        if not corners
        else f"{len(corners)} left: "
        + "; ".join(f"{ed.geom_type} len={ed.length:.2f}" for ed in corners),
    )

    # The hollow's own rim gets a matching lead-in now (endcap.py's module
    # docstring): the void's boundary grows outward toward the tip the same
    # way the outer wire's shrinks, so a cable finds a wider mouth rather than
    # a square lip. Same probe shape as the outer pair, mirrored across the
    # wall: not solid where the chamfer has widened the hollow, solid where
    # it clearly has not reached.
    void_r = plug_r - e.PLUG_WALL
    r.check(
        not is_solid_at(cap, 0.0, arc_cy - (void_r + 0.25 * li), tip - 0.25 * li),
        "...and the hollow's own rim has a matching lead-in",
        f"{li} mm on the inside too, widening toward the tip",
    )
    r.check(
        is_solid_at(cap, 0.0, arc_cy - (void_r + 2 * li), tip - 0.25 * li),
        "...and the wall between the two chamfers is still there",
    )

    # The raw-edge rule (AGENTS.md), made falsifiable: every convex edge left
    # without a chamfer or fillet has to be a *stated* exception, not merely
    # unnoticed. The endcap's own module docstring names them: the thread's
    # helix (not a straight or circular edge to begin with), the whole of the
    # CAP_T face (the tube's wall seat, with the bore's faded thread exit on
    # it), and the two seams where a screw pocket cuts out through the flank.
    # The plug tip's inner wire used to be on this list too, back when
    # PLUG_LEAD_IN only treated the outer one -- it is chamfered now
    # (_plug_void_tip_edges), so there is nothing left here to name.
    screw_u = c.SCREW_SPACING / 2

    def _is_isothread_helix(edge) -> bool:
        return edge.geom_type == GeomType.BSPLINE

    def _is_cap_t_face_edge(edge) -> bool:
        bb = edge.bounding_box()
        return abs(bb.min.Z - e.CAP_T) < 0.02 and abs(bb.max.Z - e.CAP_T) < 0.02

    def _is_screw_seat_sliver(edge) -> bool:
        # The tail of a seat's breakout: out near a flank, level with the ports,
        # inside the seat's own 1.10 mm depth. Nothing else in the part is
        # there. This is a much smaller claim than the entry it replaces, which
        # excused the whole scallop -- the scallop is filleted now, and what is
        # left is one short line per side, under a millimetre.
        bb = edge.bounding_box()
        centre = bb.center()
        return (
            abs(centre.X) > screw_u - e.SCREW_SEAT_D / 2
            and bb.max.Z < e.SCREW_SEAT_DEPTH + 0.02
            and abs(centre.Y - _loc(c.SCREW_BOSS_Z)) < e.SCREW_SEAT_D
            and edge.length < 1.0
        )

    def _is_periodic_bore_seam(edge) -> bool:
        # sharp_convex_edges now reports the None edges min_length used to
        # let through unseen (see its docstring), and three of this cap's are
        # new to this file for that reason -- not new to the geometry, only
        # to what could be said about it. Each is a straight LINE that opens
        # through the CAP_T face and runs down a bore or pocket wall: the
        # screw seats' own 45 deg cones (both sides -- this is the *rest* of
        # the same cone _is_screw_seat_sliver names the sub-mm tail of, not a
        # different feature) and the gland collar's cylindrical wall.
        #
        # ``is_periodic_seam`` does the actual proof, against OCC's own
        # topology rather than position: each of these edges' two "adjacent"
        # faces are the literal same ``TopoDS_Face``, so there is no second
        # surface to take a dihedral angle against, which is exactly why
        # interior_angle answers None here (its documented "not shared by
        # exactly two faces" case) -- not a sign the wedge is too acute to
        # probe, the other documented reason for a None. See that function's
        # own docstring for why this is checked directly instead of inferred
        # from where the edge happens to sit.
        #
        # That test alone is not scope enough on its own (its docstring says
        # so): it would just as happily match the sub-mm screw-seat tail
        # sliver _is_screw_seat_sliver already names with its own, more
        # specific reason. ``bb.max.Z`` at one of the two flat ceilings below
        # narrows this predicate to "opens through a face this part actually
        # has"; requiring more than 1 mm of span rules out both that sub-mm
        # sliver and the *other* CAP_T-adjacent edges this file already names
        # (_is_cap_t_face_edge's, which lie flat *at* CAP_T rather than
        # climbing away from it, so their own span is ~0) -- so the two
        # predicates partition disjointly rather than racing to claim the
        # same edge.
        #
        # There are two ceilings and not one because the relief pocket moved
        # the second of them: the gland collar's wall used to run the whole
        # flange and open through CAP_T, and now it stops at the pocket's
        # chamfer, which is where the pocket takes the rest of that column
        # out. Same seam, same non-edge, two millimetres lower.
        if edge.geom_type != GeomType.LINE:
            return False
        bb = edge.bounding_box()
        tops = (e.CAP_T, e.POCKET_FLOOR_Z - e.POCKET_LEAD)
        if not (
            any(abs(bb.max.Z - top) < 0.02 for top in tops)
            and (bb.max.Z - bb.min.Z) > 1.0
        ):
            return False
        return is_periodic_seam(cap, edge)

    _check_sharp_edges(
        cap,
        "endcap",
        r,
        (
            (
                "IsoThread helix",
                _is_isothread_helix,
                "the gland thread's flanks are a swept helix (geom_type "
                "BSPLINE), not a straight or circular edge -- nothing to "
                "break on a printed thread",
            ),
            (
                "CAP_T face left raw",
                _is_cap_t_face_edge,
                "the whole of the CAP_T face beds against the extrusion's "
                "0.5 mm wall -- the true outer perimeter, the gland bore's own "
                "faded thread exit, the screw clearance holes, and the shelf "
                "where the flange's terrace steps down to the plug's own "
                "narrower continuation, all sit on it. Breaking any of them "
                "would only open a gap that wall has to span. The relief "
                "pocket's own mouth used to be on this list too -- it is "
                "chamfered now (endcap.py's module docstring), since it is "
                "well inboard of where the aluminium's wall actually rests",
            ),
            (
                "screw seat's tail sliver left raw",
                _is_screw_seat_sliver,
                "where the seat's 45 deg cone leaves the flank all but "
                "tangentially, one short line per side. The seams either side "
                "of it are filleted (SCREW_SEAM_FILLET) -- this is the "
                "sub-millimetre tail OCC will not roll, and no probe can even "
                "measure its angle. check_screw_pockets bounds its length",
            ),
            (
                "periodic bore/pocket seam opening through a flat ceiling",
                _is_periodic_bore_seam,
                "the closing seam of a cone or cylinder's own periodic "
                "parametrisation (both screw seats' cones, the gland "
                "collar's wall), where it happens to open through the flat "
                "CAP_T face or the relief pocket's chamfer, which is where "
                "that wall stops now -- not a real material edge at all, "
                "confirmed by "
                "the seam's two 'adjacent' faces being IsSame() in OCC's own "
                "topology map, so there is no second surface for "
                "interior_angle to measure a dihedral angle against",
            ),
        ),
    )


def check_endcap_wired(cap: Part, r: Report) -> None:
    """The wired cap's envelope, and the claims its constants make about it.

    The variant's contract in one sentence: the same cap, 10 mm longer, all of
    it protrusion, screws unchanged, and a cable route through the bottom half
    where the standard cap has none. Each clause of that is an assertion here
    rather than a docstring's word.
    """
    r.section("Wired endcap")
    bb = cap.bounding_box()
    r.check(
        abs(bb.size.X - ew.CAP_W) < 0.01 and abs(bb.size.Y - ew.CAP_H) < 0.01,
        "flange size -- flush with the tube, like the standard cap",
        f"{bb.size.X:.2f} x {bb.size.Y:.2f} mm against a "
        f"{c.WIDTH} x {c.HEIGHT} tube",
    )
    r.check(
        abs(bb.min.Z) < 0.01, "outer face on z=0 (print pose)", f"min z {bb.min.Z:.3f}"
    )
    r.check(
        abs(bb.size.Z - (ew.CAP_T + e.PLUG_DEPTH)) < 0.01,
        "overall depth",
        f"{bb.size.Z:.2f} mm = {ew.CAP_T} flange + {e.PLUG_DEPTH} plug",
    )
    r.check(len(cap.solids()) == 1, "one solid", f"{len(cap.solids())}")

    # The variant's headline numbers, derived rather than typed: the flange is
    # the standard cap's plus EXTRA_T and the plug did not move, so the whole
    # 10 mm is protrusion past the aluminium.
    r.check(
        abs(ew.CAP_T - (e.CAP_T + ew.EXTRA_T)) < 1e-9,
        "flange is the standard cap's plus EXTRA_T -- one number couples them",
        f"{e.CAP_T} + {ew.EXTRA_T} = {ew.CAP_T} mm",
    )
    r.check(
        abs((ew.CAP_T + e.PLUG_DEPTH) - (e.CAP_T + e.PLUG_DEPTH) - ew.EXTRA_T) < 1e-9,
        "exactly EXTRA_T longer than the standard cap, all of it protrusion",
        f"{ew.CAP_T + e.PLUG_DEPTH:.2f} vs {e.CAP_T + e.PLUG_DEPTH:.2f} mm "
        f"overall; the plug is unchanged, so the flange stands "
        f"{ew.EXTRA_T:.0f} mm further out of the tube",
    )
    r.check(
        ew.CAP_T >= e.GLAND_MALE_L,
        "gland unchanged: the flange still swallows all of its male thread",
        f"{ew.CAP_T} mm of flange for {e.GLAND_MALE_L} mm of thread; the "
        f"gland seals on its flange against the outer face, which is where "
        f"it always was",
    )


def check_wired_screws(cap: Part, r: Report) -> None:
    """The access stage: same screws, same reach, sunk EXTRA_T deeper.

    The variant exists under one hard constraint -- the M2 x 20 screws keep
    their length -- so the one number that must not move is ``screw_reach()``,
    and it is asserted as an *identity* against the standard cap rather than
    re-derived. Everything else here reads the two-stage hole off the solid:
    a plain access bore, then the standard cap's 45 deg seat, then the
    clearance hole, with no ledge and no flat floor anywhere in the stack.
    """
    r.section("Wired endcap screws")
    u = c.SCREW_SPACING / 2
    v = _loc(c.SCREW_BOSS_Z)

    r.check(
        abs(ew.screw_reach() - e.screw_reach()) < 1e-9,
        "screw reach is IDENTICAL to the standard cap's",
        f"{ew.screw_reach():.2f} mm into the port from an M2 x "
        f"{e.SCREW_LEN:.0f} -- the access stage is exactly EXTRA_T deep, so "
        f"the head sinks by what the flange grew",
    )
    r.check(
        abs(ew.SCREW_ACCESS_DEPTH - ew.EXTRA_T) < 1e-9,
        "...because the access stage is the flange growth, no more, no less",
        f"{ew.SCREW_ACCESS_DEPTH} mm of plain bore before the seat",
    )
    r.check(
        abs(ew.SCREW_ACCESS_D - e.SCREW_SEAT_D) < 1e-9,
        "access bore is the seat cone's own rim -- bore hands over to cone "
        "with no ledge",
        f"{ew.SCREW_ACCESS_D:.2f} mm, swallowing a {e.SCREW_HEAD_D} mm head "
        f"with the seat's own FREE fit and sink",
    )
    r.check(
        not is_solid_at(cap, u, v, 0.05),
        "bore is open at the outer face",
    )
    # The access stage is a plain cylinder: open just inside its wall and
    # closed just outside, at two depths a cone could not pass both of.
    for depth in (ew.SCREW_ACCESS_DEPTH * 0.25, ew.SCREW_ACCESS_DEPTH * 0.9):
        r.check(
            not is_solid_at(cap, u - (ew.SCREW_ACCESS_D / 2 - 0.15), v, depth),
            f"access bore is full width {depth:.1f} mm down",
        )
        r.check(
            is_solid_at(cap, u - (ew.SCREW_ACCESS_D / 2 + 0.3), v, depth),
            "...and closed just outside it -- a bore, not a pocket",
        )
    # The seat: the standard cap's 45 deg cone, one access stage down. Same
    # two-depth probe pair as check_screw_pockets, shifted by EXTRA_T.
    for depth in (0.25, 0.75):
        radius = e.SCREW_SEAT_D / 2 - depth
        z = ew.SCREW_ACCESS_DEPTH + depth
        r.check(
            not is_solid_at(cap, u - (radius - 0.15), v, z),
            f"seat is open {depth} mm below the access stage, to r={radius:.2f}",
        )
        r.check(
            is_solid_at(cap, u - (radius + 0.15), v, z),
            "...and closed just outside it -- 45 deg, not a counterbore",
        )
    z_seat_end = ew.SCREW_ACCESS_DEPTH + e.SCREW_SEAT_DEPTH
    r.check(
        not is_solid_at(cap, u - e.SCREW_CLEAR_D / 2, v, z_seat_end - 0.05),
        "seat arrives at the clearance hole",
    )
    r.check(
        is_solid_at(cap, u - e.SCREW_CLEAR_D / 2 - 0.25, v, z_seat_end - 0.05),
        "...with no flat annular floor around it",
    )
    r.check(
        not is_solid_at(cap, u, v, ew.CAP_T - 0.2),
        "clearance hole carries on through to the aluminium",
    )
    r.check(
        is_solid_at(cap, u - e.SCREW_CLEAR_D / 2 - 0.4, v, ew.CAP_T - 0.3),
        "screw column alongside the hole is solid at the seat face",
        "the chamber keeps a POCKET_CLEAR column round each hole, and its "
        "top is what the port's boss beds against",
    )

    # The breakout: same diameter as the standard cap's seat, so the same
    # bounded bite -- just standing the access stage tall instead of 1.1 mm.
    breakout = ew.screw_breakout()
    r.check(
        0.2 < breakout < 0.5 and abs(breakout - e.screw_breakout()) < 1e-9,
        "flank breakout is the standard cap's, by construction",
        f"{breakout:.2f} mm past the flank, from bed to the seat's bottom",
    )
    half = e.cap_half_width(c.SCREW_BOSS_Z)
    r.check(
        not is_solid_at(cap, half - 0.1, v, ew.SCREW_ACCESS_DEPTH / 2),
        "...and the scallop is really cut down the access stage",
    )
    r.check(
        is_solid_at(cap, half - 0.1, v, ew.CAP_T - 0.2),
        "...but the flank below the seat is whole",
    )

    # What stays sharp at the seats after the fillet ladder: the cone tails no
    # probe can measure, and the sub-millimetre stubs where the mouth's
    # breakout crosses the bed chamfer -- held out of the roll on purpose,
    # because terminating a fillet on the bed plane drags the part below z=0
    # (endcap.SCREW_SEAM_FILLET's own history). Bounded here so neither kind
    # can quietly grow into a real raw edge.
    still_sharp = ew.screw_seam_edges(cap)
    r.check(
        len(still_sharp) <= 6 and all(x.length < 1.0 for x in still_sharp),
        "raw screw seams are only the named slivers and bed stubs",
        f"{len(still_sharp)} edges, {[round(x.length, 3) for x in still_sharp]} "
        f"mm -- all under a millimetre, none reportable by the audit's 2 mm "
        f"floor, every one either a cone tail (unmeasurable) or a bed stub",
    )
    stub_angles = [
        angle
        for x in still_sharp
        if x.bounding_box().min.Z < 0.05
        and (angle := interior_angle(cap, x)) is not None
    ]
    r.check(
        all(angle > 95.0 for angle in stub_angles),
        "...and the bed stubs are blunter than a square corner",
        f"{len(stub_angles)} stubs, sharpest "
        + (f"{min(stub_angles):.1f} deg" if stub_angles else "none"),
    )


def check_wired_chamber(cap: Part, r: Report) -> None:
    """The chamber: the cable route the standard cap explicitly does not have.

    ``check_gland`` asserts of the standard cap that its bore does *not* open
    a cable route into the wiring cavity -- a 5.5 mm slot against a 6.7 mm
    cable. This is the counterpart: past the floor, the whole bore opens into
    a chamber whose bottom half is the plug channel's own section, walls
    flush, so the cable's path is bore -> chamber -> channel -> tube with
    nothing narrower than the bore itself anywhere on it.
    """
    r.section("Wired endcap chamber")

    # --- the floor, and what fixes it -----------------------------------
    r.check(
        abs(
            ew.CHAMBER_FLOOR_Z
            - max(
                e.POCKET_FLOOR_Z,
                ew.SCREW_ACCESS_DEPTH + e.SCREW_SEAT_DEPTH,
                ew.STRAP_BLOCK_T,
            )
        )
        < 1e-9,
        "floor sits above all three of its tenants",
        f"z={ew.CHAMBER_FLOOR_Z}: the gland wants {e.POCKET_FLOOR_Z} (thread "
        f"+ collar + lead, the same rule the relief pocket follows), the "
        f"screw seats bottom out at "
        f"{ew.SCREW_ACCESS_DEPTH + e.SCREW_SEAT_DEPTH}, and the strap block "
        f"runs to {ew.STRAP_BLOCK_T} -- the one that binds. One plane, three "
        f"holes, no cones poking through",
    )
    r.check(
        ew.CHAMBER_FLOOR_Z - e.strap_slot_z()[1] >= e.STRAP_WALL - 1e-9,
        "...leaving the standard cap's own wall between slot and chamber",
        f"{ew.CHAMBER_FLOOR_Z - e.strap_slot_z()[1]:.2f} mm of web over a "
        f"slot roof at z={e.strap_slot_z()[1]:.2f}, against STRAP_WALL = "
        f"{e.STRAP_WALL} -- the slot must not open into the cable run",
    )
    r.check(
        ew.CHAMBER_FLOOR_Z - e.POCKET_LEAD - (e.GLAND_COLLAR + e.GLAND_THREAD_L)
        >= e.GLAND_PITCH,
        "...and keeps a full pitch of plain bore above the thread",
        f"{ew.CHAMBER_FLOOR_Z - e.POCKET_LEAD - e.GLAND_MALE_L + e.GLAND_COLLAR:.2f}"
        f" mm of collar -- nothing may cut into the thread's own geometry",
    )

    # --- the outline, off the real wire ----------------------------------
    wire = ew.chamber_section().wires()[0]  # ty: ignore[invalid-argument-type]
    pts = [wire @ (i / 720) for i in range(720)]
    rim = e.GLAND_MAJOR_D / 2 + e.POCKET_LEAD
    landing = min(hypot(p.X, p.Y) for p in pts) - rim
    r.check(
        landing >= 0.5,
        "the WHOLE bore opens into the chamber -- floor keeps a landing "
        "outboard of its rim chamfer everywhere",
        f"{landing:.2f} mm at the tightest point (a screw column), past a rim "
        f"at r={rim:.2f} -- against the standard cap, where only a "
        f"{e.cavity_slot_h():.1f} mm slot of the bore looks into the cavity",
    )
    outside = min(_stadium_clearance(p.X, p.Y, ew.CAP_W / 2, ew.CAP_H / 2) for p in pts)
    r.check(
        outside >= ew.CHAMBER_WALL - 0.01,
        "...and CHAMBER_WALL of shell to the outside",
        f"{outside:.2f} mm at the tightest point, against {ew.CHAMBER_WALL} "
        f"asked for -- the shell the screws clamp against the extrusion",
    )
    v = _loc(c.SCREW_BOSS_Z)
    screw = (
        min(hypot(abs(p.X) - c.SCREW_SPACING / 2, p.Y - v) for p in pts)
        - e.SCREW_CLEAR_D / 2
    )
    r.check(
        screw >= e.POCKET_CLEAR - 1e-6,
        "...and POCKET_CLEAR of column round each screw hole",
        f"{screw:.2f} mm of wall to a {e.SCREW_CLEAR_D} mm clearance hole",
    )

    # --- the route, read off the solid -----------------------------------
    z_mid = (ew.CHAMBER_FLOOR_Z + ew.CAP_T) / 2
    stations = [ew.CHAMBER_FLOOR_Z + 0.2, z_mid, ew.CAP_T - 0.2]
    blocked = [z for z in stations if is_solid_at(cap, 0.0, 0.0, z)]
    r.check(
        not blocked,
        "chamber is open on the bore's axis, floor to the inner face",
        f"blocked at z={blocked}" if blocked else f"{len(stations)} stations open",
    )
    r.check(
        not is_solid_at(cap, 0.0, e.GLAND_MAJOR_D / 2 + 1.0, z_mid)
        and not is_solid_at(cap, 0.0, -(e.GLAND_MAJOR_D / 2 + 1.0), z_mid),
        "...and open above AND below the bore -- a chamber, not a slot",
        "the standard cap is solid at both of these probes mid-flange",
    )
    r.check(
        is_solid_at(cap, 0.0, e.GLAND_MAJOR_D / 2 + 0.5, ew.CHAMBER_FLOOR_Z - 0.3),
        "floor under the chamber is solid",
    )
    r.check(
        abs(ew.chamber_run() - ew.EXTRA_T) < 1e-9 and ew.chamber_run() > mc.CABLE_OD,
        "turning room: every millimetre the cap grew, and more than a cable",
        f"{ew.chamber_run():.2f} mm from floor to inner face -- exactly "
        f"EXTRA_T, since the strap block pins the floor at the standard "
        f"cap's flange height -- for a {mc.CABLE_OD} mm cable to bow down "
        f"into the channel",
    )

    # The bottom half IS the channel: the chamber's wall and the plug
    # hollow's are the same offset of the same stadium, so the surface at the
    # bottom of the arc is one flush wall from the floor to the plug's tip.
    y_wall = -(c.HEIGHT - 2 * c.WALL - e.PLUG_FIT) / 2 + e.PLUG_WALL  # -13.02
    run = [ew.CHAMBER_FLOOR_Z + 1, z_mid, ew.CAP_T - 0.5, ew.CAP_T + 1,
           ew.CAP_T + e.PLUG_DEPTH / 2]
    inside_blocked = [z for z in run if is_solid_at(cap, 0.0, y_wall + 0.3, z)]
    wall_missing = [z for z in run if not is_solid_at(cap, 0.0, y_wall - 0.3, z)]
    r.check(
        not inside_blocked and not wall_missing,
        "chamber wall is flush with the plug channel's, floor to tip",
        f"probed either side of y={y_wall:.2f} at {len(run)} stations; "
        + (
            f"blocked inside at {inside_blocked}, wall missing at {wall_missing}"
            if inside_blocked or wall_missing
            else "open inboard, solid outboard at every one"
        ),
    )

    # The screw columns stand in the flange and ONLY in the flange. The probe
    # point is inside the scallop's bite *and* inside the plug's channel --
    # below the chord, inboard of the channel wall -- which is exactly the
    # sliver a chamber cut carried through the plug in one stroke leaves
    # standing as a rib down the channel. That bug shipped once during this
    # cap's own development, and the second probe here is the one that goes
    # red against it (demonstrated on the pre-fix solid, not assumed).
    col = (c.SCREW_SPACING / 2 - 1.2, v - 2.45)
    r.check(
        is_solid_at(cap, col[0], col[1], z_mid),
        "screw columns are really there in the flange",
        f"solid at ({col[0]:.2f}, {col[1]:.2f}), inside the scallop's bite "
        f"and clear of the clearance hole",
    )
    r.check(
        not is_solid_at(cap, col[0], col[1], ew.CAP_T + 1.0),
        "...and end at the inner face -- no ribs down the plug's channel",
        "the plug keeps the standard cap's own hollow, cut separately from "
        "the scalloped chamber",
    )

    # The strap slot and the chamber stay separate solids' worth of air: the
    # web over the slot's roof is really there, and directly above it the
    # chamber is open -- slot below the floor, cable run above, wall between.
    # (check_strap_slot runs on this cap too, for the slot's own geometry.)
    z_web = (e.strap_slot_z()[1] + ew.CHAMBER_FLOOR_Z) / 2
    r.check(
        is_solid_at(cap, 0.0, e.STRAP_SLOT_Y, z_web),
        "web between the slot's roof and the chamber floor is really there",
        f"solid at y={e.STRAP_SLOT_Y}, z={z_web:.2f}, between a slot roof at "
        f"{e.strap_slot_z()[1]:.2f} and a floor at {ew.CHAMBER_FLOOR_Z}",
    )
    r.check(
        not is_solid_at(cap, 0.0, e.STRAP_SLOT_Y, ew.CHAMBER_FLOOR_Z + 0.3),
        "...and the chamber is open directly above it",
        "the slot's y sits inside the chamber's section, so a floor that "
        "crept below the slot's roof would merge the two -- strap in the "
        "cable run",
    )

    # --- the gland is still a gland --------------------------------------
    r_crest = e.GLAND_MAJOR_D / 2 - 1.0825 * e.GLAND_PITCH / 2 + 0.25
    thread_top = e.GLAND_COLLAR + e.GLAND_THREAD_L
    turns = [
        z
        for z in [
            e.GLAND_COLLAR + 0.25 + 0.25 * i for i in range(int(4 * e.GLAND_MALE_L))
        ]
        if z < thread_top and is_solid_at(cap, r_crest, _loc(e.GLAND_Z), z)
    ]
    r.check(
        len(turns) >= 3 * int(e.GLAND_THREAD_L / e.GLAND_PITCH),
        "gland thread is actually in the bore",
        f"{len(turns)} sampled stations carry material at r={r_crest:.2f}",
    )
    r.check(
        not is_solid_at(
            cap, r_crest, _loc(e.GLAND_Z), (thread_top + ew.CHAMBER_FLOOR_Z) / 2
        ),
        "...and the bore between thread and floor is plain",
        f"probed at z={(thread_top + ew.CHAMBER_FLOOR_Z) / 2:.2f}, inside "
        f"the collar under the floor's chamfer",
    )
    # The floor's rim chamfer, both sides of its cone and on the bore's low
    # side, exactly as check_gland_pocket probes the pocket's.
    z_cone = ew.CHAMBER_FLOOR_Z - e.POCKET_LEAD / 2
    r_cone = e.GLAND_MAJOR_D / 2 + e.POCKET_LEAD / 2
    r.check(
        not is_solid_at(cap, r_cone - 0.15, 0.0, z_cone)
        and is_solid_at(cap, r_cone + 0.15, 0.0, z_cone)
        and not is_solid_at(cap, 0.0, -(r_cone - 0.15), z_cone)
        and is_solid_at(cap, 0.0, -(r_cone + 0.15), z_cone),
        "floor's rim into the bore is chamfered, all the way round",
        f"{e.POCKET_LEAD} mm cone at r={r_cone:.2f}, z={z_cone:.2f}",
    )


def check_wired_edges(cap: Part, r: Report) -> None:
    """The wired cap's edge treatments, read back off the solid.

    Same discipline as ``check_endcap_edges``: every chamfer probed inside
    the material it removed and just beyond it, every selector-driven fillet
    re-run to prove an empty answer, and the raw-edge rule closed out by the
    audit with named exceptions only.
    """
    r.section("Wired endcap edges")
    half_h = ew.CAP_H / 2
    ch, li = e.EDGE_CHAMFER, e.PLUG_LEAD_IN

    r.check(
        not is_solid_at(cap, 0.0, -(half_h - 0.25 * ch), 0.25 * ch),
        "bed face chamfered -- no elephant's foot",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(cap, 0.0, -(half_h - 2 * ch), 0.25 * ch),
        "...and no more than that",
    )
    r.check(
        is_solid_at(cap, ew.CAP_W / 2 - 0.1, 0.0, ew.CAP_T - 0.05),
        "cap face is square at the flank -- the tube's wall seat",
    )

    tip = ew.CAP_T + e.PLUG_DEPTH
    arc_cy = _loc(c.BOT_ARC_Z)
    plug_r = c.RADIUS - c.WALL - e.PLUG_FIT / 2
    r.check(
        not is_solid_at(cap, 0.0, arc_cy - (plug_r - 0.25 * li), tip - 0.25 * li),
        "plug's leading edge has a lead-in",
        f"{li} mm",
    )
    r.check(
        is_solid_at(cap, 0.0, arc_cy - (plug_r - 2 * li), tip - 0.25 * li),
        "...and the plug's tip is still there",
    )
    void_r = plug_r - e.PLUG_WALL
    r.check(
        not is_solid_at(cap, 0.0, arc_cy - (void_r + 0.25 * li), tip - 0.25 * li),
        "...and the hollow's own rim has a matching lead-in",
    )
    r.check(
        is_solid_at(cap, 0.0, arc_cy - (void_r + 2 * li), tip - 0.25 * li),
        "...and the wall between the two chamfers is still there",
    )
    corners = ew.plug_tip_corner_edges(cap)
    r.check(
        not corners,
        "...and the corners its facets leave are rolled, not raw",
        "nothing sharp left in the chamfer's own band"
        if not corners
        else f"{len(corners)} left",
    )

    # The access bores' mouths on the bed face: the one lead-in this cap has
    # that the standard one does not need (its seat cone opened at the face
    # and was its own). Probed inboard of the hole, clear of the breakout.
    u = c.SCREW_SPACING / 2
    v = _loc(c.SCREW_BOSS_Z)
    z_probe = ew.SCREW_MOUTH_LEAD * 0.4
    r_cone = ew.SCREW_ACCESS_D / 2 + ew.SCREW_MOUTH_LEAD * 0.6
    r.check(
        not is_solid_at(cap, u - (r_cone - 0.1), v, z_probe),
        "access mouth has a lead-in cone at the bed face",
        f"{ew.SCREW_MOUTH_LEAD} mm -- where the screw goes in by hand",
    )
    r.check(
        is_solid_at(cap, u - (r_cone + 0.25), v, z_probe),
        "...and no more than that",
    )

    # The plug-top seams and corners, measured as angles where they stand.
    y_top = _loc(e.plug_top_z())
    x_seam = e.plug_void_half_width()
    seam_zone = [
        edge
        for edge in cap.edges()  # ty: ignore[invalid-argument-type]
        if edge.bounding_box().min.Z > ew.CAP_T - 0.01
        and abs(edge.bounding_box().max.Y - y_top) < 0.01
        and abs(abs(edge.bounding_box().center().X) - x_seam) < 0.05
        and edge.length > 5.0
    ]
    r.check(
        not [
            edge
            for edge in seam_zone
            if (a := interior_angle(cap, edge)) is not None and a <= 120.0
        ],
        "plug-top seams are filleted, not raw",
        f"{len(seam_zone)} long edges at the seam station, none sharp "
        f"({e.PLUG_SEAM_FILLET} mm fillet)",
    )

    # The raw-edge rule, closed out with named exceptions only.
    def _is_isothread_helix(edge) -> bool:
        return edge.geom_type == GeomType.BSPLINE

    def _is_cap_t_face_edge(edge) -> bool:
        bb = edge.bounding_box()
        return abs(bb.min.Z - ew.CAP_T) < 0.02 and abs(bb.max.Z - ew.CAP_T) < 0.02

    def _is_periodic_bore_seam(edge) -> bool:
        # The same non-edges check_endcap_edges names on the standard cap,
        # at this cap's own two flat ceilings: the clearance holes' walls run
        # the screw columns' full height and open through the CAP_T face, and
        # the gland collar's wall opens through the chamber floor's chamfer.
        if edge.geom_type != GeomType.LINE:
            return False
        bb = edge.bounding_box()
        tops = (ew.CAP_T, ew.CHAMBER_FLOOR_Z - e.POCKET_LEAD)
        if not (
            any(abs(bb.max.Z - top) < 0.02 for top in tops)
            and (bb.max.Z - bb.min.Z) > 1.0
        ):
            return False
        return is_periodic_seam(cap, edge)

    _check_sharp_edges(
        cap,
        "endcap_wired",
        r,
        (
            (
                "IsoThread helix",
                _is_isothread_helix,
                "the gland thread's flanks are a swept helix -- nothing to "
                "break on a printed thread",
            ),
            (
                "CAP_T face left raw",
                _is_cap_t_face_edge,
                "the whole of the CAP_T face beds against the extrusion -- "
                "the shell ring against its 0.5 mm wall, the screw columns' "
                "tops against its port bosses -- and the chamber's mouth and "
                "the channel's outward step sit on it (endcap_wired.py's "
                "module docstring). Breaking any of it opens a gap that seat "
                "has to span",
            ),
            (
                "periodic bore seam opening through a flat ceiling",
                _is_periodic_bore_seam,
                "the closing seam of a cylinder's own periodic "
                "parametrisation (both clearance holes' walls up the screw "
                "columns, the gland collar's wall), opening through the flat "
                "CAP_T face or the chamber floor's chamfer -- IsSame() "
                "adjacent faces in OCC's topology map, no second surface to "
                "measure a dihedral against",
            ),
        ),
    )


def check_cap_on_profile(r: Report) -> None:
    """The cap and the extrusion have to agree about where everything is."""
    r.section("Cap on profile")
    alu = create_extrusion(c.SECTION_LENGTH)
    near = e.seated(length=c.SECTION_LENGTH)

    overlap = _shared_volume(alu, near)
    r.check(
        overlap < 0.01, "cap does not clash with the profile", f"{overlap:.4f} mm^3"
    )

    # The plug is a shell, and this is that claim made from the *tube's* side:
    # what the extrusion actually gets back is the bottom PLUG_WALL of its own
    # cavity, not a half-disc filling it. Probed in the profile's frame, where
    # the plug's outer surface stands WALL + PLUG_FIT/2 off the tube's inside.
    x_plug = 1.0  # 1 mm into the tube, well inside the plug's PLUG_DEPTH
    z_outer = c.WALL + e.PLUG_FIT / 2
    z_wall = z_outer + e.PLUG_WALL / 2
    z_air = z_outer + e.PLUG_WALL + 0.5
    r.check(
        is_solid_at(near, x_plug, 0, z_wall),
        "plug's wall is on the floor of the cavity",
        f"material on the axis at z={z_wall:.2f}, mid-wall -- the plug's outer "
        f"surface stands {z_outer:.2f} mm off the tube's inside",
    )
    r.check(
        not is_solid_at(near, x_plug, 0, z_air),
        "...and it is a wall, not a fill: the cavity is open above it",
        f"air on the axis at z={z_air:.2f}, over {e.PLUG_WALL} mm of wall. This "
        f"column was solid to z={e.GLAND_Z + e.POCKET_Y_LOW:.2f} when the plug "
        f"was a half-disc -- that is the room the wiring gets back",
    )
    r.check(
        not is_solid_at(near, x_plug, 0, e.GLAND_Z),
        "...and the gland's axis is clear through the plug",
    )
    r.check(
        not is_solid_at(near, x_plug, 0, e.plug_top_z() + 0.2),
        "...and the plug stops PLUG_TOP_GAP below the cavity ceiling",
        f"top at z={e.plug_top_z():.2f}, ceiling at {c.CAVITY_TOP_Z}",
    )

    # And it stands off the cavity wall all round. Sampled on the lower arc --
    # the plug is clipped below CAVITY_TOP_Z, so there is no straight-sided
    # band of it to probe.
    z_probe = 11.0
    rise = c.BOT_ARC_Z - z_probe
    r_out = c.RADIUS - c.WALL - e.PLUG_FIT / 2
    half_out = sqrt(r_out**2 - rise**2)
    r.check(
        is_solid_at(near, x_plug, half_out - 0.1, z_probe),
        "plug reaches out to the cavity wall",
        f"solid to {half_out:.2f} mm from centre",
    )
    r.check(
        not is_solid_at(near, x_plug, half_out + 0.05, z_probe),
        "and stands off it",
    )
    gap = e.PLUG_FIT / 2
    r.check(
        gap > 0.05,
        "plug clearance per side",
        f"{gap:.3f} mm ({e.PLUG_FIT} diametral, SLIDING)",
    )

    # Screw axis: the cap's hole must be centred on the profile's port.
    r.check(
        not is_solid_at(near, -e.CAP_T / 2, c.SCREW_SPACING / 2, c.SCREW_BOSS_Z),
        "screw hole is open through the cap",
    )
    r.check(
        not is_solid_at(alu, 1.0, c.SCREW_SPACING / 2, c.SCREW_BOSS_Z),
        "and lines up with the port bore",
    )


def check_assembly(r: Report) -> None:
    """Assembled, the whole thing is exactly the stadium it is supposed to be.

    ``glands=False`` on purpose: this measures what a *mount* has to bore for,
    and a fitted gland is not part of that stadium -- it used to hang below the
    tube's underside, which is what a corner's plinth exists to clear. The
    gland's own reach is measured separately below, against the two numbers
    (``corner.GLAND_DROP``, ``gland.free_length``) that consume it.
    """
    r.section("Assembly")
    bare = create_bare(c.SECTION_LENGTH).bounding_box()
    r.check(
        abs(bare.size.Y - c.WIDTH) < 0.01 and abs(bare.size.Z - c.HEIGHT) < 0.01,
        "bought hardware envelope",
        f"{bare.size.Y:.2f} x {bare.size.Z:.2f} mm, want {c.WIDTH} x {c.HEIGHT}",
    )
    full = Compound(children=lamp_parts(c.SECTION_LENGTH, glands=False)).bounding_box()
    r.check(
        abs(full.size.Y - e.CAP_W) < 0.01 and abs(full.size.Z - e.CAP_H) < 0.01,
        "finished lamp envelope is the collar",
        f"{full.size.Y:.2f} x {full.size.Z:.2f} mm",
    )
    r.check(
        abs(full.size.X - (c.SECTION_LENGTH + 2 * e.CAP_T)) < 0.01,
        "caps add CAP_T at each end",
        f"{full.size.X:.1f} mm over a {c.SECTION_LENGTH:.0f} mm cut",
    )

    # And now the glands. Both numbers below are consumed elsewhere as
    # constants -- corner.PLINTH_H is sized against the first, every mount's
    # headroom against the second -- so measuring them off a *placed* gland is
    # what stops the two sides drifting apart.
    #
    # The drop is read off the glands alone, not off the whole scene's box,
    # because the two are not the same measurement and were only ever close:
    # the fitting hung 0.35 mm below the tube while the bore was pushed down
    # the cavity, and the scene's lowest point was the cap's 0.6 mm collar.
    # Both are zero now -- the bore is on the tube's axis and the cap is flush
    # -- so the gland is comfortably inside the tube's own outline and the
    # measurement below reads negative. Clamped, because GLAND_DROP is what a
    # plinth has to clear and a gland that clears itself needs nothing.
    fitted = Compound(children=gland_mod.seated(cable=False)).bounding_box()
    drop = max(-fitted.min.Z, 0.0)  # tube-local z is 0 at the profile's underside
    r.check(
        abs(drop - corner_mod.GLAND_DROP) < 0.01,
        "a fitted gland hangs GLAND_DROP below the tube",
        f"{drop:.2f} mm ({-fitted.min.Z:+.2f} unclamped), and corner.PLINTH_H "
        f"is {corner_mod.PLINTH_H:.1f} mm",
    )
    whole = Compound(children=lamp_parts(c.SECTION_LENGTH)).bounding_box()
    reach = whole.size.X - c.SECTION_LENGTH - 2 * e.CAP_T
    r.check(
        abs(reach - 2 * gland_mod.free_length()) < 0.01,
        "...and it plus its first bend radius adds free_length at each end",
        f"{reach / 2:.1f} mm past each cap face "
        f"({mc.GLAND_PROUD:.1f} gland + {gland_mod.CABLE_STUB:.0f} cable)",
    )


def _mount_pose(part: Part, length: float) -> Part:
    """Move a mount out of its print pose and onto the tube's coordinates.

    Mount-local z is measured from the bed and the tube's underside sits a wall
    above it; the profile's own z has that underside at zero. So a mount drops
    onto the tube by sliding down ``TUBE_UNDER_Z`` -- and the cradles run along
    +X already, so nothing has to turn.
    """
    del length
    return as_part(Pos(0, 0, -mc.TUBE_UNDER_Z) * part)


def check_mount_never_touches(
    part: Part, name: str, r: Report, length: float = 200.0
) -> None:
    """The assertion the whole family exists to satisfy.

    A mount that fouls the diffuser cannot be assembled and, worse, cannot be
    taken off to change a strip. It is invisible in a projection, so it is
    point-checked here for every part in the family.
    """
    seated = _mount_pose(part, length)
    alu = create_extrusion(length)
    diffuser = create_diffuser(length)
    r.check(
        _shared_volume(seated, diffuser) < 0.01,
        f"{name}: clear of the diffuser",
        f"{_shared_volume(seated, diffuser):.3f} mm^3",
    )
    r.check(
        _shared_volume(seated, alu) < 0.01,
        f"{name}: clear of the extrusion",
        f"{_shared_volume(seated, alu):.3f} mm^3",
    )


def check_mount_basics(
    part: Part, name: str, r: Report, max_z: float | None = None
) -> None:
    """Print pose, one solid, and inside the smaller printer's bed."""
    bb = part.bounding_box()
    r.check(len(part.solids()) == 1, f"{name}: one solid", f"{len(part.solids())}")
    r.check(abs(bb.min.Z) < 0.02, f"{name}: sits on z=0", f"min z {bb.min.Z:.3f}")
    r.check(
        bb.size.X <= BED and bb.size.Y <= BED,
        f"{name}: fits the smaller bed",
        f"{bb.size.X:.0f} x {bb.size.Y:.0f} mm, bed {BED:.0f}",
    )
    if max_z is not None:
        r.check(
            bb.max.Z <= max_z + 0.02,
            f"{name}: nothing above the rim",
            f"{bb.max.Z:.2f} mm, rim at {max_z:.2f}",
        )


def check_cradle(part: Part, r: Report) -> None:
    """The bore: contact at the end bands, relieved through the middle."""
    r.section("Cradle")
    check_mount_basics(part, "cradle", r, max_z=mc.CRADLE_DEPTH)
    check_mount_never_touches(part, "cradle", r)
    check_cradle_edges(part, "cradle", r)

    # Solid just outside the bore, open just inside it, in a contact band.
    u_out = (c.WIDTH + mc.BORE_FIT) / 2 + 0.5
    u_in = (c.WIDTH + mc.BORE_FIT) / 2 - 0.3
    z = mc.TUBE_AXIS_Z
    r.check(is_solid_at(part, mc.BAND_LEN / 2, u_out, z), "band: wall present")
    r.check(not is_solid_at(part, mc.BAND_LEN / 2, u_in, z), "band: bore is open")
    # And relieved in the middle, which is the +/-1 deg a closed polygon needs.
    r.check(
        not is_solid_at(part, mc.CRADLE_LEN / 2, u_in + mc.BAND_RELIEF * 0.8, z),
        "middle is relieved",
        f"{mc.BAND_RELIEF} mm diametral, for the polygon's angular slack",
    )
    r.check(
        not is_solid_at(part, mc.CRADLE_LEN / 3, 0, 0.5),
        "cradle floor drains",
        "an upward-facing trough outdoors is a gutter",
    )
    r.check(
        mc.BORE_FIT > 0.02,
        "bore fit is a clearance, not an interference",
        f"{mc.BORE_FIT:.3f} mm diametral in {mc.MATERIAL.upper()}; SNUG would be "
        f"{fits.for_material(fits.SNUG, mc.MATERIAL):+.2f}",
    )


def _chamfer_pair(part: Part, r: Report, label: str, inside, outside) -> None:
    """One chamfer, read off the solid as two samples.

    ``inside`` is a point in the wedge the chamfer should have removed and
    ``outside`` one just past it that must still be material -- an op that never
    ran fails the first, one that ate too much fails the second.

    Where there is room, ``outside`` is taken 1.5 x ``EDGE_CHAMFER`` **along one
    face** rather than diagonally out from the corner. That is what catches a
    chamfer applied twice: doubling insets the flat face by 2 x but barely moves
    the diagonal, so a diagonal sample passes a part whose footprint has lost
    1.6 mm. ``chamfer_edge`` returns True both times, so the solid is the only
    witness.
    """
    r.check(not is_solid_at(part, *inside), label, f"{mc.EDGE_CHAMFER} mm")
    r.check(is_solid_at(part, *outside), f"...{label}: and no more than that")


def check_boss_pad_edges(part: Part, name: str, r: Report) -> None:
    """The four strap-boss pads, on any part built round ``create_cradle``.

    Checked per pad rather than once for all four, because the failure this
    exists for was one pad chamfered twice (1.6 mm off its footprint) while its
    mirror went untouched -- both calls returned True, and a single sample
    anywhere would have passed.
    """
    ch, fr = mc.EDGE_CHAMFER, mc.EDGE_FILLET
    top = mc.CRADLE_DEPTH
    pad = mc.BOSS_U + mc.BOSS_OD / 2

    for station in mc.STRAP_STATIONS:
        for side in (-1.0, 1.0):
            u = side * pad
            # Bed chamfer, sampled at the middle of the pad's outboard edge --
            # its plan corners are inside the R2.5 fillet and are air either way.
            _chamfer_pair(
                part,
                r,
                f"{name}: boss pad bed chamfered at x={station:.0f}, u={u:+.1f}",
                (station, u - side * 0.25 * ch, 0.25 * ch),
                (station, u - side * 1.5 * ch, 0.1 * ch),
            )
            # Vertical fillet at both plan corners of that pad.
            for end in (-1.0, 1.0):
                x = station + end * mc.STRAP_W / 2
                r.check(
                    not is_solid_at(
                        part, x - end * 0.2 * fr, u - side * 0.2 * fr, top / 2
                    ),
                    f"{name}: boss pad corner filleted at x={x:.0f}, u={u:+.1f}",
                    f"R{fr}",
                )
                r.check(
                    is_solid_at(part, x - end * fr, u - side * fr, top / 2),
                    "...and the corner itself is still there",
                )


def check_cradle_edges(
    part: Part,
    name: str,
    r: Report,
    extra_sharp_allow: tuple[tuple[str, Callable[[object], bool], str], ...] = (),
) -> None:
    """A cradle's edges are actually broken, not merely asked to be.

    Same instrument and same reasoning as ``check_corner_edges``: an OCC edge op
    that silently did not apply is indistinguishable from one that did in a
    projection, and ``chamfer_edge``/``fillet_edge`` swallow the failure by
    design, so every treatment is read back off the solid. Holds for the bare
    cradle and for both feet, which inherit all of it.

    Ends with ``sharp_convex_edges`` over the *whole* solid, not just the
    samples above -- the same falsifiable raw-edge rule every other
    ``check_*_edges`` in this file now runs. ``extra_sharp_allow`` is where a
    foot adds its own exceptions on top of the ones every cradle-derived part
    shares.
    """
    ch = mc.EDGE_CHAMFER
    top = mc.CRADLE_DEPTH
    half = mc.CRADLE_OUTER_HALF_W
    bore = (c.WIDTH + mc.BORE_FIT) / 2

    # Rim chamfer on the outer flank. Sampled in the 1 mm gap just past the near
    # boss pad, which is the only stretch of flank a foot's own pad does not
    # cover -- so one sample point serves the cradle and both feet.
    x = mc.STRAP_STATIONS[0] + mc.STRAP_W / 2 + 0.5
    _chamfer_pair(
        part,
        r,
        f"{name}: rim chamfered along the flank",
        (x, half - 0.25 * ch, top - 0.25 * ch),
        (x, half - 0.75 * ch, top - 0.75 * ch),  # diagonal: the gap is 1 mm wide
    )
    # The trough's mouth is the tube's lead-in as it drops in sideways. Sampled
    # in an end contact band, where the bore is at the nominal fit -- the middle
    # is relieved by BAND_RELIEF and its mouth sits at a different u.
    _chamfer_pair(
        part,
        r,
        f"{name}: trough mouth chamfered -- the tube's lead-in",
        (mc.BAND_LEN / 2, bore + 0.25 * ch, top - 0.25 * ch),
        (mc.BAND_LEN / 2, bore + 1.5 * ch, top - 0.1 * ch),
    )
    check_boss_pad_edges(part, name, r)

    # The two deliberate exceptions. A pass that "fixes" either should have to
    # delete a check that says why it is there.
    r.check(
        is_solid_at(
            part, mc.STRAP_STATIONS[0], mc.BOSS_U + mc.INSERT_D / 2 + 0.05, top - 0.05
        ),
        f"{name}: insert mouth left raw",
        "a printed lead-in removes the material the heat-set has to melt into",
    )
    r.check(
        is_solid_at(part, mc.CRADLE_LEN / 2, 0.9, 0.02),
        f"{name}: trough's own bed sliver left raw",
        "2.2 mm of a clipped R17 arc meeting it at ~4 deg -- no corner to break",
    )
    # The drain mouths take a boolean cone, not an edge op.
    x_drain = mc.CRADLE_LEN / 3
    r.check(
        not is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 0.3 * ch, 0.2 * ch),
        f"{name}: drain mouth coned at the bed",
        f"{ch} mm lead-in, cut as a boolean",
    )
    r.check(
        is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 0.3, ch + 0.4),
        "...and the bore is back to DRAIN_D above it",
    )

    # And the drain's *other* mouth, where it actually drains from: the
    # trough's own floor, the bore's curved underside. x_drain (CRADLE_LEN/3,
    # the default station) falls in the relieved middle, so its floor sits
    # BAND_RELIEF below the nominal one and curves to a wider radius --
    # trough_floor_z/trough_floor_arc_r are what a raw TUBE_UNDER_Z would get
    # wrong here, the same way it would if this station ever moved into a
    # contact band instead.
    floor_z = trough_floor_z(x_drain, mc.CRADLE_LEN)
    arc_r = trough_floor_arc_r(x_drain, mc.CRADLE_LEN)
    r.check(
        not is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 0.25 * ch, floor_z - 0.25 * ch),
        f"{name}: drain funnelled at the trough floor -- the water side",
        f"{ch} mm lead-in at floor z={floor_z:.2f}",
    )
    r.check(
        is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 1.5 * ch, floor_z - 0.25 * ch),
        "...and no more than that",
    )
    # The flank of that same mouth, and the only sample here that can tell the
    # old funnel from the new one. The floor is a cylinder lying along the
    # tube, so at y = DRAIN_D/2 it has already climbed ``lip`` above its lowest
    # point; a funnel whose widest ring sat *at* that lowest point never
    # reached the lip out here and left it raw right round both flanks -- ~4
    # sharp edges per drain, which is what the audit used to allow as the
    # "drain funnel residual". This point sits below the floor at this y (so it
    # was solid before) and inside the lifted cone (so it is air now).
    lip = arc_r - sqrt(arc_r**2 - (mc.DRAIN_D / 2) ** 2)
    r.check(
        not is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 0.05, floor_z + lip / 2),
        f"{name}: ...and broken on the flank, where the floor has climbed away",
        f"lip {lip:.3f} mm at y=DRAIN_D/2, funnel lifted "
        f"{cradle_mod.drain_funnel_rise(arc_r):.3f} mm above the floor",
    )
    r.check(
        is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 2 * ch + 0.5, floor_z + lip / 2),
        "...and the floor outboard of the funnel is untouched",
    )

    # The raw-edge rule, made falsifiable, over the whole solid -- not just
    # the samples above. ``extra_sharp_allow`` lets a foot add its own
    # exceptions (its counterbore) on top of the ones every cradle-derived
    # part shares: the insert mouths, the bed sliver, and the bore/wall's own
    # cross-section wherever the trough is axially discontinuous. The
    # curved-floor drains used to need a fourth (their funnel left the lip raw
    # on both flanks); ``cradle.drain_funnel`` reaches the flanks now, so there
    # is nothing left to allow.
    _check_sharp_edges(
        part,
        name,
        r,
        (
            (
                "insert mouth left raw",
                _is_insert_mouth_edge,
                "a printed lead-in removes the material the heat-set has to "
                "melt into -- the family-wide exception",
            ),
            (
                "trough seam (bore/wall cross-section at a discontinuity)",
                lambda edge: _is_trough_seam_edge(edge, top),
                "cradle.vertical_corners' own selection excludes these -- "
                "'the short verticals inside a trough's stadium... at the "
                "bore's relief step, and down the seam of every bore and "
                "counterbore, none of which may be rounded'",
            ),
            (
                "trough's own bed sliver left raw",
                _is_bed_sliver,
                "2.2 mm of a clipped R17 arc meeting it at ~4 deg -- no "
                "corner to break (cradle.py's module docstring)",
            ),
        )
        + extra_sharp_allow,
    )


def check_foot_edges(part: Part, name: str, hole_d: float, r: Report) -> None:
    """A foot's own bolt pads and bolt holes, on top of ``check_cradle_edges``."""
    ch, fr = mc.EDGE_CHAMFER, mc.EDGE_FILLET
    top = mc.CRADLE_DEPTH
    mid = mc.CRADLE_LEN / 2
    out = feet_mod.PAD_U_OUT
    lead = mc.BOLT_LEAD_IN
    floor = mc.CRADLE_DEPTH - feet_mod.CBORE_DEPTH
    # 3 mm in from the pad's near end: clear of the R2.5 fillet, and clear of
    # the counterbore, which on the eye foot reaches this pad's outboard face.
    x_rim = mid - feet_mod.PAD_LEN / 2 + 3.0

    for side in (-1.0, 1.0):
        u = side * out
        _chamfer_pair(
            part,
            r,
            f"{name}: bolt pad rim chamfered at u={u:+.1f}",
            (x_rim, u - side * 0.25 * ch, top - 0.25 * ch),
            (x_rim, u - side * 1.5 * ch, top - 0.1 * ch),
        )
        _chamfer_pair(
            part,
            r,
            f"{name}: bolt pad bed chamfered at u={u:+.1f}",
            (mid, u - side * 0.25 * ch, 0.25 * ch),
            (mid, u - side * 1.5 * ch, 0.1 * ch),
        )
        for end in (-1.0, 1.0):
            x = mid + end * feet_mod.PAD_LEN / 2
            r.check(
                not is_solid_at(part, x - end * 0.2 * fr, u - side * 0.2 * fr, top / 2),
                f"{name}: bolt pad corner filleted at x={x:.0f}, u={u:+.1f}",
                f"R{fr}",
            )
            r.check(
                is_solid_at(part, x - end * fr, u - side * fr, top / 2),
                "...and the corner itself is still there",
            )
        # Bolt-hole lead-ins: boolean cones, the house rule for a bore mouth,
        # and the same instrument and size strap.create_strap uses.
        hu = side * feet_mod.HOLE_U
        r.check(
            not is_solid_at(
                part, mid, hu + side * (hole_d / 2 + 0.6 * lead), 0.2 * lead
            ),
            f"{name}: bolt hole coned at the bed mouth at u={hu:+.1f}",
            f"{lead} mm",
        )
        r.check(
            is_solid_at(part, mid, hu + side * (hole_d / 2 + 0.3), lead + 0.4),
            "...and the bore is back to size above it",
        )
        # Sampled *below* the floor, inside the material the cone has to take
        # out. Above it is the counterbore's own void, where every sample comes
        # back "not solid" whether or not anything was ever cut -- which is how
        # this pocket kept a raw 90 deg shoulder through a passing check (see
        # feet._create_foot on the cone that used to sit up there).
        r.check(
            not is_solid_at(
                part, mid, hu + side * (hole_d / 2 + 0.6 * lead), floor - 0.2 * lead
            ),
            f"{name}: bolt hole coned at the counterbore floor at u={hu:+.1f}",
            "the bolt has to find the hole blind, from inside the pocket",
        )
        r.check(
            is_solid_at(part, mid, hu + side * (hole_d / 2 + 0.3), floor - 1.6 * lead),
            "...and the bore is back to size below it",
        )
        # The seat the nyloc bears on is still flat: the cone stops one
        # BOLT_LEAD_IN out, not at the counterbore wall.
        r.check(
            is_solid_at(
                part, mid, hu + side * (hole_d / 2 + 1.6 * lead), floor - 0.2 * lead
            ),
            "...and the nut's seat outboard of it is still flat",
        )


def check_strap(part: Part, r: Report) -> None:
    """Captures the tube without touching it, and cannot jack its inserts.

    The strap is the one part that crosses above the rim, so it is the one that
    can foul the diffuser -- and there is nothing else up there for it to bear
    on, since the extrusion presents only two ~0.5 mm wall edges at the rim.
    """
    r.section("Strap")
    check_mount_basics(part, "strap", r)
    dropped = as_part(Pos(0, 0, -mc.TUBE_UNDER_Z) * strap_mod.seated(mc.CRADLE_LEN / 2))

    for other, label in (
        (create_diffuser(200.0), "diffuser"),
        (create_extrusion(200.0), "extrusion"),
    ):
        overlap = _shared_volume(dropped, other)
        r.check(overlap < 0.01, f"strap touches no {label}", f"{overlap:.3f} mm^3")

    # It has to arch *over* the tube, not merely miss it: the crown must sit
    # above the diffuser and by little enough that the tube cannot lift out.
    crown = strap_mod.CROWN_Z + c.RIM_Z  # strap-local zero is the rim
    play = crown - c.HEIGHT
    r.check(
        0.8 <= play <= 2.5,
        "captures the tube with a little play",
        f"{play:.2f} mm over the diffuser crown; foam takes it up if it matters",
    )
    r.check(
        mc.BOLT_CLEAR_D < mc.INSERT_D,
        "bolt cannot jack the insert out",
        f"clearance {mc.BOLT_CLEAR_D} < insert {mc.INSERT_D}",
    )
    check_bolt_clears_arch(part, r)
    check_strap_edges(part, r)
    check_bore_crown_bridge(part, r)


def check_bore_crown_bridge(part: Part, r: Report) -> None:
    """The crown's sub-45 deg zone is a bridge because its run is short.

    ``strap``'s module docstring: the bore leaves the bed vertical, crosses
    the 45 deg overhang rule at ``|x| = BORE_HALF_W / sqrt(2)``, and is flat
    (0 deg from horizontal) at the apex. That crossing point, and so the
    ``sqrt(2) * BORE_HALF_W`` chord it bounds, is fixed by the tube's own
    geometry (``config.WIDTH``, ``mount_config.DIFFUSER_CLEAR``) -- it does
    not move if ``STRAP_W`` changes.

    What makes the zone printable is a layer-by-layer, X-only mechanism:
    ``create_strap`` extrudes the whole arc cross-section straight through
    ``STRAP_W`` in one pass, chamfered only in the last ``EDGE_CHAMFER``
    (0.8 mm) at each end, so for ~95% of the run every layer is the standard
    horizontal-round-bore case -- each layer overhangs the one below it by a
    small, continuously increasing amount *in X*, converging to a point at
    the apex. That self-support does not depend on how long ``STRAP_W`` is; a
    longer run just repeats the same X-profile more times, so it is not what
    this check is guarding against, and it is not derived from
    ``fdm-fits-and-clearances``'s 5-10 mm flat-bridge span rule -- that rule
    bounds an unsupported gap by its own width and has no aspect-ratio
    concept, so it does not apply here in that form (``STRAP_W`` at 18 mm
    already exceeds a flat 5-10 mm span with no ill effect, because the
    X-convergence handles it, not bridging).

    What the bound below actually guards is narrower and more honest: it is a
    deliberately conservative sanity check that the run (``STRAP_W``) stays
    no longer than the chord it is thrown across
    (``sqrt(2) * BORE_HALF_W``), so a change that grows ``STRAP_W``
    dramatically past the one scale this feature has been measured at has to
    re-justify itself here rather than pass silently. Currently
    18.0 <= 20.51 mm, a ~12% margin -- grow ``STRAP_W`` past the chord, or
    shrink the chord by tightening ``DIFFUSER_CLEAR`` or ``config.WIDTH``,
    and this goes red before the part is ever printed.

    Checked twice, the same pattern as ``check_bolt_clears_arch``: once in
    closed form, and once by point-sampling the real solid at the predicted
    45 deg crossing, because the formula can be right about a shape the
    builder did not actually produce.
    """
    r.section("Strap bore-crown bridge")
    chord = sqrt(2) * strap_mod.BORE_HALF_W
    r.check(
        mc.STRAP_W <= chord,
        "bridge run (STRAP_W) does not exceed the chord it is thrown across",
        f"STRAP_W={mc.STRAP_W:.2f} mm vs chord={chord:.2f} mm "
        f"(= sqrt(2) x BORE_HALF_W, the sub-45 deg span at the crown)",
    )

    # Confirm the formula against the actual solid. At the predicted 45 deg
    # crossing the arc's own tangent is itself at 45 deg, so the local normal
    # points equally into x and z; step a small distance either side of the
    # predicted (x, z) along that normal and expect void just inboard, solid
    # just outboard. Sampled at y=0, mid-strap, clear of the end chamfers.
    x45 = strap_mod.BORE_HALF_W / sqrt(2)
    z45 = strap_mod.CROWN_Z - strap_mod.BORE_HALF_W * (1 - 1 / sqrt(2))
    eps = 0.05 / sqrt(2)
    r.check(
        not is_solid_at(part, x45 - eps, 0.0, z45 - eps),
        "45 deg crossing point is void just inboard, on the real solid",
        f"x={x45:.2f}, z={z45:.2f}",
    )
    r.check(
        is_solid_at(part, x45 + eps, 0.0, z45 + eps),
        "...and solid just outboard -- the crossing is where the formula says",
    )


def check_strap_edges(part: Part, r: Report) -> None:
    """The strap's edges are actually broken, not merely asked to be.

    Same method as ``check_corner_edges``: every treatment is read back off the
    solid as a pair of samples -- one point inside the material it should have
    removed, one just beyond that must still be solid.

    The regression the bed pair exists for: the strap once chamfered its bed
    with ``faces().sort_by(Axis.Z)[0].outer_wire()``. Both feet's bed faces are
    coplanar at z=0, so that picked *one* of them and shipped the other foot
    with four raw square edges -- and it looked identical in a projection.
    """
    ch, fr = mc.EDGE_CHAMFER, mc.EDGE_FILLET
    u_out = mc.BOSS_U + mc.BOSS_OD / 2  # the foot's outer face
    u_bore = strap_mod.BORE_HALF_W
    v = mc.STRAP_W / 2
    flank = mc.arch_half_width(mc.FOOT_H)

    # Bed chamfer, on both feet -- the half-a-part regression above.
    for sign, side in ((1, "+x"), (-1, "-x")):
        r.check(
            not is_solid_at(part, sign * (u_out - 0.25 * ch), 0, 0.25 * ch),
            f"bed chamfered on the {side} foot",
            f"{ch} mm; a per-face selection would treat only one of the two",
        )
        r.check(
            is_solid_at(part, sign * (u_out - 2 * ch), 0, 2 * ch),
            f"...and no more than that ({side})",
        )

    # The bore's own bed edge: the tube's lead-in as the strap drops on.
    r.check(
        not is_solid_at(part, u_bore + 0.25 * ch, 0, 0.25 * ch),
        "bore mouth chamfered at the bed -- the strap's lead-in onto the tube",
        f"{ch} mm at u={u_bore}",
    )
    r.check(
        is_solid_at(part, u_bore + 2 * ch, 0, 2 * ch),
        "...and no more than that",
    )

    # The foot's land, where the M4 head seats: broken at its outer and end
    # edges. Sampled inboard of the bolt hole and clear of the corner fillet,
    # so this reads the chamfer and nothing else.
    r.check(
        not is_solid_at(part, 19.0, v - 0.25 * ch, mc.FOOT_H - 0.25 * ch),
        "foot land chamfered at the end edge",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(part, 19.0, v - 2 * ch, mc.FOOT_H - 2 * ch),
        "...and no more than that",
    )
    r.check(
        not is_solid_at(part, u_out - 0.25 * ch, 0, mc.FOOT_H - 0.25 * ch),
        "foot land chamfered at the outer edge",
        f"{ch} mm",
    )

    # The feet's vertical corners: the part comes off in the hand twice per
    # strip change, and these are the only true vertical edges it has.
    r.check(
        not is_solid_at(part, u_out - 0.2 * fr, v - 0.2 * fr, mc.FOOT_H / 2),
        "foot corners filleted",
        f"R{fr}",
    )
    r.check(
        is_solid_at(part, u_out - fr, v - fr, mc.FOOT_H / 2),
        "...and the corner itself is still there",
    )

    # The arch's outer silhouette and its bore mouth, on the end faces. Both
    # sampled over the crown, which is the sharpest stretch of either.
    r.check(
        not is_solid_at(part, 0, v - 0.25 * ch, strap_mod.OUTER_Z - 0.25 * ch),
        "arch silhouette chamfered over the crown",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(part, 0, v - 2 * ch, strap_mod.OUTER_Z - 2 * ch),
        "...and no more than that",
    )
    r.check(
        not is_solid_at(part, 0, v - 0.25 * ch, strap_mod.CROWN_Z + 0.25 * ch),
        "bore mouth chamfered over the crown",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(part, 0, v - 2 * ch, strap_mod.CROWN_Z + 2 * ch),
        "...and no more than that",
    )

    # And the arch's root is still raw. This one is an *absence* check: a fillet
    # or chamfer on that concave edge adds material, and it has only
    # BOLT_HEAD_CLEAR to grow into before it is under the M4 head.
    r.check(
        not is_solid_at(part, flank + 0.15, 0, mc.FOOT_H + 0.1),
        "arch root left raw, so nothing grows into the head clearance",
        f"flank {flank:.2f}, head swept circle at "
        f"{mc.BOSS_U - mc.BOLT_HEAD_D / 2:.2f}, {mc.BOLT_HEAD_CLEAR} mm between",
    )
    r.check(
        is_solid_at(part, mc.BOSS_U - mc.BOLT_HEAD_D / 2 + 0.1, 0, mc.FOOT_H - 0.2),
        "and the head's bearing land is solid under it",
    )

    def _is_bolt_bore_seam(edge) -> bool:
        # sharp_convex_edges now reports the None edges min_length used to
        # let through unseen (see its docstring): one per boss, on the bolt
        # clearance bore's own cylindrical wall (the ``Cylinder`` cut in
        # ``create_strap``, between its two lead-in cones). is_vertical_seam
        # does the proof -- LINE, degenerate X/Y bbox, then is_periodic_seam
        # against OCC's own topology (see its docstring); the 0.05 tolerance
        # is the deliberate loosening that function documents: these bore
        # walls are not perfectly vertical, so the 1e-6 default would reject
        # the very seams they are. Scoped so this cannot also claim some
        # other edge that merely happens to share a seam somewhere else on
        # the part; checked against every edge on the strap, not assumed,
        # and only these two -- one per boss -- match both conditions at
        # once.
        return is_vertical_seam(part, edge, tolerance=0.05)

    # The raw-edge rule, made falsifiable. Unlike every other part in the
    # family, the strap needed no allow list at all for its *sharp* edges:
    # every sample pair above (bed, bore mouth, foot land, corners, arch
    # silhouette, bore mouth over the crown) already accounts for the part's
    # own edges, and the arch root's absence check confirms the one concave
    # edge that stays raw on purpose is concave -- so it cannot appear in a
    # *convex*-edge audit regardless. That claim still holds (checked below,
    # not assumed): ``sharp_convex_edges``'s own ``.sharp`` bucket is empty
    # here. Its ``.unclassifiable`` bucket is not, though -- the bolt bore
    # seams above -- so the one-entry allow list is what keeps that promise
    # honest instead of silently going stale the moment this file started
    # reporting a bucket that did not used to exist.
    _check_sharp_edges(
        part,
        "strap",
        r,
        (
            (
                "bolt clearance bore's own periodic seam",
                _is_bolt_bore_seam,
                "the cylindrical wall between the bolt hole's two lead-in "
                "cones is a periodic surface with no second face at its own "
                "seam -- not a real edge, confirmed via is_periodic_seam, "
                "one per boss",
            ),
        ),
    )


def check_bolt_clears_arch(part: Part, r: Report) -> None:
    """The strap can actually be bolted down.

    The regression this exists for: ``BOSS_U`` was 19.5, which is
    ``ARCH_HALF_W`` exactly, so the bolt axis lay on the arch's own flank. The
    hole's top mouth came out bisected by the springing and an M4 head fouled
    the flank by 2.6 mm. Both are now derived from ``arch_half_width(FOOT_H)``,
    and this is what says so if either drifts back.

    Checked twice on purpose: once against the closed form, and once against
    the solid itself, by putting a head-sized slug where the head goes and
    looking for shared volume. The formula can be right about a shape the
    builder did not actually produce.
    """
    flank = mc.arch_half_width(mc.FOOT_H)
    land = mc.BOSS_U - mc.BOLT_CLEAR_D / 2 - mc.BOLT_LEAD_IN - flank
    r.check(
        land > 0.5,
        "bolt mouth opens onto flat foot, not into the arch",
        f"{land:.2f} mm of land inboard of the mouth, flank at {flank:.2f}",
    )

    head_h = 4.0  # M4 socket cap
    fouled = 0.0
    for side in (-1, 1):
        slug = as_part(
            Pos(side * mc.BOSS_U, 0, mc.FOOT_H)
            * Cylinder(
                mc.BOLT_HEAD_D / 2,
                head_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
        fouled += _shared_volume(part, slug)
    r.check(
        fouled < 0.01,
        "an M4 head has room to seat and turn",
        f"{fouled:.3f} mm^3 of arch in the way",
    )


def check_corner(r: Report) -> None:
    """Angle, setback, section and reach, over the whole parameter sweep."""
    r.section("Corner")
    part = corner_mod.create_corner(60.0)
    check_mount_basics(part, "corner 60", r, max_z=corner_mod.TOP_Z)

    z_sec = corner_mod.section_modulus()
    r.check(
        15000.0 / z_sec <= 10.0,
        "arm section under the 15 N.m handling load",
        f"Z {z_sec:.0f} mm^3 -> {15000.0 / z_sec:.1f} MPa, ASA sustained limit 10",
    )
    r.check(
        corner_mod.PLINTH_H > corner_mod.GLAND_DROP,
        "plinth clears the gland hanging below the tube",
        f"plinth {corner_mod.PLINTH_H:.1f} > drop {corner_mod.GLAND_DROP:.2f}",
    )
    r.check(
        corner_mod.CHANNEL_W >= CAP_W + 1.0,
        "channel clears the endcap",
        f"{corner_mod.CHANNEL_W} vs cap {CAP_W}",
    )
    # The channel's *other* constraint, and the one nothing would otherwise
    # notice. Where the channel wall runs alongside the trough bore it leaves a
    # land at the rim, and two EDGE_CHAMFERs meet on it: too narrow and OCC
    # refuses the whole rim chamfer -- all four arms, silently, because
    # chamfer_edge swallows the refusal by design and a raw rim looks identical
    # in a projection. Too wide and the body's own R2.5 vertical corners refuse
    # instead. Both edges of the window are measured (see corner.CHANNEL_W):
    # 1.52 refuses the chamfer, 1.72 takes it, past ~1.82 the fillets go.
    land = corner_mod.mouth_land()
    r.check(
        1.6 <= land <= 1.8,
        "channel leaves the rim a land it can chamfer -- and not more",
        f"{land:.3f} mm between the channel wall and the trough bore; the window "
        f"is about 0.25 mm wide and this is the middle of it",
    )
    # The insert holes used to bite 0.4 mm into the trough's outer wall, for the
    # same reason the strap's bolts fouled its arch: the bolt circle sat barely
    # outboard of the cradle. Both moved together when BOSS_U was derived.
    gap = mc.BOSS_U - mc.INSERT_D / 2 - outer_half_width()
    r.check(
        gap > 1.0,
        "insert holes stand clear of the trough wall",
        f"{gap:.2f} mm between the hole and the wall's outer face",
    )
    for angle in (60.0, 90.0, 120.0, 150.0):
        p = corner_mod.create_corner(angle)
        bb = p.bounding_box()
        r.check(
            len(p.solids()) == 1 and bb.size.X <= BED and bb.size.Y <= BED,
            f"corner {angle:.0f}: one solid, on the bed",
            f"{bb.size.X:.0f} x {bb.size.Y:.0f} mm",
        )
        # Edges too, at every angle rather than only at 60. The selectors are
        # geometric -- lengths and heights, not indices -- so a change to the
        # arm layout could plausibly hold at one angle and miss at another.
        check_corner_edges(p, r, angle)
        r.check(
            _tube_clears_corner(p, angle),
            f"corner {angle:.0f}: both tubes seat without fouling",
            f"dark run {mc.dark_run(angle):.0f} mm",
        )
        fouled = _cap_fouling_corner(p, angle)
        r.check(
            fouled < 0.01,
            f"corner {angle:.0f}: both endcaps seat without fouling",
            f"{fouled:.3f} mm^3 of corner inside the collars' envelope",
        )


def check_corner_edges(part: Part, r: Report, angle: float = 60.0) -> None:
    """The corner's edges are actually broken, not merely asked to be.

    An OCC edge op that silently did not apply is indistinguishable from one
    that did in a projection, and ``chamfer_edge``/``fillet_edge`` swallow the
    failure by design, so the treatments are read back off the solid. Each is a
    pair of samples: one point inside the material a treatment should have
    removed, one just beyond it that must still be solid -- an op that ran but
    ran too small fails the first, one that ate the part fails the second.
    """
    start = corner_mod.cradle_start(angle)
    ch, fr = mc.EDGE_CHAMFER, mc.EDGE_FILLET
    bearing = corner_mod._axis_bearings(angle)[0]
    a = radians(bearing)
    tag = f"corner {angle:.0f}: "

    def at(along: float, across: float, z: float) -> tuple[float, float, float]:
        """Axis-local (distance out, offset across) to world, as _drill_inserts."""
        return (
            along * cos(a) - across * sin(a),
            along * sin(a) + across * cos(a),
            z,
        )

    # Rim chamfer, on the arm's outer face midway between the two boss pads --
    # the one stretch of that face a pad does not cover.
    mid = start + mc.CRADLE_LEN / 2
    half = corner_mod.BODY_W / 2
    top = corner_mod.TOP_Z
    r.check(
        not is_solid_at(part, *at(mid, half - 0.25 * ch, top - 0.25 * ch)),
        tag + "rim chamfered along the arm",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(part, *at(mid, half - 2 * ch, top - 2 * ch)),
        tag + "...and no more than that",
    )

    # Trough mouth chamfer: the tube's lead-in. Sampled inside an end contact
    # band, where the bore is at the nominal fit -- the middle is relieved by
    # BAND_RELIEF and its mouth sits at a different u.
    band = start + mc.BAND_LEN / 2
    bore = (c.WIDTH + mc.BORE_FIT) / 2
    r.check(
        not is_solid_at(part, *at(band, bore + 0.25 * ch, top - 0.25 * ch)),
        tag + "trough mouth chamfered -- the tube's lead-in",
        f"{ch} mm at u={bore:.2f}",
    )

    # Vertical fillet at the outboard corner of the arm's far end, where the
    # boss pad runs out flush with the arm.
    end = start + mc.CRADLE_LEN
    pad = mc.BOSS_U + mc.BOSS_OD / 2
    z_mid = corner_mod.TOP_Z / 2
    r.check(
        not is_solid_at(part, *at(end - 0.2 * fr, pad - 0.2 * fr, z_mid)),
        tag + "arm end corners filleted",
        f"R{fr}",
    )
    r.check(
        is_solid_at(part, *at(end - fr, pad - fr, z_mid)),
        tag + "...and the corner itself is still there",
    )

    # The trough-mouth corners, which take MOUTH_FILLET instead. Concave, so
    # the fillet *adds* material into the channel: the first sample is inside
    # what it added, the second is at the arc's own centre and has to stay
    # air. The second is the one that fails on an R2.5 corner -- that radius
    # reached 2.5 mm into a channel with 1.0 mm to give, which is what put
    # material inside the endcap collar and left a seam across the bore mouth
    # (see corner.MOUTH_FILLET and the clearance check in check_corner).
    mf = corner_mod.MOUTH_FILLET
    half_ch = corner_mod.CHANNEL_W / 2
    z_ch = (corner_mod.PLINTH_H + corner_mod.TOP_Z) / 2
    for side in (-1.0, 1.0):
        r.check(
            is_solid_at(
                part, *at(start - 0.15 * mf, side * (half_ch - 0.15 * mf), z_ch)
            ),
            tag + f"trough mouth corner filleted at u={side * half_ch:+.1f}",
            f"R{mf} -- half the clearance the channel holds for the cap collar",
        )
        r.check(
            not is_solid_at(part, *at(start - mf, side * (half_ch - mf), z_ch)),
            tag + "...and no further into the channel than that",
        )

    check_corner_undrained(part, r, angle)

    # The raw-edge rule, made falsifiable, over the whole solid. Insert
    # mouths and the bore/wall's own cross-section seam are the same
    # exceptions every cradle-derived part makes; the engraved label is
    # corner-specific (a 0.6 mm bed-face pocket -- chamfering its glyph
    # outlines would destroy legibility).
    #
    # A known gap used to sit here and does not now, because it was geometry
    # rather than an exception: a residual by each arm's first strap boss
    # whose cause the implementer could not trace. It was the channel's own
    # end-wall fillet: R2.5 at a
    # corner with only ``(CHANNEL_W - CAP_W) / 2`` of room rolled the wall
    # inward past the bore's mouth outline *and* into the endcap collar's
    # envelope. ``MOUTH_FILLET`` sizes that corner off the room it actually
    # has -- see ``corner._mouth_corners``.

    def _is_label_glyph(edge) -> bool:
        bb = edge.bounding_box()
        return bb.min.Z > -0.01 and bb.max.Z < corner_mod.LABEL_DEPTH + 0.02

    _check_sharp_edges(
        part,
        tag.rstrip(": "),
        r,
        (
            (
                "insert mouth left raw",
                _is_insert_mouth_edge,
                "a printed lead-in removes the material the heat-set has to "
                "melt into -- the family-wide exception",
            ),
            (
                "trough seam (bore cross-section at a discontinuity)",
                lambda edge: _is_trough_seam_edge(edge, top),
                "corner._vertical_corners' own selection excludes these -- "
                "'the short verticals inside a trough's stadium... at the "
                "bore's relief step, and down the seam of every bore and "
                "counterbore, none of which may be rounded'",
            ),
            (
                "engraved label glyph outline",
                _is_label_glyph,
                "a 0.6 mm pocket in the bed face (LABEL_DEPTH); chamfering "
                "glyph outlines would destroy legibility",
            ),
        ),
    )


def check_corner_undrained(part: Part, r: Report, angle: float = 60.0) -> None:
    """The corner is the one part in this family whose pockets do **not** drain.

    This is the complement of the check it replaces, and it exists for the
    same reason that one did: design-notes S5 promises "a drain out of every
    upward-facing pocket", the corner is now the stated exception to it, and
    an exception that is only *not tested* is indistinguishable from a
    regression. So the floors are asserted solid at exactly the four stations
    that used to be drilled -- if a drain comes back, this fails and whoever
    put it there has to restate S5 rather than quietly re-diverge from it.

    It also reports the water each pocket now holds, computed from the same
    floor geometry ``cradle.trough_floor_z`` gives the cradle: depth to the
    channel's own rim at the trough mouth, and depth to the lowest lip of
    each trough. Those numbers are the cost of the decision, so they belong
    in ``uv run check`` output where they are read, not in a comment.
    """
    start = corner_mod.cradle_start(angle)
    bearing = corner_mod._axis_bearings(angle)[0]
    a = radians(bearing)
    tag = f"corner {angle:.0f}: "

    def at(along: float, across: float, z: float) -> tuple[float, float, float]:
        return (
            along * cos(a) - across * sin(a),
            along * sin(a) + across * cos(a),
            z,
        )

    # Mid-plinth: below any pocket floor, above the bed chamfer's run-out.
    z_plinth = corner_mod.PLINTH_H / 2

    r.check(
        is_solid_at(part, 0.0, 0.0, z_plinth),
        tag + "knuckle plinth is solid -- no drain",
        f"channel floor at z={corner_mod.PLINTH_H}, holds water",
    )
    r.check(
        is_solid_at(part, *at(start * 0.55, 0.0, z_plinth)),
        tag + "near arm plinth is solid -- no drain",
    )
    for frac in (0.35, 0.75):
        d = start + mc.CRADLE_LEN * frac
        r.check(
            is_solid_at(part, *at(d, 0.0, z_plinth)),
            tag + f"trough plinth is solid at {frac:.0%} of the cradle -- no drain",
        )

    # What that costs, in standing water. The channel fills to its own mouth
    # at the trough, since that is where its rim is lowest; a trough fills to
    # the lowest point of its floor's lip, which is the relieved middle.
    channel_depth = corner_mod.TOP_Z - corner_mod.PLINTH_H
    trough_depth = mc.CRADLE_DEPTH - trough_floor_z(mc.CRADLE_LEN / 2, mc.CRADLE_LEN)
    r.check(
        True,
        tag + "standing water, both pockets (the stated S5 deviation)",
        f"channel up to {channel_depth:.1f} mm deep, trough up to "
        f"{trough_depth:.1f} mm -- sheltered mounting only",
    )


def _tube_clears_corner(part: Part, angle: float) -> bool:
    """Drop a real profile into each cradle and look for interference."""
    start = corner_mod.cradle_start(angle)
    for bearing in corner_mod._axis_bearings(angle):
        tube = create_extrusion(mc.CRADLE_LEN)
        placed = as_part(
            Pos(
                start * cos(radians(bearing)),
                start * sin(radians(bearing)),
                corner_mod.PLINTH_H + mc.TUBE_UNDER_Z,
            )
            * (Rotation(0, 0, bearing) * tube)
        )
        if _shared_volume(part, placed) > 0.01:
            return False
    return True


def _cap_fouling_corner(part: Part, angle: float) -> float:
    """Material of this corner inside a seated endcap's envelope, in mm^3.

    The tube stops at ``cradle_start``; the cap collar lives in the ``CAP_T``
    *behind* that, out in the channel, so ``_tube_clears_corner`` cannot see
    it -- and a corner that fouls the collar cannot be assembled at all, since
    the cap is screwed to the tube before either goes near a corner.
    ``CHANNEL_W >= CAP_W + 1.0`` was the only thing asserting this and it
    checks a constant, not the built solid: the channel's own end-wall fillet
    reached 1.5 mm past that promise (0.18 mm^3 an arm) and the arithmetic
    stayed true throughout.
    """
    start = corner_mod.cradle_start(angle)
    fouled = 0.0
    for bearing in corner_mod._axis_bearings(angle):
        placed = as_part(
            Pos(
                start * cos(radians(bearing)),
                start * sin(radians(bearing)),
                corner_mod.PLINTH_H + mc.TUBE_UNDER_Z,
            )
            * (Rotation(0, 0, bearing) * e.seated())
        )
        fouled += _shared_volume(part, placed)
    return fouled


# The stand's edge treatment is unfinished and ``check_stand_edges`` fails on
# it. Skipped **by request** so the rest of the family can ship, and skipped
# like this -- one named flag, with the check kept intact and still callable --
# rather than by deleting it or by feeding ``sharp_convex_edges`` an ``allow``
# list. An allow entry is a claim that an edge is *meant* to be square, and none
# of these are: the flange's bed face and upper rim, the station pads' 45 deg
# ramps and their top rims are square because OCC refuses those selections as a
# group and they still need coaxing edge by edge, the way ``cradle.treat_edges``
# does its pads. Flip this to False to see exactly what is left.
SKIP_STAND_EDGES = True


def check_stand_no_undercut(r: Report) -> None:
    """The claim the whole stand design rests on, as a test.

    design-notes S1 says nothing wraps this section. The reason is stronger
    than "the diffuser is in the way": the assembled tube's width is
    **monotonically non-decreasing** from z=0 to the straight band and constant
    across it, so for a trough opening upward, every section below a lip is
    narrower than the gap that lip leaves -- the tube slides straight out at
    any lip height. Retention needs a lip past ``TOP_ARC_Z``, which is
    diffuser, and loading the diffuser routes the stand through its snap hooks
    instead of the aluminium.

    That is why ``stand.keeper`` is a key in a socket and not a snap on the
    tube, and it is worth a check rather than a paragraph, because the snap is
    the obvious thing to reach for and it is wrong every time.
    """
    r.section("stand: the section offers no undercut")

    def half_width(z: float) -> float:
        if z <= c.BOT_ARC_Z:
            return sqrt(max(c.RADIUS**2 - (c.BOT_ARC_Z - z) ** 2, 0.0))
        if z <= c.TOP_ARC_Z:
            return c.RADIUS
        return sqrt(max(c.RADIUS**2 - (z - c.TOP_ARC_Z) ** 2, 0.0))

    step = 0.05
    samples = [i * step for i in range(int(c.TOP_ARC_Z / step) + 1)]
    widths = [2 * half_width(z) for z in samples]
    r.check(
        all(b >= a - 1e-9 for a, b in zip(widths, widths[1:])),
        "width never decreases below the top arc",
        f"{samples[0]:.0f}..{samples[-1]:.2f} mm sampled at {step} mm",
    )

    worst = max(
        (max(widths[: i + 1]) - widths[i], samples[i]) for i in range(len(samples))
    )
    r.check(
        worst[0] <= 1e-9,
        "no lip below the rim can retain the tube",
        f"best undercut anywhere below z={c.TOP_ARC_Z:.2f} is {worst[0]:.3f} mm",
    )
    r.check(
        2 * half_width(c.RIM_Z) >= c.WIDTH - 1e-9,
        "the trough's mouth is the tube's full width, so it slides in freely",
        f"{2 * half_width(c.RIM_Z):.2f} mm at the rim against {c.WIDTH:.2f} overall",
    )


def check_stand(r: Report) -> None:
    """The folding tripod stand: post, three legs, two keepers."""
    post = stand_mod.create_post()
    leg = leg_mod.create_leg()
    keeper = keeper_mod.create_keeper()

    check_stand_no_undercut(r)
    check_stand_trough(post, r)
    check_stand_seat(post, r)
    check_stand_stations(post, keeper, r)
    check_stand_seated(r)
    check_stand_legs(leg, r)
    if SKIP_STAND_EDGES:
        r.section("stand: edges")
        r.check(
            True,
            "SKIPPED -- the house edge rule is NOT verified on these three parts",
            "checks.SKIP_STAND_EDGES is True; check_stand_edges still exists and "
            "still fails. This line is a record that the check did not run, not "
            "a pass of it",
        )
    else:
        check_stand_edges(post, leg, keeper, r)

    r.section("stand: it stands up")
    post_g = post.volume * ASA_DENSITY
    leg_g = leg.volume * ASA_DENSITY
    keeper_g = keeper.volume * ASA_DENSITY
    f_tip = sc.tip_force(post_g + 2 * keeper_g, leg_g)
    r.check(
        f_tip > 0.5,
        "tip force at the top of the tube",
        f"{f_tip:.2f} N ({f_tip / 9.81 * 1000:.0f} g of push) at a "
        f"{sc.leg_reach():.0f} mm reach -- studio class, weight it down",
    )
    r.check(
        True,
        "printed mass",
        f"post {post_g:.0f} g + 3 x leg {leg_g:.0f} g + 2 x keeper {keeper_g:.0f} g "
        f"= {post_g + 3 * leg_g + 2 * keeper_g:.0f} g",
    )
    for name, part in (("post", post), ("leg", leg), ("keeper", keeper)):
        bb = part.bounding_box()
        r.check(
            len(part.solids()) == 1 and bb.size.X <= BED and bb.size.Y <= BED,
            f"{name} is one solid and fits the bed",
            f"{len(part.solids())} solid, {bb.size.X:.0f} x {bb.size.Y:.0f} mm, "
            f"bed {BED:.0f}",
        )


def check_stand_trough(part: Part, r: Report) -> None:
    """The post is the family's cradle section, stood on end."""
    r.section("stand: the trough")
    z = (sc.STATIONS[0] + sc.STATIONS[1]) / 2  # clear of both stations' pads

    r.check(
        not is_solid_at(part, 0.0, 0.0, z),
        "the tube's own space is empty",
        f"sampled on the axis at z={z:.0f}",
    )
    back = -(c.HEIGHT + mc.BORE_FIT) / 2
    r.check(
        is_solid_at(part, 0.0, back - mc.CRADLE_WALL / 2, z)
        and not is_solid_at(part, 0.0, back - mc.CRADLE_WALL - 1.0, z),
        "a full wall behind the tube",
        f"{mc.CRADLE_WALL:.1f} mm from y={back:.2f} to {back - mc.CRADLE_WALL:.2f}",
    )
    r.check(
        not is_solid_at(part, 0.0, sc.MOUTH_Y + 1.0, z),
        "the mouth is open above the rim",
        f"nothing at y={sc.MOUTH_Y + 1:.2f}, so the diffuser is never shadowed "
        f"except by a keeper",
    )
    flank = (c.WIDTH + mc.BORE_FIT) / 2
    r.check(
        is_solid_at(part, flank + mc.CRADLE_WALL / 2, 0.0, z),
        "and full walls beside it",
        f"sampled at x={flank + mc.CRADLE_WALL / 2:.2f}",
    )


def check_stand_seat(part: Part, r: Report) -> None:
    """The seat, and the one identity design-notes S10 turned on."""
    r.section("stand: the seat and the cable")
    y = -(sc.WELL_D / 2 + 2.0)
    r.check(
        is_solid_at(part, 0.0, y, sc.SEAT_Z - 1.0)
        and not is_solid_at(part, 0.0, y, sc.SEAT_Z + 1.0),
        "the endcap lands on solid material",
        f"seat at z={sc.SEAT_Z:.1f}, sampled at y={y:.2f} -- outside the "
        f"{sc.WELL_D:.2f} well, inside the tube's own footprint",
    )
    r.check(
        sc.SEAT_Z > sc.FLANGE_T,
        "the seat is above the flange, not in it",
        f"{sc.SEAT_Z:.1f} against a {sc.FLANGE_T:.0f} mm flange",
    )

    # S10's identity, used forwards: what stands in line with the gland is the
    # whole run from the seat to the floor, and it is derived from the cable.
    in_line = sc.SEAT_Z + sc.LEG_T
    r.check(
        in_line >= gl.free_length() - 1e-9,
        "nothing in line with the gland for the cable's first run",
        f"{in_line:.1f} mm of clear drop against free_length() = "
        f"{gl.free_length():.1f} (gland {mc.GLAND_PROUD:.1f} + stub "
        f"{gl.CABLE_STUB:.0f})",
    )
    clear = all(
        not is_solid_at(part, 0.0, 0.0, z)
        for z in (0.5, sc.FLANGE_T / 2, sc.FLANGE_T + 2.0, sc.SEAT_Z - 1.0)
    )
    r.check(
        clear,
        "and the bore proves it rather than the arithmetic alone",
        f"four samples on the axis from z=0.5 to {sc.SEAT_Z - 1:.1f}, all empty",
    )
    r.check(
        sc.WELL_D >= mc.GLAND_ENV_D,
        "the bore clears the fitted gland's envelope",
        f"{sc.WELL_D:.2f} against {mc.GLAND_ENV_D:.2f} across the hex corners",
    )


def check_stand_stations(post: Part, keeper: Part, r: Report) -> None:
    """The keeper stations: what they grip, and what holds them."""
    r.section("stand: the keeper stations")
    low = sc.STATIONS[0] - sc.KEEPER_W / 2
    r.check(
        low >= sc.SEAT_Z + e.CAP_T,
        "the lower keeper grips aluminium, not the endcap",
        f"station starts at z={low:.1f}; the endcap ends at "
        f"{sc.SEAT_Z + e.CAP_T:.2f} (design-notes S3: no mount loads the "
        f"two M2 self-tappers)",
    )
    for centre in sc.STATIONS:
        bottom, top = stand_mod.station_z(centre)
        r.check(
            not is_solid_at(post, sc.PEG_U, sc.PEG_Y, top - sc.PEG_L / 2),
            f"socket at z={centre:.0f} is open",
            f"pad {bottom:.1f}..{top:.1f}, socket {sc.SOCKET_DEPTH:.0f} deep",
        )
        r.check(
            is_solid_at(post, sc.PEG_U, sc.PEG_Y, bottom + 1.0),
            f"and bottoms on a floor at z={centre:.0f}",
            f"{sc.PAD_H - sc.SOCKET_DEPTH:.1f} mm of pad under it",
        )

    r.check(
        sc.PEG_FIT > 0,
        "the peg is a sliding fit in ASA, not a press",
        f"{sc.PEG_FIT:.2f} mm diametral -- fits.SLIDING for ASA; SNUG there is "
        f"an interference",
    )
    stress = sc.peg_bearing_stress()
    r.check(
        stress < 10.0,
        "the pegs carry the abuse case as bearing, not as a snap",
        f"{sc.keeper_pull():.0f} N over 2 x {sc.PEG_D:.0f} x {sc.PEG_L:.0f} mm "
        f"= {stress:.2f} MPa, against 10 MPa sustained (design-notes S3)",
    )

    # The keeper touches nothing: same rule as strap.py.
    r.check(
        sc.KEEPER_CLEAR >= mc.DIFFUSER_CLEAR - 1e-9,
        "the keeper clears the diffuser rather than pressing on it",
        f"{sc.KEEPER_CLEAR:.1f} mm all round, the family's DIFFUSER_CLEAR",
    )
    crown = c.HEIGHT / 2 + sc.KEEPER_CLEAR
    r.check(
        not is_solid_at(keeper, 0.0, crown - 0.3, sc.KEEPER_W / 2)
        and is_solid_at(keeper, 0.0, crown + sc.KEEPER_T / 2, sc.KEEPER_W / 2),
        "and the crown is where that clearance says it is",
        f"bore ends at y={crown:.2f}, {sc.KEEPER_T:.1f} mm of wall above it",
    )
    r.check(
        crown - c.HEIGHT / 2 <= mc.DIFFUSER_CLEAR + 1e-9,
        "so the tube's play is bounded by the keeper, not by the trough",
        f"{crown - c.HEIGHT / 2:.1f} mm before the tube meets the crown -- it "
        f"cannot leave the mouth without passing that",
    )


def check_stand_seated(r: Report) -> None:
    """The keepers as ``assemblies.standing`` actually places them.

    Every other check on this family measures a part in its own frame, and that
    is exactly the blind spot this one covers: a keeper can be perfect and still
    go into the post upside down. It printed pegs-up and the sockets open
    upward, so ``seated_keepers`` has to turn it over -- and nothing above would
    notice if it stopped. The symptom is not subtle in the viewer (two pegs
    standing in the air, the arch floating half its own width clear of the pads)
    and it was invisible here, so it is stated as a test rather than left to the
    eye.

    Sampled on the *placed* solids, not derived from the same offsets that
    place them: an assertion recomputed from the expression under test passes
    whatever that expression says.
    """
    r.section("stand: the keepers, as seated")
    post = stand_mod.seated()
    keepers = stand_mod.seated_keepers()

    r.check(
        len(keepers) == len(sc.STATIONS),
        "one keeper per station",
        f"{len(keepers)} keepers, {len(sc.STATIONS)} stations",
    )
    for keeper, centre in zip(keepers, sc.STATIONS):
        top = stand_mod.station_z(centre)[1] + sc.LEG_T  # the pads' seating face
        floor = top - sc.SOCKET_DEPTH
        bb = keeper.bounding_box()

        for u in (sc.PEG_U, -sc.PEG_U):
            r.check(
                is_solid_at(keeper, u, sc.PEG_Y, top - sc.PEG_L / 2),
                f"the peg at u={u:+.0f} is down in its socket at z={centre:.0f}",
                f"keeper material on the socket's axis {sc.PEG_L / 2:.0f} mm "
                f"below the pads' face at z={top:.1f} -- pegs point down, the "
                f"way the sockets open",
            )
        r.check(
            bb.min.Z > floor + 1e-9,
            f"and stops short of the socket floor at z={centre:.0f}",
            f"lowest keeper material z={bb.min.Z:.1f} against a floor at "
            f"z={floor:.1f}: it seats on the pads, not on its own peg tips "
            f"(SOCKET_DEPTH's {sc.SOCKET_DEPTH - sc.PEG_L:.1f} mm relief)",
        )
        r.check(
            abs(bb.max.Z - (sc.LEG_T + centre + sc.KEEPER_W / 2)) < 0.01,
            f"the arch is centred on the station at z={centre:.0f}",
            f"crown at z={bb.max.Z:.1f}, half an arch above the station's "
            f"z={sc.LEG_T + centre:.1f}",
        )
        shared = _shared_volume(post, keeper)
        r.check(
            shared < 0.01,
            f"and it fouls nothing on the post at z={centre:.0f}",
            f"{shared:.4f} mm^3 shared -- the pegs are a {sc.PEG_FIT:.2f} mm "
            f"sliding fit and the arch clears the flanks",
        )


def check_stand_legs(part: Part, r: Report) -> None:
    """One leg: the pivot, the stop, and whether three of them nest."""
    r.section("stand: the legs")
    bb = part.bounding_box()
    r.check(
        bb.size.X <= BED - 6.0,
        "the leg fits the smaller bed lying flat, with margin",
        f"{bb.size.X:.0f} mm against a {BED:.0f} mm bed",
    )
    r.check(
        not is_solid_at(part, 0.0, 0.0, sc.LEG_T / 2),
        "the pivot bore goes through",
        f"{sc.PIVOT_CLEAR_D:.1f} mm for an M6",
    )
    r.check(
        not is_solid_at(part, 0.0, sc.PIVOT_NUT_POCKET_D / 2 - 1.0, 1.0)
        and is_solid_at(part, 0.0, sc.PIVOT_NUT_POCKET_D / 2 - 1.0, sc.LEG_T - 1.0),
        "with a nyloc pocket in the underside only",
        f"{sc.PIVOT_NUT_POCKET_D:.2f} across corners, "
        f"{sc.PIVOT_NUT_POCKET_H:.1f} deep, so the leg still lies flat",
    )
    r.check(
        is_solid_at(part, sc.STOP_SLOT_R, 0.0, sc.LEG_T + sc.STOP_PIN_H / 2),
        "the stop pin stands proud of the top face",
        f"{sc.STOP_PIN_D:.2f} x {sc.STOP_PIN_H:.1f} into a "
        f"{sc.STOP_SLOT_W:.1f} x {sc.STOP_SLOT_DEPTH:.1f} slot",
    )
    r.check(
        sc.STOP_PIN_D < sc.STOP_SLOT_W and sc.STOP_PIN_H < sc.STOP_SLOT_DEPTH,
        "and clears the slot it rides in",
        f"{sc.STOP_SLOT_W - sc.STOP_PIN_D:.2f} mm across, "
        f"{sc.STOP_SLOT_DEPTH - sc.STOP_PIN_H:.2f} mm deep",
    )

    # Nesting: the two swinging legs run parallel half-way through the sweep.
    pitch = sc.PIVOT_R * sqrt(3.0)
    gap = pitch * abs(sin(radians(sc.LEG_AZIMUTHS[2] - sc.LEG_FOLD_SWEEP / 2)))
    r.check(
        gap > sc.LEG_W,
        "the two folding legs clear each other mid-sweep",
        f"{gap:.1f} mm between their centre lines against a {sc.LEG_W:.0f} mm bar",
    )
    r.check(
        sum(1 for d in sc.LEG_FOLD_DIRS if d == 0.0) == 1,
        "exactly one leg is indexed rather than swung",
        "a uniform sweep rotates the tripod instead of packing it -- "
        "see config.LEG_FOLD_DIRS",
    )


def _is_stand_socket_mouth(edge) -> bool:
    """A keeper socket's mouth, or the peg tip that seats in it."""
    rad = cradle_mod.arc_radius(edge)
    if rad is None:
        return False
    return any(
        abs(rad - x) < 0.35
        for x in (
            (sc.PEG_D + sc.PEG_FIT) / 2,
            (sc.PEG_D + sc.PEG_FIT) / 2 + sc.PEG_LEAD_IN,
            sc.PEG_D / 2,
            sc.PEG_D / 2 - sc.PEG_LEAD_IN,
        )
    )


def _is_stand_pivot_mouth(edge) -> bool:
    """A pivot bore, its counterbore, their cone lead-ins, or a nut pocket."""
    rad = cradle_mod.arc_radius(edge)
    if rad is None:
        return False
    return any(
        abs(rad - x) < 0.35
        for x in (
            sc.PIVOT_CLEAR_D / 2,
            sc.PIVOT_CLEAR_D / 2 + sc.PIVOT_LEAD_IN,
            sc.PIVOT_CBORE_D / 2,
            sc.PIVOT_CBORE_D / 2 + sc.PIVOT_LEAD_IN,
            sc.STOP_SLOT_W / 2,
            sc.STOP_PIN_D / 2,
        )
    )


def check_stand_edges(post: Part, leg: Part, keeper: Part, r: Report) -> None:
    """The house edge rule on all three printed parts."""
    allow = (
        (
            "hole and socket mouths left to their boolean cones",
            lambda edge: _is_stand_socket_mouth(edge) or _is_stand_pivot_mouth(edge),
            "every hole mouth in this family is coned as a boolean rather than "
            "chamfered as an OCC edge op, so its rim is already at 45 deg and "
            "the arcs that ring it are the cone's own seams",
        ),
        (
            "the nut pocket's flats",
            lambda edge: abs(edge.bounding_box().min.Z) < 0.01
            and abs(edge.bounding_box().max.Z) < 0.01
            and edge.length < sc.PIVOT_NUT_POCKET_D,
            "a hex pocket's six edges bed against a nyloc's flats; breaking "
            "them would only let the nut turn",
        ),
    )
    for name, part in (
        ("stand post", post),
        ("stand leg", leg),
        ("stand keeper", keeper),
    ):
        _check_sharp_edges(part, name, r, allow)


def check_feet(r: Report) -> None:
    """Eye and wall feet: holes clear of the bore, on through-bolts."""
    r.section("Feet")
    for part, name, hole_d, cbore_d in (
        (
            feet_mod.create_eye_foot(),
            "eye foot",
            feet_mod.EYE_HOLE_D,
            feet_mod.EYE_CBORE_D,
        ),
        (
            feet_mod.create_wall_foot(),
            "wall foot",
            feet_mod.WALL_HOLE_D,
            feet_mod.WALL_CBORE_D,
        ),
    ):
        check_mount_basics(part, name, r, max_z=mc.CRADLE_DEPTH)
        check_mount_never_touches(part, name, r)
        # A foot's own exception, on top of every cradle-derived part's shared
        # set: the counterbore mouth (documented, feet.py's module docstring).
        # The counterbore *floor's* step used to need a second one -- it is
        # broken by a cone now (feet._create_foot), so there is nothing left
        # to allow.
        foot_sharp_allow = (
            (
                "counterbore mouth left raw",
                lambda edge, cd=cbore_d: _is_cbore_mouth_edge(edge, cd / 2),
                "feet.py's module docstring: an 0.8 lead-in there would eat "
                "half of PAD_WALL, the only wall between an M6/M5 nyloc and "
                "open air; the nut is dropped in by hand, not found blind",
            ),
            (
                "counterbore mouth left raw -- the same mouth, where it "
                "crosses the pad's own inner-rim chamfer as an ellipse "
                "instead of the flat top",
                lambda edge, cd=cbore_d: _is_cbore_inner_tangency_edge(
                    edge, feet_mod.HOLE_U, cd / 2
                ),
                "only the eye foot's Ø12 counterbore reaches inward far "
                "enough (to HOLE_U - 6 = 14.0) to land inside the chamfered "
                "strip at PAD_U_IN..PAD_U_IN+EDGE_CHAMFER (13.5..14.3); the "
                "chamfer plane and the hole wall are exactly tangent at "
                "z=20.5, where the remaining sliver of chamfer pinches to "
                "zero width -- the same tangency cradle.py's module "
                "docstring already accepts for the trough's bed sliver, "
                "'a chamfer would only turn a shallow edge into a knife "
                "edge'; there is nothing left there to round",
            ),
        )
        check_cradle_edges(part, name, r, extra_sharp_allow=foot_sharp_allow)
        check_foot_edges(part, name, hole_d, r)
    r.check(
        feet_mod.HOLE_U - feet_mod.EYE_HOLE_D / 2 > (c.WIDTH + mc.BORE_FIT) / 2,
        "eye bolts clear the bore",
        f"inner edge at {feet_mod.HOLE_U - feet_mod.EYE_HOLE_D / 2:.2f}, "
        f"bore half-width {(c.WIDTH + mc.BORE_FIT) / 2:.2f}",
    )

    # The nyloc pocket's outboard wall. PAD_U_OUT was typed as 26.0 and
    # HOLE_U + EYE_CBORE_D / 2 is 26.0 exactly, so this was zero -- a slit down
    # the side of the pocket on the one part rated for 20 kg of shock. Same
    # smell as BOSS_U == ARCH_HALF_W: a typed constant equal to a derived one.
    # Checked twice, because the closed form can be right about a shape the
    # builder did not produce.
    pocket = feet_mod.HOLE_U + feet_mod.EYE_CBORE_D / 2
    wall = feet_mod.PAD_U_OUT - pocket
    r.check(
        wall > 1.0,
        "nyloc pocket has an outboard wall",
        f"{wall:.2f} mm = PAD_WALL, {wall / 0.4:.0f} perimeters at 0.4 mm",
    )
    r.check(
        is_solid_at(
            feet_mod.create_eye_foot(),
            mc.CRADLE_LEN / 2,
            pocket + wall / 2,
            mc.CRADLE_DEPTH - feet_mod.CBORE_DEPTH / 2,
        ),
        "...and the solid actually has it, beside the pocket",
    )


def _classify_child(label: str) -> str:
    """ "bought", "printed", or "mock" (bought, but neither side of the check).

    See ``BOUGHT_LABEL_PREFIXES`` for why this is a prefix match, and
    ``MOCK_LABEL_PREFIXES`` for what the third category is for.
    """
    if label.startswith(BOUGHT_LABEL_PREFIXES):
        return "bought"
    if label.startswith(MOCK_LABEL_PREFIXES):
        return "mock"
    return "printed"


def _check_scene_clearance(
    assembly: Compound, name: str, r: Report, expected_bought: int
) -> None:
    """No printed part may share volume with the bought hardware in ``assembly``.

    The bought parts never touch each other in a working lamp (``check_diffuser``
    and ``check_strip`` already hold that to < 0.01 mm^3), so they can be fused
    into one ``Compound`` and intersected against a printed part in a single
    boolean call -- verified on this model to read the same total (zero) as
    summing per-bought-part intersects, at about half the cost. Each part is
    passed through an identity ``Pos`` first: ``Compound(children=...)``
    re-parents whatever shapes it is given, which would silently empty them
    out of ``assembly.children`` -- the same trick ``assemblies/`` uses
    throughout to move a part *without* mutating the source is what keeps this
    a read of the scene instead of a rewrite of it.

    0.01 mm^3 is the same noise floor every other overlap check in this file
    uses, not a stand-in for an allowed cradle-bore touch: every mount in this
    family grips the tube on a clearance fit (``BORE_FIT`` > 0, checked in
    ``check_cradle``), so a genuine foul would read many orders of magnitude
    above this, not just over it.

    ``_classify_child`` treats anything that matches none of
    ``BOUGHT_LABEL_PREFIXES`` as printed, not bought -- so a label rename on
    the bought side would quietly drop a part out of ``bought``, and an empty
    ``bought`` makes every intersect below a no-op (``_shared_volume`` even
    swallows the ``Part.intersect()`` exception an empty ``Compound`` raises
    and reports it as "no overlap"). ``expected_bought`` closes that hole
    explicitly, so drift shows up as a loud, specific FAIL instead of every
    printed part in the scene quietly reading clear.
    """
    bought = [
        child for child in assembly.children if _classify_child(child.label) == "bought"
    ]
    printed = [
        child
        for child in assembly.children
        if _classify_child(child.label) == "printed"
    ]
    r.check(
        len(bought) == expected_bought,
        f"{name}: found all {expected_bought} bought parts",
        f"{len(bought)} classified as bought -- a renamed label would exempt a part from this check silently",
    )
    if not bought:
        return  # nothing to intersect against; the count check above already failed loudly
    bought_all = as_part(Compound(children=[as_part(Pos(0, 0, 0) * b) for b in bought]))
    for part in printed:
        overlap = _shared_volume(part, bought_all)
        r.check(
            overlap < 0.01,
            f"{name}: {part.label} clear of bought hardware",
            f"{overlap:.4f} mm^3 shared with {len(bought)} bought parts",
        )


def _end_face_points(
    part: Part, r: Report, label: str
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """The two points at the ends of a straight tube's own axis, read off the solid.

    The end caps are the **two faces whose centres are farthest apart**. On a
    1.5 m extrusion that is unambiguous and needs no axis at all: every wall,
    web and channel face runs the tube's whole length, so its centre sits at
    mid-length, and any two of those are at most a cross-section apart (~30 mm).
    A lengthwise face to an end cap is ~750 mm; the two end caps are the full
    1500. So the maximum is the pair this wants, whichever way the assembly
    turned the tube -- which keeps this a measurement of the placed solid rather
    than a replay of the Pos/Rotation that built it.

    Two selections have been retired here, and both failed the same way -- they
    were sound for the numbers of the day rather than for the shape:

    * *the two smallest faces.* The end caps are bounded by the ~70 mm^2
      cross-section while lengthwise faces were in the hundreds -- until the
      cavity's inner flank between ``BOT_ARC_Z`` and ``CAVITY_TOP_Z``, which is
      only ``CAVITY_TOP_Z - RADIUS`` tall, came down to 0.05 mm at WIDTH 26.1
      and 75 mm^2. That is 1.07x the end caps, against the 1.5x its own guard
      demanded, and the guard was right to call it.
    * *faces whose normal lies along the solid's longest bounding-box extent.*
      True only for a tube the assembly left axis-aligned; two of the triangle's
      three are rotated to a bearing, and their longest extent is a diagonal.
    """
    # ty resolves Part.faces() to Mixin2D.faces and rejects the receiver; it is
    # the right call at runtime (see led_psu_enclosure/checks.py for the same).
    faces = list(part.faces())  # ty: ignore[invalid-argument-type]
    centres = [f.center() for f in faces]
    best = max(
        (
            ((centres[i] - centres[j]).length, i, j)
            for i in range(len(faces))
            for j in range(i + 1, len(faces))
        ),
        default=(0.0, 0, 0),
    )
    span, i, j = best
    caps = (faces[i], faces[j])

    # Confirm the pick really is a pair of end caps rather than merely the
    # farthest-apart pair of something: both have to be planes, and each has to
    # face *along* the line joining them. On a straight extrusion only the end
    # caps do; every lengthwise face's normal is square to that line.
    axis = (centres[j] - centres[i]).normalized()
    facing = [
        f
        for f in caps
        if f.geom_type == GeomType.PLANE
        # abs(): build123d makes no promise which way a face's normal points.
        and abs(abs(f.normal_at(f.center()).dot(axis)) - 1.0) < 1e-3
    ]
    r.check(
        len(facing) == 2,
        f"{label}: end caps are the farthest-apart pair, and both face along it",
        f"{span:.1f} mm apart over {len(faces)} faces, {len(facing)} of 2 square to the axis",
    )
    matched = abs(caps[0].area - caps[1].area) / caps[1].area
    r.check(
        matched < 0.001,
        f"{label}: the two end caps are a matched pair",
        f"{caps[0].area:.2f} and {caps[1].area:.2f} mm^2, {matched * 100:.3f}% apart",
    )
    c0, c1 = caps[0].center(), caps[1].center()
    return (c0.X, c0.Y, c0.Z), (c1.X, c1.Y, c1.Z)


def _xy_intersect(
    p1: tuple[float, float],
    d1: tuple[float, float],
    p2: tuple[float, float],
    d2: tuple[float, float],
) -> tuple[float, float] | None:
    """Where two lines (point + direction, z ignored) cross in the XY plane."""
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denom) < 1e-9:
        return None
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / denom
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def _check_triangle_geometry(triangle: Compound, r: Report) -> None:
    """The loop closes, and the dark run at each vertex matches ``mount_config``.

    Both come out of one measurement: each lamp's aluminium tube is a straight
    extrusion, so its two end-face centres (``_end_face_points``) fix a line --
    the tube's real axis, in the world frame the assembly actually placed it
    in. Three tubes, three lines; where consecutive lines cross is where
    ``create_triangle`` intended a corner's vertex to sit, but here it is read
    off the tubes themselves, not off the vertex ``triangle_vertices`` computed
    to place them.

    The two checks below the crossing split what "closes" means, and they are
    not redundant: the equilateral check below uses only each tube's
    *direction*, so a bearing error (wrong angle between two tubes) shows up
    there as an unequal side. It is blind to a tube sliding along its own
    axis -- that leaves the infinite line, and so the crossing, unchanged --
    which is exactly the placement error the dark-run check catches, since
    that one measures against each tube's actual finite endpoint. Closure of
    the physical loop is carried by the dark-run check; the equilateral check
    only confirms the derived triangle is the right shape and scale.
    """
    r.section("Triangle geometry")
    lamps = sorted(
        (
            child
            for child in triangle.children
            if child.label.startswith("aluminium profile (lamp ")
        ),
        key=lambda child: child.label,
    )
    r.check(len(lamps) == 3, "found the three lamp tubes", f"{len(lamps)} of them")
    if len(lamps) != 3:
        return

    lines: list[
        tuple[
            tuple[float, float, float], tuple[float, float, float], tuple[float, float]
        ]
    ] = []
    for lamp in lamps:
        p0, p1 = _end_face_points(lamp, r, lamp.label)
        lines.append((p0, p1, (p1[0] - p0[0], p1[1] - p0[1])))

    # Coplanar: every tube level along its own length, and all three at the
    # same height -- the LED faces have to line up around the loop, not just
    # the loop closing in plan view.
    z0 = lines[0][0][2]
    for lamp, (p0, p1, _d) in zip(lamps, lines):
        r.check(
            abs(p0[2] - p1[2]) < 0.01 and abs(p0[2] - z0) < 0.01,
            f"{lamp.label}: level, and at the loop's common height",
            f"ends at z={p0[2]:.3f}/{p1[2]:.3f} mm",
        )

    # Consecutive tube axes, extended, cross at the triangle's three vertices --
    # not at the tube endpoints themselves, which sit `cradle_start` short of
    # the true corner (that gap is what the dark-run check below measures).
    pairs = ((0, 1), (1, 2), (2, 0))
    verts: list[tuple[float, float]] = []
    for a, b in pairs:
        pa, _pa1, da = lines[a]
        pb, _pb1, db = lines[b]
        v = _xy_intersect((pa[0], pa[1]), da, (pb[0], pb[1]), db)
        r.check(
            v is not None,
            f"lamps {a}/{b}: axes are not parallel",
            "a closed loop needs a real crossing",
        )
        verts.append(v if v is not None else (0.0, 0.0))

    # Scale/shape only: this depends solely on each tube's direction, not on
    # where along its own axis the tube actually sits, so it cannot see a
    # tube slid lengthwise (same line, same crossing) -- that placement error
    # is what the dark-run check right below exists to catch.
    sides = [
        hypot(verts[i][0] - verts[(i + 1) % 3][0], verts[i][1] - verts[(i + 1) % 3][1])
        for i in range(3)
    ]
    mean_side = sum(sides) / 3
    for i, side in enumerate(sides):
        r.check(
            abs(side - mean_side) < 0.01,
            f"edge {i}: derived vertex triangle is equilateral (scale check)",
            f"{side:.3f} mm vs mean {mean_side:.3f} mm -- a bearing/angle error would show up here; "
            "an axial placement error would not, see the dark-run check below",
        )

    # Dark run: at each measured vertex, the unlit length is the sum of both
    # tubes' distance from their own aluminium end back to that vertex -- the
    # quantity mount_config.dark_run describes as "both sides". This is the
    # check that actually constrains each tube's position along its own axis
    # (via its real endpoint, not just its direction), so it is what carries
    # "the loop closes" -- not just its own claim, but the equilateral check's
    # too.
    want = mc.dark_run(60.0)
    for i, (a, b) in enumerate(pairs):
        vx, vy = verts[i]
        run = 0.0
        for lamp_idx in (a, b):
            p0, p1, _d = lines[lamp_idx]
            near = (
                p0
                if hypot(p0[0] - vx, p0[1] - vy) < hypot(p1[0] - vx, p1[1] - vy)
                else p1
            )
            run += hypot(near[0] - vx, near[1] - vy)
        r.check(
            abs(run - want) < 0.01,
            f"vertex {i}: dark run matches mount_config.dark_run(60)",
            f"{run:.2f} mm measured (both sides, via the crossing) vs {want:.2f} mm predicted",
        )


def _check_suspended_bessel_points(suspended: Compound, r: Report) -> None:
    """The two hang points sit at the Bessel points, read off the real feet.

    An eye foot's own bounding box is symmetric about its bolt-hole station
    along the tube (``feet._create_foot`` centres both the boss pads and the
    holes on ``CRADLE_LEN / 2``, and the cradle itself runs the full length
    either side of that), so the box's own X centre in world space -- after
    ``feet.seated``'s pure X-translation -- is exactly the hang point.
    Sorting both the measured pair and ``bessel_points()`` before comparing
    avoids assuming which foot in the scene is the "near" one.
    """
    r.section("Suspended: Bessel points")
    feet = [child for child in suspended.children if child.label == "eye foot"]
    r.check(len(feet) == 2, "found both eye feet", f"{len(feet)}")
    if len(feet) != 2:
        return
    measured = sorted(foot.bounding_box().center().X for foot in feet)
    want = sorted(assemblies.bessel_points())
    for i, (m, w) in enumerate(zip(measured, want)):
        r.check(
            abs(m - w) < 0.01,
            f"foot {i}: hang point at its Bessel point",
            f"{m:.2f} mm measured vs {w:.2f} mm = 0.2203 x length from the end",
        )


def check_assemblies(r: Report) -> None:
    """Whole-lamp scenes: printed parts against bought hardware, at full scale.

    Every scene here is built at its default LENGTH (1.5 m). Shortening the
    tube would not meaningfully speed this up -- the cost is dominated by
    endcap threads and corner booleans, both independent of tube length
    (measured: LENGTH=200 only shaved ~13% off the triangle build) -- while it
    would weaken ``_end_face_points``' area-based pick of the tube's end
    faces, which needs the flank/web faces to keep running the tube's full
    length to stay far bigger than the end caps. So the full-size scene is
    worth what it costs.
    """
    r.section("Assemblies")
    suspended = assemblies.create_suspended()
    standing = assemblies.create_standing()
    triangle = assemblies.create_triangle()

    # One lamp's worth of bought hardware -- alu, carrier, emitter, diffuser
    # (``profile.create_extrusion``/``create_strip``/``create_diffuser``) -- per
    # lamp in the scene: one lamp in the suspended and standing views, three
    # around the triangle.
    bought_per_lamp = len(BOUGHT_LABEL_PREFIXES)
    _check_scene_clearance(suspended, "suspended", r, expected_bought=bought_per_lamp)
    _check_scene_clearance(standing, "standing", r, expected_bought=bought_per_lamp)
    _check_scene_clearance(triangle, "triangle", r, expected_bought=3 * bought_per_lamp)

    _check_triangle_geometry(triangle, r)
    _check_suspended_bessel_points(suspended, r)


def _shared_volume(a: Part, b: Part) -> float:
    """Volume common to two parts. Zero unless something interferes."""
    try:
        common = a.intersect(b)
    except Exception:
        return 0.0  # OCC raises rather than returning an empty shape
    if common is None:
        return 0.0
    # intersect() hands back either a single shape or a ShapeList of them.
    shapes = list(common) if isinstance(common, list) else [common]
    return float(sum(s.volume for s in shapes))


# ------------------------------------------------------- sharp convex edges
#
# ``AGENTS.md`` has always said "never ship a part with raw square edges",
# and a corner shipped with one chamfer and passed 185 assertions before
# anyone noticed (models/lib/checks.py's own module docstring).
# ``sharp_convex_edges`` makes the rule falsifiable; nothing called it until
# here, so the whole family below is the first time it has ever been
# enforced. Every legitimate raw edge is an *allow* entry -- a predicate, a
# reason, and (below) a count -- so an exception has to be stated, not merely
# not noticed.
#
# The audit's first run left five findings that resolved to no design
# decision at all, labelled KNOWN GAP and left to the model files. Four have
# since been fixed in the geometry rather than in the allow-list -- the
# curved-floor drain funnels (cradle.drain_funnel), the counterbore floor
# steps (feet, stand), the cable slot's mouth (stand._cable_mouth_flare) and
# the corner's own trough-mouth fillet (corner.MOUTH_FILLET, which was also
# putting material inside the endcap collar). Two remain, both stated in
# their own reason rather than folded into a neighbouring one: the well /
# cable-slot crossing's horizontal pair, and the socket-root fillet's run-out
# at the collar exclusion.
#
# **An allow entry is a claim about what an edge is, not a way to get to
# green.** The run-out pair spent a release inside the "collar bore root"
# entry, matched by a position test five times looser than the exclusion that
# produced them, and a reason about the cap's seat that did not describe them
# at all -- which is worse than the prose rule this replaced, because it
# stops anyone looking. Predicates here match on the thing itself (an arc's
# own radius, a face's own plane), and fall back to position only where there
# is no radius to match.

_SEAM_BORE_R = (c.WIDTH + mc.BORE_FIT) / 2  # 13.035 -- same as `bore` below


def _edge_radius(edge) -> float | None:
    """An edge's radius, or None if it is straight. Same trick as
    ``cradle.arc_radius``/``corner._arc_radius``/``stand._arc_radius``:
    ``Edge.radius`` raises on a line rather than returning None."""
    try:
        return edge.radius
    except Exception:  # noqa: BLE001 -- "not a circle" is the answer, not an error
        return None


def _is_insert_mouth_edge(edge) -> bool:
    """The heat-set insert mouth, family-wide: a printed lead-in removes the
    material the insert has to melt into, so every ``INSERT_D`` hole is left
    raw on purpose (``cradle.is_insert_mouth``, ``corner._is_insert_mouth``,
    and the stand's own copy of the same rule)."""
    r = _edge_radius(edge)
    return r is not None and abs(r - mc.INSERT_D / 2) < 0.05


def _is_trough_seam_edge(edge, top_z: float) -> bool:
    """An edge that belongs to the cradle-derived bore/wall's own
    cross-section, exposed wherever the trough is axially discontinuous: its
    two open ends, and (on cradle/feet/corner) the two band/relief-step
    transitions. Named and excluded from filleting by the module's own
    selectors -- ``cradle.vertical_corners``: "the short verticals inside a
    trough's stadium... at the bore's relief step, and down the seam of
    every bore and counterbore, none of which may be rounded"; identical
    wording in ``corner._vertical_corners``. Matched the same way those
    selectors exclude it: by the arc's own radius for the curved pieces, and
    by the same length-below-``top_z``-derived threshold, on a genuinely
    vertical edge, for the short straight ones in between.

    **The margin on that threshold is load-bearing, not the threshold.** This
    is the exact complement of the construction selector -- ``cradle
    .vertical_corners`` and ``corner._vertical_corners`` both keep
    ``length > 0.6 * top_z``, this keeps ``<=`` -- so the two can never both
    claim an edge, or both miss one. What makes it *safe* rather than merely
    complementary is that the seam edges it matches are 3.0 mm against a
    17.28 mm ceiling: nearly six times' clearance. Narrow the window towards
    the real lengths and it stops being a complement and starts being a
    tuned filter, which is how a fillet residual gets absorbed by a
    neighbouring reason (see ``_is_socket_root_runout`` for the one that did).
    """
    r = _edge_radius(edge)
    if r is not None and abs(r - _SEAM_BORE_R) < 0.02:
        return True
    if r is not None and abs(r - mc.CRADLE_OUTER_HALF_W) < 0.02:
        return True
    if edge.geom_type != GeomType.LINE:
        return False
    bb = edge.bounding_box()
    return edge.length <= 0.6 * top_z and bb.size.X < 0.05 and bb.size.Y < 0.05


def _is_bed_sliver(edge) -> bool:
    """cradle.py's documented 2.2 mm bed sliver: 'the trough's own footprint
    on the bed... its corner is already a ~4 deg tangency, so there is
    nothing there to break' (module docstring; also asserted directly in
    ``check_cradle_edges``)."""
    bb = edge.bounding_box()
    return bb.max.Z < 0.02 and 1.5 < edge.length < 3.0


def _is_cbore_mouth_edge(edge, cbore_r: float) -> bool:
    """A foot's counterbore mouth, at the open (top) face -- feet.py's own
    module docstring: 'an 0.8 lead-in there would eat half of PAD_WALL...
    the nut is dropped in by hand from the open side rather than found
    blind.' Documented, deliberate."""
    r = _edge_radius(edge)
    bb = edge.bounding_box()
    return (
        r is not None
        and abs(r - cbore_r) < 0.05
        and abs(bb.min.Z - mc.CRADLE_DEPTH) < 0.05
    )


def _is_cbore_inner_tangency_edge(edge, hole_u: float, cbore_r: float) -> bool:
    """The same counterbore mouth as ``_is_cbore_mouth_edge``, on the short
    stretch where the hole's cylindrical wall crosses the pad's own
    inner-rim chamfer instead of the flat top.

    ``cradle.treat_edges`` chamfers the whole rim -- including the pad's
    inner-top edge, at ``feet_mod.PAD_U_IN`` (13.5) rising to
    ``PAD_U_IN + EDGE_CHAMFER`` (14.3) over ``z`` = ``CRADLE_DEPTH -
    EDGE_CHAMFER`` (20.0) to ``CRADLE_DEPTH`` (20.8) -- *before* ``feet.py``
    cuts the counterbore. The eye foot's Ø12 counterbore reaches inward to
    ``hole_u - cbore_r`` = 14.0, which lands inside that chamfered strip
    rather than clear of it (the wall foot's Ø10 counterbore stops at 15.0,
    past ``PAD_U_IN + EDGE_CHAMFER``, so it never shows this edge). Where the
    two surfaces cross, the hole's wall no longer meets flat material: it
    meets the sloped chamfer plane, so the mouth's boundary there is an
    ellipse (a cylinder cutting a 45 deg plane), not a circle, and does not
    match ``_is_cbore_mouth_edge``'s radius test even though it is the same
    raw mouth.

    It is also a genuine tangency, not just a differently-shaped edge: the
    chamfer plane and the hole wall coincide exactly at
    ``z = CRADLE_DEPTH - EDGE_CHAMFER + (hole_u - cbore_r - PAD_U_IN)``
    (20.5 on the eye foot), where the remaining wedge of chamfer material
    pinches to zero width -- confirmed by point-sampling on either side of
    it. That is the same shape of artifact ``cradle.py``'s own module
    docstring already accepts for the trough's bed sliver: 'its corner is
    already a ~4 deg tangency, so there is nothing there to break, and a
    chamfer would only turn a shallow edge into a knife edge.' There is no
    material left near the pinch point to round without manufacturing a
    sharper edge than the one being left raw.
    """
    if edge.geom_type != GeomType.ELLIPSE:
        return False
    bb = edge.bounding_box()
    inner = hole_u - cbore_r
    y = abs(edge.center().Y)
    return (
        abs(bb.max.Z - mc.CRADLE_DEPTH) < 0.05
        and bb.min.Z > mc.CRADLE_DEPTH - mc.EDGE_CHAMFER - 0.05
        and abs(y - inner) < mc.EDGE_CHAMFER
    )


def _check_sharp_edges(
    part: Part,
    name: str,
    r: Report,
    allow: tuple[tuple[str, Callable[[object], bool], str], ...],
) -> None:
    """The raw-edge rule, made falsifiable, for one already-built part.

    Calls ``sharp_convex_edges`` exactly once with no ``allow`` of its own --
    building the adjacency map is the expensive part of that function, and
    the raw, unfiltered lists are also the only way to report *how many*
    edges each exception actually accounts for. Every classification below is
    therefore done in plain Python against those two lists, not by asking the
    kernel again.

    ``sharp_convex_edges`` now returns a ``SharpEdgeSurvey`` -- a measured,
    too-sharp bucket and a could-not-be-measured bucket, which are different
    claims (see that type's docstring). Both are walked through the *same*
    ``allow`` triples here, because an allow predicate matches an edge's
    geometry, not its angle: the same "screw seat's tail sliver" reason, say,
    is just as valid an explanation whether that edge happened to measure
    sharp or came back unmeasurable. ``allow`` is a list of
    ``(label, predicate, reason)`` triples, applied in order to each bucket;
    whatever no predicate claims, in *either* bucket, is asserted to be empty
    -- the hard gate the rest of the family never had before this file, and
    now covering both claims instead of only the one ``ShapeList`` could
    represent.
    """
    survey = sharp_convex_edges(part)
    r.check(
        True,
        f"{name}: sharp convex edges found before allow-listing",
        f"{len(survey.sharp)}",
    )
    r.check(
        True,
        f"{name}: unclassifiable convex edges found before allow-listing",
        f"{len(survey.unclassifiable)}",
    )

    def _account_for(edges: list, bucket: str) -> list:
        remaining = list(edges)
        for label, predicate, reason in allow:
            matched = [edge for edge in remaining if predicate(edge)]
            remaining = [edge for edge in remaining if not predicate(edge)]
            r.check(
                True, f"{name}: {bucket}: {label}", f"{len(matched)} edges -- {reason}"
            )
        return remaining

    def _detail(remaining: list) -> str:
        if not remaining:
            return "all accounted for"
        return f"{len(remaining)} left: " + "; ".join(
            f"{edge.geom_type} len={edge.length:.2f} at "
            f"{tuple(round(v, 2) for v in edge.bounding_box().center())}"
            for edge in remaining
        )

    remaining_sharp = _account_for(list(survey.sharp), "sharp")
    remaining_unclassifiable = _account_for(
        list(survey.unclassifiable), "unclassifiable"
    )
    r.check(
        not remaining_sharp,
        f"{name}: no unexplained sharp convex edges",
        _detail(remaining_sharp),
    )
    r.check(
        not remaining_unclassifiable,
        f"{name}: no unexplained unclassifiable convex edges",
        _detail(remaining_unclassifiable),
    )


def run() -> Report:
    r = Report()
    length = c.SECTION_LENGTH
    alu = create_extrusion(length)
    diffuser = create_diffuser(length)
    carrier, _emitter = create_strip(length)

    check_outline(alu, r)
    check_wiring_cavity(alu, r)
    check_channel(alu, r)
    check_screw_ports(alu, r)
    check_diffuser(alu, diffuser, r)
    check_strip(alu, carrier, r)

    cap = e.create_endcap()
    check_endcap(cap, r)
    check_screw_pockets(cap, r)
    check_gland(cap, r)
    check_gland_pocket(cap, r)
    check_plug_shell(cap, r)
    check_strap_slot(cap, r)
    check_endcap_edges(cap, r)

    capw = ew.create_endcap_wired()
    check_endcap_wired(capw, r)
    check_wired_screws(capw, r)
    check_wired_chamber(capw, r)
    check_strap_slot(capw, r, section="Wired endcap strap slot")
    check_wired_edges(capw, r)

    check_cap_on_profile(r)
    check_assembly(r)

    check_cradle(create_cradle(), r)
    check_strap(strap_mod.create_strap(), r)
    check_corner(r)
    check_stand(r)
    check_feet(r)
    check_assemblies(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
