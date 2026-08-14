"""Build a single self-contained HTML artifact showing a model in 3D.

``uv run view <name>`` writes ``exports/<name>.html``: one file that renders the
model with the same three.js viewer the deployed site uses (website/viewer.js),
so what the agent shows matches what CI ships. The artifact is fully
self-contained — three.js and its loaders are inlined, and the model's GLB (or
STL) is embedded as a base64 data URI — because it is destined for two places
that can fetch nothing from the network:

* locally, the agent opens it straight off the filesystem with its browser tool;
* in the cloud (Claude Code), the agent publishes it as an artifact, which a
  strict CSP renders without any external request.

Usage: uv run view <name> [--out PATH] [--serve] [--port N]
"""

import base64
import importlib
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent.resolve()
EXPORTS_DIR = HERE / "exports"
VIEWER_JS = HERE / "website" / "viewer.js"

# three.js version must match website/index.html's import map exactly, so the
# artifact and the site render with the same library.
THREE_VERSION = "0.160.0"
VENDOR_URLS = {
    "three.min.js": f"https://unpkg.com/three@{THREE_VERSION}/build/three.min.js",
    "OrbitControls.js": f"https://unpkg.com/three@{THREE_VERSION}/examples/jsm/controls/OrbitControls.js",
    "STLLoader.js": f"https://unpkg.com/three@{THREE_VERSION}/examples/jsm/loaders/STLLoader.js",
    "BufferGeometryUtils.js": f"https://unpkg.com/three@{THREE_VERSION}/examples/jsm/utils/BufferGeometryUtils.js",
    "GLTFLoader.js": f"https://unpkg.com/three@{THREE_VERSION}/examples/jsm/loaders/GLTFLoader.js",
}

# The artifact inlines everything into ONE <script type="module">. three.min.js
# loads as a classic script and sets window.THREE; the addons and viewer.js are
# ESM, so every import preamble is stripped. The addons share many 'three' names
# (Vector3, MathUtils, ...), so rewriting each into its own `const {...} = THREE`
# would redeclare them in one module scope and throw. Instead their names are
# unioned into ONE destructure emitted before the addons, and every import line
# (named, namespace, or relative) is then simply dropped: the addons and viewer
# see the shared names from that single declaration, and a sibling reached by a
# relative import is already inlined ahead of it. The result has no import
# statement and no data:-URI module, so it renders under the strict artifact CSP
# as a plain inline script.
THREE_IMPORT_RE = re.compile(r"import\s*\{([\s\S]*?)\}\s*from\s*['\"]three['\"]\s*;")
ANY_IMPORT_RE = re.compile(r"^import\s+[\s\S]*?;\s*$", re.MULTILINE)
ADDON_ORDER = (
    "OrbitControls.js",
    "STLLoader.js",
    "BufferGeometryUtils.js",
    "GLTFLoader.js",
)


def _addon_three_names(text: str) -> list[str]:
    """The names (possibly `X as Y`) an addon imports from 'three'."""
    names = []
    for m in THREE_IMPORT_RE.finditer(text):
        for item in m.group(1).split(","):
            item = item.strip()
            if item:
                names.append(item)
    return names


def _strip_all_imports(js: str, fname: str) -> str:
    out = ANY_IMPORT_RE.sub("", js)
    leftover = [ln for ln in out.splitlines() if ln.lstrip().startswith("import ")]
    if leftover:
        raise RuntimeError(f"unhandled import(s) in {fname}: {leftover[0]!r}")
    return out


def _label(name: str) -> str:
    """Human-readable model name for the page title, as the site labels it."""
    return " / ".join(part.replace("_", " ").title() for part in name.split("."))


def _vendor_dir() -> Path:
    return EXPORTS_DIR / ".vendor" / f"three-{THREE_VERSION}"


def _ensure_vendor() -> Path:
    d = _vendor_dir()
    if all((d / f).exists() for f in VENDOR_URLS):
        return d
    d.mkdir(parents=True, exist_ok=True)
    for fname, url in VENDOR_URLS.items():
        dest = d / fname
        if dest.exists():
            continue
        print(f"Fetching three@{THREE_VERSION} {fname} ...")
        urllib.request.urlretrieve(url, dest)
    return d


def _ensure_model_asset(name: str) -> Path:
    """The model's GLB if present, else its STL; build either if missing."""
    glb = EXPORTS_DIR / f"{name}.glb"
    stl = EXPORTS_DIR / f"{name}.stl"
    if glb.exists():
        return glb
    if stl.exists():
        return stl
    module = importlib.import_module(f"models.{name}")
    from export import export

    export(module.create(), name, step=False)  # writes STL + GLB
    return glb if glb.exists() else stl


def _module_js(vendor: Path, has_glb: bool, b64: str) -> str:
    """The artifact's single inline module: THREE + shared names + addons + viewer + shell."""
    addons = {f: (vendor / f).read_text() for f in ADDON_ORDER}
    union = sorted({n for f in ADDON_ORDER for n in _addon_three_names(addons[f])})
    parts = [
        f"const THREE = window.THREE;\nconst {{ {', '.join(union)} }} = THREE;",
        "",
    ]
    for fname in ADDON_ORDER:
        parts.append(_strip_all_imports(addons[fname], fname))
        parts.append("")
    parts.append(_strip_all_imports(VIEWER_JS.read_text(), "viewer.js"))
    parts.append(
        """
// ---------------------------------------------------------------------------
// Artifact shell: build the viewer, load the embedded model, wire the grid.
// ---------------------------------------------------------------------------
const statusEl = document.getElementById('vstatus');
function setStatus(text, isErr) {
  if (!text) { statusEl.classList.add('hidden'); return; }
  statusEl.textContent = text;
  statusEl.classList.remove('hidden');
  statusEl.classList.toggle('err', !!isErr);
}
const viewer = createViewer({
  container: document.getElementById('view'),
  canvas: document.getElementById('viewer'),
  onStatus: (text, isErr) => setStatus(text, isErr),
  onLog: (m) => console.warn(m),
});
const { showStl, showGlb, setGrid, getGrid } = viewer;

const gridBtn = document.getElementById('btn-grid');
gridBtn.addEventListener('click', () => {
  const on = __omp_shell("getGrid();")
  setGrid(on);
  gridBtn.setAttribute('aria-pressed', String(on));
});

function b64ToBytes(b64) {
  const bin = atob(b64);
  const u = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
  return u;
}
const HAS_GLB = @@HAS_GLB@@;
const MODEL_B64 = "@@MODEL_B64@@";
try {
  if (HAS_GLB) showGlb(b64ToBytes(MODEL_B64), true);
  else showStl(b64ToBytes(MODEL_B64), true);
} catch (e) {
  setStatus('failed to render: ' + e, true);
}
""".replace("@@HAS_GLB@@", "true" if has_glb else "false").replace("@@MODEL_B64@@", b64)
    )
    return "\n".join(parts)


def _artifact_html(title: str, three_min_js: str, module_js: str) -> str:
    return (
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>build123d — """
        + title
        + """</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; }
  body { background: #14171c; color: #e6e8eb; font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
  #view { position: fixed; inset: 0; }
  canvas#viewer { position: absolute; inset: 0; width: 100%; height: 100%; display: block; touch-action: none; }
  #vinfo { position: absolute; left: 12px; bottom: 10px; font-size: 11px; color: #6b7280; pointer-events: none; z-index: 1; }
  #vstatus { position: absolute; left: 12px; top: 10px; right: 12px; font-size: 12px; color: #cdd3db;
    background: rgba(20,23,28,.7); border: 1px solid #2a2f37; border-radius: 6px; padding: 5px 10px; z-index: 2; }
  #vstatus.err { color: #f0a5a5; border-color: #5c2f2f; }
  .vbtn { position: absolute; right: 12px; bottom: 10px; z-index: 2; padding: 5px 10px; font-size: 12px;
    background: rgba(20,23,28,.7); border: 1px solid #333a44; border-radius: 6px; color: #cdd3db; cursor: pointer; }
  .vbtn[aria-pressed="true"] { border-color: #4a90ff; color: #e6e8eb; background: rgba(59,130,246,.18); }
  .hidden { display: none; }
</style>
</head>
<body>
<section id="view">
  <div id="vstatus" class="hidden" aria-live="polite"></div>
  <canvas id="viewer"></canvas>
  <div id="vinfo">drag = rotate · scroll = zoom · right-drag = pan</div>
  <button id="btn-grid" class="vbtn" aria-pressed="true" title="Show or hide the ground grid">Grid</button>
</section>
<script>
"""
        + three_min_js
        + """
</script>
<script type="module">
"""
        + module_js
        + """
</script>
</body>
</html>
"""
    )


def _serve(exports_dir: Path, fname: str, port: int) -> str:
    import functools
    import http.server
    import threading

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(exports_dir)
    )
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/{fname}"


def main() -> None:
    argv = sys.argv[1:]
    name = next((a for a in argv if not a.startswith("-")), None)
    serve = "--serve" in argv
    known = {"--serve"}
    out_flag = None
    if "--out" in argv:
        known.add("--out")
        out_flag = argv[argv.index("--out") + 1]
    port = 8000
    if "--port" in argv:
        known.add("--port")
        port = int(argv[argv.index("--port") + 1])
    unknown = [a for a in argv if a.startswith("-") and a not in known]

    if not name or unknown:
        print("Usage: uv run view <name> [--out PATH] [--serve] [--port N]")
        sys.exit(1)
    assert name is not None

    asset = _ensure_model_asset(name)
    has_glb = asset.suffix == ".glb"
    b64 = base64.b64encode(asset.read_bytes()).decode("ascii")

    vendor = _ensure_vendor()
    module_js = _module_js(vendor, has_glb, b64)
    three_min_js = (vendor / "three.min.js").read_text()

    title = _label(name)
    html = _artifact_html(title, three_min_js, module_js)

    out = EXPORTS_DIR / f"{name}.html" if not out_flag else Path(out_flag)
    out.write_text(html)

    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"Wrote {out} ({size_mb:.1f} MiB, {'GLB' if has_glb else 'STL'} render)")
    if size_mb > 14:
        print(
            "Warning: approaching the 16 MiB cloud-artifact limit; PNG fallback may be needed."
        )
    print(f"Open it: file://{out}")

    if serve:
        print("Serving:", _serve(EXPORTS_DIR, out.name, port))
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
