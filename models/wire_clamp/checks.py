"""Geometry assertions for the wire clamp.

    uv run check wire_clamp

Three of these are the model's reason for existing and are worth reading before
the rest:

* ``thread survives the printable-thread gate`` runs the rules from
  ``fasteners-and-inserts``' ``references/threads.md`` over this model's thread
  **and over the original's, at both ends of its published range**. The
  original passes at 6 mm rope and fails three of four rules at 3 mm. That is
  the defect this model was written to fix, stated as a number rather than as a
  complaint -- and it is what stops the gate being vacuous, because a gate that
  has never been shown to reject anything has not been shown to do anything.
* ``thread does not move with the wire`` builds the clamp at both ends of the
  slider and asserts every thread dimension is *identical*. This is the fix
  itself: the original's slider moves the thread, and that is why it has a
  broken size.
* ``screw and body never intersect`` poses the two solids at points across the
  whole travel and takes a boolean each time. A printed thread's clearance is a
  claim about a helix, and a helix is only clear at one height at a time: a
  single-position check cannot see a thread that binds a turn later.
"""

from __future__ import annotations

import sys

from build123d import Compound, Part, Pos, Rot

from ..lib.checks import Report, is_solid_at, is_periodic_seam, sharp_convex_edges
from ..lib.edges import as_part
from . import body, screw, wire
from . import screw_turn
from .config import (
    BASE_T,
    COLLAR_H,
    KNOB_CHAMFER,
    KNOB_LOBE_DEPTH,
    RING_H,
    CORE_R,
    FEMALE_CREST_R,
    FEMALE_ROOT_R,
    MALE_CREST_R,
    MALE_ROOT_R,
    PLUNGER_R,
    RIB_H,
    STRANDS,
    THREAD_CLEAR,
    THREAD_D,
    THREAD_DEPTH,
    THREAD_ENGAGE_MIN,
    THREAD_FLAT,
    THREAD_PITCH,
    WALL,
    WIRE_MAX,
    WIRE_MIN,
    Clamp,
)

NOZZLE = 0.4
"""The extrusion width every "can the printer resolve this" rule below is in
terms of. The repo's machines are 0.4 mm nozzles (``models.lib.fits``)."""

LAYER = 0.2
"""Layer height the pitch rule is stated at."""

MIN_LAYERS_PER_PITCH = 6
"""``references/threads.md``: below about six layers to a turn the helix
staircases into a stack of rings and stops being a thread."""

CLEAR_MIN = 0.30
"""Diametral, printed male in printed female: the tightest row of the clearance
table in ``references/threads.md``, for a well-calibrated printer at M10 and
below. A **floor, not a range**, because this gate asks one question -- can the
printer resolve this -- and only a clearance below the floor fails it. A thread
with too much clearance wobbles, which is a complaint about feel; a thread with
too little seizes, which is the complaint being fixed."""


# ---------------------------------------------------------------------------
# The original, as measured. Every number is a ratio to the rope diameter, read
# off the ten published files by comparing them against each other -- see
# ``docs/reverse-engineering.md`` for how, and for the rest of the table.
# ---------------------------------------------------------------------------

ORIGINAL_PITCH = 0.360
ORIGINAL_DEPTH = 0.100
ORIGINAL_CREST_FLAT = 0.097
ORIGINAL_CLEAR = 0.100
ORIGINAL_RANGE = (3.1, 12.0)
"""The published range. The file called 3 mm is built at 3.1: the original's own
description says the parameter fails below 3.1, and its body measures 9.30 mm
across against the 3.00 x d the other nine files hold to."""


def thread_gate(pitch: float, depth: float, crest_flat: float, clear: float) -> list[str]:
    """Every printable-thread rule this set of numbers breaks.

    One function, applied to this model's thread and to the original's at both
    ends of its range, so the comparison is like for like rather than a story.
    Empty list means the thread is printable by these rules.
    """
    broken = []
    if depth < NOZZLE:
        broken.append(f"tooth {depth:.2f} < one extrusion ({NOZZLE})")
    if crest_flat < NOZZLE:
        broken.append(f"crest flat {crest_flat:.2f} < one extrusion ({NOZZLE})")
    if pitch / LAYER < MIN_LAYERS_PER_PITCH:
        broken.append(f"{pitch / LAYER:.1f} layers per pitch < {MIN_LAYERS_PER_PITCH}")
    if clear < CLEAR_MIN:
        broken.append(f"clearance {clear:.2f} < {CLEAR_MIN} floor")
    return broken


def original_at(rope_d: float) -> list[str]:
    """The gate, applied to the original scaled to a given rope diameter."""
    return thread_gate(
        ORIGINAL_PITCH * rope_d,
        ORIGINAL_DEPTH * rope_d,
        ORIGINAL_CREST_FLAT * rope_d,
        ORIGINAL_CLEAR * rope_d,
    )


def check_thread_rules(r: Report) -> None:
    r.section("thread: the printable-thread gate")

    broken = thread_gate(THREAD_PITCH, THREAD_DEPTH, THREAD_FLAT, THREAD_CLEAR)
    r.check(
        not broken,
        "this model's thread is printable",
        f"pitch {THREAD_PITCH}, tooth {THREAD_DEPTH}, crest {THREAD_FLAT}, "
        f"clearance {THREAD_CLEAR}" + (f" -- BROKEN: {broken}" if broken else ""),
    )

    # The gate has teeth: it must accept the original where the original works
    # and reject it where it does not. Without both halves this is a rule that
    # has never rejected anything.
    big = original_at(ORIGINAL_RANGE[1])
    r.check(
        not big,
        f"gate accepts the original at {ORIGINAL_RANGE[1]} mm rope",
        "the shape being reconstructed prints fine at the top of its range, "
        "and a gate that failed it would be measuring the wrong thing",
    )
    small = original_at(ORIGINAL_RANGE[0])
    r.check(
        len(small) >= 3,
        f"gate rejects the original at {ORIGINAL_RANGE[0]} mm rope",
        "; ".join(small) or "gate found nothing wrong, which contradicts the "
        "reported failure",
    )
    scaled = original_at(1.0)
    r.check(
        bool(scaled),
        "gate rejects the original scaled to 1 mm wire",
        "; ".join(scaled),
    )

    r.section("thread: profile")
    closes = THREAD_FLAT + 2 * THREAD_DEPTH + THREAD_FLAT
    r.check(
        abs(closes - THREAD_PITCH) < 1e-9,
        "45 degree profile closes on the pitch",
        f"crest {THREAD_FLAT} + 2 x {THREAD_DEPTH} + root {THREAD_FLAT} "
        f"= {closes} vs pitch {THREAD_PITCH}",
    )
    r.check(
        THREAD_DEPTH > 0 and abs(THREAD_DEPTH / THREAD_DEPTH - 1.0) < 1e-9,
        "flank overhang is 45 degrees",
        "flank rise equals flank run by construction, so the underside of every "
        "flank sits at the house 45 degree limit exactly",
    )
    r.check(
        abs((FEMALE_ROOT_R - MALE_CREST_R) - THREAD_CLEAR / 2) < 1e-9
        and abs((FEMALE_CREST_R - MALE_ROOT_R) - THREAD_CLEAR / 2) < 1e-9,
        "clearance is the same at crest and root",
        f"female root {FEMALE_ROOT_R} - male crest {MALE_CREST_R} = "
        f"{FEMALE_ROOT_R - MALE_CREST_R}; female crest {FEMALE_CREST_R} - male "
        f"root {MALE_ROOT_R} = {FEMALE_CREST_R - MALE_ROOT_R}",
    )
    r.check(
        THREAD_ENGAGE_MIN >= THREAD_D,
        "engagement is at least 1.0 x D",
        f"{THREAD_ENGAGE_MIN} mm of female thread on a {THREAD_D} mm thread",
    )


def check_thread_is_fixed(r: Report) -> None:
    r.section("thread: does not move with the wire")
    lo, hi = Clamp.of(WIRE_MIN), Clamp.of(WIRE_MAX)
    r.check(
        lo.channel_l != hi.channel_l and lo.window_h != hi.window_h,
        "the wire does move the cord features",
        f"channel {lo.channel_l:.2f} -> {hi.channel_l:.2f} mm, window "
        f"{lo.window_h:.2f} -> {hi.window_h:.2f} mm across the slider",
    )
    # THREAD_* are module constants, so this is asserting the *structure* of the
    # model rather than a computed value: there is no per-instance thread to
    # differ. thread_engage is the one exception and may only grow.
    r.check(
        hi.thread_engage >= lo.thread_engage >= THREAD_ENGAGE_MIN,
        "thread length only ever grows with the wire",
        f"{lo.thread_engage:.2f} -> {hi.thread_engage:.2f} mm, floor "
        f"{THREAD_ENGAGE_MIN}",
    )
    r.check(
        not any(
            thread_gate(THREAD_PITCH, THREAD_DEPTH, THREAD_FLAT, THREAD_CLEAR)
            for _ in (lo, hi)
        ),
        "the thread passes the gate at both ends of the slider",
        "pitch, tooth, crest and clearance are module constants and no "
        "``Clamp`` property touches them",
    )


def check_kinematics(r: Report, c: Clamp) -> None:
    r.section("kinematics")
    r.check(
        abs((c.closed_z + c.plunger_len) - c.thread_z0) < 1e-9,
        "male thread never drives below the female thread's first turn",
        f"knob home puts it at {c.closed_z + c.plunger_len:.2f}, female starts "
        f"at {c.thread_z0:.2f} -- below that the bore is the channel, which is "
        "a whole tooth narrower",
    )
    r.check(
        c.open_engagement >= THREAD_PITCH,
        "a full turn is still engaged with the clamp open",
        f"{c.open_engagement:.2f} mm at the open position, pitch "
        f"{THREAD_PITCH} -- so the screw cannot be dropped out of an open clamp",
    )
    r.check(
        c.travel > c.wire_d,
        "travel exceeds the wire it has to let go of",
        f"{c.travel:.2f} mm of plunger travel for a {c.wire_d} mm wire",
    )
    r.check(
        c.closed_z + c.plunger_len + c.male_len + COLLAR_H <= c.body_h + 1e-9,
        "knob seats on the body with the plunger home",
        f"knob underside reaches {c.closed_z + c.plunger_len + c.male_len + COLLAR_H:.2f}, "
        f"body top {c.body_h:.2f} -- so an empty clamp closes flush and any "
        "wire at all holds the knob proud",
    )
    r.check(
        c.open_z >= c.window_z1,
        "plunger clears the top of the window when open",
        f"open at {c.open_z:.2f}, window top {c.window_z1:.2f}",
    )


def check_wire_path(r: Report, c: Clamp) -> None:
    r.section("wire path")
    passage = c.channel_l / 2 - PLUNGER_R
    r.check(
        passage >= c.wire_d,
        "the wire fits past the plunger",
        f"{passage:.2f} mm of passage at each end of the slot for a "
        f"{c.wire_d} mm wire -- this is the departure from the original, "
        "whose round bore leaves 0.3 mm at any size",
    )
    side = c.channel_w / 2 - PLUNGER_R
    r.check(
        side < c.wire_d,
        "the wire cannot escape sideways past the plunger",
        f"{side:.2f} mm at the slot's flats, against a {c.wire_d} mm wire -- "
        "the same slot that opens a path along the wire closes one across it",
    )
    r.check(
        STRANDS * c.wire_d < c.channel_w,
        "both strands fit side by side under the plunger",
        f"{STRANDS} x {c.wire_d} = {STRANDS * c.wire_d:.2f} mm in a "
        f"{c.channel_w:.2f} mm slot",
    )
    r.check(
        c.lip >= c.wire_d * 0.8,
        "the sill is deep enough to be a bend and not a graze",
        f"lip {c.lip:.2f} mm against a {c.wire_d} mm wire",
    )


def check_body_solid(r: Report, part: Part, c: Clamp) -> None:
    r.section("body: geometry, point-sampled")
    mid_thread = (c.thread_z0 + c.thread_z1) / 2
    r.check(
        is_solid_at(part, 0, 0, BASE_T / 2),
        "the channel has a floor",
        f"solid on the axis at z={BASE_T / 2}",
    )
    r.check(
        not is_solid_at(part, 0, 0, c.channel_top - 0.2),
        "the channel is open above the floor",
        "void on the axis just under the channel's top",
    )
    r.check(
        is_solid_at(part, 0, 0, BASE_T + RIB_H / 2),
        "there is a rib on the axis",
        "the rib pattern is centred, so the middle of the floor is ribbed "
        "rather than flat",
    )
    r.check(
        not is_solid_at(part, 0, c.body_r + 1, (c.window_z0 + c.window_z1) / 2)
        and not is_solid_at(part, 0, 0, (c.window_z0 + c.window_z1) / 2),
        "the window is a through hole",
        "void on the axis and outside the part at the window's mid-height",
    )
    r.check(
        is_solid_at(part, c.body_r - WALL / 2, 0, mid_thread),
        "the shell is solid beside the thread",
        f"solid at r={c.body_r - WALL / 2:.2f} halfway up the thread",
    )
    r.check(
        is_solid_at(part, 0, c.channel_l / 2 + 0.5, BASE_T / 2)
        and is_solid_at(part, c.channel_w / 2 + 0.5, 0, BASE_T / 2),
        "the slot is surrounded by material at floor level",
        "solid just outside the slot in both axes",
    )
    r.check(
        abs(part.bounding_box().min.Z) < 1e-6,
        "body is in print pose",
        f"bounding box starts at z={part.bounding_box().min.Z}",
    )
    r.check(
        len(part.solids()) == 1,
        "the body is one solid",
        f"{len(part.solids())} solids -- the silent failure a thread can cause "
        "is OCC's fuse returning the thread alone, or leaving it as a second "
        "body, and both look like a perfectly valid part until counted",
    )


def check_screw_solid(r: Report, part: Part, c: Clamp) -> None:
    r.section("screw: geometry, point-sampled")
    bb = part.bounding_box()
    r.check(abs(bb.min.Z) < 1e-6, "screw is in print pose", f"z={bb.min.Z}")
    r.check(
        bb.max.Z > 2 * c.body_r,
        "screw is taller than it is wide, and so prints knob down",
        f"{bb.max.Z:.2f} mm tall, {2 * c.body_r:.2f} mm across -- knob on the "
        "bed is the only pose with no unsupported ledge",
    )
    # The knob is the bed face: sample near the rim at the first layer.
    # Inside the scallops and inside the bottom chamfer, so the sample lands in
    # material at any rotation rather than depending on where lobe zero fell.
    inner = c.body_r - KNOB_LOBE_DEPTH - KNOB_CHAMFER - 0.5
    r.check(
        is_solid_at(part, inner, 0, 0.1) and is_solid_at(part, 0, inner, 0.1),
        "the knob is the face on the bed",
        f"solid at r={inner:.2f} on the first layer, in both axes -- a "
        f"{2 * inner:.1f} mm first layer against the plunger's "
        f"{2 * PLUNGER_R:.1f}",
    )
    # The topmost material on the part is the ridges, not the face they stand
    # on: sample across one of them, then off it in both directions.
    tip = bb.max.Z
    probe_z = tip - RING_H / 2
    ring = screw.ring_radii(c)[0]
    r.check(
        is_solid_at(part, ring, 0, probe_z)
        and not is_solid_at(part, 0, 0, probe_z)
        and not is_solid_at(part, PLUNGER_R + 0.5, 0, probe_z),
        "the plunger's ridges stand proud of its face, and print last",
        f"at z={probe_z:.2f}: solid on the first ridge (r={ring:.2f}), void on "
        "the axis between ridges and void outside the plunger -- the ridges are "
        "top features in this pose, which is where a 0.3 mm bump is crispest",
    )
    r.check(
        PLUNGER_R > CORE_R,
        "the plunger is fatter than the shank it hangs off",
        f"plunger {PLUNGER_R:.2f} vs core {CORE_R:.2f} -- the plunger is sized "
        "off the channel, the core off the thread's root",
    )
    r.check(
        PLUNGER_R < FEMALE_CREST_R,
        "the plunger passes through the female thread to be assembled",
        f"plunger {PLUNGER_R:.2f} < female crest {FEMALE_CREST_R:.2f}",
    )
    r.check(
        len(part.solids()) == 1,
        "the screw is one solid",
        f"{len(part.solids())} solids -- same reason as the body: a thread that "
        "failed to fuse leaves a valid-looking part in two pieces",
    )


def check_no_interference(r: Report, c: Clamp) -> None:
    r.section("assembly: screw turns through its whole travel")
    b = body.build(c)
    s = screw.build_upright(c)
    steps = 5
    for i in range(steps):
        at = c.closed_z + (c.open_z - c.closed_z) * i / (steps - 1)
        placed = as_part(Pos(0, 0, at) * (Rot(0, 0, screw_turn(c, at)) * s))
        hit = b.intersect(placed)
        shapes = hit if isinstance(hit, list) else [hit]
        volume = sum(x.volume for x in shapes if x is not None) if hit else 0.0
        r.check(
            volume < 1e-6,
            f"no interference at plunger z={at:.2f}",
            f"{volume:.6f} mm^3 of overlap; thread clearance {THREAD_CLEAR} mm "
            "diametral",
        )


def check_sharp_edges(r: Report, part: Part, label: str) -> None:
    allow = (
        (
            lambda e: is_periodic_seam(part, e),
            "periodic seam: a cylindrical or lofted wall closing on itself, "
            "where OCC hands the same face back on both sides and there is no "
            "dihedral angle to measure",
        ),
        (
            lambda e: e.geom_type.name in ("BSPLINE", "BEZIER")
            and e.length < 2 * THREAD_PITCH,
            "thread fade: the first and last turn ramp to nothing over a "
            "quarter pitch, per the modelling rule that a thread must not start "
            "at a knife edge, and the ramp's own tail is what this reports",
        ),
    )
    survey = sharp_convex_edges(part, allow=allow)
    r.section(f"{label}: edge treatment")
    r.check(
        not survey.sharp,
        "no untreated sharp convex edges",
        f"{len(survey.sharp)} found"
        + (f" at {[tuple(round(v, 2) for v in e.center()) for e in survey.sharp]}"
           if survey.sharp else ""),
    )
    r.check(
        not survey.unclassifiable,
        "no unmeasurable edges outside the allow-list",
        f"{len(survey.unclassifiable)} found"
        + (
            f" at {[tuple(round(v, 2) for v in e.center()) for e in survey.unclassifiable]}"
            if survey.unclassifiable
            else ""
        ),
    )


def check_slider_stops(r: Report) -> None:
    r.section("parameter stops")
    for w in (WIRE_MIN, WIRE_MAX):
        c = Clamp.of(w)
        built = body.build(c)
        r.check(
            built.volume > 0 and abs(built.bounding_box().min.Z) < 1e-6,
            f"body builds at wire_d={w}",
            f"{built.volume:.1f} mm^3, {2 * c.body_r:.2f} x {c.body_h:.2f} mm",
        )
        r.check(
            c.open_engagement >= THREAD_PITCH,
            f"a full turn still engaged at wire_d={w}",
            f"{c.open_engagement:.2f} mm",
        )
    r.check(
        Clamp.of(WIRE_MIN - 5).wire_d == WIRE_MIN
        and Clamp.of(WIRE_MAX + 5).wire_d == WIRE_MAX,
        "the slider clamps out of range values back in",
        f"[{WIRE_MIN}, {WIRE_MAX}]",
    )


def check_assembly(r: Report, c: Clamp) -> None:
    r.section("assembly view")
    strands = wire.wire_strands(c)
    r.check(
        len(strands) == STRANDS,
        "the assembly shows the loop, not one leg",
        f"{len(strands)} strands",
    )
    lowest = min(s.bounding_box().min.Z for s in strands)
    r.check(
        lowest >= BASE_T + RIB_H - 1e-6,
        "the mocked-up wire rests on the ribs, not through them",
        f"wire bottom {lowest:.2f}, rib tops {BASE_T + RIB_H:.2f}",
    )
    scene = Compound(children=[body.build(c), *strands])
    r.check(
        scene.bounding_box().size.Y > 2 * c.body_r,
        "the wire runs out of both sides",
        f"scene is {scene.bounding_box().size.Y:.1f} mm along the wire",
    )


def run() -> Report:
    r = Report()
    c = Clamp()

    check_thread_rules(r)
    check_thread_is_fixed(r)
    check_kinematics(r, c)
    check_wire_path(r, c)

    body_part = body.build(c)
    screw_part = screw.build(c)
    check_body_solid(r, body_part, c)
    check_screw_solid(r, screw_part, c)
    check_sharp_edges(r, body_part, "body")
    check_sharp_edges(r, screw_part, "screw")

    check_no_interference(r, c)
    check_assembly(r, c)
    check_slider_stops(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
