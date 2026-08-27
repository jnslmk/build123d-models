"""Modular 24 V addressable COB linear lamp system.

Daisy-chainable 1.5 m lamps built on an aluminium T8 profile with 3D printed
endcaps, an internal ESP32 + power-distribution PCB, and industrial-style
wiring throughout (SP16/SP17 connectors, LAPP ÖLFLEX CLASSIC 110 cable, M12
glands). Native 24 V operation; USB-C PD is an optional standalone input.

The system specification lives in ``README.md`` in this package. What exists so
far is the hardware the printed parts have to fit: the aluminium profile, its
snap-in diffuser and the COB strip, reconstructed from calipers in
``config.py``. Printed parts (endcaps, PCB mount, mounting hardware) are added
alongside as they get designed.

    uv run show led_profiles                # the full 1.5 m lamp, caps on
    uv run show led_profiles.corner         # one part; also .strap .stand .feet
    uv run show led_profiles.assemblies.triangle   # 3 lamps, 3 corners, 12 straps
    uv run show led_profiles.assemblies.standing   # upright on the tripod stand
    uv run show led_profiles.assemblies.suspended  # hung from two eye feet
    uv run export led_profiles.corner       # STLs for the slicer, a part at a time
    uv run check led_profiles               # hold it all to its measurements
"""

from . import config, mount_config
from .assemblies import create_standing, create_suspended, create_triangle
from .assembly import PARAMS, create, create_bare, create_print_layout, create_section
from .corner import create_corner
from .cradle import create_cradle
from .endcap import create_endcap
from .feet import create_eye_foot, create_wall_foot
from .gland import create_cable, create_gland
from .profile import create_diffuser, create_extrusion, create_strip
from .stand import create_post
from .stand.keeper import create_keeper
from .stand.leg import create_leg
from .strain_relief import create_strain_relief
from .strap import create_strap

# ``create()`` is a finished lamp: bought aluminium, bought diffuser, the COB
# strip, and both endcaps in place. Nothing about that mesh is a print job, so
# the website offers no STL/STEP for it -- the printed parts have their own
# models. Same for every scene under ``assemblies/``. See
# tessellate_models.model_is_assembly.
IS_ASSEMBLY = True

__all__ = [
    "IS_ASSEMBLY",
    "PARAMS",
    "config",
    "create",
    "create_bare",
    "create_cable",
    "create_corner",
    "create_cradle",
    "create_diffuser",
    "create_endcap",
    "create_extrusion",
    "create_eye_foot",
    "create_gland",
    "create_print_layout",
    "create_section",
    "create_keeper",
    "create_leg",
    "create_post",
    "create_standing",
    "create_strain_relief",
    "create_strap",
    "create_strip",
    "create_suspended",
    "create_triangle",
    "create_wall_foot",
    "mount_config",
]
