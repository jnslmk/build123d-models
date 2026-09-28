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
   thick, 10.4 mm long, and forced 2.0 mm apart to get over the 20.4 mm stack:
   `eps = 3*t*y/(2*l^2) = 4.4%`, against 1.0% for PETG in repeated use and
   1.7% one-shot. They take a permanent set on assembly, and after that the
   clip is a loose collar.

So this one is a different mechanism, not a tidied-up version of that one. It
does not clamp. Its jaws are a clearance fit on the 20.4 mm stack and hold it
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

from math import atan2, cos, degrees, radians, sin

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Face,
    Part,
    Plane,
    Polyline,
    Pos,
    Rotation,
    Vector,
    Wire,
    add,
    extrude,
    make_face,
    revolve,
)

from ..lib.checks import solid_probe
from ..lib.edges import as_part, fillet_edge
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


def _radial_plane_edges(part: Part, plane: float) -> list:
    """Straight profile edges on a radial end face, independent of edge order."""
    out = []
    for edge in part.edges():  # ty: ignore[invalid-argument-type]
        pts = [v.to_tuple() for v in edge.vertices()]
        if len(pts) != 2:
            continue
        if all(abs(degrees(atan2(y, x)) - plane) < 1e-3 for x, y, _ in pts):
            out.append(edge)
    return out


def _end_break_tools(part: Part) -> list[Part]:
    """Cut 0.2 mm bevels at the exposed radial ends without OCC edge chamfers.

    Each tool is a triangular prism along a straight end-profile edge. In its
    normal section, the material side of the radial face is removed wherever
    (distance inward from the profile + distance inward from the end) < 0.2.
    The stock outside those two faces is enlarged so the boolean has no
    coincident cutting surfaces. The detent tooth's catch and the narrow arm
    root slot are *not* end faces; their square edges remain intentional.
    """
    inside = solid_probe(part)
    tools: list[Part] = []
    for plane in (-cfg.CLIP_WRAP / 2.0, cfg.CLIP_WRAP / 2.0):
        angle = radians(plane)
        radial = Vector(cos(angle), sin(angle), 0.0)
        into_end = Vector(-sin(angle), cos(angle), 0.0) * (1 if plane < 0 else -1)
        for edge in _radial_plane_edges(part, plane):
            # The short upper-jaw nose and 45-degree profile breaks are
            # already eased; beveling their sub-0.3 mm facets would erase them.
            if edge.length < 0.3:
                continue
            start, finish = (
                Vector(vertex.X, vertex.Y, vertex.Z) for vertex in edge.vertices()
            )
            along = (finish - start).normalized()
            normal = Vector(
                -along.Z * radial.X,
                -along.Z * radial.Y,
                along.X * radial.X + along.Y * radial.Y,
            )
            midpoint = (start + finish) * 0.5 + into_end * 0.3
            left = inside(midpoint + normal * 0.1)
            right = inside(midpoint - normal * 0.1)
            if left == right:
                left = inside(midpoint + normal * 0.3)
                right = inside(midpoint - normal * 0.3)
            if left == right:
                # The two long outer vertical edges have already been rounded
                # by the end fillet, so they no longer bound a sharp corner.
                if abs(along.Z) > 0.9 and edge.length > 5.0:
                    continue
                raise ValueError(f"cannot determine material side of {edge}")
            inward = normal if left else -normal
            base = start - along * 0.005
            triangle = Wire.make_polygon(
                [
                    base - inward * 0.5 - into_end * 0.5,
                    base + inward * 0.7 - into_end * 0.5,
                    base - inward * 0.5 + into_end * 0.7,
                ]
            )
            tools.append(extrude(Face(triangle), amount=edge.length + 0.01, dir=along))
    return tools


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

    # The full end profiles carry the small radial-face bevels. OCC's grouped
    # chamfers repeatedly refused the tooth and arm-root planes on native and
    # hung inside the fourth group in browser WASM. The tooth flanks must stay
    # square for the captive catch; the root slot must not widen. Bevel only
    # the two hand-facing ends with subtractive tools built from their outline.
    part = clip.part
    return as_part(part.cut(*_end_break_tools(part)))


def create() -> Part:
    """One clip, in print pose: lower jaw on `z = 0`, centred over the origin."""
    part = build()
    box = part.bounding_box()
    return as_part(Pos(-box.center().X, -box.center().Y, -box.min.Z) * part)
