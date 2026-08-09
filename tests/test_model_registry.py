"""A model that is not on the website is a model nobody can find.

``AGENTS.md`` already says how to register one -- add the name to
``tessellate_models.MODELS`` -- and saying it is not the same as enforcing it.
Nothing about a forgotten registration looks wrong: the module imports, its
checks pass, ``uv run show`` and ``uv run export`` both work by name, and the
model is simply absent from the site and from CI's build. The same is true one
level down, where a package missing from ``[tool.setuptools] packages`` ships a
wheel without it -- which ``pyproject.toml`` warns about in a comment that, like
any comment, only helps somebody already reading it.

So this is the ``sharp_convex_edges`` treatment applied to the roster: turn the
prose rule into something a runner fails on. The shape is deliberately the same
as that check's, and for the same reason. Exceptions are real -- not every
``create()`` under ``models/`` is a model -- so they are **named here with a
reason** rather than quietly left out. An unregistered module is fine; an
unregistered module nobody has explained is the bug this file exists to catch.

Everything below is a static AST read. No model is imported, so the suite pays
none of the OCP cost and this stays a sub-second test.
"""

from __future__ import annotations

import ast
import tomllib
import unittest
from pathlib import Path

import website
from tessellate_models import MODELS

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

# Modules that expose a zero-arg ``create()`` and are deliberately **not**
# models. Each entry needs a reason, and ``test_every_excuse_is_still_true``
# fails if one goes stale -- an allow-list nobody prunes is how a real omission
# hides behind a legitimate one.
NOT_A_MODEL = {
    "led_profiles.cradle": (
        "shared geometry, not a view: the trough every mount in the family "
        "grips the tube with. AGENTS.md names it explicitly under 'the shared "
        "pieces a part is built from ... are not models'."
    ),
}


def _model_name(path: Path) -> str:
    """``models/led_profiles/stand.py`` -> ``led_profiles.stand``; a package's
    ``__init__.py`` -> the package's own name."""
    rel = path.relative_to(MODELS_DIR)
    parts = rel.parent.parts if rel.name == "__init__.py" else (*rel.parent.parts, rel.stem)
    return ".".join(parts)


def _module_paths() -> list[Path]:
    """Every module under ``models/`` that could be a model.

    ``models/lib/`` and ``models/__init__.py`` are excluded by definition:
    AGENTS.md places shared helpers there precisely so they are not models.
    """
    out = []
    for py in sorted(MODELS_DIR.rglob("*.py")):
        rel = py.relative_to(MODELS_DIR)
        if rel.parts[0] == "lib" or rel == Path("__init__.py"):
            continue
        if "__pycache__" in rel.parts:
            continue
        out.append(py)
    return out


def _exposes_zero_arg_create(path: Path) -> bool:
    """Does this module offer ``create()`` callable with no arguments?

    Three ways to offer one, and all three count, because all three are what
    ``tessellate_models.get_part`` will find: defining it, re-exporting it from
    a sibling (how every package's ``__init__.py`` does it), or binding it to a
    name. ``**params`` is zero-arg for this purpose -- that is the signature the
    parametric models use.
    """
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "create":
            args = node.args
            positional = args.posonlyargs + args.args
            if len(positional) - len(args.defaults) > 0:
                return False
            return all(d is not None for d in args.kw_defaults)
        if isinstance(node, ast.ImportFrom) and any(a.asname == "create" or (a.asname is None and a.name == "create") for a in node.names):
            return True
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "create" for t in node.targets
        ):
            return True
    return False


def _reexport_sources(package_init: Path) -> set[str]:
    """Sibling modules a package's ``__init__.py`` takes its ``create`` from.

    ``led_psu_enclosure/__init__.py`` does ``from .assembly import create``, so
    ``led_psu_enclosure.assembly`` is already on the website -- under the
    package's name. Detected rather than allow-listed, so the next package with
    an ``assembly.py`` needs no new entry here.
    """
    tree = ast.parse(package_init.read_text())
    pkg = _model_name(package_init)
    out = set()
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.level or not node.module:
            continue
        if any(a.name == "create" for a in node.names):
            out.add(f"{pkg}.{node.module}")
    return out


def _already_reachable() -> set[str]:
    return {
        src
        for init in MODELS_DIR.rglob("__init__.py")
        if "__pycache__" not in init.parts and init != MODELS_DIR / "__init__.py"
        for src in _reexport_sources(init)
    }


class RosterTests(unittest.TestCase):
    def test_every_model_is_registered(self) -> None:
        """The one that would have caught a model built but never put on the site."""
        reachable = _already_reachable()
        roster = set(MODELS)
        unregistered = []
        for py in _module_paths():
            name = _model_name(py)
            if not _exposes_zero_arg_create(py):
                continue
            if name in roster or name in reachable or name in NOT_A_MODEL:
                continue
            unregistered.append(name)
        self.assertEqual(
            [],
            sorted(unregistered),
            "These modules offer a zero-arg create() but are not in "
            "tessellate_models.MODELS, so they exist for `uv run show` and for "
            "nothing else -- no website entry, no CI build, no download. Add "
            "each to MODELS, or add it to NOT_A_MODEL above with the reason it "
            "is not a model.",
        )

    def test_every_registered_name_resolves(self) -> None:
        """Catches a typo in the roster, which the website swallows silently."""
        broken = []
        for name in MODELS:
            flat = MODELS_DIR / f"{name.replace('.', '/')}.py"
            pkg = MODELS_DIR / name.replace(".", "/") / "__init__.py"
            path = flat if flat.exists() else pkg
            if not path.exists() or not _exposes_zero_arg_create(path):
                broken.append(name)
        self.assertEqual(
            [], sorted(broken),
            "In MODELS but has no module with a zero-arg create(). This is the "
            "check that has to catch it: website._source_path now raises on an "
            "unresolvable name, so the alternative to failing here is failing "
            "the site build with what reads like a website bug.",
        )

    def test_source_path_refuses_a_name_it_cannot_resolve(self) -> None:
        """Pins the raise, so nobody restores the silent fallback by accident."""
        with self.assertRaises(FileNotFoundError):
            website._source_path("no_such_model_anywhere")
        # ...and still resolves both shapes of real model.
        self.assertEqual(website._source_path("lens_cap"), "models/lens_cap.py")
        self.assertEqual(
            website._source_path("sonicare_charger_holder"),
            "models/sonicare_charger_holder/__init__.py",
        )

    def test_every_model_package_ships_in_the_wheel(self) -> None:
        cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())
        declared = set(cfg["tool"]["setuptools"]["packages"])
        on_disk = {
            "models." + ".".join(init.relative_to(MODELS_DIR).parent.parts)
            if init != MODELS_DIR / "__init__.py"
            else "models"
            for init in MODELS_DIR.rglob("__init__.py")
            if "__pycache__" not in init.parts
        }
        self.assertEqual(
            set(), on_disk - declared,
            "Package directories under models/ that are missing from "
            "[tool.setuptools] packages. Subpackages are not implied by their "
            "parent, so a built wheel ships without them.",
        )

    def test_website_offers_every_model_its_own_source(self) -> None:
        """The webapp guarantee, asserted end to end rather than assumed."""
        manifest = {m["name"]: m for m in website._manifest()["models"]}
        self.assertEqual(set(MODELS), set(manifest))
        missing_source = [
            name for name, m in manifest.items() if not (ROOT / m["source"]).exists()
        ]
        self.assertEqual(
            [], sorted(missing_source),
            "Manifest entries whose 'source' path does not exist -- the Code "
            "panel shows 'source unavailable' for these.",
        )

    def test_every_excuse_is_still_true(self) -> None:
        """Prune the allow-list, or it starts hiding real omissions."""
        for name, reason in NOT_A_MODEL.items():
            with self.subTest(module=name):
                flat = MODELS_DIR / f"{name.replace('.', '/')}.py"
                pkg = MODELS_DIR / name.replace(".", "/") / "__init__.py"
                path = flat if flat.exists() else pkg
                self.assertTrue(path.exists(), f"{name} no longer exists; drop the entry")
                self.assertTrue(
                    _exposes_zero_arg_create(path),
                    f"{name} no longer has a zero-arg create(); the entry is dead",
                )
                self.assertNotIn(
                    name, set(MODELS), f"{name} is now registered; drop the entry"
                )
                self.assertGreater(len(reason), 40, f"{name} needs a real reason")


if __name__ == "__main__":
    unittest.main()
