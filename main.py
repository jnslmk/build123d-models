"""Build all models and export them."""

from export import export
from models.cube import create as create_cube


def main() -> None:
    """Build and export all models."""
    print("Building all models...")
    export(create_cube(), "cube")
    print("Done!")


if __name__ == "__main__":
    main()
