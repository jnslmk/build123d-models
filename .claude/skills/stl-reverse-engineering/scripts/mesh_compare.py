#!/usr/bin/env python3
"""Score a reconstruction against the original mesh.

Reports volume and bounding-box deltas AND a real geometric accuracy figure by
Monte-Carlo intersection-over-union. The IoU is the number that matters: a
reconstruction can match volume and bounding box exactly and still be the wrong
shape (see Rule 3 in references/reconstruction-guide.md).

Usage:
    uv run --group mesh python .claude/skills/stl-reverse-engineering/scripts/mesh_compare.py \
        original.stl reconstruction.stl [--samples 200000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh  # ty: ignore[unresolved-import]  # optional 'mesh' group

sys.path.insert(0, str(Path(__file__).parent))
from mesh_analyze import slice_polygons  # noqa: E402  # ty: ignore[unresolved-import]


def load(path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load(path, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        raise SystemExit(
            f"{path}: not a single triangle mesh (got {type(mesh).__name__})"
        )
    if not mesh.is_watertight:
        print(
            f"WARNING: {path.name} is not watertight -- IoU is unreliable.",
            file=sys.stderr,
        )
    return mesh


def iou_boolean(a: trimesh.Trimesh, b: trimesh.Trimesh) -> dict | None:
    """Exact IoU via manifold3d booleans. Milliseconds, but needs clean meshes."""
    try:
        inter = a.intersection(b)
        union = a.union(b)
        if union.volume <= 0:
            return None
        return {
            "iou": float(inter.volume / union.volume),
            "missing_volume": float(a.volume - inter.volume),
            "excess_volume": float(b.volume - inter.volume),
            "method": "boolean (exact)",
        }
    except Exception as exc:  # noqa: BLE001 - any boolean failure means fall back
        print(
            f"Boolean IoU failed ({type(exc).__name__}); falling back to sampling.",
            file=sys.stderr,
        )
        return None


def alignment_gap(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    """How far apart the two meshes' bounding-box centres sit, in mm.

    IoU is not translation- or rotation-invariant, and this script does not
    align anything. That is fine for round-trip validation, where both meshes
    come out of the same pipeline at the same origin -- and a trap for a
    *downloaded* reference, which sits whereever its author left it. A mesh
    exported with its base still attached, 19 mm up the z axis, scores near zero
    against a correct reconstruction and says nothing about why.
    """
    return float(np.linalg.norm((a.bounds.mean(axis=0) - b.bounds.mean(axis=0))))


N_SECTIONS, N_ANGLES = 160, 256


def radial_field(mesh: trimesh.Trimesh, axis: int, heights, angles):
    """r(angle, height) of a mesh's outer ring, or None where a slice fails."""
    polys, _ = slice_polygons(mesh, axis, heights)
    rows = []
    for slice_polys in polys:
        if not slice_polys:
            rows.append(None)
            continue
        ring = np.asarray(max(slice_polys, key=lambda p: p.area).exterior.coords)
        theta = np.mod(np.arctan2(ring[:, 1], ring[:, 0]), 2 * np.pi)
        radius = np.hypot(ring[:, 0], ring[:, 1])
        order = np.argsort(theta)
        theta, radius = theta[order], radius[order]
        th = np.concatenate(([theta[-1] - 2 * np.pi], theta, [theta[0] + 2 * np.pi]))
        rr = np.concatenate(([radius[-1]], radius, [radius[0]]))
        rows.append(np.interp(angles, th, rr))
    return rows


def _paired_fields(a, b, axis: int):
    """Both meshes' radial fields on one grid, restricted to sections both have."""
    lo = max(a.bounds[0][axis], b.bounds[0][axis])
    hi = min(a.bounds[1][axis], b.bounds[1][axis])
    if hi - lo <= 0:
        return None, None
    pad = (hi - lo) * 0.02
    heights = np.linspace(lo + pad, hi - pad, N_SECTIONS)
    angles = np.linspace(0, 2 * np.pi, N_ANGLES, endpoint=False)
    fa, fb = radial_field(a, axis, heights, angles), radial_field(b, axis, heights, angles)
    keep = [i for i in range(len(heights)) if fa[i] is not None and fb[i] is not None]
    if len(keep) < len(heights) // 2:
        return None, None
    return np.vstack([fa[i] for i in keep]), np.vstack([fb[i] for i in keep])


def align(a: trimesh.Trimesh, b: trimesh.Trimesh, axis: int = 2) -> tuple[float, float]:
    """Move `b` onto `a`: bottoms together, then the best rotation about the axis.

    Both are rigid transforms, so neither is a difference in shape, and removing
    them is not flattering the reconstruction -- it is declining to score it on
    where it happens to sit. Returns (mm shifted, degrees rotated).

    The rotation is found by rolling one radial field against the other, which
    costs one slicing pass rather than one per candidate angle. Only the axis is
    scanned: which way *up* a part is is a real difference, and this will not
    hide it.
    """
    shift = a.bounds[0][axis] - b.bounds[0][axis]
    delta = np.zeros(3)
    delta[axis] = shift
    b.apply_translation(delta)

    fa, fb = _paired_fields(a, b, axis)
    if fa is None:
        return float(shift), 0.0
    best, best_err = 0, np.inf
    for roll in range(fa.shape[1]):
        err = float(np.mean((fa - np.roll(fb, roll, axis=1)) ** 2))
        if err < best_err:
            best, best_err = roll, err
    deg = 360.0 * best / fa.shape[1]
    direction = np.zeros(3)
    direction[axis] = 1.0
    b.apply_transform(
        trimesh.transformations.rotation_matrix(
            np.radians(deg), direction, a.bounds.mean(axis=0)
        )
    )
    return float(shift), deg


def iou_envelope(a: trimesh.Trimesh, b: trimesh.Trimesh, axis: int = 2) -> dict | None:
    """Exact IoU of two star-shaped-about-an-axis solids, from their radial fields.

    The escape hatch for a reference that is not watertight -- the normal state
    of a vase-mode export, and the state that disables the boolean and leaves
    only a sampling fallback this script's own warning calls unreliable. Where a
    solid is star-shaped about its axis it is described entirely by r(theta, z),
    and then the intersection at each sample goes as ``min(r1, r2)^2`` and the
    union as ``max(r1, r2)^2``. Exact, in seconds, with no mesh repair at all.

    It measures the **outer envelope**, so it is blind to a hollow. That is a
    feature when comparing two shells of the same wall thickness (the hollow is
    the same offset in both, so including it would only dilute the number) and a
    trap otherwise -- so the caller has to ask for it, and the printed method
    says which number it is.
    """
    fa, fb = _paired_fields(a, b, axis)
    if fa is None:
        return None
    inter = float((np.minimum(fa, fb) ** 2).sum())
    union = float((np.maximum(fa, fb) ** 2).sum())
    if union <= 0:
        return None
    return {
        "iou": inter / union,
        "missing_volume": float("nan"),
        "excess_volume": float("nan"),
        "radial_rms_mm": float(np.sqrt(np.mean((fa - fb) ** 2))),
        "method": f"outer envelope, exact ({fa.shape[0]} sections x {fa.shape[1]} angles)",
    }


def iou_sampled(
    a: trimesh.Trimesh, b: trimesh.Trimesh, samples: int, seed: int = 0
) -> dict:
    """Monte-Carlo intersection-over-union over the union bounding box.

    The fallback for meshes a boolean refuses -- which is exactly the dirty input
    this tool exists to handle. Standard error is ~1/sqrt(samples).
    """
    lo = np.minimum(a.bounds[0], b.bounds[0])
    hi = np.maximum(a.bounds[1], b.bounds[1])
    span = hi - lo
    pad = span * 0.01
    lo, hi = lo - pad, hi + pad

    rng = np.random.default_rng(seed)
    pts = rng.uniform(lo, hi, size=(samples, 3))

    in_a = a.contains(pts)
    in_b = b.contains(pts)

    both = int(np.count_nonzero(in_a & in_b))
    either = int(np.count_nonzero(in_a | in_b))
    only_a = int(np.count_nonzero(in_a & ~in_b))
    only_b = int(np.count_nonzero(~in_a & in_b))

    box_volume = float(np.prod(hi - lo))
    per_sample = box_volume / samples

    return {
        "iou": both / either if either else 0.0,
        "missing_volume": only_a * per_sample,
        "excess_volume": only_b * per_sample,
        "samples": samples,
        "samples_inside_either": either,
        "method": f"sampled ({samples} points, +/- {100 / samples**0.5:.2f}%)",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original", type=Path)
    ap.add_argument("reconstruction", type=Path)
    ap.add_argument("--samples", type=int, default=200_000)
    ap.add_argument(
        "--sampled", action="store_true", help="skip the boolean, always sample"
    )
    ap.add_argument(
        "--envelope",
        action="store_true",
        help="grade the outer envelope from radial fields; exact, ignores hollows, "
        "and works on meshes no boolean will touch",
    )
    ap.add_argument(
        "--align",
        action="store_true",
        help="put the reconstruction's bottom and rotation onto the original's "
        "before grading (both are rigid transforms, not shape)",
    )
    ap.add_argument("--json", type=Path, help="also write the report here")
    args = ap.parse_args()

    a, b = load(args.original), load(args.reconstruction)

    if args.align:
        shift, deg = align(a, b)
        print(f"aligned   moved {shift:+.3f} mm and rotated {deg:.1f} deg before grading")
    else:
        gap = alignment_gap(a, b)
        scale = float(np.linalg.norm(a.extents))
        if gap > 0.02 * scale:
            print(
                f"WARNING: bounding-box centres are {gap:.2f} mm apart. This script does "
                "not align;\n         a downloaded reference sits wherever its author "
                "left it, and an unaligned\n         pair scores near zero for reasons "
                "that are not shape. Re-run with --align.",
                file=sys.stderr,
            )

    vol_error = float(abs(b.volume - a.volume) / a.volume * 100.0)
    bbox_delta = b.extents - a.extents

    report: dict = {
        "original": str(args.original),
        "reconstruction": str(args.reconstruction),
        "volume_original": float(a.volume),
        "volume_reconstruction": float(b.volume),
        "volume_error_pct": vol_error,
        "bbox_original": a.extents.tolist(),
        "bbox_reconstruction": b.extents.tolist(),
        "bbox_delta": bbox_delta.tolist(),
    }
    if args.envelope:
        measured = iou_envelope(a, b)
        if measured is None:
            print(
                "Envelope IoU failed -- these are not star-shaped about z; sampling.",
                file=sys.stderr,
            )
    else:
        measured = None if args.sampled else iou_boolean(a, b)
        if measured is None and not a.is_watertight:
            print(
                "         (the original is not watertight -- if it is a turned or lofted\n"
                "         shell, --envelope is exact and needs no repair)",
                file=sys.stderr,
            )
    stats: dict = measured if measured else iou_sampled(a, b, args.samples)
    report.update(stats)

    acc = float(stats["iou"]) * 100.0
    if acc >= 98:
        verdict, level = "excellent -- production quality", 0
    elif acc >= 95:
        verdict, level = "good -- functional, ready for a test print", 0
    elif acc >= 85:
        verdict, level = "draft -- structure is right, details are not", 1
    else:
        verdict, level = "wrong shape -- do not iterate on this, re-analyse", 1
    report["verdict"] = verdict

    print(f"volume    {a.volume:12.2f} -> {b.volume:12.2f}   ({vol_error:.2f}% error)")
    print(f"bbox      {np.round(a.extents, 3)} -> {np.round(b.extents, 3)}")
    print(f"          delta {np.round(bbox_delta, 4)}")
    print(f"IoU       {acc:.2f}%   ({verdict})  [{stats['method']}]")
    print(
        f"missing   {float(stats['missing_volume']):12.2f} mm^3  (in original, not in reconstruction)"
    )
    print(
        f"excess    {float(stats['excess_volume']):12.2f} mm^3  (in reconstruction, not in original)"
    )

    if vol_error < 1.0 and acc < 90:
        print(
            "\nNOTE: volume matches but IoU does not. The reconstruction has the right"
        )
        print(
            "      amount of material in the wrong places. Re-check the profile axis."
        )

    if args.json:
        args.json.write_text(json.dumps(report, indent=2))
    return level


if __name__ == "__main__":
    sys.exit(main())
