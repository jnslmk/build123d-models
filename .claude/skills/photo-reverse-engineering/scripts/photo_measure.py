"""Turn a photo into a measurement ledger with honest error bars.

A photo has no scale and, unless the camera was square-on, no consistent one
either: the same part is worth more millimetres per pixel at the far edge of an
oblique shot than at the near edge. This script fixes both, in that order.

1. **Rectify.** Given the four image corners of a planar rectangle whose real
   size is known, it solves the homography that maps that quadrilateral back to
   a rectangle and warps the photo through it. Everything coplanar with that
   rectangle is then square-on and uniformly scaled.
2. **Scale.** The same homography fixes px_per_mm exactly, because the
   rectangle's real size was an input.
3. **Measure.** Point pairs become millimetres -- each carrying the error bar
   implied by how precisely a human can put a cursor on an edge.

That third column is the point of the whole script. A measurement without its
uncertainty invites being written straight into a model as if it were a caliper
reading, and a photo is typically an order of magnitude coarser than the fits
this repo works in. The ledger prints, per measurement, the finest fit class
that measurement could legitimately set -- usually "none of them".

Input is one JSON spec (see ``--example``), output is ``ledger.json``, a
markdown table on stdout, and the rectified image when rectification was asked
for. Depends only on numpy and pillow (the ``photo`` dependency group).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Diametral clearances from models/lib/fits.py, tightest first. A measurement
# may set a dimension in a class only if its error bar is at most half that
# class's clearance -- otherwise the measurement error alone can consume the
# whole fit and land on the wrong side of it. PRESS is omitted: it is an
# interference fit of the same magnitude as SNUG, so it never widens what a
# given measurement is good enough for.
FIT_CLASSES = [("SNUG", 0.10), ("SLIDING", 0.22), ("FREE", 0.40)]

EXAMPLE_SPEC = {
    "photo": "refs/latch_front.jpg",
    "rectify": {
        "corners_px": [[412, 388], [1691, 372], [1723, 1204], [388, 1219]],
        "size_mm": [148.0, 105.0],
        "note": "A6 sheet the part was photographed on",
    },
    "point_uncertainty_px": 2.0,
    "measurements": [
        {
            "name": "body_width",
            "from": [520, 640],
            "to": [1160, 645],
            "note": "outer wall to outer wall, rectified pixels",
        }
    ],
}


def homography(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Solve H with dst ~ H @ src for four point correspondences (DLT).

    Both arrays are (4, 2). The 8 unknowns of a projective transform are fixed
    by 4 point pairs, so this is exact, not a fit -- which is why the corners
    have to be clicked carefully. Their error propagates into every
    measurement downstream, unlike the endpoint error, which is per
    measurement.
    """
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.asarray(rows, dtype=float))
    return (vt[-1] / vt[-1][-1]).reshape(3, 3)


def apply_h(h: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Map (N, 2) points through a homography."""
    pts = np.atleast_2d(np.asarray(pts, dtype=float))
    hom = np.hstack([pts, np.ones((len(pts), 1))])
    out = hom @ h.T
    return out[:, :2] / out[:, 2:3]


def warp(img: np.ndarray, h_inv: np.ndarray, out_wh: tuple[int, int]) -> np.ndarray:
    """Inverse-map an image through ``h_inv`` with bilinear sampling.

    Forward-mapping source pixels would leave holes wherever the transform
    stretches, so every output pixel asks where it came from instead.
    """
    w, h = out_wh
    ys, xs = np.mgrid[0:h, 0:w]
    src = apply_h(h_inv, np.column_stack([xs.ravel(), ys.ravel()]))
    sx, sy = src[:, 0], src[:, 1]

    ih, iw = img.shape[:2]
    x0 = np.clip(np.floor(sx).astype(int), 0, iw - 1)
    y0 = np.clip(np.floor(sy).astype(int), 0, ih - 1)
    x1 = np.clip(x0 + 1, 0, iw - 1)
    y1 = np.clip(y0 + 1, 0, ih - 1)
    fx = np.clip(sx - x0, 0, 1)[:, None]
    fy = np.clip(sy - y0, 0, 1)[:, None]

    px = img.reshape(ih, iw, -1).astype(float)
    top = px[y0, x0] * (1 - fx) + px[y0, x1] * fx
    bot = px[y1, x0] * (1 - fx) + px[y1, x1] * fx
    out = (top * (1 - fy) + bot * fy).reshape(h, w, -1)

    # Anything sampled from outside the source frame is not evidence; black it
    # out rather than smearing the border pixel across the rectified plane.
    inside = (sx >= 0) & (sx <= iw - 1) & (sy >= 0) & (sy <= ih - 1)
    out.reshape(-1, out.shape[-1])[~inside] = 0
    return out.astype(np.uint8).squeeze()


def finest_fit(tolerance_mm: float) -> str:
    """The tightest fit class a measurement with this error bar could set."""
    for name, clearance in FIT_CLASSES:
        if tolerance_mm <= abs(clearance) / 2:
            return name
    return "none"


def run(spec: dict, spec_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    photo_path = (spec_dir / spec["photo"]).resolve()
    img = np.asarray(Image.open(photo_path).convert("RGB"))

    sigma_px = float(spec.get("point_uncertainty_px", 2.0))
    rectified_path = None

    if "rectify" in spec:
        rect = spec["rectify"]
        corners = np.asarray(rect["corners_px"], dtype=float)
        if corners.shape != (4, 2):
            raise SystemExit("rectify.corners_px must be 4 [x, y] pairs (TL, TR, BR, BL)")
        w_mm, h_mm = (float(v) for v in rect["size_mm"])

        # Resolution of the rectified plane. Matching the longest source edge
        # keeps the output from inventing detail the photo never had.
        edge_px = max(
            np.linalg.norm(corners[1] - corners[0]), np.linalg.norm(corners[2] - corners[3])
        )
        px_per_mm = float(rect.get("px_per_mm", edge_px / w_mm))
        out_w, out_h = round(w_mm * px_per_mm), round(h_mm * px_per_mm)

        dst = np.array([[0, 0], [out_w, 0], [out_w, out_h], [0, out_h]], dtype=float)
        h = homography(corners, dst)
        rectified = warp(img, np.linalg.inv(h), (out_w, out_h))
        rectified_path = out_dir / "rectified.png"
        Image.fromarray(rectified).save(rectified_path)
        measure_space = "rectified"
    else:
        if "scale" not in spec:
            raise SystemExit("spec needs either 'rectify' or 'scale.px_per_mm'")
        px_per_mm = float(spec["scale"]["px_per_mm"])
        h = np.eye(3)
        measure_space = "original"

    entries = []
    for m in spec.get("measurements", []):
        p0, p1 = np.asarray([m["from"], m["to"]], dtype=float)
        if measure_space == "rectified" and m.get("space", "original") == "original":
            p0, p1 = apply_h(h, np.array([p0, p1]))
        dist_px = float(np.linalg.norm(p1 - p0))
        # Two independent endpoint errors add in quadrature; 2 sigma is the
        # bar reported, so a stated +/- is a ~95% interval, not a 1-sigma one.
        tol_mm = 2 * math.sqrt(2) * sigma_px / px_per_mm
        mm = dist_px / px_per_mm
        entries.append(
            {
                "name": m["name"],
                "mm": round(mm, 3),
                "tolerance_mm": round(tol_mm, 3),
                "px": round(dist_px, 1),
                "finest_fit_class": finest_fit(tol_mm),
                "note": m.get("note", ""),
                "provenance": "photo",
            }
        )

    ledger = {
        "photo": str(photo_path),
        "px_per_mm": round(px_per_mm, 4),
        "point_uncertainty_px": sigma_px,
        "measure_space": measure_space,
        "rectified": str(rectified_path) if rectified_path else None,
        "measurements": entries,
    }
    (out_dir / "ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    return ledger


def report(ledger: dict) -> int:
    print(f"px_per_mm            {ledger['px_per_mm']:.4f}")
    print(f"point uncertainty    +/-{ledger['point_uncertainty_px']:.1f} px")
    if ledger["rectified"]:
        print(f"rectified            {ledger['rectified']}")
    print()
    print(f"{'measurement':<24}{'mm':>10}{'+/-':>9}   finest fit it can set")
    print("-" * 72)
    for e in ledger["measurements"]:
        print(
            f"{e['name']:<24}{e['mm']:>10.2f}{e['tolerance_mm']:>9.3f}   {e['finest_fit_class']}"
        )
    print()

    unusable = [e for e in ledger["measurements"] if e["finest_fit_class"] == "none"]
    if unusable:
        print(
            f"{len(unusable)} of {len(ledger['measurements'])} measurements are coarser than "
            "every fit class in models/lib/fits.py.\n"
            "Use them for shape and proportion. Take mating dimensions from calipers or a\n"
            "datasheet, and derive the clearance from fdm-fits-and-clearances."
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Turn a photo into a measurement ledger with honest error bars")
    ap.add_argument("spec", nargs="?", help="JSON measurement spec")
    ap.add_argument("--out", default="analysis", help="output directory")
    ap.add_argument("--example", action="store_true", help="print an example spec and exit")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE_SPEC, indent=2))
        return 0
    if not args.spec:
        ap.error("a spec path is required (or --example)")

    spec_path = Path(args.spec).resolve()
    spec = json.loads(spec_path.read_text())
    return report(run(spec, spec_path.parent, Path(args.out)))


if __name__ == "__main__":
    sys.exit(main())
