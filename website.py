"""Static dev server + web-bundle builder for the Pyodide site.

The site is fully static: geometry is generated in the browser (Pyodide + build123d
+ OpenCASCADE WASM), so there is no server API. This module just (a) builds the two
generated assets the page fetches and (b) serves ``website/`` for local preview.

``build_web_bundle()`` is the single function both this dev server and CI call, so
the local preview matches GitHub Pages exactly. It writes:

  * ``website/models-manifest.json`` -- per-model label, PARAMS schema, asset paths.
  * ``website/py-sources.json``       -- source text of every ``models/*.py`` so the
                                          worker can import them in the Pyodide FS.

and copies the CI-rendered ``exports/<name>.stl|.step|.png`` into ``website/exports/``.
"""

import functools
import http.server
import json
import shutil
import sys
from pathlib import Path

from tessellate_models import MODELS, model_params

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

    Falls back to the flat ``models/<name>.py`` when neither exists, so a typo in
    the roster shows up as an empty editor rather than an exception here.
    """
    flat = MODELS_DIR / f"{name.replace('.', '/')}.py"
    if flat.exists():
        return str(flat.relative_to(HERE))
    package = MODELS_DIR / name.replace(".", "/") / "__init__.py"
    if package.exists():
        return str(package.relative_to(HERE))
    return f"models/{name}.py"


def _label(name: str) -> str:
    """Human-readable name for the picker: ``led_profiles.stand`` -> the
    package and the part, each read as words."""
    return " / ".join(part.replace("_", " ").title() for part in name.split("."))


def _manifest() -> dict:
    """Per-model metadata for the UI (labels, PARAMS, prebuilt-asset paths)."""
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
                "source": _source_path(name),
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
