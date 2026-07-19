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

    Only the ``models`` package -- no ``create()`` path pulls in ``export.py``,
    ``fontfix.py`` or ``tessellate_models.py`` (which would drag in ocp_vscode /
    ocp_tessellate that don't exist in Pyodide).
    """
    sources: dict[str, str] = {}
    init = MODELS_DIR / "__init__.py"
    if init.exists():
        sources["models/__init__.py"] = init.read_text()
    for name in MODELS:
        sources[f"models/{name}.py"] = (MODELS_DIR / f"{name}.py").read_text()
    return sources


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
                "label": name.replace("_", " ").title(),
                "params": model_params(name),
                "source": f"models/{name}.py",
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
