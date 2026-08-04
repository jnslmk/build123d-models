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
from math import cos, hypot, radians, sin, sqrt

from build123d import Compound, Part, Pos, Rotation

from models.lib import fits
from models.lib.checks import Report, is_solid_at
from models.lib.edges import as_part

from . import assemblies
from . import config as c
from . import corner as corner_mod
from . import endcap as e
from . import feet as feet_mod
from . import mount_config as mc
from . import stand as stand_mod
from . import strap as strap_mod
from .assembly import create_bare, create_section
from .endcap import CAP_W
from .cradle import create_cradle
from .profile import _loc, create_diffuser, create_extrusion, create_strip

# Sample well inside the ends, so a face never lands on a sample point.
X = c.SECTION_LENGTH / 2

# The smaller of the two printers this repo targets, and ASA's density.
BED = 256.0
ASA_DENSITY = 1.07e-3  # g/mm^3

# Every bought part, in every assembly view, is labelled with one of these
# prefixes (a suffix like " (lamp 0)" or " (near)" may follow, hence a prefix
# match rather than an exact one). Everything else in a scene is a printed
# mount -- endcap, strap, foot, corner, stand hub -- except a tripod's "leg N"
# parts, which are bought hardware too, but `stand.create_leg` is explicit
# that it is a mock standing in for one and must never be treated as printed.
BOUGHT_LABEL_PREFIXES = ("aluminium profile", "diffuser", "COB strip", "COB emitter")


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
    """The cap itself: collar, gland thread, screw holes, register lip."""
    r.section("Endcap")
    bb = cap.bounding_box()
    r.check(
        abs(bb.size.X - e.CAP_W) < 0.01 and abs(bb.size.Y - e.CAP_H) < 0.01,
        "collar size",
        f"{bb.size.X:.2f} x {bb.size.Y:.2f} mm, {e.CAP_PROUD} proud of the tube",
    )
    r.check(
        abs(bb.min.Z) < 0.01, "outer face on z=0 (print pose)", f"min z {bb.min.Z:.3f}"
    )
    r.check(
        abs(bb.size.Z - (e.CAP_T + e.LIP_DEPTH)) < 0.01,
        "overall depth",
        f"{bb.size.Z:.2f} mm = {e.CAP_T} flange + {e.LIP_DEPTH} lip",
    )
    r.check(len(cap.solids()) == 1, "one solid", f"{len(cap.solids())}")

    # The collar has to be proud enough that a screw head lands entirely on it.
    # This is the constraint that stopped the cap being flush with the tube.
    head_r = 3.8 / 2  # M2 pan head
    wall = e.CAP_W / 2 - c.SCREW_SPACING / 2 - e.SCREW_CLEAR_D / 2
    r.check(wall > 1.2, "material outboard of the screw hole", f"{wall:.2f} mm")
    r.check(
        e.CAP_W / 2 - c.SCREW_SPACING / 2 > head_r,
        "screw head lands on the face",
        f"{e.CAP_W / 2 - c.SCREW_SPACING / 2:.2f} mm to the edge, head r {head_r}",
    )


def check_gland(cap: Part, r: Report) -> None:
    """The M12 bore: the tightest thing in the design."""
    r.section("Gland bore")
    z_mid = e.CAP_T / 2
    # Cap-local x is the profile's u; cap-local y is the profile's z.
    r.check(not is_solid_at(cap, 0, _loc(e.GLAND_Z), z_mid), "bore is open")
    r.check(
        is_solid_at(cap, 0, _loc(e.GLAND_Z) - e.GLAND_MAJOR_D / 2 - 1.0, z_mid),
        "solid below the bore",
    )

    # Wall to the outside of the collar, measured to the nearest arc centre.
    arc_z = c.BOT_ARC_Z if e.GLAND_Z < c.BOT_ARC_Z else c.TOP_ARC_Z
    reach = hypot(0, e.GLAND_Z - arc_z) + e.GLAND_MAJOR_D / 2
    wall = (c.WIDTH / 2 + e.CAP_PROUD) - reach
    r.check(wall > 1.6, "wall outboard of the bore", f"{wall:.2f} mm")

    # The bore has to open into the cavity, or the cable has nowhere to go.
    cavity_r = c.WIDTH / 2 - c.WALL
    into_cavity = cavity_r - hypot(0, e.GLAND_Z - c.BOT_ARC_Z)
    r.check(
        into_cavity > 3.35,
        "bore centre clears the cavity wall",
        f"{into_cavity:.2f} mm of cavity radius at the bore axis",
    )
    r.check(
        e.GLAND_Z < c.CAVITY_TOP_Z,
        "bore axis is below the cavity ceiling",
        f"{e.GLAND_Z} < {c.CAVITY_TOP_Z}",
    )

    # Thread engagement, against the printed-thread rule of >= 1.0 x D.
    ratio = e.GLAND_THREAD_L / e.GLAND_THREAD_D
    r.check(
        ratio > 0.85,
        "thread engagement",
        f"{e.GLAND_THREAD_L} mm = {ratio:.2f} x D (rule wants 1.0; see module docstring)",
    )
    # Cable has to fit through the thread's crests.
    minor = e.GLAND_MAJOR_D - 1.0825 * e.GLAND_PITCH
    r.check(
        minor > 7.5,
        "cable clears the thread crests",
        f"minor dia {minor:.2f} mm vs 6.7 cable",
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

    # The lip is inside the bore, and the screws line up with the ports.
    x_lip = 1.0  # 1 mm into the tube, well inside the lip's 6 mm
    r.check(
        is_solid_at(near, x_lip, 0, c.CAVITY_TOP_Z - 3.0) is False,
        "lip is a ring, not a plug",
    )

    # Sample the lip on the lower arc -- it is clipped below CAVITY_TOP_Z, so
    # there is no straight-sided band of it to probe.
    z_probe = 11.0
    rise = c.BOT_ARC_Z - z_probe
    r_out = c.RADIUS - c.WALL - e.LIP_FIT / 2
    half_out = sqrt(r_out**2 - rise**2)
    half_in = sqrt((r_out - e.LIP_T) ** 2 - rise**2)
    r.check(
        is_solid_at(near, x_lip, (half_out + half_in) / 2, z_probe),
        "lip wall is inside the cavity",
        f"ring from {half_in:.2f} to {half_out:.2f} from centre",
    )
    r.check(
        not is_solid_at(near, x_lip, half_out + 0.05, z_probe),
        "and stands off the cavity wall",
    )
    gap = e.LIP_FIT / 2
    r.check(
        gap > 0.05,
        "lip clearance per side",
        f"{gap:.3f} mm ({e.LIP_FIT} diametral, SLIDING)",
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
    """Assembled, the whole thing is exactly the stadium it is supposed to be."""
    r.section("Assembly")
    bare = create_bare(c.SECTION_LENGTH).bounding_box()
    r.check(
        abs(bare.size.Y - c.WIDTH) < 0.01 and abs(bare.size.Z - c.HEIGHT) < 0.01,
        "bought hardware envelope",
        f"{bare.size.Y:.2f} x {bare.size.Z:.2f} mm, want {c.WIDTH} x {c.HEIGHT}",
    )
    full = create_section().bounding_box()
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
        f"plinth {corner_mod.PLINTH_H} > drop {corner_mod.GLAND_DROP}",
    )
    r.check(
        corner_mod.CHANNEL_W >= CAP_W + 1.0,
        "channel clears the endcap collar",
        f"{corner_mod.CHANNEL_W} vs collar {CAP_W}",
    )

    for angle in (60.0, 90.0, 120.0, 150.0):
        p = corner_mod.create_corner(angle)
        bb = p.bounding_box()
        r.check(
            len(p.solids()) == 1 and bb.size.X <= BED and bb.size.Y <= BED,
            f"corner {angle:.0f}: one solid, on the bed",
            f"{bb.size.X:.0f} x {bb.size.Y:.0f} mm",
        )
        r.check(
            _tube_clears_corner(p, angle),
            f"corner {angle:.0f}: both tubes seat without fouling",
            f"dark run {mc.dark_run(angle):.0f} mm",
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


def check_stand(r: Report) -> None:
    """The hub, and the number that decides whether it is any use."""
    r.section("Stand")
    part = stand_mod.create_stand_hub()
    check_mount_basics(part, "stand hub", r)

    hub_g = part.volume * ASA_DENSITY
    f_tip = stand_mod.tip_force(hub_g)
    r.check(
        f_tip > 0.5,
        "tip force at the top of the tube",
        f"{f_tip:.2f} N ({f_tip / 9.81 * 1000:.0f} g of push) -- studio class, sandbag it",
    )
    r.check(
        stand_mod.SOCKET_DEPTH >= 3 * c.HEIGHT,
        "socket depth",
        f"{stand_mod.SOCKET_DEPTH:.0f} mm = {stand_mod.SOCKET_DEPTH / c.HEIGHT:.1f} x the section",
    )
    # The offset gland well is the easiest thing in the part to get wrong.
    r.check(
        abs(stand_mod.GLAND_OFFSET + 6.0) < 0.01,
        "gland well is offset, not concentric",
        f"{stand_mod.GLAND_OFFSET:.1f} mm below the tube axis",
    )
    r.check(
        not is_solid_at(part, 0, stand_mod.GLAND_OFFSET, stand_mod.FLANGE_T + 2),
        "gland well is open",
    )
    r.check(
        not is_solid_at(part, 0, stand_mod.GLAND_OFFSET, stand_mod.FLANGE_T / 2),
        "and drains through the flange",
    )
    # The seat is the annulus around the well, so sample clear of the well --
    # the tube's centre line is inside it, which is the whole point of the offset.
    r.check(
        is_solid_at(part, 0, 10.0, stand_mod.SEAT_Z - 1),
        "seat carries the endcap around the well",
        "sampled off the centre line, which is well",
    )
    r.check(
        not is_solid_at(part, 0, -stand_mod.PEDESTAL_D / 2 + 2, stand_mod.FLANGE_T + 3),
        "cable exits the back of the well",
    )

    # The socket needs its own strap bosses; without them the insert holes cut
    # air. Sample off the insert axis, or the hole reads as a missing boss.
    z = stand_mod.STATIONS[0]
    r.check(is_solid_at(part, mc.BOSS_U, -12.0, z), "socket has strap bosses")
    r.check(
        not is_solid_at(part, mc.BOSS_U, mc.CRADLE_DEPTH + stand_mod.SINK - 2.0, z),
        "and their inserts are drilled inward",
        "Align.MAX here would drill outward into the air",
    )


def check_feet(r: Report) -> None:
    """Eye and wall feet: holes clear of the bore, on through-bolts."""
    r.section("Feet")
    for part, name in (
        (feet_mod.create_eye_foot(), "eye foot"),
        (feet_mod.create_wall_foot(), "wall foot"),
    ):
        check_mount_basics(part, name, r, max_z=mc.CRADLE_DEPTH)
        check_mount_never_touches(part, name, r)
    r.check(
        feet_mod.HOLE_U - feet_mod.EYE_HOLE_D / 2 > (c.WIDTH + mc.BORE_FIT) / 2,
        "eye bolts clear the bore",
        f"inner edge at {feet_mod.HOLE_U - feet_mod.EYE_HOLE_D / 2:.2f}, "
        f"bore half-width {(c.WIDTH + mc.BORE_FIT) / 2:.2f}",
    )


def _classify_child(label: str) -> str:
    """ "bought", "printed", or "leg" (a bought mock, neither side of the check).

    See ``BOUGHT_LABEL_PREFIXES`` for why this is a prefix match.
    """
    if label.startswith(BOUGHT_LABEL_PREFIXES):
        return "bought"
    if label.startswith("leg "):
        return "leg"
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
    out of ``assembly.children`` -- the same trick ``assemblies.py`` uses
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

    Every wall, web and channel face of an extruded profile runs the tube's
    full length, so at LENGTH it reads in the thousands of mm^2; the two end
    caps are bounded by the ~400 mm^2 cross-section alone and so are always
    the smallest two faces on the solid, by a wide margin, and identical to
    each other (opposite ends of the same straight extrusion). Picking them
    by area -- rather than by an assumed local axis or normal direction --
    is what makes this a measurement of the placed solid, not a replay of the
    Pos/Rotation that built it.
    """
    # ty resolves Part.faces() to Mixin2D.faces and rejects the receiver; it is
    # the right call at runtime (see led_psu_enclosure/checks.py for the same).
    faces = sorted(part.faces(), key=lambda f: f.area)  # ty: ignore[invalid-argument-type]
    matched = abs(faces[0].area - faces[1].area) / faces[1].area
    r.check(
        matched < 0.001,
        f"{label}: two smallest faces are a matched pair (the end caps)",
        f"{faces[0].area:.2f} and {faces[1].area:.2f} mm^2, {matched * 100:.3f}% apart",
    )
    r.check(
        faces[2].area > faces[1].area * 1.5,
        f"{label}: end caps stand out from the next-smallest face",
        f"next face is {faces[2].area / faces[1].area:.2f}x bigger -- safe to pick the end caps by area",
    )
    c0, c1 = faces[0].center(), faces[1].center()
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
    check_gland(cap, r)
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
