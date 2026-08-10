"""The bottom disc and the hub the other two hang on.

    uv run show cable_spool.base
    uv run export cable_spool.base      # the STL to print
    uv run check cable_spool

Print pose is use pose: the disc is on the bed, the hub points up, and nothing
on the part overhangs -- the collar, the ribs, the liners and the spindle are
all vertical walls rising off a flat plate.

**The hub is a staircase, and that is what holds the stack apart.** One radius
(`HUB_RIB_R`) does three jobs at three heights:

* below `MIDDLE_Z` it is a full collar, and the middle disc lands on top of it;
* from there to `COVER_Z` it survives only as `HUB_RIB_COUNT` ribs. Both upper
  discs have relief pockets that slide past them -- the middle's on the rib
  centres, the cover's `COVER_TWIST` degrees round -- and the cover's *locking*
  sector lands on the rib tops;
* above `COVER_Z` it comes back as a flare over a groove, and that is the
  bayonet. See `_bayonet_relief`.

So a single 24 mm tube with three families of feature gives two 7.2 mm cable
channels, a positive twist-lock on the cover, and needs no fasteners, no glue
and no separate spacers.

**The bayonet is the source's, measured and reproduced, not invented here.**
Above each rib the hub steps in to `HUB_R` for `BAYONET_LIP_H`, cones back out
over `BAYONET_RAMP_H` and stands proud again for `BAYONET_FLARE_H`, which is
exactly `PLATE_T` of band. The cover's bore is the negative of it. Drop the
cover on with its pockets over the ribs, twist `COVER_TWIST` degrees until its
tabs butt the flares, and its lip is trapped in the groove: the rib top under
it stops it sinking and the flare over it stops it lifting. An earlier reading
of this model called that band a 0.9 mm notch and concluded the bayonet could
not close; it measures 2.01 mm against a 2.00 mm cover, and the cover's bore is
stepped rather than straight. `docs/design-notes.md` section 2 has the
arithmetic.

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
    Polygon,
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


def _liner_top_break() -> Part:
    """The 45 degree break on the liner's top inner corner, as a revolve."""
    c = cfg.WINDOW_CHAMFER
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (cfg.HUB_LINER_R - 2.0, cfg.STACK_H - c),
                    (cfg.HUB_LINER_R, cfg.STACK_H - c),
                    (cfg.HUB_LINER_R + c, cfg.STACK_H),
                    (cfg.HUB_LINER_R - 2.0, cfg.STACK_H),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return tool.part


def _liner(phase: float) -> Part:
    """The wall thickening behind one guide rib, broken at its top mouth.

    It runs the rib's whole height *and the bayonet's*: the flare above the
    groove is a 1 mm ledge that the cover hangs off, and a bare 2 mm tube
    behind it would peel rather than hold.

    Built the same way `_rib` is, as an extruded sketch whose plan corners are
    already round, and for the same measured reason: the two vertical corners a
    liner leaves in the bore are now 19 mm tall, and at that length `fillet`
    refuses three of the four on the finished hub. Drawn into the sketch they
    cost nothing. It reaches `HUB_BORE_R + 1.0` rather than the wall itself so
    that its outer face stays buried behind the tube's own top chamfer instead
    of poking through it and leaving a fresh square ring at the top of the hub.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(cfg.PLATE_T)) as sk:
            with Locations(Rotation(0.0, 0.0, phase)):
                add(sector(cfg.HUB_LINER_R, cfg.HUB_BORE_R + 1.0, cfg.HUB_RIB_ARC))
            fillet(sk.vertices(), cfg.BORE_FILLET)
        extrude(amount=cfg.STACK_H - cfg.PLATE_T)
        add(_liner_top_break(), mode=Mode.SUBTRACT)
    return tool.part


def _bayonet_relief() -> Part:
    """Everything the rib is *not* over the 2 mm the cover locks into.

    Subtracted from the rib prism, this is what leaves the groove and the cone
    above it. Written as one revolved profile, oversize on the outside so the
    boolean never meets a coincident cylinder:

        COVER_Z .. GROOVE_TOP_Z     take the rib back to `HUB_R`   -- the groove
        .. FLARE_BOTTOM_Z           give it back linearly          -- the cone
        above that                  nothing                        -- the flare
    """
    far = cfg.HUB_RIB_R + 2.0
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (cfg.HUB_R, cfg.COVER_Z),
                    (far, cfg.COVER_Z),
                    (far, cfg.FLARE_BOTTOM_Z),
                    (cfg.HUB_RIB_R, cfg.FLARE_BOTTOM_Z),
                    (cfg.HUB_R, cfg.GROOVE_TOP_Z),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return tool.part


def _flare_top_chamfer() -> Part:
    """The break on the flare's top outer edge, at the very top of the hub."""
    c = cfg.FLARE_CHAMFER
    far = cfg.HUB_RIB_R + 2.0
    with BuildPart() as tool:
        with BuildSketch(Plane.XZ) as sk:
            with BuildLine():
                Polyline(
                    (cfg.HUB_RIB_R - c, cfg.STACK_H),
                    (cfg.HUB_RIB_R, cfg.STACK_H - c),
                    (far, cfg.STACK_H - c),
                    (far, cfg.STACK_H + 1.0),
                    (cfg.HUB_RIB_R - c, cfg.STACK_H + 1.0),
                    close=True,
                )
            make_face()
        _ = sk
        revolve(axis=Axis.Z)
    return tool.part


def _rib_lead_in(phase: float) -> Part:
    """The chamfer on one rib's top trailing corner: the twist's lead-in.

    Cut as a triangular prism swept radially rather than chased with
    `chamfer()`, because the corner it breaks does not survive as a single
    edge once the groove above it is cut. `phase` is the rib's *trailing*
    edge -- the side the cover's locking sector sweeps in from.

    It reaches no further in than `HUB_R`, so it can only ever touch a rib and
    never the tube behind it.
    """
    z1 = cfg.COVER_Z
    z0 = z1 - cfg.RIB_LEAD_H
    with BuildPart() as tool:
        with BuildSketch(Plane.YZ.offset(cfg.HUB_R)) as sk:
            Polygon(
                (0.0, z1),
                (-cfg.RIB_LEAD_W, z1),
                (0.0, z0),
                align=None,
            )
        _ = sk
        extrude(amount=cfg.HUB_RIB_R + 1.0 - cfg.HUB_R)
    return as_part(Rotation(0.0, 0.0, phase) * tool.part)


def _rib(phase: float) -> Part:
    """One guide rib and the bayonet above it, as one prism worked twice.

    The prism is extruded from a sketch whose corners are already round. A
    revolve would be the obvious tool and leaves two square corners at
    `HUB_RIB_R` -- the ones the innermost turn of the upper channel runs over.
    They cannot be filleted afterwards: OCC refuses them at every radius, one
    at a time, on the bare hub. Rounding them in the sketch costs nothing, and
    it rounds the flare's corners in the same stroke.

    Then two cuts. `_bayonet_relief` carves the groove and its cone out of the
    top 2 mm, leaving the flare standing; `_rib_lead_in` breaks the rib's top
    trailing corner so the cover's underside has something to climb.
    """
    # Far enough inside the tube that the prism's own inner face stays behind
    # the tube's top chamfer. Left at `HUB_R - 0.5` it surfaces through that
    # chamfer at the top of the hub and leaves four 13 mm square rings there --
    # right where the cover sits.
    inner = cfg.HUB_R - cfg.WINDOW_CHAMFER - 0.2
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(cfg.MIDDLE_Z)) as sk:
            with Locations(Rotation(0.0, 0.0, phase)):
                add(sector(inner, cfg.HUB_RIB_R, cfg.HUB_RIB_ARC))
            fillet(sk.vertices(), cfg.RIB_FILLET)
        extrude(amount=cfg.STACK_H - cfg.MIDDLE_Z)
        add(_bayonet_relief(), mode=Mode.SUBTRACT)
        add(_flare_top_chamfer(), mode=Mode.SUBTRACT)
        add(_rib_lead_in(phase + cfg.HUB_RIB_ARC / 2.0), mode=Mode.SUBTRACT)
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
    """The hub's remaining square corners: the two slots' flanks.

    Each is picked out by the feature it belongs to -- a slot flank crossing
    the bore, the tube or the collar -- rather than caught in a radius window.
    A window wide enough to reach the collar also catches the guide ribs' own
    flanks, which are *concave* where they meet the tube and so need nothing,
    and which OCC refuses at every radius: left in the list they contribute two
    dozen warning lines a build and not one fillet.

    The rib liners' end faces used to be here too. They are drawn round in
    `_liner`'s own sketch now, which is both cheaper and, at their present
    19 mm height, the only thing that works.
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
        if abs(r - cfg.HUB_BORE_R) < 0.5 and (on_rib or on_slot):
            out.append(edge)
        elif on_slot and any(
            abs(r - seat) < 0.5 for seat in (cfg.HUB_R, cfg.HUB_COLLAR_R)
        ):
            out.append(edge)
    return out


def _hub() -> Part:
    """The whole hub, filleted before it ever meets the plate.

    Every square corner the hub has left is vertical -- the two slots' flanks
    where they cross the bore, the tube and the collar -- and the cable's
    anchored tail is dragged over all of them, so the house rule's fillet is
    the right treatment rather than an argument for leaving them square.

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
