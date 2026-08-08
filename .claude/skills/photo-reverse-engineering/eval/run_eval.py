"""Executable checks for photo-reverse-engineering's published claims.

SKILL.md makes four numeric claims. This harness re-derives each by running the
skill's own scripts and fails when a number drifts from the pinned baseline in
``scenarios.json``.

Two of the four are **required negatives** -- scenarios that must score badly,
or must score *suspiciously well*, for the skill's warnings to be true:

* ``scale_error_2pct``  -- a part 2% too large must still score high IoU. If a
  future change made IoU collapse there, the skill's "IoU cannot see a scale
  error, read the ratio" warning would be obsolete, and the guidance wrong.
* ``hidden_cavity``     -- two parts of visibly different volume must score
  100% IoU. This is the claim that a silhouette gate is blind to internal
  geometry. If it ever failed, the skill would be over-warning.

Nothing here is LLM-judged. Every assertion is a number out of a script.

Run:
    uv run --no-group viewer --group photo python \\
        .claude/skills/photo-reverse-engineering/eval/run_eval.py
"""

from __future__ import annotations

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent


def load_script(name: str):
    """Import a script from ../scripts by path, without installing anything."""
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sil = load_script("silhouette_match")
meas = load_script("photo_measure")


def scenario_self_match(cfg: dict) -> dict:
    """A silhouette against itself. Anything but 100% means the tool is broken."""
    part = sil.load_model(cfg["model"])
    mask = sil.rasterise(sil.project(part, cfg["view"]), cfg["px_per_mm"])
    score = sil.align_and_score(mask, mask)
    return {"iou": score["iou"], "width_ratio": score["width_ratio"]}


def scenario_scale_error(cfg: dict) -> dict:
    """The same part rasterised at two scales -- exactly a uniform size error.

    Rasterising at ``px_per_mm * k`` produces the identical mask a part scaled
    by ``k`` would produce, so this is an exact scale error with no
    remodelling and no sampling noise beyond the rasteriser's own.
    """
    part = sil.load_model(cfg["model"])
    tris = sil.project(part, cfg["view"])
    truth = sil.rasterise(tris, cfg["px_per_mm"])
    wrong = sil.rasterise(tris, cfg["px_per_mm"] * cfg["scale_factor"])
    score = sil.align_and_score(wrong, truth)
    return {"iou": score["iou"], "width_ratio": score["width_ratio"]}


def scenario_hidden_cavity(cfg: dict) -> dict:
    """A solid block versus the same block with a sealed internal void.

    Every outside surface is identical, so every silhouette is identical, while
    a quarter of the material is gone. This is the case a visual critic cannot
    reach, and the reason a model still needs checks.py.
    """
    from build123d import Box, BuildPart, Mode

    ow, od, oh = cfg["outer_mm"]
    iw, idp, ih = cfg["cavity_mm"]

    with BuildPart() as solid:
        Box(ow, od, oh)
    with BuildPart() as hollow:
        Box(ow, od, oh)
        Box(iw, idp, ih, mode=Mode.SUBTRACT)

    worst = 1.0
    for view in cfg["views"]:
        a = sil.rasterise(sil.project(solid.part, view), cfg["px_per_mm"])
        b = sil.rasterise(sil.project(hollow.part, view), cfg["px_per_mm"])
        worst = min(worst, sil.align_and_score(a, b)["iou"])

    return {
        "iou": worst,
        "volume_ratio": hollow.part.volume / solid.part.volume,
    }


def scenario_rectify(cfg: dict) -> dict:
    """End-to-end check of the homography maths on a synthetic oblique photo.

    A rectangle of known size, plus a segment of known length inside it, is
    warped by a known projective transform -- simulating a camera that was not
    square-on. photo_measure then rectifies from the four warped corners and
    re-measures the segment. Recovering the original millimetres proves the
    rectification, the scale and the measurement path all agree.
    """
    w_mm, h_mm = cfg["board_mm"]
    ppm = cfg["synthetic_px_per_mm"]
    seg_mm = cfg["segment_mm"]

    # Ground-truth board in millimetre-anchored pixels.
    board_px = np.array(
        [[0, 0], [w_mm * ppm, 0], [w_mm * ppm, h_mm * ppm], [0, h_mm * ppm]], dtype=float
    )
    seg_y = h_mm * ppm / 2
    seg = np.array([[10 * ppm, seg_y], [(10 + seg_mm) * ppm, seg_y]], dtype=float)

    # An oblique camera: push the far edge in and up, the way a tilted phone
    # shot does. Corner offsets in pixels, hand-chosen, not fitted.
    warped_corners = board_px + np.asarray(cfg["oblique_offsets_px"], dtype=float)
    h = meas.homography(board_px, warped_corners)
    warped_seg = meas.apply_h(h, seg)

    # Paint the warped board so the rectified output is checkable too, not just
    # the point maths: a correct warp turns this quadrilateral back into a
    # rectangle that fills the frame.
    canvas_w = int(warped_corners[:, 0].max() + 40)
    canvas_h = int(warped_corners[:, 1].max() + 40)
    img = Image.new("RGB", (canvas_w, canvas_h), (20, 20, 20))
    ImageDraw.Draw(img).polygon([tuple(p) for p in warped_corners], fill=(255, 255, 255))
    img.save(HERE / "_synthetic.png")

    spec = {
        "photo": "_synthetic.png",
        "rectify": {
            "corners_px": warped_corners.tolist(),
            "size_mm": [w_mm, h_mm],
            "px_per_mm": ppm,
        },
        "point_uncertainty_px": 1.0,
        "measurements": [
            {
                "name": "known_segment",
                "from": warped_seg[0].tolist(),
                "to": warped_seg[1].tolist(),
                "space": "original",
            }
        ],
    }
    out = HERE / "_rectify_out"
    ledger = meas.run(spec, HERE, out)
    recovered = ledger["measurements"][0]["mm"]
    rectified = np.asarray(Image.open(ledger["rectified"]).convert("L"))
    filled = float((rectified > 127).mean())

    (HERE / "_synthetic.png").unlink(missing_ok=True)
    for leftover in out.glob("*"):
        leftover.unlink()
    out.rmdir()

    return {
        "recovered_mm": recovered,
        "error_mm": abs(recovered - seg_mm),
        "rectified_fill": filled,
    }


RUNNERS = {
    "self_match": scenario_self_match,
    "scale_error": scenario_scale_error,
    "hidden_cavity": scenario_hidden_cavity,
    "rectify": scenario_rectify,
}


def check(scenario: dict, measured: dict) -> list[str]:
    """Compare measured values to the scenario's pinned assertions."""
    failures = []
    for key, expected in scenario["assertions"].items():
        got = measured.get(key)
        if got is None:
            failures.append(f"{scenario['id']}: no measurement for '{key}'")
            continue
        lo, hi = expected["min"], expected["max"]
        if not (lo <= got <= hi):
            failures.append(f"{scenario['id']}: {key}={got:.6f} outside [{lo}, {hi}]")
    return failures


def append_result(passed: int, total: int, failures: list[str], note: str) -> None:
    log = HERE / "results.jsonl"
    previous = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
    entry = {
        "iteration": len(previous),
        "kind": "run",
        "timestamp": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "score": round(100 * passed / total, 2) if total else 0.0,
        "passed": passed,
        "total": total,
        "failed_assertions": failures,
        "skill_version_hash": hashlib.sha256((SKILL / "SKILL.md").read_bytes()).hexdigest()[:12],
        "change_description": note,
    }
    with log.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-derive photo-reverse-engineering's published numbers and check them")
    ap.add_argument("--change-description", default="unattributed run")
    args = ap.parse_args()

    scenarios = json.loads((HERE / "scenarios.json").read_text())["scenarios"]
    rows, failures = [], []

    for scenario in scenarios:
        measured = RUNNERS[scenario["runner"]](scenario["config"])
        problems = check(scenario, measured)
        failures.extend(problems)
        rows.append((scenario, measured, not problems))

    print(f"{'scenario':<22}{'measured':<44}result")
    print("-" * 76)
    for scenario, measured, ok in rows:
        summary = "  ".join(f"{k}={v:.4f}" for k, v in measured.items())
        print(f"{scenario['id']:<22}{summary:<44}{'PASS' if ok else 'FAIL'}")

    passed = sum(1 for _, _, ok in rows if ok)
    print(f"\n{passed}/{len(rows)} scenarios matched their pinned baseline")
    for problem in failures:
        print(f"  ! {problem}")

    append_result(passed, len(rows), failures, args.change_description)
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
