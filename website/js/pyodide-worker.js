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
//   {type:"generate", id, model, params}    // param build (cacheable)
//   {type:"generate", id, model, source}    // live code edit (never cached)

importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.0a3/full/pyodide.js");

let pyodide = null;
const cache = new Map(); // JSON({model,params}) -> {stl:Uint8Array, glb:Uint8Array|null}

const status = (text) => self.postMessage({ type: "status", text });
const log = (text) => self.postMessage({ type: "log", text });

// Install OpenCASCADE (the big one) + build123d from the OCP.wasm index, then
// stub out ocp_vscode so models that `from ocp_vscode import show` at module top
// level (lens_cap, satellite_led) import cleanly in the headless runtime.
const SETUP = `
import micropip
micropip.set_index_urls(["https://yeicor.github.io/OCP.wasm", "https://pypi.org/simple"])
print("installing lib3mf ...")
await micropip.install("lib3mf")
micropip.add_mock_package("py-lib3mf", "2.4.1", modules={"py_lib3mf": "from lib3mf import *"})
print("installing OpenCASCADE WASM (cadquery-ocp, the big one) ...")
await micropip.install("cadquery-ocp")
micropip.add_mock_package("cadquery-ocp-novtk", "7.9.3.0")
print("installing build123d ...")
await micropip.install(["build123d", "sqlite3"])

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

// Build one model. SOURCE is the edited text for a live code edit, or None for a
// plain parameter build. On a source edit we purge EVERY models.* module (not
// just the edited one) because models import each other -- a stale dependency in
// sys.modules would silently run old code and yield wrong geometry.
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

def _run(model, params_json, source):
    if source is not None:
        with open("/models/" + model + ".py", "w") as f:
            f.write(source)
        for k in [k for k in sys.modules if k == "models" or k.startswith("models.")]:
            del sys.modules[k]
        importlib.invalidate_caches()
    mod = importlib.import_module("models." + model)
    params = json.loads(params_json) if params_json else {}
    t = time.time()
    part = mod.create(**params)       # Part or Compound; exporters handle both
    cad_ms = round((time.time() - t) * 1000)
    export_stl(part, "/tmp/out.stl", tolerance=0.1)   # colourless, drives downloads
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

_run(MODEL, PARAMS_JSON, SOURCE)
`;

async function boot() {
  status("Booting Python WebAssembly runtime…");
  pyodide = await loadPyodide({ stdout: log, stderr: log });
  status("Installing numpy / micropip…");
  await pyodide.loadPackage(["micropip", "numpy", "sqlite3", "typing-extensions"]);
  status("Downloading build123d + OpenCASCADE WASM (~40 MB, cached after)…");
  await pyodide.runPythonAsync(SETUP);

  status("Loading model sources…");
  const sources = await (await fetch("../py-sources.json")).json();
  pyodide.FS.mkdirTree("/models");
  for (const [path, text] of Object.entries(sources)) {
    // path is like "models/cube.py"; write it at the FS root so "import models.x" works
    const full = "/" + path;
    const dir = full.slice(0, full.lastIndexOf("/"));
    pyodide.FS.mkdirTree(dir);
    pyodide.FS.writeFile(full, text);
  }
  pyodide.runPython("import sys; sys.path.insert(0, '/')");

  log("runtime ready ✔");
  self.postMessage({ type: "ready" });
}

const bootPromise = boot().catch((e) =>
  self.postMessage({ type: "error", message: "boot: " + (e.message || e) })
);

self.onmessage = async (ev) => {
  const msg = ev.data;
  if (msg.type !== "generate") return;
  await bootPromise;
  if (!pyodide) return;

  const isEdit = typeof msg.source === "string";
  const params = msg.params || {};
  const key = JSON.stringify({ model: msg.model, params });

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
    pyodide.globals.set("MODEL", msg.model);
    pyodide.globals.set("PARAMS_JSON", isEdit ? "" : JSON.stringify(params));
    pyodide.globals.set("SOURCE", isEdit ? msg.source : null);

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
    self.postMessage({ type: "error", id: msg.id, message: e.message || String(e) });
  }
};
