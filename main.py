"""Build all models and export them."""

from export import export
from models.cube import create as create_cube
from models.satellite_led import create as create_satellite_led


def main() -> None:
    """Build and export all models."""
    print("Building all models...")
    export(create_cube(), "cube")
    export(create_satellite_led(), "satellite_led")
    print("Done!")


if __name__ == "__main__":
    main()
