"""The three tool sets, and everything that differs between them.

A set is the *only* thing a variant gets to decide. The clearances live in
``config.py`` (one land fit, one guide fit, one relief, for all three), the
geometry lives in ``base.py`` / ``insert.py`` / ``cover.py``, and the packing is
solved by ``box.layout_bores``. What is left -- which sizes, how long they are,
what the cover says, and how far a shank runs under its nominal size -- is here,
in one table you can read side by side.

    WOOD    2 - 10 mm brad-point, plus a 10 mm countersink on a hex shank
    METAL   1 - 10 mm HSS twist, plus a 4 - 20 mm step drill on a hex shank
    STONE   3 - 12 mm carbide-tipped masonry, no hex tool

Adding a fourth is a ``DrillSet`` here and a four-module package next to
``wood/``; nothing in the geometry has to know.

**One set is not packed in rows.** ``METAL`` carries a step drill whose 20 mm body
``pack_rows`` cannot place beside the tap in any ordering, so its layout is solved
by ``freepack`` instead and frozen into ``FREE_LAYOUT`` below. That is a property
of one outsized footprint, not a new default: a set gets an explicit ``layout``
only once the row packer has been shown to fail, and it meets the same walls
either way.

**Bores are cut to the shank, not to the name.** A drill goes in shank-first and
stands on the base's floor, so every millimetre of bore -- ASA guide and TPU land
alike -- only ever touches the shank. On a twist or brad-point drill the two are
the same number. On a masonry bit they are not: the carbide tip is *wider* than
the ground shank behind it, so a bore cut to the printed size would hold nothing
at all. The stone set's shanks are measured per drill and ground well below
nominal (a reduced-shank set), so each drill carries its own ``shank`` diameter
and the bore is cut to that. The legend still engraves the nominal size, because
that is what you ask a merchant for.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .box import (
    WALL_LABEL_SIZE,
    cover_height_for,
    layout_bores,
    wall_label_line_h,
)
from .freepack import LEGEND_MAX_LINES, legend_lines
from . import config as c

# Minimum gap wanted above the longest tip when picking the cover's Gridfinity
# unit. Deliberately not ``box.DRILL_HEADROOM`` (6 mm): asking for the generic
# headroom pushes a set that would just fit up a whole 7 mm unit, so every set
# here asks for a tip clearance instead and lands on the true minimum. The 7 mm
# quantisation then leaves whatever it leaves -- usually a few mm anyway.
COVER_TIP_CLEARANCE = 1.0


# How deep a hex socket runs: from the base's floor, where a shank long enough
# bottoms out, to the cartridge's top face, where a head wider than the socket
# stops. Derived, never typed -- it moves with the collar.
HEX_SOCKET_DEPTH = c.CART_TOP_Z - c.GUIDE_FLOOR_Z  # 31.2


@dataclass(frozen=True)
class HexTool:
    """A hex-shank tool sharing the tray with the drills.

    ``across_flats`` is measured on the tool itself, with no fit folded in --
    ``config``'s ``HEX_LAND_FIT`` / ``RELIEF_FIT`` / ``GUIDE_FIT`` own the
    clearances, and a hand-added tenth here would be a second, invisible one.

    ``head_d`` is a head wider than the shank that rests above the tray (a
    countersink's cone, a step drill's body); it reserves the footprint even
    though the bore is only shank-sized. 0 means the shank is the widest part of
    the tool.

    ``shank_len`` is how much of that length is hex. 0 means "all of it" -- a
    plain tap, which is shank end to end. It only matters when it is *shorter
    than the socket*: see ``seat_z``.
    """

    key: str  # what the wall legend calls it: "CSK", "STEP"
    across_flats: float
    length: float  # overall, for the assembly scene
    head_d: float = 0.0
    shank_len: float = 0.0  # 0 = the whole tool is shank

    @property
    def shank(self) -> float:
        """The hex length that actually goes into the socket."""
        return self.shank_len or self.length

    @property
    def seat_z(self) -> float:
        """World z of the shank's *lower* end once the tool is in the tray.

        Two ways a tool can stop, and which one it does is arithmetic rather than
        a choice: a shank longer than ``HEX_SOCKET_DEPTH`` **bottoms out** on the
        base's ASA floor with its head standing proud, and a shorter one **hangs**
        by its head on the cartridge's top face, shank dangling in the socket.

        The second is not a compromise. A hung tool's shank spans the collar from
        the top face down, so it engages the *whole* grip land -- where a shank
        that bottoms out only engages the land if it is long enough to reach it.
        ``checks.py`` asserts the land engagement either way, because a tool that
        cleared the land would be held by nothing at all.
        """
        return c.CART_TOP_Z - min(self.shank, HEX_SOCKET_DEPTH)

    @property
    def reach(self) -> float:
        """How far the tip stands above the base floor -- what sizes the cover.

        Not the same as ``length``: a hung tool starts higher up than a drill
        standing on the floor, so it reaches further for its size.
        """
        return self.seat_z - c.GUIDE_FLOOR_Z + self.length


@dataclass(frozen=True)
class StepDrill(HexTool):
    """A conical step drill on a hex shank: ``d_min`` to ``head_d`` in ``step``s.

    A ``HexTool`` whose "head" is the stepped cone, widest at the bottom where it
    meets the shank -- which is why ``head_d`` is the *largest* step and why the
    tray has to reserve that much footprint for a socket only 6.3 mm across.

    It exists as its own type for the assembly's benefit: drawn as a countersink
    the envelope would be upside down (a countersink is widest at the *top*), and
    the one question the scene is built to answer is whether the tool fouls its
    neighbour -- which it would do at the bottom, right where the other bits'
    bodies are.
    """

    d_min: float = 0.0  # the smallest step, at the tip
    step: float = 2.0  # the ladder's rung, for the drawing only


@dataclass(frozen=True)
class Drill:
    """One round-shank bit: the size it is sold as, how long it is, and -- for a
    set whose shanks are ground below nominal -- how wide the shank actually is.

    ``shank`` is the measured shank diameter. ``None`` means the shank is the
    nominal, or the set's uniform ``shank_allowance`` below it. The bore is cut
    to whatever the shank really is, because the drill stands on its shank; the
    legend still engraves ``nominal``.
    """

    nominal: float
    length: float
    shank: float | None = None


@dataclass(frozen=True, eq=False)
class DrillSet:
    """One tool set, with its layout solved on construction.

    ``bores`` / ``hex_bores`` / ``rows`` / ``pos`` come out of a single call to
    ``layout_bores``, and the base and the insert are both built from that one
    call -- which is what makes it impossible for the two halves to disagree
    about where a hole is, or for the engraved legend to name the wrong one.

    ``layout`` replaces the packing, not the rest of it: hand it ``{key: (x, y)}``
    and every hole goes where it says, while the bores, the sockets, the legend
    and the cover are still derived here from that one map. It exists for a set
    whose footprints ``pack_rows`` cannot lay out in rows at all -- see
    ``freepack`` and ``METAL`` -- and nothing about it is a licence to nudge a
    hole by hand: ``checks.py`` holds an explicit layout to exactly the walls and
    gaps the packer would have had to meet.
    """

    name: str  # module name: "wood"
    label: str  # cover engraving: "Wood"
    style: str  # how the assembly draws a bit: brad / twist / masonry
    drills: tuple[Drill, ...]
    hex_tools: tuple[HexTool, ...] = ()
    swap: tuple[tuple[str, str], ...] = ()
    shank_allowance: float = 0.0  # nominal - shank, diametral (see module docs)
    material: str = ""  # what the set is for, in words, for the docs
    layout: dict[str, tuple[float, float]] | None = None  # skip the row packer
    small_bore_comp: bool = False  # opt in to config.SMALL_BORE_*: open the
    #                                grip lands of bores at and under the
    #                                threshold, progressively (see the taper's
    #                                argument in config.py -- it trades grip for
    #                                insertability on the sizes that need it)

    # Solved in __post_init__ -- derived, never passed in.
    bores: tuple[tuple[float, float, float], ...] = field(init=False)
    hex_bores: tuple[tuple[float, float, float], ...] = field(init=False)
    rows: list[list[str]] = field(init=False)
    pos: dict[str, tuple[float, float]] = field(init=False)
    cover_h: float = field(init=False)
    legend_line_h: float = field(init=False)

    def cut_d(self, drill: Drill) -> float:
        """The diameter this set's bores are actually cut at for one drill.

        Two corrections, in order, and both of them are the difference between
        a number on a bit and a hole that holds it:

        * the **shank**, measured or the set's uniform allowance below nominal,
          because a drill goes in shank-first and only the shank ever touches;
        * the **small-bore shift** (``config.small_bore_comp``) when the set
          opts in, because under about 3 mm the printer closes a hole by much
          more than any fit in ``config`` is expressing.

        Every consumer takes its diameter from here -- the land, the relief, the
        ASA guide, and the packer's footprint -- so a bore cannot be compensated
        in one of them and not the others. That was the bug the second printed
        cartridge found: an eased land behind a relief too narrow to reach it.
        """
        shank = drill.shank if drill.shank is not None else drill.nominal - self.shank_allowance
        return shank + (c.small_bore_comp(shank) if self.small_bore_comp else 0.0)

    def footprint_r(self, drill: Drill) -> float:
        """What the packer has to reserve at this drill's position: its relieved
        bore, or the drill's own body when a reduced shank makes the body the
        wider thing standing above the tray. ``freepack`` solves against exactly
        this, so a re-solve and an import agree by construction.
        """
        return max(c.relieved_bore_r(self.cut_d(drill)), drill.nominal / 2)

    def __post_init__(self) -> None:
        nominal = [d.nominal for d in self.drills]
        bore_of = {d.nominal: self.cut_d(d) for d in self.drills}
        footprint_of = {d.nominal: self.footprint_r(d) for d in self.drills}

        def drill_footprint_r(nominal_d: float) -> float:
            return footprint_of[nominal_d]

        # Packed by the widest thing cut at each position: the insert's relieved
        # bore for a drill, and for a hex tool whichever is bigger, its head or
        # its own relieved socket. A hex socket's circumradius is 2/sqrt(3) of
        # its across-flats, so it is easy to under-reserve by eye.
        hex_tools = [
            (
                t.key,
                t.across_flats - self.shank_allowance,
                max(
                    t.head_d / 2,
                    (t.across_flats - self.shank_allowance + c.RELIEF_FIT) / 3**0.5,
                ),
            )
            for t in self.hex_tools
        ]
        if self.layout is None:
            bores, hex_bores, rows, pos = layout_bores(
                nominal,
                hex_tools=hex_tools,
                swap=list(self.swap),
                footprint_r=drill_footprint_r,
                half_w=c.PACK_HALF_W,
                corner_r=c.PACK_CORNER_R,
                hole_wall=c.PACK_HOLE_WALL,
                wall_clearance=c.PACK_WALL_CLEARANCE,
            )
        else:
            if self.swap:
                raise ValueError(
                    f"{self.name}: swap moves two keys the *packer* placed, so it "
                    "has nothing to do when the layout is given outright -- put "
                    "the positions where you want them in the layout instead"
                )
            pos = dict(self.layout)
            missing = {f"{d:g}" for d in nominal} | {t[0] for t in hex_tools}
            missing -= set(pos)
            if missing:
                raise KeyError(
                    f"{self.name}: layout is missing {sorted(missing)} -- an "
                    "explicit layout must place every hole, or the base and the "
                    "cartridge would be cut from different maps"
                )
            bores = [(d, pos[f"{d:g}"][0], pos[f"{d:g}"][1]) for d in nominal]
            hex_bores = [(af, pos[k][0], pos[k][1]) for k, af, _foot_r in hex_tools]
            # No rows to read the legend off, so the lines are packed instead.
            # Four, not three: a free layout puts holes at arbitrary x, and three
            # lines cannot hold twelve labels without two of them colliding.
            rows = legend_lines(
                list(pos), pos, WALL_LABEL_SIZE, max_lines=LEGEND_MAX_LINES
            )
        # Keys and the legend stay nominal; the hole is cut to the shank.
        object.__setattr__(
            self,
            "bores",
            tuple((bore_of[d], x, y) for d, x, y in bores),
        )
        object.__setattr__(self, "hex_bores", tuple(hex_bores))
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "pos", pos)
        object.__setattr__(self, "legend_line_h", wall_label_line_h(len(rows)))
        object.__setattr__(
            self,
            "cover_h",
            cover_height_for(
                self.max_len,
                headroom=COVER_TIP_CLEARANCE,
                bore_floor_z=c.GUIDE_FLOOR_Z,
                foot_top=c.SHELL_FOOT_TOP,
            ),
        )

    @property
    def max_len(self) -> float:
        """The highest tip above the base floor -- what sizes the cover.

        A drill's own length, since a drill stands on that floor. For a hex tool
        it is ``HexTool.reach``, which is longer than the tool whenever the tool
        hangs by its head instead of bottoming out.
        """
        return max([d.length for d in self.drills] + [t.reach for t in self.hex_tools])

    @property
    def nominal(self) -> list[float]:
        return [d.nominal for d in self.drills]

    def length_of(self, nominal: float) -> float:
        for d in self.drills:
            if d.nominal == nominal:
                return d.length
        raise KeyError(f"{nominal} is not in the {self.name} set")


# --- Wood ---------------------------------------------------------------------
# Eleven brad-point drills plus a countersink. The countersink is packed by its
# 10 mm head (which sits above the tray) but bored as a 6.3 mm hex socket, and
# swapped with the 10 mm drill so it lands at a row edge rather than in the
# centre slot; their footprints are within 0.2 mm, so the trade costs no wall.
#
# The 10 mm brad-point at 121 mm is the longest thing here and so picks the
# cover: 109 mm, for a 133 mm (19U) assembled envelope with ~3 mm over the tip.
WOOD = DrillSet(
    name="wood",
    label="Wood",
    style="brad",
    material="brad-point wood drills",
    drills=(
        Drill(2.0, 60.0),
        Drill(2.5, 62.0),
        Drill(3.0, 66.0),
        Drill(3.5, 70.0),
        Drill(4.0, 75.0),
        Drill(5.0, 86.0),
        Drill(6.0, 93.0),
        Drill(7.0, 100.0),
        Drill(8.0, 110.0),
        Drill(9.0, 117.0),
        Drill(10.0, 121.0),
    ),
    hex_tools=(HexTool(key="CSK", across_flats=6.3, length=48.0, head_d=10.0),),
    swap=(("CSK", "10"),),
)

# --- Metal --------------------------------------------------------------------
# Solved by ``freepack.pack_free`` and frozen here rather than re-solved on every
# import: regenerate with ``uv run python -m models.drill_storage.freepack``.
# What makes these numbers trustworthy is not the solver but ``checks.py``, which
# re-derives every wall and every gap from them.
FREE_LAYOUT: dict[str, tuple[float, float]] = {
    "3": (+12.97, +14.37),
    "5": (-2.27, +13.43),
    "2": (+14.77, +10.13),
    "10": (-10.93, +10.01),
    "TAP": (+6.25, +8.00),
    "2.5": (-3.24, +6.80),
    "1.5": (+5.32, -0.59),
    "8": (+11.93, -2.23),
    "STEP": (-6.09, -6.00),
    "4": (+13.93, -9.85),
    "6": (+7.84, -12.93),
    "1": (+2.54, -15.06),
}

# Ten HSS twist drills on DIN 338 jobber lengths, plus a 4 - 20 mm step drill.
# The 10 mm at 132 mm is the longest, which lands this set on a 116 mm cover
# (140 mm / 20U assembled) -- the middle of the three, behind stone's 137.
#
# This is the one set that is **not** packed in rows, and the step drill is why.
# A 4 - 20 mm step drill reserves a 20 mm footprint for a 6.3 mm socket, and
# ``pack_rows`` cannot place that next to the tap: a row is 32.68 mm of usable
# span and those two alone want 20 + 1.1 + 11.92 = 33.02, so the packer puts the
# step drill in a row of its own -- which then spends 20 mm of the *vertical*
# budget as well and crushes everything under it. Every ordering fails the same
# way, and dropping small drills does not help, because what does not fit is the
# tap's own 11.9 mm rather than the count.
#
# Rows are not a requirement though, only a tidy default. Freed from them, all
# twelve fit with room: ``FREE_LAYOUT`` below is packed to a 1.75 mm worst wall
# and a 1.48 mm worst gap, against the 1.50 / 1.10 they are held to -- so the
# irregular layout is not a compromise on spacing, it beats the 1.27 mm of the
# row layout it replaces on both counts.
#
# The 1 and 1.5 mm bores are the smallest holes in the package, and they are at
# the edge of what a 0.4 mm nozzle can resolve at all. This set opts into the
# small-bore shift (``config.SMALL_BORE_*``), which cuts them substantially
# *wider* than the drills they hold so that they arrive at the drill.
#
# This set is where that shift is calibrated, because it is the only one that
# reaches down this far, and it took two printed cartridges to read it. The
# first said the small bores would not accept their bits at all. The second,
# cut to a taper that assumed a constant ~0.3 mm of closure, said something far
# more useful: its 1.5 mm bore -- land modelled 1.700 -- held a *1.0 mm* drill
# snugly, while its 2.5 mm bore was very nearly right. Those two readings put
# the closure at ~0.67 mm at 1.7 mm of hole and ~0.08 mm at 2.6 mm, which is
# what moved the compensation from a taper on the land to a shift of the cut
# diameter, and from a straight-ish curve to 1/sqrt(d). See ``config``.
#
# The shift is why this layout was re-solved rather than merely re-bored: it
# widens the *relief* too, so the small bores' footprints grew by up to 0.38 mm
# of radius and the old positions no longer kept the 1 mm bore its wall.
METAL = DrillSet(
    name="metal",
    label="Metal",
    style="twist",
    material="HSS twist drills",
    small_bore_comp=True,
    drills=(
        Drill(1.0, 34.0),
        Drill(1.5, 40.0),
        Drill(2.0, 49.0),
        Drill(2.5, 57.0),
        Drill(3.0, 61.0),
        Drill(4.0, 75.0),
        Drill(5.0, 86.0),
        Drill(6.0, 93.0),
        Drill(8.0, 117.0),
        Drill(10.0, 132.0),
    ),
    # 25 mm of hex is 6.2 mm short of the 31.2 mm socket, so the step drill hangs
    # by the underside of its 20 mm step on the cartridge's top face rather than
    # bottoming out on the ASA -- see ``HexTool.seat_z``. That is the better of
    # the two: the shank then spans the grip land completely, where a 25 mm shank
    # standing on the floor would top out 1.7 mm into it.
    hex_tools=(
        HexTool(key="TAP", across_flats=10.0, length=70.0),
        StepDrill(
            key="STEP",
            across_flats=6.3,
            length=75.0,
            head_d=20.0,
            d_min=4.0,
            step=2.0,
            shank_len=25.0,
        ),
    ),
    layout=FREE_LAYOUT,
)

# --- Stone --------------------------------------------------------------------
# Eight carbide-tipped masonry bits. No hex tool: a masonry set is drills, and
# the room is better spent on the 12 mm.
#
# The shanks are measured, and they are ground below nominal -- this is a
# reduced-shank set, where every shank is ground to the next-lower R10 preferred
# number (12 -> 10, 10 -> 8, 8 -> 6.3, 6 -> 5, 5 -> 4, 4 -> 3.15). That is what
# makes the set more than a different drill list: a masonry bit's brazed carbide
# tip stands proud of the shank on every side, so a bore cut to the printed size
# would grip 0.2 mm of air. The five measured sizes (12/9.9, 10/8, 6/5.1,
# 5/4.1, 4/3.15) are the user's caliper readings; the rest (8, 7, 3) are
# extrapolated on that same rule and will be corrected when the drills are at
# hand. Bores are cut to the shank either way -- a drill stands on its shank,
# and the legend still reads the nominal size, because that is what the bit is
# sold as. The bits go in shank-first and the tip never enters the tray, so
# cutting to the shank costs nothing.
#
# The 12 mm at 150 mm is the longest, so this set gets a 137 mm cover
# (161 mm / 23U assembled) -- the tallest of the three, despite the shortest
# drill list.
STONE = DrillSet(
    name="stone",
    label="Stone",
    style="masonry",
    material="carbide-tipped masonry bits",
    drills=(
        Drill(3.0, 70.0, shank=2.5),
        Drill(4.0, 75.0, shank=3.15),
        Drill(5.0, 85.0, shank=4.1),
        Drill(6.0, 100.0, shank=5.1),
        Drill(7.0, 100.0, shank=6.3),
        Drill(8.0, 120.0, shank=6.3),
        Drill(10.0, 150.0, shank=8.0),
        Drill(12.0, 150.0, shank=9.9),
    ),
)

ALL = (WOOD, METAL, STONE)

# The roster registry: the sets the website + CI list as variants. Aliasing
# ``ALL`` keeps a single tuple of sets -- a fourth set is added there and shows
# up here (and in the variant roster) with nothing else to hand-sync.
DRILL_SETS: tuple[DrillSet, ...] = ALL


def roster_names() -> list[str]:
    """The variant module paths these sets contribute to the model roster.

    Each set is four names -- the assembled scene plus its three printed parts,
    base, insert and cover -- concatenated in registry order.
    """
    return [
        f"drill_storage.{s.name}{suffix}"
        for s in DRILL_SETS
        for suffix in ("", ".base", ".insert", ".cover")
    ]


__all__ = [
    "ALL",
    "COVER_TIP_CLEARANCE",
    "DRILL_SETS",
    "HEX_SOCKET_DEPTH",
    "METAL",
    "STONE",
    "WOOD",
    "Drill",
    "DrillSet",
    "HexTool",
    "StepDrill",
    "roster_names",
]
