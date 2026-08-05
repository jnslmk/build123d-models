#!/usr/bin/env python3
"""Analyse an STL mesh and emit a build123d starting point.

Detects the extrusion axis by cross-section stability, extracts the dominant
profile, and writes builder-mode build123d code plus a JSON report.

Adapted from andreahaku/openscad_claude_skill (MIT) -- the slicing and
stability-score approach is theirs; the code generation and the axis reporting
are rewritten for build123d.

Usage:
    uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_analyze.py \
        model.stl --out analysis/ [--simplify 0.05]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh  # ty: ignore[unresolved-import]  # optional 'mesh' group
from shapely.geometry import MultiLineString, Polygon  # ty: ignore[unresolved-import]  # optional 'mesh' group
from shapely.ops import polygonize  # ty: ignore[unresolved-import]  # optional 'mesh' group
from trimesh import intersections  # ty: ignore[unresolved-import]  # optional 'mesh' group

AXIS_NAMES = ("X", "Y", "Z")


def load_mesh(path) -> trimesh.Trimesh:
    """Load a mesh, insisting on a single Trimesh rather than a Scene."""
    mesh = trimesh.load(path, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        raise SystemExit(
            f"{path}: not a single triangle mesh (got {type(mesh).__name__})"
        )
    return mesh


def segments_to_polygons(segments, snap: float = 1e-4) -> list[Polygon]:
    """Stitch slice line segments into polygons, snapping to kill tessellation noise."""
    lines = []
    for seg in np.asarray(segments):
        a = tuple(np.round(seg[0] / snap) * snap)
        b = tuple(np.round(seg[1] / snap) * snap)
        if a != b:
            lines.append([a, b])
    if not lines:
        return []
    return [p for p in polygonize(MultiLineString(lines)) if p.area > snap * snap]


def slice_polygons(mesh: trimesh.Trimesh, axis: int, heights):
    """Slice `mesh` perpendicular to `axis` at each height.

    Returns (polygons_per_height, to_3D_per_height). The to_3D transforms are
    what map a slice's 2D coordinates back into world space -- do NOT assume the
    2D axes are the world axes, because trimesh picks its own in-plane basis.
    """
    normal = np.zeros(3)
    normal[axis] = 1.0
    origin = np.zeros(3)
    segments, to_3d, _ = intersections.mesh_multiplane(
        mesh, plane_origin=origin, plane_normal=normal, heights=np.asarray(heights)
    )
    polys = [segments_to_polygons(s) if len(s) else [] for s in segments]
    return polys, to_3d


def detect_extrusion_axis(mesh: trimesh.Trimesh, n_slices: int = 64) -> dict:
    """Score each axis by how little its cross-section changes along it.

    The LOWEST score is the most stable axis. Read this together with the
    thinnest-axis extent -- for models with diagonal features the thinnest axis
    is usually the better extrusion direction even when it loses on stability.
    """
    results = {}
    for axis in range(3):
        lo, hi = mesh.bounds[0][axis], mesh.bounds[1][axis]
        margin = (hi - lo) * 0.02
        heights = np.linspace(lo + margin, hi - margin, n_slices)
        per_slice, _ = slice_polygons(mesh, axis, heights)

        areas, perims, holes = [], [], []
        for polys in per_slice:
            if not polys:
                continue
            areas.append(sum(p.area for p in polys))
            perims.append(sum(p.length for p in polys))
            holes.append(sum(len(p.interiors) for p in polys))

        if len(areas) < 3:
            results[AXIS_NAMES[axis]] = {
                "stability": float("inf"),
                "note": "too few valid slices",
            }
            continue

        areas, perims = np.array(areas), np.array(perims)
        # Normalised spread: unitless, so the three axes are comparable.
        score = float(
            np.std(areas) / (np.mean(areas) + 1e-9)
            + np.std(perims) / (np.mean(perims) + 1e-9)
            + np.std(holes)
        )
        results[AXIS_NAMES[axis]] = {
            "stability": score,
            "mean_area": float(np.mean(areas)),
            "extent": float(hi - lo),
            "hole_counts": sorted(set(int(h) for h in holes)),
        }

    ranked = sorted(results.items(), key=lambda kv: kv[1]["stability"])
    extents = {AXIS_NAMES[a]: float(mesh.extents[a]) for a in range(3)}
    thinnest = min(extents, key=lambda k: extents[k])
    return {
        "per_axis": results,
        "stability_axis": ranked[0][0],
        "stability_score": ranked[0][1]["stability"],
        "thinnest_axis": thinnest,
        "extents": extents,
        "axes_agree": ranked[0][0] == thinnest,
    }


def dominant_profile(
    mesh: trimesh.Trimesh, axis: int, simplify: float, n_slices: int = 64
):
    """Return (polygon, height, plane) for the largest cross-section along `axis`.

    `plane` carries the origin/x_dir/z_dir needed to put the sketch back exactly
    where the mesh sits, with the origin slid down the normal to the base of the
    mesh so the extrusion starts at the real bottom rather than at the slice.
    """
    lo, hi = mesh.bounds[0][axis], mesh.bounds[1][axis]
    margin = (hi - lo) * 0.02
    heights = np.linspace(lo + margin, hi - margin, n_slices)
    per_slice, to_3d = slice_polygons(mesh, axis, heights)

    best, best_h, best_t = None, None, None
    for polys, h, t in zip(per_slice, heights, to_3d):
        if not polys:
            continue
        largest = max(polys, key=lambda p: p.area)
        if best is None or largest.area > best.area:
            best, best_h, best_t = largest, h, t
    if best is None or best_t is None or best_h is None:
        return None, None, None
    if simplify > 0:
        best = best.simplify(simplify, preserve_topology=True)

    x_dir = best_t[:3, 0]
    normal = best_t[:3, 2]
    origin = best_t[:3, 3]

    # Slide the sketch plane to the base of the mesh measured along the normal,
    # so extruding a positive amount sweeps the real extent.
    d = mesh.vertices @ normal
    origin = origin + (d.min() - origin @ normal) * normal

    plane = {
        "origin": [float(v) for v in origin],
        "x_dir": [float(v) for v in x_dir],
        "z_dir": [float(v) for v in normal],
        "length": float(d.max() - d.min()),
    }
    return best, float(best_h), plane


def _fmt_points(coords) -> str:
    pts = [f"    ({x:.3f}, {y:.3f})," for x, y in coords]
    return "\n".join(pts)


def emit_build123d(poly: Polygon, plane: dict, axis: int, name: str) -> str:
    """Generate builder-mode build123d source for an extruded profile with holes.

    Holes are subtracted AFTER the outer face is made -- see the ordering rule in
    references/reconstruction-guide.md.
    """
    outer = list(poly.exterior.coords)[:-1]
    holes = [list(r.coords)[:-1] for r in poly.interiors]
    extrude_len = plane["length"]

    def vec(v):
        return "(" + ", ".join(f"{c:.6f}" for c in v) + ")"

    lines = [
        '"""Reconstructed from a mesh by mesh_analyze.py -- STARTING POINT, NOT A MODEL.',
        "",
        f"Extruded along {AXIS_NAMES[axis]} for {extrude_len:.3f} mm from a profile of",
        f"{len(outer)} points and {len(holes)} hole(s).",
        "",
        "Before this is a real model: replace the polygon with parametric geometry,",
        "name the measured dimensions, add the edge treatments AGENTS.md requires, and",
        "confirm the part is returned in print pose.",
        '"""',
        "",
        "from build123d import (",
        "    BuildLine,",
        "    BuildPart,",
        "    BuildSketch,",
        *(["    Mode,"] if holes else []),
        "    Part,",
        "    Plane,",
        "    Polyline,",
        "    extrude,",
        "    make_face,",
        ")",
        "",
        f"EXTRUDE_LENGTH = {extrude_len:.3f}",
        "",
        "# The plane the profile was sliced on, slid to the base of the mesh. The",
        "# in-plane axes are trimesh's, not the world axes -- keep this transform or",
        "# the part rebuilds in the wrong place.",
        "PROFILE_PLANE = Plane(",
        f"    origin={vec(plane['origin'])},",
        f"    x_dir={vec(plane['x_dir'])},",
        f"    z_dir={vec(plane['z_dir'])},",
        ")",
        "",
        "OUTER = [",
        _fmt_points(outer),
        "]",
        "",
    ]

    for i, hole in enumerate(holes):
        lines += [f"HOLE_{i} = [", _fmt_points(hole), "]", ""]

    lines += [
        "",
        "def create() -> Part:",
        '    """Build the reconstructed part."""',
        "    with BuildPart() as builder:",
        "        with BuildSketch(PROFILE_PLANE):",
        "            with BuildLine():",
        "                Polyline(*OUTER, close=True)",
        "            make_face()",
    ]

    for i in range(len(holes)):
        lines += [
            "            with BuildLine():",
            f"                Polyline(*HOLE_{i}, close=True)",
            "            make_face(mode=Mode.SUBTRACT)",
        ]

    lines += [
        "        extrude(amount=EXTRUDE_LENGTH)",
        "    return builder.part",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stl", type=Path)
    ap.add_argument("--out", type=Path, default=Path("analysis"))
    ap.add_argument(
        "--simplify",
        type=float,
        default=0.05,
        help="Douglas-Peucker tolerance in mm. Lower = more points = closer curves. "
        "0.3 flattens curves badly; 0.02 is near the useful floor.",
    )
    ap.add_argument("--slices", type=int, default=64)
    args = ap.parse_args()

    mesh = load_mesh(args.stl)
    args.out.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "source": str(args.stl),
        "triangles": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "volume": float(mesh.volume) if mesh.is_watertight else None,
        "bounds": mesh.bounds.tolist(),
        "extents": mesh.extents.tolist(),
    }

    if not mesh.is_watertight:
        report["warning"] = (
            "Mesh is not watertight. Volume and containment tests are unreliable; "
            "slice contours may fail to close."
        )
        print(f"WARNING: {args.stl} is not watertight.", file=sys.stderr)

    ax: dict = detect_extrusion_axis(mesh, args.slices)
    report["axis"] = ax

    chosen_name = ax["stability_axis"]
    axis = AXIS_NAMES.index(chosen_name)
    poly, at_height, plane = dominant_profile(mesh, axis, args.simplify, args.slices)

    profile: dict | None = None
    if poly is None or plane is None:
        print(
            "Could not extract a profile -- no closed contour on any slice.",
            file=sys.stderr,
        )
    else:
        extrude_len = plane["length"]
        profile = {
            "axis": chosen_name,
            "sampled_at": at_height,
            "points": len(poly.exterior.coords) - 1,
            "holes": len(poly.interiors),
            "profile_area": float(poly.area),
            "swept_volume": float(poly.area * extrude_len),
            "plane": plane,
        }
        if mesh.is_watertight:
            ratio = float(poly.area * extrude_len / mesh.volume)
            profile["swept_over_actual"] = ratio
            profile["clean_extrusion"] = bool(0.97 < ratio < 1.03)

        code = emit_build123d(poly, plane, axis, args.stl.stem)
        (args.out / "reconstructed.py").write_text(code)

    report["profile"] = profile
    (args.out / "analysis.json").write_text(json.dumps(report, indent=2))

    extents: dict = ax["extents"]
    print(
        f"{args.stl.name}: {report['triangles']} triangles, watertight={report['watertight']}"
    )
    print(
        f"  extents      X={extents['X']:.2f} Y={extents['Y']:.2f} Z={extents['Z']:.2f}"
    )
    print(f"  stability    {ax['stability_axis']} (score {ax['stability_score']:.4f})")
    print(f"  thinnest     {ax['thinnest_axis']}")
    if not ax["axes_agree"]:
        print(
            "  NOTE: stability and thinnest axes disagree -- if the model has diagonal"
        )
        print("        features, prefer the thinnest axis. See the guide.")
    if profile is not None:
        print(
            f"  profile      {profile['points']} pts, {profile['holes']} hole(s) on {profile['axis']}"
        )
        if "swept_over_actual" in profile:
            clean = profile["clean_extrusion"]
            print(
                f"  swept/actual {profile['swept_over_actual']:.3f}"
                f"{'  (clean extrusion)' if clean else '  (NOT a clean extrusion)'}"
            )
        print(f"  wrote        {args.out / 'reconstructed.py'}")
    print(f"  wrote        {args.out / 'analysis.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
