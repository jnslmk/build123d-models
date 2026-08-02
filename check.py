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
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run check <name>")
        print("Example: uv run check led_psu_enclosure")
        sys.exit(1)

    name = sys.argv[1]
    module = _load_model(name)

    checks = _checks_submodule(module, name)
    if checks is not None and callable(getattr(checks, "main", None)):
        # Its main() owns the exit code (it knows how many assertions failed).
        checks.main()
        return

    fn = getattr(module, "check", None)
    if callable(fn):
        try:
            result = fn()
        except AssertionError as exc:
            print(f"FAILED: {exc}")
            sys.exit(1)
        sys.exit(1 if result is False else 0)

    print(f"Model '{name}' has no checks defined (no checks.main(), no check()).")
    sys.exit(0)


if __name__ == "__main__":
    main()
