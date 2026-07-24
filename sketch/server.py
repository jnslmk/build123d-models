"""Local HTTP backend for the click-and-drag canvas.

This is the *human* editor. It serves the static canvas UI and exposes a tiny JSON
API that maps 1:1 onto ``sketch.commands`` -- the exact same mutation surface the
MCP server (the agent editor) uses. Both read and write ``sketches/<name>.sketch.json``
on disk, so an edit from the browser and an edit from the agent interleave: the
canvas polls the file and reflects the agent's changes live, and vice versa.

    uv run sketch-ui                 # serve on http://localhost:8744
    uv run sketch-ui 9001            # custom port

No build step, no framework -- one static ``ui/index.html`` and stdlib http.server,
matching this repo's website.py approach.
"""

from __future__ import annotations

import functools
import http.server
import json
import sys
from typing import Any

from sketch import codegen, commands
from sketch.model import REPO_ROOT, Sketch
from sketch.solver import solve

UI_DIR = REPO_ROOT / "sketch" / "ui"
DEFAULT_PORT = 8744


def _state(sk: Sketch, report: Any) -> dict[str, Any]:
    """The document + solve status the canvas renders from."""
    return {
        "name": sk.name,
        "plane": sk.plane,
        "extrude": sk.extrude,
        "points": sk.points,
        "segments": sk.segments,
        "circles": sk.circles,
        "constraints": sk.constraints,
        "solve": {
            "status": report.status,
            "dof": report.dof,
            "residual": report.residual,
            "satisfied": report.satisfied,
        },
    }


def _apply_command(name: str, body: dict[str, Any]) -> dict[str, Any]:
    """Run one command against sketch ``name`` and return the fresh state.

    ``drag`` is special: the point is pinned at the cursor while the rest re-solves
    (so the grabbed point tracks the mouse), then the report is read back without
    moving anything further.
    """
    sk = Sketch.load(name)
    command = body.pop("command")
    if command == "drag":
        commands.drag(sk, body["pid"], body["x"], body["y"])
        report = solve(sk, iterations=0)  # report only; geometry already solved
    else:
        out = commands.apply(sk, command, **body)
        report = out["report"] or solve(sk, iterations=0)
    sk.save()
    return _state(sk, report)


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serve the static UI, plus a small JSON API under /api/."""

    def log_message(self, *args: Any) -> None:  # keep the console quiet
        pass

    # -- helpers ----------------------------------------------------------
    def _send_json(self, obj: Any, code: int = 200) -> None:
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    # -- routing ----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path == "/api/sketches":
            self._send_json({"names": Sketch.list_names()})
            return
        if self.path.startswith("/api/sketch/"):
            name = self.path.rsplit("/", 1)[-1]
            try:
                sk = Sketch.load(name)
            except FileNotFoundError:
                self._send_json({"error": f"no sketch {name!r}"}, 404)
                return
            self._send_json(_state(sk, solve(sk, iterations=0)))
            return
        super().do_GET()  # static file from UI_DIR

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_body()
            if self.path == "/api/create":
                name = body["name"]
                if name in Sketch.list_names():
                    self._send_json({"error": f"{name!r} already exists"}, 409)
                    return
                sk = Sketch(
                    name=name,
                    plane=body.get("plane", "XY"),
                    extrude=float(body.get("extrude", 3.0)),
                )
                sk.save()
                self._send_json(_state(sk, solve(sk, iterations=0)))
                return
            if self.path.startswith("/api/sketch/") and self.path.endswith("/command"):
                name = self.path[len("/api/sketch/") : -len("/command")]
                self._send_json(_apply_command(name, body))
                return
            if self.path.startswith("/api/sketch/") and self.path.endswith("/generate"):
                name = self.path[len("/api/sketch/") : -len("/generate")]
                sk = Sketch.load(name)
                solve(sk)
                sk.save()
                path = codegen.write_model(sk)
                self._send_json(
                    {
                        "path": str(path.relative_to(REPO_ROOT)),
                        "show_command": f"uv run show {sk.name}",
                    }
                )
                return
            self._send_json({"error": f"no route {self.path}"}, 404)
        except (commands.CommandError, KeyError, ValueError) as exc:
            self._send_json({"error": str(exc)}, 400)


def run(port: int = DEFAULT_PORT) -> None:
    handler = functools.partial(Handler, directory=str(UI_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Sketch canvas at http://localhost:{port}/  (Ctrl+C to stop)")
    print("The agent (MCP) and this canvas edit the same sketches/*.sketch.json.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main() -> None:
    args = sys.argv[1:]
    port = int(args[0]) if args and args[0].isdigit() else DEFAULT_PORT
    run(port)


if __name__ == "__main__":
    main()
