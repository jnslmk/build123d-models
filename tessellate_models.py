"""Model registry + loader shared by the web-bundle builder (website.py) and CI.

Historically this also tessellated models for three-cad-viewer; that pipeline is
gone (the site now runs build123d in-browser via Pyodide), but the module name is
kept because callers import ``MODELS`` / ``model_params`` / ``get_part`` from it.
"""

import fontfix  # noqa: F401 -- preload system libfontconfig before OCP imports

import importlib

# The model roster the website + CI expose. The **single** source of truth:
# ``main.py`` builds straight from this list rather than keeping its own copy.
#
# A name is a **module path under ``models``**, so a package's parts and scenes
# can be listed individually: ``led_profiles`` is the whole lamp,
# ``led_profiles.stand`` is one printed part, ``led_profiles.assemblies.standing``
# is one way of mounting it. Everything downstream derives from that --
# ``_module`` imports it, ``website._manifest`` turns the dots into the source
# file's own path, and the exports land under the dotted name. Only modules with
# a zero-arg ``create()`` belong here; the shared pieces a part is built from
# (``led_profiles.cradle``, ``drill_storage.box``, ``models.lib``) are not models.
MODELS = [
    "cube",
    "door_latch",
    # Fit coupons: three ways of cutting a bore, then three sweeps that settle
    # the number it is cut at. See models/drill_fit_tester/__init__.py.
    "drill_fit_tester",
    "drill_fit_tester.plain",
    "drill_fit_tester.taper",
    "drill_fit_tester.sweep",
    "drill_fit_tester.small",
    "drill_fit_tester.full",
    # One Gridfinity base/cover engine, one holder per tool set, plus the scene
    # that proves a drill fits inside.
    "drill_storage",
    "drill_storage.wood",
    "drill_storage.metal",
    "drill_storage.hex",
    "drill_storage.assemblies.wood",
    # The lamp system: the whole stick, the three ways it gets mounted, and
    # each printed part on its own in print pose.
    "led_profiles",
    "led_profiles.assemblies.triangle",
    "led_profiles.assemblies.standing",
    "led_profiles.assemblies.suspended",
    "led_profiles.endcap",
    "led_profiles.corner",
    "led_profiles.strap",
    "led_profiles.stand",
    "led_profiles.feet",
    # The enclosure: the assembled scene, the slicer layout, and every printed
    # part on its own.
    "led_psu_enclosure",
    "led_psu_enclosure.printable",
    "led_psu_enclosure.tray",
    "led_psu_enclosure.lid",
    "led_psu_enclosure.shelf",
    "led_psu_enclosure.plate",
    "led_psu_enclosure.vent",
    "led_psu_enclosure.gasket",
    "lens_cap",
    "round_snap_box",
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


def model_is_assembly(name: str) -> bool:
    """True if this model is a *scene* rather than something you print.

    An assembly view shows parts in their use pose, usually with bought
    hardware among them -- the lamp in its tripod, the enclosure with its PSU
    mocked up inside. Its mesh is not a print job and its B-rep is not the
    geometry of record for any one part, so the website offers no STL/STEP
    download for it; the per-part models next to it are what you download.

    Declared per module as ``IS_ASSEMBLY = True``, the same way a parametric
    model declares ``PARAMS``, so the fact lives with the model rather than in
    a list here that would drift. Absent means a printable part -- the common
    case, including multi-part *print layouts* like ``drill_storage.wood``
    (base and cover, side by side on the bed), which are downloadable.
    """
    return bool(getattr(_module(name), "IS_ASSEMBLY", False))


def get_part(name: str, params: dict | None = None):
    """Build a model part, optionally with parameters."""
    create = _module(name).create
    return create(**params) if params else create()
