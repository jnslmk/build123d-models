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
const cache = new Map(); // JSON({model,params}) -> Uint8Array (STL bytes)

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
from build123d import export_stl, export_step

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
    part = mod.create(**params)       # Part or Compound; export_stl handles both
    cad_ms = round((time.time() - t) * 1000)
    export_stl(part, "/tmp/out.stl", tolerance=0.1)
    have_step = False
    try:
        export_step(part, "/tmp/out.step")
        have_step = True
    except Exception as exc:            # STEP is best-effort; never block the STL
        print("step export skipped:", exc)
    return json.dumps({"cadMs": cad_ms, "step": have_step})

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
    const copy = new Uint8Array(cache.get(key));
    self.postMessage(
      { type: "result", id: msg.id, model: msg.model, cached: true, cadMs: 0, wallMs: 0, stl: copy.buffer, step: null },
      [copy.buffer]
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
    if (!isEdit) cache.set(key, new Uint8Array(stlBytes)); // keep a copy for the cache

    let stepBuf = null;
    const transfer = [stlBytes.buffer];
    if (meta.step) {
      const stepBytes = new Uint8Array(pyodide.FS.readFile("/tmp/out.step"));
      stepBuf = stepBytes.buffer;
      transfer.push(stepBuf);
    }

    self.postMessage(
      {
        type: "result", id: msg.id, model: msg.model, cached: false,
        cadMs: meta.cadMs, wallMs: Math.round(performance.now() - t0),
        stl: stlBytes.buffer, step: stepBuf,
      },
      transfer
    );
  } catch (e) {
    self.postMessage({ type: "error", id: msg.id, message: e.message || String(e) });
  }
};
