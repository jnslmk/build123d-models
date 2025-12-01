"""Export a model by name to STEP and STL."""

import importlib
import sys

from export import export


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run export <name>")
        print("Example: uv run export cube")
        sys.exit(1)

    name = sys.argv[1]

    try:
        module = importlib.import_module(f"models.{name}")
        part = module.create()
        export(part, name)
    except ModuleNotFoundError:
        print(f"Model '{name}' not found in models/")
        sys.exit(1)


if __name__ == "__main__":
    main()
