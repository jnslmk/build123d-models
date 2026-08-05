#!/usr/bin/env python3
"""Map a mesh into feature zones along all three axes.

The tool to reach for when mesh_analyze.py reports the model is NOT a clean
extrusion. It finds the heights where the cross-section changes and classifies
each stable band between them, so you can see the model's structure -- where a
channel opens, where a taper runs, where holes start and stop -- before writing
any geometry.

Adapted from andreahaku/openscad_claude_skill (MIT). Their coarse-then-fine
approach and zone taxonomy; batch slicing and the build123d mapping are new.

Usage:
    uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_zones.py \
        model.stl [--out analysis/] [--coarse 5] [--fine 0.5]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh  # ty: ignore[unresolved-import]  # optional 'mesh' group
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


def scan_axis(
    mesh: trimesh.Trimesh,
    axis: int,
    coarse: float,
    fine: float,
    span: float,
    threshold: float,
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

    return {
        "axis": AXIS_NAMES[axis],
        "extent": round(hi - lo, 3),
        "slices": len(heights),
        "transitions": [round(t, 3) for t in transitions],
        "zones": zones,
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
    args = ap.parse_args()

    mesh = load_mesh(args.stl)
    args.out.mkdir(parents=True, exist_ok=True)

    axes: list[dict] = []
    for axis in range(3):
        result = scan_axis(
            mesh, axis, args.coarse, args.fine, args.span, args.threshold
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
