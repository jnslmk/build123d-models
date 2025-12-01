"""Run a model by name."""

import importlib
import sys

from export import display_and_export
from viewer import ensure_server


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run model <name>")
        print("Example: uv run model cube")
        sys.exit(1)

    name = sys.argv[1]

    # Start viewer if not running (stays open after script exits)
    if ensure_server():
        print("Started viewer in background")

    try:
        module = importlib.import_module(f"models.{name}")
        part = module.create()
        display_and_export(part, name)
    except ModuleNotFoundError:
        print(f"Model '{name}' not found in models/")
        sys.exit(1)


if __name__ == "__main__":
    main()
