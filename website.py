import json
import os
import shutil
import http.server
import sys
import signal
import threading
import time
from pathlib import Path

HERE = Path(__file__).parent.resolve()
DOCS_EXPORTS = HERE / "exports"
WEBSITE_DIR = HERE / "website"
WEBSITE_EXPORTS = WEBSITE_DIR / "exports"
DOCS_MODELS = [
    "cube",
    "door_latch",
    "lens_cap",
    "satellite_led",
    "slotted_plate",
    "spiral_vase_lampshade",
    "wall_bar_lamp",
]


def sync_models() -> None:
    WEBSITE_EXPORTS.mkdir(parents=True, exist_ok=True)

    for name in DOCS_MODELS:
        src = DOCS_EXPORTS / f"{name}_shapes.json"
        if src.exists():
            shutil.copy2(src, WEBSITE_EXPORTS / f"{name}_shapes.json")

    models = []
    for name in DOCS_MODELS:
        stl = WEBSITE_EXPORTS / f"{name}.stl"
        iso = WEBSITE_EXPORTS / f"{name}_iso.svg"
        top = WEBSITE_EXPORTS / f"{name}_top.svg"
        front = WEBSITE_EXPORTS / f"{name}_front.svg"
        shapes = WEBSITE_EXPORTS / f"{name}_shapes.json"
        if stl.exists():
            models.append(
                {
                    "name": name,
                    "stl": f"exports/{name}.stl",
                    "iso": f"exports/{name}_iso.svg" if iso.exists() else None,
                    "top": f"exports/{name}_top.svg" if top.exists() else None,
                    "front": f"exports/{name}_front.svg" if front.exists() else None,
                    "shapes": f"exports/{name}_shapes.json"
                    if shapes.exists()
                    else None,
                }
            )

    manifest_path = WEBSITE_EXPORTS / "models.json"
    with manifest_path.open("w") as f:
        json.dump({"models": models}, f, indent=2)

    print(f"Synced {len(models)} models to website/exports/")


def serve(port: int, stop_event: threading.Event) -> None:
    os.chdir(WEBSITE_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    print(f"Serving at http://localhost:{port}/")
    print("Press Ctrl+C to stop")

    while not stop_event.is_set():
        server.serve_forever()


def main(port: int = 8743, watch: bool = False) -> None:
    try:
        from watchfiles import watch
    except ImportError:
        print("watchfiles not installed. Run: uv sync")
        sys.exit(1)

    sync_models()

    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    stop_event = threading.Event()
    server_thread = threading.Thread(target=serve, args=(port, stop_event), daemon=True)
    server_thread.start()
    print("Press Ctrl+C to stop")

    if watch:
        print(f"Watching {WEBSITE_DIR}/ for changes...")
        for changes in watch(WEBSITE_DIR, stop_event=stop_event):
            for change in changes:
                print(f"Change: {change}")
            print("Reloading...")
            sync_models()
            stop_event.set()
            time.sleep(0.5)
            stop_event.clear()
            server_thread = threading.Thread(
                target=serve, args=(port, stop_event), daemon=True
            )
            server_thread.start()
    else:
        server_thread.join()


if __name__ == "__main__":
    port = 8743
    watch = False
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print("Usage: uv run website              # serve on port 8743")
        print("       uv run website 9000          # serve on port 9000")
        print("       uv run website --watch       # serve with hot reload")
        print("       uv run website 9000 --watch  # serve on 9000 with hot reload")
        sys.exit(0)
    if args and args[0].isdigit():
        port = int(args[0])
        args = args[1:]
    watch = "--watch" in args
    main(port, watch)
