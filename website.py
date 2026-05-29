import json
import os
import shutil
import http.server
import sys
from pathlib import Path

DOCS_EXPORTS = Path("exports")
WEBSITE_DIR = Path("website")
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


def main(port: int = 8743) -> None:
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
    print(f"Manifest: {manifest_path}")

    os.chdir(WEBSITE_DIR)

    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    print(f"Serving at http://localhost:{port}/")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
        server.shutdown()


if __name__ == "__main__":
    port = 8743
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print("Usage: uv run website        # serve on port 8743")
        print("       uv run website 9000   # serve on port 9000")
        sys.exit(0)
    if args and args[0].isdigit():
        port = int(args[0])
    main(port)
