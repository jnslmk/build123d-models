"""Grade a build123d model's silhouette against a reference photo silhouette.

This is the critic's instrument. It renders a model's outline from a named view
at a known px_per_mm, lines it up with the reference, and reports three numbers:

* **IoU** -- how much of the two outlines coincide. Necessary, not sufficient.
* **width / height ratio** -- the reference's bounding box over the model's.
  This is the number that actually catches mistakes, because it converts "looks
  about right" into "your part is 3.1% too wide", and a scale error is the
  single most common way a photo reconstruction goes wrong.
* **the residual image** -- where the two disagree, so a failure is legible
  rather than just low.

What it cannot see is the whole reason this repo also has `checks.py`: a
silhouette is an outline. Internal cavities, blind pockets, wall thickness, and
anything behind the front surface leave it completely unchanged. See the
`hidden_cavity` scenario in this skill's eval, which scores 100% IoU on two
parts of visibly different volume. Never let a silhouette gate stand in for a
geometry assertion.

Depends on numpy and pillow (the ``photo`` dependency group) plus build123d.
"""

from __future__ import annotations

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Same camera directions as render_svg.py, so a silhouette lines up with the
# SVG a human would look at for the same view name.
VIEWS: dict[str, tuple[float, float, float]] = {
    "iso": (100, -100, 80),
    "front": (0, -100, 0),
    "back": (0, 100, 0),
    "left": (-100, 0, 0),
    "right": (100, 0, 0),
    "top": (0, 0, 100),
    "bottom": (0, 0, -100),
}

# Rasterise at this multiple of the requested resolution, then threshold down.
# A binary mask from a single-sample rasteriser has a jagged edge worth about
# one pixel of IoU on a small part; supersampling puts that back.
SUPERSAMPLE = 3

DEFAULT_PASS_IOU = 0.95


def camera_basis(view: str) -> tuple[np.ndarray, np.ndarray]:
    """Right and up vectors of the image plane for a named view."""
    eye = np.asarray(VIEWS[view], dtype=float)
    forward = -eye / np.linalg.norm(eye)
    # Any world up works except one parallel to the view direction, which is
    # exactly the top and bottom views.
    world_up = np.array([0.0, 1.0, 0.0]) if abs(forward[2]) > 0.999 else np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return right, up / np.linalg.norm(up)


def project(part, view: str, tolerance: float = 0.05) -> np.ndarray:
    """Tessellate a part and project its triangles onto the view plane.

    Returns an (N, 3, 2) array of 2-D triangles in millimetres. Depth is
    discarded on purpose -- a silhouette is the union of every triangle's
    shadow, so which one is in front never matters.
    """
    verts, tris = part.tessellate(tolerance)
    pts = np.array([[v.X, v.Y, v.Z] for v in verts], dtype=float)
    right, up = camera_basis(view)
    flat = np.column_stack([pts @ right, pts @ up])
    return flat[np.asarray(tris, dtype=int)]


def rasterise(tris_mm: np.ndarray, px_per_mm: float, pad_mm: float = 1.0) -> np.ndarray:
    """Fill projected triangles into a boolean mask.

    PIL's polygon fill is a C loop, which keeps this practical on the 30k+
    triangle models in this repo where a per-pixel numpy test would not be.
    """
    lo = tris_mm.reshape(-1, 2).min(axis=0) - pad_mm
    hi = tris_mm.reshape(-1, 2).max(axis=0) + pad_mm
    scale = px_per_mm * SUPERSAMPLE
    w = max(1, int(round((hi[0] - lo[0]) * scale)))
    h = max(1, int(round((hi[1] - lo[1]) * scale)))

    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    px = (tris_mm - lo) * scale
    px[:, :, 1] = h - px[:, :, 1]  # image y grows downward
    for tri in px:
        draw.polygon([tuple(p) for p in tri], fill=255)

    full = np.asarray(img) > 127
    # Box-downsample the supersampled mask; a pixel is solid if most of its
    # subpixels were.
    hh, ww = h // SUPERSAMPLE, w // SUPERSAMPLE
    if hh == 0 or ww == 0:
        return full
    cropped = full[: hh * SUPERSAMPLE, : ww * SUPERSAMPLE]
    blocks = cropped.reshape(hh, SUPERSAMPLE, ww, SUPERSAMPLE)
    return blocks.mean(axis=(1, 3)) > 0.5


def load_reference_mask(path: Path, threshold: int | None = None) -> np.ndarray:
    """Read a reference silhouette from a photo, a mask, or an alpha channel.

    Photo segmentation here is deliberately the dumbest thing that works: a
    global threshold. It is correct only for a part shot against a plain,
    strongly contrasting background. For anything else, cut the mask by hand
    and pass that instead -- a bad segmentation produces a confident, wrong
    IoU, which is worse than no number.
    """
    img = Image.open(path)
    if "A" in img.getbands():
        return np.asarray(img.getchannel("A")) > 127

    grey = np.asarray(img.convert("L"))
    if threshold is None:
        threshold = otsu(grey)
    # The part is whichever side of the threshold does not touch the border:
    # backgrounds reach the frame edge, parts photographed whole do not.
    dark = grey < threshold
    border = np.concatenate([dark[0], dark[-1], dark[:, 0], dark[:, -1]])
    return dark if border.mean() < 0.5 else ~dark


def otsu(grey: np.ndarray) -> int:
    """Otsu's threshold: the split that minimises within-class variance."""
    hist = np.bincount(grey.ravel(), minlength=256).astype(float)
    total = hist.sum()
    omega = np.cumsum(hist) / total
    mu = np.cumsum(hist * np.arange(256)) / total
    mu_t = mu[-1]
    denom = omega * (1 - omega)
    with np.errstate(divide="ignore", invalid="ignore"):
        between = np.where(denom > 0, (mu_t * omega - mu) ** 2 / denom, 0)
    return int(np.argmax(between))


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        raise SystemExit("empty mask -- nothing to compare")
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def align_and_score(a: np.ndarray, b: np.ndarray, search_px: int = 6) -> dict:
    """Best IoU of two masks over a small translation search.

    Translation only, on purpose. Letting the search rotate or rescale would
    hide exactly the errors this is meant to surface: a part that is 3% too
    wide should score badly, not be quietly resized until it scores well.
    """
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    h = max(a.shape[0], b.shape[0]) + 2 * search_px
    w = max(a.shape[1], b.shape[1]) + 2 * search_px

    def placed(mask, box, dx=0, dy=0):
        x0, y0, x1, y1 = box
        sub = mask[y0:y1, x0:x1]
        out = np.zeros((h, w), dtype=bool)
        oy = (h - (y1 - y0)) // 2 + dy
        ox = (w - (x1 - x0)) // 2 + dx
        out[oy : oy + (y1 - y0), ox : ox + (x1 - x0)] = sub
        return out

    base = placed(a, (ax0, ay0, ax1, ay1))
    best = None
    for dy in range(-search_px, search_px + 1):
        for dx in range(-search_px, search_px + 1):
            shifted = placed(b, (bx0, by0, bx1, by1), dx, dy)
            inter = np.logical_and(base, shifted).sum()
            union = np.logical_or(base, shifted).sum()
            iou = inter / union if union else 0.0
            if best is None or iou > best["iou"]:
                best = {"iou": float(iou), "dx": dx, "dy": dy, "shifted": shifted}

    assert best is not None
    return {
        "iou": best["iou"],
        "offset_px": [best["dx"], best["dy"]],
        "width_ratio": (bx1 - bx0) / (ax1 - ax0),
        "height_ratio": (by1 - by0) / (ay1 - ay0),
        "base": base,
        "other": best["shifted"],
    }


def residual_png(base: np.ndarray, other: np.ndarray, path: Path) -> None:
    """Model-only in red, reference-only in blue, agreement in grey."""
    rgb = np.zeros((*base.shape, 3), dtype=np.uint8)
    both = base & other
    rgb[both] = (110, 110, 110)
    rgb[base & ~other] = (220, 60, 60)
    rgb[other & ~base] = (60, 120, 220)
    Image.fromarray(rgb).save(path)


def load_model(name: str):
    module = importlib.import_module(f"models.{name}")
    if not hasattr(module, "create"):
        raise SystemExit(f"models.{name} has no create()")
    return module.create()


def main() -> int:
    ap = argparse.ArgumentParser(description="Grade a model's silhouette against a reference photo silhouette")
    ap.add_argument("model", help="model name, e.g. lens_cap or led_profiles.stand")
    ap.add_argument("--view", default="front", choices=sorted(VIEWS))
    ap.add_argument("--reference", help="reference photo or mask (PNG/JPG)")
    ap.add_argument("--px-per-mm", type=float, default=8.0)
    ap.add_argument("--pass-iou", type=float, default=DEFAULT_PASS_IOU)
    ap.add_argument("--threshold", type=int, help="fixed grey threshold instead of Otsu")
    ap.add_argument("--out", default="analysis", help="output directory")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    model_mask = rasterise(project(load_model(args.model), args.view), args.px_per_mm)
    Image.fromarray((model_mask * 255).astype(np.uint8)).save(
        out / f"{args.model}_{args.view}_silhouette.png"
    )

    if not args.reference:
        print(f"wrote silhouette for {args.model} ({args.view}), no reference to compare")
        return 0

    ref_mask = load_reference_mask(Path(args.reference), args.threshold)
    score = align_and_score(model_mask, ref_mask)
    residual_png(score["base"], score["other"], out / f"{args.model}_{args.view}_residual.png")

    result = {
        "model": args.model,
        "view": args.view,
        "reference": args.reference,
        "iou": round(score["iou"], 6),
        "width_ratio": round(score["width_ratio"], 4),
        "height_ratio": round(score["height_ratio"], 4),
        "offset_px": score["offset_px"],
        "pass_iou": args.pass_iou,
        "passed": score["iou"] >= args.pass_iou,
    }
    (out / f"{args.model}_{args.view}_match.json").write_text(json.dumps(result, indent=2) + "\n")

    print(f"IoU            {score['iou'] * 100:6.2f}%   (pass >= {args.pass_iou * 100:.0f}%)")
    print(f"width ratio    {score['width_ratio']:6.4f}   reference / model")
    print(f"height ratio   {score['height_ratio']:6.4f}")
    for axis in ("width", "height"):
        err = (score[f"{axis}_ratio"] - 1) * 100
        if abs(err) > 1.0:
            print(f"  -> model is {abs(err):.1f}% too {'small' if err > 0 else 'large'} in {axis}")
    print(f"residual       {out / f'{args.model}_{args.view}_residual.png'}")

    if not result["passed"]:
        print("\nFAIL: silhouettes disagree. Fix the shape before iterating on detail.")
        return 1
    print("\nPASS on silhouette only -- this says nothing about internal geometry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
