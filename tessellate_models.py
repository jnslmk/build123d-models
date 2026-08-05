"""Model registry + loader shared by the web-bundle builder (website.py) and CI.

Historically this also tessellated models for three-cad-viewer; that pipeline is
gone (the site now runs build123d in-browser via Pyodide), but the module name is
kept because callers import ``MODELS`` / ``model_params`` / ``get_part`` from it.
"""

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import importlib

# The model roster the website + CI expose. Single source of truth; main.py's
# BUILDERS mirrors this list.
#
# A name is a **module path under ``models``**, so a package's parts can be
# listed individually: ``led_profiles`` is the whole lamp, ``led_profiles.stand``
# is one printed part. Everything downstream derives from that -- ``_module``
# imports it, ``website._manifest`` turns the dots into the source file's own
# path, and the exports land under the dotted name. Only modules with a zero-arg
# ``create()`` belong here; the shared pieces a part is built from
# (``led_profiles.cradle``, ``models.lib``) are not models.
MODELS = [
    "cube",
    "door_latch",
    "drill_fit_tester",
    "drill_fit_tester_plain",
    "drill_fit_tester_taper",
    "drill_storage_gridfinity",
    "drill_storage_hex",
    "drill_storage_metal",
    "drill_storage_wood",
    "drill_storage_wood_assembly",
    "led_profiles",
    "led_profiles.printable",
    "led_profiles.endcap",
    "led_profiles.corner",
    "led_profiles.strap",
    "led_profiles.stand",
    "led_profiles.feet",
    "led_psu_enclosure",
    "lens_cap",
    "satellite_led",
    "slotted_plate",
    "spiral_vase_lampshade",
    "wall_bar_lamp",
]


def _module(name: str):
    return importlib.import_module(f"models.{name}")


def model_params(name: str) -> list[dict]:
    """UI schema for a model's parameters, or [] if it isn't parametric.

    A parametric model module exposes a module-level ``PARAMS`` list of dicts with
    keys ``name``, ``label``, ``type``, ``min``, ``max``, ``step``, ``default`` and
    a matching ``create(**kwargs)`` signature.
    """
    return list(getattr(_module(name), "PARAMS", []))


def get_part(name: str, params: dict | None = None):
    """Build a model part, optionally with parameters."""
    create = _module(name).create
    return create(**params) if params else create()
