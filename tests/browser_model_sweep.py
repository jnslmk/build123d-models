#!/usr/bin/env python3
"""Sweep published models through the real browser CAD worker.

Run separately from unittest discovery:
    uv run --with playwright==1.58.0 python tests/browser_model_sweep.py
    uv run --with playwright==1.58.0 python tests/browser_model_sweep.py \\
        --start-at led_profiles.stand --stop-at led_profiles.stand.leg

Chromium must be installed (``python -m playwright install chromium``). The
worker downloads Pyodide and WASM wheels on first run; the browser needs network
access. Each model emits a JSON result line, followed by a JSON summary.
The worker treats STEP and glTF as best-effort exports; STL is required.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402

import website  # noqa: E402
from tessellate_models import MODELS  # noqa: E402


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-timeout-ms", type=int, default=720_000)
    parser.add_argument("--model-timeout-ms", type=int, default=600_000)
    parser.add_argument("--start-at", choices=MODELS, help="resume from this model")
    parser.add_argument(
        "--stop-at", choices=MODELS, help="include this as the last model"
    )
    args = parser.parse_args()
    if min(args.boot_timeout_ms, args.model_timeout_ms) <= 0:
        parser.error("timeouts must be positive")

    manifest = website._manifest()["models"]
    if [item["name"] for item in manifest] != MODELS:
        raise ValueError("website manifest does not match tessellate_models.MODELS")
    if args.start_at:
        manifest = manifest[MODELS.index(args.start_at) :]
    if args.stop_at:
        manifest = manifest[
            : next(i for i, item in enumerate(manifest) if item["name"] == args.stop_at)
            + 1
        ]
    selected = [item["name"] for item in manifest]

    results: dict[str, dict] = {}

    def report(row: dict) -> None:
        results[row["model"]] = row
        print(json.dumps(row, sort_keys=True), flush=True)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        website.stage_browser_runtime(root)
        assets = {"models": manifest}
        website._write_source_assets(assets, root)
        (root / "index.html").write_text(
            "<!doctype html><title>Browser model sweep</title>"
        )
        handler = functools.partial(_QuietHandler, directory=str(root))
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    try:
                        page = browser.new_page()
                        page.goto(
                            f"http://127.0.0.1:{server.server_port}/",
                            wait_until="networkidle",
                        )
                        page.expose_function("reportSweep", report)
                        page.evaluate(
                            """async ({models, editSources, bootTimeout, modelTimeout}) => {
                                let worker = null;
                                let pending = null;
                                let bootWait = null;
                                let lastStatus = 'loading worker script';
                                let logs = [];
                                const editSourcesUrl = new URL(editSources, document.baseURI).href;

                                function stopWorker(reason) {
                                    if (worker) worker.terminate();
                                    worker = null;
                                    if (bootWait) {
                                        const reject = bootWait;
                                        bootWait = null;
                                        reject(new Error(reason));
                                    }
                                    if (pending) {
                                        const resolve = pending;
                                        pending = null;
                                        resolve({type: 'error', message: reason});
                                    }
                                }
                                async function startWorker() {
                                    logs = [];
                                    lastStatus = 'loading worker script';
                                    worker = new Worker('./js/pyodide-worker.js');
                                    await new Promise((resolve, reject) => {
                                        const timer = setTimeout(() =>
                                            stopWorker('boot timed out at: ' + lastStatus), bootTimeout);
                                        bootWait = (error) => { clearTimeout(timer); reject(error); };
                                        worker.onerror = (event) =>
                                            stopWorker('worker crashed: ' + event.message);
                                        worker.onmessageerror = () =>
                                            stopWorker('worker message could not be decoded');
                                        worker.onmessage = ({data}) => {
                                            if (data.type === 'status') lastStatus = data.text;
                                            else if (data.type === 'log') {
                                                logs.push(data.text);
                                                if (logs.length > 15) logs.shift();
                                            } else if (data.type === 'ready') {
                                                clearTimeout(timer);
                                                bootWait = null;
                                                resolve();
                                            } else if (data.type === 'error' && data.id == null) {
                                                stopWorker('boot: ' + data.message);
                                            } else if (pending) {
                                                const done = pending;
                                                pending = null;
                                                done(data);
                                            }
                                        };
                                        worker.postMessage({type: 'init',
                                            baseUrl: new URL('./', document.baseURI).href});
                                    });
                                }
                                async function generate(item, id) {
                                    return await new Promise((resolve) => {
                                        const timer = setTimeout(() =>
                                            stopWorker('build timed out at: ' + item.name), modelTimeout);
                                        pending = (data) => { clearTimeout(timer); resolve(data); };
                                        worker.postMessage({type: 'generate', id,
                                            model: item.name, sourcePath: item.source,
                                            sourcesUrl: new URL(item.sources, document.baseURI).href,
                                            editSourcesUrl, params: {}});
                                    });
                                }
                                function stlTriangles(buffer) {
                                    if (!(buffer instanceof ArrayBuffer) || buffer.byteLength < 184)
                                        throw new Error('missing or trivial binary STL');
                                    const view = new DataView(buffer);
                                    const triangles = view.getUint32(80, true);
                                    if (triangles < 2 || buffer.byteLength !== 84 + triangles * 50)
                                        throw new Error('invalid STL triangle table');
                                    return triangles;
                                }
                                function glbMeshes(buffer) {
                                    if (!(buffer instanceof ArrayBuffer) || buffer.byteLength < 32)
                                        throw new Error('missing or trivial GLB');
                                    const view = new DataView(buffer);
                                    if (view.getUint32(0, true) !== 0x46546c67 ||
                                        view.getUint32(4, true) !== 2 ||
                                        view.getUint32(8, true) !== buffer.byteLength ||
                                        view.getUint32(16, true) !== 0x4e4f534a ||
                                        view.getUint32(12, true) + 20 > buffer.byteLength)
                                        throw new Error('invalid GLB header/JSON chunk');
                                    const text = new TextDecoder().decode(
                                        new Uint8Array(buffer, 20, view.getUint32(12, true)));
                                    const meshes = JSON.parse(text).meshes;
                                    if (!Array.isArray(meshes) ||
                                        !meshes.some(mesh => mesh.primitives?.length > 0))
                                        throw new Error('GLB contains no mesh primitives');
                                    return meshes.length;
                                }

                                let bootError = null;
                                try {
                                    for (let id = 0; id < models.length; id++) {
                                        const item = models[id];
                                        const started = performance.now();
                                        const row = {model: item.name, assembly: item.assembly};
                                        try {
                                            if (bootError) throw new Error(bootError);
                                            if (!worker) {
                                                try { await startWorker(); }
                                                catch (error) {
                                                    bootError = String(error);
                                                    throw error;
                                                }
                                            }
                                            const data = await generate(item, id);
                                            if (data.type !== 'result' || data.id !== id ||
                                                data.model !== item.name || data.cached)
                                                throw new Error(data.message || 'wrong/uncached worker response');
                                            row.triangles = stlTriangles(data.stl);
                                            row.stlBytes = data.stl.byteLength;
                                            row.glbBytes = data.glb?.byteLength || 0;
                                            row.glbMeshes = data.glb ? glbMeshes(data.glb) : 0;
                                            row.stepBytes = data.step?.byteLength || 0;
                                            if (data.step && row.stepBytes < 100)
                                                throw new Error('trivial STEP export');
                                            row.cadMs = data.cadMs;
                                            row.workerMs = data.wallMs;
                                            row.ok = true;
                                        } catch (error) {
                                            row.ok = false;
                                            row.error = String(error);
                                            row.logs = logs.slice();
                                        }
                                        row.elapsedMs = Math.round(performance.now() - started);
                                        await window.reportSweep(row);
                                    }
                                } finally {
                                    if (worker) worker.terminate();
                                }
                            }""",
                            {
                                "models": [
                                    {
                                        "name": item["name"],
                                        "source": item["source"],
                                        "sources": item["sources"],
                                        "assembly": item["assembly"],
                                    }
                                    for item in manifest
                                ],
                                "editSources": assets["editSources"],
                                "bootTimeout": args.boot_timeout_ms,
                                "modelTimeout": args.model_timeout_ms,
                            },
                        )
                    finally:
                        browser.close()
            except Exception as exc:
                # Preserve completed rows even if Chromium exits unexpectedly.
                for item in manifest:
                    if item["name"] not in results:
                        report(
                            {
                                "model": item["name"],
                                "assembly": item["assembly"],
                                "ok": False,
                                "error": f"browser sweep aborted: {exc}",
                            }
                        )
            finally:
                server.shutdown()
                thread.join()

    failed = [name for name in selected if not results[name]["ok"]]
    print(
        json.dumps(
            {
                "total": len(selected),
                "passed": len(selected) - len(failed),
                "failed": failed,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
