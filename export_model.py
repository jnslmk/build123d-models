"""Export a model by name to STEP and STL."""

import importlib
import sys

from export import export


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--step"]
    step = "--step" in sys.argv[1:]

    if not args:
        print("Usage: uv run export <name> [--step]")
        print("Example: uv run export lens_cap")
        sys.exit(1)

    name = args[0]

    try:
        module = importlib.import_module(f"models.{name}")
        part = module.create()
        export(part, name, step=step)
    except ModuleNotFoundError:
        print(f"Model '{name}' not found in models/")
        sys.exit(1)


if __name__ == "__main__":
    main()
