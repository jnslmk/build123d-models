"""The bottom disc and the hub the other two hang on.

    uv run show cable_spool.base
    uv run export cable_spool.base      # the STL to print
    uv run check cable_spool

Print pose is use pose: the disc is on the bed, the hub points up, and nothing
on the part overhangs -- the collar, the ribs, the liners and the spindle are
all vertical walls rising off a flat plate.

**The hub is a staircase, and that is what holds the stack apart.** One radius
(`HUB_RIB_R`) does two jobs at two heights:

* below `MIDDLE_Z` it is a full collar, and the middle disc lands on top of it;
* above that it survives only as `HUB_RIB_COUNT` ribs. The middle disc has four
  relief pockets on the rib centres and slides straight past them; the cover
  has none, so it stops on the rib tops at `COVER_Z`.

So a single 24 mm tube with two families of feature gives two 7 mm cable
channels and needs no fasteners, no glue and no separate spacers. The source
model does the same thing and then adds a fifth step -- a flare over a notch in
the ribs that the cover is meant to twist under. That has been dropped: as
published the cover is 2.0 mm thick and the notch is 0.9 mm tall, so the
bayonet cannot close. Here the cover rests on the rib tops and the clips hold
it down, which is what the clips are for.

**Two slots down the hub.** The one at `CABLE_SLOT_PHASE` runs the full height:
push the cable's end through it before winding and the tail is anchored at the
middle instead of flapping. The one opposite starts at `MIDDLE_Z`, and it is a
keyway -- the middle disc's two keys drop into the pair so the disc cannot turn
on the hub and saw at the cable's anchor.

**The hub is built as its own part and fused in whole.** That is not tidiness:
its vertical corners have to be filleted, and `fillet` refuses them once the
plate's six windows and two rim chamfers are in the same solid. See `_hub`.
"""

from __future__ import annotations

from math import atan2, degrees

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    Rectangle,
    Rotation,
    add,
    extrude,
    fillet,
    make_face,
    revolve,
)

from ..lib.edges import as_part, fillet_edge
from . import config as cfg
from .plate import bore_mouth_chamfers, plate_body, sector


def _hub_shell() -> Part:
    """Tube plus collar, as one revolved profile so every break is drawn in.

    Drawing the chamfers into the profile rather than chasing them with
    `chamfer()` afterwards is the whole reason this is a revolve: the finished
    hub carries two slots and four ribs, and an OCC edge op on a shape like
    that is the failure mode `build123d-geometry-ops` exists to warn about.
    """
    z0, z1 = cfg.PLATE_T, cfg.STACK_H
    c = cfg.WINDOW_CHAMFER
    with BuildPart() as hub:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (cfg.HUB_BORE_R, z0),
                    (cfg.HUB_BORE_R, z1 - c),
                    (cfg.HUB_BORE_R + c, z1),
                    (cfg.HUB_R - c, z1),
                    (cfg.HUB_R, z1 - c),
                    (cfg.HUB_R, cfg.MIDDLE_Z),
                    (cfg.HUB_COLLAR_R - c, cfg.MIDDLE_Z),
                    (cfg.HUB_COLLAR_R, cfg.MIDDLE_Z - c),
                    (cfg.HUB_COLLAR_R, z0),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return hub.part


def _liner(phase: float) -> Part:
    """The wall thickening behind one guide rib, broken at its top mouth."""
    c = cfg.WINDOW_CHAMFER
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (cfg.HUB_LINER_R, cfg.PLATE_T),
                    (cfg.HUB_BORE_R + 0.5, cfg.PLATE_T),
                    (cfg.HUB_BORE_R + 0.5, cfg.COVER_Z),
                    (cfg.HUB_LINER_R + c, cfg.COVER_Z),
                    (cfg.HUB_LINER_R, cfg.COVER_Z - c),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z, revolution_arc=cfg.HUB_RIB_ARC)
    return as_part(Rotation(0.0, 0.0, phase - cfg.HUB_RIB_ARC / 2.0) * ring.part)


def _rib(phase: float) -> Part:
    """One guide rib, extruded from a sketch whose corners are already round.

    A revolve would be the obvious tool and leaves two 9 mm square corners at
    `HUB_RIB_R` -- the ones the innermost turn of the upper channel runs over.
    They cannot be filleted afterwards: OCC refuses them at every radius, one
    at a time, on the bare hub. Rounding them in the sketch costs nothing.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(cfg.MIDDLE_Z)) as sk:
            with Locations(Rotation(0.0, 0.0, phase)):
                add(sector(cfg.HUB_R - 0.5, cfg.HUB_RIB_R, cfg.HUB_RIB_ARC))
            fillet(sk.vertices(), cfg.RIB_FILLET)
        extrude(amount=cfg.COVER_Z - cfg.MIDDLE_Z)
    return tool.part


def _slot(z0: float, phase: float) -> Part:
    """One slot down the hub, from `z0` to the top, cut from a sketch.

    A sketch rather than a revolve so the cut's own corners are filleted before
    anything is extruded.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(z0)) as sk:
            with Locations(Rotation(0.0, 0.0, phase)):
                add(
                    sector(
                        cfg.HUB_BORE_R - 1.5,
                        cfg.HUB_COLLAR_R + 1.5,
                        cfg.CABLE_SLOT_ARC,
                    )
                )
            fillet(sk.vertices(), cfg.SLOT_FILLET)
        extrude(amount=cfg.STACK_H - z0 + 0.001)
    return tool.part


def _spindle() -> Part:
    """The post up the middle, with its top edge broken."""
    c = cfg.SPINDLE_CHAMFER
    with BuildPart() as post:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (0.0, 0.0),
                    (cfg.SPINDLE_R, 0.0),
                    (cfg.SPINDLE_R, cfg.STACK_H - c),
                    (cfg.SPINDLE_R - c, cfg.STACK_H),
                    (0.0, cfg.STACK_H),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return post.part


def _spindle_bore() -> Part:
    """The 2.5 mm hole down the post, mouths broken at both ends."""
    c = cfg.SPINDLE_CHAMFER
    r0 = cfg.SPINDLE_BORE_R
    with BuildPart() as bore:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (0.0, -1.0),
                    (r0 + c, -1.0),
                    (r0 + c, 0.0),
                    (r0, c),
                    (r0, cfg.STACK_H - c),
                    (r0 + c, cfg.STACK_H),
                    (r0 + c, cfg.STACK_H + 1.0),
                    (0.0, cfg.STACK_H + 1.0),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return bore.part


def _hub_corners(part: Part) -> list:
    """The hub's remaining square corners: the two slots' flanks, and the four
    rib liners' end faces.

    Each is picked out by the feature it belongs to -- a liner end at a rib
    boundary, a slot flank crossing the bore, the tube or the collar -- rather
    than caught in a radius window. A window wide enough to reach the collar
    also catches the guide ribs' own flanks, which are *concave* where they
    meet the tube and so need nothing, and which OCC refuses at every radius:
    left in the list they contribute two dozen warning lines a build and not
    one fillet.
    """
    slots = (cfg.CABLE_SLOT_PHASE, cfg.KEY_SLOT_PHASE)
    ribs = [
        cfg.HUB_RIB_PHASE + i * 360.0 / cfg.HUB_RIB_COUNT
        for i in range(cfg.HUB_RIB_COUNT)
    ]

    def near(theta: float, centres, half: float) -> bool:
        return any(
            min(abs(theta - c) % 360.0, 360.0 - abs(theta - c) % 360.0) < half
            for c in centres
        )

    out = []
    for edge in part.edges().filter_by(Axis.Z):  # ty: ignore[invalid-argument-type]
        if edge.length <= 2.0:
            continue
        c = edge.center()
        r = (c.X**2 + c.Y**2) ** 0.5
        theta = degrees(atan2(c.Y, c.X)) % 360.0
        on_slot = near(theta, slots, cfg.CABLE_SLOT_ARC / 2.0 + 3.0)
        on_rib = near(theta, ribs, cfg.HUB_RIB_ARC / 2.0 + 3.0)
        if abs(r - cfg.HUB_LINER_R) < 0.5 and on_rib:
            out.append(edge)
        elif abs(r - cfg.HUB_BORE_R) < 0.5 and (on_rib or on_slot):
            out.append(edge)
        elif on_slot and any(
            abs(r - seat) < 0.5 for seat in (cfg.HUB_R, cfg.HUB_COLLAR_R)
        ):
            out.append(edge)
    return out


def _hub() -> Part:
    """The whole hub, filleted before it ever meets the plate.

    Every square corner the hub has left is vertical -- the four rib liners'
    end faces, and the two slots' flanks where they cross the bore, the tube
    and the collar -- and the cable's anchored tail is dragged over all of
    them, so the house rule's fillet is the right treatment rather than an
    argument for leaving them square.

    Two things about how they are cut, both measured rather than assumed:

    * **On the finished base, `fillet` refuses them at every radius down to
      0.4 mm.** On the hub alone, with the plate's six windows and two rim
      chamfers not yet in the solid, the same edges at the same radius take.
      That is the neighbourhood sensitivity `build123d-geometry-ops` describes,
      and it is the whole reason this function exists.
    * **One edge per call.** Handed the whole set at once it still refuses;
      handed each on its own, every one succeeds. So the loop re-reads the
      topology after each fillet and picks the surviving edge nearest the
      corner it is aiming at.
    """
    with BuildPart() as hub:
        add(_hub_shell())
        for i in range(cfg.HUB_RIB_COUNT):
            angle = cfg.HUB_RIB_PHASE + i * 360.0 / cfg.HUB_RIB_COUNT
            add(_rib(angle))
            # The wall is thickened on the inside over the same sector. The
            # source hub does this and it is worth copying: the cover's whole
            # weight lands on four 1 mm ledges, and a 2 mm wall backing them
            # would rather fold than carry it.
            add(_liner(angle))

        add(_slot(cfg.PLATE_T, cfg.CABLE_SLOT_PHASE), mode=Mode.SUBTRACT)
        add(_slot(cfg.MIDDLE_Z, cfg.KEY_SLOT_PHASE), mode=Mode.SUBTRACT)

        targets = [e.center() for e in _hub_corners(hub.part)]
        for target in targets:
            here = [
                e for e in _hub_corners(hub.part) if (e.center() - target).length < 0.2
            ]
            if here:
                # No size ladder: measured edge by edge on this hub, a corner
                # either takes BORE_FILLET or refuses every radius down to 0.4.
                fillet_edge(hub, here[:1], cfg.BORE_FILLET)
    return hub.part


def _bore_sketch():
    """The hole through the middle of the plate: a bore, less its rib.

    The bore is pulled back to `HUB_LINER_R` under each guide rib. That is not
    decoration: the liner behind a rib runs r 21..22, and over a plain 22 mm
    bore its whole underside would be a 1 mm ledge printed in mid-air.
    """
    step = 360.0 / cfg.HUB_RIB_COUNT
    with BuildSketch() as sk:
        Circle(cfg.HUB_BORE_R)
        with Locations(
            *[
                Rotation(0.0, 0.0, cfg.HUB_RIB_PHASE + i * step)
                for i in range(cfg.HUB_RIB_COUNT)
            ]
        ):
            add(
                sector(cfg.HUB_LINER_R, cfg.HUB_BORE_R + 0.5, cfg.HUB_RIB_ARC),
                mode=Mode.SUBTRACT,
            )
        Rectangle(2.0 * cfg.HUB_BORE_R, cfg.DIAMETRAL_RIB_W, mode=Mode.SUBTRACT)
    return sk.sketch


def create() -> Part:
    """The base plate and hub, in print pose on `z = 0`."""
    bore = _bore_sketch()
    _top, bottom = bore_mouth_chamfers(bore)

    with BuildPart() as part:
        add(plate_body(cfg.BASE_RIM_CHAMFER_W))

        with BuildSketch():
            add(bore)
        extrude(amount=cfg.PLATE_T, mode=Mode.SUBTRACT)
        # Only the bed-side mouth is broken. The other is buried under the hub,
        # and chamfering it would undercut the liner that stands on it.
        add(bottom, mode=Mode.SUBTRACT)

        add(_hub())
        add(_spindle())

        # The spindle bore, all the way through: a nail or a length of 2.5 mm
        # filament turns the whole spool while the cable is wound on. The
        # source model's is blind from the top, which cannot do that.
        add(_spindle_bore(), mode=Mode.SUBTRACT)
    return part.part
