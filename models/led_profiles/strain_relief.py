"""Strain-relief insert: a printed stand-in for the M12 gland, when glands run out.

Screws into the same printed M12 x 1.5 female thread every cap in this family
carries (``endcap.GLAND_MAJOR_D``), so it needs nothing the caps do not already
have. Where the bought gland seals and clamps with a compression nut, this
part strain-relieves with a **cable tie**: the cable runs through a central
bore and out alongside a single solid fin standing on the head, and the tie
cinches cable and fin together in a groove around the fin's outer faces.
Pull on the cable is taken by the tie bearing on the groove's shoulders and
by the jacket's grip against the fin, not by the solder joints inside the
tube. No IP sealing -- that is the one thing of the gland's this does not
replace.

Second revision, reshaped by the first printed article:

* **The bore is cut oversize on purpose.** The first print at cable + free
  fit (7.1) came out too tight to thread the 6.7 mm cable -- the FDM
  vertical-bore undersize the fits reference documents, arriving on cue. The
  bore now adds that correction explicitly and the cable is meant to be
  loose in it; the *grip* is the tie's job.
* **One sturdy fin, not a collet.** The first article's four collet fingers
  (1.2 mm arcs on slotted hinges) snapped off in use. The fin is a solid
  3.3 x 9.2 mm buttress spanning a whole hex flat -- an order of magnitude
  more bending section, with nothing slotted to hinge on. The tie wraps the
  fin's outer three faces and presses the cable against its flat inner face.
  The fin does clock wherever the thread stops, which the collet avoided --
  but a tie-down that survives beats one that self-aligns and breaks.
* **The head seats flush, not on a taper.** The first article stood off the
  cap on its 45 deg seat cone. The flange underside is now a flat ring that
  lands flat on the cap's outer face, gland-style; the male thread band is
  placed so full engagement of the female thread happens exactly at that
  contact. What remains under the flange is a small 45 deg cone to
  ``MOUTH_CLEAR`` *inside* the cap's own bore-mouth chamfer -- it never
  touches (checked), and exists only so the flange's underside is a narrow
  printable overhang ring instead of a wide one.

The thread: printed male in printed female wants 0.50 mm total diametral
clearance (V-profile, PETG -- see the printed-thread reference). The caps'
female thread is already cut 0.30 over nominal for the metal gland, so this
male thread gives back only the remaining 0.20.

Which cap it serves: any of them mechanically, but a cable can only actually
*route* through ``endcap_wired`` -- the standard cap's own docstring is
explicit that its gland port is a fitting, not a cable route.

Print pose: stem tip down, fin up, thread axis vertical -- the only
orientation a thread prints well in. The flange's underside overhang is held
to ~1.3 mm at the flats by the clearance cone, and everything else is
vertical wall or chamfered. The bed contact is only the stem tip's ring
(~18 mm^2), so **slice it with a brim**. Hand-tighten by the hex (a 17 mm
spanner fits loosely); the flush flange needs no more.

Hardware: one standard cable tie up to 3.6 mm wide, ~1.3 mm thick (2.5 mm
ties fit too). Cable is the family's 6.7 mm LAPP round cable
(``mount_config.CABLE_OD``).
"""

from __future__ import annotations

from math import radians, tan

from bd_warehouse.thread import IsoThread
from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    Rectangle,
    RegularPolygon,
    ShapeList,
    add,
    extrude,
    fillet,
    make_face,
    revolve,
)

from models.lib import fits
from models.lib.checks import interior_angle
from models.lib.edges import chamfer_edge

from . import endcap as e
from . import mount_config as m

# ------------------------------------------------------------------ the thread

# Printed male inside printed female, ISO V profile: 0.50 mm total diametral
# clearance (printed-thread reference, PETG first attempt). The female is
# already cut e.THREAD_CLEARANCE = 0.30 over the gland's nominal, so the male
# major gives back only the remainder -- stating it this way keeps the *total*
# pinned at 0.50 even if the cap's own clearance is retuned.
MALE_CLEARANCE = 0.50
MALE_MAJOR_D = e.GLAND_THREAD_D - (MALE_CLEARANCE - e.THREAD_CLEARANCE)  # 11.80

# The root radius IsoThread will use, restated from its own min_radius formula
# (major - 2 * 5/8 * H, H the ISO fundamental triangle height) so the stem's
# core can be drawn before the thread object exists. create() asserts the two
# agree rather than trusting the copy.
_H = (e.GLAND_PITCH / 2) / tan(radians(30))
MALE_ROOT_D = MALE_MAJOR_D - 2 * (5 / 8) * _H  # 10.18

# The female thread's own crest bore, same formula on the cap's major: what
# the tip collar and thread root must pass through.
FEMALE_MINOR_D = e.GLAND_MAJOR_D - 2 * (5 / 8) * _H  # 10.68

# -------------------------------------------------------------------- the stem
#
# Print-pose z runs tip -> head: the tip enters the cap first in use. All
# lengths are derived from the cap's own thread stack so a cap change moves
# this part with it. The axial datum is the *flush seat*: flange underside on
# the cap's outer face, so stem-z below the flange IS cap-z.

# Slack between the seated tip and the relief pocket's floor plane -- the
# deepest the bore is guaranteed open in both caps (the wired cap's chamber
# floor is deeper still).
STEM_MARGIN = 0.5
STEM_L = e.POCKET_FLOOR_Z - STEM_MARGIN  # 9.5

# The thread band: at flush seat the male band must be the female's own
# [GLAND_COLLAR, GLAND_MALE_L] band, so measured from the tip it starts one
# collar up -- which is also the printed-thread rule's plain lead collar.
THREAD_L = e.GLAND_THREAD_L  # 6.5
THREAD_Z0 = STEM_L - e.GLAND_MALE_L  # 1.5

# Below the thread, the plain collar at the root diameter, chamfered at the
# tip -- thread lead-in and elephant-foot relief in one.
TIP_CHAMFER = 0.3

# --------------------------------------------------------- the flange and head

# No seat taper any more: the flange lands flat on the cap's face. Under it,
# a 45 deg cone runs from the thread's major out to MOUTH_CLEAR *short* of
# the cap's own mouth chamfer -- pure daylight, never a seat (checked). It is
# kept because the flange's underside prints as an overhang ring in this
# pose, and the cone is what holds that ring to ~1.3 mm at the flats.
MOUTH_CLEAR = 0.2
CONE_TOP_R = e.GLAND_MAJOR_D / 2 + e.GLAND_LEAD_IN - MOUTH_CLEAR  # 6.75
FLANGE_Z = STEM_L + (CONE_TOP_R - MALE_MAJOR_D / 2)  # 10.35, 45 deg cone

# Hex head: hand/spanner grip. Across corners it must clear the envelope every
# mount already reserves for the bought gland (checked, not assumed).
HEAD_AF = 16.0
HEAD_H = 4.0
HEAD_CORNER_R = 1.0  # house rule: vertical edges fillet -- cut in the sketch
HEAD_TOP = FLANGE_Z + HEAD_H  # 14.35
HEAD_CHAMFER = 0.8  # top rim, house standard
SEAT_RIM_CHAMFER = 0.3  # the flange underside's own rim

# --------------------------------------------------------------------- the bore

# The cable must thread through freely; the *grip* comes from the tie, not
# the bore. Free fit plus the FDM vertical-bore undersize (rule 4 of the fits
# reference, ~0.24 mm measured on a 0.4 mm nozzle): the first print at free
# fit alone was too tight on the 6.7 mm cable, which is that rule arriving
# in person.
BORE_UNDERSIZE = 0.4
BORE_D = m.CABLE_OD + fits.FREE + BORE_UNDERSIZE  # 7.5
BORE_MOUTH_LEAD = 0.4  # lead-in cone at the tip-end mouth
TOP_MOUTH_LEAD = 0.8  # generous lead where the cable exits past the fin

# ---------------------------------------------------------------------- the fin

# One solid buttress, replacing the first article's four snapped-off collet
# fingers. It stands on the head's top face, its outer face flush with one
# hex flat, spanning that flat's whole length -- the biggest footprint the
# head offers without overhanging it.
FIN_GAP = 0.15  # daylight between the fin's inner face and the mouth lead's rim
FIN_X0 = BORE_D / 2 + TOP_MOUTH_LEAD + FIN_GAP  # 4.70, the cable-side face
FIN_T = HEAD_AF / 2 - FIN_X0  # 3.30, out to the hex flat
FIN_W = HEAD_AF / 3**0.5  # 9.24, the hex flat's own length
FIN_H = 12.0  # above the head
FIN_TOP = HEAD_TOP + FIN_H
FIN_EMBED = 1.0  # sunk into the head so the fuse is a volume overlap
FIN_CORNER_R = 1.0  # vertical corners, filleted in the sketch
FIN_TOP_CHAMFER = 1.0

# The tie groove, around the fin's outer three faces only -- the inner face
# stays flat for the cable. Groove width takes ties up to 3.6 mm wide; depth
# is about a tie's thickness, so the tie rides flush. The fin's waist at the
# groove is FIN_T - GROOVE_DEPTH = 2.3 mm thick across its full width --
# still roughly double the section of one collet finger, per finger.
TIE_SLOT_W = 4.2  # not a fit: pocket for a <=3.6 mm cable tie + hand room
GROOVE_DEPTH = 1.0
GROOVE_Z0 = HEAD_TOP + 4.0  # floor: the shoulder the loaded tie bears on
GROOVE_Z1 = GROOVE_Z0 + TIE_SLOT_W  # ceiling: full section resumes
SHOULDER_CHAMFER = 0.3  # on both ledges' rims, leaving 0.7 of crisp shoulder


def groove_rim_edges(shape: BuildPart | Part) -> ShapeList:
    """The tie groove's ledge rims still sharp on the fin.

    The groove's floor and ceiling are horizontal ledges; their outer rims
    are the convex edges the chamfer ladder in ``create()`` breaks. Re-run
    after it, an empty answer is the assertion the ladder took. Two-pass
    selection as everywhere in this family: a cheap geometric gate (a
    horizontal edge at either ledge's height), then the interior angle
    decides -- which also keeps the chamfers' own new edges (at ~135 deg)
    from re-selecting themselves.
    """
    part = shape.part if isinstance(shape, BuildPart) else shape
    if part is None:
        return ShapeList([])
    out = []
    for edge in part.edges():  # ty: ignore[invalid-argument-type]
        bb = edge.bounding_box()
        if bb.max.Z - bb.min.Z > 0.02:
            continue
        if not (
            abs(bb.center().Z - GROOVE_Z0) < 0.02
            or abs(bb.center().Z - GROOVE_Z1) < 0.02
        ):
            continue
        angle = interior_angle(part, edge)
        if angle is not None and angle <= 120.0:
            out.append(edge)
    return ShapeList(out)


def _stem_profile() -> Polyline:
    """The stem's revolve outline: tip collar, thread core, clearance cone.

    One closed polyline on ``Plane.XZ`` (sketch (u, v) = global (x, z), so
    every constant goes in unconverted): chamfered tip ring at the thread's
    root diameter, root-diameter core under the thread band, a 45 deg flare
    up to the major above it, and the 45 deg mouth-clearance cone out to the
    flange plane -- closed back along the axis so ``revolve`` gets a face
    touching it. The flange's flat underside is *not* drawn here: it is the
    hex head's own bottom face, left where the cone stops.
    """
    root_r = MALE_ROOT_D / 2
    major_r = MALE_MAJOR_D / 2
    flare_z0 = THREAD_Z0 + THREAD_L  # core flares to major above the thread
    return Polyline(
        (0, 0),
        (root_r - TIP_CHAMFER, 0),
        (root_r, TIP_CHAMFER),
        (root_r, flare_z0),
        (major_r, flare_z0 + (major_r - root_r)),
        (major_r, STEM_L),
        (CONE_TOP_R, FLANGE_Z),
        (0, FLANGE_Z),
        close=True,
    )


def create_strain_relief() -> Part:
    """The insert, in its print pose: tip ring on z=0, fin up.

    Build discipline as the endcap's: the thread is constructed *outside* the
    builder (a BasePartObject auto-adds itself at the origin otherwise) and
    added once, last, over a collar the mouth cones never touch; the OCC
    chamfers (hex rims, groove shoulders, fin top) each run a ladder through
    ``chamfer_edge`` while their faces are as clean as they get, and checks
    read every treatment back off the solid.
    """
    thread = IsoThread(
        major_diameter=MALE_MAJOR_D,
        pitch=e.GLAND_PITCH,
        length=THREAD_L,
        external=True,
        end_finishes=("fade", "fade"),
    )
    assert abs(thread.root_radius - MALE_ROOT_D / 2) < 1e-6, (
        "MALE_ROOT_D restates IsoThread.min_radius; the two have drifted"
    )

    with BuildPart() as bp:
        # Stem: one revolve, tip chamfer and mouth-clearance cone baked into
        # the profile. PRIVATE because a plain nested sketch stays *pending*
        # on the parent builder even after revolve() consumes it explicitly,
        # and a later operation would sweep it up.
        with BuildSketch(Plane.XZ, mode=Mode.PRIVATE) as stem:
            with BuildLine():
                _stem_profile()
            make_face()
        revolve(profiles=stem.sketch.faces(), axis=Axis.Z)

        # The hex head, its flat underside the flange that seats on the cap.
        with BuildSketch(Plane.XY.offset(FLANGE_Z)) as hex_s:
            RegularPolygon(HEAD_AF / 2, 6, major_radius=False)
            fillet(hex_s.vertices(), HEAD_CORNER_R)
        extrude(amount=HEAD_H)

        # The flange underside's rim, broken while the face is clean. Small
        # on purpose: the ring inboard of it is the seat. Selected by its
        # height, not by sort order -- the tip ring at z=0 is also a bottom-
        # facing XY face, and an index pick lands there (gotchas section 9).
        underside = next(
            f
            for f in bp.faces().filter_by(Plane.XY)
            if abs(f.center().Z - FLANGE_Z) < 0.01
        )
        for size in (SEAT_RIM_CHAMFER, 0.2):
            if chamfer_edge(bp, underside.outer_wire().edges(), size):
                break

        # Top rim chamfer, also while clean -- before the fin stands on the
        # face and the bore opens through it.
        for size in (HEAD_CHAMFER, 0.5, 0.3):
            if chamfer_edge(
                bp, bp.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), size
            ):
                break

        # The fin, as three stacked extrusions: full section to the groove
        # floor, the waist across the groove, full section again to the top.
        # The bottom segment starts sunk in the head, which also re-fills the
        # top-rim chamfer under the fin's own flat so the outer face runs
        # flush from hex flank to fin tip.
        for z0, z1, inset in (
            (HEAD_TOP - FIN_EMBED, GROOVE_Z0, 0.0),
            (GROOVE_Z0, GROOVE_Z1, GROOVE_DEPTH),
            (GROOVE_Z1, FIN_TOP, 0.0),
        ):
            with BuildSketch(Plane.XY.offset(z0)) as fs:
                x1 = HEAD_AF / 2 - inset
                half_w = FIN_W / 2 - inset
                with Locations(((FIN_X0 + x1) / 2, 0)):
                    Rectangle(x1 - FIN_X0, 2 * half_w)
                fillet(fs.vertices(), FIN_CORNER_R - inset / 2)
            extrude(amount=z1 - z0)

        # The groove ledges' rims -- horizontal, so the house rule says
        # chamfer -- leaving 0.7 mm of crisp shoulder for the tie to bear on.
        for size in (SHOULDER_CHAMFER, 0.2):
            if chamfer_edge(bp, groove_rim_edges(bp), size):
                break

        # The fin's top rim.
        for size in (FIN_TOP_CHAMFER, 0.6, 0.3):
            if chamfer_edge(
                bp, bp.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), size
            ):
                break

        # Cable bore, through everything on the axis.
        with BuildSketch():
            Circle(BORE_D / 2)
        extrude(amount=HEAD_TOP, mode=Mode.SUBTRACT)

        # Lead-ins at both mouths. Boolean cones, per house style; the lower
        # one stops a full collar below the thread's first turn, the upper
        # one's rim stays FIN_GAP clear of the fin's face.
        Cone(
            bottom_radius=BORE_D / 2 + BORE_MOUTH_LEAD,
            top_radius=BORE_D / 2,
            height=BORE_MOUTH_LEAD,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        with Locations((0, 0, HEAD_TOP - TOP_MOUTH_LEAD)):
            Cone(
                bottom_radius=BORE_D / 2,
                top_radius=BORE_D / 2 + TOP_MOUTH_LEAD,
                height=TOP_MOUTH_LEAD,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # The thread, last, over its collar -- constructed outside, added once.
        with Locations((0, 0, THREAD_Z0)):
            add(thread)

    part = bp.part
    part.color = e.CAP_COLOR
    part.label = "strain relief insert"
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.strain_relief``."""
    return create_strain_relief()


__all__ = [
    "BORE_D",
    "CONE_TOP_R",
    "FEMALE_MINOR_D",
    "FIN_H",
    "FIN_T",
    "FIN_TOP",
    "FIN_W",
    "FIN_X0",
    "FLANGE_Z",
    "GROOVE_DEPTH",
    "GROOVE_Z0",
    "GROOVE_Z1",
    "HEAD_AF",
    "HEAD_TOP",
    "MALE_CLEARANCE",
    "MALE_MAJOR_D",
    "MALE_ROOT_D",
    "MOUTH_CLEAR",
    "STEM_L",
    "THREAD_L",
    "THREAD_Z0",
    "TIE_SLOT_W",
    "create",
    "create_strain_relief",
    "groove_rim_edges",
]
