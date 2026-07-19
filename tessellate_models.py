"""Model registry + loader shared by the web-bundle builder (website.py) and CI.

Historically this also tessellated models for three-cad-viewer; that pipeline is
gone (the site now runs build123d in-browser via Pyodide), but the module name is
kept because callers import ``MODELS`` / ``model_params`` / ``get_part`` from it.
"""

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import importlib

# The model roster the website + CI expose. Single source of truth; main.py's
# BUILDERS mirrors this list.
MODELS = [
    "cube",
    "door_latch",
    "drill_fit_tester",
    "drill_fit_tester_plain",
    "drill_fit_tester_taper",
    "drill_storage_gridfinity",
    "drill_storage_metal",
    "drill_storage_wood",
    "drill_storage_wood_assembly",
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
