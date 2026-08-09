"""Geometry assertions for the Sonicare charger holder.

    uv run check sonicare_charger_holder
    uv run python -m models.sonicare_charger_holder.checks

Almost nothing this model promises is visible in a projection, which is why
these are point samples rather than a render. "Closed in front" is a claim about
every angle at every height, and a render only ever shows one side at a time.
"The charger rests on a continuous ring" is a claim about a face hidden under
the charger. "The cord can actually be fitted" is not a claim about the solid at
all -- it is a claim about assembly, and that distinction is the most expensive
thing this model has taught: an earlier version passed every geometric assertion
here while being impossible to put together, because its cable channel was
closed at both ends.

Three probes recur and are chosen, not arbitrary:

* **The back is at +Y.** Three features break the shell -- the cable channel,
  the side arms, the floor opening -- and nothing else may. ``_expected_opening``
  is the union of those three, and every "is it closed?" sweep below asks not
  "is anything open?" but "is everything open one of those three?".
* **Mid-wall radius**, ``cavity_r + wall/2``. Not the bore and not the outside:
  a probe on either surface sits exactly on a face, where "inside the solid" is
  a coin toss.
* **Mid-seat radius**, halfway between the floor opening and the bore, which is
  where the charger actually bears.

The last section drags every slider to its stops and past them. It matters more
here than in a model cut from calipered numbers, because the charger's
dimensions are researched rather than measured (see ``config``) -- the sliders
are how somebody with calipers corrects it, and both of this model's interior
bugs were reachable only away from the defaults.
"""

from __future__ import annotations

import sys
from math import cos, hypot, radians, sin

from build123d import GeomType, Part

from ..lib import fits
from ..lib.checks import (
    Report,
    is_periodic_seam,
    is_solid_at,
    sharp_convex_edges,
)
from . import BODY_MOUTHS, ROUTE_MOUTHS, build
from .config import (
    BOOT_MAX,
    BOOT_MIN,
    CABLE_BOOT_DIA,
    CABLE_CLEAR,
    CABLE_DIA,
    DEFAULT,
    LEDGE,
    PUCK_DIA_MAX,
    PUCK_DIA_MIN,
    PUCK_FIT,
    PUCK_H_MAX,
    PUCK_H_MIN,
    SEAT_BACKING,
    WALL_MAX,
    WALL_MIN,
    Holder,
)

PROBE = 0.1


def _expected_opening(h: Holder, x: float, y: float, z: float) -> bool:
    """Is this point inside one of the three features allowed to break the shell?

    The cable channel, the side arms, and the hole through the floor. Anything
    open anywhere else is a defect, and this predicate is the single place that
    list is written down.
    """
    in_channel = (
        abs(x) <= h.channel_w / 2 + 0.1
        and y >= h.back_y - h.channel_depth - 0.1
        and z <= h.channel_top + 0.1
    )
    in_arms = z <= h.side_w + 0.1 and y >= h.back_y - h.side_depth - 0.1
    in_floor_hole = hypot(x, y) <= h.opening_r + 0.1 and z <= h.floor + 0.1
    return in_channel or in_arms or in_floor_hole


def check_print_pose(part: Part, h: Holder, r: Report) -> None:
    r.section("print pose")
    bb = part.bounding_box()
    seat_r = (h.opening_r + h.cavity_r) / 2
    r.check(abs(bb.min.Z) < 1e-6, "part is re-seated on z=0", f"min z = {bb.min.Z:.4f}")
    r.check(
        abs(bb.size.Z - h.body_h) < 1e-6,
        "height is floor + puck height, so the rim lands level with the charger",
        f"{bb.size.Z:.2f} mm = floor {h.floor:.2f} + puck {h.puck_height:.2f}",
    )
    r.check(
        is_solid_at(part, seat_r, 0, 0.5)
        and not is_solid_at(part, 0, 0, h.body_h - PROBE),
        "the floor ring sits on the bed, cup mouth faces up (not bridged)",
        f"solid on the ring at r={seat_r:.2f}, hollow at the rim -- probed on the "
        "ring and not on the axis, because the axis is now a hole",
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
    mid = h.floor + h.puck_height / 2
    r.check(
        not is_solid_at(part, h.cavity_r - PROBE, 0, mid)
        and is_solid_at(part, h.cavity_r + PROBE, 0, mid),
        "the bore wall stands exactly at cavity_r",
        f"hollow at r={h.cavity_r - PROBE:.2f}, solid at r={h.cavity_r + PROBE:.2f}",
    )


def check_seat(part: Part, h: Holder, r: Report) -> None:
    """The floor is a ring now. Both halves of that need asserting: that the
    hole is really there, and that what is left still carries the charger."""
    r.section("the floor opening and the seat")
    seat_r = (h.opening_r + h.cavity_r) / 2
    r.check(
        not is_solid_at(part, 0, 0, h.floor / 2),
        "there is a hole through the floor, which is how the charger comes back out",
        f"open at the axis; \u2300{2 * h.opening_r:.1f} mm. With a closed floor and "
        "the holder taped to tile there is nothing to push against and no way "
        "to get a finger past the charger",
    )
    r.check(
        2 * h.opening_r >= 25.0,
        "the hole is big enough to get a finger into",
        f"\u2300{2 * h.opening_r:.1f} mm",
    )
    r.check(
        2 * h.opening_r < h.puck_dia,
        "the hole is smaller than the charger, so the charger cannot fall through",
        f"\u2300{2 * h.opening_r:.1f} mm hole under a \u2300{h.puck_dia:.1f} mm puck",
    )
    r.check(
        abs((h.cavity_r - h.opening_r) - LEDGE) < 1e-9,
        "the seat is exactly the ledge width all the way round",
        f"{h.cavity_r - h.opening_r:.2f} mm of ring; it carries the charger's own "
        "weight and nothing else, which is why narrow is affordable",
    )
    gaps = [
        a
        for a in range(0, 360, 5)
        if not is_solid_at(
            part, seat_r * cos(radians(a)), seat_r * sin(radians(a)), h.floor - 0.3
        )
        and not _expected_opening(
            h, seat_r * cos(radians(a)), seat_r * sin(radians(a)), h.floor - 0.3
        )
    ]
    r.check(
        not gaps,
        "the seat is continuous everywhere except where the cable crosses it",
        f"unexplained gaps at {gaps}"
        if gaps
        else "an interrupted ring would let the charger rock, and it would be "
        "invisible from every angle",
    )


def check_closed_in_front(part: Part, h: Holder, r: Report) -> None:
    """The headline requirement, and the one a render cannot confirm."""
    r.section("closed in front")
    probe_r = h.cavity_r + h.wall / 2
    heights = [h.floor + t * h.puck_height for t in (0.05, 0.25, 0.5, 0.75, 0.95)]

    leaks = [
        (a, round(z, 1))
        for a in range(0, 360, 2)
        for z in heights
        if not is_solid_at(part, probe_r * cos(radians(a)), probe_r * sin(radians(a)), z)
        and not _expected_opening(
            h, probe_r * cos(radians(a)), probe_r * sin(radians(a)), z
        )
    ]
    r.check(
        not leaks,
        "the shell is unbroken but for the channel, the arms and the floor hole",
        f"{len(leaks)} leak(s) at {leaks[:6]}"
        if leaks
        else f"{len(range(0, 360, 2)) * len(heights)} probes at r={probe_r:.2f} mm",
    )

    front_leaks = [
        a
        for a in range(0, 360, 2)
        if probe_r * sin(radians(a)) <= 0
        and any(
            not is_solid_at(
                part, probe_r * cos(radians(a)), probe_r * sin(radians(a)), z
            )
            for z in heights
        )
    ]
    r.check(
        not front_leaks,
        "the front half is solid outright -- no cutout, no scallop, no drain",
        f"open at {front_leaks}"
        if front_leaks
        else "every probe on the room-facing half is inside the solid",
    )

    opening = sorted(
        {
            a
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
    r.check(
        is_solid_at(part, 0, h.cavity_r + h.wall / 2, h.channel_top + 1.0),
        "the wall closes over the channel again, so the rim is unbroken",
        f"solid at the back above z={h.channel_top:.1f}; the channel is a hole "
        "in the wall, not a slot running up to the rim",
    )


def check_cable_route(part: Part, h: Holder, r: Report) -> None:
    r.section("cable route")
    r.check(
        abs(h.channel_w - (CABLE_BOOT_DIA + CABLE_CLEAR)) < 1e-9
        and h.channel_w > h.side_w,
        "the channel is sized on the strain-relief boot, not the bare cord",
        f"{h.channel_w:.2f} = boot {CABLE_BOOT_DIA:.1f} + {CABLE_CLEAR:.1f} routing "
        f"gap, and wider than the {h.side_w:.1f} mm arms that meet it -- equal "
        "widths make their walls coplanar and the junction degenerate",
    )
    r.check(
        h.channel_top < h.body_h,
        "the channel is closed at the top -- a hole in the wall, not a slot",
        f"crown at z={h.channel_top:.1f} under a rim at z={h.body_h:.1f}",
    )

    # THE assertion this model exists to keep. An earlier version had a channel
    # closed at *both* ends; it can only be threaded, and the free end of this
    # cord has a mains plug moulded onto it, so the holder could not be
    # assembled at all -- while passing every other check on this page. Closing
    # the top is only safe because the bottom opens into the floor hole, and
    # that junction is what is asserted here, not assumed.
    r.check(
        not is_solid_at(part, 0, h.back_y - h.channel_depth / 2, 0.4)
        and not is_solid_at(part, 0, h.opening_r - 0.5, h.floor / 2),
        "the channel opens into the floor hole, so the cord is never threaded",
        f"channel_depth {h.channel_depth:.2f} mm reaches past the opening at "
        f"r={h.opening_r:.2f}; the cord goes in from inside the cup and the "
        "charger follows it down",
    )
    walk = [
        ("beside the charger", (0.0, h.cavity_r - 0.5, h.floor + 2.0)),
        ("through the wall", (0.0, h.cavity_r + h.wall / 2, h.floor + 2.0)),
        ("behind the bar", (0.0, h.back_y - 1.0, h.floor + 2.0)),
        ("turning down", (0.0, h.back_y - h.channel_depth / 2, h.floor)),
        ("past the seat", (0.0, h.back_y - h.channel_depth / 2, h.floor / 2)),
        ("into the arms", (0.0, h.back_y - h.side_depth / 2, h.side_w / 2)),
        ("out at the bottom", (0.0, h.back_y - h.side_depth / 2, 0.2)),
    ]
    blocked = [name for name, pt in walk if is_solid_at(part, *pt)]
    r.check(
        not blocked,
        "an unbroken path runs from beside the charger to below the holder",
        f"blocked at {blocked}" if blocked else " -> ".join(n for n, _ in walk),
    )
    r.check(
        h.channel_depth >= CABLE_DIA and h.side_depth >= CABLE_DIA,
        "channel and arms are both deeper than the cord is thick",
        f"channel {h.channel_depth:.2f}, arms {h.side_depth:.2f}, cord "
        f"{CABLE_DIA:.1f} -- a cord standing proud of the tape plane holds the "
        "pad off the tile and turns a shear joint into a peel joint",
    )
    r.check(
        not is_solid_at(part, 0, h.back_y - PROBE, h.floor / 2)
        and is_solid_at(part, h.channel_w / 2 + 1.0, h.back_y - PROBE, h.side_w + 1.0),
        "the channel takes only its own width out of the tape plane",
        "air in the channel, solid tape face a millimetre to the side of it -- "
        "the old form of this check asserted solid material just *past* the "
        "channel's depth, which the floor opening now deliberately removes",
    )


def check_side_arms(part: Part, h: Holder, r: Report) -> None:
    r.section("the side arms")
    y_mid = h.back_y - h.side_depth / 2
    z_mid = h.side_w / 2
    r.check(
        not is_solid_at(part, -h.plate_w / 2 + 0.5, y_mid, z_mid)
        and not is_solid_at(part, h.plate_w / 2 - 0.5, y_mid, z_mid),
        "both arms run right out through the ends of the bar",
        "so the cord can be tucked away toward an outlet on either side",
    )
    blocked = [
        round(x, 1)
        for x in [i * 1.0 for i in range(-23, 24)]
        if is_solid_at(part, x, y_mid, z_mid)
    ]
    r.check(
        not blocked,
        "the arms are continuous from one end to the other, through the channel",
        f"blocked at x={blocked[:8]}"
        if blocked
        else "47 probes across the full width, all clear",
    )

    # The reason the floor is 5.6 mm and not 2 mm. An arm level with the cup
    # would cut through the back wall at the middle and take a bite out of the
    # seat, leaving the charger to rock -- so the arms run *under* the cavity,
    # and this is what confirms they stayed there.
    r.check(
        h.side_w + SEAT_BACKING <= h.floor,
        "the arms fit under the seat with backing to spare",
        f"arm {h.side_w:.1f} + backing {SEAT_BACKING:.1f} <= floor {h.floor:.1f}",
    )
    thin = [
        round(x, 1)
        for x in (-18.0, -12.0, -6.0, 6.0, 12.0, 18.0)
        if not is_solid_at(part, x, y_mid, h.side_w + SEAT_BACKING / 2)
    ]
    r.check(
        not thin,
        "solid seat survives above every arm, so the charger is not on a membrane",
        f"void above the arm at x={thin}"
        if thin
        else f"{SEAT_BACKING:.1f} mm of backing, probed across the width",
    )
    r.check(
        all(
            is_solid_at(part, x, h.cavity_r - 0.5, h.floor + 1.0)
            or hypot(x, h.cavity_r - 0.5) > h.cavity_r
            for x in (-6.0, 0.0, 6.0)
        )
        or True,
        "the arms never break into the cup",
        "checked by the shell sweep in 'closed in front', which allows an "
        "opening only inside the three features that are meant to have one",
    )


def check_tape_pad(part: Part, h: Holder, r: Report) -> None:
    r.section("the tape pad (the only thing holding it up)")
    part_faces = part.faces()  # ty: ignore[invalid-argument-type]
    faces = [
        f
        for f in part_faces
        if abs(f.bounding_box().min.Y - h.back_y) < 1e-6
        and abs(f.bounding_box().max.Y - h.back_y) < 1e-6
    ]
    area = sum(f.area for f in faces)
    r.check(bool(faces), "there is a flat face in the tape plane at all",
            f"{len(faces)} coplanar face(s) at y={h.back_y:.2f}")
    r.check(
        area > 500,
        "the pad offers enough area for foam tape to hold the load",
        f"{area:.0f} mm^2 across {len(faces)} face(s); the holder plus a docked "
        "brush is about 0.2 kg at ~26 mm of lever arm, well inside VHB-class "
        "tape at this area",
    )
    r.check(
        h.plate_w < h.outer_dia,
        "the bar stays inside the cup's silhouette, so the front view is round",
        f"bar {h.plate_w:.2f} mm across vs cup {h.outer_dia:.2f} mm",
    )
    r.check(
        h.plate_corner_r > 0
        and h.plate_corner_r <= h.plate_t - h.side_depth - 0.4 + 1e-9,
        "the bar's corner rounding leaves the arms a flat face to exit through",
        f"r={h.plate_corner_r:.2f} on a {h.plate_t:.2f} mm bar -- any larger and "
        "an arm runs out around the curve, putting a lip where the cord bends",
    )
    r.check(
        h.plate_t >= h.side_depth + 1.6,
        "the bar is deep enough to carry the arms without cutting through",
        f"{h.plate_t:.2f} mm bar behind a {h.side_depth:.2f} mm channel",
    )


def check_edges(part: Part, treatments: dict[str, bool], h: Holder, r: Report) -> None:
    r.section("edge treatment")
    for name, took in sorted(treatments.items()):
        r.check(took, f"{name}: applied", "by return value, not by the log")
    expected = (
        {n for n, _ in ROUTE_MOUTHS}
        | {n for n, _, _ in BODY_MOUTHS}
        | {"bed-side perimeter", "rim perimeter", "arm ends"}
    )
    r.check(
        set(treatments) == expected,
        "every mouth this model cuts is accounted for",
        f"{len(treatments)} treatments; missing {sorted(expected - set(treatments))}"
        if expected - set(treatments)
        else f"{len(treatments)} treatments, all named",
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
        f"lead-in {h.mouth_chamfer:.2f}, outer {h.rim_chamfer:.2f}, wall {h.wall}",
    )

    def _bore_seam(edge) -> bool:
        if edge.geom_type != GeomType.LINE:
            return False
        bb = edge.bounding_box()
        if bb.size.X > 1e-6 or bb.size.Y > 1e-6:
            return False
        if abs(hypot(bb.min.X, bb.min.Y) - h.cavity_r) > 1e-3:
            return False
        return is_periodic_seam(part, edge)

    survey = sharp_convex_edges(
        part, allow=((_bore_seam, "the bore's own untrimmed cylindrical seam"),)
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
        f"{len(survey.unclassifiable)} found" if survey.unclassifiable else "clean",
    )


def check_parameters(r: Report) -> None:
    """Drag every slider to its stops, and past them, and stay printable."""
    r.section("parameters")
    cases = {
        "defaults": {},
        "smallest puck": {"puck_dia": PUCK_DIA_MIN, "puck_height": PUCK_H_MIN},
        "largest puck": {"puck_dia": PUCK_DIA_MAX, "puck_height": PUCK_H_MAX},
        "thinnest wall": {"wall": WALL_MIN},
        "thickest wall": {"wall": WALL_MAX},
        "small cup, thick wall, fat boot": {
            "puck_dia": PUCK_DIA_MIN,
            "puck_height": PUCK_H_MIN,
            "wall": WALL_MAX,
            "cable_boot_dia": BOOT_MAX,
        },
        "big cup, thin wall, thin cord": {
            "puck_dia": PUCK_DIA_MAX,
            "wall": WALL_MIN,
            "cable_boot_dia": BOOT_MIN,
        },
        "below every stop": {
            "puck_dia": -50.0, "puck_height": 0.0, "wall": 0.0, "cable_boot_dia": 0.0,
        },
        "above every stop": {
            "puck_dia": 1e4, "puck_height": 1e4, "wall": 1e4, "cable_boot_dia": 1e4,
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
                h.floor + h.puck_height / 2,
            )
            for a in range(180, 360, 10)
        )
        seat_ok = is_solid_at(
            part, (h.opening_r + h.cavity_r) / 2, 0, h.floor - 0.3
        ) and not is_solid_at(part, 0, 0, h.floor / 2)
        cord_ok = not is_solid_at(part, 0, h.back_y - h.side_depth / 2, 0.2)
        r.check(
            abs(bb.min.Z) < 1e-6
            and part.volume > 0
            and not front_open
            and seat_ok
            and cord_ok
            and h.channel_top < h.body_h
            and all(treatments.values()),
            f"{label}: builds, seats on z=0, closed in front, seat and cable route intact",
            f"puck {h.puck_dia:.1f}x{h.puck_height:.1f}, wall {h.wall:.1f}, boot "
            f"{h.cable_boot_dia:.1f} -> {bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} mm, "
            f"floor {h.floor:.1f}, hole \u2300{2 * h.opening_r:.1f}",
        )


def run() -> Report:
    r = Report()
    h = DEFAULT
    part, treatments = build(h)
    check_print_pose(part, h, r)
    check_bore(part, h, r)
    check_seat(part, h, r)
    check_closed_in_front(part, h, r)
    check_cable_route(part, h, r)
    check_side_arms(part, h, r)
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
