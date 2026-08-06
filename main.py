"""Build the roster's models and export them to STL + STEP + GLB.

There is no model list here. The roster is ``tessellate_models.MODELS`` and this
builds straight from it, so CI, the website and this command can never disagree
about what a model is -- which is exactly what the two hand-kept lists that used
to live here did whenever one of them was updated alone.

To add a model to the build, add its name to ``MODELS``. Nothing else.

Two things make this cheap enough to run on every push:

**It rebuilds only what a change can reach.** Each model is fingerprinted over
its own import closure (``model_deps``) plus the build's global inputs, and the
fingerprint of the last successful build is kept in ``exports/.build-stamps.json``
next to the artifacts it describes. A model whose fingerprint still matches, and
whose files are all still on disk, is already built. This is the automated form
of the "rebuild what you changed *and everything that imports it*" rule in
``AGENTS.md`` -- the same question, answered by walking imports instead of by
grep. Restore ``exports/`` from a cache and CI inherits the same skipping.

**It builds the rest in parallel.** The models are independent, so they go
through a process pool, longest-job-first using the durations recorded by the
previous run. That ordering matters: the roster's slowest model takes minutes
while ten of them together take under two seconds, and starting the long poles
last leaves workers idle at the end.

    uv run python main.py              # build whatever is stale
    uv run python main.py --all        # ignore the stamps, rebuild everything
    uv run python main.py --list       # show the plan, build nothing
    uv run python main.py --jobs 1     # serialise (for a readable traceback)
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import traceback
from pathlib import Path

import model_deps
from tessellate_models import MODELS

ROOT = Path(__file__).parent.resolve()
EXPORTS_DIR = ROOT / "exports"
STAMPS = EXPORTS_DIR / ".build-stamps.json"
STAMP_VERSION = 1

# Each worker holds a whole OCC solid, so the pool is bounded by memory as well
# as by cores. Past eight, the meshing threads OCC starts internally contend
# with each other and the extra processes stop paying for themselves.
MAX_JOBS = 8


def _load_stamps() -> dict[str, dict]:
    """The previous run's fingerprints, or empty if there is nothing to trust.

    A stamp file from a different schema, or one that is unreadable for any
    reason, is discarded rather than guessed at: the cost is one full rebuild,
    and the alternative is skipping a model that should have been built.
    """
    try:
        data = json.loads(STAMPS.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if data.get("version") != STAMP_VERSION:
        return {}
    models = data.get("models")
    return models if isinstance(models, dict) else {}


def _save_stamps(stamps: dict[str, dict]) -> None:
    EXPORTS_DIR.mkdir(exist_ok=True)
    payload = {"version": STAMP_VERSION, "models": stamps}
    # Write-then-replace: a run interrupted mid-write must not leave a truncated
    # stamp file that reads as "everything is up to date".
    tmp = STAMPS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=1, sort_keys=True))
    tmp.replace(STAMPS)


def _staleness(name: str, stamp: dict | None, fingerprint: str) -> str:
    """Why ``name`` needs rebuilding, or "" if it does not."""
    if stamp is None:
        return "never built"
    if stamp.get("fingerprint") != fingerprint:
        return "sources changed"
    missing = [
        out for out in stamp.get("outputs", []) if not (EXPORTS_DIR / out).exists()
    ]
    if missing:
        return f"missing {', '.join(sorted(missing))}"
    return ""


def plan(force: bool) -> tuple[list[tuple[str, str]], dict[str, dict]]:
    """The models to rebuild and why, plus the stamps carried over from before."""
    stamps = {} if force else _load_stamps()
    stale = []
    for name in MODELS:
        reason = (
            "forced"
            if force
            else _staleness(name, stamps.get(name), model_deps.fingerprint(name))
        )
        if reason:
            stale.append((name, reason))
    return stale, stamps


def _build(name: str) -> dict:
    """Build and export one model. Runs in a pool worker, so it must be picklable.

    Failures come back as data rather than as an exception: one bad model should
    report itself at the end of the run alongside the others, not abort the pool
    and hide which of the remaining models would also have failed.
    """
    import time

    # ``export.EXPORTS_DIR`` is relative, so the worker has to agree with this
    # module about where "exports/" is however the build was invoked. Otherwise
    # the stamps would describe one directory and the artifacts land in another.
    os.chdir(ROOT)

    from export import export
    from tessellate_models import get_part

    started = time.perf_counter()
    try:
        written = export(get_part(name), name, step=True, children=False)
    except Exception:  # noqa: BLE001 -- collected and re-reported by main()
        return {"name": name, "error": traceback.format_exc()}
    return {
        "name": name,
        "seconds": time.perf_counter() - started,
        "outputs": sorted(path.name for path in written),
    }


def _order(stale: list[tuple[str, str]], stamps: dict[str, dict]) -> list[str]:
    """Longest job first, using the durations the last successful build recorded.

    A model with no recorded duration sorts first: it has never been timed, and
    guessing it is cheap risks leaving the pool's longest job until last.
    """

    def cost(name: str) -> float:
        return stamps.get(name, {}).get("seconds", float("inf"))

    return sorted((name for name, _ in stale), key=cost, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and export the model roster.")
    parser.add_argument(
        "--all", action="store_true", help="rebuild every model, ignoring the stamps"
    )
    parser.add_argument(
        "--list", action="store_true", help="print what would be rebuilt, and stop"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(os.cpu_count() or 1, MAX_JOBS),
        help=f"parallel build processes (default: cores, capped at {MAX_JOBS})",
    )
    args = parser.parse_args()

    stale, stamps = plan(args.all)

    orphans = sorted(set(stamps) - set(MODELS))
    if orphans:
        print(f"Left the roster, exports kept on disk: {', '.join(orphans)}")
        stamps = {name: stamp for name, stamp in stamps.items() if name in MODELS}

    if not stale:
        print(f"All {len(MODELS)} models up to date.")
        _save_stamps(stamps)
        return

    print(f"Building {len(stale)} of {len(MODELS)} models:")
    for name, reason in sorted(stale):
        print(f"  {name}  ({reason})")
    if args.list:
        return

    order = _order(stale, stamps)
    jobs = max(1, min(args.jobs, len(order)))
    print(f"\nUsing {jobs} process(es).\n")

    failures = []
    done = 0
    # ``spawn`` rather than ``fork``: the parent has not imported OCP at this
    # point and should not inherit a copy of it into every worker.
    with mp.get_context("spawn").Pool(jobs) as pool:
        for result in pool.imap_unordered(_build, order):
            done += 1
            name = result["name"]
            if "error" in result:
                failures.append(result)
                print(f"[{done}/{len(order)}] FAILED {name}")
                continue
            stamps[name] = {
                "fingerprint": model_deps.fingerprint(name),
                "seconds": round(result["seconds"], 3),
                "outputs": result["outputs"],
            }
            # Persist as we go: a run killed halfway keeps credit for the models
            # it did finish, so the next one resumes instead of starting over.
            _save_stamps(stamps)
            print(f"[{done}/{len(order)}] {name} ({result['seconds']:.1f}s)")

    if failures:
        print(f"\n{len(failures)} model(s) failed:\n", file=sys.stderr)
        for failure in failures:
            print(f"--- {failure['name']} ---\n{failure['error']}", file=sys.stderr)
        sys.exit(1)
    print("\nDone!")


if __name__ == "__main__":
    main()
