#!/usr/bin/env python3
"""Map a mesh into feature zones along all three axes.

The tool to reach for when mesh_analyze.py reports the model is NOT a clean
extrusion. It finds the heights where the cross-section changes and classifies
each stable band between them, so you can see the model's structure -- where a
channel opens, where a taper runs, where holes start and stop -- before writing
any geometry.

It also tracks every hole up the axis it was scanned on and classifies it as a
through-hole, a blind hole, a counterbore, a countersink, or a member of a
regular hole pattern -- see "Hole feature detection" below.

Adapted from andreahaku/openscad_claude_skill (MIT). Their coarse-then-fine
approach and zone taxonomy; batch slicing and the build123d mapping are new.
Hole/counterbore/countersink/pattern detection adapts the idea from
pzfreo/build123d-mcp (reading bolt features back off built123d topology);
this version reads them off the slice stack instead, since an STL has no
topology to read.

Usage:
    uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_zones.py \
        model.stl [--out analysis/] [--coarse 5] [--fine 0.5] \
        [--feature-step 0.3] [--feature-max-slices 600]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh  # ty: ignore[unresolved-import]  # optional 'mesh' group
from shapely.geometry import Polygon  # ty: ignore[unresolved-import]  # optional 'mesh' group
from shapely.ops import unary_union  # ty: ignore[unresolved-import]  # optional 'mesh' group

sys.path.insert(0, str(Path(__file__).parent))
from mesh_analyze import AXIS_NAMES, load_mesh, slice_polygons  # noqa: E402  # ty: ignore[unresolved-import]

# What each zone shape means when you go to build it in build123d.
ZONE_RECIPES = {
    "solid": "extrude() the profile",
    "solid_with_holes": "extrude(), then subtract each hole with Mode.SUBTRACT",
    "shell_or_channel": "offset() the outer profile inward by the wall, or subtract a cavity",
    "multi_body": "separate bodies or a slot -- extrude each contour, do not hull them",
    "empty": "nothing here",
}


def classify(contours: int, holes: int) -> str:
    if contours == 0:
        return "empty"
    if contours >= 2:
        return "multi_body"
    if holes >= 1:
        return "solid_with_holes"
    return "solid"


def measure(polys) -> dict | None:
    if not polys:
        return None
    combined = unary_union(polys)
    minx, miny, maxx, maxy = combined.bounds
    return {
        "area": float(combined.area),
        "perimeter": float(combined.length),
        "contours": len(polys),
        "holes": sum(len(p.interiors) for p in polys),
        "width": float(maxx - minx),
        "depth": float(maxy - miny),
    }


# --------------------------------------------------------------------------
# Hole feature detection -- through-holes, blind holes, counterbores,
# countersinks, and regular hole patterns.
#
# A hole is a shapely *interior ring* of a slice polygon. Slicing the same
# axis at a fine, even step from face to face and tracking each interior
# ring's centre from one height to the next (nearest match, within
# CENTER_MATCH_TOL) turns each physical hole into a "thread": a
# height-ordered list of (center, radius, circularity, radius_uniformity)
# samples. The radius-vs-height curve of a thread is what tells the five
# cases apart -- constant end to end is a plain bore, constant then a
# shoulder to another constant is a counterbore, a steady drift is a
# countersink -- and grouping same-radius threads across a whole axis by the
# regularity of their centres is what finds a hole pattern. A ring that is
# not round enough in the first place (a slot, a D-flat connector cutout, a
# vent) is filtered by radius_uniformity, not by circularity -- see
# RADIUS_UNIFORMITY_MIN's comment.
#
# What each detected feature means when you go to build it in build123d.
FEATURE_RECIPES = {
    "through_hole": "Circle(r) sketched once, extrude(..., mode=Mode.SUBTRACT) clean through",
    "blind_hole": "Circle(r) subtracted for a partial depth -- a pocket, not a through-bore",
    "counterbore": "two Cylinder(r, depth) subtracts on the same centre, the wider one shallower",
    "countersink": "a Cone(...) subtract at the mouth -- a flat-head seat, or just a printed lead-in chamfer",
    "hole_pattern": "one Locations(...) (grid / PolarLocations) feeding a single hole feature, not N repeats",
}

CENTER_MATCH_TOL = (
    1.0  # mm -- centre drift budget to call two slices' rings "the same hole"
)
STEP_REL_TOL = 0.03  # relative radius change tolerated between adjacent samples before a run breaks
STEP_ABS_TOL = 0.02  # mm floor under STEP_REL_TOL, for small holes
TAPER_REL_TOL = 0.12  # a run's net (first-to-last) radius change, relative, above which it is a taper
TAPER_ABS_TOL = 0.08  # mm floor under TAPER_REL_TOL
MERGE_REL_TOL = (
    0.04  # relative radius match to re-merge two adjacent flat runs split by noise
)
MERGE_ABS_TOL = 0.03
CIRCULARITY_MIN = (
    0.8  # informational only -- see RADIUS_UNIFORMITY_MIN for the actual gate
)
# Isoperimetric circularity (4*pi*A/P**2) is a weak gate on its own: flattening
# one chord of a circle barely moves either area or perimeter, so a real
# D-flat connector cutout (Ø17 with a 15.6 mm flat, see
# models/led_psu_enclosure/penetrations.py) measures 0.987 -- comfortably
# above CIRCULARITY_MIN -- and would pass as a plain hole. Measured instead:
# the ratio of the nearest to the farthest ring vertex from its own centroid.
# A true circle sits at ~0.9996-0.9999 here (STL tessellation noise only,
# ~250 points around a bolt-sized hole); the same D-flat cutout sits at
# ~0.858, and a non-circular slot/rectangle lower still (~0.5-0.6). The gap on
# both sides of RADIUS_UNIFORMITY_MIN is large enough that the number is not
# tuned to one part -- see references/hole-features.md for the measurements.
RADIUS_UNIFORMITY_MIN = (
    0.95  # below this an interior ring is not round enough to be a bolt hole
)
PATTERN_RADIUS_TOL = (
    0.08  # relative radius match to call two holes "the same size" for a pattern
)
PATTERN_SPACING_TOL = 0.08  # relative spacing/angle match to call a layout "regular"
MIN_FLAT_SAMPLES = (
    3  # a run shorter than this is a transition being sampled, not a plateau
)


def _ring_metrics(ring_coords) -> dict | None:
    """A shapely interior ring's centre, area-equivalent radius, and two circularity measures.

    ``circularity`` (4*pi*area / perimeter**2, 1.0 for a perfect circle) is
    reported for reference but is NOT the classification gate -- it barely
    moves when one chord of a circle is flattened, which is exactly why a
    real D-flat connector cutout slips past it (see RADIUS_UNIFORMITY_MIN's
    comment). ``radius_uniformity`` -- the nearest ring vertex's distance from
    the centroid over the farthest one's -- is what actually gates "is this a
    bolt hole": a flattened chord pulls the near side in sharply while the
    untouched arc stays at the true radius, so the ratio drops hard where
    circularity barely notices.
    """
    poly = Polygon(ring_coords)
    if poly.area < 1e-6:
        return None
    perim = poly.length
    if perim <= 1e-9:
        return None
    circularity = 4.0 * np.pi * poly.area / (perim * perim)
    centroid = poly.centroid
    pts = np.asarray(ring_coords, dtype=float)
    d = np.hypot(pts[:, 0] - centroid.x, pts[:, 1] - centroid.y)
    d_max = float(d.max())
    radius_uniformity = float(d.min() / d_max) if d_max > 1e-9 else 0.0
    return {
        "center": (float(centroid.x), float(centroid.y)),
        "radius": float(np.sqrt(poly.area / np.pi)),
        "circularity": float(circularity),
        "radius_uniformity": radius_uniformity,
    }


def _slice_rings(polys: list) -> list[dict]:
    """Every hole in one slice's polygons, as ring metrics."""
    rings = []
    for p in polys:
        for interior in p.interiors:
            m = _ring_metrics(interior.coords)
            if m is not None:
                rings.append(m)
    return rings


def _link_hole_threads(
    heights: list[float], rings_per_height: list[list[dict]]
) -> list[list[tuple[float, float, float, float, float, float]]]:
    """Chain each slice's rings into threads by nearest centre, height to height.

    Each thread is one physical hole tracked up its axis: a list of
    ``(height, cx, cy, radius, circularity, radius_uniformity)`` samples. A
    thread ends the moment no ring in the next slice is within
    ``CENTER_MATCH_TOL`` -- that is exactly what a blind hole's floor looks
    like.
    """
    threads: list[list[tuple[float, float, float, float, float, float]]] = []
    open_ends: list[tuple[int, float, float]] = []
    for h, rings in zip(heights, rings_per_height):
        available = list(range(len(rings)))
        new_open: list[tuple[int, float, float]] = []
        for idx, cx, cy in open_ends:
            best_j, best_d = None, None
            for j in available:
                d = math.hypot(rings[j]["center"][0] - cx, rings[j]["center"][1] - cy)
                if best_d is None or d < best_d:
                    best_j, best_d = j, d
            if best_j is not None and best_d is not None and best_d <= CENTER_MATCH_TOL:
                available.remove(best_j)
                r = rings[best_j]
                threads[idx].append(
                    (
                        h,
                        r["center"][0],
                        r["center"][1],
                        r["radius"],
                        r["circularity"],
                        r["radius_uniformity"],
                    )
                )
                new_open.append((idx, r["center"][0], r["center"][1]))
        for j in available:
            r = rings[j]
            threads.append(
                [
                    (
                        h,
                        r["center"][0],
                        r["center"][1],
                        r["radius"],
                        r["circularity"],
                        r["radius_uniformity"],
                    )
                ]
            )
            new_open.append((len(threads) - 1, r["center"][0], r["center"][1]))
        open_ends = new_open
    return threads


def _radius_runs(
    thread: list[tuple[float, float, float, float, float, float]],
) -> list[dict]:
    """Collapse a thread's samples into piecewise radius runs, each "flat" or "taper".

    A run continues as long as each new sample stays within
    ``STEP_REL_TOL``/``STEP_ABS_TOL`` of the *previous* sample -- not the run's
    running mean, so a slow drift does not get absorbed into an ever-widening
    "flat" run. Once a run closes, its own net change (last sample vs first)
    decides what it was: small net change over however many samples is a
    plateau (``flat`` -- a plain bore or a counterbore's shoulder), a large net
    change is a ``taper`` (a countersink or a printed lead-in cone).
    """
    raw: list[dict] = []
    for h, cx, cy, r, circ, _runif in thread:
        if raw:
            prev = raw[-1]
            step_tol = max(STEP_REL_TOL * prev["_last_r"], STEP_ABS_TOL)
            if abs(r - prev["_last_r"]) <= step_tol:
                prev["to"] = h
                prev["_last_r"] = r
                prev["_rs"].append(r)
                prev["_cs"].append(circ)
                prev["_cxs"].append(cx)
                prev["_cys"].append(cy)
                continue
        raw.append(
            {
                "from": h,
                "to": h,
                "_last_r": r,
                "_rs": [r],
                "_cs": [circ],
                "_cxs": [cx],
                "_cys": [cy],
            }
        )

    runs = []
    for r in raw:
        radius = float(np.mean(r["_rs"]))
        net_change = abs(r["_rs"][-1] - r["_rs"][0])
        taper_tol = max(TAPER_REL_TOL * radius, TAPER_ABS_TOL)
        # A run earns "flat" only by being BOTH long enough and internally
        # stable. A run too short to judge (fewer than MIN_FLAT_SAMPLES,
        # typically 1-2 samples that landed inside a sub-millimetre lead-in
        # cone at --feature-step's resolution) is treated as part of a
        # transition instead -- see the taper-merge pass below, which is what
        # turns a run of these into one reported taper rather than several
        # spurious "plateaus".
        kind = (
            "flat"
            if len(r["_rs"]) >= MIN_FLAT_SAMPLES and net_change <= taper_tol
            else "taper"
        )
        runs.append(
            {
                "from": r["from"],
                "to": r["to"],
                "radius": radius,
                "circularity": float(np.mean(r["_cs"])),
                "cx": float(np.mean(r["_cxs"])),
                "cy": float(np.mean(r["_cys"])),
                "kind": kind,
            }
        )

    # Re-merge adjacent flat runs of near-equal radius: STEP_REL_TOL can split
    # a genuine plateau in two if one sample's radius wobbles past it and back.
    merged: list[dict] = []
    for r in runs:
        if merged and merged[-1]["kind"] == "flat" and r["kind"] == "flat":
            prev = merged[-1]
            if abs(r["radius"] - prev["radius"]) <= max(
                MERGE_REL_TOL * prev["radius"], MERGE_ABS_TOL
            ):
                prev["to"] = r["to"]
                prev["radius"] = (prev["radius"] + r["radius"]) / 2
                prev["circularity"] = (prev["circularity"] + r["circularity"]) / 2
                prev["cx"] = (prev["cx"] + r["cx"]) / 2
                prev["cy"] = (prev["cy"] + r["cy"]) / 2
                continue
        merged.append(dict(r))

    # Collapse consecutive taper runs into one bridging taper: a lead-in cone
    # sampled at only 1-2 points per side of its own centre otherwise shows up
    # as several adjacent short "taper" runs instead of the one transition
    # they actually are.
    bridged: list[dict] = []
    for r in merged:
        if bridged and bridged[-1]["kind"] == "taper" and r["kind"] == "taper":
            prev = bridged[-1]
            prev["to"] = r["to"]
            prev["radius"] = r[
                "radius"
            ]  # the far end's radius is what matters for a taper
            prev["circularity"] = (prev["circularity"] + r["circularity"]) / 2
            prev["cx"] = (prev["cx"] + r["cx"]) / 2
            prev["cy"] = (prev["cy"] + r["cy"]) / 2
            continue
        bridged.append(dict(r))
    return bridged


def _classify_thread(
    thread: list[tuple[float, float, float, float, float, float]],
    lo: float,
    hi: float,
    end_tol: float,
) -> dict:
    """One thread -> one feature dict: kind, centre, size, extent, and the runs behind it."""
    thread = sorted(thread, key=lambda t: t[0])
    h0, h1 = thread[0][0], thread[-1][0]
    mean_circ = float(np.mean([t[4] for t in thread]))
    mean_runif = float(np.mean([t[5] for t in thread]))
    runs = _radius_runs(thread)
    flat = [r for r in runs if r["kind"] == "flat"]
    taper = [r for r in runs if r["kind"] == "taper"]

    reaches_lo = (h0 - lo) <= end_tol
    reaches_hi = (hi - h1) <= end_tol
    # The actual "is this round enough to be a bolt hole" gate. NOT
    # `circularity` -- see RADIUS_UNIFORMITY_MIN's comment for why that one
    # passes a real D-flat connector cutout straight through.
    circular = mean_runif >= RADIUS_UNIFORMITY_MIN

    if not circular:
        # Not a bolt hole at all -- a slot, a D-flat connector cutout, a vent.
        # Reported for completeness (Rule 2: don't drop evidence), not folded
        # into any of the five named feature kinds.
        kind = "irregular_void"
    elif len(flat) >= 2:
        kind = "counterbore"
    elif flat:
        kind = "through_hole" if reaches_lo and reaches_hi else "blind_hole"
    else:
        # No plateau at all -- the whole thread is one continuous taper.
        kind = "countersink"

    # A taper riding alongside a plain bore or a counterbore is a mouth
    # lead-in chamfer, not its own top-level feature -- note it rather than
    # double-reporting the same physical hole as two entries.
    chamfer = None
    if taper and kind not in ("irregular_void", "countersink"):
        biggest = max(taper, key=lambda r: r["to"] - r["from"])
        chamfer = {
            "from": round(biggest["from"], 3),
            "to": round(biggest["to"], 3),
            "note": "radius tapers here -- a lead-in cone or countersink chamfer at the mouth",
        }

    if flat:
        narrow = min(flat, key=lambda r: r["radius"])
        cx, cy, nominal_radius = narrow["cx"], narrow["cy"], narrow["radius"]
    else:
        cx = float(np.mean([t[1] for t in thread]))
        cy = float(np.mean([t[2] for t in thread]))
        nominal_radius = runs[-1]["radius"]

    return {
        "kind": kind,
        "center": (round(cx, 3), round(cy, 3)),
        "nominal_radius": round(float(nominal_radius), 3),
        "from": round(h0, 3),
        "to": round(h1, 3),
        "length": round(h1 - h0, 3),
        "circularity": round(mean_circ, 3),
        "radius_uniformity": round(mean_runif, 3),
        "reaches_lo": bool(reaches_lo),
        "reaches_hi": bool(reaches_hi),
        "runs": [
            {
                "radius": round(r["radius"], 3),
                "from": round(r["from"], 3),
                "to": round(r["to"], 3),
                "kind": r["kind"],
            }
            for r in runs
        ],
        "chamfer": chamfer,
        "build": FEATURE_RECIPES.get(kind, "not one of the five named feature kinds"),
    }


def _regular_layout(points: list[tuple[float, float]]) -> dict | None:
    """Classify a set of hole centres as a grid, a radial ring, or a line -- or None.

    Checked in that order because a grid is the most specific claim. Distances
    are in the slice's own local 2D basis (see mesh_analyze.slice_polygons),
    not necessarily the world X/Y/Z -- fine for spacing, which is
    rotation-invariant, but do not read these as world coordinates.
    """
    pts = np.array(points, dtype=float)
    n = len(pts)

    xs = sorted({round(float(x), 2) for x, _ in points})
    ys = sorted({round(float(y), 2) for _, y in points})

    def _near(a: float, b: float, tol: float = 0.3) -> bool:
        return abs(a - b) <= tol

    if 1 < len(xs) <= 6 and 1 < len(ys) <= 6 and len(xs) * len(ys) == n:
        combos = [(x, y) for x in xs for y in ys]
        if all(
            any(_near(px, cx) and _near(py, cy) for cx, cy in combos)
            for px, py in points
        ):
            pitch_x = float(np.mean(np.diff(xs))) if len(xs) > 1 else 0.0
            pitch_y = float(np.mean(np.diff(ys))) if len(ys) > 1 else 0.0
            return {
                "layout": "grid",
                "params": {"pitch_x": round(pitch_x, 3), "pitch_y": round(pitch_y, 3)},
            }

    centroid = pts.mean(axis=0)
    radii = np.hypot(pts[:, 0] - centroid[0], pts[:, 1] - centroid[1])
    if radii.mean() > 1e-6 and radii.std() / radii.mean() <= PATTERN_SPACING_TOL:
        angles = np.sort(
            np.mod(
                np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0]), 2 * np.pi
            )
        )
        gaps = np.diff(np.concatenate([angles, [angles[0] + 2 * np.pi]]))
        if gaps.mean() > 1e-6 and gaps.std() / gaps.mean() <= PATTERN_SPACING_TOL:
            return {
                "layout": "radial",
                "params": {
                    "radius": round(float(radii.mean()), 3),
                    "angle_pitch_deg": round(float(np.degrees(gaps.mean())), 2),
                },
            }

    if n >= 2:
        d = pts[-1] - pts[0]
        length = float(np.hypot(*d))
        if length > 1e-6:
            u = d / length
            perp = np.abs((pts - pts[0]) @ np.array([-u[1], u[0]]))
            proj = np.sort((pts - pts[0]) @ u)
            gaps = np.diff(proj)
            if (
                perp.max() <= max(0.3, 0.05 * length)
                and gaps.size
                and gaps.min() > 1e-6
                and gaps.std() / gaps.mean() <= PATTERN_SPACING_TOL
            ):
                return {
                    "layout": "linear",
                    "params": {"pitch": round(float(gaps.mean()), 3)},
                }

    return None


def _detect_patterns(features: list[dict]) -> list[dict]:
    """Group same-size hole features into regular patterns.

    Only ``through_hole``/``blind_hole``/``counterbore`` features are eligible
    -- a ``countersink`` alone has no single "the bolt goes here" radius to
    match on, and ``irregular_void`` is not a bolt hole at all. Grouping is
    pairwise-greedy on radius, which is not transitive-safe for a long chain
    of near-equal radii; fine for the handful of holes one part actually has.
    """
    candidates = [
        f
        for f in features
        if f["kind"] in ("through_hole", "blind_hole", "counterbore")
    ]
    used = [False] * len(candidates)
    patterns = []
    for i, f in enumerate(candidates):
        if used[i]:
            continue
        group = [i]
        for j in range(i + 1, len(candidates)):
            if used[j]:
                continue
            g = candidates[j]
            if abs(
                g["nominal_radius"] - f["nominal_radius"]
            ) <= PATTERN_RADIUS_TOL * max(f["nominal_radius"], 1e-6):
                group.append(j)
        if len(group) < 2:
            continue
        layout = _regular_layout([candidates[k]["center"] for k in group])
        if layout is None:
            continue
        for k in group:
            used[k] = True
        patterns.append(
            {
                "kind": "hole_pattern",
                "layout": layout["layout"],
                "count": len(group),
                "feature_kind": candidates[group[0]]["kind"],
                "nominal_radius": round(
                    float(np.mean([candidates[k]["nominal_radius"] for k in group])), 3
                ),
                **layout["params"],
                "build": FEATURE_RECIPES["hole_pattern"],
            }
        )
    return patterns


def detect_hole_features(
    mesh: trimesh.Trimesh,
    axis: int,
    lo: float,
    hi: float,
    step: float,
    max_slices: int,
) -> dict:
    """Slice one axis end to end at an even step and classify every hole on it.

    Independent of ``scan_axis``'s coarse/fine transition scan on purpose: a
    counterbore's shoulder or a countersink's taper rarely changes the *whole*
    cross-section's area or width enough to register as a "transition" (Rule
    2's evidence bar is the hole/contour count, and neither changes at a
    shoulder), so a scan that only refines near transitions would sample
    straight through most of these features and miss them.
    """
    extent = hi - lo
    if extent <= 0:
        return {
            "step": step,
            "coarsened": False,
            "slices": 0,
            "holes_tracked": 0,
            "features": [],
            "patterns": [],
        }

    margin = min(0.02 * extent, 0.05)
    n = int(extent / step) + 1 if step > 0 else 2
    coarsened = False
    if max_slices and n > max_slices:
        step = extent / max_slices
        n = max_slices
        coarsened = True

    heights = list(np.linspace(lo + margin, hi - margin, max(n, 2)))
    polys, _ = slice_polygons(mesh, axis, heights)
    rings_per_height = [_slice_rings(p) for p in polys]
    threads = _link_hole_threads(heights, rings_per_height)

    end_tol = max(3 * margin, 2 * step, 0.05)
    features = [_classify_thread(t, lo, hi, end_tol) for t in threads if t]
    patterns = _detect_patterns(features)

    return {
        "step": round(step, 4),
        "coarsened": coarsened,
        "slices": len(heights),
        "holes_tracked": len(threads),
        "features": features,
        "patterns": patterns,
    }


def scan_axis(
    mesh: trimesh.Trimesh,
    axis: int,
    coarse: float,
    fine: float,
    span: float,
    threshold: float,
    feature_step: float = 0.3,
    feature_max_slices: int = 600,
) -> dict:
    """Coarse pass to find transitions, fine pass only around them."""
    lo, hi = float(mesh.bounds[0][axis]), float(mesh.bounds[1][axis])

    heights = list(np.arange(lo + coarse / 2, hi, coarse))
    polys, _ = slice_polygons(mesh, axis, heights)
    stats = [measure(p) for p in polys]

    # Where does the section change enough to matter?
    transitions = []
    for i in range(1, len(stats)):
        prev, curr = stats[i - 1], stats[i]
        if prev is None or curr is None:
            if prev is not curr:
                transitions.append(float(heights[i]))
            continue
        d_area = abs(curr["area"] - prev["area"]) / max(prev["area"], 1e-9)
        d_width = abs(curr["width"] - prev["width"]) / max(prev["width"], 1e-9)
        if (
            d_area > threshold
            or d_width > threshold
            or curr["contours"] != prev["contours"]
            or curr["holes"] != prev["holes"]
        ):
            transitions.append(float(heights[i]))

    # Refine around each transition so the boundary lands within `fine`.
    refined = set()
    for t in transitions:
        for h in np.arange(max(lo, t - span), min(hi, t + span), fine):
            refined.add(round(float(h), 4))
    if refined:
        extra_h = sorted(refined)
        extra_p, _ = slice_polygons(mesh, axis, extra_h)
        for h, p in zip(extra_h, extra_p):
            heights.append(h)
            stats.append(measure(p))

    order = np.argsort(heights)
    heights = [float(heights[i]) for i in order]
    stats = [stats[i] for i in order]

    # Collapse consecutive same-shape slices into runs, then describe each run.
    # Kept as typed tuples rather than dict fields so the numbers stay numbers.
    runs: list[tuple[str, float, float, list[float], list[float]]] = []
    for h, s in zip(heights, stats):
        kind = classify(s["contours"], s["holes"]) if s else "empty"
        area = float(s["area"]) if s else 0.0
        width = float(s["width"]) if s else 0.0
        if runs and runs[-1][0] == kind:
            k, lo_h, _, areas, widths = runs[-1]
            areas.append(area)
            widths.append(width)
            runs[-1] = (k, lo_h, h, areas, widths)
        else:
            runs.append((kind, h, h, [area], [width]))

    zones: list[dict] = []
    for kind, from_h, to_h, areas, widths in runs:
        z: dict = {
            "type": kind,
            "from": round(from_h, 3),
            "to": round(to_h, 3),
            "length": round(to_h - from_h, 3),
            "mean_area": round(float(np.mean(areas)), 2),
        }
        # A steadily shrinking width across a zone is a taper, not a straight wall.
        mean_w = float(np.mean(widths))
        if len(widths) > 2 and mean_w > 1e-9:
            drift = (widths[-1] - widths[0]) / mean_w
            z["width_drift_pct"] = round(drift * 100, 1)
            if abs(drift) > 0.05:
                z["note"] = (
                    "width changes across the zone -- taper or fillet, not a straight extrude"
                )
        z["build"] = ZONE_RECIPES[kind]
        zones.append(z)

    holes = detect_hole_features(mesh, axis, lo, hi, feature_step, feature_max_slices)

    return {
        "axis": AXIS_NAMES[axis],
        "extent": round(hi - lo, 3),
        "slices": len(heights),
        "transitions": [round(t, 3) for t in transitions],
        "zones": zones,
        "holes": holes,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stl", type=Path)
    ap.add_argument("--out", type=Path, default=Path("analysis"))
    ap.add_argument("--coarse", type=float, default=5.0, help="coarse slice step, mm")
    ap.add_argument(
        "--fine", type=float, default=0.5, help="fine slice step near transitions, mm"
    )
    ap.add_argument(
        "--span",
        type=float,
        default=3.0,
        help="how far either side of a transition to refine",
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        help="fractional change that counts as a transition",
    )
    ap.add_argument(
        "--feature-step",
        type=float,
        default=0.3,
        help="even slice step, mm, for tracking holes end to end (independent of --fine, "
        "which only refines near zone transitions and can skip straight through a "
        "counterbore shoulder or a countersink taper)",
    )
    ap.add_argument(
        "--feature-max-slices",
        type=int,
        default=600,
        help="cap on hole-tracking slices per axis; --feature-step is coarsened to fit",
    )
    args = ap.parse_args()

    mesh = load_mesh(args.stl)
    args.out.mkdir(parents=True, exist_ok=True)

    axes: list[dict] = []
    for axis in range(3):
        result = scan_axis(
            mesh,
            axis,
            args.coarse,
            args.fine,
            args.span,
            args.threshold,
            args.feature_step,
            args.feature_max_slices,
        )
        axes.append(result)

        print(
            f"\n{result['axis']}  extent {result['extent']:.2f} mm, "
            f"{result['slices']} slices, {len(result['zones'])} zones"
        )
        for z in result["zones"]:
            line = (
                f"  {z['from']:8.2f} -> {z['to']:8.2f}  ({z['length']:6.2f} mm)  "
                f"{z['type']:<18} area {z['mean_area']:>10.1f}"
            )
            print(line)
            if "note" in z:
                print(f"           ^ {z['note']}")

        holes = result["holes"]
        named = [f for f in holes["features"] if f["kind"] != "irregular_void"]
        irregular = len(holes["features"]) - len(named)
        if holes["features"]:
            step_note = (
                " (coarsened to fit --feature-max-slices)" if holes["coarsened"] else ""
            )
            print(
                f"  {holes['holes_tracked']} hole(s) tracked at {holes['step']:.3f} mm "
                f"step{step_note}, {irregular} not circular enough to classify"
            )
        for f in named:
            print(
                f"    {f['kind']:<14} r={f['nominal_radius']:>6.2f}  "
                f"z {f['from']:>8.2f} -> {f['to']:>8.2f}  centre {f['center']}"
            )
            print(f"                   ^ {f['build']}")
            if len(f["runs"]) > 1:
                run_desc = ", ".join(
                    f"r={r['radius']:.2f}@{r['kind']}" for r in f["runs"]
                )
                print(f"                   runs: {run_desc}")
            if f["chamfer"]:
                print(f"                   ^ {f['chamfer']['note']}")
        for p in holes["patterns"]:
            print(
                f"    hole_pattern   {p['layout']:<7} x{p['count']}  "
                f"r={p['nominal_radius']:.2f}  {p['feature_kind']}"
            )
            print(f"                   ^ {p['build']}")

    # Fewest zones = simplest structure to describe along that axis.
    simplest = min(axes, key=lambda a: len(a["zones"]))
    report = {"source": str(args.stl), "axes": axes, "simplest_axis": simplest["axis"]}
    print(
        f"\nFewest zones along {simplest['axis']} ({len(simplest['zones'])}). "
        f"That is usually the axis to decompose along."
    )

    out = args.out / "zones.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
