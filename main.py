"""Build all models and export them."""

from export import export
from models.cube import create as create_cube
from models.door_latch import create as create_door_latch
from models.lens_cap import create as create_lens_cap
from models.satellite_led import create as create_satellite_led
from models.slotted_plate import create as create_slotted_plate
from models.spiral_vase_lampshade import create as create_spiral_vase_lampshade
from models.wall_bar_lamp import create as create_wall_bar_lamp


def main() -> None:
    """Build and export all models."""
    print("Building all models...")
    export(create_cube(), "cube")
    export(create_door_latch(), "door_latch")
    export(create_lens_cap(), "lens_cap")
    export(create_satellite_led(), "satellite_led")
    export(create_slotted_plate(), "slotted_plate")
    export(create_spiral_vase_lampshade(), "spiral_vase_lampshade")
    export(create_wall_bar_lamp(), "wall_bar_lamp")
    print("Done!")


if __name__ == "__main__":
    main()
