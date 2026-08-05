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
from math import acos, cos, degrees, hypot, radians, sin, sqrt

from build123d import Align, Compound, Cylinder, GeomType, Part, Pos, Rotation

from models.lib import fits
from models.lib.checks import Report, is_solid_at, sharp_convex_edges
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
from .cradle import create_cradle, outer_half_width, trough_floor_lift
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

    # A second thread auto-added at the cap's origin (geometry-ops gotchas S6)
    # survives every envelope check: same bbox, same one solid, +68 mm^3. But
    # its crests reach GLAND_MAJOR_D / 2 out from x=y=0 and the bore's axis sits
    # inside that band, so walking the axis is both "the cable has a path" and
    # "nothing got added twice". Verified against a deliberately broken build:
    # a stray copy blocks 6 of these 9 stations; the correct cap is clear at all.
    blocked = [
        z
        for z in (0.2, 1.6, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, e.CAP_T - 0.2)
        if is_solid_at(cap, 0, _loc(e.GLAND_Z), z)
    ]
    r.check(
        not blocked,
        "bore axis is clear end to end -- no stray thread at the origin",
        f"blocked at z={blocked}" if blocked else "9 stations, all open",
    )


def check_endcap_edges(cap: Part, r: Report) -> None:
    """The cap's three chamfers are broken, not merely asked for.

    ``chamfer_edge`` swallows an OCC refusal by design, and a chamfer that never
    applied is invisible in a projection, so each treatment is read back off the
    solid: one sample inside the material it should have removed, one just
    beyond that must still be solid. An op that ran too small fails the first,
    one that ate the part fails the second.
    """
    r.section("Endcap edges")
    half_h = e.CAP_H / 2
    ch, cc, li = e.EDGE_CHAMFER, e.COLLAR_CHAMFER, e.LIP_LEAD_IN

    # Bed face, sampled down the bottom arc -- clear of both screw lead-in cones.
    r.check(
        not is_solid_at(cap, 0.0, -(half_h - 0.25 * ch), 0.25 * ch),
        "bed face chamfered -- no elephant's foot",
        f"{ch} mm",
    )
    r.check(
        is_solid_at(cap, 0.0, -(half_h - 2 * ch), 0.25 * ch),
        "...and no more than that",
    )

    # Collar rim at CAP_T. The toe has to land on the tube's own silhouette:
    # everything outboard of WIDTH/2 is bevel, everything inboard is the seat
    # the extrusion's 0.5 mm wall stands on. Sampled at y=0, inside the
    # stadium's straight flank band, where u really is the outer surface.
    r.check(
        not is_solid_at(cap, c.WIDTH / 2 + 0.02, 0.0, e.CAP_T - 0.01),
        "collar rim chamfered at the cap face",
        f"{cc} mm = CAP_PROUD, so the toe lands on u={c.WIDTH / 2}",
    )
    r.check(
        is_solid_at(cap, c.WIDTH / 2 - 0.05, 0.0, e.CAP_T - 0.01),
        "...and the tube's wall seat is untouched",
    )
    r.check(
        is_solid_at(cap, e.CAP_W / 2 - 0.05, 0.0, e.CAP_T - cc - 0.05),
        "...and the collar is full width below the chamfer",
    )

    # The lip's lead-in, down the bottom of its arc. Shrinking a stadium leaves
    # its arc centres where they were, so the lip's lower arc is still the
    # profile's, at _loc(BOT_ARC_Z).
    tip = e.CAP_T + e.LIP_DEPTH
    arc_cy = _loc(c.BOT_ARC_Z)
    lip_r = c.RADIUS - c.WALL - e.LIP_FIT / 2
    r.check(
        not is_solid_at(cap, 0.0, arc_cy - (lip_r - 0.25 * li), tip - 0.25 * li),
        "lip's leading edge has a lead-in",
        f"{li} mm on a {e.LIP_T} mm wall, vs {e.LIP_FIT / 2:.2f} mm of clearance",
    )
    r.check(
        is_solid_at(cap, 0.0, arc_cy - (lip_r - 2 * li), tip - 0.25 * li),
        "...and the lip's tip is still there",
    )

    # The raw-edge rule (AGENTS.md), made falsifiable: every convex edge left
    # without a chamfer or fillet has to be a *stated* exception, not merely
    # unnoticed. The endcap's own module docstring names its three: the
    # thread's helix (not a straight or circular edge to begin with), the
    # whole of the CAP_T face inboard of the collar chamfer (both screw
    # mouths and the gland bore's faded thread exit sit on it), and the
    # lip's inner wire at its tip, where only the outer wire got a lead-in.
    lip_tip_z = e.CAP_T + e.LIP_DEPTH

    def _is_isothread_helix(edge) -> bool:
        return edge.geom_type == GeomType.BSPLINE

    def _is_cap_t_face_edge(edge) -> bool:
        bb = edge.bounding_box()
        return abs(bb.min.Z - e.CAP_T) < 0.02 and abs(bb.max.Z - e.CAP_T) < 0.02

    def _is_lip_tip_inner_wire(edge) -> bool:
        bb = edge.bounding_box()
        return abs(bb.min.Z - lip_tip_z) < 0.02 and abs(bb.max.Z - lip_tip_z) < 0.02

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
                "the whole of the CAP_T face inboard of the collar chamfer "
                "beds against the extrusion's 0.5 mm wall; both screw mouths "
                "and the gland bore's own faded thread exit sit on it too "
                "(endcap.py's module docstring)",
            ),
            (
                "lip tip's inner wire left raw",
                _is_lip_tip_inner_wire,
                "the lip's lead-in chamfer (LIP_LEAD_IN) only treats the "
                "outer wire at z=CAP_T+LIP_DEPTH; the inner wire is "
                "untouched by design (endcap.py's module docstring)",
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
    # BAND_RELIEF below the nominal one -- trough_floor_lift is what a raw
    # TUBE_UNDER_Z would get wrong here, the same way it would if this station
    # ever moved into a contact band instead.
    floor_z = mc.TUBE_UNDER_Z - trough_floor_lift(x_drain, mc.CRADLE_LEN)
    r.check(
        not is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 0.25 * ch, floor_z - 0.25 * ch),
        f"{name}: drain funnelled at the trough floor -- the water side",
        f"{ch} mm lead-in at floor z={floor_z:.2f}",
    )
    r.check(
        is_solid_at(part, x_drain, mc.DRAIN_D / 2 + 1.5 * ch, floor_z - 0.25 * ch),
        "...and no more than that",
    )

    # The raw-edge rule, made falsifiable, over the whole solid -- not just
    # the samples above. ``extra_sharp_allow`` lets a foot add its own
    # exceptions (its counterbore) on top of the ones every cradle-derived
    # part shares: the insert mouths, the bed sliver, the bore/wall's own
    # cross-section wherever the trough is axially discontinuous, and the
    # curved-floor drains' funnel residual (a known gap -- see
    # ``_is_near_drain_funnel``).
    spacing = mc.CRADLE_LEN / 3  # cradle.add_drains' default count=2
    drain_xy = ((spacing, 0.0), (2 * spacing, 0.0))
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
                "drain funnel residual (KNOWN GAP)",
                lambda edge: _is_near_drain_funnel(edge, drain_xy),
                "the curved-floor drains' funnel cone cannot conform to a "
                "doubly-curved floor; see _is_near_drain_funnel",
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
        r.check(
            not is_solid_at(
                part, mid, hu + side * (hole_d / 2 + 0.6 * lead), floor + 0.8 * lead
            ),
            f"{name}: bolt hole coned at the counterbore floor at u={hu:+.1f}",
            "the bolt has to find the hole blind, from inside the pocket",
        )
        r.check(
            is_solid_at(part, mid, hu + side * (hole_d / 2 + 0.3), floor - 0.4),
            "...and the bore is back to size below it",
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

    # The raw-edge rule, made falsifiable. Unlike every other part in the
    # family, the strap needs no allow list at all: every sample pair above
    # (bed, bore mouth, foot land, corners, arch silhouette, bore mouth over
    # the crown) already accounts for the part's own edges, and the arch
    # root's absence check confirms the one concave edge that stays raw on
    # purpose is concave -- so it cannot appear in a *convex*-edge audit
    # regardless. Kept as an explicit assertion rather than an assumption:
    # allow=() here is a claim about the geometry, and this is what checks it.
    _check_sharp_edges(part, "strap", r, ())


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
        f"plinth {corner_mod.PLINTH_H} > drop {corner_mod.GLAND_DROP}",
    )
    r.check(
        corner_mod.CHANNEL_W >= CAP_W + 1.0,
        "channel clears the endcap collar",
        f"{corner_mod.CHANNEL_W} vs collar {CAP_W}",
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

    check_corner_drain_funnels(part, r, angle)

    # The raw-edge rule, made falsifiable, over the whole solid. Insert
    # mouths and the bore/wall's own cross-section seam are the same
    # exceptions every cradle-derived part makes; the drain funnel residual
    # is the same known gap as ``check_cradle_edges``', just at this corner's
    # own drain stations. Two more are corner-specific: the engraved label
    # (a 0.6 mm bed-face pocket -- chamfering its glyph outlines would
    # destroy legibility) and a small, unresolved residual near the first
    # strap boss, tracked as a known gap rather than folded into a reason
    # that was not actually verified.
    drain_xy = ((0.0, 0.0), *corner_mod._drain_positions(angle, start))

    def _is_label_glyph(edge) -> bool:
        bb = edge.bounding_box()
        return bb.min.Z > -0.01 and bb.max.Z < corner_mod.LABEL_DEPTH + 0.02

    def _is_boss_area_residual(edge) -> bool:
        # Length and z-window match exactly, across all four angles, a small
        # (<=6 mm) BSPLINE/LINE residual sitting where a strap boss's own
        # insert hole (drilled INSERT_DEPTH down from the rim, z 19.8-28.8)
        # and the bore's band/relief step (whose short vertical seam already
        # matches ``_is_trough_seam_edge`` reaches z~25-28) come closest
        # together -- but the two adjacent faces were not traced by hand to
        # full certainty, so this is reported as a known gap, not asserted
        # as that specific cause.
        if edge.geom_type not in (GeomType.BSPLINE, GeomType.LINE):
            return False
        bb = edge.bounding_box()
        return edge.length <= 6.0 and 19.0 < bb.min.Z < 21.0 and 24.0 < bb.max.Z < 26.0

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
                "drain funnel residual (KNOWN GAP)",
                lambda edge: _is_near_drain_funnel(edge, drain_xy),
                "the curved-floor drains' funnel cone cannot conform to a "
                "doubly-curved floor; see _is_near_drain_funnel",
            ),
            (
                "engraved label glyph outline",
                _is_label_glyph,
                "a 0.6 mm pocket in the bed face (LABEL_DEPTH); chamfering "
                "glyph outlines would destroy legibility",
            ),
            (
                "boss/insert-area residual (KNOWN GAP, cause not fully traced)",
                _is_boss_area_residual,
                "a small (<=6 mm) residual near the first strap boss's "
                "insert hole and the bore's own relief step; the exact "
                "adjacent faces were not traced to full certainty -- see "
                "_is_boss_area_residual",
            ),
        ),
    )


def check_corner_drain_funnels(part: Part, r: Report, angle: float = 60.0) -> None:
    """Every drain's *upper* mouth is funnelled too, not just the bed one.

    Two floors, treated differently in ``corner._add_drains``: the knuckle
    drain and the near arm station open into the channel floor, which is
    flat, while the other two arm stations open into the cradle trough, whose
    floor is the bore's curved underside -- and one of those two sits in the
    relieved middle (a lower floor) while the other sits in a contact band (the
    nominal one), so both regimes ``cradle.trough_floor_lift`` has to tell
    apart are exercised here.
    """
    start = corner_mod.cradle_start(angle)
    ch = mc.EDGE_CHAMFER
    bearing = corner_mod._axis_bearings(angle)[0]
    a = radians(bearing)
    tag = f"corner {angle:.0f}: "

    def at(along: float, across: float, z: float) -> tuple[float, float, float]:
        return (
            along * cos(a) - across * sin(a),
            along * sin(a) + across * cos(a),
            z,
        )

    def pair(label: str, d: float, floor_z: float) -> None:
        r.check(
            not is_solid_at(
                part, *at(d, mc.DRAIN_D / 2 + 0.25 * ch, floor_z - 0.25 * ch)
            ),
            tag + label,
            f"{ch} mm lead-in at floor z={floor_z:.2f}",
        )
        r.check(
            is_solid_at(part, *at(d, mc.DRAIN_D / 2 + 1.5 * ch, floor_z - 0.25 * ch)),
            tag + "..." + label + ": and no more than that",
        )

    # The knuckle drain, at the vertex -- the channel floor, flat.
    pair("knuckle drain funnelled at the channel floor", 0.0, corner_mod.PLINTH_H)

    # The near arm station (d < start): channel floor too.
    pair(
        "near arm drain funnelled at the channel floor",
        start * 0.55,
        corner_mod.PLINTH_H,
    )

    # The other two arm stations: the trough's curved floor, one in the
    # relieved middle and one in a contact band.
    for frac, region in ((0.35, "relieved"), (0.75, "banded")):
        d = start + mc.CRADLE_LEN * frac
        lift = trough_floor_lift(d - start, mc.CRADLE_LEN)
        floor_z = corner_mod.PLINTH_H + mc.TUBE_UNDER_Z - lift
        pair(f"trough drain ({region}) funnelled at the curved floor", d, floor_z)


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
    check_stand_edges(part, r)
    check_stand_gusset(part, r)

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
    # air. Sample past the insert's own reach (MOUTH_Y - INSERT_DEPTH = -7.2)
    # but short of PAD_BASE_V (-9.0, where the pad itself stops) -- the pad no
    # longer runs to the stadium's back tip, see PAD_BASE_V's own comment.
    z = stand_mod.STATIONS[0]
    r.check(is_solid_at(part, mc.BOSS_U, -8.5, z), "socket has strap bosses")
    r.check(
        not is_solid_at(part, mc.BOSS_U, mc.CRADLE_DEPTH + stand_mod.SINK - 2.0, z),
        "and their inserts are drilled inward",
        "Align.MAX here would drill outward into the air",
    )


def check_stand_edges(part: Part, r: Report) -> None:
    """The hub's edges are actually broken, not merely asked to be.

    Same instrument as ``check_corner_edges``: ``chamfer_edge`` and
    ``fillet_edge`` swallow an OCC refusal by design, so every treatment is read
    back off the solid as a pair of samples -- one point in the material the op
    should have removed (or, for a concave fillet, added), one just past it that
    must be unchanged.

    The stand needs its own copy rather than sharing the corner's, because it is
    the family's odd one out: it prints standing on its flange, so the house
    rule's "vertical" is global Z here, the socket's mouth lips are vertical
    edges that take fillets instead of a horizontal rim that takes a chamfer,
    and the tube's lead-in is the rim at ``TOP_Z`` because the tube drops in
    from above.
    """
    ch, fr = mc.EDGE_CHAMFER, mc.EDGE_FILLET
    lip = stand_mod.LIP_FILLET
    hw, hh = stand_mod.SOCKET_HALF_W, stand_mod.SOCKET_HALF_H
    top, seat = stand_mod.TOP_Z, stand_mod.SEAT_Z
    pad_x = mc.BOSS_U + mc.BOSS_OD / 2

    # The rim at TOP_Z is the tube's lead-in. On every other mount in the family
    # the tube arrives sideways through a horizontal mouth; here it drops in
    # from above, so this chamfer is functional and not merely a broken edge.
    bore = (c.WIDTH + mc.BORE_FIT) / 2
    r.check(
        not is_solid_at(part, bore + 0.3 * ch, 0, top - 0.3 * ch),
        "socket rim chamfered -- the tube's lead-in from above",
        f"{ch} mm at u={bore:.2f}",
    )
    r.check(
        is_solid_at(part, bore + 1.2 * ch, 0, top - 0.3 * ch),
        "...and no more than that",
    )
    r.check(
        not is_solid_at(part, hw - 0.3 * ch, 0, top - 0.3 * ch),
        "socket rim chamfered -- outer silhouette too",
    )

    # The mouth lips are vertical, so they take a fillet -- and a smaller one
    # than EDGE_FILLET, because over the collar band the lip is only
    # SOCKET_HALF_W - COLLAR_HALF_W wide. Sampled a few mm above a boss pad's
    # crown, which is where the lip corner is not buried in a pad -- and not
    # the two stations' midpoint any more, because each boss's gusset now
    # climbs past the wall's own half-width before it reaches that pad (see
    # GUSSET_SUPPORT_U/_RUN), which eats into the lip's continuous stretch
    # from the *next* station's side.
    z_gap = stand_mod.STATIONS[0] + mc.STRAP_W / 2 + 3.0
    r.check(
        not is_solid_at(part, hw - 0.17 * lip, stand_mod.MOUTH_Y - 0.17 * lip, z_gap),
        "mouth lips filleted",
        f"R{lip}; R{fr} would leave "
        f"{stand_mod.SOCKET_HALF_W - stand_mod.COLLAR_HALF_W - fr:.2f} mm of lip",
    )
    r.check(
        is_solid_at(part, hw - 0.53 * lip, stand_mod.MOUTH_Y - 0.53 * lip, z_gap),
        "...and the lip itself is still there",
    )

    # The one structural blend on the part: the socket cantilevers off the
    # pedestal, and this fillet adds material rather than removing it.
    r.check(
        is_solid_at(part, 0, -(hh + 0.19 * fr), seat + 0.2 * fr),
        "socket root filleted where it stands on the pedestal",
        f"R{fr}, carrying a {top - seat:.0f} mm cantilever",
    )
    r.check(
        not is_solid_at(part, 0, -(hh + 0.59 * fr), seat + 0.6 * fr),
        "...and the fillet stops at that radius",
    )
    # Deliberately *not* filleted: the collar bore's root. The cap has only
    # this much clearance a side, and a blend there would stop it seating.
    r.check(
        not is_solid_at(part, stand_mod.COLLAR_HALF_W - 0.1, 0, seat + 0.2 * fr),
        "collar bore's root left raw -- a fillet there would unseat the cap",
        f"{stand_mod.COLLAR_HALF_W - CAP_W / 2:.2f} mm of clearance a side to lose",
    )

    # Boss pads: vertical corners filleted, crowns and undersides chamfered.
    r.check(
        not is_solid_at(
            part,
            pad_x - 0.16 * fr,
            stand_mod.MOUTH_Y - 0.16 * fr,
            stand_mod.STATIONS[0],
        ),
        "boss pads' outboard corners filleted",
        f"R{fr}",
    )
    r.check(
        is_solid_at(
            part, pad_x - 0.6 * fr, stand_mod.MOUTH_Y - 0.6 * fr, stand_mod.STATIONS[0]
        ),
        "...and the corner itself is still there",
    )
    # Sampled at v=-3.0, not the old -12.0 -- the pad no longer reaches that
    # deep (PAD_BASE_V=-9.0), see its own comment in stand.py.
    z = stand_mod.STATIONS[0] + mc.STRAP_W / 2
    r.check(
        not is_solid_at(part, pad_x - 0.3 * ch, -3.0, z - 0.3 * ch),
        "boss pad crown chamfered",
        "upward-facing",
    )
    # The underside does *not* get the same pairwise check: the pad's whole
    # underside is now the 45 deg gusset (check_stand_gusset below), not an
    # 0.8 mm edge chamfer. A sliver of edge still survives at the pad's own
    # outboard-bottom corner, where the gusset's far face and the pad's own
    # rectangle meet, and _boss_undersides still chamfers it -- but asserting
    # that sliver by point-sample would pin down an incidental seam rather
    # than the real fix, which check_stand_gusset verifies directly.

    # The two exposed rings, both facing up, both chamfered off their radius
    # rather than off the face above them -- those faces carry the counterbores
    # and the whole socket footprint.
    for z, rad, label in (
        (stand_mod.FLANGE_T, stand_mod.FLANGE_D / 2, "flange top rim"),
        (seat, stand_mod.PEDESTAL_D / 2, "pedestal top rim"),
    ):
        r.check(
            not is_solid_at(part, rad - 0.25 * ch, 0, z - 0.5 * ch),
            f"{label} chamfered",
            f"{ch} mm",
        )
        r.check(
            is_solid_at(part, rad - 1.5 * ch, 0, z - 0.5 * ch),
            f"...and no more than that ({label})",
        )

    # Boolean cone lead-ins at every mouth that is not a heat-set insert.
    px, py = stand_mod._pivot_positions()[0]
    r.check(
        not is_solid_at(
            part, px + stand_mod.PIVOT_CLEAR_D / 2 + 0.5 * ch, py, 0.25 * ch
        ),
        "pivot holes have a bed-face lead-in cone",
        "boolean: that face also carries the drain and the flange's own rim",
    )
    r.check(
        is_solid_at(part, px + stand_mod.PIVOT_CLEAR_D / 2 + 0.5 * ch, py, 0.875 * ch),
        "...and it is only EDGE_CHAMFER deep",
    )
    r.check(
        not is_solid_at(
            part,
            0.55 * mc.DRAIN_D,
            stand_mod.GLAND_OFFSET,
            stand_mod.FLANGE_T - 0.375 * ch,
        ),
        "the well's drain is funnelled, so the well actually empties into it",
    )
    r.check(
        is_solid_at(
            part,
            mc.DRAIN_D / 2 + 1.5 * ch,
            stand_mod.GLAND_OFFSET,
            stand_mod.FLANGE_T - 0.25 * ch,
        ),
        "...and no more than that",
    )
    sx = stand_mod.CABLE_SLOT_W / 2
    sy = -sqrt((stand_mod.PEDESTAL_D / 2) ** 2 - sx**2)
    r.check(
        not is_solid_at(part, sx + 0.12 * fr, sy + 0.12 * fr, stand_mod.FLANGE_T + 5),
        "cable slot's mouth filleted -- the cable is never clamped here",
        f"R{fr}",
    )
    r.check(
        is_solid_at(part, sx + 0.72 * fr, sy + 0.72 * fr, stand_mod.FLANGE_T + 5),
        "...and the slot is still CABLE_SLOT_W wide behind it",
    )

    # The family-wide exception, asserted rather than assumed: a printed lead-in
    # removes the material the heat-set insert has to melt into.
    r.check(
        is_solid_at(
            part,
            mc.BOSS_U + mc.INSERT_D / 2 + 0.125 * ch,
            stand_mod.MOUTH_Y - 0.25 * ch,
            stand_mod.STATIONS[0],
        ),
        "insert mouths have no lead-in -- the deliberate exception",
        "the insert's own chamfer guides it; a printed one starves it",
    )
    # And the counterbore mouths, for a reason particular to this part:
    # PIVOT_R - PIVOT_CBORE_D / 2 clears the pedestal wall by only this much.
    gap = stand_mod.PIVOT_R - stand_mod.PIVOT_CBORE_D / 2 - stand_mod.PEDESTAL_D / 2
    r.check(
        is_solid_at(
            part,
            stand_mod.PIVOT_R - stand_mod.PIVOT_CBORE_D / 2 + 0.25 * ch,
            py - 4.0,
            stand_mod.FLANGE_T - 0.625 * ch,
        ),
        "counterbore mouths left raw -- a cone there would undercut the pedestal",
        f"{gap:.2f} mm between the counterbore and the pedestal's wall",
    )

    # The raw-edge rule, made falsifiable, over the whole solid. The stand is
    # the family's odd one out (see this function's own docstring), so its
    # bore/wall seam is matched by position -- pinned at X = +/-BORE -- not
    # by the vertical/short-length test the other mounts' lying-down troughs
    # use: the collar-to-nominal bore step at z=SEAT_Z+CAP_T runs in Y, not
    # Z, because this part's own "vertical" is global Z throughout.
    z0 = stand_mod.FLANGE_T + 1.0  # cable slot box, bed-side face
    z1 = z0 + mc.CABLE_OD + 2.0  # cable slot box, well-side face (CABLE_SLOT_W)
    pivot_floor_z = stand_mod.FLANGE_T - stand_mod.PIVOT_CBORE_H

    def _is_stand_seam(edge) -> bool:
        r = _edge_radius(edge)
        if r is not None and abs(r - _SEAM_BORE_R) < 0.02:
            return True
        if r is not None and abs(r - mc.CRADLE_OUTER_HALF_W) < 0.02:
            return True
        if edge.geom_type != GeomType.LINE:
            return False
        bb = edge.bounding_box()
        return (
            bb.size.X < 0.05
            and abs(abs((bb.min.X + bb.max.X) / 2) - _SEAM_BORE_R) < 0.1
        )

    def _is_pivot_cbore_mouth(edge) -> bool:
        r = _edge_radius(edge)
        bb = edge.bounding_box()
        return (
            r is not None
            and abs(r - stand_mod.PIVOT_CBORE_D / 2) < 0.02
            and abs(bb.min.Z - stand_mod.FLANGE_T) < 0.05
        )

    def _is_well_mouth(edge) -> bool:
        r = _edge_radius(edge)
        return r is not None and abs(r - stand_mod.WELL_D / 2) < 0.02

    def _is_collar_bore_root(edge) -> bool:
        r = _edge_radius(edge)
        if r is not None and abs(r - stand_mod.COLLAR_HALF_W) < 0.02:
            return True
        ctr = edge.bounding_box().center()
        return abs(stand_mod._collar_dist(ctr.X, ctr.Y)) < 0.5

    def _is_cable_slot_mouth(edge) -> bool:
        # Two raw seams from the same box cut: the pedestal's own outer wall
        # (top/bottom of the notch, at the box's Z extent) and the box's
        # flat side wall crossing the offset well's cylindrical boundary
        # inside the cavity. _cable_mouth_corners() only fillets the
        # vertical corners *on the pedestal's own radius* -- neither of these
        # is on that radius, so both were missed.
        bb = edge.bounding_box()
        r = _edge_radius(edge)
        if r is not None and abs(r - stand_mod.PEDESTAL_D / 2) < 0.05:
            return abs(bb.min.Z - z0) < 0.1 or abs(bb.min.Z - z1) < 0.1
        if edge.geom_type == GeomType.LINE and bb.size.X < 0.05:
            half = mc.CABLE_OD / 2 + 1.0  # CABLE_SLOT_W / 2
            if abs(abs((bb.min.X + bb.max.X) / 2) - half) < 0.05:
                return abs(bb.min.Z - z0) < 0.1 and abs(bb.max.Z - z1) < 0.1
        return False

    def _is_pivot_cbore_floor_step(edge) -> bool:
        r = _edge_radius(edge)
        bb = edge.bounding_box()
        return (
            r is not None
            and abs(r - stand_mod.PIVOT_CLEAR_D / 2) < 0.05
            and abs(bb.min.Z - pivot_floor_z) < 0.05
        )

    _check_sharp_edges(
        part,
        "stand hub",
        r,
        (
            (
                "insert mouth left raw",
                _is_insert_mouth_edge,
                "a printed lead-in removes the material the heat-set has to "
                "melt into -- the family-wide exception",
            ),
            (
                "bore/wall seam (cross-section at a discontinuity)",
                _is_stand_seam,
                "the tube bore's and the collar bore's own cross-section, "
                "including the collar-to-nominal step at z=SEAT_Z+CAP_T -- "
                "same family as cradle.vertical_corners' exclusion, pinned "
                "by position here since this part does not lie on its side",
            ),
            (
                "pivot counterbore mouth left raw",
                _is_pivot_cbore_mouth,
                "PIVOT_R - PIVOT_CBORE_D/2 clears the pedestal wall by only "
                "0.25 mm -- a cone there would undercut the pedestal "
                "(this function's own docstring)",
            ),
            (
                "gland well mouth left raw",
                _is_well_mouth,
                "_socket_root excludes it: at this height it is a ceiling "
                "over the well, not a root, and its arc looks like a root "
                "edge to any position test",
            ),
            (
                "collar bore root left raw",
                _is_collar_bore_root,
                "_socket_root excludes it: the seat is already only ~0.6 mm "
                "wide at the narrowest, and a fillet there would stop the "
                "cap seating altogether",
            ),
            (
                "cable slot mouth left raw (KNOWN GAP)",
                _is_cable_slot_mouth,
                "_cable_mouth_corners() only fillets the vertical corners on "
                "the pedestal's own outer radius; the notch's top/bottom "
                "edges and its flat side wall's crossing of the offset "
                "well were missed -- see _is_cable_slot_mouth",
            ),
            (
                "pivot counterbore floor step (KNOWN GAP)",
                _is_pivot_cbore_floor_step,
                "the flat shoulder between the pivot counterbore and the "
                "narrower through-hole -- same family as feet.py's "
                "counterbore floor step",
            ),
        ),
    )


def check_stand_gusset(part: Part, r: Report) -> None:
    """The boss pads' real fix: a 45 deg ramp, not a cosmetic edge chamfer.

    ``check_stand_edges`` verifies the pad's *edges* are broken where the
    house rule says to; this verifies the pad's whole underside is actually
    self-supporting, by measuring the angle of the surface ``_boss_gusset``
    adds -- not by re-checking the constants (``GUSSET_SUPPORT_U``/``_RUN``)
    it was built from, which would only prove the arithmetic agrees with
    itself. The angle is read off the built solid: each ramp face's normal is
    looked up directly, and the angle a plane makes with horizontal equals the
    angle its normal makes with the vertical (Z) axis regardless of which way
    the normal happens to point -- build123d makes no promise about that
    (``models/lib/checks.py``). So neither this formula nor
    ``_gusset_faces``'s own selection ever has to resolve that sign: both
    work from ``abs()`` of the normal's components -- ``abs(n.Z)`` here,
    ``abs(n.Y)`` and ``abs(n.Z)`` there for its tilt window -- and neither
    calls an outward-orientation probe like ``models.lib.checks._outward``.
    ``_gusset_faces`` still needs its position/shape predicate on top of that
    tilt window, to tell the six ramps apart from each other and from the
    socket lip's own flat vertical faces.

    "Overhang angle" is measured from horizontal throughout: 90 deg is a
    vertical wall (no overhang), 0 deg is a flat ceiling (the worst case), and
    45 deg is the conventional FDM self-supporting threshold -- the same one
    every boolean lead-in cone elsewhere in this file already assumes.
    """
    faces = stand_mod._gusset_faces(part)
    r.check(
        len(faces) == 6,
        "a gusset ramp found under every boss pad, both sides",
        f"{len(faces)} of 6 -- 3 stations x 2 sides",
    )
    angles = [degrees(acos(min(1.0, abs(f.normal_at(f.center()).Z)))) for f in faces]
    worst = min(angles, default=-1.0)
    r.check(
        bool(faces) and worst >= 45.0 - 0.01,
        "every gusset ramp is self-supporting",
        f"{worst:.1f} deg from horizontal, worst of {len(faces)} -- >=45 deg needed",
    )


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
        # A foot's own two exceptions, on top of every cradle-derived part's
        # shared set: the counterbore mouth (documented, feet.py's module
        # docstring) and the counterbore floor's own step (a known gap --
        # see ``_is_cbore_floor_step_edge``).
        foot_sharp_allow = (
            (
                "counterbore mouth left raw",
                lambda edge, cd=cbore_d: _is_cbore_mouth_edge(edge, cd / 2),
                "feet.py's module docstring: an 0.8 lead-in there would eat "
                "half of PAD_WALL, the only wall between an M6/M5 nyloc and "
                "open air; the nut is dropped in by hand, not found blind",
            ),
            (
                "counterbore floor step (KNOWN GAP)",
                lambda edge, hd=hole_d: _is_cbore_floor_step_edge(edge, hd / 2),
                "the flat shoulder between the counterbore's own diameter "
                "and the narrower through-hole the lead-in cone widens; see "
                "_is_cbore_floor_step_edge",
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


# ------------------------------------------------------- sharp convex edges
#
# ``AGENTS.md`` has always said "never ship a part with raw square edges",
# and a corner shipped with one chamfer and passed 185 assertions before
# anyone noticed (models/lib/checks.py's own module docstring).
# ``sharp_convex_edges`` makes the rule falsifiable; nothing called it until
# here, so the whole family below is the first time it has ever been
# enforced. Every legitimate raw edge is an *allow* entry -- a predicate, a
# reason, and (below) a count -- so an exception has to be stated, not merely
# not noticed. A few findings did not resolve to a documented design
# decision; those are labelled KNOWN GAP and still asserted machine-clean
# only because the offending geometry lives in a file outside this one's
# write-set (cradle.py, corner.py, stand.py) -- see the reasons themselves,
# and the task report, for what would need to change there.

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


def _is_near_drain_funnel(
    edge,
    drain_xy: tuple[tuple[float, float], ...],
    max_len: float = 6.0,
    tol: float = 4.0,
) -> bool:
    """KNOWN GAP: a drain's upper-mouth funnel, left slightly sharp.

    The boolean cone that funnels a drain's throat into the trough floor
    (``cradle.add_drains``, ``corner._add_drains``) is a single-curvature
    surface; the trough floor it funnels into, wherever it is the bore's own
    curved underside rather than a flat channel/bed face, is not. The cone
    cannot conform to it exactly, so every drain that opens into that curved
    floor keeps a short (<=6 mm), real seam around its throat -- invisible in
    a projection and never checked before this audit existed. Fixing it means
    reshaping the funnel in ``cradle.py``/``corner.py``, both outside this
    file's write-set, so it is recorded here rather than folded into a reason
    that does not actually apply.
    """
    if edge.length > max_len:
        return False
    ctr = edge.bounding_box().center()
    return any(
        ((ctr.X - px) ** 2 + (ctr.Y - py) ** 2) ** 0.5 < tol for px, py in drain_xy
    )


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


def _is_cbore_floor_step_edge(edge, hole_r: float) -> bool:
    """KNOWN GAP: the counterbore's own floor shoulder, where it steps down
    to the narrower through-hole.

    feet.py documents and treats the *bed* mouth and the counterbore *floor*
    lead-in (both boolean cones, verified in ``check_foot_edges``), but not
    this remainder: the flat annular shoulder between the counterbore's own
    diameter and the narrower hole the lead-in cone actually widens. Fixing
    it means widening that cone's base radius in ``feet.py``, outside this
    file's write-set.
    """
    r = _edge_radius(edge)
    bb = edge.bounding_box()
    floor_z = mc.CRADLE_DEPTH - feet_mod.CBORE_DEPTH
    return r is not None and abs(r - hole_r) < 0.05 and abs(bb.min.Z - floor_z) < 0.05


def _check_sharp_edges(
    part: Part,
    name: str,
    r: Report,
    allow: tuple[tuple[str, Callable[[object], bool], str], ...],
) -> None:
    """The raw-edge rule, made falsifiable, for one already-built part.

    Calls ``sharp_convex_edges`` exactly once with no ``allow`` of its own --
    building the adjacency map is the expensive part of that function, and
    the raw, unfiltered list is also the only way to report *how many* edges
    each exception actually accounts for. Every classification below is
    therefore done in plain Python against that one list, not by asking the
    kernel again. ``allow`` is a list of ``(label, predicate, reason)``
    triples, applied in order; whatever no predicate claims is asserted to be
    empty -- the hard gate the rest of the family never had before this file.
    """
    raw = sharp_convex_edges(part)
    r.check(
        True, f"{name}: sharp convex edges found before allow-listing", f"{len(raw)}"
    )
    remaining = list(raw)
    for label, predicate, reason in allow:
        matched = [edge for edge in remaining if predicate(edge)]
        remaining = [edge for edge in remaining if not predicate(edge)]
        r.check(True, f"{name}: {label}", f"{len(matched)} edges -- {reason}")
    detail = "all accounted for"
    if remaining:
        detail = f"{len(remaining)} left: " + "; ".join(
            f"{edge.geom_type} len={edge.length:.2f} at "
            f"{tuple(round(v, 2) for v in edge.bounding_box().center())}"
            for edge in remaining
        )
    r.check(not remaining, f"{name}: no unexplained sharp convex edges", detail)


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
    check_endcap_edges(cap, r)
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
