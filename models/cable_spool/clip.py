"""The rim clip -- a redesign, not a reconstruction.

    uv run show cable_spool.clip
    uv run export cable_spool.clip      # the STL to print; you want three
    uv run check cable_spool

The source model's clip falls off, and measuring it says why. Three separate
things are wrong with it and any one of them would be enough:

1. **It is straight and the rim is round.** Its jaws are flat over 24 mm of a
   90 mm radius, so the middle of each jaw stands `24^2/(8*90) = 0.8 mm` off
   the disc it is meant to hold and the clip touches only at its two corners.
   It rocks, and every rock walks it further off.
2. **Its jaws land where there is no disc.** They reach 14.5 mm in from the
   rim and their retaining lips sit at r = 75.5..79.9 -- *inside* the 10 mm
   ring at r = 80..90, so at most angular positions there is nothing under
   them but a window. Whether a given clip grips at all depends on whether it
   happened to be pushed on over a spoke.
3. **Its arms are strained past yield the first time it is fitted.** 1.6 mm
   thick, 10.4 mm long, and forced 2.0 mm apart to get over the 20 mm stack:
   `eps = 3*t*y/(2*l^2) = 4.4%`, against 1.0% for PETG in repeated use and
   1.7% one-shot. They take a permanent set on assembly, and after that the
   clip is a loose collar.

So this one is a different mechanism, not a tidied-up version of that one. It
does not clamp. Its jaws are a clearance fit on the 20 mm stack and hold it
together without squeezing it -- PETG creeps, and a joint whose retention is a
sustained squeeze is a joint with a shelf life. What holds the clip *on* is a
detent: a curved cantilever under the base disc carrying a tooth that drops up
into one of the six windows and catches on the window's own r = 80 wall.

**Everything is a revolve about the spool axis**, so every face that touches
the spool is a true cylinder at the right radius rather than a chord across
it. That is the "correct curvature" the clip was missing, and getting it costs
nothing once the profile is drawn in the r-z plane.

**Where it goes.** Centred on a window -- the tooth needs one to drop into.
Three clips at 120 degrees land on alternate windows, which is why
`CLIP_COUNT` is 3 and not 4.

**Getting one off again.** The catch is a vertical face (`DETENT_TOOTH_OUTER_R`
says why it has to be), so it will not pull off: lift the spool, press the
arm's free end down about 1.6 mm, and slide the clip out.

**Print pose** is spool-axis-up, lower jaw on the bed, three per plate. Nothing
overhangs beyond the upper jaw's 3.8 mm ledge, and the detent arm lies flat in
XY so its bending stress runs along the extrusions rather than across the
layers -- which `snap-fits` calls the single biggest lever there is on a
printed spring.
"""

from __future__ import annotations

from math import atan2, degrees

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Part,
    Plane,
    Polyline,
    Pos,
    Rotation,
    add,
    make_face,
    revolve,
)

from ..lib.edges import as_part, chamfer_edge, fillet_edge
from . import config as cfg

_ARM_MID_R = (cfg.DETENT_INNER_R + cfg.DETENT_OUTER_R) / 2.0

ARM_ROOT_ANGLE = -cfg.CLIP_WRAP / 2.0 + cfg.DETENT_ROOT_ARC
"""Where the arm leaves its root block, degrees from the clip's centre."""

TOOTH_ANGLE = ARM_ROOT_ANGLE + degrees(cfg.DETENT_L / _ARM_MID_R)
"""Where the tooth sits: `DETENT_L` of arc further round, which is the whole
point of the clip being as wide as it is."""


def _revolved(points: list[tuple[float, float]], arc: float, phase: float) -> Part:
    """A closed `(r, z)` profile revolved `arc` degrees, centred on `phase`."""
    with BuildPart() as solid:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(*points, close=True)
            make_face()
        _ = sk
        revolve(axis=Axis.Z, revolution_arc=arc)
    return as_part(Rotation(0.0, 0.0, phase - arc / 2.0) * solid.part)


def _body_profile() -> list[tuple[float, float]]:
    """The C section: lower jaw, spine, upper jaw, with its breaks drawn in.

    Read it as a loop starting at the bottom of the mouth and going round the
    outside. The only two segments that are not obvious:

    * `(CLIP_TOP_JAW_LEDGE_R, top_lo)` back up to the tip is the 45 degree
      relief that keeps the upper jaw printable -- see that constant.
    * the pair either side of `CLIP_JAW_INNER_R` at `z = 0` is the mouth's
      lead-in, so the rim wedges in instead of butting a square corner.
    """
    jaw_in = cfg.CLIP_JAW_INNER_R
    out = cfg.CLIP_OUTER_R
    inner = cfg.CLIP_BORE_R
    ch = cfg.CLIP_EDGE_CHAMFER
    lead = cfg.CLIP_LEAD_IN
    bot = -cfg.CLIP_JAW_T
    top_lo = cfg.STACK_H + cfg.CLIP_STACK_CLEAR
    top_hi = top_lo + cfg.CLIP_TOP_JAW_T
    tip = cfg.CLIP_TOP_JAW_R
    nose = cfg.CLIP_TIP_BREAK
    # Where the 45 degree relief meets the tip: it rises one millimetre per
    # millimetre from the ledge, so it reaches the tip `LEDGE_R - tip` above
    # the underside. Getting this line backwards is what turns a 3.8 mm
    # unsupported ledge into a 6 mm one.
    tip_face = top_lo + (cfg.CLIP_TOP_JAW_LEDGE_R - tip)
    return [
        (jaw_in + ch, bot),
        (out - ch, bot),
        (out, bot + ch),
        (out, top_hi - ch),
        (out - ch, top_hi),
        (tip + nose, top_hi),
        (tip, top_hi - nose),
        (tip, tip_face),
        (cfg.CLIP_TOP_JAW_LEDGE_R, top_lo),
        (inner, top_lo),
        (inner, 0.0),
        (jaw_in + lead, 0.0),
        (jaw_in, -lead),
        (jaw_in, bot + ch),
    ]


def _tooth_profile() -> list[tuple[float, float]]:
    """The catch, in `(r, z)`.

    Flat on top, a `DETENT_LEAD_ANGLE` ramp on the outside for the base's rim
    to ride up during assembly, and `DETENT_LEAD_Z` of vertical face below
    that -- which is the bit that actually catches on the window wall, and the
    reason the tooth is `WINDOW_CHAMFER` taller than the vertical face is
    long. The inner face never touches anything and is drawn at 45 degrees
    only so it is not a wall of unsupported plastic.
    """
    h = cfg.DETENT_TOOTH_H
    lead_z = cfg.DETENT_LEAD_Z
    outer = cfg.DETENT_TOOTH_OUTER_R
    inner = cfg.DETENT_TOOTH_INNER_R
    return [
        (inner - h, 0.0),
        (inner, h),
        (outer - (h - lead_z), h),
        (outer, lead_z),
        (outer, 0.0),
    ]


def _radial_plane_edges(part: Part, planes: list[float]) -> list:
    """Every edge lying wholly in one of a set of radial planes.

    Everything in this part is a revolve, so every square corner it has that
    is not already broken in a profile lies in one of six planes: the clip's
    two ends, the plane the detent arm leaves its root block on, and the two
    ends of the tooth. Selecting them by geometry rather than by index means
    the list survives a change to any of those angles.
    """
    out = []
    for edge in part.edges():  # ty: ignore[invalid-argument-type]
        pts = [v.to_tuple() for v in edge.vertices()]
        if len(pts) != 2:
            continue
        angles = [degrees(atan2(y, x)) for x, y, _ in pts]
        if any(all(abs(a - t) < 1e-3 for a in angles) for t in planes):
            out.append(edge)
    return out


def cut_planes() -> list[float]:
    """The six radial planes that carry the clip's remaining square corners."""
    half_tooth = cfg.DETENT_TOOTH_ARC / 2.0
    return [
        cfg.CLIP_WRAP / 2.0,
        -cfg.CLIP_WRAP / 2.0,
        ARM_ROOT_ANGLE,
        TOOTH_ANGLE - half_tooth,
        TOOTH_ANGLE + half_tooth,
    ]


def build() -> Part:
    """The clip in spool coordinates: on the rim, where it is used."""
    with BuildPart() as clip:
        add(_revolved(_body_profile(), cfg.CLIP_WRAP, 0.0))

        # The block that roots the detent arm into the spine and lower jaw,
        # its own inner corners broken the same way the arm's are.
        rc = cfg.ARM_EDGE_CHAMFER
        add(
            _revolved(
                [
                    (cfg.DETENT_INNER_R + rc, -cfg.CLIP_JAW_T),
                    (cfg.CLIP_BORE_R, -cfg.CLIP_JAW_T),
                    (cfg.CLIP_BORE_R, 0.0),
                    (cfg.DETENT_INNER_R + rc, 0.0),
                    (cfg.DETENT_INNER_R, -rc),
                    (cfg.DETENT_INNER_R, -cfg.CLIP_JAW_T + rc),
                ],
                cfg.DETENT_ROOT_ARC,
                -cfg.CLIP_WRAP / 2.0 + cfg.DETENT_ROOT_ARC / 2.0,
            )
        )

        # The arm itself, hanging free from that block to the clip's far end.
        # Its four long edges are broken in the profile: the top two are under
        # the base disc's bearing face and the bottom two are what a finger
        # meets when the arm is pressed to release the clip.
        arm_arc = cfg.CLIP_WRAP / 2.0 - ARM_ROOT_ANGLE
        c = cfg.ARM_EDGE_CHAMFER
        lo, hi = cfg.DETENT_INNER_R, cfg.DETENT_OUTER_R
        add(
            _revolved(
                [
                    (lo + c, -cfg.DETENT_H),
                    (hi - c, -cfg.DETENT_H),
                    (hi, -cfg.DETENT_H + c),
                    (hi, -c),
                    (hi - c, 0.0),
                    (lo + c, 0.0),
                    (lo, -c),
                    (lo, -cfg.DETENT_H + c),
                ],
                arm_arc,
                ARM_ROOT_ANGLE + arm_arc / 2.0,
            )
        )

        add(_revolved(_tooth_profile(), cfg.DETENT_TOOTH_ARC, TOOTH_ANGLE))

        # Round the four long vertical edges where the arc ends -- the house
        # rule's "fillet vertical edges", and the corners a hand meets.
        # A ladder, not one radius: two of these four edges run alongside the
        # `CLIP_EDGE_CHAMFER` breaks on the spine, and OCC refuses a fillet
        # that does not fit its narrowest neighbouring face.
        ends = [e for e in clip.part.edges().filter_by(Axis.Z) if e.length > 5.0]
        for radius in (cfg.CLIP_END_FILLET, 1.2, 0.8):
            if fillet_edge(clip, ends, radius):
                break

        # Everything left is a raw 90 degree corner in one of the five radial
        # planes this part is cut on. Broken as a group, isolated, because a
        # chamfer that will not take on one of them must not silently kill the
        # rest (`build123d-geometry-ops`).
        # One plane at a time, each on its own size ladder: an edge that will
        # not take 0.4 mm on the tooth must not cost the spine its chamfer.
        for plane in cut_planes():
            edges = _radial_plane_edges(clip.part, [plane])
            for size in (cfg.CLIP_EDGE_CHAMFER / 2.0, 0.3, 0.2):
                if chamfer_edge(clip, edges, size):
                    break
    return clip.part


def create() -> Part:
    """One clip, in print pose: lower jaw on `z = 0`, centred over the origin."""
    part = build()
    box = part.bounding_box()
    return as_part(
        Pos(-box.center().X, -box.center().Y, -box.min.Z) * part
    )
