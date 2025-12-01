"""Build all models and export them."""

from models.cube import main as build_cube


def main() -> None:
    """Build and export all models."""
    print("Building all models...")
    build_cube()
    print("Done!")


if __name__ == "__main__":
    main()
