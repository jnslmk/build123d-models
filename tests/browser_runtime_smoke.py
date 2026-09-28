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
            # website.build_web_bundle() writes this same dictionary to the site.
            # Stage it outside the checkout so this test never modifies site assets.
            (root / "py-sources.json").write_text(json.dumps(website._py_sources()))
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
                                let defaultWidth;
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
                                                    params: {}});
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
                                                        params: {inner_dia: 70}});
                                                } else if (data.id === 2) {
                                                    resolve({triangles, defaultWidth, width});
                                                } else {
                                                    fail('unexpected build result id: ' + data.id);
                                                }
                                            }
                                        };
                                        worker.postMessage({type: 'init',
                                            sourcesUrl: new URL('./py-sources.json', document.baseURI).href});
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
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()
