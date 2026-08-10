"""Packing without rows, for the one layout that cannot have them.

``box.pack_rows`` lays holes out in tidy rows, which is the right default: it
reads well, it engraves well, and for eleven graduated drills it wastes almost
nothing. It has one hard failure mode, and ``sets.METAL`` walked into it -- a
single outsized footprint (a 4 - 20 mm step drill reserves 20 mm for a 6.3 mm
socket) takes a whole row, and then spends 20 mm of the *vertical* budget on a
row that is mostly air. Everything under it gets crushed. No ordering rescues it,
because the constraint is one item's size against the row span, not the count.

So this is the escape hatch: solve the same constraints without the row
structure. It is the identical contract -- every footprint keeps
``wall_clearance`` to the rounded-square wall and ``hole_wall`` to every other
footprint -- and only the tidiness is given up.

**The result is frozen, not solved at import.** ``main()`` prints a paste-ready
block that goes into ``sets.py`` as an explicit layout, for two reasons: a
relaxation with random restarts costs seconds and every ``uv run`` would pay it,
and a solver quietly re-deciding where every hole goes on an unrelated refactor
is exactly the kind of drift the rest of this package is built to prevent. The
frozen numbers are the layout; ``checks.py`` re-derives every wall and every gap
from them and fails if one is short, so what guarantees the layout is the check,
not this file.

    uv run python -m models.drill_storage.freepack

The method is a penalty relaxation from random starts: push every overlapping
pair apart, project any escapee back inside the wall, keep the best of N. Not
elegant and not optimal, but the objective is only feasibility-with-margin, and
the margin it reaches is reported so a bad run cannot pass silently.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

# Enough restarts and sweeps to land on the margin quoted in ``sets.METAL``, and
# a fixed seed so the same call gives the same layout on any machine.
SEED = 201
RESTARTS = 50
SWEEPS = 2200
PUSH = 0.35  # fraction of the overlap resolved per sweep, per hole

# How many lines the wall legend may stack, and how many seeds ``main`` will try
# before giving up. A layout is not usable just because the holes fit: every
# hole also needs its label on the wall, and ``legend_lines`` packs those by the
# holes' *x* alone -- so a layout that stacks four holes in one column is
# perfectly packed and unlabellable. That is not hypothetical, it is what the
# first re-solve after the small-bore shift produced. So the seed is a search,
# not a constant, and ``main`` advances it until both constraints hold.
LEGEND_MAX_LINES = 4
SEED_ATTEMPTS = 40


def sdf(px: float, py: float, half: float, corner_r: float) -> float:
    """Signed distance to the rounded-square wall, negative inside.

    The same envelope ``pack_rows`` uses, and deliberately the same expression --
    two packers disagreeing about where the wall is would be a very quiet bug.
    """
    qx = abs(px) - (half - corner_r)
    qy = abs(py) - (half - corner_r)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - corner_r


def worst_slack(
    pos: Sequence[tuple[float, float]],
    radii: Sequence[float],
    half: float,
    corner_r: float,
    hole_wall: float,
    wall_clearance: float,
) -> tuple[float, str]:
    """The tightest constraint in a layout: ``(slack, what)``, negative = violated.

    Measures the same two things ``checks.py`` measures, so a layout that passes
    here passes there.
    """
    worst, what = math.inf, "nothing"
    for i, r in enumerate(radii):
        s = -sdf(pos[i][0], pos[i][1], half, corner_r) - r - wall_clearance
        if s < worst:
            worst, what = s, f"wall/{i}"
    for i in range(len(radii)):
        for j in range(i + 1, len(radii)):
            s = math.dist(pos[i], pos[j]) - radii[i] - radii[j] - hole_wall
            if s < worst:
                worst, what = s, f"pair/{i}-{j}"
    return worst, what


def pack_free(
    items: list[tuple[str, float]],
    half_w: float,
    corner_r: float,
    hole_wall: float,
    wall_clearance: float,
    margin: float = 0.0,
    seed: int = SEED,
    restarts: int = RESTARTS,
    sweeps: int = SWEEPS,
) -> tuple[dict[str, tuple[float, float]], float]:
    """Place ``items`` -- ``(key, footprint_r)`` -- with no row structure.

    ``margin`` inflates every radius and both clearances before solving, so the
    layout is packed to a standard it does not have to meet. Solving straight at
    the requirement lands on it with nothing to spare, and a layout with zero
    slack fails the moment anything downstream is nudged.

    Returns ``({key: (x, y)}, slack)``, where ``slack`` is the margin actually
    achieved against the *unmodified* requirement. Callers should refuse a
    negative one -- it means no arrangement was found, not that a tight one was.
    """
    keys = [k for k, _r in items]
    radii = [r for _k, r in items]
    n = len(items)
    # Solve against the inflated requirement...
    solve_r = [r + margin / 2 for r in radii]
    solve_wall = wall_clearance + margin / 2
    solve_gap = hole_wall + margin
    rng = random.Random(seed)
    span = half_w - wall_clearance

    best: list[tuple[float, float]] = []
    best_slack = -math.inf
    for _ in range(restarts):
        pos = [[rng.uniform(-span, span), rng.uniform(-span, span)] for _ in range(n)]
        for _sweep in range(sweeps):
            for i in range(n):
                dx = dy = 0.0
                for j in range(n):
                    if i == j:
                        continue
                    vx = pos[i][0] - pos[j][0]
                    vy = pos[i][1] - pos[j][1]
                    d = math.hypot(vx, vy) or 1e-6
                    need = solve_r[i] + solve_r[j] + solve_gap
                    if d < need:
                        k = (need - d) / d * PUSH
                        dx += vx * k
                        dy += vy * k
                x, y = pos[i][0] + dx, pos[i][1] + dy
                # Project back inside the wall along the envelope's own gradient.
                over = -sdf(x, y, half_w, corner_r) - solve_r[i] - solve_wall
                if over < 0.0:
                    e = 1e-4
                    gx = (
                        sdf(x + e, y, half_w, corner_r)
                        - sdf(x - e, y, half_w, corner_r)
                    ) / (2 * e)
                    gy = (
                        sdf(x, y + e, half_w, corner_r)
                        - sdf(x, y - e, half_w, corner_r)
                    ) / (2 * e)
                    g = math.hypot(gx, gy) or 1e-6
                    x -= gx / g * (-over)
                    y -= gy / g * (-over)
                pos[i] = [x, y]
        # ...but score against the real one.
        placed = [(p[0], p[1]) for p in pos]
        slack, _what = worst_slack(
            placed, radii, half_w, corner_r, hole_wall, wall_clearance
        )
        if slack > best_slack:
            best_slack, best = slack, placed

    return {k: (round(p[0], 2), round(p[1], 2)) for k, p in zip(keys, best)}, best_slack


def legend_lines(
    keys: Sequence[str],
    pos: dict[str, tuple[float, float]],
    label_size: float,
    max_lines: int = 3,
    gap: float = 0.6,
) -> list[list[str]]:
    """Group labels into engraving lines that do not collide horizontally.

    ``engrave_row_legend`` puts each label at its own hole's x and stacks the
    lines it is given in z. With rows that grouping comes free -- a row's holes
    are spread along x already. Without rows two holes can share an x to within
    a tenth, so the lines have to be *packed* rather than read off the layout.

    Greedy, widest label first, into the first line where it clears its
    neighbours. The label's half-width estimate is the one ``engrave_row_legend``
    uses for the same glyphs, so the two cannot disagree about what fits.
    """

    def half_w(text: str) -> float:
        return 0.31 * label_size * len(text)

    lines: list[list[str]] = [[] for _ in range(max_lines)]
    for key in sorted(keys, key=lambda k: -half_w(k)):
        for line in lines:
            if all(
                abs(pos[key][0] - pos[other][0]) >= half_w(key) + half_w(other) + gap
                for other in line
            ):
                line.append(key)
                break
        else:
            raise ValueError(
                f"{key!r} does not fit on any of {max_lines} legend lines -- "
                "raise max_lines (and check the block still lands on the wall) "
                "or shorten a label"
            )
    # Left-to-right within a line, and drop any line the greedy pass left empty.
    return [sorted(line, key=lambda k: pos[k][0]) for line in lines if line]


def main() -> None:
    """Re-solve ``sets.METAL``'s layout and print it ready to paste."""
    from . import config as c
    from .sets import METAL

    # The set's own footprint rule, called rather than restated: the relieved
    # bore at the *cut* diameter -- shank correction and small-bore shift
    # included -- or the drill's body when a reduced shank makes the body the
    # wider thing standing above the tray. Re-deriving it here is how a solved
    # layout drifts from the one the geometry is cut to.
    items = [(f"{d.nominal:g}", METAL.footprint_r(d)) for d in METAL.drills]
    items += [
        (t.key, max(t.head_d / 2, (t.across_flats + c.RELIEF_FIT) / 3**0.5))
        for t in METAL.hex_tools
    ]
    from .box import WALL_LABEL_SIZE

    for seed in range(SEED, SEED + SEED_ATTEMPTS):
        pos, slack = pack_free(
            items,
            half_w=c.PACK_HALF_W,
            corner_r=c.PACK_CORNER_R,
            hole_wall=c.PACK_HOLE_WALL,
            wall_clearance=c.PACK_WALL_CLEARANCE,
            margin=0.25,
            seed=seed,
        )
        if slack < 0.0:
            continue
        # The second constraint, and the one no amount of packing implies: every
        # label has to land on the wall without touching its neighbour.
        try:
            lines = legend_lines(
                list(pos), pos, WALL_LABEL_SIZE, max_lines=LEGEND_MAX_LINES
            )
        except ValueError:
            continue
        break
    else:
        raise SystemExit(
            f"no layout in {SEED_ATTEMPTS} seeds both packs and labels -- the "
            "tray is genuinely full, so drop a tool or grow the envelope rather "
            "than widening the search"
        )

    print(
        f"# solved with freepack.pack_free, seed {seed}, margin "
        f"{slack:+.2f} mm over spec, {len(lines)} legend lines"
    )
    print("FREE_LAYOUT = {")
    for key, (x, y) in sorted(pos.items(), key=lambda kv: -kv[1][1]):
        print(f'    "{key}": ({x:+.2f}, {y:+.2f}),')
    print("}")


if __name__ == "__main__":
    main()


__all__ = ["legend_lines", "pack_free", "sdf", "worst_slack"]
