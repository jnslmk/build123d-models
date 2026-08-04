"""The strap: the one part every mount in the family shares.

An arch that bolts down onto a cradle's two boss lands and holds the tube in.
Two per station, and it is the *only* thing in the whole family that crosses
above the rim -- so its 18 mm width is the entire optical cost of mounting a
lamp, and two screws take it off when a strip needs replacing.

**It touches nothing.** That is a correction to the original design, which had
two compliant lips gripping the aluminium flank. There is no aluminium flank to
grip: at the rim the extrusion presents only two ~0.5 mm wall edges (the channel
wall at u ~9.5-10 and the shell at u ~12.5-13), and everything above the rim is
diffuser. Pressing on either edge dents it, and pressing on the diffuser pops
it. So the strap arches clear of the whole tube by ``DIFFUSER_CLEAR`` and simply
captures it: the cradle locates the tube by shape, the strap stops it lifting
out, and the tube keeps that much vertical play. Nothing is clamped.

The feet bottom on solid boss lands with the bolt axis through the middle of
each, so the bolt is in pure compression against a stop and over-torque squashes
a pad rather than the tube: *tighten until it bottoms, plus a quarter turn*.
Where the play matters -- a lamp that travels, or one overhead -- a strip of
self-adhesive foam under the crown takes it up, which is a bought consumable
rather than geometry that could crush a 0.5 mm wall.

Print pose: feet on the bed, arch up. The arch's underside is the only overhang
and it is an offset stadium, so every face is at or above 45 deg.

Strap-local z is measured from the land, i.e. ``mount_config.CRADLE_DEPTH``
below the mount's own z.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    Sketch,
    SlotOverall,
    add,
    extrude,
)

from models.lib.edges import chamfer_edge

from . import config as c
from . import mount_config as m

# The tube's axis, seen from the land the strap bolts to.
AXIS_Z = m.TUBE_AXIS_Z - m.CRADLE_DEPTH  # -1.8
INNER_CLEAR = 2 * m.DIFFUSER_CLEAR  # diametral
CROWN_Z = AXIS_Z + (c.HEIGHT + INNER_CLEAR) / 2  # 14.7 -- inner face at the top
OUTER_Z = CROWN_Z + m.STRAP_T  # 19.7 -- overall height


def _big() -> float:
    return 4 * c.HEIGHT


def _clip_below(y: float) -> None:
    """Remove everything under ``y`` from the sketch under construction."""
    with Locations((0, y)):
        Rectangle(_big(), _big(), align=(Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)


def arch_section() -> Sketch:
    """The strap's cross-section, in the plane across the tube."""
    with BuildSketch() as s:
        # Arch: the tube's envelope plus clearance, walled by STRAP_T.
        with Locations((0, AXIS_Z)):
            SlotOverall(
                c.HEIGHT + INNER_CLEAR + 2 * m.STRAP_T,
                c.WIDTH + INNER_CLEAR + 2 * m.STRAP_T,
                rotation=90,
            )
        # Feet, out to the bolt bosses.
        with Locations((-m.BOSS_U, 0), (m.BOSS_U, 0)):
            Rectangle(m.BOSS_OD, m.FOOT_H, align=(Align.CENTER, Align.MIN))
        _clip_below(0.0)
        # The bore is a straight clearance offset of the tube -- nothing reaches
        # in to touch it. See the module docstring for why there is no lip here.
        with Locations((0, AXIS_Z)):
            SlotOverall(
                c.HEIGHT + INNER_CLEAR,
                c.WIDTH + INNER_CLEAR,
                rotation=90,
                mode=Mode.SUBTRACT,
            )
    return s.sketch


def create_strap() -> Part:
    """One strap, in its print pose: feet on z=0, arch up."""
    with BuildPart() as bp:
        # Plane.XZ's normal is -Y, so the sketch starts at +STRAP_W/2 and the
        # extrusion runs back through zero: the strap ends up centred on its
        # own origin, which is what seated() assumes.
        with BuildSketch(Plane.XZ.offset(-m.STRAP_W / 2)):
            add(arch_section())
        extrude(amount=m.STRAP_W)

        with Locations(
            (-m.BOSS_U, 0, 0),
            (m.BOSS_U, 0, 0),
        ):
            Cylinder(
                m.BOLT_CLEAR_D / 2,
                m.FOOT_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        # Lead-ins at both mouths of both bolt holes, cut as boolean cones --
        # house style, and an OCC chamfer on a thin foot is exactly the flaky case.
        for z, flip in ((0.0, Align.MIN), (m.FOOT_H, Align.MAX)):
            for u in (-m.BOSS_U, m.BOSS_U):
                with Locations((u, 0, z)):
                    Cone(
                        bottom_radius=m.BOLT_CLEAR_D / 2
                        + (m.BOLT_LEAD_IN if flip is Align.MIN else 0),
                        top_radius=m.BOLT_CLEAR_D / 2
                        + (0 if flip is Align.MIN else m.BOLT_LEAD_IN),
                        height=m.BOLT_LEAD_IN,
                        align=(Align.CENTER, Align.CENTER, flip),
                        mode=Mode.SUBTRACT,
                    )

        chamfer_edge(bp, bp.faces().sort_by(Axis.Z)[0].outer_wire().edges(), 0.5)

    part = bp.part
    part.label = "strap"
    return part


def seated(x: float = 0.0) -> Part:
    """A strap moved onto a cradle, centred on ``x`` along the tube.

    Strap-local x is across the tube and y along it; the mount has those the
    other way round, so this is a quarter turn about z. The strap is symmetric
    on both axes, so the direction of the turn does not matter.
    """
    from build123d import Pos, Rotation

    from models.lib.edges import as_part

    placed = as_part(Pos(x, 0, m.CRADLE_DEPTH) * (Rotation(0, 0, 90) * create_strap()))
    placed.label = "strap"
    return placed


def create() -> Part:
    """Entry point for ``uv run show led_profiles.strap``."""
    return create_strap()


__all__ = ["arch_section", "create", "create_strap", "seated"]
