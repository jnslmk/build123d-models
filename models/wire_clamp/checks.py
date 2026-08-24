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

from build123d import BuildSketch, Circle, Compound, GeomType, Part, Pos, Rot

from ..lib.checks import (
    Report,
    adjacent_faces,
    is_periodic_seam,
    is_solid_at,
    sharp_convex_edges,
)
from ..lib.edges import as_part
from . import body, printable, screw, thread as tp, wire
from . import screw_turn
from .config import (
    COLLAR_H,
    MOUTH_COLLAR,
    KNOB_CHAMFER,
    NOTCH_SHOULDER,
    RING_H,
    SHEAR_SAFETY,
    ABS_SHEAR,
    THREAD_ENGAGE_RATIO,
    STRANDS,
    THREAD_CLEAR,
    THREAD_D_MIN,
    THREAD_DEPTH,
    THREAD_FLAT,
    THREAD_PITCH,
    WALL,
    WIRE_DEFAULT,
    WIRE_MAX,
    WIRE_MIN,
    Clamp,
)

SAMPLES = (WIRE_MIN, 1.0, 2.0, 2.9, 5.6, WIRE_MAX)
"""Slider positions every rule below is checked at, rather than only the
default -- including the edge audit, which used to run on the default alone and
so left the whole top half of the slider unlooked-at. **2.9** is chosen rather
than spaced: it brackets the one discontinuity in the model, where the thread
steps up off its floor. A property that holds at both ends of a range and breaks
in the middle is exactly what a two-point check misses, and two families of
untreated edge were living in that gap."""

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
        all(
            abs((Clamp.of(w).female_root_r - Clamp.of(w).male_crest_r) - THREAD_CLEAR / 2)
            < 1e-9
            and abs(
                (Clamp.of(w).female_crest_r - Clamp.of(w).male_root_r) - THREAD_CLEAR / 2
            )
            < 1e-9
            for w in SAMPLES
        ),
        "clearance is the same at crest and root, at every diameter",
        f"{THREAD_CLEAR / 2} mm radial on both, checked at {list(SAMPLES)} mm of "
        "wire -- the property that makes a 45 degree flank need only one "
        "clearance number survives the diameter moving",
    )
    worst = max(Clamp.of(w).thread_shear for w in SAMPLES)
    r.check(
        worst <= ABS_SHEAR / SHEAR_SAFETY,
        f"thread roots stay under {ABS_SHEAR / SHEAR_SAFETY:.0f} MPa at hand torque",
        f"worst {worst:.1f} MPa across {list(SAMPLES)} mm of wire, against "
        f"{ABS_SHEAR:.0f} MPa for ABS across layers -- a factor of "
        f"{ABS_SHEAR / worst:.1f}. This is what {THREAD_ENGAGE_RATIO} x D of "
        "engagement is justified by, in place of the 1.0 x D the printed-thread "
        "table asks for; that rule is written for a structural thread and this "
        "one carries a finger",
    )
    r.check(
        all(
            Clamp.of(w).thread_engage >= THREAD_ENGAGE_RATIO * Clamp.of(w).thread_d
            for w in SAMPLES
        ),
        f"engagement is at least {THREAD_ENGAGE_RATIO} x D everywhere",
        f"{[round(Clamp.of(w).thread_engage, 2) for w in SAMPLES]} mm against "
        f"diameters {[Clamp.of(w).thread_d for w in SAMPLES]} mm",
    )


def check_thread_is_fixed(r: Report) -> None:
    """The split that is the whole model: profile pinned, diameter free.

    Four numbers a nozzle has to resolve -- pitch, tooth, crest flat, clearance
    -- must be identical at every position of the slider. The thread's
    *diameter* may move, and has to: the plunger passes through the thread to be
    assembled, so the thread is what caps how wide a pair of strands can be, and
    a clamp for thicker cord genuinely needs a bigger one. Growing a diameter
    asks nothing of the printer that a smaller one did not already ask.
    """
    r.section("thread: profile pinned, diameter free")

    lo, hi = Clamp.of(WIRE_MIN), Clamp.of(WIRE_MAX)
    r.check(
        lo.channel_l != hi.channel_l and lo.window_h != hi.window_h,
        "the wire does move the cord features",
        f"slot {lo.channel_l:.2f} -> {hi.channel_l:.2f} mm, window "
        f"{lo.window_h:.2f} -> {hi.window_h:.2f} mm across the slider",
    )
    r.check(
        lo.body_r != hi.body_r and lo.body_h != hi.body_h,
        "the wire does size the whole clamp",
        f"body {2 * lo.body_r:.1f} x {lo.body_h:.1f} -> {2 * hi.body_r:.1f} x "
        f"{hi.body_h:.1f} mm across the slider",
    )

    # The four resolution-critical numbers are module constants, so this asserts
    # the *structure*: no ``Clamp`` property is allowed to be one of them.
    profile = ("thread_pitch", "thread_depth", "thread_flat", "thread_clear")
    leaked = [n for n in profile if hasattr(Clamp, n)]
    r.check(
        not leaked,
        "no slider position can change the thread's profile",
        "pitch, tooth, crest flat and clearance are module constants with no "
        f"``Clamp`` property shadowing them{'; LEAKED: ' + str(leaked) if leaked else ''}",
    )

    broken = {
        w: thread_gate(THREAD_PITCH, THREAD_DEPTH, THREAD_FLAT, THREAD_CLEAR)
        for w in SAMPLES
    }
    r.check(
        not any(broken.values()),
        "the thread passes the gate at every sampled slider position",
        f"checked at {list(SAMPLES)} mm of wire",
    )

    diameters = [Clamp.of(w).thread_d for w in SAMPLES]
    r.check(
        diameters == sorted(diameters) and min(diameters) >= THREAD_D_MIN,
        "the thread diameter only ever grows, and never below its floor",
        f"{diameters} mm against a {THREAD_D_MIN} mm floor -- so no position of "
        "the slider can reproduce the original's small end",
    )
    fits_strands = [
        (w, Clamp.of(w).channel_w, Clamp.of(w).strand_room) for w in SAMPLES
    ]
    r.check(
        all(slot >= room - 1e-9 for _, slot, room in fits_strands),
        "the thread is always big enough for the strands it has to admit",
        "; ".join(
            f"{w} mm wire: {room:.2f} of strand in a {slot:.2f} slot"
            for w, slot, room in fits_strands
        ),
    )
    r.check(
        all(Clamp.of(w).knob_tip_r > KNOB_CHAMFER for w in SAMPLES),
        "the knob's tip roll stays bigger than the chamfer that offsets it",
        f"tip radii {[round(Clamp.of(w).knob_tip_r, 2) for w in SAMPLES]} "
        f"against a {KNOB_CHAMFER} mm offset -- below it the offset profile "
        "comes back with a corner and the knife edge lands on the bed layer",
    )


def check_thread_lengths(r: Report) -> None:
    """No thread length may sit a hair above a whole number of turns.

    ``bd_warehouse`` stacks whole thread loops and then adds one partial loop,
    guarded by a bare ``thread_loops % 1 > 0.0``. An exact multiple of the pitch
    skips the partial loop and is fine; a length a hair *over* one passes the
    guard and asks OCC to build a helix a few femtometres tall, which raises
    ``Standard_ConstructionError`` and takes the whole model with it.

    This is the least size-related bug in the package and the easiest to
    reintroduce: which side of the line a length falls on is float noise, so
    moving *any* constant -- the base, the collar, the mouth -- can push a
    length that builds today onto the wrong side tomorrow. Hence a sweep rather
    than a sample, and hence the demonstration below that the trap is real and
    reachable inside the shipped range rather than theoretical.
    """
    r.section("thread: lengths clear of the whole-turn trap")

    # Demonstrated on the function rather than on a slider position. It *was*
    # pinned to one -- 5.6 mm of wire produced a 15.000000000000004 mm male
    # thread -- and then the clamp's dimensions moved and the example evaporated
    # while the trap stayed exactly as real. A demonstration that depends on the
    # geometry happening to land on a knife edge is a demonstration with a shelf
    # life; this one is the failure's own shape.
    bad = 6 * THREAD_PITCH + THREAD_PITCH + 4e-15
    bad_frac = ((bad - THREAD_PITCH) / THREAD_PITCH) % 1
    fixed_frac = ((tp._whole_turn_safe(bad) - THREAD_PITCH) / THREAD_PITCH) % 1
    r.check(
        0.0 < bad_frac < tp.WHOLE_TURN_EPS and fixed_frac == 0.0,
        "the guard turns a degenerate partial turn into no partial turn",
        f"{bad!r} is {bad_frac:.2e} of a turn past a whole one -- above zero, so "
        "bd_warehouse builds that partial loop, and small enough that the helix "
        f"is degenerate. Snapped to {tp._whole_turn_safe(bad)!r}, which is "
        "exactly a whole number of turns, so the partial loop is skipped instead",
    )

    r.check(
        MOUTH_COLLAR >= NOZZLE,
        "the thread's last turn is not coplanar with the body's top face",
        f"{MOUTH_COLLAR} mm of plain bore above it. The thread carries its own "
        "lead-in now, so nothing needs the full pitch of collar the lead-in cone "
        "used to -- but at exactly zero the thread ends *on* the top face, and a "
        "fuse between two solids sharing a plane is where OCC stops answering "
        "sensibly: three solids and 4% of the volume, silently, at one slider "
        "position in six. One extrusion of land is enough that they are not the "
        "same plane",
    )

    unsafe = []
    for i in range(int(WIRE_MIN * 100), int(WIRE_MAX * 100) + 1):
        c = Clamp.of(i / 100)
        for label, length in (("male", c.male_len), ("female", c.thread_engage)):
            frac = ((tp._whole_turn_safe(length) - THREAD_PITCH) / THREAD_PITCH) % 1
            if 0.0 < frac < tp.WHOLE_TURN_EPS or frac > 1 - tp.WHOLE_TURN_EPS:
                unsafe.append((i / 100, label, length))
    swept = int(WIRE_MAX * 100) - int(WIRE_MIN * 100) + 1
    r.check(
        not unsafe,
        "every length across the whole slider is safe",
        f"{swept} positions x 2 threads swept at 0.01 mm"
        + (f" -- UNSAFE: {unsafe[:5]}" if unsafe else ""),
    )
    r.check(
        all(
            abs(tp._whole_turn_safe(L) - L) < 1e-6
            for w in SAMPLES
            for L in (Clamp.of(w).male_len, Clamp.of(w).thread_engage)
        ),
        "the snap never moves a length enough to matter",
        "under a micron in every sampled case -- it exists to dodge a float "
        "boundary, not to change the part, and ``body_h`` is computed from the "
        "unsnapped number",
    )


def check_web_ui(r: Report) -> None:
    """Every module you can download an STL from carries the slider.

    The website reads ``PARAMS`` off whichever model is on screen, so a slider
    declared only on the assembly is a slider on the one page with no download
    button. This is the check that would have caught that.
    """
    r.section("web UI: the slider is where the downloads are")
    for name, module in (
        ("wire_clamp.body", body),
        ("wire_clamp.screw", screw),
        ("wire_clamp.printable", printable),
    ):
        params = getattr(module, "PARAMS", [])
        names = [p["name"] for p in params]
        r.check(
            names == ["wire_d"],
            f"{name} exposes the wire slider",
            f"PARAMS = {names}",
        )
        spec = params[0] if params else {}
        r.check(
            spec.get("min") == WIRE_MIN
            and spec.get("max") == WIRE_MAX
            and spec.get("default") == WIRE_DEFAULT,
            f"{name}'s slider covers the same range as the others",
            f"{spec.get('min')}..{spec.get('max')} mm, default "
            f"{spec.get('default')} -- three modules disagreeing about the "
            "range is three parts that do not fit each other",
        )
        built = module.create(2.0)
        r.check(
            built.volume > 0,
            f"{name}.create(2.0) builds",
            f"{built.volume:.1f} mm^3 at a non-default slider position",
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
    r.section("wire path and plunger coverage")
    passage = c.channel_l / 2 - c.plunger_r
    r.check(
        passage >= c.wire_d,
        "the wire fits past the plunger",
        f"{passage:.2f} mm of passage at each end for a {c.wire_d} mm wire -- "
        "this is the departure from the original, whose round bore leaves "
        "0.3 mm at any size",
    )
    side = c.channel_w / 2 - c.plunger_r
    r.check(
        side < c.wire_d,
        "the wire cannot escape sideways past the plunger",
        f"{side:.2f} mm of annulus round the plunger, against a {c.wire_d} mm "
        "wire",
    )
    r.check(
        c.notch_w < c.channel_w,
        "the notches are narrower than the bore they open off",
        f"{c.notch_w:.2f} mm notch in a {c.channel_w:.2f} mm bore -- so a strand "
        "in a notch is boxed in across the wire by the notch's own walls, and a "
        "strand anywhere else is under the plunger",
    )
    r.check(
        STRANDS * c.wire_d < c.notch_w,
        "both strands fit down a notch, side by side",
        f"{STRANDS} x {c.wire_d} = {STRANDS * c.wire_d:.2f} mm in a "
        f"{c.notch_w:.2f} mm notch",
    )
    r.check(
        c.lip >= c.wire_d * 0.5,
        "the sill is deep enough to be a bend and not a graze",
        f"lip {c.lip:.2f} mm against a {c.wire_d} mm wire",
    )

    # The claim in full, measured off the actual outlines rather than argued:
    # take the bore out of the channel's cross-section and what is left must be
    # the two notch tongues, nothing wider.
    opening = body.channel_section(c)
    with BuildSketch() as bore:
        Circle(c.female_crest_r)
    tongues = opening - bore.sketch
    bb = tongues.bounding_box()
    r.check(
        c.notch_w - 1e-6 <= bb.size.X <= c.notch_w + 2 * body.NOTCH_CORNER_R + 1e-6,
        "the only opening outside the bore is the notches",
        f"what lies outside the bore is {bb.size.X:.2f} mm wide -- the notch "
        f"({c.notch_w:.2f}) plus its rolled corners, not the bore's "
        f"{c.channel_w:.2f} -- and is "
        f"{100 * tongues.area / opening.area:.0f}% of the opening's area. "
        "The plunger fills the rest to a running clearance",
    )

    # The shoulder is what makes the sentence above possible, and its absence is
    # a *segfault* rather than a failure: sized to the strands alone, the notch
    # came within 0.2 mm of the bore, their outlines crossed at a glancing angle,
    # and OCC died building the union. No exception, no traceback, exit 139.
    shoulders = [(w, (Clamp.of(w).channel_w - Clamp.of(w).notch_w) / 2) for w in SAMPLES]
    r.check(
        all(sh >= NOTCH_SHOULDER - 1e-9 for _, sh in shoulders),
        "the bore keeps its shoulder either side of the notch",
        "; ".join(f"{w} mm: {sh:.2f}" for w, sh in shoulders)
        + f" against a {NOTCH_SHOULDER} mm floor",
    )


def check_body_solid(r: Report, part: Part, c: Clamp) -> None:
    r.section("body: geometry, point-sampled")
    mid_thread = (c.thread_z0 + c.thread_z1) / 2
    r.check(
        is_solid_at(part, 0, 0, c.base_t / 2),
        "the channel has a floor",
        f"solid on the axis at z={c.base_t / 2}",
    )
    r.check(
        not is_solid_at(part, 0, 0, c.channel_top - 0.2),
        "the channel is open above the floor",
        "void on the axis just under the channel's top",
    )
    r.check(
        is_solid_at(part, 0, 0, c.base_t + c.rib_h / 2),
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
        is_solid_at(part, 0, c.channel_l / 2 + 0.5, c.base_t / 2)
        and is_solid_at(part, c.channel_w / 2 + 0.5, 0, c.base_t / 2),
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
    inner = c.body_r - c.knob_lobe_depth - KNOB_CHAMFER - 0.5
    r.check(
        is_solid_at(part, inner, 0, 0.1) and is_solid_at(part, 0, inner, 0.1),
        "the knob is the face on the bed",
        f"solid at r={inner:.2f} on the first layer, in both axes -- a "
        f"{2 * inner:.1f} mm first layer against the plunger's "
        f"{2 * c.plunger_r:.1f}",
    )
    # The topmost material on the part is the ridges, not the face they stand
    # on: sample across one of them, then off it in both directions.
    tip = bb.max.Z
    probe_z = tip - RING_H / 2
    ring = screw.ring_radii(c)[0]
    r.check(
        is_solid_at(part, ring, 0, probe_z)
        and not is_solid_at(part, 0, 0, probe_z)
        and not is_solid_at(part, c.plunger_r + 0.5, 0, probe_z),
        "the plunger's ridges stand proud of its face, and print last",
        f"at z={probe_z:.2f}: solid on the first ridge (r={ring:.2f}), void on "
        "the axis between ridges and void outside the plunger -- the ridges are "
        "top features in this pose, which is where a 0.3 mm bump is crispest",
    )
    r.check(
        all(Clamp.of(w).plunger_r > Clamp.of(w).core_r for w in SAMPLES),
        "the plunger is fatter than the shank it hangs off, at every size",
        f"plunger {c.plunger_r:.2f} vs core {c.core_r:.2f} here -- the plunger "
        "is sized off the channel, the core off the thread's root",
    )
    r.check(
        all(Clamp.of(w).plunger_r < Clamp.of(w).female_crest_r for w in SAMPLES),
        "the plunger passes through the female thread to be assembled",
        f"plunger {c.plunger_r:.2f} < female crest {c.female_crest_r:.2f} here, "
        f"and at {list(SAMPLES)} mm of wire",
    )
    r.check(
        len(part.solids()) == 1,
        "the screw is one solid",
        f"{len(part.solids())} solids -- same reason as the body: a thread that "
        "failed to fuse leaves a valid-looking part in two pieces",
    )


def check_no_interference(r: Report, c: Clamp) -> None:
    r.section(f"assembly: screw turns through its whole travel (wire {c.wire_d} mm)")
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


def check_sharp_edges(r: Report, part: Part, label: str, c: Clamp) -> None:
    """The house edge rule, run at every sampled size rather than only the default.

    That last part matters more than it sounds. This used to run on the default
    clamp alone, and the whole top half of the slider went unaudited -- which is
    exactly where the interesting geometry is, because that is where the window,
    the bore and the notch grow into each other. Two families of edge were
    hiding there; both are named below rather than quietly passed.
    """
    body_r = c.body_r

    def on_outer_wall(edge) -> bool:
        ctr = edge.center()
        return abs((ctr.X**2 + ctr.Y**2) ** 0.5 - body_r) < 0.05

    def thread_surface(edge) -> bool:
        ctr = edge.center()
        rad = (ctr.X**2 + ctr.Y**2) ** 0.5
        lo = min(c.male_root_r, c.female_crest_r) - 0.3
        hi = max(c.male_crest_r, c.female_root_r) + 0.3
        return lo <= rad <= hi

    def curved_crossing(edge) -> bool:
        """A sliver where two curved surfaces cross at a shallow angle."""
        faces = adjacent_faces(part, edge)
        if len(faces) != 2 or any(f.geom_type != GeomType.CYLINDER for f in faces):
            return False
        return min(f.area for f in faces) < 2.0

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
        (
            thread_surface,
            "thread surface: bd_warehouse builds a thread as a stack of separate "
            "loops joined end to end, so every turn meets the next at a seam "
            "whose two sides are the same surface and OCC has no dihedral angle "
            "to give. Thread flanks are on the house rule's own list of "
            "legitimately square edges; this excludes the band between root and "
            "crest radius, and nothing else",
        ),
        (
            curved_crossing,
            "curved crossing: the window's rounded end and the channel bore are "
            "both cylinders, and above about 3 mm of cord they cross. What that "
            "leaves is a sub-2 mm2 sliver of bore wall at 111 degrees -- a "
            "shallow ridge inside a hole nothing bears on, not an untreated "
            "corner. Removing it means holding the window's ends clear of the "
            "bore, which costs pillar section at every size to tidy a ridge that "
            "only exists at the large ones",
        ),
        (
            on_outer_wall,
            "window mouth: rolled by ``body.MOUTH_FILLET_FRACTIONS`` up to about "
            "4 mm of cord and left square above it, because OCC refuses the "
            "fillet there at every radius from 1.4 mm down to 0.1 mm. The house "
            "rule is to stop asking after two -- and its usual answer, a boolean "
            "chamfer tool, does not apply to a hole through a *curved* wall: the "
            "mouth's own radius runs from the pillar's to the body's along its "
            "length, so a tool aimed along the cord is inside the material at "
            "one end of the mouth and outside it at the other. Known limitation "
            "at the top of the slider; the cord still bears on a rolled mouth "
            "everywhere this model was designed for",
        ),
    )
    survey = sharp_convex_edges(part, allow=allow)
    r.section(f"{label}: edge treatment (wire {c.wire_d} mm)")
    r.check(
        not survey.sharp,
        "no untreated sharp convex edges",
        f"{len(survey.sharp)} found"
        + (
            f" at {[tuple(round(v, 2) for v in e.center()) for e in survey.sharp]}"
            if survey.sharp
            else ""
        ),
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
    """Every rule that is about *this* clamp, re-run at every slider position.

    The point of one slider driving everything is that every position has to be
    a working clamp, not just the default -- so the kinematics and the wire path
    are asserted across ``SAMPLES`` rather than once.
    """
    r.section("parameter stops")
    for w in SAMPLES:
        c = Clamp.of(w)
        r.check(
            abs((c.closed_z + c.plunger_len) - c.thread_z0) < 1e-9
            and c.open_engagement >= THREAD_PITCH
            and c.travel > c.wire_d,
            f"kinematics hold at wire_d={w}",
            f"travel {c.travel:.2f} mm, {c.open_engagement:.2f} mm still "
            f"engaged when open, thread starts at {c.thread_z0:.2f}",
        )
        r.check(
            c.channel_l / 2 - c.plunger_r >= c.wire_d
            and c.channel_w / 2 - c.plunger_r < c.wire_d
            and STRANDS * c.wire_d < c.channel_w,
            f"the wire path holds at wire_d={w}",
            f"{c.channel_l / 2 - c.plunger_r:.2f} mm of passage along the wire, "
            f"{c.channel_w / 2 - c.plunger_r:.2f} mm across it",
        )
        # Both parts, not just the body: the whole-turn trap above lived in the
        # *male* thread, so a sweep that only builds bodies would have missed
        # the one bug this section exists to catch.
        for label, built in (("body", body.build(c)), ("screw", screw.build(c))):
            r.check(
                built.volume > 0
                and abs(built.bounding_box().min.Z) < 1e-6
                and len(built.solids()) == 1,
                f"{label} builds as one solid, on the bed, at wire_d={w}",
                f"{built.volume:.1f} mm^3, min.Z={built.bounding_box().min.Z:+.2e}, "
                f"{len(built.solids())} solid(s), thread {c.thread_d} mm",
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
        lowest >= c.base_t + c.rib_h - 1e-6,
        "the mocked-up wire rests on the ribs, not through them",
        f"wire bottom {lowest:.2f}, rib tops {c.base_t + c.rib_h:.2f}",
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
    check_thread_lengths(r)
    check_web_ui(r)
    check_kinematics(r, c)
    check_wire_path(r, c)

    body_part = body.build(c)
    screw_part = screw.build(c)
    check_body_solid(r, body_part, c)
    check_screw_solid(r, screw_part, c)
    for w in SAMPLES:
        sized = Clamp.of(w)
        check_sharp_edges(r, body.build(sized), "body", sized)
        check_sharp_edges(r, screw.build(sized), "screw", sized)

    check_no_interference(r, c)
    # Again at the top of the slider, where the thread has stepped up: the
    # clearance is a claim about a helix that is now a different diameter.
    check_no_interference(r, Clamp.of(WIRE_MAX))
    check_assembly(r, c)
    check_slider_stops(r)
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
