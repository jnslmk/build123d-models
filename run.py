"""Run a model by name."""

import importlib
import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run model <name>")
        print("Example: uv run model cube")
        sys.exit(1)

    name = sys.argv[1]
    try:
        module = importlib.import_module(f"models.{name}")
        module.main()
    except ModuleNotFoundError:
        print(f"Model '{name}' not found in models/")
        sys.exit(1)


if __name__ == "__main__":
    main()
