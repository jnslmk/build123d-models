"""One keeper: the arch that closes the post's trough and holds the lamp in.

    uv run show led_profiles.stand.keeper

Two per stand. This is the family's ``strap`` with its two M4 bolts replaced by
two pegs, and it does the same job for the same reason: **it touches nothing.**
The trough locates the tube by shape, the keeper stops it leaving through the
mouth, and the tube keeps ``DIFFUSER_CLEAR`` of play. Nothing is clamped, and
nothing bears on either the 0.5 mm wall edges at the rim or the diffuser.

Fitting one is a single downward push: drop the lamp into the trough, drop a
keeper into each station's pair of sockets. Lifting them back out is how the
lamp comes off. No tools, no threads, and nothing to lose but the keepers
themselves.

**Why this is a key and not a snap.** The obvious version of this part is a C
that springs over the post's own outer stadium, which does have a real undercut
below its widest line -- and it would work, as an *assembly* aid. It will not
hold the lamp. The return angle that geometry offers is about 20 deg at the
lip, and against ASA's 0.7 % repeated strain that is worth roughly 30 N however
the arm is proportioned, while design-notes S3's abuse case puts
``config.keeper_pull()`` = 96 N of forward pull on the lower keeper. A snap is
an assembly aid; it is not a retention feature at this load. Two pegs in two
sockets carry the same pull as a bearing stress -- ``config.peg_bearing_stress()``
-- and that number is under 1 MPa, so the thing between the lamp and the floor
is solid material rather than a spring at 3x its rating.

**And the snap could never have been on the tube.** The assembled tube's width
climbs monotonically to its straight band and is constant across it, so no lip
hooks it from any direction that stays clear of the diffuser -- see the package
docstring and ``checks.check_stand_no_undercut``. That is design-notes S1's
conclusion, and it is why the retention lives between two printed parts here
rather than between a printed part and the extrusion.

Print pose: the arch flat on the bed, ``KEEPER_W`` tall, pegs up. The whole
part is one prismatic section extruded straight up, so there is no overhang
anywhere -- not even the crown bridge ``strap.py`` has to throw, because this
arch is extruded along the tube's axis rather than across it.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Rectangle,
    Sketch,
    SlotOverall,
    add,
    extrude,
)

from models.lib.edges import chamfer_edge

from . import config as sc
from .. import config as c

KEEPER_COLOR = Color(0.78, 0.42, 0.22)


def arch_section() -> Sketch:
    """The keeper's shape in the tube's cross-section plane.

    The arch clears the tube's whole envelope by ``KEEPER_CLEAR``; the two feet
    reach outboard to the peg circle, starting clear of the post's own flank so
    the keeper drops past it rather than onto it.
    """
    with BuildSketch() as s:
        SlotOverall(
            c.HEIGHT + 2 * sc.KEEPER_CLEAR + 2 * sc.KEEPER_T,
            c.WIDTH + 2 * sc.KEEPER_CLEAR + 2 * sc.KEEPER_T,
            rotation=90,
        )
        for side in (1.0, -1.0):
            with Locations(
                (
                    side * (sc.KEEPER_FOOT_IN + sc.KEEPER_FOOT_OUT) / 2,
                    (sc.PAD_BACK_Y + sc.KEEPER_CLIP_Y) / 2,
                )
            ):
                Rectangle(
                    sc.KEEPER_FOOT_OUT - sc.KEEPER_FOOT_IN,
                    sc.KEEPER_CLIP_Y - sc.PAD_BACK_Y,
                )
        # The bore last, so a foot can never eat into it.
        SlotOverall(
            c.HEIGHT + 2 * sc.KEEPER_CLEAR,
            c.WIDTH + 2 * sc.KEEPER_CLEAR,
            rotation=90,
            mode=Mode.SUBTRACT,
        )
        # Nothing behind the post's mouth *inboard of the feet*: the trough's
        # own walls are there. The feet themselves reach back past the mouth on
        # purpose -- they sit outboard of the flank, at the pads' height, and
        # that overlap in y is the only thing that gives them a real ligament
        # into the arch rather than a tangency at one point.
        with Locations((0.0, sc.KEEPER_CLIP_Y)):
            Rectangle(
                2 * sc.KEEPER_FOOT_IN,
                8 * c.HEIGHT,
                align=(Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
        # And nothing below the pads at all. Without this the arch's outer arc
        # runs on past the feet and tapers to a knife point where it meets them
        # -- 0 mm of wall, which no chamfer can break and no slicer can print.
        with Locations((0.0, sc.PAD_BACK_Y)):
            Rectangle(
                8 * sc.OUTER_HALF_W,
                8 * c.HEIGHT,
                align=(Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
    return s.sketch


def create_keeper() -> Part:
    """One keeper, in its print pose: arch flat on z=0, pegs up."""
    with BuildPart() as bp:
        with BuildSketch():
            add(arch_section())
        extrude(amount=sc.KEEPER_W)

        # Elephant's-foot relief on the bed face and a break on the arch's top,
        # each taken off that face's **outer wire** and taken **before the pegs
        # exist**. Both halves of that matter: the inner wires are the bore and
        # the peg roots, which must stay raw, and OCC refuses the top wire
        # outright once two 6 mm pegs stand on the face -- same call, same
        # size, same 3.0 mm shortest edge, and it fails only in their presence
        # (gotchas S1, all-or-nothing). The pegs are added after instead, which
        # costs nothing: they stand well inboard of the chamfer.
        for z in (0.0, sc.KEEPER_W):
            for face in (
                bp.faces()
                .filter_by(Axis.Z)
                .filter_by_position(Axis.Z, z - 0.01, z + 0.01)
            ):
                chamfer_edge(bp, face.outer_wire().edges(), sc.EDGE_CHAMFER)

        with Locations(
            (sc.PEG_U, sc.PEG_Y, sc.KEEPER_W),
            (-sc.PEG_U, sc.PEG_Y, sc.KEEPER_W),
        ):
            Cylinder(
                sc.PEG_D / 2,
                sc.PEG_L - sc.PEG_LEAD_IN,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        # The tip's lead-in is *added* as a truncated cone rather than cut out
        # of a full-length peg: subtracting a cone from a cylinder takes the
        # middle out and leaves the corner, which is the opposite of a lead-in.
        with Locations(
            (sc.PEG_U, sc.PEG_Y, sc.KEEPER_W + sc.PEG_L - sc.PEG_LEAD_IN),
            (-sc.PEG_U, sc.PEG_Y, sc.KEEPER_W + sc.PEG_L - sc.PEG_LEAD_IN),
        ):
            Cone(
                bottom_radius=sc.PEG_D / 2,
                top_radius=sc.PEG_D / 2 - sc.PEG_LEAD_IN,
                height=sc.PEG_LEAD_IN,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    part = bp.part
    part.label = "stand keeper"
    part.color = KEEPER_COLOR
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stand.keeper``."""
    return create_keeper()


__all__ = ["KEEPER_COLOR", "arch_section", "create", "create_keeper"]
