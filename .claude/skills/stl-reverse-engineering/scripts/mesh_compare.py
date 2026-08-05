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
    ap.add_argument("--json", type=Path, help="also write the report here")
    args = ap.parse_args()

    a, b = load(args.original), load(args.reconstruction)

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
    measured = None if args.sampled else iou_boolean(a, b)
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
