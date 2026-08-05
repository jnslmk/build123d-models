"""Build all models and export them to STL + STEP."""

from export import export
from models.cube import create as create_cube
from models.door_latch import create as create_door_latch
from models.drill_fit_tester import create as create_drill_fit_tester
from models.drill_fit_tester_plain import create as create_drill_fit_tester_plain
from models.drill_fit_tester_taper import create as create_drill_fit_tester_taper
from models.drill_storage_gridfinity import create as create_drill_storage_gridfinity
from models.drill_storage_hex import create as create_drill_storage_hex
from models.drill_storage_metal import create as create_drill_storage_metal
from models.drill_storage_wood import create as create_drill_storage_wood
from models.drill_storage_wood_assembly import (
    create as create_drill_storage_wood_assembly,
)
from models.led_profiles import create as create_led_profiles
from models.led_profiles.assemblies.standing import (
    create as create_led_profiles_standing,
)
from models.led_profiles.assemblies.suspended import (
    create as create_led_profiles_suspended,
)
from models.led_profiles.assemblies.triangle import (
    create as create_led_profiles_triangle,
)
from models.led_profiles.corner import create as create_led_profiles_corner
from models.led_profiles.endcap import create as create_led_profiles_endcap
from models.led_profiles.feet import create as create_led_profiles_feet
from models.led_profiles.stand import create as create_led_profiles_stand
from models.led_profiles.strap import create as create_led_profiles_strap
from models.led_psu_enclosure import create as create_led_psu_enclosure
from models.lens_cap import create as create_lens_cap
from models.satellite_led import create as create_satellite_led
from models.slotted_plate import create as create_slotted_plate
from models.spiral_vase_lampshade import create as create_spiral_vase_lampshade
from models.wall_bar_lamp import create as create_wall_bar_lamp

# name -> zero-arg builder. This is the single source of truth for the model
# roster the website and CI consume (mirror of tessellate_models.MODELS).
BUILDERS = {
    "cube": create_cube,
    "door_latch": create_door_latch,
    "drill_fit_tester": create_drill_fit_tester,
    "drill_fit_tester_plain": create_drill_fit_tester_plain,
    "drill_fit_tester_taper": create_drill_fit_tester_taper,
    "drill_storage_gridfinity": create_drill_storage_gridfinity,
    "drill_storage_hex": create_drill_storage_hex,
    "drill_storage_metal": create_drill_storage_metal,
    "drill_storage_wood": create_drill_storage_wood,
    "drill_storage_wood_assembly": create_drill_storage_wood_assembly,
    # The lamp system: the whole stick, the three ways it gets mounted, and
    # each printed part on its own in print pose. Keys are module paths under
    # ``models``, matching tessellate_models.MODELS -- see its comment.
    "led_profiles": create_led_profiles,
    "led_profiles.assemblies.triangle": create_led_profiles_triangle,
    "led_profiles.assemblies.standing": create_led_profiles_standing,
    "led_profiles.assemblies.suspended": create_led_profiles_suspended,
    "led_profiles.endcap": create_led_profiles_endcap,
    "led_profiles.corner": create_led_profiles_corner,
    "led_profiles.strap": create_led_profiles_strap,
    "led_profiles.stand": create_led_profiles_stand,
    "led_profiles.feet": create_led_profiles_feet,
    "led_psu_enclosure": create_led_psu_enclosure,
    "lens_cap": create_lens_cap,
    "satellite_led": create_satellite_led,
    "slotted_plate": create_slotted_plate,
    "spiral_vase_lampshade": create_spiral_vase_lampshade,
    "wall_bar_lamp": create_wall_bar_lamp,
}


def main() -> None:
    """Build and export every model to STL + STEP."""
    print("Building all models...")
    for name, build in BUILDERS.items():
        export(build(), name, step=True)
    print("Done!")


if __name__ == "__main__":
    main()
