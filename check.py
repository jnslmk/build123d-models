"""Run a model's geometry assertions by name, and fail the shell on a bad part.

Ribs, wall gaps and fit clearances are invisible in a projection, so models
verify themselves in code. This is the one entry point that runs those
assertions and, crucially, **exits non-zero** when they fail -- so a check is
something CI or a pre-commit hook can hold you to, not something you have to
remember to eyeball.

Discovery, in order:

1. ``models.<name>`` is a package with a ``checks`` submodule exposing
   ``main()``  -- the convention for a model big enough to earn its own package.
2. ``models.<name>`` exposes ``check()``  -- the convention for a single-file
   model.
3. Neither -- say so plainly and exit 0. A model without checks is not a
   failure, and reporting it as one would train people to ignore this command.

``--json <path>`` additionally writes every assertion -- its section, name,
pass/fail and (free-text) measured/expected detail -- to ``path`` as JSON,
alongside the usual printed output and exit code. The idea is adapted from
cyberchitta/cad-khana (https://github.com/cyberchitta/cad-khana, Apache-2.0
licensed), whose ``khana check`` writes a structured ``mechanism.json``
reporting interferences, clearances and every assertion's result, diffable
with ``khana diff <old> <new>``. ``check_diff.py`` is this repo's counterpart
to that ``diff`` command, comparing two ``--json`` reports.

Without ``--json``, behaviour is unchanged from before this was added for every
``check()`` shape except one: a single-file ``check()`` that returns a
``models.lib.checks.Report`` is rendered and exits 1 on any failure, with or
without ``--json`` -- the same rule ``checks.main()`` already applies to a
package. ``None``/``False``/a raised ``AssertionError`` keep their original
discovery order, stdout and exit codes.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_model(name: str) -> ModuleType:
    """Import ``models.<name>``, telling 'no such model' apart from a broken one.

    A ModuleNotFoundError raised *inside* the model (a typo'd import, a missing
    dependency) must not be reported as "model not found" -- that sends you
    looking in the wrong place entirely.
    """
    try:
        return importlib.import_module(f"models.{name}")
    except ModuleNotFoundError as exc:
        if exc.name in (f"models.{name}", "models"):
            print(f"Model '{name}' not found in models/")
            sys.exit(1)
        raise


def _checks_submodule(module: ModuleType, name: str) -> ModuleType | None:
    """The model's own ``checks`` submodule, if it is a package and has one."""
    if not hasattr(module, "__path__"):
        return None
    if importlib.util.find_spec(f"models.{name}.checks") is None:
        return None
    return importlib.import_module(f"models.{name}.checks")


def _write_json(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2) + "\n")


def _run_package_checks_json(name: str, checks: ModuleType, json_path: str) -> None:
    """``--json`` path for a package's ``checks`` submodule.

    Prefers ``run() -> Report`` (both existing ``checks.py`` files split their
    ``main()`` into exactly this plus printing + ``sys.exit``), which gives the
    full per-assertion structure via ``Report.entries`` with no changes to the
    model's own checks needed. A ``checks.py`` with only ``main()`` cannot be
    captured this way; it still runs correctly, just without structured detail.
    """
    run_fn = getattr(checks, "run", None)
    if callable(run_fn):
        report = run_fn()
        print(report.render())
        _write_json(json_path, {"model": name, **report.to_dict()})
        sys.exit(1 if report.failures else 0)

    _write_json(
        json_path,
        {
            "model": name,
            "status": "unsupported",
            "note": (
                f"models.{name}.checks has main() but no run() -> Report, so "
                "per-assertion detail could not be captured"
            ),
            "assertions": [],
            "passed": 0,
            "failed": 0,
        },
    )
    checks.main()


def _run_check_fn_json(name: str, fn, json_path: str) -> None:
    """``--json`` path for a single-file model's ``check()``.

    A ``check()`` that returns a ``models.lib.checks.Report`` -- the same
    instrumentation a package's ``run()`` uses -- is captured with full
    per-assertion detail, exactly like ``_run_package_checks_json`` above: same
    ``render()`` to stdout, same ``{"model": name, **report.to_dict()}`` JSON
    shape, same "failures means exit 1" rule. This is what lets a tier-1
    model's ``check()`` grow real assertions without becoming a package just
    to get structured ``--json`` output.

    One that returns ``None``/``False`` or raises -- the only shapes a
    single-file ``check()`` has ever had before this -- is still recorded as a
    single synthetic assertion, unchanged.
    """
    try:
        result = fn()
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        entry = {"section": "", "name": "check()", "passed": False, "detail": str(exc)}
        _write_json(
            json_path, {"model": name, "assertions": [entry], "passed": 0, "failed": 1}
        )
        sys.exit(1)

    # Imported here, not at module scope: by this point `fn` (the model's own
    # check()) has already run, which means the model module -- and therefore
    # build123d/OCP, which models.lib.checks itself imports -- is already in
    # sys.modules. A module-scope import would pay that ~2s cost on every
    # invocation of this CLI, including the "model not found"/"no checks
    # defined" paths that never touch a Report at all.
    from models.lib.checks import Report

    if isinstance(result, Report):
        print(result.render())
        _write_json(json_path, {"model": name, **result.to_dict()})
        sys.exit(1 if result.failures else 0)

    ok = result is not False
    entry = {"section": "", "name": "check()", "passed": ok, "detail": ""}
    _write_json(
        json_path,
        {
            "model": name,
            "assertions": [entry],
            "passed": 1 if ok else 0,
            "failed": 0 if ok else 1,
        },
    )
    sys.exit(0 if ok else 1)


def main() -> None:
    argv = sys.argv[1:]
    json_path: str | None = None
    if "--json" in argv:
        i = argv.index("--json")
        if i + 1 >= len(argv):
            print("Usage: uv run check <name> [--json <path>]")
            sys.exit(1)
        json_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2 :]

    if len(argv) < 1:
        print("Usage: uv run check <name>")
        print("Example: uv run check led_psu_enclosure")
        sys.exit(1)

    name = argv[0]
    module = _load_model(name)

    checks = _checks_submodule(module, name)
    if checks is not None and callable(getattr(checks, "main", None)):
        if json_path is not None:
            _run_package_checks_json(name, checks, json_path)
            return
        # Its main() owns the exit code (it knows how many assertions failed).
        checks.main()
        return

    fn = getattr(module, "check", None)
    if callable(fn):
        if json_path is not None:
            _run_check_fn_json(name, fn, json_path)
            return
        try:
            result = fn()
        except AssertionError as exc:
            print(f"FAILED: {exc}")
            sys.exit(1)
        # Local import for the same reason as in _run_check_fn_json: deferred
        # until after fn() has run, so this never pays build123d/OCP's ~2s
        # import cost on a path that doesn't return a Report.
        from models.lib.checks import Report

        if isinstance(result, Report):
            # Same rule as the package path (checks.main(), above): render
            # every assertion and let its own failures decide the exit code.
            # Without this, a Report with failures is merely truthy -- not
            # `False` -- and this would silently report success.
            print(result.render())
            sys.exit(1 if result.failures else 0)
        sys.exit(1 if result is False else 0)

    print(f"Model '{name}' has no checks defined (no checks.main(), no check()).")
    if json_path is not None:
        _write_json(
            json_path,
            {
                "model": name,
                "status": "no_checks",
                "assertions": [],
                "passed": 0,
                "failed": 0,
            },
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
