"""Real browser proof of lazy scikit-learn and the edited-source public API.

Run separately: uv run --with playwright==1.58.0 python -m unittest tests.browser_lazy_dependency
"""

from __future__ import annotations

import functools
import http.server
import json
import tempfile
import threading
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

import website


EDITED_SOURCE = """\
from build123d import Box, detect_primitives
from models.led_profiles import config as profile
from importlib.metadata import version
from sklearn.cluster import DBSCAN


def create():
    assert version('build123d') == '0.11.1'
    assert profile.WIDTH == 26.1
    assert DBSCAN.__module__ == 'sklearn.cluster._dbscan'
    assert list(DBSCAN(eps=1, min_samples=2).fit([[0], [0.5], [10]]).labels_) == [0, 0, -1]
    part = Box(10, 10, 10)
    faces, leftovers, code = detect_primitives(part)
    assert len(faces) + len(leftovers) > 0
    return part
"""


class BrowserLazyDependency(unittest.TestCase):
    def test_default_then_edited_detect_primitives(self) -> None:
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
            assets = {
                "models": [
                    {"name": "lens_cap", "source": "models/lens_cap/__init__.py"}
                ]
            }
            website._write_source_assets(assets, root)
            (root / "models-manifest.json").write_text(json.dumps(assets))
            (root / "index.html").write_text(
                "<!doctype html><title>Browser CAD</title>"
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
                            page.set_default_timeout(720_000)
                            requests: list[str] = []
                            page.on(
                                "request", lambda request: requests.append(request.url)
                            )
                            page.expose_function(
                                "getSklearnRequestCount",
                                lambda: sum(
                                    "scikit_learn" in url or "scikit-learn" in url
                                    for url in requests
                                ),
                            )
                            page.goto(f"http://127.0.0.1:{server.server_port}/")
                            result = page.evaluate(
                                """async (source) => {
                                    const worker = new Worker('./js/pyodide-worker.js');
                                    const assets = await (await fetch('models-manifest.json')).json();
                                    const sourcesUrl = new URL(assets.models[0].sources, document.baseURI).href;
                                    const editSourcesUrl = new URL(assets.editSources, document.baseURI).href;
                                    let status = 'loading worker';
                                    let next = null;
                                    try {
                                        await new Promise((resolve, reject) => {
                                            const timer = setTimeout(() => reject(
                                                new Error('boot timed out: ' + status)), 600000);
                                            worker.onerror = (event) => reject(new Error(event.message));
                                            worker.onmessage = ({data}) => {
                                                if (data.type === 'status') status = data.text;
                                                if (data.type === 'error') {
                                                    if (next) {
                                                        const finish = next;
                                                        next = null;
                                                        finish.reject(new Error(data.message));
                                                    } else reject(new Error(data.message));
                                                }
                                                if (data.type === 'ready') {
                                                    clearTimeout(timer);
                                                    resolve();
                                                }
                                                if (data.type === 'result' && next) {
                                                    const finish = next;
                                                    next = null;
                                                    finish.resolve(data);
                                                }
                                            };
                                            worker.postMessage({type: 'init',
                                                baseUrl: new URL('./', document.baseURI).href});
                                        });
                                        const generate = (id, edit) => new Promise((resolve, reject) => {
                                            const timer = setTimeout(() =>
                                                reject(new Error('build timed out: ' + status)), 180000);
                                            next = {
                                                resolve: (data) => {clearTimeout(timer); resolve(data);},
                                                reject: (error) => {clearTimeout(timer); reject(error);}
                                            };
                                            worker.postMessage({type: 'generate', id,
                                                model: 'lens_cap',
                                                sourcePath: 'models/lens_cap/__init__.py',
                                                sourcesUrl, editSourcesUrl,
                                                ...(edit ? {source} : {params: {}})});
                                        });
                                        const first = await generate(1, false);
                                        const defaultSklearnRequests = await window.getSklearnRequestCount();
                                        const second = await generate(2, true);
                                        return {defaultStl: first.stl?.byteLength,
                                            defaultCached: first.cached,
                                            defaultSklearnRequests,
                                            editedStl: second.stl?.byteLength,
                                            editedCached: second.cached};
                                    } finally { worker.terminate(); }
                                }""",
                                EDITED_SOURCE,
                            )
                            self.assertGreater(result["defaultStl"], 84, result)
                            self.assertFalse(result["defaultCached"], result)
                            self.assertEqual(
                                result["defaultSklearnRequests"], 0, result
                            )
                            self.assertGreater(result["editedStl"], 84, result)
                            self.assertFalse(result["editedCached"], result)
                            self.assertTrue(
                                any(
                                    "scikit_learn" in url or "scikit-learn" in url
                                    for url in requests
                                ),
                                requests,
                            )
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()
