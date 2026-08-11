"""One tripod leg: a flat printed bar that swings about a vertical pivot.

    uv run show led_profiles.stand.leg

Three of these lie flat on the floor under the post's flange and rotate about
their M6 pivots, spreading into a tripod and nesting together for packing. The
old stand bought this part in -- 20 x 3 x 250 flat steel bar -- and printing it
instead is what takes the stand's bought-hardware list down to three bolts and
three nyloc nuts.

**Printing it costs stability, and the number is not hidden.** A steel bar that
size is 118 g; this leg is a fraction of that, and ``F_tip`` is linear in total
mass, so the printed tripod is tippier than the bought-bar one at equal reach.
Reach enters ``F_tip`` linearly too, so ``LEG_LEN`` buys some of it back, and
240 mm is what fits the smaller bed lying flat. ``checks.check_stand``
recomputes the sum from the built solids and fails below 0.5 N, so the trade is
bounded rather than assumed. design-notes S4 states it plainly: this is
studio-class kit and it gets weighted down in use.

**The load path wants a flat bar, not a beam.** The leg lies on the floor along
its whole length, so the floor carries the vertical load and the section only
has to be stiff enough not to lift and rock. That is why this is a pocketed
plate rather than the deep beam the reach might suggest: an unpocketed bar this
size is a 55 cm3 brick that prints for an hour and buys nothing.

Two features tie it to the post:

* the **pivot bore**, with a hex pocket in the underside for the nyloc, so the
  nut sits inside the leg and the leg still lies flat on the floor;
* the **stop pin** on the top face, riding in the flange's arc slot. The slot's
  two ends are the deployed and folded positions, so the tripod lands on a true
  120 deg spread every time instead of on the user's eye.

Print pose: flat on the bed, pivot bore vertical, stop pin up. Every pocket
opens on a flat face, so the only unsupported run in the part is the nut
pocket's ceiling -- 11.8 mm across under ``LEG_T - PIVOT_NUT_POCKET_H`` of
shell, which is a bridge in name only.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    RegularPolygon,
    Sketch,
    add,
    extrude,
    make_hull,
)

from models.lib.edges import chamfer_edge

from . import config as sc

LEG_COLOR = Color(0.42, 0.44, 0.48)

# Drawn along +x with the pivot at the origin, which is how ``seated_legs``
# places it: rotate about the pivot, then translate to it.
ROOT_X = -sc.LEG_HOLE_INSET
TIP_X = sc.LEG_LEN - sc.LEG_HOLE_INSET
WAIST_X = TIP_X * 0.45
FOOT_X = TIP_X - sc.LEG_FOOT_W / 2


def _hull_of(root_r: float, waist_r: float, foot_r: float) -> Sketch:
    """Hull of the leg's three defining circles, at the given radii.

    A hull rather than a drawn polygon because the **root has to be a true
    round centred on the pivot** -- anything else fouls the neighbouring leg
    part-way through the swing -- and hulling that circle into the waist and
    the foot gives tangent flanks for free, where a polygon would need fillets
    asked for by hand.
    """
    with BuildSketch(mode=Mode.PRIVATE) as seeds:
        with Locations((0.0, 0.0)):
            Circle(root_r)
        with Locations((WAIST_X, 0.0)):
            Circle(waist_r)
        with Locations((FOOT_X, 0.0)):
            Circle(foot_r)
    with BuildSketch() as s:
        add(make_hull(seeds.sketch.edges()))
    return s.sketch


def leg_outline() -> Sketch:
    """The bar's plan shape: round root, waisted shank, splayed foot."""
    return _hull_of(sc.LEG_ROOT_R, sc.LEG_WAIST / 2, sc.LEG_FOOT_W / 2)


def pocket_outline() -> Sketch:
    """The lightening pocket: the same hull, one shell thickness in, less the
    lengthwise rib and the two bosses that must stay solid."""
    with BuildSketch() as s:
        add(
            _hull_of(
                sc.LEG_ROOT_R - sc.LEG_SHELL,
                sc.LEG_WAIST / 2 - sc.LEG_SHELL,
                sc.LEG_FOOT_W / 2 - sc.LEG_SHELL,
            )
        )
        with Locations(((ROOT_X + TIP_X) / 2, 0.0)):
            Rectangle(TIP_X - ROOT_X, sc.LEG_RIB_T, mode=Mode.SUBTRACT)
        with Locations((0.0, 0.0)):
            Circle(sc.LEG_ROOT_R - 0.5, mode=Mode.SUBTRACT)
        with Locations((sc.STOP_SLOT_R, 0.0)):
            Circle(sc.STOP_PIN_D, mode=Mode.SUBTRACT)
    return s.sketch


def create_leg() -> Part:
    """One leg, in its print pose: flat on z=0, stop pin up."""
    with BuildPart() as bp:
        with BuildSketch():
            add(leg_outline())
        extrude(amount=sc.LEG_T)

        # Pocket both faces to the same depth, so the rib sits on the neutral
        # plane and the part is symmetric about it.
        with BuildSketch(Plane.XY.offset(sc.LEG_T)):
            add(pocket_outline())
        extrude(amount=-sc.LEG_POCKET_DEPTH / 2, mode=Mode.SUBTRACT)
        with BuildSketch():
            add(pocket_outline())
        extrude(amount=sc.LEG_POCKET_DEPTH / 2, mode=Mode.SUBTRACT)

        # The stop pin, riding in the flange's arc slot.
        with Locations((sc.STOP_SLOT_R, 0.0, sc.LEG_T)):
            Cylinder(
                sc.STOP_PIN_D / 2,
                sc.STOP_PIN_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # The pivot: a through bore with the nyloc pocketed into the underside.
        Cylinder(
            sc.PIVOT_CLEAR_D / 2,
            3 * sc.LEG_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        with BuildSketch():
            RegularPolygon(sc.PIVOT_NUT_POCKET_D / 2, 6)
        extrude(amount=sc.PIVOT_NUT_POCKET_H, mode=Mode.SUBTRACT)

        # House rule: hole mouths are boolean cones, never OCC edge ops.
        with Locations((0.0, 0.0, sc.LEG_T)):
            Cone(
                bottom_radius=sc.PIVOT_CLEAR_D / 2,
                top_radius=sc.PIVOT_CLEAR_D / 2 + sc.PIVOT_LEAD_IN,
                height=sc.PIVOT_LEAD_IN,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )

        # Elephant's-foot relief on the bed face, matching break on top. The
        # outline is one closed wire per face, so this is selected by height
        # alone -- the pocket rims sit inboard at a different z.
        for z in (0.0, sc.LEG_T):
            rim = bp.edges().filter_by_position(Axis.Z, z - 0.01, z + 0.01)
            chamfer_edge(
                bp,
                [e for e in rim if e.length > 4 * sc.LEG_ROOT_R],
                sc.EDGE_CHAMFER,
            )

    part = bp.part
    part.label = "stand leg"
    part.color = LEG_COLOR
    return part


def create() -> Part:
    """Entry point for ``uv run show led_profiles.stand.leg``."""
    return create_leg()


__all__ = ["LEG_COLOR", "create", "create_leg", "leg_outline", "pocket_outline"]
