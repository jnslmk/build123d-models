#!/usr/bin/env python3
"""Eval harness for the stl-reverse-engineering skill.

Adapts the eval/ concept from andreahaku/openscad_claude_skill (MIT): named
scenarios, each with pass/fail assertions, plus an append-only results log with
a documented baseline. That reference repo's assertions are LLM-judged prose
checks on a conversation transcript. Ours are not -- this skill ships
deterministic scripts (mesh_analyze.py, mesh_compare.py) with known numeric
ground truth, so the assertions here are real executable checks against real
script output. No LLM judging involved.

For each scenario in scenarios.json this:
  1. Exports the named model to STL (`uv run export <model>`).
  2. Runs mesh_analyze.py on that STL and reads swept_over_actual.
  3. Imports the generated reconstructed.py, builds it, and exports it to STL.
  4. Runs mesh_compare.py between the original and the reconstruction.
  5. Asserts the measured swept_over_actual and IoU match the pinned baseline
     within tolerance, AND that mesh_compare's exit code matches the declared
     requirement -- for led_profiles.stand that requirement is 1 (a REQUIRED
     NEGATIVE: the tool must refuse that reconstruction, not pass it).

Appends one line to results.jsonl per run. See README.md for the pinned
baselines, their provenance, the tolerance rationale, and this harness's own
first real run.

Usage:
    uv run --group mesh python .claude/skills/stl-reverse-engineering/eval/run_eval.py
    uv run --group mesh python .claude/skills/stl-reverse-engineering/eval/run_eval.py \
        --change-description "tightened simplify tolerance in mesh_analyze.py"
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from build123d import export_stl

EVAL_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVAL_DIR.parent
REPO_ROOT = SKILL_DIR.parents[2]
SCRIPTS_DIR = SKILL_DIR / "scripts"
SCENARIOS_PATH = EVAL_DIR / "scenarios.json"
RESULTS_PATH = EVAL_DIR / "results.jsonl"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"

MESH_ANALYZE = SCRIPTS_DIR / "mesh_analyze.py"
MESH_COMPARE = SCRIPTS_DIR / "mesh_compare.py"


@dataclass
class ScenarioResult:
    """Outcome of running one scenario, including every assertion checked."""

    scenario_id: str
    passed: bool
    measured_swept_over_actual: float | None = None
    measured_iou: float | None = None
    measured_exit_code: int | None = None
    failed_assertions: list[str] = field(default_factory=list)
    error: str | None = None


def skill_version_hash() -> str:
    """Short hash of SKILL.md, so a results.jsonl line records which skill version ran."""
    digest = hashlib.sha256(SKILL_MD_PATH.read_bytes()).hexdigest()
    return digest[:12]


def run_subprocess(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a subprocess, always capturing output as text."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def export_model_stl(model: str) -> Path:
    """Run `uv run export <model>` and return the STL path it produced.

    export.py names the file `exports/<model>.stl` verbatim -- including the
    dot for a package model like `led_profiles.stand` -- so no name-mangling
    is needed here.
    """
    proc = run_subprocess(["uv", "run", "export", model], cwd=REPO_ROOT)
    if proc.returncode != 0:
        raise RuntimeError(
            f"`uv run export {model}` failed (exit {proc.returncode}):\n{proc.stderr}"
        )
    stl_path = REPO_ROOT / "exports" / f"{model}.stl"
    if not stl_path.exists():
        raise RuntimeError(
            f"`uv run export {model}` succeeded but {stl_path} does not exist "
            "-- export.py's naming convention may have changed."
        )
    return stl_path


def analyze_mesh(
    stl_path: Path, out_dir: Path, simplify: float | None, slices: int | None
) -> dict:
    """Run mesh_analyze.py and return its parsed analysis.json."""
    args = [
        "uv",
        "run",
        "--group",
        "mesh",
        "python",
        str(MESH_ANALYZE),
        str(stl_path),
        "--out",
        str(out_dir),
    ]
    if simplify is not None:
        args += ["--simplify", str(simplify)]
    if slices is not None:
        args += ["--slices", str(slices)]
    proc = run_subprocess(args, cwd=REPO_ROOT)
    analysis_path = out_dir / "analysis.json"
    if not analysis_path.exists():
        raise RuntimeError(
            f"mesh_analyze.py did not write {analysis_path} (exit {proc.returncode}):\n"
            f"{proc.stderr}"
        )
    return json.loads(analysis_path.read_text())


def build_reconstruction_stl(
    reconstructed_py: Path, module_name: str, out_stl: Path
) -> None:
    """Dynamically import reconstructed.py's create() and export it to an STL."""
    if not reconstructed_py.exists():
        raise RuntimeError(f"{reconstructed_py} was not generated -- no profile found.")
    spec = importlib.util.spec_from_file_location(module_name, reconstructed_py)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load a module spec for {reconstructed_py}")
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    part = module.create()
    export_stl(part, str(out_stl))


def compare_meshes(
    original: Path, reconstruction: Path, out_json: Path
) -> tuple[int, dict]:
    """Run mesh_compare.py and return (exit_code, parsed compare.json)."""
    args = [
        "uv",
        "run",
        "--group",
        "mesh",
        "python",
        str(MESH_COMPARE),
        str(original),
        str(reconstruction),
        "--json",
        str(out_json),
    ]
    proc = run_subprocess(args, cwd=REPO_ROOT)
    if not out_json.exists():
        raise RuntimeError(
            f"mesh_compare.py did not write {out_json} (exit {proc.returncode}):\n{proc.stderr}"
        )
    return proc.returncode, json.loads(out_json.read_text())


def run_scenario(
    scenario: dict, swept_tolerance: float, iou_tolerance: float
) -> ScenarioResult:
    """Run the full export -> analyze -> reconstruct -> compare pipeline for one scenario."""
    scenario_id = scenario["id"]
    model = scenario["model"]
    result = ScenarioResult(scenario_id=scenario_id, passed=False)

    try:
        stl_path = export_model_stl(model)

        with tempfile.TemporaryDirectory(
            prefix=f"stl-eval-{scenario_id.replace('.', '_')}-"
        ) as tmp:
            tmp_dir = Path(tmp)

            analysis = analyze_mesh(
                stl_path,
                tmp_dir,
                scenario.get("simplify"),
                scenario.get("slices"),
            )
            profile = analysis.get("profile") or {}
            measured_swept = profile.get("swept_over_actual")
            result.measured_swept_over_actual = measured_swept

            reconstructed_py = tmp_dir / "reconstructed.py"
            reconstruction_stl = tmp_dir / "reconstruction.stl"
            build_reconstruction_stl(
                reconstructed_py,
                f"reconstructed_{scenario_id.replace('.', '_')}",
                reconstruction_stl,
            )

            compare_json = tmp_dir / "compare.json"
            exit_code, compare_report = compare_meshes(
                stl_path, reconstruction_stl, compare_json
            )
            result.measured_exit_code = exit_code
            result.measured_iou = compare_report.get("iou")

        # -- Assertions --
        baseline_swept = scenario["baseline_swept_over_actual"]
        if measured_swept is None:
            result.failed_assertions.append(
                "swept_over_actual was not reported by mesh_analyze.py (no profile found)"
            )
        elif abs(measured_swept - baseline_swept) > swept_tolerance:
            result.failed_assertions.append(
                f"swept_over_actual drifted: measured={measured_swept:.4f} "
                f"baseline={baseline_swept:.4f} tolerance={swept_tolerance} "
                f"(this ratio is deterministic given the same model -- a drift "
                f"here means the pipeline itself changed, not just the mesh)"
            )

        baseline_iou = scenario["baseline_iou"]
        measured_iou = result.measured_iou
        if measured_iou is None:
            result.failed_assertions.append(
                "mesh_compare.py did not report an iou value"
            )
        elif abs(measured_iou - baseline_iou) > iou_tolerance:
            result.failed_assertions.append(
                f"IoU drifted: measured={measured_iou:.4f} baseline={baseline_iou:.4f} "
                f"tolerance={iou_tolerance}"
            )

        required_exit = scenario["required_compare_exit_code"]
        if exit_code != required_exit:
            polarity = "REQUIRED NEGATIVE" if required_exit != 0 else "required pass"
            result.failed_assertions.append(
                f"mesh_compare.py exit code {exit_code} != required {required_exit} "
                f"({polarity})"
            )

        result.passed = not result.failed_assertions

    except Exception as exc:  # noqa: BLE001 - a scenario failure must not abort the run
        result.error = f"{type(exc).__name__}: {exc}"
        result.failed_assertions.append(result.error)

    return result


def load_scenarios() -> dict:
    return json.loads(SCENARIOS_PATH.read_text())


def next_iteration() -> int:
    """One more than the highest iteration already logged, so runs number sequentially.

    Reads the max rather than counting lines: the seed entry is iteration 0 (a
    documented pin, not a harness run), so counting lines would skip straight
    to 2 for the first real run.
    """
    if not RESULTS_PATH.exists():
        return 1
    iterations = [
        json.loads(line)["iteration"]
        for line in RESULTS_PATH.read_text().splitlines()
        if line.strip()
    ]
    return max(iterations, default=0) + 1


def append_result(results: list[ScenarioResult], change_description: str) -> dict:
    """Append one JSON line to results.jsonl and return the record written.

    Every record this function writes is `"kind": "run"` and describes the
    execution that just happened -- this call site is the only place a "run"
    line is ever produced, and it always fires immediately after the pipeline
    it is reporting on actually completed. Never hand-author a "run" line
    (e.g. to pre-record a review or a future check as if it had already
    happened): a line's `change_description` must only ever describe an event
    that has already occurred by the time the line is written, and the only
    honest way to satisfy that is to let this function -- not a person -- write
    it, right after the run it describes. The one line exempt from this is the
    `"kind": "seed"` provenance entry at the top of the file, which is
    deliberately hand-authored and labeled as such because it records a pin,
    not a run.
    """
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    failed_assertions = [
        f"{r.scenario_id}: {msg}" for r in results for msg in r.failed_assertions
    ]
    record = {
        "iteration": next_iteration(),
        "kind": "run",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "score": round(100.0 * passed / total, 2) if total else 0.0,
        "passed": passed,
        "total": total,
        "failed_assertions": failed_assertions,
        "skill_version_hash": skill_version_hash(),
        "change_description": change_description,
    }
    with RESULTS_PATH.open("a") as fh:
        fh.write(json.dumps(record) + "\n")
    return record


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--change-description",
        default="routine eval run (no change description given)",
        help="One-line note recorded in results.jsonl explaining what prompted this run.",
    )
    args = ap.parse_args()

    config = load_scenarios()
    swept_tolerance = config["swept_tolerance"]
    iou_tolerance = config["iou_tolerance"]

    results = [
        run_scenario(scenario, swept_tolerance, iou_tolerance)
        for scenario in config["scenarios"]
    ]

    print(f"{'scenario':<22} {'swept/actual':>14} {'IoU':>10} {'exit':>6}  result")
    for r in results:
        swept_str = (
            f"{r.measured_swept_over_actual:.4f}"
            if r.measured_swept_over_actual is not None
            else "n/a"
        )
        iou_str = (
            f"{r.measured_iou * 100:.2f}%" if r.measured_iou is not None else "n/a"
        )
        exit_str = (
            str(r.measured_exit_code) if r.measured_exit_code is not None else "n/a"
        )
        status = "PASS" if r.passed else "FAIL"
        print(
            f"{r.scenario_id:<22} {swept_str:>14} {iou_str:>10} {exit_str:>6}  {status}"
        )
        for msg in r.failed_assertions:
            print(f"    - {msg}")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{passed}/{total} scenarios matched their pinned baseline")

    record = append_result(results, args.change_description)
    print(f"logged run #{record['iteration']} to {RESULTS_PATH.relative_to(REPO_ROOT)}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
