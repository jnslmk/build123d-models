"""Gridfinity drill storage tubes -- square-base variant of ``drill_storage``.

Same two-part telescoping idea (a bored base + a tall labelled cover that
friction-fits over it), but the round base is replaced by a **1x1 Gridfinity
foot** so the holder drops into any Gridfinity baseplate, and the cover becomes
a rounded-square tube whose flat face carries the embossed material label.

* Base  -- 42 mm Gridfinity footprint (41.5 mm pad, standard 0.7/1.8/1.9 mm
  foot profile), 42 mm tall (6U). A 41.5 mm body steps down to a 35 mm collar
  that plugs into the cover; graduated drill bores are sunk from the top face.
* Cover -- 42 mm rounded square, 123 mm tall, pillow-rounded closed top, open
  bottom that snaps over the base collar. The material name is engraved (with
  chamfered mouths) up one flat face.

The cover height is derived so the *assembled* holder (cover top above the
baseplate) is a whole number of Gridfinity Z units (147 mm = 21U) and encloses
a drill up to ``MAX_DRILL_LEN`` (132 mm) standing on the bore floor.

Printed standing (cover) / bores-up (base) in PETG, no supports. The base sits
in a Gridfinity baseplate; the cover is a free lid.
"""

import math
import sys

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Cone,
    Cylinder,
    Circle,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Pos,
    RectangleRounded,
    RegularPolygon,
    Text,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
    sweep,
)

# --- Gridfinity standard ------------------------------------------------------
GRID = 42.0
TOLERANCE = 0.5
PAD = GRID - TOLERANCE  # 41.5 mm pad top
CORNER_R = 4.0  # Gridfinity top corner radius
FOOT_C1 = 0.7  # bottom chamfer (45 deg)
FOOT_STRAIGHT = 1.8  # vertical section
FOOT_C3 = 1.9  # top chamfer (45 deg)
BASE_H = FOOT_C1 + FOOT_STRAIGHT + FOOT_C3  # 4.4 mm foot profile
HEIGHT_UNIT = 7.0  # Gridfinity Z unit

# --- Cover --------------------------------------------------------------------
# (COVER_H is derived under "Assembled height" once the base + cap are known.)
COVER_W = 42.0  # rounded-square outer (roughly flush with body)
COVER_WALL = 1.2  # thin wall (flexes for the snap)
INNER_W = COVER_W - 2 * COVER_WALL  # 39.6 mm bore -- close slip fit over collar
CAP_H = 3.0  # solid rounded cap at the top
TOP_FILLET = 4.0
CAP_FILLET = 1.5  # inner fillet where the bore ceiling meets walls
INNER_R = 2.0
LABEL_SIZE = 13.0
LABEL_Z = 45.0
LABEL_DEPTH = 0.6  # engrave depth into the flat face (< COVER_WALL, no punch-through)
LABEL_CHAMFER = 0.5  # near-full-depth bevel -> a continuous V-groove wall, no step

# --- Snap fit -----------------------------------------------------------------
# A small rounded bead runs around the inside of the cover near its opening and
# clicks into a matching groove on the base collar. Both are half-round rings so
# the cover rides on and off with a light detent.
SLIP = 0.4  # diametral slip clearance, collar in cover bore
SNAP_Z = 6.0  # height above the cover opening / collar base
SNAP_BEAD_R = 0.6  # bead radius -> protrudes 0.6 mm into the bore
SNAP_GROOVE_R = 0.8  # groove radius on the collar (a touch deeper)

# --- Base ---------------------------------------------------------------------
FOOT_TOP = 24.0  # top of the full-width body (cover seats here)
COLLAR_W = INNER_W - SLIP  # collar is a close slip fit inside the cover bore
COLLAR_R = 3.5
COLLAR_H = 18.0
BASE_TOTAL_H = FOOT_TOP + COLLAR_H  # 42 mm (6U)
COVER_SEAT_CH = 0.4  # cover bottom-edge chamfer so it seats flush on
#                                 the flat body shoulder without overhanging it
BORE_DEPTH = 36.0  # bores sunk from the top face (stops above foot)
BORE_MOUTH_CHAMFER = 0.8  # 45-deg lead-in chamfer depth at every insert-hole mouth
BASE_TOP_CHAMFER = 1.0  # 45-deg chamfer on the base's top outer rim

# --- Assembled height ---------------------------------------------------------
# A drill stands on the bore floor and rises up into the cover. Size the cover
# so the assembled envelope (cover top above the baseplate) rounds UP to a whole
# Gridfinity Z unit and still clears the longest drill plus headroom.
MAX_DRILL_LEN = 132.0  # longest drill the assembled holder must enclose
DRILL_HEADROOM = 6.0  # clear space above the drill tip under the cap
BORE_FLOOR_Z = BASE_TOTAL_H - BORE_DEPTH  # 6 mm above plate
_cover_top_min = BORE_FLOOR_Z + MAX_DRILL_LEN + DRILL_HEADROOM + CAP_H
TOTAL_ASSEMBLED_H = math.ceil(_cover_top_min / HEIGHT_UNIT) * HEIGHT_UNIT  # 147 (21U)
COVER_H = TOTAL_ASSEMBLED_H - FOOT_TOP  # 123 mm cover

# --- Ribbed bores (opt-in) ----------------------------------------------------
# A ribbed bore is cut RIB_RELIEF wider than the bit and then given RIB_COUNT
# rounded internal ribs. The bit rides on the rib tips (three line-contacts)
# instead of a full-circle wall, so FDM bore variation and layer scarring no
# longer bind the bit -- it drops in cleanly with a light, even grip. Each rib
# ramps out to nothing over RIB_TAPER and fades out just below the mouth fillet
# (RIB_TOP_GAP), so it flows into the fillet while leaving the mouth circle
# clean. The small gap past the fillet edge matters: a rib fade that lands
# exactly on the fillet's tangent circle makes a degenerate solid (OCC crash).
RIB_COUNT = 3
RIB_RELIEF = 0.45  # radial relief of the valley beyond the rib tips (also rib width)
RIB_TAPER = 4.0  # height over which each rib ramps out to nothing
RIB_TOP_GAP = BORE_MOUTH_CHAMFER + 0.4  # rib fades just below the mouth chamfer

# Bore layouts (diameter, x, y) -- graduated drill sizes on a square grid.
BORES_9 = [  # 3x3, 10 mm pitch (keeps the corner bores inside the collar)
    (3.0, -10, 10),
    (3.5, 0, 10),
    (4.0, 10, 10),
    (5.0, -10, 0),
    (6.0, 0, 0),
    (7.0, 10, 0),
    (8.0, -10, -10),
    (9.0, 0, -10),
    (9.5, 10, -10),
]
BORES_4 = [  # 2x2, 14 mm pitch, larger bits
    (12.0, -7, -7),
    (10.0, 7, -7),
    (8.0, -7, 7),
    (6.0, 7, 7),
]

BASE_COLOR = Color(0.62, 0.64, 0.67)
COVER_COLOR = Color(0.93, 0.93, 0.92)


def _gridfinity_foot() -> Part:
    """One 1x1 Gridfinity base foot; pad top lands at z=BASE_H."""
    bottom = PAD - 2 * (FOOT_C1 + FOOT_C3)
    mid = PAD - 2 * FOOT_C3
    r_bottom = CORNER_R - (FOOT_C1 + FOOT_C3)
    r_mid = CORNER_R - FOOT_C3
    with BuildPart() as foot:
        for size, radius, z in [
            (bottom, r_bottom, 0.0),
            (mid, r_mid, FOOT_C1),
            (mid, r_mid, FOOT_C1 + FOOT_STRAIGHT),
            (PAD, CORNER_R, BASE_H),
        ]:
            with BuildSketch(Plane.XY.offset(z)):
                RectangleRounded(size, size, radius)
        loft(ruled=True)
    return foot.part


def _snap_ring(size: float, corner_r: float, z: float, bead_r: float) -> Part:
    """A half-round bead ring: a circle of radius ``bead_r`` swept around a
    rounded-square perimeter of side ``size`` at height ``z``. Union it for a
    bead (protrudes inward), or subtract it for a groove."""
    with BuildSketch(Plane.XY.offset(z)) as outline:
        RectangleRounded(size, size, corner_r)
    path = outline.faces()[0].outer_wire()
    with BuildPart() as ring:
        with BuildSketch(Plane.XZ):
            with Locations((size / 2, z)):
                Circle(bead_r)
        sweep(path=path)
    return ring.part


def _rim_chamfer_tool(width: float, corner_r: float, top_z: float, ch: float) -> Part:
    """A subtract tool that 45-deg-chamfers a rounded-square top outer rim.

    Built as booleans (an oversized slab minus the beveled keep-frustum) instead
    of an OCC fillet/chamfer op, which is unreliable on this rim next to the
    perimeter holes. Subtract the returned part from the base.
    """
    with BuildPart() as tool:
        with BuildSketch(Plane.XY.offset(top_z - ch)):
            RectangleRounded(width + 4, width + 4, corner_r)
        extrude(amount=ch)
        # Beveled keep-shape: full rim at the bottom, inset by ch at the top.
        with BuildSketch(Plane.XY.offset(top_z - ch)):
            RectangleRounded(width, width, corner_r)
        with BuildSketch(Plane.XY.offset(top_z)):
            RectangleRounded(width - 2 * ch, width - 2 * ch, max(corner_r - ch, 0.2))
        loft(mode=Mode.SUBTRACT)
    return tool.part


# Fixed symmetry slots for the structured layout, outermost group first: the
# corner diagonals, the edge axes, then an inner diagonal ring, an inner axis
# ring, and finally the centre. Each entry is (angles_deg, seed_radius_fraction,
# pinned). Pinned (perimeter) holes are held at their maximum radius so every one
# sits the SAME distance from the wall -- even margins all the way round; the
# rest seed inward and relax so the interior spreads out without touching a wall.
_HOLE_SLOTS = [
    ([45, 135, 225, 315], 0.62, True),  # corners -> pinned to a uniform wall gap
    ([0, 90, 180, 270], 0.60, True),  # edges -> pinned to a uniform wall gap
    ([45, 135, 225, 315], 0.28, False),  # inner diagonal ring -> relaxed inward
    ([0, 90, 180, 270], 0.24, False),  # inner axis ring -> relaxed inward
    ([None], 0.0, False),  # centre
]


def pack_holes(
    footprints: list[tuple[str, float]],
    collar_half: float,
    corner_r: float,
    hole_wall: float,
    collar_wall: float,
    iters: int = 6000,
) -> dict[str, tuple[float, float]]:
    """Place holes in an orderly, symmetric layout; return ``{key: (x, y)}``.

    ``footprints`` is ``(key, radius)`` per hole, ``radius`` being the hole's cut
    footprint (a ribbed bore's valley radius, or the hex countersink's head
    radius). The holes are graded onto fixed symmetry slots (``_HOLE_SLOTS``) --
    largest four to the corner diagonals, next four to the edge axes, the rest to
    an inner ring / centre -- and each hole's radius *along its fixed spoke* is
    relaxed until it keeps at least ``hole_wall`` to its neighbours edge-to-edge
    and at least ``collar_wall`` to the rounded collar wall. Fixing the angles
    keeps the arrangement tidy and symmetric while the radial relaxation resolves
    spacing.

    Size ``hole_wall`` to ``2 * BORE_MOUTH_CHAMFER`` so both mouth fillets fit
    between neighbours, and ``collar_wall`` to ``BORE_MOUTH_CHAMFER +
    BASE_TOP_CHAMFER`` so a hole's mouth fillet and the top-rim fillet both fit;
    then every fillet in ``create_base`` forms. Deterministic (no RNG). Prints a
    WARNING if the collar is too crowded to reach the spacing.
    """
    order = sorted(range(len(footprints)), key=lambda i: -footprints[i][1])
    keys = [footprints[i][0] for i in order]
    r = [footprints[i][1] for i in order]
    n = len(footprints)

    theta: list[float | None] = []
    seed: list[float] = []
    pinned: list[bool] = []
    for angles, frac, pin in _HOLE_SLOTS:
        for a in angles:
            if len(theta) < n:
                theta.append(None if a is None else math.radians(a))
                seed.append(frac * collar_half)
                pinned.append(pin)

    def sdf(px: float, py: float) -> float:
        # Signed distance to the rounded-square collar wall (negative inside).
        qx = abs(px) - (collar_half - corner_r)
        qy = abs(py) - (collar_half - corner_r)
        return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - corner_r

    def max_radius(i: int) -> float:
        # Largest radius on hole i's fixed spoke that still clears the collar
        # wall by ``collar_wall`` -- i.e. an exactly ``collar_wall`` margin.
        lo, hi = 0.0, collar_half
        for _ in range(28):
            m = (lo + hi) / 2.0
            if (
                -sdf(m * math.cos(theta[i]), m * math.sin(theta[i])) - r[i]
                >= collar_wall
            ):
                lo = m
            else:
                hi = m
        return lo

    def spoke(i: int, rho: float) -> list[float]:
        return [rho * math.cos(theta[i]), rho * math.sin(theta[i])]

    # Pin perimeter holes to their max radius (uniform wall margin); seed the
    # rest inward to relax.
    pos = [
        [0.0, 0.0]
        if theta[i] is None
        else spoke(i, max_radius(i) if pinned[i] else seed[i])
        for i in range(n)
    ]

    def reproject(i: int) -> None:
        # Keep each hole on its fixed spoke: perimeter holes stay pinned at the
        # uniform wall margin; inner holes clamp to their max radius but are
        # otherwise free to relax inward.
        if theta[i] is None:
            pos[i] = [0.0, 0.0]
        elif pinned[i]:
            pos[i] = spoke(i, max_radius(i))
        else:
            pos[i] = spoke(i, min(math.hypot(pos[i][0], pos[i][1]), max_radius(i)))

    for _ in range(iters):
        moved = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                dx = pos[j][0] - pos[i][0]
                dy = pos[j][1] - pos[i][1]
                d = math.hypot(dx, dy) or 1e-9
                need = r[i] + r[j] + hole_wall
                if d < need:
                    push = (need - d) / 2.0
                    ux, uy = dx / d, dy / d
                    pos[i][0] -= ux * push
                    pos[i][1] -= uy * push
                    pos[j][0] += ux * push
                    pos[j][1] += uy * push
                    moved = max(moved, push)
        for i in range(n):
            reproject(i)
        if moved < 1e-4:
            break

    worst = min(
        (
            math.hypot(pos[j][0] - pos[i][0], pos[j][1] - pos[i][1]) - r[i] - r[j]
            for i in range(n)
            for j in range(i + 1, n)
        ),
        default=hole_wall,
    )
    if worst < hole_wall - 0.05:
        print(
            f"WARNING: hole placement only reached {worst:.2f} mm walls "
            f"(wanted {hole_wall:.2f} mm) -- the collar is too crowded; drop a "
            f"hole or shrink one.",
            file=sys.stderr,
        )
    return {keys[i]: (round(pos[i][0], 2), round(pos[i][1], 2)) for i in range(n)}


def cut_holes(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None,
    clearance: float,
    ribbed: bool,
    top_z: float,
    bore_depth: float,
    through: bool = False,
) -> None:
    """Sink drill bores + hex sockets into the active part and chamfer every mouth.

    Call this inside a ``with BuildPart()`` block; it operates on the active
    builder and is shared by the Gridfinity base and the fit tester so both get
    identical bore geometry.

    Round ``bores`` are ``(diameter, x, y)`` sunk ``bore_depth`` down from
    ``top_z``; when ``ribbed`` each gets ``RIB_COUNT`` rounded ribs (tips at the
    bit radius) that taper out just below the mouth. ``hex_bores`` are
    ``(across_flats, x, y)``. Every mouth gets a 45-deg lead-in chamfer of depth
    ``BORE_MOUTH_CHAMFER``, cut as a boolean (robust; see the note below). With
    ``through`` the bores punch out the bottom (no floor); the ribs still start
    at ``top_z - bore_depth``.
    """
    floor_z = top_z - bore_depth
    below = 1.0 if through else 0.0  # extend the cut past the bottom face
    for d, x, y in bores:
        r_tip = (d + clearance) / 2
        r_valley = r_tip + (RIB_RELIEF if ribbed else 0.0)
        with Locations((x, y, floor_z - below)):
            Cylinder(
                r_valley,
                bore_depth + 1 + below,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        if ribbed:
            # Each rib is a rounded vertical pin that ramps out to nothing near
            # the mouth (a cone cap) so it blends smoothly into the valley wall
            # and the lead-in fillet instead of ending abruptly.
            cyl_h = bore_depth - RIB_TOP_GAP - RIB_TAPER
            with Locations((x, y, floor_z)):
                with PolarLocations(r_valley, RIB_COUNT):
                    Cylinder(
                        RIB_RELIEF,
                        cyl_h,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.ADD,
                    )
                    with Locations((0, 0, cyl_h)):
                        Cone(
                            RIB_RELIEF,
                            0.0,
                            RIB_TAPER,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                            mode=Mode.ADD,
                        )

    for af, x, y in hex_bores or []:
        with BuildSketch(Plane.XY.offset(top_z)) as hex_sk:
            with Locations((x, y)):
                RegularPolygon(af / 3**0.5, 6)
        # Pass the sketch explicitly: inside a helper the implicit "pending
        # sketch" lookup that a bare extrude() relies on doesn't resolve.
        extrude(hex_sk.sketch, amount=-(bore_depth + below), mode=Mode.SUBTRACT)

    # Lead-in chamfer at every mouth, cut as a boolean 45-deg cone/frustum. We
    # deliberately avoid OCC's fillet op here: filleting a *ribbed* mouth is
    # unreliable, and a failed fillet corrupts the builder so every later fillet
    # fails too (a silent cascade). A boolean cut can't fail that way, and a
    # chamfer on a horizontal top edge is the house style anyway. The ribs fade
    # out below the chamfer zone, so it only bevels the clean valley rim.
    for d, x, y in bores:
        r = (d + clearance) / 2 + (RIB_RELIEF if ribbed else 0.0)
        with Locations((x, y, top_z - BORE_MOUTH_CHAMFER)):
            Cone(
                r,
                r + BORE_MOUTH_CHAMFER,
                BORE_MOUTH_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    for af, x, y in hex_bores or []:
        rc = af / 3**0.5  # hex circumradius
        with Locations((x, y, top_z - BORE_MOUTH_CHAMFER)):
            Cone(
                rc,
                rc + BORE_MOUTH_CHAMFER,
                BORE_MOUTH_CHAMFER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )


def create_base(
    bores: list[tuple[float, float, float]],
    hex_bores: list[tuple[float, float, float]] | None = None,
    clearance: float = 0.0,
    ribbed: bool = False,
) -> Part:
    """A Gridfinity 1x1 base: foot + body stepping to a collar, with drill bores.

    ``bores`` are round holes ``(diameter, x, y)``. ``hex_bores`` are hex
    sockets ``(across_flats, x, y)`` for hex-shank bits -- the shank drops into
    the socket and any wider head above just rests on the top face, so leave
    clearance around a hex position for the head diameter.

    ``clearance`` is a diametral allowance (mm) added to every round bore so the
    bit drops in freely. FDM prints small vertical holes 0.1-0.3 mm *under* the
    modelled size, so a bore cut at exactly the nominal diameter ends up a tight
    press fit; a modest positive clearance restores a slip fit. Hex sockets are
    unaffected -- their across-flats already carries its own fit allowance.

    ``ribbed`` cuts each round bore ``RIB_RELIEF`` wider and restores ``RIB_COUNT``
    rounded internal ribs, so the bit contacts only the rib tips. This tolerates
    print variation better than a plain wall and keeps a light, consistent grip.
    Ribbed bores need more room, so a tightly packed layout may need re-spacing.

    Every hole mouth (round *and* hex) gets a lead-in fillet of ``BORE_MOUTH_CHAMFER``.
    """
    with BuildPart() as base:
        add(_gridfinity_foot())

        # Full-width body from the pad top up to the shoulder.
        with BuildSketch(Plane.XY.offset(BASE_H)):
            RectangleRounded(PAD, PAD, CORNER_R)
        extrude(amount=FOOT_TOP - BASE_H)
        # Leave the body top a flat shoulder (no chamfer) so the cover's bottom
        # rim seats flush on it. The cover carries the matching bottom chamfer
        # (COVER_SEAT_CH) so it clears the body edge instead of overhanging it.

        # Collar that plugs into the cover.
        with BuildSketch(Plane.XY.offset(FOOT_TOP)):
            RectangleRounded(COLLAR_W, COLLAR_W, COLLAR_R)
        extrude(amount=COLLAR_H)
        # Snap groove around the collar (mates with the cover's internal bead).
        add(
            _snap_ring(COLLAR_W, COLLAR_R, FOOT_TOP + SNAP_Z, SNAP_GROOVE_R),
            mode=Mode.SUBTRACT,
        )

        # Sink the graduated drill bores + hex socket and round every mouth.
        cut_holes(bores, hex_bores, clearance, ribbed, BASE_TOTAL_H, BORE_DEPTH)

        # Chamfer the collar's top outer rim (softer top edge + a lead-in for the
        # cover) via a boolean cut -- robust, unlike the flaky fillet op.
        add(
            _rim_chamfer_tool(COLLAR_W, COLLAR_R, BASE_TOTAL_H, BASE_TOP_CHAMFER),
            mode=Mode.SUBTRACT,
        )
    return base.part


def create_cover(label: str) -> Part:
    """A tall rounded-square cover with a pillow top and an engraved label."""
    with BuildPart() as cover:
        with BuildSketch():
            RectangleRounded(COVER_W, COVER_W, CORNER_R)
        extrude(amount=COVER_H)
        # Round the top over into a pillow.
        fillet(cover.edges().group_by(Axis.Z)[-1], TOP_FILLET)
        # Chamfer the bottom outer edge so the open rim seats flush on the flat
        # base shoulder rather than overhanging the body edge (the cover is a
        # touch wider than the body). Doubles as elephant-foot relief, since the
        # cover prints open-end-down.
        chamfer(cover.edges().group_by(Axis.Z)[0], COVER_SEAT_CH)

        # Hollow: a single uniform bore (no step), open bottom to the solid cap.
        with BuildSketch():
            RectangleRounded(INNER_W, INNER_W, INNER_R)
        extrude(amount=COVER_H - CAP_H, mode=Mode.SUBTRACT)
        # Small internal fillet where the bore ceiling meets the walls: relieves
        # stress at the cap join and eases the overhang printed under the cap.
        ceiling = cover.edges().filter_by_position(
            Axis.Z, COVER_H - CAP_H, COVER_H - CAP_H
        )
        if ceiling:
            fillet(ceiling, CAP_FILLET)
        # Snap bead: a rounded ridge just inside the opening that clicks into
        # the groove on the base collar.
        add(_snap_ring(INNER_W, INNER_R, SNAP_Z, SNAP_BEAD_R))

        # Engraved label, upright and reading up the +Y flat face. The glyphs
        # are cut into the wall (durable, can't snag or shear off), shallower
        # than the wall, and their mouths chamfered so they read crisply, print
        # without a square overhang on the vertical wall, and take a paint-fill.
        text_plane = Plane(
            origin=(0, COVER_W / 2, LABEL_Z),
            x_dir=(0, 0, 1),
            z_dir=(0, 1, 0),
        )
        with BuildSketch(text_plane):
            Text(label, font_size=LABEL_SIZE)
        extrude(amount=-LABEL_DEPTH, mode=Mode.SUBTRACT)
        # Chamfer the engraved mouths: the glyph edges lying on the face, keeping
        # only the short ones so the cover's long face-boundary edges are left
        # alone. Best-effort -- the engraving stands on its own if it fails.
        mouth = (
            cover.edges()
            .filter_by_position(Axis.Y, COVER_W / 2, COVER_W / 2)
            .filter_by(lambda e: e.length < 30.0)
        )
        if mouth:
            try:
                chamfer(mouth, LABEL_CHAMFER)
            except Exception:
                pass
    return cover.part


def create() -> Compound:
    """Full set: three labelled square covers with two Gridfinity bases."""
    covers = []
    for label, x in [("Metal", -52), ("Stone", 0), ("Wood", 52)]:
        c = create_cover(label)
        c.label = f"cover_{label.lower()}"
        c.color = COVER_COLOR
        covers.append(Pos(x, 30, 0) * c)

    base9 = create_base(BORES_9)
    base9.label = "base_9_bore"
    base9.color = BASE_COLOR
    base4 = create_base(BORES_4)
    base4.label = "base_4_bore"
    base4.color = BASE_COLOR

    return Compound(
        label="drill_storage_gridfinity",
        children=[
            *covers,
            Pos(-26, -30, 0) * base9,
            Pos(26, -30, 0) * base4,
        ],
    )


def main() -> None:
    from export import display_and_export

    display_and_export(create(), "drill_storage_gridfinity")


if __name__ == "__main__":
    main()
