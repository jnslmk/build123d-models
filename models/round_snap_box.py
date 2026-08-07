"""Round box with a snap-on lid that closes flush.

The box has a *stepped* rim (a rabbet): the top of the box wall is recessed
inward to a thin lip. The lid drops over that lip and its outer face sits flush
with the box's lower body -- so when closed the assembly is one continuous
cylinder with no lip standing proud. This works by spending the wall budget
asymmetrically: the box body wall is thick, the lid wall is thin, and the two
plus the joint clearance add up to the body wall.

    body_wall = lip_wall + clearance + lid_wall

A continuous bead on the lip and a matching bead inside the lid skirt interlock
to snap the box shut; both beads live inside the joint, so they never break the
flush exterior.

**The two beads are what make this a snap rather than a friction fit.** As the
lid goes on, its bead has to climb over the box's bead: interference peaks when
the two cross (at ``SNAP`` above seated), then *drops* as the lid bead falls
past into the space below. That peak-then-drop is the click, and the height of
the drop is the retention -- pulling the lid off has to push the interference
back up over the same peak. ``check()`` measures the whole profile with an
insertion sweep rather than assuming it.

Two parts, both returned already in print pose (box floor-down, lid mouth-up).
Exterior horizontal rings (box bottom, lid top) get 45 chamfers -- clean edges
that also fight elephant's foot on the bed.
"""

from build123d import (
    Align,
    Axis,
    BuildPart,
    Compound,
    Cylinder,
    GeomType,
    Locations,
    Mode,
    Part,
    Pos,
    Rotation,
    SortBy,
    Torus,
    chamfer,
)

from models.lib import fits
from models.lib.checks import (
    Report,
    is_periodic_seam,
    is_solid_at,
    sharp_convex_edges,
)

# --- Box interior (the two numbers the user actually cares about) -----------
INNER_DIA = 78.0  # ID of the box
INNER_HEIGHT = 20.0  # usable depth from the floor up

# --- Walls (asymmetric so the closed box is flush) --------------------------
# BODY_WALL = lip_wall + CLEARANCE + LID_WALL is the flush identity, and this
# budget is the one this box has always shipped: outside diameter 82.8 mm.
#
# box-closures section 3 asks for "2 perimeters of material behind the bead: a
# 0.4 mm bead wants a 1.2 mm lip". Read that against how the beads are actually
# built here -- both are `Torus(..., mode=Mode.ADD)` centred on the member's
# face, so they *protrude* and nothing is cut away. The material behind such a
# bead is therefore the member's whole wall, and the skill's "1.2 mm lip" is
# the total section at the bead (0.8 mm of backing + the 0.4 mm bead standing
# proud of it), not 1.2 mm of backing on top of the bead. So the rule binds as
#
#   lip_wall >= MIN_WALL   and   LID_WALL >= MIN_WALL
#
# which 0.95 and 1.2 both satisfy. An earlier revision of this file read it as
# `>= MIN_WALL + BEAD`, double-counting the bead's own height, and grew
# BODY_WALL to 3.0 (OD 84.0 mm) to satisfy the stricter rule it had just
# invented. The joint measures the same either way -- same 0.30 mm barrier,
# same 6.1x detent, 0.88% vs 0.87% strain -- so the growth bought nothing and
# was reverted. A bead that is *cut into* a member would owe the stricter form.
BODY_WALL = 2.4  # box lower body wall (thick: carries the lip + lid + gap)
LID_WALL = 1.2  # lid wall + top (thin: nests into the recess, carries a bead)
FLOOR = 2.4  # box floor thickness
MIN_WALL = 0.8  # 2 perimeters at a 0.4 mm nozzle -- fdm-fits-and-clearances
# The lip's top face is a free rim, not a structural wall: it carries no load
# and both of its edges get a lead-in chamfer. It only has to stay printable --
# one full extrusion wide, so the top face is a real flat rather than the crest
# where two chamfers meet. MIN_WALL would be the wrong floor here and would
# squeeze the lead-ins to 0.075 mm on this lip, which no nozzle resolves.
MIN_RIM = 0.4  # 1 extrusion width at a 0.4 mm nozzle
# Radial gap between lip and lid inner wall -- diametral equivalent is 0.5 mm
# (fits.py's classes are diametral; this one is per-side, so double it before
# comparing). That is looser than fits.FREE (0.40 mm diametral, PETG
# baseline), the nearest class. Deliberate, not an error: the joint is ~83 mm
# across (out_r 41.4 mm), near the scaling rule's +0.05 mm/100 mm threshold,
# and the lid skirt must also flex enough to ride over the retaining bead
# (BEAD, radial) on the way to snapping home -- the bead pair sets true
# centring and retention, so this gap only has to clear the lip without
# binding, not locate anything precisely. It is also a step tighter than the
# 0.3 mm this box used to ship, which box-closures called "the number to beat".
CLEARANCE = 0.25  # radial gap between lip and lid inner wall
# lip_wall = BODY_WALL - LID_WALL - CLEARANCE  (derived; keep it >= MIN_WALL)

# --- Snap fit ----------------------------------------------------------------
# Double-bead interlock: the box carries an external bead on its lip, the lid a
# matching internal bead in its bore. Three different radial quantities come out
# of that pairing, and keeping them apart is the whole design:
#
#   peak    = 2*BEAD - CLEARANCE   the two beads crossing, at SNAP above seated
#   seated  = BEAD - CLEARANCE     box bead vs the lid's plain bore, at rest
#   barrier = peak - seated = BEAD the step the lid must climb to come off
#
# * `peak` drives the STRAIN, and it is momentary -- one stroke per open or
#   close. That is the load Covestro's allowable-strain table is written for,
#   and (materials.md) its 0.60x derate for "frequent separation and rejoining"
#   is exactly this joint's duty cycle, so `peak` is compared against PETG's
#   *repeated-use* 1.0%, not its 1.7% one-shot figure.
# * `seated` is SUSTAINED for as long as the lid is shut. Neither PETG figure
#   is a creep allowable, so this one wants to be small, not merely legal.
# * `barrier` is the RETENTION. It is what a pull-off has to push back over,
#   and it is the number MIN_ENGAGEMENT gates -- not `seated`, which only sets
#   how rattle-free the closed lid feels.
#
# BEAD = 0.30 mm with CLEARANCE = 0.25 mm gives peak 0.35, seated 0.05 and
# barrier 0.30 mm on a d = 79.9 mm lip: momentary strain 0.88% (under the 1.0%
# repeated ceiling), sustained strain 0.13% (half the 0.25% the pre-existing
# BEAD = 0.4 / CLEARANCE = 0.3 budget sat at), and a barrier equal to
# led_psu_enclosure's 0.3 mm net engagement, this repo's worked precedent for a
# comfortable annular snap. check() measures all three, and sweeps the
# insertion to prove the peak-then-drop is really there. The whole strain fix
# lives in these two constants -- the wall budget is untouched.
#
# Two earlier revisions of this joint are worth not repeating. BEAD = 0.4 with
# CLEARANCE = 0.3 put the momentary peak at 1.25%, over the repeated ceiling.
# Deleting the lid's bead to cure that (leaving one bead riding a plain bore)
# cured the peak but destroyed the joint: with nothing for the bead to fall
# past, interference is flat over the entire stroke -- no click, retention by
# friction rather than geometry (box-closures section 1: a friction fit "wears
# looser every cycle"), and the strain that used to be momentary becomes
# permanent.
BEAD = 0.30  # radial protrusion of each interlocking bead
BEAD_DROP = 3.0  # box bead centre, measured down from the box rim
SNAP = 1.0  # how far the seated lid bead sits below the box bead
LIP_H = 8.0  # recessed lip height / lid engagement depth
# Minimum radial *barrier* (see above) for the retention to survive a real
# print rather than only the boolean kernel. fdm-fits-and-clearances Rule 6: an
# uncalibrated extrusion multiplier alone eats 0.1-0.2 mm off the inside of a
# hole -- "if press fits feel impossible... the flow rate is the first suspect,
# not the CAD" -- so a barrier under the top of that band could be erased by
# flow variance alone. Rule 4's ~0.34 mm two-halves budget (0.24 mm hole
# undersize + 0.10 mm shaft oversize) is the same argument at larger scale, and
# it cuts both ways: it can as easily *add* interference, which is why the
# momentary-strain check below has to keep headroom under the ceiling too
# rather than sitting on it.
MIN_ENGAGEMENT = 0.20  # mm radial; fdm-fits-and-clearances Rule 6 flow-variance ceiling

# --- Edges -------------------------------------------------------------------
RING_CHAMFER = 0.8  # 45 chamfer on the exterior bottom/top rings
LEAD_IN = 0.4  # small lead-in chamfer at the joint mouths

# UI schema for the parametric web app. See tessellate_models.model_params().
#
# SCOPE OF THE BOUNDS BELOW -- this applies to the four *joint* sliders
# (`body_wall`, `lid_wall`, `clearance`, `bead`) and NOT to `inner_dia` or
# `inner_height`, which are unguarded (see the known gap at the end of this
# comment). The snap couples those four: `bead` and `clearance` together set
# the momentary strain, the sustained strain and the retention barrier at once,
# and each wall slider takes its width straight out of the other's, so a
# wide-open range offers settings that quietly stop being a snap. Each bound is
# the one that holds *with the other three sliders at their defaults*: seated
# interference positive (the lid does not rattle), barrier >= MIN_ENGAGEMENT
# (it still retains), and momentary strain under PETG's 1.0% repeated ceiling.
#
# KNOWN GAPS, accepted rather than hidden -- PARAMS cannot express a constraint
# between two sliders, so neither of these can be fixed here:
#   * Two sliders at opposing corners can still leave the envelope: bead 0.32
#     with clearance 0.22 reaches ~1.04% momentary strain, and bead 0.26 with
#     clearance 0.28 leaves zero seated interference.
#   * `inner_dia` has no strain guard at all -- hoop strain is y/d, so shrinking
#     the box raises it (~3% at the 20 mm floor). Pre-existing, and worse before
#     BEAD came down.
# check() pins the defaults, which is what the website renders first and what
# `uv run check round_snap_box` measures.
PARAMS = [
    {
        "name": "inner_dia",
        "label": "Inner diameter (mm)",
        "type": "number",
        "min": 20.0,
        "max": 200.0,
        "step": 0.5,
        "default": INNER_DIA,
    },
    {
        "name": "inner_height",
        "label": "Inner height (mm)",
        "type": "number",
        "min": 5.0,
        "max": 120.0,
        "step": 0.5,
        "default": INNER_HEIGHT,
    },
    {
        # Floor is MIN_WALL + CLEARANCE + LID_WALL: the thinnest body that
        # still leaves the lip 2 perimeters of backing behind its bead.
        "name": "body_wall",
        "label": "Box body wall (mm)",
        "type": "number",
        "min": 2.3,
        "max": 5.0,
        "step": 0.1,
        "default": BODY_WALL,
    },
    {
        # Floor leaves the lid mouth a lead-in (LID_WALL - MIN_WALL); at
        # MIN_WALL exactly the mouth chamfer vanishes. The ceiling is the same
        # budget seen from the other end -- every 0.1 mm added here comes
        # straight off the lip, and past 1.35 the lip drops under MIN_WALL.
        "name": "lid_wall",
        "label": "Lid wall (mm)",
        "type": "number",
        "min": 1.0,
        "max": 1.3,
        "step": 0.1,
        "default": LID_WALL,
    },
    {
        # Below ~0.22 the momentary peak (2*BEAD - clearance) crosses the 1.0%
        # ceiling; at 0.30 it equals BEAD and the seated interference vanishes.
        "name": "clearance",
        "label": "Joint clearance (mm)",
        "type": "number",
        "min": 0.22,
        "max": 0.28,
        "step": 0.01,
        "default": CLEARANCE,
    },
    {
        # Below CLEARANCE the beads never seat against anything; above ~0.33
        # the momentary peak crosses the 1.0% ceiling.
        "name": "bead",
        "label": "Snap bead size (mm)",
        "type": "number",
        "min": 0.26,
        "max": 0.32,
        "step": 0.01,
        "default": BEAD,
    },
]


def _chamfer_edge(builder, edge, size):
    """Chamfer one edge, isolating an OCC failure so it can't cascade."""
    saved = builder.part
    try:
        chamfer(edge, length=size)
    except Exception as exc:  # noqa: BLE001 -- OCC edge ops are flaky
        builder.part = saved
        print(f"warning: chamfer skipped ({exc})")


def _dims(inner_dia, body_wall, lid_wall, clearance):
    """Shared radii so box and lid stay mated."""
    inner_r = inner_dia / 2
    out_r = inner_r + body_wall  # flush outer radius (box body & lid)
    lid_inner_r = out_r - lid_wall  # lid bore
    lip_r = lid_inner_r - clearance  # recessed lip outer radius
    return inner_r, out_r, lid_inner_r, lip_r


def _rim_lead_in(lip_wall: float) -> float:
    """The lead-in the lip's top rim can afford on *both* of its edges.

    The lip's top face is an annulus ``lip_wall`` wide, and it gets a lead-in
    chamfer at each edge -- outward-facing (so the lid funnels on) and
    inward-facing (the cavity mouth). Two 45 deg chamfers of size ``c`` eat
    ``2*c`` of that width between them, so an unbounded ``LEAD_IN`` on a thin
    lip leaves a knife rim: at this box's 0.95 mm lip, two 0.4 mm chamfers
    leave a 0.15 mm ring. Cap the size so ``MIN_RIM`` of flat rim always
    survives, and return 0.0 rather than a negative when even that is
    impossible.

    The floor is ``MIN_RIM``, not ``MIN_WALL``: this is a free top face rather
    than a structural wall, and holding it to two perimeters would leave only
    0.075 mm of lead-in on this lip -- far below what a 0.4 mm nozzle resolves,
    i.e. trading a real chamfer for a nominal one.

    This also keeps ``_chamfer_edge`` from having to swallow an OCC failure: an
    over-large chamfer is what made it roll back and silently restore the sharp
    edge it was called to remove.
    """
    return max(0.0, min(LEAD_IN, (lip_wall - MIN_RIM) / 2))


def create_box(
    inner_dia: float = INNER_DIA,
    inner_height: float = INNER_HEIGHT,
    body_wall: float = BODY_WALL,
    lid_wall: float = LID_WALL,
    clearance: float = CLEARANCE,
    bead: float = BEAD,
) -> Part:
    """The box body: prints floor-down, open mouth up (its natural pose)."""
    inner_r, out_r, _, lip_r = _dims(inner_dia, body_wall, lid_wall, clearance)
    rim_z = FLOOR + inner_height  # top of the wall
    shoulder_z = rim_z - LIP_H  # where the body steps in to the lip
    bead_z = rim_z - BEAD_DROP

    with BuildPart() as box:
        # Lower body at the full (flush) outer radius, base on the bed.
        Cylinder(out_r, shoulder_z, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Recessed lip on top, at the smaller radius -> forms the seat shoulder.
        with Locations((0, 0, shoulder_z)):
            Cylinder(lip_r, LIP_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Hollow the cavity out above the floor.
        with Locations((0, 0, FLOOR)):
            Cylinder(
                inner_r,
                inner_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # External retaining bead on the lip (inner half merges into the lip).
        with Locations((0, 0, bead_z)):
            Torus(lip_r, bead, mode=Mode.ADD)

        # Exterior bottom ring: 45 chamfer (clean edge + elephant's-foot relief).
        bottom = box.faces().sort_by(Axis.Z).first
        _chamfer_edge(box, bottom.edges().sort_by(SortBy.RADIUS).last, RING_CHAMFER)
        # Both lead-ins on the lip's top rim, sized so the rim keeps MIN_WALL of
        # flat between them (see _rim_lead_in).
        rim_lead_in = _rim_lead_in(lip_r - inner_r)
        if rim_lead_in > 0:
            # Outer edge first, so the lid funnels onto the lip.
            top = box.faces().sort_by(Axis.Z).last
            _chamfer_edge(box, top.edges().sort_by(SortBy.RADIUS).last, rim_lead_in)
            # Then the cavity mouth's inner edge -- re-query the top face, since
            # the previous chamfer just changed its outer boundary.
            top = box.faces().sort_by(Axis.Z).last
            _chamfer_edge(box, top.edges().sort_by(SortBy.RADIUS).first, rim_lead_in)

    return box.part


def create_lid(
    inner_dia: float = INNER_DIA,
    inner_height: float = INNER_HEIGHT,
    body_wall: float = BODY_WALL,
    lid_wall: float = LID_WALL,
    clearance: float = CLEARANCE,
    bead: float = BEAD,
) -> Part:
    """The snap-on lid; returned flipped to its print pose (mouth up)."""
    _, out_r, lid_inner_r, _ = _dims(inner_dia, body_wall, lid_wall, clearance)
    # Skirt + top. Both terms must come from the *parameter*, not the module
    # constant: the lid's top thickness is what sets how deep the lid sits over
    # the rim, so taking LID_WALL here while the caller passed something else
    # built a lid whose top and wall disagreed, and the joint stopped seating.
    lid_total = LIP_H + lid_wall

    # Seated: lid interior top meets box rim, so the box bead lands at
    # lid-frame z = LIP_H - BEAD_DROP; the lid bead sits SNAP below that. That
    # gap is what makes the joint a detent rather than a friction fit: the two
    # beads cross (peak interference) SNAP before the lid is home, then the lid
    # bead drops past into the clear space below it.
    lid_bead_z = LIP_H - BEAD_DROP - SNAP

    with BuildPart() as lid:
        # Solid outer at the flush radius, mouth at z=0, closed top up.
        Cylinder(out_r, lid_total, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Interior the lip slides into.
        Cylinder(
            lid_inner_r,
            LIP_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # Internal retaining bead (inner half protrudes into the bore). The lid
        # is the thicker of the two members (LID_WALL vs the lip), which is the
        # side box-closures prefers to carry a bead.
        with Locations((0, 0, lid_bead_z)):
            Torus(lid_inner_r, bead, mode=Mode.ADD)

        # Lead-in on the mouth's inner edge (helps it catch the lip). The lid
        # mouth is a lid_wall-wide annulus and only its inner edge is chamfered
        # here, so it needs MIN_WALL left over rather than _rim_lead_in's
        # two-sided budget.
        mouth_lead_in = max(0.0, min(LEAD_IN, lid_wall - MIN_WALL))
        mouth = lid.faces().sort_by(Axis.Z).first
        if mouth_lead_in > 0:
            _chamfer_edge(
                lid, mouth.edges().sort_by(SortBy.RADIUS).first, mouth_lead_in
            )
        # Exterior top ring: 45 chamfer (ends up on the bed once flipped).
        top = lid.faces().sort_by(Axis.Z).last
        _chamfer_edge(lid, top.edges().sort_by(SortBy.RADIUS).last, RING_CHAMFER)

    # Print pose: flip so the open mouth faces up, then re-seat on z=0.
    part = Rotation(180, 0, 0) * lid.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


def create(
    inner_dia: float = INNER_DIA,
    inner_height: float = INNER_HEIGHT,
    body_wall: float = BODY_WALL,
    lid_wall: float = LID_WALL,
    clearance: float = CLEARANCE,
    bead: float = BEAD,
) -> Compound:
    """Box + lid laid out side by side, each in its own print pose."""
    box = create_box(inner_dia, inner_height, body_wall, lid_wall, clearance, bead)
    lid = create_lid(inner_dia, inner_height, body_wall, lid_wall, clearance, bead)
    gap = inner_dia + 2 * body_wall + 20
    return Compound(children=[box, Pos(gap, 0, 0) * lid])


def check() -> Report:
    """Pin the joint's clearance, bead engagement and wall budget on the defaults.

    Runs against the ``PARAMS`` defaults (``create_box()``/``create_lid()`` with
    no arguments), same as ``uv run check round_snap_box`` and the website's
    first render. The bead/undercut math is the double-bead annular case that
    the ``snap-fits`` skill works through for this exact file, and that skill's
    worked example tracks the constants below. See it before changing the
    strain assertions here.
    """
    r = Report()
    inner_r, out_r, lid_inner_r, lip_r = _dims(
        INNER_DIA, BODY_WALL, LID_WALL, CLEARANCE
    )
    box = create_box()
    lid = create_lid()
    probe = 0.05
    rim_z = FLOOR + INNER_HEIGHT  # top of the box wall
    shoulder_z = rim_z - LIP_H  # where the body steps in to the lip

    r.section("walls")
    lip_wall = BODY_WALL - LID_WALL - CLEARANCE
    # Point-sample the built box, not just the _dims() arithmetic: the earlier
    # version of this check re-derived lip_r - inner_r from the same formula
    # _dims() already uses, so it could never disagree with itself no matter
    # what create_box() actually built. Sample away from the bead (z_probe is
    # 3 mm clear of bead_z) so the bead's own protrusion doesn't confuse the
    # reading.
    z_probe = shoulder_z + 2.0
    r.check(
        not is_solid_at(box, inner_r - probe, 0, z_probe)
        and is_solid_at(box, inner_r + probe, 0, z_probe)
        and is_solid_at(box, lip_r - probe, 0, z_probe)
        and not is_solid_at(box, lip_r + probe, 0, z_probe),
        "the lip wall is actually built from inner_r to lip_r",
        f"sampled at z={z_probe:.2f} mm: open below {inner_r:.2f}, solid "
        f"{inner_r:.2f}-{lip_r:.2f}, open above {lip_r:.2f} mm -- matches "
        f"lip_wall = BODY_WALL - LID_WALL - CLEARANCE = {lip_wall:.2f} mm",
    )
    r.check(
        lip_wall >= MIN_WALL - 1e-9,
        "the rabbet lip clears the 2-perimeter wall floor",
        f"{lip_wall:.2f} mm (min {MIN_WALL} mm) -- {BODY_WALL} - {LID_WALL} - "
        f"{CLEARANCE}; the flush geometry silently thins this if LID_WALL or "
        "CLEARANCE is raised without BODY_WALL following",
    )
    r.check(
        BODY_WALL >= MIN_WALL - 1e-9 and LID_WALL >= MIN_WALL - 1e-9,
        "body and lid walls each clear the 2-perimeter floor",
        f"body {BODY_WALL} mm, lid {LID_WALL} mm (min {MIN_WALL} mm)",
    )
    r.check(
        FLOOR >= MIN_WALL - 1e-9,
        "floor clears the 2-perimeter floor",
        f"{FLOOR} mm (min {MIN_WALL} mm)",
    )
    # box-closures section 3: "Leave >= 2 perimeters of material behind the
    # bead: a 0.4 mm bead wants a 1.2 mm lip." Both beads here are built with
    # `Torus(..., mode=Mode.ADD)` centred on the member's face, so they stand
    # proud and nothing is cut away -- the material *behind* each bead is that
    # member's entire wall, and the skill's "1.2 mm lip" is the total section
    # (0.8 mm backing + a 0.4 mm bead standing on it). So the rule binds as
    # `wall >= MIN_WALL` for a protruding bead. A bead *cut into* a member
    # would owe `MIN_WALL + BEAD` instead, since the cut eats its own depth;
    # an earlier revision applied that stricter form to these protruding beads
    # and grew BODY_WALL 2.4 -> 3.0 to satisfy it, for no measured gain.
    r.check(
        lip_wall >= MIN_WALL - 1e-9,
        "the lip keeps 2 perimeters of backing behind its protruding bead",
        f"lip {lip_wall:.2f} mm vs MIN_WALL = {MIN_WALL:.2f} mm -- the bead is "
        f"added on top of this wall (+{BEAD:.2f} mm proud), not cut into it, so "
        "the backing is the full lip",
    )
    r.check(
        LID_WALL >= MIN_WALL - 1e-9,
        "the lid wall keeps 2 perimeters of backing behind its protruding bead",
        f"lid {LID_WALL:.2f} mm vs MIN_WALL = {MIN_WALL:.2f} mm -- the lid is "
        "the thicker of the two members, which is the side box-closures "
        "prefers to carry a bead",
    )
    # The lip's top rim takes a lead-in chamfer on *each* edge, so an unbounded
    # LEAD_IN leaves a knife ring between them (0.15 mm on this 0.95 mm lip;
    # 0.10 mm on the 0.90 mm lip this box shipped before CLEARANCE tightened).
    # _rim_lead_in caps it; point-sample the built rim just below the top face
    # to confirm the flat that survives is real, not just arithmetic.
    rim_lead_in = _rim_lead_in(lip_wall)
    rim_probe_z = rim_z - rim_lead_in - probe  # below both chamfers' run-out
    rim_lo = inner_r + rim_lead_in
    rim_hi = lip_r - rim_lead_in
    r.check(
        rim_hi - rim_lo >= MIN_RIM - 1e-9
        and is_solid_at(box, rim_lo + probe, 0, rim_probe_z)
        and is_solid_at(box, rim_hi - probe, 0, rim_probe_z),
        "the lip's top rim keeps MIN_RIM of flat between its two lead-ins",
        f"{rim_hi - rim_lo:.2f} mm of flat rim (r={rim_lo:.2f}-{rim_hi:.2f} mm, "
        f"solid when sampled at z={rim_probe_z:.2f} mm) after two "
        f"{rim_lead_in:.2f} mm lead-ins on a {lip_wall:.2f} mm lip -- MIN_RIM "
        "(1 extrusion), not MIN_WALL: a free top face has to be printable, not "
        "structural",
    )

    r.section("fit")
    diametral_clearance = 2 * CLEARANCE  # CLEARANCE is per-side; fits.py is diametral
    r.check(
        diametral_clearance > fits.FREE,
        "lip-to-lid clearance is looser than fits.FREE (deliberate -- see "
        "CLEARANCE's own comment: the joint is near the scaling rule's "
        "threshold and the lid skirt must also flex over the bead)",
        f"{diametral_clearance:.2f} mm diametral vs fits.FREE={fits.FREE:.2f} mm",
    )

    r.section("bead / undercut")
    bead_z = rim_z - BEAD_DROP
    # Point-sample the built solids for the bead's actual peak radius and the
    # lid bore's actual radius, rather than trusting the arithmetic alone --
    # this is what would catch a BEAD_DROP or LIP_H drift that moves the bead
    # off the lip entirely, or a stray feature narrowing the lid bore again.
    box_bead_peak = lip_r + BEAD
    r.check(
        is_solid_at(box, box_bead_peak - probe, 0, bead_z)
        and not is_solid_at(box, box_bead_peak + probe, 0, bead_z),
        "box bead protrudes exactly BEAD past the lip",
        f"solid to r={box_bead_peak:.2f} mm at z={bead_z:.2f} mm",
    )
    # The lid is returned in print pose (mouth up); its bead sits at
    # LID_WALL + BEAD_DROP + SNAP from the bed in that pose (derived from the
    # same flip the seated-assembly transform below re-derives independently).
    lid_bead_z_print_pose = LID_WALL + BEAD_DROP + SNAP
    lid_bead_trough = lid_inner_r - BEAD
    r.check(
        not is_solid_at(lid, lid_bead_trough - probe, 0, lid_bead_z_print_pose)
        and is_solid_at(lid, lid_bead_trough + probe, 0, lid_bead_z_print_pose),
        "lid bead protrudes exactly BEAD into the bore",
        f"open to r={lid_bead_trough:.2f} mm at z={lid_bead_z_print_pose:.2f} mm",
    )

    # Three different radial quantities fall out of the bead pair, and they
    # carry three different engineering meanings (see the BEAD comment). All
    # three are built from radii the point-sample checks above confirmed the
    # real solids stop at, not from _dims()-style algebra that could never
    # disagree with itself.
    #
    #   peak    = the two beads crossing, SNAP above seated -- MOMENTARY, one
    #             stroke per open or close. This is the strain-driving number.
    #   seated  = box bead vs the lid's plain bore, at rest -- SUSTAINED for as
    #             long as the lid is shut, so it is the creep-relevant one.
    #   barrier = peak - seated -- the step a pull-off has to climb back over.
    #             This, not `seated`, is the retention.
    peak_interf = box_bead_peak - lid_bead_trough
    seated_interf = max(0.0, box_bead_peak - lid_inner_r)
    barrier = peak_interf - seated_interf
    d = 2 * lip_r
    y_peak = 2 * peak_interf
    y_seated = 2 * seated_interf
    epsilon = 100 * y_peak / d  # percent hoop strain, momentary
    epsilon_seated = 100 * y_seated / d  # percent hoop strain, sustained
    # PETG (Prusament), from the snap-fits skill's materials.md: flexural
    # modulus 1.7 GPa, elongation at yield 5.1% -> ceiling = 1/3 of that; the
    # repeated-use figure is Covestro's 0.60x derate for "frequent separation
    # and rejoining". AGENTS.md defaults every model to PETG unless stated
    # otherwise, and this box states no other material.
    petg_one_shot_pct = 1.7
    petg_repeated_pct = 1.0
    r.check(
        epsilon <= petg_one_shot_pct + 1e-9,
        "momentary hoop strain stays under PETG's one-shot ceiling",
        f"{epsilon:.2f}% vs {petg_one_shot_pct}% ceiling "
        f"(y={y_peak:.2f} mm, d={d:.1f} mm)",
    )
    r.check(
        epsilon <= petg_repeated_pct + 1e-9,
        "momentary hoop strain stays under PETG's repeated-use ceiling",
        f"{epsilon:.2f}% vs {petg_repeated_pct}% ceiling -- this is the "
        "double-bead crossing peak, the load Covestro's table is written for, "
        "and the 0.60x repeated derate is for 'frequent separation and "
        "rejoining', which is exactly this lid's duty cycle. The older "
        "BEAD=0.4/CLEARANCE=0.3 budget put this at 1.25%, over the ceiling",
    )
    # Neither PETG figure above is a creep allowable -- both are short-term
    # snap numbers. A joint that holds strain permanently is a different
    # question from one that peaks for a stroke, so the sustained figure is
    # held to the tighter of the two limits deliberately: it should be a small
    # fraction of the ceiling, not merely under it.
    sustained_ceiling = petg_repeated_pct / 2
    r.check(
        epsilon_seated <= sustained_ceiling + 1e-9,
        "sustained (lid-shut) hoop strain stays well clear of the ceiling",
        f"{epsilon_seated:.2f}% vs {sustained_ceiling:.2f}% "
        f"(half the repeated ceiling, used as a creep guard because neither "
        f"PETG figure is a creep allowable) -- seated interference "
        f"{seated_interf:.2f} mm radial",
    )
    # Note what this one is and is not. `barrier` reduces algebraically to BEAD
    # (peak - seated = (2*BEAD - CLEARANCE) - (BEAD - CLEARANCE)), so this is a
    # DESIGN GATE on a constant -- "is BEAD big enough to survive print
    # variance" -- not a measurement of the built solids. It cannot catch a
    # geometry regression; the point-sample checks above and the insertion
    # sweep below are what do that. It is kept because the threshold it encodes
    # is a real sourced limit that a future BEAD edit should have to argue with.
    r.check(
        barrier >= MIN_ENGAGEMENT - 1e-9,
        f"retention barrier clears the {MIN_ENGAGEMENT:.2f} mm dimensional-error "
        "floor (design gate on BEAD, not a geometry measurement)",
        f"{barrier:.2f} mm radial (peak {peak_interf:.2f} - seated "
        f"{seated_interf:.2f}, which reduces to BEAD) vs {MIN_ENGAGEMENT:.2f} mm "
        "floor (fdm-fits-and-clearances Rule 6's 0.1-0.2 mm flow-variance band). "
        "The barrier is what a pull-off must climb, so it -- not the seated "
        "interference -- is what has to survive real FDM dimensional error",
    )

    r.section("closed-state interference")
    seat_shift = rim_z + LID_WALL
    seated_lid = Pos(0, 0, seat_shift) * Rotation(180, 0, 0) * lid
    r.check(
        abs(seated_lid.bounding_box().min.Z - shoulder_z) < 1e-6,
        "seated lid's skirt bottom lands exactly on the box's shoulder",
        f"{seated_lid.bounding_box().min.Z:.3f} mm vs shoulder {shoulder_z:.3f} mm",
    )
    common = box.intersect(seated_lid)
    shapes = (
        []
        if common is None
        else (list(common) if isinstance(common, list) else [common])
    )
    vol = sum(s.volume for s in shapes)
    r.check(
        vol > 0,
        "box and lid interfere when seated (the retention itself)",
        f"{vol:.2f} mm^3",
    )
    r.check(
        len(shapes) == 1,
        "the interference is one contiguous region, not scattered clashes",
        f"{len(shapes)} region(s)",
    )
    if shapes:
        ib = shapes[0].bounding_box()
        r.check(
            ib.size.Z < BEAD_DROP,
            "the interference is confined near the bead, not the whole joint",
            f"{ib.size.Z:.2f} mm tall (bead centres BEAD_DROP={BEAD_DROP} mm apart)",
        )
        max_r = ib.size.X / 2
        r.check(
            abs(max_r - box_bead_peak) < 0.05,
            "the interference's radial extent matches the box bead's peak",
            f"{max_r:.2f} mm vs bead peak {box_bead_peak:.2f} mm",
        )

    r.section("insertion profile (is it actually a snap?)")

    # `vol > 0` seated proves the parts touch; it does NOT prove the joint is a
    # snap. A bead riding a constant-diameter bore also intersects at every
    # offset -- flat profile, no click, retention by friction rather than
    # geometry, and the hoop strain sustained instead of momentary. A revision
    # of this file did exactly that and passed every check that existed at the
    # time. So sweep the insertion and require the shape of a real detent:
    # interference has to PEAK partway on (where the beads cross, at SNAP above
    # seated) and then DROP as the lid bead falls past into the clear space.
    def interference_at(delta: float) -> float:
        placed = Pos(0, 0, seat_shift + delta) * Rotation(180, 0, 0) * lid
        got = box.intersect(placed)
        parts = [] if got is None else (list(got) if isinstance(got, list) else [got])
        return sum(s.volume for s in parts)

    offsets = (2.0, SNAP, 0.0)
    profile = {delta: interference_at(delta) for delta in offsets}
    v_approach, v_peak, v_seated = (profile[delta] for delta in offsets)
    trace = ", ".join(f"{delta:.2f}mm->{profile[delta]:.2f}" for delta in offsets)
    r.check(
        v_peak > v_approach and v_peak > v_seated,
        "interference peaks mid-insertion, where the two beads cross",
        f"volume mm^3 by offset above seated: {trace} -- the peak at "
        f"delta=SNAP={SNAP} mm is the beads crossing",
    )
    # The drop off that peak is the click, and how far it drops is how
    # decisively the lid seats. A shallow drop is a joint that merely gets
    # tighter rather than one that snaps.
    drop_ratio = v_peak / v_seated if v_seated > 0 else float("inf")
    r.check(
        drop_ratio >= 2.0,
        "the peak drops off decisively once seated (the click)",
        f"{v_peak:.2f} -> {v_seated:.2f} mm^3, a {drop_ratio:.1f}x drop "
        "(>=2x required; a flat profile means a friction fit, which "
        "box-closures section 1 warns 'wears looser every cycle')",
    )

    r.section("edges")

    def on_shoulder(e) -> bool:
        b = e.bounding_box()
        return abs(b.min.Z - shoulder_z) < 0.05 and abs(b.max.Z - shoulder_z) < 0.05

    def _is_round_wall_seam(part: Part, e) -> bool:
        # sharp_convex_edges now reports the None edges used to drop unseen
        # (see its docstring). Point-sampling the 7 edges this caught (4 on
        # the box, 3 on the lid, before this predicate existed) shows every
        # one sits at a fixed (x, y) -- i.e. a fixed radius -- and runs
        # vertically: the box's cavity/bore ID (r=inner_r, one seam, FLOOR to
        # the rim lead-in), lip OD (r=lip_r, two seams) and body OD
        # (r=out_r, one seam, the bottom chamfer to the shoulder); the lid's
        # OD (r=out_r, one seam) and bore ID (r=lid_inner_r, two seams). Each
        # of those is a plain revolved/extruded cylinder -- nothing ever cuts
        # sideways into one -- so it carries its own closing seam purely from
        # OCC's periodic parametrisation, with no nearby boolean cut for that
        # seam to coincide with (unlike a seam that lands on a genuine
        # near-tangent sliver elsewhere in this repo; see
        # ``is_periodic_seam``'s docstring for why that distinction matters
        # and why this does not stop at "same face"). Where a wall also
        # carries the interlocking bead (lip OD, lid bore ID), the fused
        # torus locally interrupts the wall and splits its one seam into two
        # -- still the same untrimmed periodic seam on either side, not a
        # second feature, which is why this predicate matches 4 edges on 3
        # walls on the box and 3 on 2 on the lid rather than one apiece.
        # Scoped to a straight, purely-vertical LINE so this cannot also
        # claim some other, differently-shaped edge -- in particular, not the
        # bead's own closing seam (a circular arc, not a straight vertical
        # line), which is a classic source of a genuine tangent-runout sliver
        # elsewhere but is not among the edges this predicate has ever
        # matched here.
        if e.geom_type != GeomType.LINE:
            return False
        b = e.bounding_box()
        if b.size.X > 1e-6 or b.size.Y > 1e-6:
            return False
        return is_periodic_seam(part, e)

    box_allow = (
        (
            on_shoulder,
            "lid mouth seats flat-on-flat on this shoulder -- box-closures says "
            "explicitly: do not chamfer it",
        ),
        (
            lambda e: _is_round_wall_seam(box, e),
            "a concentric round wall's own untrimmed cylindrical seam -- "
            "confirmed via is_periodic_seam, no nearby cut for it to "
            "coincide with",
        ),
    )
    box_edges = sharp_convex_edges(box, allow=box_allow)
    r.check(
        not box_edges.sharp,
        "box has no unexplained sharp convex edges",
        f"{len(box_edges.sharp)} found" if box_edges.sharp else "all treated or named",
    )
    r.check(
        not box_edges.unclassifiable,
        "box has no unexplained unclassifiable convex edges",
        f"{len(box_edges.unclassifiable)} found"
        if box_edges.unclassifiable
        else "all measured or named",
    )

    # The lid's own mouth-outer edge, in its print pose (mouth up), sits at
    # z = LIP_H + LID_WALL. Replaying the seated-assembly transform above on
    # this edge alone lands it at (r=out_r, z=shoulder_z) -- exactly the same
    # seam as the box's on_shoulder exception above, verified below rather
    # than asserted on faith. It is the same flush exterior mating edge seen
    # from the lid's side, not a second defect: chamfering it would cut a
    # groove into the promised flush seam (see the module docstring's "one
    # continuous cylinder with no lip standing proud").
    lid_mouth_outer_z = LIP_H + LID_WALL
    seated_z = seat_shift - lid_mouth_outer_z  # Rotation(180,0,0) negates z
    r.check(
        abs(seated_z - shoulder_z) < 1e-6,
        "the lid's mouth-outer edge lands on the box's shoulder when seated",
        f"seated z={seated_z:.3f} mm vs shoulder {shoulder_z:.3f} mm -- same "
        "seam as on_shoulder above, confirmed by replaying the seating "
        "transform on the edge's own z instead of assuming it",
    )

    def on_flush_seam(e) -> bool:
        b = e.bounding_box()
        return (
            abs(b.min.Z - lid_mouth_outer_z) < 0.05
            and abs(b.max.Z - lid_mouth_outer_z) < 0.05
        )

    lid_allow = (
        (
            on_flush_seam,
            "same seam as the box's on_shoulder exception, seen from the "
            "lid's side (verified above by replaying the seating transform) "
            "-- chamfering it would break the flush mate",
        ),
        (
            lambda e: _is_round_wall_seam(lid, e),
            "a concentric round wall's own untrimmed cylindrical seam -- "
            "confirmed via is_periodic_seam, no nearby cut for it to "
            "coincide with",
        ),
    )
    lid_edges = sharp_convex_edges(lid, allow=lid_allow)
    r.check(
        not lid_edges.sharp,
        "lid has no unexplained sharp convex edges",
        f"{len(lid_edges.sharp)} found" if lid_edges.sharp else "all treated or named",
    )
    r.check(
        not lid_edges.unclassifiable,
        "lid has no unexplained unclassifiable convex edges",
        f"{len(lid_edges.unclassifiable)} found"
        if lid_edges.unclassifiable
        else "all measured or named",
    )

    return r
