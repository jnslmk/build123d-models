"""Geometry assertions for the Sonicare charger holder.

    uv run check sonicare_charger_holder
    uv run python -m models.sonicare_charger_holder.checks

Almost nothing this model promises is visible in a projection, which is why
these are point samples rather than a render. "Closed in front" is a claim about
every angle at every height, and a render only ever shows one side at a time.
"The floor is closed" is a claim about a face the cup's own wall hides. "The
cord sits below the tape plane" is a claim about a channel that faces the tile.
Each of those is a fact about a solid, so each is sampled *in* the solid.

Two probes recur and are chosen, not arbitrary:

* **The back is at +Y**, and the cable route is the only thing that breaks the
  shell. So every sweep here asks not "is anything open?" but "is everything
  that is open inside the route's footprint?" -- ``_in_route`` is that
  footprint, and it is the single place the answer is defined.
* **Mid-wall radius**, ``cavity_r + wall/2``, is where the shell is probed. Not
  the bore and not the outside: a probe on either surface sits exactly on a
  face, where "inside the solid" is a coin toss.

The last section is a different kind of check. This model is parametric on the
website, and its numbers are researched rather than measured (see ``config``),
so the sliders are the feature that matters most -- they are how somebody with
calipers corrects it. That section drags them to their stops and past them and
asserts that what comes back is still a closed, printable part.
"""

from __future__ import annotations

import sys
from math import cos, degrees, hypot, radians, sin

from build123d import GeomType, Part

from ..lib import fits
from ..lib.checks import (
    Report,
    is_periodic_seam,
    is_solid_at,
    sharp_convex_edges,
)
from . import ROUTE_MOUTHS, build
from .config import (
    CABLE_BOOT_DIA,
    CABLE_CLEAR,
    CABLE_DIA,
    DEFAULT,
    FLOOR,
    PUCK_FIT,
    Holder,
)

PROBE = 0.1


def _in_route(h: Holder, x: float, y: float) -> bool:
    """Is (x, y) inside the cable route's footprint?

    The route is the *only* opening in the shell, so this predicate is what
    every "is it closed?" assertion below is written against. Generous by a
    tenth on each bound, because a probe landing exactly on a cut face is
    undefined, not open.
    """
    return abs(x) <= h.channel_w / 2 + 0.1 and y >= h.back_y - h.channel_depth - 0.1


def check_print_pose(part: Part, h: Holder, r: Report) -> None:
    r.section("print pose")
    bb = part.bounding_box()
    r.check(abs(bb.min.Z) < 1e-6, "part is re-seated on z=0", f"min z = {bb.min.Z:.4f}")
    r.check(
        abs(bb.size.Z - h.body_h) < 1e-6,
        "height is floor + puck height, i.e. the rim is level with the charger",
        f"{bb.size.Z:.2f} mm vs {h.body_h:.2f} mm -- the 'puck height only' front wall",
    )
    r.check(
        is_solid_at(part, 0, 0, FLOOR / 2)
        and not is_solid_at(part, 0, 0, h.body_h - PROBE),
        "closed floor sits on the bed, cup mouth faces up (not bridged)",
        f"solid at z={FLOOR / 2:.2f} (floor), hollow at z={h.body_h - PROBE:.2f} (mouth)",
    )
    r.check(
        abs(bb.max.Y - h.back_y) < 1e-6,
        "nothing protrudes past the tape plane, so the pad meets flat tile",
        f"max y = {bb.max.Y:.3f} vs tape plane {h.back_y:.3f}",
    )


def check_bore(part: Part, h: Holder, r: Report) -> None:
    r.section("the bore the charger drops into")
    r.check(
        PUCK_FIT == fits.SLIDING,
        "puck clearance is the named SLIDING class, not a typed literal",
        f"{PUCK_FIT} mm diametral -- drops in and lifts out by hand without "
        "rattling on a wall; FREE (0.40) would be audible, PRESS would not seat",
    )
    r.check(
        abs(h.cavity_dia - (h.puck_dia + PUCK_FIT)) < 1e-9,
        "bore is cut at nominal + the fit, never at nominal",
        f"{h.cavity_dia:.2f} = {h.puck_dia:.2f} + {PUCK_FIT:.2f}; an FDM bore "
        "already prints a couple of tenths under, so nominal is a press fit",
    )
    mid = FLOOR + h.puck_height / 2
    r.check(
        not is_solid_at(part, h.cavity_r - PROBE, 0, mid)
        and is_solid_at(part, h.cavity_r + PROBE, 0, mid),
        "the bore wall stands exactly at cavity_r",
        f"hollow at r={h.cavity_r - PROBE:.2f}, solid at r={h.cavity_r + PROBE:.2f}",
    )
    r.check(
        is_solid_at(part, 0, 0, FLOOR - PROBE)
        and not is_solid_at(part, 0, 0, FLOOR + PROBE),
        "the bore's floor is at FLOOR, so the charger sits on solid plastic",
        f"solid below z={FLOOR:.2f}, hollow above it",
    )


def check_closed_in_front(part: Part, h: Holder, r: Report) -> None:
    """The headline requirement, and the one a render cannot confirm."""
    r.section("closed in front")
    probe_r = h.cavity_r + h.wall / 2
    heights = [FLOOR + t * (h.puck_height) for t in (0.05, 0.25, 0.5, 0.75, 0.95)]

    leaks: list[tuple[int, float]] = []
    for a in range(0, 360, 2):
        x, y = probe_r * cos(radians(a)), probe_r * sin(radians(a))
        for z in heights:
            if not is_solid_at(part, x, y, z) and not _in_route(h, x, y):
                leaks.append((a, round(z, 1)))
    r.check(
        not leaks,
        "the shell is unbroken at every angle and height except the cable route",
        f"{len(leaks)} leak(s) at {leaks[:6]}" if leaks else
        f"{len(range(0, 360, 2)) * len(heights)} probes at r={probe_r:.2f} mm, "
        "every opening inside the route footprint",
    )

    # Stronger and narrower: the half of the shell that faces the room has no
    # opening at all, route or otherwise. This is the claim the sketch makes.
    front_leaks = [
        a
        for a in range(0, 360, 2)
        if probe_r * sin(radians(a)) <= 0
        and any(
            not is_solid_at(part, probe_r * cos(radians(a)), probe_r * sin(radians(a)), z)
            for z in heights
        )
    ]
    r.check(
        not front_leaks,
        "the front half is solid outright -- no cutout, no scallop, no drain",
        f"open at {front_leaks}" if front_leaks else
        "every probe on the room-facing half is inside the solid",
    )

    opening = sorted(
        {
            round(degrees(radians(a)))
            for a in range(0, 360, 2)
            if any(
                not is_solid_at(
                    part, probe_r * cos(radians(a)), probe_r * sin(radians(a)), z
                )
                for z in heights
            )
        }
    )
    r.check(
        all(60 <= a <= 120 for a in opening),
        "the only opening in the wall faces the tile (+Y), not the room",
        f"open at bearings {opening} deg (90 deg is straight at the wall)",
    )


def check_closed_floor(part: Part, h: Holder, r: Report) -> None:
    r.section("closed floor")
    holes: list[tuple[int, int]] = []
    for a in range(0, 360, 5):
        for rr in (3, 8, 13, 18, 22, 23):
            x, y = rr * cos(radians(a)), rr * sin(radians(a))
            if not is_solid_at(part, x, y, FLOOR / 2) and not _in_route(h, x, y):
                holes.append((a, rr))
    r.check(
        not holes,
        "the floor is closed everywhere outside the cable route",
        f"{len(holes)} hole(s) at {holes[:6]}" if holes else
        "no drain holes and no open ring -- the cable route is the one opening",
    )
    r.check(
        not is_solid_at(part, 0, h.back_y - h.channel_depth / 2, FLOOR / 2),
        "the route does break the floor at the very back, which is the cord's exit",
        "and doubles as the only path standing water has off the floor -- "
        "stated because a closed floor in a wet room is a deliberate trade, "
        "not an oversight",
    )


def check_cable_route(part: Part, h: Holder, r: Report) -> None:
    r.section("cable route")
    r.check(
        abs(h.channel_w - (CABLE_BOOT_DIA + CABLE_CLEAR)) < 1e-9,
        "the channel is sized on the strain-relief boot, not the bare cord",
        f"{h.channel_w:.2f} = boot {CABLE_BOOT_DIA:.1f} + {CABLE_CLEAR:.1f} routing "
        "gap; the boot is the widest thing that has to pass, and it passes along "
        "the whole height because it descends with the puck",
    )

    # The headline requirement, and the one the first version of this model got
    # wrong. A channel closed at the top can only be threaded, and the free end
    # of this cord has a mains plug moulded onto it -- so the cable could not be
    # fitted at all. "Open" is not a property of one probe: it has to hold at
    # every height and across the boot's full width, or the puck jams on the way
    # down at whatever height it stops holding.
    lanes = (-h.channel_w / 2 + 0.3, 0.0, h.channel_w / 2 - 0.3)
    steps = [i * 0.5 for i in range(int(h.body_h * 2) + 1)]
    obstructed = [
        (round(x, 1), round(z, 1))
        for x in lanes
        for z in steps
        if is_solid_at(part, x, h.back_y - h.channel_depth / 2, min(z, h.body_h - 0.05))
    ]
    r.check(
        not obstructed,
        "the channel is open from the bed to the rim, at the boot's full width",
        f"obstructed at {obstructed[:6]}"
        if obstructed
        else f"{len(lanes) * len(steps)} probes clear -- the cord is laid in from "
        "above and the puck follows it down, rather than being threaded through",
    )
    r.check(
        not is_solid_at(part, 0, h.back_y - h.channel_depth / 2, h.body_h - 0.05)
        and not is_solid_at(part, 0, h.back_y - h.channel_depth / 2, 0.05),
        "the channel breaks both the rim and the bed, so it is a channel not a hole",
        "open at both ends: a closed end at either one turns laying the cord in "
        "back into threading it",
    )

    # Continuity, walked the way the cord is actually fitted.
    z_wall = FLOOR + 2.0
    stations = [
        ("laid in at the rim", (0.0, h.back_y - h.channel_depth / 2, h.body_h - 0.3)),
        ("beside the puck", (0.0, h.cavity_r - 0.5, z_wall)),
        ("through the wall", (0.0, h.cavity_r + h.wall / 2, z_wall)),
        ("through the bar", (0.0, h.back_y - 1.0, z_wall)),
        ("turning down", (0.0, h.back_y - h.channel_depth / 2, FLOOR)),
        ("in the channel", (0.0, h.back_y - h.channel_depth / 2, FLOOR / 2)),
        ("off the bottom edge", (0.0, h.back_y - h.channel_depth / 2, 0.05)),
    ]
    blocked = [name for name, pt in stations if is_solid_at(part, *pt)]
    r.check(
        not blocked,
        "an unbroken path runs from the rim, past the puck, and out below",
        f"blocked at {blocked}" if blocked else " -> ".join(n for n, _ in stations),
    )

    r.check(
        h.channel_depth >= CABLE_DIA,
        "the channel is deeper than the cord is thick, so the cord clears the tile",
        f"{h.channel_depth:.2f} mm deep vs a {CABLE_DIA:.1f} mm cord -- a cord "
        "left standing proud would hold the pad off the tile along its whole "
        "length and turn a shear joint into a peel joint",
    )
    r.check(
        not is_solid_at(part, 0, h.back_y - PROBE, FLOOR / 2)
        and is_solid_at(part, 0, h.back_y - h.channel_depth - PROBE, FLOOR / 2),
        "the channel is cut to its full depth and no further",
        f"air at the tape plane, solid {h.channel_depth:.2f} mm in",
    )

    # Opening the channel to the rim costs rim, and the cost has to stay small
    # or the cup stops being a cup. Measured, not asserted by eye.
    probe_r = h.cavity_r + h.wall / 2
    open_deg = [
        a
        for a in range(360)
        if not is_solid_at(
            part, probe_r * cos(radians(a)), probe_r * sin(radians(a)), h.body_h - 0.3
        )
    ]
    r.check(
        len(open_deg) <= 40 and all(60 <= a <= 120 for a in open_deg),
        "the rim is broken only by the channel, and only at the back",
        f"open over {len(open_deg)} deg of 360, bearings "
        f"{min(open_deg)}-{max(open_deg)} (90 deg is straight at the tile)"
        if open_deg
        else "rim unbroken -- which would mean the channel never reached it",
    )


def check_tape_pad(part: Part, h: Holder, r: Report) -> None:
    r.section("the tape pad (the only thing holding it up)")
    # Part.faces() is correct at runtime; same suppression as door_latch.py.
    part_faces = part.faces()  # ty: ignore[invalid-argument-type]
    faces = [
        f
        for f in part_faces
        if abs(f.bounding_box().min.Y - h.back_y) < 1e-6
        and abs(f.bounding_box().max.Y - h.back_y) < 1e-6
    ]
    area = sum(f.area for f in faces)
    r.check(
        bool(faces),
        "there is a flat face in the tape plane at all",
        f"{len(faces)} coplanar face(s) at y={h.back_y:.2f}",
    )
    r.check(
        area > 500,
        "the pad offers enough area for foam tape to hold the load",
        f"{area:.0f} mm^2 of flat contact across {len(faces)} pad(s); the holder "
        "plus a docked brush is about 0.2 kg at ~26 mm of lever arm, which is "
        "well inside VHB-class tape at this area",
    )
    r.check(
        len(faces) == 2,
        "the channel splits the pad in two, so tape goes on both sides of it",
        f"{len(faces)} pad face(s) -- opening the channel to the rim severs the "
        "bar; taping only one side would load the joint in peel about the other",
    )
    r.check(
        h.plate_w < h.outer_dia,
        "the bar stays inside the cup's silhouette, so the front view is round",
        f"bar {h.plate_w:.2f} mm across vs cup {h.outer_dia:.2f} mm",
    )
    r.check(
        h.plate_corner_r < h.plate_t / 2,
        "the bar's vertical corners are filleted in the sketch, not by an edge op",
        f"r={h.plate_corner_r:.2f} on a {h.plate_t:.2f} mm bar -- taken in "
        "RectangleRounded, which cannot fail the way an OCC fillet can",
    )


def check_edges(part: Part, treatments: dict[str, bool], h: Holder, r: Report) -> None:
    r.section("edge treatment")
    for name, took in treatments.items():
        r.check(took, f"{name} chamfer applied", "by return value, not by the log")
    r.check(
        set(treatments) >= {name for name, _ in ROUTE_MOUTHS},
        "every mouth of the cable route was treated",
        f"treated {sorted(treatments)}",
    )

    r.check(
        not is_solid_at(part, h.cavity_r + 0.05, 0, h.body_h - h.mouth_chamfer + 0.1)
        and is_solid_at(part, h.cavity_r + 0.5, 0, h.body_h - h.mouth_chamfer + 0.1),
        "the mouth's lead-in starts on the bore wall, not as a counterbore ledge",
        "the frustum matches the bore's own cross-section, so the bevel begins "
        "at cavity_r; a tool of the wrong section would ring the mouth with a step",
    )
    r.check(
        h.mouth_chamfer < h.wall / 2 and h.rim_chamfer < h.wall / 2,
        "neither rim treatment can knife-edge the wall, at any wall thickness",
        f"lead-in {h.mouth_chamfer:.2f}, outer {h.rim_chamfer:.2f}, wall {h.wall} "
        "-- both are properties bounded by the wall, not fixed constants",
    )
    r.check(
        h.route_chamfer < CABLE_DIA / 2,
        "the route's mouth chamfers cannot meet and narrow the route",
        f"{h.route_chamfer:.2f} mm on a {h.channel_w:.1f} mm channel",
    )

    def _bore_seam(edge) -> bool:
        # The cavity is a plain extruded bore: nothing is ever cut into its
        # side, so this straight vertical LINE at r = cavity_r is the untrimmed
        # cylinder's own periodic parametrisation closing on itself, with no
        # boolean anywhere near it to coincide with. Confirmed, not assumed --
        # is_periodic_seam does the confirming.
        if edge.geom_type != GeomType.LINE:
            return False
        bb = edge.bounding_box()
        if bb.size.X > 1e-6 or bb.size.Y > 1e-6:
            return False
        if abs(hypot(bb.min.X, bb.min.Y) - h.cavity_r) > 1e-3:
            return False
        return is_periodic_seam(part, edge)

    survey = sharp_convex_edges(
        part,
        allow=((_bore_seam, "the bore's own untrimmed cylindrical seam"),),
    )
    r.check(
        not survey.sharp,
        "no unchamfered sharp convex edges",
        f"{len(survey.sharp)} at "
        f"{[(round(e.center().X, 1), round(e.center().Y, 1), round(e.center().Z, 1)) for e in survey.sharp]}"
        if survey.sharp
        else "clean",
    )
    r.check(
        not survey.unclassifiable,
        "no unclassifiable convex edges (unmeasured is not the same as clean)",
        f"{len(survey.unclassifiable)} found"
        if survey.unclassifiable
        else "clean",
    )


def check_parameters(r: Report) -> None:
    """Drag every slider to its stops, and past them, and stay printable.

    This matters more here than in a model cut from calipered numbers: the
    charger's dimensions are researched, so the sliders are the mechanism by
    which somebody with a caliper fixes them. A clamp that quietly stopped
    clamping would show up here and nowhere else.
    """
    r.section("parameters")
    cases = {
        "defaults": {},
        "smallest puck": {"puck_dia": 20.0, "puck_height": 6.0},
        "largest puck": {"puck_dia": 120.0, "puck_height": 60.0},
        "thinnest wall": {"wall": 1.2},
        "thickest wall": {"wall": 6.0},
        "boot larger than the cup is tall": {"puck_height": 6.0, "cable_boot_dia": 12.0},
        "below every stop": {
            "puck_dia": -50.0,
            "puck_height": 0.0,
            "wall": 0.0,
            "cable_boot_dia": 0.0,
        },
        "above every stop": {
            "puck_dia": 1e4,
            "puck_height": 1e4,
            "wall": 1e4,
            "cable_boot_dia": 1e4,
        },
        "junk key ignored": {"nonsense": 3.0},
    }
    for label, params in cases.items():
        try:
            h = Holder.of(**params)
            part, treatments = build(h)
        except Exception as exc:  # noqa: BLE001 -- the point is that none escape
            r.check(False, f"{label}: builds", f"raised {exc!r}")
            continue
        bb = part.bounding_box()
        probe_r = h.cavity_r + h.wall / 2
        front_open = any(
            not is_solid_at(
                part,
                probe_r * cos(radians(a)),
                probe_r * sin(radians(a)),
                FLOOR + h.puck_height / 2,
            )
            for a in range(180, 360, 10)
        )
        r.check(
            abs(bb.min.Z) < 1e-6
            and part.volume > 0
            and not front_open
            and all(treatments.values()),
            f"{label}: builds, seats on z=0, stays closed in front, fully chamfered",
            f"puck {h.puck_dia:.1f}x{h.puck_height:.1f}, wall {h.wall:.1f}, "
            f"boot {h.cable_boot_dia:.1f} -> {bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} mm",
        )


def run() -> Report:
    r = Report()
    h = DEFAULT
    part, treatments = build(h)
    check_print_pose(part, h, r)
    check_bore(part, h, r)
    check_closed_in_front(part, h, r)
    check_closed_floor(part, h, r)
    check_cable_route(part, h, r)
    check_tape_pad(part, h, r)
    check_edges(part, treatments, h, r)
    check_parameters(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
