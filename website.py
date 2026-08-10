"""Static dev server + web-bundle builder for the Pyodide site.

The site is fully static: geometry is generated in the browser (Pyodide + build123d
+ OpenCASCADE WASM), so there is no server API. This module just (a) builds the two
generated assets the page fetches and (b) serves ``website/`` for local preview.

``build_web_bundle()`` is the single function both this dev server and CI call, so
the local preview matches GitHub Pages exactly. It writes:

  * ``website/models-manifest.json`` -- per-model label, PARAMS schema, asset paths,
                                        last-edited timestamp.
  * ``website/py-sources.json``       -- source text of every ``models/*.py`` so the
                                          worker can import them in the Pyodide FS.

and copies the CI-rendered ``exports/<name>.stl|.step|.png`` into ``website/exports/``.
"""

import functools
import http.server
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from model_deps import model_files
from tessellate_models import MODELS, model_is_assembly, model_params

HERE = Path(__file__).parent.resolve()
EXPORTS = HERE / "exports"
MODELS_DIR = HERE / "models"
WEBSITE_DIR = HERE / "website"
WEBSITE_EXPORTS = WEBSITE_DIR / "exports"


def _py_sources() -> dict[str, str]:
    """Source text the in-browser runtime needs to ``import models.<name>``.

    The whole ``models`` tree is bundled -- single-file models, packages like
    ``led_psu_enclosure``, and the shared ``models.lib`` helpers they import --
    but nothing outside it: no ``create()`` path pulls in ``export.py``,
    ``fontfix.py`` or ``tessellate_models.py`` (which would drag in ocp_vscode /
    ocp_tessellate that don't exist in Pyodide).
    """
    return {
        str(py.relative_to(HERE)): py.read_text()
        for py in sorted(MODELS_DIR.rglob("*.py"))
    }


def _source_path(name: str) -> str:
    """Where a model's own source lives, relative to the repo root.

    A model name is a module path under ``models`` (``tessellate_models.MODELS``),
    so the dots become directories: ``led_profiles.stand`` is
    ``models/led_profiles/stand.py``. A package's own name resolves to its
    ``__init__.py`` -- ``models/led_psu_enclosure.py`` has not existed since that
    model became a package, and the page's Code panel has been showing "source
    unavailable" for it ever since, because this is the key it looks up in
    ``py-sources.json``.

    Raises on a name that resolves to neither. This used to fall back to the
    flat ``models/<name>.py`` so that a typo in the roster surfaced as an empty
    editor rather than an exception, and that was the right trade only while
    nothing else caught the typo: the fallback bought a bundle that still built,
    at the price of a model whose Code panel silently said "source unavailable"
    with nothing anywhere explaining why. ``tests/test_model_registry.py`` now
    fails on an unresolvable roster name, so the typo is caught before a build
    is ever attempted and the silence buys nothing -- it only delays the same
    problem to a place where it reads as a website bug instead of a bad entry
    in ``MODELS``.
    """
    flat = MODELS_DIR / f"{name.replace('.', '/')}.py"
    if flat.exists():
        return str(flat.relative_to(HERE))
    package = MODELS_DIR / name.replace(".", "/") / "__init__.py"
    if package.exists():
        return str(package.relative_to(HERE))
    raise FileNotFoundError(
        f"{name!r} is in tessellate_models.MODELS but resolves to neither "
        f"models/{name.replace('.', '/')}.py nor "
        f"models/{name.replace('.', '/')}/__init__.py"
    )


def _label(name: str) -> str:
    """Human-readable name for the picker: ``led_profiles.stand`` -> the
    package and the part, each read as words."""
    return " / ".join(part.replace("_", " ").title() for part in name.split("."))


@functools.lru_cache(maxsize=1)
def _commit_dates() -> dict[str, datetime]:
    """``models/...`` path -> commit date of the newest commit that touched it.

    One ``git log`` for the whole tree rather than one per file: the roster is 41
    models over a few hundred source files, and a subprocess each would dominate
    the bundle build. The log is newest-first, so the first date seen for a path
    is its latest, and merge commits contribute nothing (``git log`` prints no
    ``--name-only`` list for them), which is what we want -- a merge does not
    edit a model.

    Returns ``{}`` when git cannot answer at all (no repo, no git binary, or a
    tarball of the sources); ``_last_edited`` then falls back to file mtimes.
    Beware the *shallow* clone, which is not an error and so not caught here: a
    ``fetch-depth: 1`` checkout has one commit that adds every file, so every
    model would report the same date. ``.github/workflows/build.yml`` therefore
    checks out the full history for the job that builds the bundle.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(HERE), "log", "--pretty=format:\x01%cI", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return {}

    dates: dict[str, datetime] = {}
    stamp: datetime | None = None
    for line in out.splitlines():
        if line.startswith("\x01"):
            stamp = datetime.fromisoformat(line[1:])
        elif line and stamp is not None:
            dates.setdefault(line, stamp)
    return dates


def _last_edited(name: str) -> str | None:
    """When this model's geometry last changed, as a UTC ISO-8601 timestamp.

    Taken over the model's whole import closure (``model_deps.model_files``),
    not just the file its name resolves to. Most models here are cut from shared
    engines -- every ``drill_storage.*`` part comes out of ``drill_storage/box.py``,
    every ``led_profiles`` part out of its ``config.py`` -- so dating a part by
    its own four-line module would show a week-old date for a part that changed
    this morning.

    Two kinds of input are left out, both because including them dates models
    that nobody edited:

    * ``model_deps.GLOBAL_INPUTS``. A lockfile bump or an edit to ``export.py``
      re-exports the roster without anyone having touched a model, and stamping
      all 41 with that date would make the field meaningless.
    * Every ``checks.py``. Assertions *verify* a model, they do not define it,
      and ``models/lib/checks.py`` is in the closure of nearly every model here
      (a single-file model's ``check()`` imports it), so one commit tightening a
      shared assertion would otherwise redate half the site. This is the one
      place the answer deliberately differs from ``main.py``'s fingerprint,
      which rebuilds on a ``checks.py`` edit and is right to: it is asking
      whether the export is stale, not when the design last moved.

    Uncommitted files (a model added but not yet committed) have no commit date,
    so they fall back to their mtime, which reads as "just now" -- right for a
    local preview and unreachable in CI, which only ever builds committed trees.
    """
    dates = _commit_dates()
    stamps: list[datetime] = []
    for path in model_files(name):
        if path.name == "checks.py":
            continue
        stamp = dates.get(str(path.relative_to(HERE)))
        if stamp is None:
            try:
                stamp = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            except OSError:  # deleted between the walk and the stat
                continue
        stamps.append(stamp)
    if not stamps:
        return None
    newest = max(stamps).astimezone(timezone.utc)
    return newest.isoformat(timespec="seconds").replace("+00:00", "Z")


def _manifest() -> dict:
    """Per-model metadata for the UI (labels, PARAMS, prebuilt-asset paths).

    ``assembly`` is what the page's two download buttons key off: a scene has
    no STL or STEP worth handing anyone (see
    ``tessellate_models.model_is_assembly``), so the buttons are hidden rather
    than offered on a mesh nobody can print.
    """
    models = []
    for name in MODELS:
        stl = EXPORTS / f"{name}.stl"
        step = EXPORTS / f"{name}.step"
        glb = EXPORTS / f"{name}.glb"
        thumb = EXPORTS / f"{name}.png"
        models.append(
            {
                "name": name,
                "label": _label(name),
                "params": model_params(name),
                "assembly": model_is_assembly(name),
                "source": _source_path(name),
                # UTC ISO-8601, or null when neither git nor the filesystem can
                # say; the page renders it in the visitor's own timezone.
                "updated": _last_edited(name),
                # Kept even for an assembly, which offers no STL download: it is
                # the preview's fallback when a model has no GLB.
                "stl": f"exports/{name}.stl" if stl.exists() else None,
                "step": f"exports/{name}.step" if step.exists() else None,
                "glb": f"exports/{name}.glb" if glb.exists() else None,
                "thumb": f"exports/{name}.png" if thumb.exists() else None,
            }
        )
    return {"models": models}


def build_web_bundle() -> None:
    """Emit models-manifest.json + py-sources.json and copy prebuilt render assets."""
    WEBSITE_EXPORTS.mkdir(parents=True, exist_ok=True)
    (WEBSITE_DIR / "py-sources.json").write_text(json.dumps(_py_sources()))
    (WEBSITE_DIR / "models-manifest.json").write_text(json.dumps(_manifest(), indent=2))
    copied = 0
    for name in MODELS:
        for ext in ("stl", "step", "glb", "png"):
            src = EXPORTS / f"{name}.{ext}"
            if src.exists():
                shutil.copy2(src, WEBSITE_EXPORTS / src.name)
                copied += 1
    print(f"Built web bundle: {len(MODELS)} models, {copied} render assets → website/")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".stl": "model/stl",
        ".step": "application/step",
    }

    def log_message(self, *args) -> None:  # keep the console quiet
        pass


def serve(port: int) -> None:
    handler = functools.partial(Handler, directory=str(WEBSITE_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Serving at http://localhost:{port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def run(port: int = 8743, watch: bool = False) -> None:
    build_web_bundle()

    if not watch:
        serve(port)
        return

    # --watch: rebuild the bundle whenever a model source changes. The static
    # handler reads files per-request, so the server itself never needs a restart.
    try:
        from watchfiles import watch as watch_files
    except ImportError:
        print("watchfiles not installed (run: uv sync); serving without --watch")
        serve(port)
        return

    import threading

    threading.Thread(target=serve, args=(port,), daemon=True).start()
    print(f"Watching {MODELS_DIR}/ for changes…")
    try:
        for _changes in watch_files(MODELS_DIR):
            print("Change detected — rebuilding web bundle…")
            build_web_bundle()
    except KeyboardInterrupt:
        pass


def main() -> None:
    """Console entry point: parse args (port / --watch) and serve."""
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print("Usage: uv run website              # build bundle + serve on 8743")
        print("       uv run website 9000          # serve on port 9000")
        print("       uv run website --watch       # rebuild bundle on model changes")
        return
    port = 8743
    if args and args[0].isdigit():
        port = int(args[0])
    run(port, watch="--watch" in args)


if __name__ == "__main__":
    main()
