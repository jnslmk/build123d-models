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
    # 180 mm spool for a coiled patch cable: three identical discs on one hub,
    # plus the rim clip that holds them together. The discs are a
    # reconstruction of Printables 27496; the clip is a redesign, because the
    # original's falls off.
    "cable_spool",
    "cable_spool.base",
    "cable_spool.middle",
    "cable_spool.cover",
    "cable_spool.clip",
    "door_latch",
    # Gridfinity drill storage: the family view, then one variant per tool set.
    # A variant is an assembled scene plus its three printed parts -- ASA base,
    # TPU cartridge, PETG cover -- which are three filaments and so three jobs.
    # ``allen`` is the 8-piece hex-key box and ``hex`` the 16-piece driver-bit
    # box: both 1x1 Gridfinity, cut from the same hex geometry (BITS shaves its
    # lead-in clearances), each a rigid base + TPU insert + translucent cover.
    "drill_storage",
    "drill_storage.wood",
    "drill_storage.wood.base",
    "drill_storage.wood.insert",
    "drill_storage.wood.cover",
    "drill_storage.metal",
    "drill_storage.metal.base",
    "drill_storage.metal.insert",
    "drill_storage.metal.cover",
    "drill_storage.stone",
    "drill_storage.stone.base",
    "drill_storage.stone.insert",
    "drill_storage.stone.cover",
    "drill_storage.allen",
    "drill_storage.allen.base",
    "drill_storage.allen.insert",
    "drill_storage.allen.cover",
    "drill_storage.hex",
    "drill_storage.hex.bits.base",
    "drill_storage.hex.bits.insert",
    "drill_storage.hex.bits.cover",
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
    "led_profiles.stand.leg",
    "led_profiles.stand.keeper",
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
    # Wall-mounted cradle for the round Sonicare charging puck, taped to tile.
    # Closed in front; the cable route is the only opening in the shell.
    "sonicare_charger_holder",
    # The salad-bowl pendant: the hung lamp, the printed grille that is the only
    # print job in it, the grille's outer band on its own as a fit test, and the
    # bought bowl the grille is fitted to.
    "salad_bowl_lamp",
    "salad_bowl_lamp.shade",
    "salad_bowl_lamp.fit_test",
    "salad_bowl_lamp.bowl",
    "round_snap_box",
    "spiral_vase_lampshade",
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
