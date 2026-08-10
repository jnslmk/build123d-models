"""Geometry assertions for the cable spool.

    uv run check cable_spool
    uv run python -m models.cable_spool.checks

Almost nothing this model claims is visible in a projection. "The middle disc
slides past the ribs and the cover does not" is a claim about four pockets in a
bore. "The clip's jaws land on the rim ring" is a claim about where a face
stops, and it is exactly the claim the source model gets wrong. "The clip can
be pushed on" is not a claim about either solid on its own -- it is a claim
about the two of them together, which is why the last section here is a
boolean and not a probe.

Four groups, and each exists because something specific could go wrong:

* **The plate.** Windows and spokes, sampled where the geometry is supposed to
  change rather than where it is obviously solid.
* **The staircase.** The whole spacing scheme is two heights on one radius. If
  a seat moves, the channels change height and nothing else complains.
* **The clip.** Its three faults are the reason this package exists, so each is
  asserted as its inverse: it is round, its jaws land on the ring, and its
  spring is inside PETG's strain limit.
* **Assembly.** The clip and the discs, intersected. A clip that fouls the rim
  by a tenth of a millimetre passes every probe above and cannot be fitted.
"""

from __future__ import annotations

import sys
from math import asin, cos, degrees, radians, sin

from build123d import Part, Rotation

from ..lib.checks import (
    Report,
    is_periodic_seam,
    is_solid_at,
    sharp_convex_edges,
)
from ..lib.edges import as_part
from . import base as base_mod
from . import clip as clip_mod
from . import config as cfg
from . import cover as cover_mod
from . import middle as middle_mod

PETG_STRAIN_REPEATED = 0.010
"""`snap-fits` `references/materials.md`, Prusament PETG: 5.1% elongation at
yield, a third of it for a printed part, 60% of that again for a joint that is
taken apart and put back together."""

PETG_FLEX_MODULUS = 1700.0
"""MPa, flexural (not tensile -- a snap arm is a beam in bending)."""

FRICTION = 0.5
"""House default for like-on-like FDM plastic, same source."""


def at(part: Part, r: float, theta: float, z: float) -> bool:
    """Is there material at a cylindrical coordinate? `theta` in degrees."""
    a = radians(theta)
    return is_solid_at(part, r * cos(a), r * sin(a), z)


def _plate(r: Report, base: Part) -> None:
    """The disc every part is cut from: six windows, six 10 mm spokes."""
    r.check(at(base, 85.0, 17.0, 1.0), "rim ring is solid all the way round")
    r.check(
        not at(base, 55.0, cfg.WINDOW_PHASE, 1.0),
        "a window is open at its centre",
    )
    spoke = cfg.WINDOW_PHASE + 30.0
    r.check(at(base, 55.0, spoke, 1.0), "a spoke is solid at its centre")

    # The spokes are straight 10 mm bars, so at radius r they subtend
    # asin(5/r) either side of centre and not one degree more.
    half = degrees(asin(cfg.SPOKE_HALF_W / 55.0))
    r.check(
        at(base, 55.0, spoke + half - 0.6, 1.0)
        and not at(base, 55.0, spoke + half + 0.6, 1.0),
        f"spoke edge at r=55 sits at {half:.2f} deg, i.e. {cfg.SPOKE_HALF_W} mm off-axis",
    )
    r.check(
        at(base, 40.0, spoke + degrees(asin(cfg.SPOKE_HALF_W / 40.0)) - 0.8, 1.0)
        and not at(base, 40.0, spoke + degrees(asin(cfg.SPOKE_HALF_W / 40.0)) + 0.8, 1.0),
        "the same 10 mm width holds at r=40 -- the spokes are bars, not wedges",
    )
    r.check(
        not at(base, cfg.OUTER_R - 0.3, 0.0, cfg.PLATE_T - 0.3),
        "the rim's top edge is chamfered, not square",
    )


def _staircase(r: Report, base: Part, middle: Part, cover: Part) -> None:
    """Two heights on one radius, which is the whole spacing scheme."""
    plain = 0.0  # between two ribs (45 deg apart) and clear of both slots
    r.check(
        at(base, cfg.HUB_RIB_R - 0.2, plain, cfg.MIDDLE_Z - 0.3)
        and not at(base, cfg.HUB_RIB_R - 0.2, plain, cfg.MIDDLE_Z + 0.3),
        f"the collar stops at MIDDLE_Z = {cfg.MIDDLE_Z} -- the middle disc's seat",
    )
    r.check(
        at(base, cfg.HUB_RIB_R - 0.2, cfg.HUB_RIB_PHASE, cfg.COVER_Z - 0.3)
        and not at(base, cfg.HUB_RIB_R - 0.2, cfg.HUB_RIB_PHASE, cfg.COVER_Z + 0.3),
        f"the guide ribs stop at COVER_Z = {cfg.COVER_Z} -- the cover's seat",
    )
    r.check(
        at(base, cfg.HUB_R - 0.5, plain, cfg.STACK_H - 0.3),
        "the hub tube itself runs to the top of the stack",
    )
    r.check(
        not at(base, cfg.HUB_R - 0.5, cfg.CABLE_SLOT_PHASE, cfg.PLATE_T + 1.0),
        "the cable slot is open at the bottom of the first channel",
    )
    r.check(
        not at(base, cfg.HUB_R - 0.5, cfg.KEY_SLOT_PHASE, cfg.MIDDLE_Z + 1.0)
        and at(base, cfg.HUB_R - 0.5, cfg.KEY_SLOT_PHASE, cfg.MIDDLE_Z - 2.0),
        "the keyway starts at MIDDLE_Z and the collar below it is unbroken",
    )

    # The mechanism: same bore, opposite outcome, because of four pockets.
    probe_r = (cfg.HUB_RIB_R + cfg.MIDDLE_BORE_R) / 2.0
    r.check(
        not at(middle, probe_r, cfg.HUB_RIB_PHASE, 1.0),
        "the middle disc is relieved where a rib is, so it drops past",
    )
    r.check(
        at(middle, probe_r, plain, 1.0),
        "and is not relieved anywhere else, so it lands on the collar",
    )
    r.check(
        at(cover, probe_r, cfg.HUB_RIB_PHASE, 1.0),
        "the cover has no relief at all, which is what stops it on the ribs",
    )
    r.check(
        at(middle, cfg.MIDDLE_KEY_R + 0.3, cfg.KEY_SLOT_PHASE, 1.0)
        and at(middle, cfg.MIDDLE_KEY_R + 0.3, cfg.CABLE_SLOT_PHASE, 1.0),
        "the middle disc's two keys reach into both hub slots",
    )
    r.check(
        not at(cover, cfg.MIDDLE_KEY_R + 0.3, cfg.KEY_SLOT_PHASE, 1.0),
        "the cover has no keys -- it is located by the clips, not the hub",
    )


def _clip_shape(r: Report, clip: Part) -> None:
    """The three faults of the source clip, asserted as their inverses."""
    # 1. It is round. The inner face is one cylinder across the whole wrap.
    span = cfg.CLIP_WRAP / 2.0 - 1.0
    angles = [-span, -span / 2.0, 0.0, span / 2.0, span]
    on = [at(clip, cfg.CLIP_BORE_R + 0.4, a, 10.0) for a in angles]
    off = [not at(clip, cfg.CLIP_BORE_R - 0.4, a, 10.0) for a in angles]
    r.check(
        all(on) and all(off),
        f"the spine's bore is a true cylinder at r={cfg.CLIP_BORE_R} over all "
        f"{cfg.CLIP_WRAP} deg, not a chord across it",
    )

    # 2. Both jaws bear on the 10 mm ring, and neither reaches past it.
    r.check(
        at(clip, cfg.RIM_INNER_R + 0.5, 0.0, -cfg.CLIP_JAW_T / 2.0)
        and at(clip, cfg.OUTER_R - 1.0, 0.0, -cfg.CLIP_JAW_T / 2.0),
        "the lower jaw covers the rim ring from r=80 out to the rim",
    )
    top_z = cfg.STACK_H + cfg.CLIP_STACK_CLEAR + cfg.CLIP_TOP_JAW_T / 2.0
    r.check(
        at(clip, cfg.CLIP_TOP_JAW_LEDGE_R + 0.5, 0.0, top_z)
        and at(clip, cfg.OUTER_R - 1.0, 0.0, top_z),
        "the upper jaw's flat land is r 86.4..90 -- all of it on the ring",
    )
    r.check(
        not at(clip, cfg.CLIP_TOP_JAW_R - 0.5, 0.0, top_z),
        "and it stops before the windows start, unlike the source clip's lips",
    )

    # The mouth is a clearance fit, not a clamp: nothing between the jaws.
    r.check(
        not at(clip, cfg.OUTER_R - 1.0, 0.0, cfg.STACK_H / 2.0),
        "the mouth is open over the whole stack height",
    )
    r.check(
        not at(clip, cfg.OUTER_R - 1.0, 0.0, cfg.STACK_H + cfg.CLIP_STACK_CLEAR / 2.0),
        f"the upper jaw clears the cover by {cfg.CLIP_STACK_CLEAR} mm",
    )

    # 3. The detent, which is what actually holds the clip on.
    tooth = clip_mod.TOOTH_ANGLE
    r.check(
        at(clip, cfg.DETENT_TOOTH_OUTER_R - 0.3, tooth, cfg.DETENT_LEAD_Z / 2.0),
        "the tooth reaches the window wall it catches on",
    )
    r.check(
        not at(clip, cfg.RIM_INNER_R + 0.1, tooth, 0.2),
        "and stops short of it, so the tooth cannot foul the disc it locks into",
    )
    r.check(
        at(clip, cfg.DETENT_TOOTH_INNER_R + 0.5, tooth, cfg.DETENT_TOOTH_H - 0.2)
        and not at(clip, cfg.DETENT_TOOTH_INNER_R + 0.5, tooth, cfg.DETENT_TOOTH_H + 0.2),
        f"the tooth stands {cfg.DETENT_TOOTH_H} mm proud -- the undercut the arm rides",
    )
    arm_mid = (cfg.DETENT_INNER_R + cfg.DETENT_OUTER_R) / 2.0
    r.check(
        at(clip, arm_mid, tooth, -cfg.DETENT_H / 2.0),
        "the arm is there under the tooth",
    )
    r.check(
        not at(clip, arm_mid, tooth, -cfg.DETENT_H - 0.2),
        "with nothing below it -- that gap is the only reason it can bend",
    )
    r.check(
        not at(clip, cfg.DETENT_OUTER_R + 0.4, tooth, -cfg.DETENT_H / 2.0),
        "and a slot between the arm and the lower jaw, so the two are separate",
    )
    r.check(
        at(clip, arm_mid, -cfg.CLIP_WRAP / 2.0 + cfg.DETENT_ROOT_ARC / 2.0, -cfg.CLIP_JAW_T + 0.2),
        "the arm's root block is solid to the jaw's own bottom face",
    )


def _snap_sizing(r: Report) -> None:
    """The cantilever arithmetic from `snap-fits`, held to its own limits."""
    h = cfg.DETENT_H
    b = cfg.DETENT_OUTER_R - cfg.DETENT_INNER_R
    length = cfg.DETENT_L
    y = cfg.DETENT_TOOTH_H

    strain = y * h / (0.67 * length**2)
    force = (b * h**2 / 6.0) * (PETG_FLEX_MODULUS * strain / length)
    lead = radians(cfg.DETENT_LEAD_ANGLE)
    mating = force * (FRICTION + sin(lead) / cos(lead)) / (
        1.0 - FRICTION * sin(lead) / cos(lead)
    )

    r.check(
        strain <= PETG_STRAIN_REPEATED,
        f"root strain {strain * 100:.2f}% is inside PETG's repeated-use 1.00%",
    )
    r.check(y >= h, f"undercut {y} mm >= arm thickness {h} mm")
    r.check(y >= 1.2, f"undercut {y} mm >= the 1.2 mm FDM floor")
    r.check(h >= 1.6, f"arm thickness {h} mm >= 4 perimeters at a 0.4 mm nozzle")
    r.check(b >= 6.0, f"arm width {b} mm >= the 6 mm floor")
    r.check(length / h >= 10.0, f"l/h = {length / h:.1f} -- a slender beam, as assumed")
    r.check(
        5.0 <= mating <= 50.0,
        f"push-on force {mating:.1f} N is in the 20-50 N band's comfortable end",
    )
    # The fault being fixed, stated as a number: the source arm's own strain.
    source = 3.0 * 1.6 * 2.0 / (2.0 * 10.4**2)
    r.check(
        source > PETG_STRAIN_REPEATED,
        f"for contrast, the source clip's arms run {source * 100:.1f}% -- over yield",
    )


def _fits_together(r: Report, base: Part, middle: Part, cover: Part, clip: Part) -> None:
    """The one thing no probe on a single solid can answer."""
    from build123d import Pos

    stack = [
        ("base", base),
        ("middle", as_part(Pos(0.0, 0.0, cfg.MIDDLE_Z) * middle)),
        ("cover", as_part(Pos(0.0, 0.0, cfg.COVER_Z) * cover)),
    ]
    for angle in cfg.clip_angles():
        placed = as_part(Rotation(0.0, 0.0, angle) * clip)
        for name, disc in stack:
            overlap = placed.intersect(disc)
            fouled = overlap.volume if overlap is not None else 0.0  # ty: ignore[possibly-missing-attribute]
            r.check(
                fouled < 1e-3,
                f"clip at {angle:.0f} deg does not foul the {name} ({fouled:.3f} mm^3)",
            )

    # And the converse: it has to actually overlap the faces it holds.
    r.check(
        at(clip, cfg.RIM_INNER_R + 2.0, 0.0, -0.2)
        and at(clip, cfg.CLIP_TOP_JAW_LEDGE_R + 1.0, 0.0, cfg.STACK_H + 0.5),
        "the jaws overlap the base's underside and the cover's top face",
    )
    # The tooth has to land in a window, not on a spoke, at the angle the
    # clips are actually placed. This is why CLIP_COUNT is 3 and not 4.
    reach = cfg.DETENT_TOOTH_ARC / 2.0 + degrees(cfg.DETENT_L / 75.2)
    r.check(
        reach < degrees(asin(cfg.window_half_width(78.0) / 78.0)),
        f"the tooth sits {reach:.1f} deg off the clip's centre, inside the "
        "window's own half-width -- so a clip centred on a window locks",
    )


def _radius(edge) -> float:
    c = edge.center()
    return (c.X**2 + c.Y**2) ** 0.5


ALLOW = (
    (
        lambda e: abs(_radius(e) - cfg.OUTER_R) < 1e-3
        and abs(e.center().Z - cfg.RIM_CHAMFER_H) < 1e-6,
        "the rim's top chamfer is deliberately shallower than 45 deg -- 3:1 on "
        "the base and 2:1 on the middle, both measured off the source -- so it "
        "leaves 108 and 117 deg where a 45 deg chamfer leaves 135. The edge is "
        "treated; it removes *more* material than the check's threshold assumes, "
        "not less",
    ),
    (
        lambda e: abs(e.center().Z - cfg.COVER_Z) < 1e-6
        and cfg.HUB_R - 0.6 < _radius(e) < cfg.HUB_RIB_R + 0.5,
        "the guide ribs' seat, same argument -- and unlike the collar the ribs "
        "cannot be widened to make room for one, because the middle disc has to "
        "slide past them",
    ),
    (
        lambda e: abs(e.center().Z - cfg.PLATE_T) < 1e-6
        and _radius(e) < cfg.HUB_BORE_R + 0.5,
        "the bore's upper mouth, buried inside the hub. Breaking it would "
        "undercut the liner that stands on it, and nothing reaches it",
    ),
    (
        lambda e: abs(e.center().Z - cfg.MIDDLE_Z) < 1e-6
        and _radius(e) < cfg.HUB_R,
        "the keyway's floor, inside the hub bore and under the middle disc",
    ),
    (
        lambda e: cfg.DETENT_TOOTH_INNER_R - cfg.DETENT_TOOTH_H - 0.5
        < _radius(e)
        < cfg.DETENT_TOOTH_OUTER_R + 0.5
        and -0.01 < e.center().Z < cfg.DETENT_TOOTH_H + 0.01,
        "the detent tooth's own flanks. Its outer face is the catch and its "
        "inner face the lead-in; a break on either is a break in the lock, and "
        "OCC declines a chamfer there at any size the ladder in clip.py tries",
    ),
    (
        lambda e: cfg.DETENT_INNER_R - 1.0 <= _radius(e) <= cfg.CLIP_JAW_INNER_R + 0.5
        and e.center().Z <= 1e-6,
        "the step where the detent arm leaves its root block, and the mouth of "
        "the 1.0 mm slot that lets the arm bend. Both sit under the base disc "
        "over a window, where nothing touches them, and a chamfer on the slot "
        "would open it past what a 0.4 mm nozzle can hold apart",
    ),
)
"""Edges this model ships square, each with the argument for doing so.

Every entry here is load-bearing: run `sharp_convex_edges` with `allow=()` over
the four parts and each of these predicates catches at least one edge. An entry
that stopped matching would be a claim about geometry that no longer exists,
which is worse than no entry at all -- the collar's seat had one until its
chamfer moved into the revolve profile, and it was deleted rather than left.
"""


def _edges(r: Report, parts: list[tuple[str, Part]]) -> None:
    """The house rule on raw edges, with this model's exceptions named."""
    for name, part in parts:
        survey = sharp_convex_edges(part, allow=ALLOW)
        r.check(
            not survey.sharp,
            f"{name}: no untreated sharp convex edges",
            ", ".join(f"{e.length:.1f} mm at {e.center()}" for e in survey.sharp[:6]),
        )
        unexplained = [
            e for e in survey.unclassifiable if not is_periodic_seam(part, e)
        ]
        r.check(
            not unexplained,
            f"{name}: every unmeasurable edge is a face closing on itself",
            f"{len(survey.unclassifiable)} seam(s)"
            + (
                ""
                if not unexplained
                else "; unexplained: "
                + ", ".join(f"{e.length:.1f} mm at {e.center()}" for e in unexplained[:6])
            ),
        )


def run() -> Report:
    r = Report()
    base = base_mod.create()
    middle = middle_mod.create()
    cover = cover_mod.create()
    clip = clip_mod.build()

    r.section("The plate")
    _plate(r, base)
    r.section("The staircase")
    _staircase(r, base, middle, cover)
    r.section("The clip")
    _clip_shape(r, clip)
    r.section("Snap sizing")
    _snap_sizing(r)
    r.section("Assembly")
    _fits_together(r, base, middle, cover, clip)
    r.section("Edges")
    _edges(r, [("base", base), ("middle", middle), ("cover", cover), ("clip", clip)])
    return r


def main() -> None:
    r = run()
    print(r.render())
    sys.exit(1 if r.failures else 0)


if __name__ == "__main__":
    main()
