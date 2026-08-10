"""The top disc: the lid of the outer cable channel, and half of the bayonet.

    uv run show cable_spool.cover
    uv run export cable_spool.cover      # the STL to print
    uv run check cable_spool

The same six-window disc as the other two, and everything that makes it a lid
rather than a spacer is in the bore. Read it as three angular sectors repeating
`HUB_RIB_COUNT` times, and one step through the 2 mm thickness:

* **Four locking sectors**, `COVER_LOCK_ARC` wide, on the rib centres. Here the
  bore is `COVER_LIP_R` for the bottom `BAYONET_LIP_H` -- the *lip* -- then
  cones out to `COVER_SLEEVE_R` and stays there to the top face. The lip drops
  into the hub's groove; the counterbore above it sleeves the flare.
* **Four tabs**, `COVER_TAB_ARC` wide, immediately trailing each locking
  sector. `COVER_LIP_R` over the *whole* thickness, so a tab cannot pass a
  flare at any height. That is the rotation stop: twisting the cover home walks
  each tab up against a flare and ends the motion with the locking sectors
  square on the ribs.
* **Four pockets**, `COVER_POCKET_ARC` wide, at `COVER_RELIEF_R` over the whole
  thickness. These are what the cover is dropped past the ribs on.

So the assembly motion is: align the pockets with the ribs, lower the cover the
length of the hub, twist `COVER_TWIST` degrees until it stops. The rib top
under the lip stops the cover sinking; the flare over it stops it lifting. The
clips are then belt and braces rather than the only retention.

The cover is drawn in its **locked** orientation, which is also its print pose:
lip down, chamfered rim up, no supports. Printed that way the bore's cone is an
outward step layer over layer and carries no overhang at all.

Its rim chamfer is the shallowest of the three (1 mm against the base's 3 mm),
which is the source model's proportioning and worth keeping: nothing rubs over
this edge, and a deeper chamfer would only take material out from under the
clips' upper jaws.
"""

from __future__ import annotations

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    Part,
    Plane,
    Polyline,
    Sketch,
    add,
    extrude,
    make_face,
    revolve,
)

from . import config as cfg
from .plate import mouth_chamfer, plate_body, polar, sector


def lip_sketch() -> Sketch:
    """The bore's outline at the bed face: lip radius, plus the four pockets."""
    with BuildSketch() as sk:
        Circle(cfg.COVER_LIP_R)
        with polar(cfg.HUB_RIB_COUNT, cfg.POCKET_PHASE):
            add(_pocket())
    return sk.sketch


def top_sketch() -> Sketch:
    """The bore's outline at the top face: counterbore, tabs and pockets."""
    with BuildSketch() as sk:
        Circle(cfg.COVER_SLEEVE_R)
        with polar(cfg.HUB_RIB_COUNT, cfg.TAB_PHASE):
            add(
                sector(
                    cfg.COVER_LIP_R, cfg.COVER_SLEEVE_R + 0.5, cfg.COVER_TAB_ARC
                ),
                mode=Mode.SUBTRACT,
            )
        with polar(cfg.HUB_RIB_COUNT, cfg.POCKET_PHASE):
            add(_pocket())
    return sk.sketch


def _pocket() -> Sketch:
    """One drop-on pocket, reaching in past the lip so the prism cuts cleanly."""
    return sector(cfg.COVER_LIP_R - 0.8, cfg.COVER_RELIEF_R, cfg.COVER_POCKET_ARC)


def _counterbore() -> Part:
    """Cone and counterbore: everything above the lip except behind a tab.

    Three things here are about the boolean and not about the part, and each
    one was measured rather than guessed -- with any of them undone, this cut
    does not finish in two minutes; with all three, it takes half a second.

    * **The cone is run past its own start**, down the same line to
      `COVER_LIP_R - 0.5`. Stopped exactly on the lip's wall the two surfaces
      are *tangent* along a circle instead of crossing it.
    * **The mask stops `COUNTERBORE_INSET_ARC` short of each pocket**, so its
      flank never lands on the flank the pocket cut will make. It is one
      contiguous sector per quarter turn, so the mask itself needs no union.
    * **`COVER_SLEEVE_R` is not `COVER_RELIEF_R`.** Equal, the counterbore's
      outer wall and the pockets' outer wall are the same cylinder in two
      cuts, which is the worst case of the three. They are different for a
      reason of their own anyway -- see `config.py`.
    """
    slope = cfg.BAYONET_RAMP_H / (cfg.HUB_RIB_R - cfg.HUB_R)
    z0 = cfg.BAYONET_LIP_H
    z1 = z0 + slope * (cfg.COVER_SLEEVE_R - cfg.COVER_LIP_R)
    back = 0.5
    inner = cfg.COVER_LIP_R - back - 1.0
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (inner, z0 - slope * back),
                    (cfg.COVER_LIP_R - back, z0 - slope * back),
                    (cfg.COVER_SLEEVE_R, z1),
                    (cfg.COVER_SLEEVE_R, cfg.PLATE_T + 1.0),
                    (inner, cfg.PLATE_T + 1.0),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)

        # The mask: one contiguous run from the trailing edge of each tab to
        # the leading edge of the next, less the inset at the pocket end.
        arc = 360.0 / cfg.HUB_RIB_COUNT - cfg.COVER_TAB_ARC - cfg.COUNTERBORE_INSET_ARC
        phase = (
            cfg.TAB_PHASE
            + cfg.COVER_TAB_ARC / 2.0
            + cfg.COUNTERBORE_INSET_ARC
            + arc / 2.0
        )
        with BuildSketch(Plane.XY.offset(-1.0)) as mask:
            with polar(cfg.HUB_RIB_COUNT, phase):
                add(sector(cfg.COVER_LIP_R - 3.0, cfg.COVER_SLEEVE_R + 1.0, arc))
        _ = mask
        extrude(amount=cfg.PLATE_T + 2.0, mode=Mode.INTERSECT)
    return tool.part


def create() -> Part:
    """The cover disc, in print pose -- which is also its locked pose -- on `z = 0`.

    Cut in the one order in which every cut meets solid material rather than a
    face the cut before it left: plain bore, then counterbore, then pockets.
    """
    c = cfg.BAYONET_MOUTH_CHAMFER
    with BuildPart() as part:
        add(plate_body(cfg.COVER_RIM_CHAMFER_W))

        with BuildSketch():
            Circle(cfg.COVER_LIP_R)
        extrude(amount=cfg.PLATE_T, mode=Mode.SUBTRACT)

        add(_counterbore(), mode=Mode.SUBTRACT)

        with BuildSketch():
            with polar(cfg.HUB_RIB_COUNT, cfg.POCKET_PHASE):
                add(_pocket())
        extrude(amount=cfg.PLATE_T, mode=Mode.SUBTRACT)

        # Both mouths broken, each against the outline it actually opens
        # through: the lip and its pockets below, the counterbore, tabs and
        # pockets above. A `WINDOW_CHAMFER`-sized break would be wrong here --
        # it is nearly the whole height of the lip it would be breaking.
        add(mouth_chamfer(lip_sketch(), c, 0.0), mode=Mode.SUBTRACT)
        add(
            mouth_chamfer(top_sketch(), cfg.PLATE_T - c, cfg.PLATE_T),
            mode=Mode.SUBTRACT,
        )
    return part.part
