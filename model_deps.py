"""Which files a model is built from, and what changing a file can reach.

``AGENTS.md`` tells you to rebuild "the model you changed *and everything that
imports what you changed*", and to find that family by ``grep`` rather than from
memory. This module is that grep, done properly: it walks the import graph
instead of matching text, so it cannot miss the ``from ..box import`` one level
down or the cross-package ``from ..drill_storage.box import`` that a coupon uses
to reach another family.

Two things are built on top of it:

* ``main.py`` fingerprints each model and rebuilds only the ones whose own
  sources moved, which is what makes an incremental build safe.
* ``uv run deps <path>`` answers "what do I have to re-check after editing
  this?" from the shell.

**The graph is deliberately over-approximate.** It records every ``models.*``
module a model's source can reach, without asking whether the imported name is
actually used to build geometry. An unused import therefore rebuilds more than
strictly necessary -- which costs time, never correctness. The failure that
matters is the other one, and it is the reason this is a real import walk: a
missed edge ships a stale STL that nobody looks at again.

Two limits worth knowing, both of which fail *safe* only because
``GLOBAL_INPUTS`` catches them:

* Only ``import``/``from ... import`` are followed. Nothing in ``models/`` uses
  ``importlib`` or ``__import__``, and a model that started to would need adding
  here.
* Only Python sources count. No model reads a data file at build time (fonts
  come from the system, via ``fontfix``), so there is nothing else to hash.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
MODELS_DIR = ROOT / "models"

# Files that feed *every* model's output, so a change to one invalidates the
# whole roster. These are the build's own inputs rather than any one model's:
# the exporter (tolerances, which formats get written), the font preload that
# runs before OCP imports, the roster and loader, the driver that decides how
# ``export`` is called, this module (it defines what a fingerprint *means*), and
# the lockfile that pins the OCC version every solid is cut by.
#
# ``pyproject.toml`` is deliberately absent: its dependency edits already show
# up in ``uv.lock``, and its ``[tool.setuptools] packages`` list has no effect on
# a source-tree build. Hashing it would force a full rebuild every time a model
# package is registered, for no change in geometry.
GLOBAL_INPUTS = (
    "export.py",
    "fontfix.py",
    "main.py",
    "model_deps.py",
    "tessellate_models.py",
    "uv.lock",
)


class UnparseableModel(Exception):
    """A model source could not be parsed, so its dependencies are unknown.

    Raised rather than swallowed: an empty dependency set would look exactly
    like "nothing to rebuild", which is the one wrong answer this module must
    never give.
    """


def _module_path(module: str) -> Path | None:
    """The file backing a dotted module name, or None if it names no module.

    Returns None for the common, harmless case of a ``from .box import grip_for``
    whose ``models.pkg.box.grip_for`` is a function rather than a submodule.
    """
    flat = ROOT / (module.replace(".", "/") + ".py")
    if flat.is_file():
        return flat
    package = ROOT / module.replace(".", "/") / "__init__.py"
    if package.is_file():
        return package
    return None


def _package_of(module: str, path: Path) -> str:
    """The package a relative import inside ``path`` is resolved against."""
    return module if path.name == "__init__.py" else module.rpartition(".")[0]


def _ancestors(module: str) -> list[str]:
    """The packages Python imports on the way to ``module``, nearest first."""
    parts = module.split(".")
    return [".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]


def _imported_modules(module: str, path: Path) -> set[str]:
    """Every module name the source at ``path`` could be importing.

    Each ``from X import a, b`` contributes ``X`` plus ``X.a`` and ``X.b``,
    because the imported name may be either an attribute or a submodule and the
    syntax does not say which. ``_module_path`` discards the ones that name no
    file.
    """
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError as exc:
        raise UnparseableModel(f"{path.relative_to(ROOT)}: {exc}") from exc

    package = _package_of(module, path)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # ``from . import x`` resolves against the package; each extra
                # dot strips one more component off it.
                parts = package.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1])
            else:
                base = ""
            absolute = (
                f"{base}.{node.module}"
                if base and node.module
                else (base or node.module or "")
            )
            if not absolute:
                continue
            found.add(absolute)
            found.update(f"{absolute}.{alias.name}" for alias in node.names)
    return found


@lru_cache(maxsize=None)
def model_files(name: str) -> tuple[Path, ...]:
    """Every file under ``models/`` that building ``name`` can reach.

    Walks the import graph from ``models.<name>``, following only ``models.*``
    edges -- third-party imports are pinned by ``uv.lock``, which is hashed
    separately as a global input.
    """
    root = f"models.{name}"
    if _module_path(root) is None:
        raise ModuleNotFoundError(f"Model '{name}' not found in models/")

    seen: set[str] = set()
    files: set[Path] = set()
    pending = [root]
    while pending:
        module = pending.pop()
        if module in seen or not module.startswith("models"):
            continue
        seen.add(module)
        path = _module_path(module)
        if path is None:
            continue
        files.add(path)
        pending.extend(_imported_modules(module, path))
        # Importing ``models.pkg.part`` runs ``models/__init__.py`` and
        # ``models/pkg/__init__.py`` first, so whatever those execute is part of
        # this model's build whether or not it names them. Walking the ancestors
        # too picks up what *they* import -- which for a package like
        # ``led_psu_enclosure`` is its entire re-exported surface.
        pending.extend(_ancestors(module))
    return tuple(sorted(files))


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return "absent"


def fingerprint(name: str) -> str:
    """A content hash of everything that decides ``name``'s exported geometry.

    Equal fingerprints mean the exports on disk are exactly what a rebuild would
    produce, so the rebuild can be skipped. Both the model's own import closure
    and ``GLOBAL_INPUTS`` are covered, and paths are hashed alongside contents so
    that moving a file counts as a change.
    """
    parts = [f"{path.relative_to(ROOT)}:{_digest(path)}" for path in model_files(name)]
    parts += [f"{rel}:{_digest(ROOT / rel)}" for rel in GLOBAL_INPUTS]
    return hashlib.sha256("\n".join(sorted(parts)).encode()).hexdigest()


def affected_models(changed: list[str], models: list[str]) -> list[str]:
    """Which of ``models`` a change to ``changed`` can reach.

    Paths are taken relative to the repo root, as ``git diff --name-only`` emits
    them. Anything in ``GLOBAL_INPUTS`` selects the whole roster.
    """
    changed_set = {str(Path(c)) for c in changed}
    if changed_set & set(GLOBAL_INPUTS):
        return list(models)
    return [
        name
        for name in models
        if changed_set & {str(p.relative_to(ROOT)) for p in model_files(name)}
    ]


def main() -> None:
    """``uv run deps <path>...`` -- the models a change to those paths reaches."""
    from tessellate_models import MODELS

    args = sys.argv[1:]
    if not args:
        print("Usage: uv run deps <changed-path>...   models a change reaches")
        print("       uv run deps --files <model>     files a model is built from")
        sys.exit(1)

    if args[0] == "--files":
        if len(args) != 2:
            print("Usage: uv run deps --files <model>")
            sys.exit(1)
        for path in model_files(args[1]):
            print(path.relative_to(ROOT))
        return

    hits = affected_models(args, list(MODELS))
    for name in hits:
        print(name)
    print(f"\n{len(hits)} of {len(MODELS)} models affected", file=sys.stderr)


if __name__ == "__main__":
    main()
