"""Exercise the shipped worker in Chromium with sources bundled for the site.

Run with ``uv run --with playwright==1.58.0 python -m unittest tests.browser_runtime_smoke``.
This deliberately does not match unittest discovery's test_*.py pattern: installing
Chromium and downloading the WASM runtime belong to the dedicated CI job.
"""

from __future__ import annotations

import functools
import http.server
import json
import math
import os
import tempfile
import threading
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

import website


def _stage_page(
    root: Path, names: tuple[str, ...], *, with_worker: bool = False
) -> dict:
    """Build a small real GLB preview instead of relying on ignored CI exports."""
    from build123d import Box, export_gltf

    for filename in ("index.html", "viewer.js"):
        (root / filename).write_bytes((website.WEBSITE_DIR / filename).read_bytes())
    (root / "exports").mkdir()
    models = []
    for index, name in enumerate(names):
        export_gltf(
            Box(10 + index, 10, 10),
            str(root / "exports" / f"{name}.glb"),
            binary=True,
        )
        models.append(
            {
                "name": name,
                "label": name.replace("_", " ").title(),
                "source": website._source_path(name),
                "params": [],
                "assembly": False,
                "updated": None,
                "stl": None,
                "step": None,
                "glb": f"exports/{name}.glb",
                "thumb": None,
            }
        )
    if with_worker:
        (root / "js").mkdir()
        (root / "js" / "pyodide-worker.js").write_bytes(
            (website.WEBSITE_DIR / "js" / "pyodide-worker.js").read_bytes()
        )
        (root / "browser-wheels").mkdir()
        wheel = "build123d-0.11.1-py3-none-any.whl"
        (root / "browser-wheels" / wheel).write_bytes(
            (website.WEBSITE_DIR / "browser-wheels" / wheel).read_bytes()
        )
    assets = {"models": models}
    website._write_source_assets(assets, root)
    (root / "models-manifest.json").write_text(json.dumps(assets))
    return assets


class BrowserRuntimeSmoke(unittest.TestCase):
    def test_pyodide_boots_and_rebuilds_lens_cap_with_new_diameter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "js").mkdir()
            (root / "js" / "pyodide-worker.js").write_bytes(
                (website.WEBSITE_DIR / "js" / "pyodide-worker.js").read_bytes()
            )
            (root / "browser-wheels").mkdir()
            wheel = "build123d-0.11.1-py3-none-any.whl"
            (root / "browser-wheels" / wheel).write_bytes(
                (website.WEBSITE_DIR / "browser-wheels" / wheel).read_bytes()
            )
            # Stage only the selected model's closure for parameter rebuilds.
            assets = {
                "models": [
                    {"name": "lens_cap", "source": "models/lens_cap/__init__.py"}
                ]
            }
            website._write_source_assets(assets, root)
            variant = json.loads((root / assets["models"][0]["sources"]).read_text())
            own_source = assets["models"][0]["source"]
            self.assertIn("WALL_THICKNESS = 1.2", variant[own_source])
            variant[own_source] = variant[own_source].replace(
                "WALL_THICKNESS = 1.2", "WALL_THICKNESS = 1.6"
            )
            (root / "model-sources" / "lens_cap-variant.json").write_text(
                json.dumps(variant)
            )
            (root / "models-manifest.json").write_text(json.dumps(assets))
            (root / "index.html").write_text(
                "<!doctype html><title>Browser CAD smoke</title>"
            )

            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=str(root)
            )
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        try:
                            page = browser.new_page()
                            timeout_ms = int(
                                os.environ.get("BROWSER_SMOKE_TIMEOUT_MS", "720000")
                            )
                            page.set_default_timeout(timeout_ms + 60_000)
                            page.goto(f"http://127.0.0.1:{server.server_port}/")
                            # Promise rejects for boot errors, failed imports, worker crashes,
                            # generation errors and timeouts; it never accepts a cached STL.
                            result = page.evaluate(
                                """async (timeoutMs) => {
                                const worker = new Worker('./js/pyodide-worker.js');
                                const assets = await (await fetch('models-manifest.json')).json();
                                const sourcesUrl = new URL(assets.models[0].sources, document.baseURI).href;
                                const editSourcesUrl = new URL(assets.editSources, document.baseURI).href;
                                const changedUrl = new URL('./model-sources/lens_cap-variant.json', document.baseURI).href;
                                let defaultWidth, widthWithDiameter;
                                let lastStatus = 'loading worker script';
                                try {
                                    return await new Promise((resolve, reject) => {
                                        const fail = (reason) => {
                                            clearTimeout(timer);
                                            reject(new Error(reason));
                                        };
                                        timer = setTimeout(() => fail('worker boot/build timed out at: ' + lastStatus), timeoutMs);
                                        worker.onerror = (event) => fail('worker crashed: ' + event.message);
                                        worker.onmessageerror = () => fail('worker message could not be decoded');
                                        worker.onmessage = ({data}) => {
                                            if (data.type === 'status') {
                                                lastStatus = data.text;
                                            } else if (data.type === 'error') {
                                                fail('worker error: ' + data.message);
                                            } else if (data.type === 'ready') {
                                                worker.postMessage({type: 'generate', id: 1,
                                                    model: 'lens_cap', sourcePath: 'models/lens_cap/__init__.py',
                                                    sourcesUrl, editSourcesUrl, params: {}});
                                            } else if (data.type === 'result') {
                                                if (data.cached || !(data.stl instanceof ArrayBuffer)) {
                                                    fail('expected freshly generated STL ArrayBuffer');
                                                    return;
                                                }
                                                const view = new DataView(data.stl);
                                                if (view.byteLength < 84) {
                                                    fail('STL too short');
                                                    return;
                                                }
                                                const triangles = view.getUint32(80, true);
                                                if (!triangles || view.byteLength !== 84 + triangles * 50) {
                                                    fail('invalid binary STL triangle table');
                                                    return;
                                                }
                                                let minX = Infinity, maxX = -Infinity;
                                                for (let i = 0; i < triangles; i++) {
                                                    const offset = 84 + i * 50;
                                                    for (const vertex of [12, 24, 36]) {
                                                        const x = view.getFloat32(offset + vertex, true);
                                                        const y = view.getFloat32(offset + vertex + 4, true);
                                                        const z = view.getFloat32(offset + vertex + 8, true);
                                                        if (!Number.isFinite(x) || !Number.isFinite(y) ||
                                                            !Number.isFinite(z)) {
                                                            fail('non-finite STL vertex');
                                                            return;
                                                        }
                                                        minX = Math.min(minX, x);
                                                        maxX = Math.max(maxX, x);
                                                    }
                                                }
                                                const width = maxX - minX;
                                                if (data.id === 1) {
                                                    defaultWidth = width;
                                                    worker.postMessage({type: 'generate', id: 2,
                                                        model: 'lens_cap', sourcePath: 'models/lens_cap/__init__.py',
                                                        sourcesUrl, editSourcesUrl, params: {inner_dia: 70}});
                                                } else if (data.id === 2) {
                                                    widthWithDiameter = width;
                                                    worker.postMessage({type: 'generate', id: 3,
                                                        model: 'lens_cap', sourcePath: 'models/lens_cap/__init__.py',
                                                        sourcesUrl: changedUrl, editSourcesUrl, params: {}});
                                                } else if (data.id === 3) {
                                                    resolve({triangles, defaultWidth, width: widthWithDiameter, changedWidth: width});
                                                } else {
                                                    fail('unexpected build result id: ' + data.id);
                                                }
                                            }
                                        };
                                        worker.postMessage({type: 'init',
                                            baseUrl: new URL('./', document.baseURI).href});
                                    });
                                } finally {
                                    clearTimeout(timer);
                                    worker.terminate();
                                }
                            }""",
                                timeout_ms,
                            )
                            self.assertGreater(result["triangles"], 0)
                            # A changed bore must produce a second, uncached mesh:
                            # default 51 + 2*1.2 mm walls, then 70 + 2*1.2 mm.
                            self.assertTrue(
                                math.isclose(result["defaultWidth"], 53.4, abs_tol=0.2),
                                result,
                            )
                            self.assertTrue(
                                math.isclose(result["width"], 72.4, abs_tol=0.2), result
                            )
                            self.assertTrue(
                                math.isclose(result["changedWidth"], 54.2, abs_tol=0.2),
                                result,
                            )
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()


class BrowserPageSourceSmoke(unittest.TestCase):
    def test_prebuilt_preview_and_code_revert_survive_model_switch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = _stage_page(root, ("lens_cap", "door_latch"))
            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=str(root)
            )
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        try:
                            page = browser.new_page()
                            page.set_default_timeout(90_000)
                            requests = []
                            page.on(
                                "request", lambda request: requests.append(request.url)
                            )
                            stale = json.loads(json.dumps(assets))
                            stale["models"][0]["sources"] = (
                                "model-sources/lens_cap.removed.json"
                            )
                            manifest_requests = []

                            def serve_manifest(route):
                                manifest_requests.append(route.request.url)
                                if len(manifest_requests) == 1:
                                    route.fulfill(json=stale)
                                else:
                                    route.continue_()

                            page.route("**/models-manifest.json", serve_manifest)
                            page.goto(
                                f"http://127.0.0.1:{server.server_port}/",
                                wait_until="networkidle",
                            )
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').classList.contains('hidden')"
                            )
                            self.assertIn("/exports/lens_cap.glb", " ".join(requests))
                            self.assertFalse(
                                any(
                                    "model-sources/" in url or "py-sources.json" in url
                                    for url in requests
                                ),
                                requests,
                            )
                            self.assertEqual(
                                page.locator("#runtime").inner_text(), "Python: off"
                            )

                            page.click("#btn-code")
                            page.wait_for_function(
                                "() => !document.querySelector('#btn-run').disabled",
                                timeout=15_000,
                            )
                            self.assertIn(
                                "Push-on camera lens cap",
                                page.locator(".cm-content").inner_text(),
                            )
                            self.assertTrue(
                                any(
                                    "model-sources/lens_cap." in url for url in requests
                                ),
                                requests,
                            )
                            self.assertGreaterEqual(len(manifest_requests), 2)
                            self.assertTrue(
                                any("lens_cap.removed.json" in url for url in requests)
                            )
                            page.locator(".cm-content").click()
                            page.keyboard.insert_text("# changed")
                            self.assertIn(
                                "edited", page.locator("#edit-dirty").inner_text()
                            )
                            page.click("#btn-revert")
                            self.assertEqual(
                                page.locator("#edit-dirty").inner_text(), ""
                            )

                            failed_asset = "**/model-sources/door_latch.*.json"
                            page.route(
                                failed_asset,
                                lambda route: route.fulfill(
                                    status=503, body="unavailable"
                                ),
                            )
                            page.select_option("#family", "door_latch")
                            page.wait_for_function(
                                "() => document.querySelector('#cm-loading').textContent.includes('HTTP 503')"
                            )
                            self.assertTrue(page.locator("#btn-run").is_disabled())
                            self.assertNotIn(
                                "source unavailable",
                                page.locator(".cm-content").inner_text(),
                            )
                            page.unroute(failed_asset)
                            page.click("#btn-code")
                            page.click("#btn-code")
                            page.wait_for_function(
                                "() => !document.querySelector('#btn-run').disabled && "
                                "document.querySelector('#edit-file').textContent.includes('door_latch')"
                            )
                            self.assertIn(
                                "Rounded L-shaped door latch",
                                page.locator(".cm-content").inner_text(),
                            )
                            self.assertTrue(
                                any(
                                    "model-sources/door_latch." in url
                                    for url in requests
                                ),
                                requests,
                            )
                            self.assertFalse(
                                any("py-sources.json" in url for url in requests)
                            )
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()

    def test_old_tab_refreshes_manifest_after_parameter_source_404(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = _stage_page(root, ("lens_cap",), with_worker=True)
            stale = json.loads(json.dumps(assets))
            stale["models"][0]["sources"] = "model-sources/lens_cap.removed.json"
            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=str(root)
            )
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        try:
                            page = browser.new_page()
                            page.set_default_timeout(120_000)
                            manifest_requests = []

                            def serve_manifest(route):
                                manifest_requests.append(route.request.url)
                                if len(manifest_requests) == 1:
                                    route.fulfill(json=stale)
                                else:
                                    route.continue_()

                            page.route("**/models-manifest.json", serve_manifest)
                            page.goto(
                                f"http://127.0.0.1:{server.server_port}/",
                                wait_until="networkidle",
                            )
                            page.click("#runtime")
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').textContent.includes('built in')"
                            )
                            self.assertGreaterEqual(len(manifest_requests), 2)
                            self.assertIn(
                                "HTTP 404", page.locator("#log").text_content()
                            )
                            self.assertEqual(
                                page.locator("#runtime").inner_text(), "Python: ready"
                            )
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()

    def test_old_source_failure_cannot_overwrite_new_model_preview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = _stage_page(root, ("lens_cap", "door_latch"), with_worker=True)
            stale = json.loads(json.dumps(assets))
            stale["models"][0]["sources"] = "model-sources/lens_cap.removed.json"
            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=str(root)
            )
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        try:
                            page = browser.new_page()
                            page.set_default_timeout(120_000)
                            page.add_init_script("""(() => {
                                const realFetch = window.fetch.bind(window);
                                window.fetch = (url, options) => {
                                    if (String(url).includes('models-manifest.json') &&
                                        options?.cache === 'no-store') {
                                        return new Promise(resolve => {
                                            window.releaseSourceRefresh = async () => {
                                                const response = await realFetch(url, options);
                                                const parse = response.json.bind(response);
                                                response.json = async () => {
                                                    const data = await parse();
                                                    window.sourceRefreshConsumed = true;
                                                    return data;
                                                };
                                                resolve(response);
                                            };
                                        });
                                    }
                                    return realFetch(url, options);
                                };
                            })();""")
                            manifest_requests = []

                            def serve_manifest(route):
                                manifest_requests.append(route.request.url)
                                if len(manifest_requests) == 1:
                                    route.fulfill(json=stale)
                                else:
                                    route.continue_()

                            page.route("**/models-manifest.json", serve_manifest)
                            page.goto(
                                f"http://127.0.0.1:{server.server_port}/",
                                wait_until="networkidle",
                            )
                            page.click("#runtime")
                            page.wait_for_function(
                                "() => typeof window.releaseSourceRefresh === 'function'"
                            )
                            page.select_option("#family", "door_latch")
                            page.wait_for_function(
                                "() => new URL(location).searchParams.get('model') === 'door_latch' && "
                                "document.querySelector('#vstatus').classList.contains('hidden')"
                            )
                            page.evaluate("window.releaseSourceRefresh()")
                            page.wait_for_function("() => window.sourceRefreshConsumed")
                            page.wait_for_timeout(300)
                            self.assertIn(
                                "hidden",
                                page.locator("#vstatus").get_attribute("class"),
                            )
                            self.assertNotIn(
                                "source asset missing",
                                page.locator("#vstatus").text_content(),
                            )
                            self.assertEqual(
                                page.locator("#runtime").inner_text(), "Python: ready"
                            )
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()

    def test_cycled_selection_rejects_stale_worker_404_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = _stage_page(root, ("lens_cap", "door_latch"))
            assets["models"][0]["params"] = [
                {
                    "name": "width",
                    "label": "Width",
                    "type": "number",
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                }
            ]
            (root / "models-manifest.json").write_text(json.dumps(assets))
            stale = json.loads(json.dumps(assets))
            stale["models"][0]["sources"] = "model-sources/lens_cap.removed.json"
            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=str(root)
            )
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        try:
                            page = browser.new_page()
                            page.set_default_timeout(90_000)
                            page.add_init_script("""(() => {
                                const realFetch = window.fetch.bind(window);
                                window.sourceRefreshRequests = 0;
                                window.fetch = (url, options) => {
                                    if (String(url).includes('models-manifest.json') &&
                                        options?.cache === 'no-store') {
                                        window.sourceRefreshRequests++;
                                        return new Promise(resolve => {
                                            window.releaseSourceRefresh = async () => {
                                                const response = await realFetch(url, options);
                                                const parse = response.json.bind(response);
                                                response.json = async () => {
                                                    const data = await parse();
                                                    window.sourceRefreshConsumed = true;
                                                    return data;
                                                };
                                                resolve(response);
                                            };
                                        });
                                    }
                                    return realFetch(url, options);
                                };
                                window.generatedJobs = [];
                                window.Worker = class {
                                    constructor() { window.fakeWorker = this; }
                                    postMessage(message) {
                                        if (message.type === 'init') {
                                            queueMicrotask(() => this.onmessage({data: {type: 'ready'}}));
                                        } else if (message.type === 'generate') {
                                            window.generatedJobs.push(message);
                                        }
                                    }
                                };
                                window.deliverError = (index) => {
                                    const job = window.generatedJobs[index];
                                    window.fakeWorker.onmessage({data: {
                                        type: 'error', id: job.id, model: job.model,
                                        message: 'source asset: HTTP 404', httpStatus: 404,
                                    }});
                                };
                                window.deliverResult = (index, triangles) => {
                                    const job = window.generatedJobs[index];
                                    const stl = new ArrayBuffer(84 + triangles * 50);
                                    const view = new DataView(stl);
                                    view.setUint32(80, triangles, true);
                                    for (let i = 0; i < triangles; i++) {
                                        const offset = 84 + i * 50;
                                        view.setFloat32(offset + 12, i, true);
                                        view.setFloat32(offset + 24, i + 1, true);
                                        view.setFloat32(offset + 36, i + 2, true);
                                        view.setFloat32(offset + 40, 1, true);
                                    }
                                    window.fakeWorker.onmessage({data: {
                                        type: 'result', id: job.id, model: job.model,
                                        stl, cached: false, wallMs: 1200,
                                    }});
                                };
                            })();""")
                            manifest_requests = []

                            def serve_manifest(route):
                                manifest_requests.append(route.request.url)
                                if len(manifest_requests) == 1:
                                    route.fulfill(json=stale)
                                else:
                                    route.continue_()

                            page.route("**/models-manifest.json", serve_manifest)
                            page.goto(
                                f"http://127.0.0.1:{server.server_port}/",
                                wait_until="networkidle",
                            )
                            page.click("#runtime")
                            page.wait_for_function(
                                "() => window.generatedJobs.length === 1"
                            )
                            page.select_option("#family", "door_latch")
                            page.select_option("#family", "lens_cap")
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').classList.contains('hidden')"
                            )
                            page.evaluate("""window.fakeWorker.onmessage({data: {
                                type: 'status', text: 'Loading old model sources…',
                            }})""")
                            self.assertIn(
                                "hidden",
                                page.locator("#vstatus").get_attribute("class"),
                            )
                            page.evaluate("window.deliverError(0)")
                            self.assertEqual(
                                page.evaluate("window.sourceRefreshRequests"), 0
                            )
                            self.assertEqual(
                                page.evaluate("window.generatedJobs.length"), 1
                            )
                            self.assertIn(
                                "hidden",
                                page.locator("#vstatus").get_attribute("class"),
                            )
                            self.assertTrue(page.locator("#btn-stl").is_disabled())

                            # A refresh started before the switch must not revive the old job.
                            page.locator('input[data-name="width"]').fill("12")
                            page.wait_for_function(
                                "() => window.generatedJobs.length === 2"
                            )
                            page.evaluate("window.deliverError(1)")
                            page.wait_for_function(
                                "() => window.sourceRefreshRequests === 1"
                            )
                            page.select_option("#family", "door_latch")
                            page.select_option("#family", "lens_cap")
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').classList.contains('hidden')"
                            )
                            page.evaluate("window.releaseSourceRefresh()")
                            page.wait_for_function(
                                "() => window.sourceRefreshConsumed === true"
                            )
                            page.evaluate(
                                "() => new Promise(resolve => setTimeout(resolve, 0))"
                            )
                            self.assertEqual(
                                page.evaluate("window.generatedJobs.length"), 2
                            )
                            self.assertTrue(page.locator("#btn-stl").is_disabled())
                            self.assertIn(
                                "hidden",
                                page.locator("#vstatus").get_attribute("class"),
                            )

                            page.locator('input[data-name="width"]').fill("13")
                            page.wait_for_function(
                                "() => window.generatedJobs.length === 3"
                            )
                            page.select_option("#family", "door_latch")
                            page.select_option("#family", "lens_cap")
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').classList.contains('hidden')"
                            )
                            page.locator('input[data-name="width"]').fill("14")
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').textContent.includes('queued')"
                            )
                            page.evaluate("window.deliverResult(2, 2)")
                            page.wait_for_function(
                                "() => window.generatedJobs.length === 4"
                            )
                            self.assertTrue(page.locator("#btn-stl").is_disabled())
                            page.evaluate("window.deliverResult(3, 1)")
                            page.wait_for_function(
                                "() => document.querySelector('#vstatus').textContent.includes('1 triangles')"
                            )
                            self.assertFalse(page.locator("#btn-stl").is_disabled())
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()
