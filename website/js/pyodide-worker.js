// Pyodide + build123d, running off the main thread so the UI never freezes
// during the (slow) OpenCASCADE geometry build. This is the browser CAD engine:
// it runs the repo's real `models/<name>.py::create(**params)` unmodified via
// CPython + OpenCASCADE (cadquery-ocp) compiled to WebAssembly.
//
// Adapted from gridfinity-bins/docs/pyodide-worker.js, generalized to (a) any
// model in the repo and (b) live-edited source from the in-page code editor.
//
// Protocol (worker -> main):
//   {type:"status", text}         boot progress (shown in the overlay)
//   {type:"log", text}            console line
//   {type:"ready"}                runtime up, first generate can run
//   {type:"result", id, model, stl(ArrayBuffer), step(ArrayBuffer|null),
//                   cadMs, wallMs, cached}
//   {type:"error", id?, message}
// Protocol (main -> worker):
//   {type:"init", baseUrl}                                      // absolute site URL
//   {type:"generate", id, model, sourcePath, sourcesUrl, editSourcesUrl, params}
//   {type:"generate", id, model, sourcePath, sourcesUrl, editSourcesUrl, source}
//
// The edited file is at the manifest's `source` path, which may be a package
// __init__.py. Source assets are versioned URLs from the manifest.

importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.0a3/full/pyodide.js");

let pyodide = null;
const cache = new Map(); // JSON({model,params,sourcesUrl}) -> generated mesh buffers
let resolveBaseUrl;
const baseUrl = new Promise((resolve) => { resolveBaseUrl = resolve; });
const sourceAssets = new Map(); // asset URL -> Promise of source dictionary
const writtenSources = new Map(); // Python FS path -> most recently written text

const status = (text) => self.postMessage({ type: "status", text });
const log = (text) => self.postMessage({ type: "log", text });

// Install OpenCASCADE (the big one) + build123d from the OCP.wasm index, then
// stub out ocp_vscode so any model that `from ocp_vscode import show` at module
// top level imports cleanly in the headless runtime.
const SETUP = `
import micropip
micropip.set_index_urls(["https://yeicor.github.io/OCP.wasm", "https://pypi.org/simple"])
print("installing lib3mf ...")
await micropip.install("lib3mf")
micropip.add_mock_package("py-lib3mf", "2.4.1", modules={"py_lib3mf": "from lib3mf import *"})
print("installing OpenCASCADE WASM (cadquery-ocp, the big one) ...")
await micropip.install("cadquery-ocp")
micropip.add_mock_package("cadquery-ocp-novtk", "7.9.3.0")
# Keep the browser CAD release on the available OCCT 7.9 WASM stack. This
# verified upstream 0.11.1 wheel only moves DBSCAN imports into their call
# sites and omits scikit-learn from its eager dependency metadata (not SciPy).
print("installing build123d ...")
await micropip.install(BUILD123D_WHEEL_URL)
# Standard hardware (bd_warehouse.thread's IsoThread, in led_profiles.endcap).
# Pure Python on top of build123d, so it installs straight from PyPI -- but it
# has to be here, not just in pyproject.toml: the endcap is imported by the
# led_profiles package's own __init__, so without it every model in that
# package fails to import in the browser while still building fine locally.
#
# Keep the same bd_warehouse cap as the native project. Pinning build123d above
# prevents the resolver from silently upgrading the browser's OCCT stack.
print("installing bd_warehouse (standard threads/fasteners) ...")
await micropip.install("bd_warehouse>=0.2.0,<0.3.0")

import sys, types
_stub = types.ModuleType("ocp_vscode")
_stub.show = lambda *a, **k: None
_stub.show_object = lambda *a, **k: None
_stub.show_all = lambda *a, **k: None
_stub.set_defaults = lambda *a, **k: None
_stub.reset_show = lambda *a, **k: None
sys.modules["ocp_vscode"] = _stub

import build123d
print("build123d", build123d.__version__, "ready")
`;

// Build one model. RELOAD is true whenever a source file on the Python FS
// changed (or code was explicitly run). Purge all models.* modules because
// models import each other; otherwise an import can silently reuse old code.
const DRIVER = `
import json, time, importlib, sys
from build123d import Color, Compound, export_stl, export_step, export_gltf

# House blue (#59a6ff) so uncolored models still render in brand colour rather
# than glTF's material-less white. Kept in sync with export.py / the viewer CSS.
_DEFAULT_COLOR = Color(0.35, 0.65, 1.0)

def _apply_default_colors(part):
    leaves = list(part.leaves) if isinstance(part, Compound) else [part]
    for leaf in leaves:
        if leaf.color is None:
            leaf.color = _DEFAULT_COLOR

def _run(model, params_json, reload):
    if reload:
        for k in [k for k in sys.modules if k == "models" or k.startswith("models.")]:
            del sys.modules[k]
        importlib.invalidate_caches()
    mod = importlib.import_module("models." + model)
    params = json.loads(params_json) if params_json else {}
    t = time.time()
    part = mod.create(**params)       # Part or Compound; exporters handle both
    cad_ms = round((time.time() - t) * 1000)
    # Keep browser downloads at the same printable resolution as export.py.
    export_stl(
        part, "/tmp/out.stl", tolerance=0.001, angular_tolerance=0.05
    )  # colourless, drives downloads
    have_glb = False
    try:                               # colour-carrying render asset for the viewer
        _apply_default_colors(part)
        export_gltf(part, "/tmp/out.glb", binary=True)
        have_glb = True
    except Exception as exc:            # glTF is best-effort; STL still renders
        print("gltf export skipped:", exc)
    have_step = False
    try:
        export_step(part, "/tmp/out.step")
        have_step = True
    except Exception as exc:            # STEP is best-effort; never block the STL
        print("step export skipped:", exc)
    return json.dumps({"cadMs": cad_ms, "glb": have_glb, "step": have_step})

_run(MODEL, PARAMS_JSON, RELOAD)
`;

async function boot() {
  status("Booting Python WebAssembly runtime…");
  pyodide = await loadPyodide({ stdout: log, stderr: log });
  status("Installing numpy / micropip…");
  await pyodide.loadPackage(["micropip", "numpy", "typing-extensions"]);
  // Workers may be created from blobs; resolve relative to the page's site URL.
  pyodide.globals.set(
    "BUILD123D_WHEEL_URL",
    new URL("browser-wheels/build123d-0.11.1-py3-none-any.whl", await baseUrl).href
  );
  status("Downloading build123d + OpenCASCADE WASM (~40 MB, cached after)…");
  await pyodide.runPythonAsync(SETUP);

  pyodide.FS.mkdirTree("/models");
  pyodide.runPython("import sys; sys.path.insert(0, '/')");

  log("runtime ready ✔");
  self.postMessage({ type: "ready" });
}

let bootFailed = false;
const bootPromise = boot().catch((e) => {
  bootFailed = true;
  self.postMessage({ type: "error", message: "boot: " + (e.message || e) });
});

async function loadSources(url) {
  if (!sourceAssets.has(url)) {
    const request = (async () => {
      const response = await fetch(url);
      if (!response.ok) {
        const error = new Error(`source asset ${url}: HTTP ${response.status}`);
        error.httpStatus = response.status;
        throw error;
      }
      return response.json();
    })();
    sourceAssets.set(url, request);
    request.catch(() => sourceAssets.delete(url));
  }
  return sourceAssets.get(url);
}

function writeSources(sources, path, editedSource) {
  if (typeof sources[path] !== "string") throw new Error(`source asset missing ${path}`);
  let changed = editedSource !== null;
  for (const [file, original] of Object.entries(sources)) {
    const text = editedSource !== null && file === path ? editedSource : original;
    if (writtenSources.get(file) === text) continue;
    const full = "/" + file;
    pyodide.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
    pyodide.FS.writeFile(full, text);
    writtenSources.set(file, text);
    changed = true;
  }
  return changed;
}

self.onmessage = async (ev) => {
  const msg = ev.data;
  if (msg.type === "init") { resolveBaseUrl(msg.baseUrl); return; }
  if (msg.type !== "generate") return;
  await bootPromise;
  if (bootFailed) return;

  const isEdit = typeof msg.source === "string";
  const params = msg.params || {};
  const key = JSON.stringify({ model: msg.model, params, sourcesUrl: msg.sourcesUrl });

  // Cache hit (param builds only) — hand back a fresh copy so the cached buffer
  // survives the transfer.
  if (!isEdit && cache.has(key)) {
    const hit = cache.get(key);
    const stl = new Uint8Array(hit.stl);
    const glb = hit.glb ? new Uint8Array(hit.glb) : null;
    const transfer = [stl.buffer];
    if (glb) transfer.push(glb.buffer);
    self.postMessage(
      { type: "result", id: msg.id, model: msg.model, cached: true, cadMs: 0, wallMs: 0,
        stl: stl.buffer, glb: glb ? glb.buffer : null, step: null },
      transfer
    );
    return;
  }

  try {
    // Live edits may invoke any build123d API, including detect_primitives.
    // Install the real Pyodide scikit-learn package before importing edited code;
    // parameter-only rebuilds never request it.
    if (isEdit) {
      status("Installing scikit-learn for edited source…");
      await pyodide.loadPackage("scikit-learn");
    }
    status("Loading model sources…");
    const sources = await loadSources(isEdit ? msg.editSourcesUrl : msg.sourcesUrl);
    const reload = writeSources(sources, msg.sourcePath, isEdit ? msg.source : null);
    pyodide.globals.set("MODEL", msg.model);
    pyodide.globals.set("PARAMS_JSON", isEdit ? "" : JSON.stringify(params));
    pyodide.globals.set("RELOAD", reload);

    const t0 = performance.now();
    const metaJson = await pyodide.runPythonAsync(DRIVER);
    const meta = JSON.parse(metaJson);

    const stlBytes = new Uint8Array(pyodide.FS.readFile("/tmp/out.stl"));
    const glbBytes = meta.glb ? new Uint8Array(pyodide.FS.readFile("/tmp/out.glb")) : null;
    // keep copies for the cache (the originals get transferred away below)
    if (!isEdit) cache.set(key, { stl: new Uint8Array(stlBytes), glb: glbBytes ? new Uint8Array(glbBytes) : null });

    const transfer = [stlBytes.buffer];
    let glbBuf = null;
    if (glbBytes) { glbBuf = glbBytes.buffer; transfer.push(glbBuf); }
    let stepBuf = null;
    if (meta.step) {
      const stepBytes = new Uint8Array(pyodide.FS.readFile("/tmp/out.step"));
      stepBuf = stepBytes.buffer;
      transfer.push(stepBuf);
    }

    self.postMessage(
      {
        type: "result", id: msg.id, model: msg.model, cached: false,
        cadMs: meta.cadMs, wallMs: Math.round(performance.now() - t0),
        stl: stlBytes.buffer, glb: glbBuf, step: stepBuf,
      },
      transfer
    );
  } catch (e) {
    self.postMessage({
      type: "error", id: msg.id, message: e.message || String(e),
      httpStatus: e.httpStatus || null,
    });
  }
};
