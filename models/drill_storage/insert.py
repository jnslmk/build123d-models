"""The compliant half: a short TPU collar that grips, and grips only.

Set-agnostic: hand it a layout and it cuts that layout. The three sets each own a
thin module (``wood.insert``, ``metal.insert``, ``stone.insert``) that supplies
one from ``sets.py`` and nothing else -- and a set is a cartridge reprint away, so
this is the part you re-cut when the tools change.

A **collar**, not a block: it reaches exactly as far below its retention bead as
it stands above it, so the bead sits on its mid-plane and the whole part is
8.0 mm of TPU -- and that reach is itself derived from what it has to contain, so
the collar is as short as its own features allow. Everything under it is ASA,
bored at a free fit. The shell guides a drill over 23.2 mm; this grips it over 3.5.

Each bore is **plain and round -- no ribs**: TPU supplies the compliance the
ribbed PETG bores this replaced had to build out of three sprung beads. What it
does *not* supply is a way out of the friction that comes with it, so the grip is
confined to a short land at the very bottom of the collar and the rest of the
bore is relieved. ``config.LAND_FIT`` carries the full argument, including the
ease it has since been opened by.

Printed top-face-down, bores down, in TPU, no supports. Every bore is a through
hole -- drills pass clean through into the shell's guide below -- so there is
nothing to bridge and nothing to drain.

A printed cartridge is the only instrument that settles ``LAND_FIT``, and the one
printed so far said "holds, harder than wanted" -- hence ``LAND_EASE``. Judge the
next one the same way, and write the judgement into ``docs/design-notes.md``.
"""

from __future__ import annotations

from collections.abc import Sequence

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    RectangleRounded,
    RegularPolygon,
    Rotation,
    add,
    extrude,
    loft,
)

from ..lib.edges import bottom_chamfer_tool
from .box import hex_mouth_tool, rim_chamfer_tool, snap_bead_ring
from . import config as c
from .sets import DrillSet


def _hex_r(across_flats: float, fit: float) -> float:
    """Circumradius of a hex socket cut ``fit`` over ``across_flats``."""
    return (across_flats + fit) / 3**0.5


def _cut_round_bore(d: float, x: float, y: float, land_ease: float = 0.0) -> None:
    """One plain round through-bore: a short grip land, a lead-in cone, then a
    relieved guide the rest of the way up. Call inside the active BuildPart.

    ``land_ease`` opens the land beyond ``LAND_FIT`` -- the size-dependent
    small-bore compensation (``config.small_bore_comp``) when the set opts in.
    It only ever widens the land: the relief above stays put, so the packing
    footprint and every spacing check are untouched by it.
    """
    land_r = c.land_bore_r(d, land_ease)
    relief_r = (d + c.RELIEF_FIT) / 2

    with Locations((x, y, 0.0)):
        Cylinder(
            land_r,
            c.LAND_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    # Lead-in from the relief down onto the land, so a drill finds the grip
    # instead of stubbing on its top edge.
    with Locations((x, y, c.LAND_H)):
        Cone(
            land_r,
            relief_r,
            c.LAND_LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    with Locations((x, y, c.LAND_H + c.LAND_LEAD_IN)):
        Cylinder(
            relief_r,
            c.CART_H - c.LAND_H - c.LAND_LEAD_IN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    # Elephant's-foot relief where the land meets the bed.
    with Locations((x, y, 0.0)):
        Cone(
            land_r + c.BORE_FOOT_RELIEF,
            land_r,
            c.BORE_FOOT_RELIEF,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )


def hex_bore_tool(af: float, x: float, y: float) -> Part:
    """A subtractable hex socket: foot relief, land, lead-in, relief.

    The exact profile ``_cut_round_bore`` cuts, in hex. Built as a standalone
    tool and subtracted whole, rather than as a run of sketches inside the
    cartridge's builder, because ``loft`` consumes *pending* sketches -- mixing
    the two styles in one builder is how a stray sketch ends up lofted into
    something nobody asked for.
    """
    land_r = _hex_r(af, c.HEX_LAND_FIT)
    relief_r = _hex_r(af, c.RELIEF_FIT)
    relief_z = c.LAND_H + c.LAND_LEAD_IN

    # Sketches are written out rather than factored into a helper: BuildSketch
    # finds its parent BuildPart by walking the call stack, so one built inside a
    # nested function never lands in pending_faces and the loft gets no sections.
    with BuildPart() as tool:
        # Elephant's-foot relief at the bed, widening downward.
        with BuildSketch(Plane.XY):
            RegularPolygon(land_r + c.BORE_FOOT_RELIEF, 6)
        with BuildSketch(Plane.XY.offset(c.BORE_FOOT_RELIEF)):
            RegularPolygon(land_r, 6)
        loft(ruled=True)
        # The land itself.
        with BuildSketch(Plane.XY.offset(c.BORE_FOOT_RELIEF)):
            RegularPolygon(land_r, 6)
        extrude(amount=c.LAND_H - c.BORE_FOOT_RELIEF)
        # Lead-in from the relief down onto the land.
        with BuildSketch(Plane.XY.offset(c.LAND_H)):
            RegularPolygon(land_r, 6)
        with BuildSketch(Plane.XY.offset(relief_z)):
            RegularPolygon(relief_r, 6)
        loft(ruled=True)
        # Relieved guide the rest of the way up.
        with BuildSketch(Plane.XY.offset(relief_z)):
            RegularPolygon(relief_r, 6)
        extrude(amount=c.CART_H - relief_z)
    return Pos(x, y, 0) * tool.part


def key_rib() -> Part:
    """The keying rib on the +X face.

    It stands *outside* the cartridge body, so it can never collide with a bore
    however the packer lays them out, and rides in a matching slot in the shell.
    Its whole job is to make the engraved legend on the shell truthful: a rounded
    square would otherwise go in four ways and be right in one.

    Its vertical edges are rounded and its bottom is lofted back to a lead-in --
    house rule, chamfer horizontal edges and fillet vertical ones, and the bottom
    is the end that goes in first.
    """
    depth = c.KEY_D + c.KEY_ROOT  # KEY_ROOT is buried in the cartridge wall
    x_mid = c.CART_W / 2 + c.KEY_D / 2 - c.KEY_ROOT / 2
    lead = c.KEY_LEAD_IN

    # Written out rather than factored into a helper: BuildSketch finds its
    # parent BuildPart by walking the call stack, so a sketch built inside a
    # nested function never lands in pending_faces and the loft gets no sections.
    with BuildPart() as rib:
        with BuildSketch(Plane.XY):
            with Locations((x_mid, 0)):
                RectangleRounded(
                    depth - 2 * lead,
                    c.KEY_W - 2 * lead,
                    max(c.KEY_FILLET - lead, 0.2),
                )
        with BuildSketch(Plane.XY.offset(lead)):
            with Locations((x_mid, 0)):
                RectangleRounded(depth, c.KEY_W, c.KEY_FILLET)
        loft(ruled=True)
        with BuildSketch(Plane.XY.offset(lead)):
            with Locations((x_mid, 0)):
                RectangleRounded(depth, c.KEY_W, c.KEY_FILLET)
        extrude(amount=c.CART_H - lead)
    return rib.part


def create_insert(
    bores: Sequence[tuple[float, float, float]],
    hex_bores: Sequence[tuple[float, float, float]] | None = None,
    small_bore_comp: bool = False,
) -> Part:
    """The TPU cartridge: a keyed block of plain round bores, land at the bottom.

    ``bores`` are ``(diameter, x, y)`` and ``hex_bores`` ``(across_flats, x, y)``,
    both in the shell's coordinates -- pass the same tuples ``create_shell`` was
    given its legend for, or the labels lie.

    ``small_bore_comp`` opts in to ``config``'s size-dependent taper, opening
    the grip lands of bores at and under the threshold progressively. A set
    decides, not this function -- pass ``drill_set.small_bore_comp`` through.

    Returned in print pose, top face on ``z=0`` -- upside down from how it sits
    in the shell, so the grip land prints last, clear of the bed. The collar's
    own z=0 is the shell's ``CAVITY_FLOOR_Z`` (29.2), so a feature at world z
    appears here at ``CART_H - (z - CAVITY_FLOOR_Z)`` -- the bead included,
    which lands on ``CART_H - CART_BELOW_BEAD`` and is exactly halfway up.
    """
    with BuildPart() as cart:
        with BuildSketch(Plane.XY):
            RectangleRounded(c.CART_W, c.CART_W, c.CART_R)
        extrude(amount=c.CART_H)
        add(key_rib())

        # Retention bead: outward, so the compliant part carries it and seating
        # costs a squeeze rather than deflecting the ASA wall. Asymmetric ramp
        # (long lead-in below, short retention face above) for the reason in
        # box.snap_bead_ring -- a half-round bump fights the user going on.
        add(
            snap_bead_ring(
                c.CART_W,
                c.CART_R,
                c.BEAD_Z - c.CAVITY_FLOOR_Z,
                protrusion=c.CART_BEAD,
                lead_in=c.BEAD_LEAD_IN,
                back=c.BEAD_BACK,
                tip_flat=c.BEAD_TIP_FLAT,
                outward=True,
            )
        )

        # Chamfer the outer edges before the bores are cut, so both tools only
        # ever see the plain prism.
        add(
            rim_chamfer_tool(c.CART_W, c.CART_R, c.CART_H, c.SHELL_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )
        add(
            bottom_chamfer_tool(c.CART_W, c.CART_W, c.CART_R, 0.0, 0.4),
            mode=Mode.SUBTRACT,
        )

        for d, x, y in bores:
            _cut_round_bore(
                d,
                x,
                y,
                land_ease=c.small_bore_comp(d) if small_bore_comp else 0.0,
            )
        for af, x, y in hex_bores or []:
            add(hex_bore_tool(af, x, y), mode=Mode.SUBTRACT)

        # Lead-in at every mouth on the top face, cut as a boolean cone. Never an
        # OCC chamfer: a failed edge op corrupts the builder so every later one
        # fails silently (see the note in box.cut_holes).
        for d, x, y in bores:
            r = (d + c.RELIEF_FIT) / 2
            with Locations((x, y, c.CART_H - c.CART_MOUTH_CH)):
                Cone(
                    r,
                    r + c.CART_MOUTH_CH,
                    c.CART_MOUTH_CH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        # The hex mouth gets a *hex* frustum, not a cone. A round cone cut into a
        # hex hole only reaches the corners, leaving the flats barely bevelled and
        # a scalloped sharp rim between them -- which is what the sharp-edge audit
        # used to find on the PETG base next door (48 edges per base at z=27.20:
        # 8 sockets x 6 flats), until ``box.cut_holes`` was moved onto the same
        # frustum this has always used. Note what the shared tool takes: a
        # *circumradius*, where every bore here is named by its across-flats.
        for af, x, y in hex_bores or []:
            add(
                hex_mouth_tool(
                    _hex_r(af, c.RELIEF_FIT), x, y, c.CART_H, c.CART_MOUTH_CH
                ),
                mode=Mode.SUBTRACT,
            )

    # Print pose: top face down. The land is the tightest feature in the part --
    # a 1 mm land cannot afford the first layers' elephant's foot squeezing it
    # inward, so the grip end prints last on the clean upper layers and the
    # mouth lead-ins take the bed instead. Rotating about X keeps the key rib on
    # the +X face; the rounded-square body is symmetric in Y.
    part = Rotation(180, 0, 0) * cart.part
    return Pos(0, 0, -part.bounding_box().min.Z) * part


def create_insert_for(drill_set: DrillSet) -> Part:
    """The cartridge for one ``sets.DrillSet``, labelled and coloured."""
    insert = create_insert(
        drill_set.bores,
        hex_bores=drill_set.hex_bores,
        small_bore_comp=drill_set.small_bore_comp,
    )
    insert.label = f"insert_tpu_{drill_set.name}"
    insert.color = c.CART_COLOR
    return insert


__all__ = [
    "create_insert",
    "create_insert_for",
    "hex_bore_tool",
    "key_rib",
]
