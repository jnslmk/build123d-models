"""Export a model by name to STL, STEP and GLB.

STEP is written by default, which is what ``AGENTS.md`` documents and what
``main.py`` (and so CI, and so the website's download buttons) has always done
with ``step=True``. It used to be opt-in behind ``--step`` here and nowhere
else, so a local ``uv run export`` quietly produced a different set of files
from the build that ships -- visible as a missing STEP download in a locally
built manifest. ``--step`` is still accepted, and now means what it says.
"""

import importlib
import sys

from export import export

USAGE = "Usage: uv run export <name> [--no-step]\nExample: uv run export lens_cap"


def main() -> None:
    argv = sys.argv[1:]
    # ``--step`` is the old opt-in flag, kept working now that it is the
    # default; ``--no-step`` is the way to skip it.
    step = "--no-step" not in argv
    args = [a for a in argv if not a.startswith("-")]
    unknown = [a for a in argv if a.startswith("-") and a not in ("--step", "--no-step")]

    if not args or unknown:
        if unknown:
            print(f"Unknown option(s): {' '.join(unknown)}")
        print(USAGE)
        sys.exit(1)

    name = args[0]
    target = f"models.{name}"
    try:
        module = importlib.import_module(target)
    except ModuleNotFoundError as exc:
        # Only claim the model is missing when it is the model that is missing.
        # This used to wrap create() and export() as well, so a bad import
        # *inside* a model reported "not found in models/" and sent the reader
        # looking for a file that was right there.
        missing = exc.name or ""
        if target == missing or target.startswith(f"{missing}."):
            print(f"Model '{name}' not found in models/")
            sys.exit(1)
        raise

    export(module.create(), name, step=step)


if __name__ == "__main__":
    main()
