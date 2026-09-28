"""Regenerate the Pyodide 0.28.0a3 browser lock in a real Chromium worker.

``uv run --with playwright==1.58.0 python tests/browser_runtime_lock.py --update``
resolves upstream wheels and writes the checked-in lock. Without --update, it
compares a fresh independent resolution against the checked-in artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import functools
import http.server
import json
import tempfile
import unittest
import threading
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

import website

ROOT = website.WEBSITE_DIR
LOCK = ROOT / "runtime-lock.json"
PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.28.0a3/full/"
WHEEL = "build123d-0.11.1-py3-none-any.whl"
LOCAL_WHEEL = "browser-wheels/" + WHEEL
# These are the only roots; the resolver discovers and records every transitive
# wheel. The adapted wheel deliberately omits scikit-learn, which the Pyodide
# catalog already locks but is only loaded when edited code is requested.
RESOLVER_WORKER = r"""
importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.0a3/full/pyodide.js");
self.onmessage = async ({data}) => {
  try {
    const pyodide = await loadPyodide({
      stdout: text => self.postMessage({type: 'log', text}),
      stderr: text => self.postMessage({type: 'log', text}),
    });
    await pyodide.loadPackage(['micropip', 'numpy', 'typing-extensions']);
    pyodide.globals.set('BUILD123D_WHEEL_URL',
      new URL('browser-wheels/build123d-0.11.1-py3-none-any.whl', data.baseUrl).href);
    await pyodide.runPythonAsync(`
import micropip
micropip.set_index_urls(["https://yeicor.github.io/OCP.wasm", "https://pypi.org/simple"])
await micropip.install("lib3mf")
micropip.add_mock_package("py-lib3mf", "2.4.1", modules={"py_lib3mf": "from lib3mf import *"})
await micropip.install("cadquery-ocp")
micropip.add_mock_package("cadquery-ocp-novtk", "7.9.3.0")
await micropip.install(BUILD123D_WHEEL_URL)
await micropip.install("bd_warehouse>=0.2.0,<0.3.0")
print("BROWSER_FREEZE=" + micropip.freeze())
    `);
    self.postMessage({type: 'ready'});
  } catch (error) {
    self.postMessage({type: 'error', message: String(error)});
  }
};
"""


def normalize(resolved: dict) -> dict:
    """Use portable URLs and discard the synthetic resolver-only mock dependency."""
    if resolved["info"]["version"] != "0.28.0a3":
        raise ValueError("unexpected Pyodide version")
    packages = resolved["packages"]
    wheel = packages["build123d"]
    digest = hashlib.sha256((ROOT / LOCAL_WHEEL).read_bytes()).hexdigest()
    if digest != wheel["sha256"] or wheel["version"] != "0.11.1":
        raise ValueError("local build123d wheel changed during resolution")
    wheel["file_name"] = LOCAL_WHEEL
    wheel["depends"] = sorted(
        {
            "cadquery-ocp" if name == "cadquery-ocp-novtk" else name
            for name in wheel["depends"]
        }
    )
    for package in packages.values():
        if not package["file_name"].startswith(
            ("http://", "https://", "browser-wheels/")
        ):
            package["file_name"] = PYODIDE_CDN + package["file_name"]
        if package["file_name"].startswith("http://"):
            raise ValueError("insecure wheel URL in resolved graph")
    queue = [
        "micropip",
        "numpy",
        "typing-extensions",
        "build123d",
        "bd-warehouse",
        "scikit-learn",
    ]
    visited = set()
    while queue:
        name = queue.pop()
        if name in visited:
            continue
        if name not in packages:
            raise ValueError(f"missing dependency {name}")
        visited.add(name)
        queue.extend(packages[name]["depends"])
    return resolved


def resolve_in_browser() -> dict:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "js").mkdir()
        (root / "js" / "pyodide-worker.js").write_text(RESOLVER_WORKER)
        (root / "browser-wheels").mkdir()
        (root / "browser-wheels" / WHEEL).write_bytes((ROOT / LOCAL_WHEEL).read_bytes())
        (root / "index.html").write_text(
            "<!doctype html><title>Runtime resolver</title>"
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
                        page.goto(f"http://127.0.0.1:{server.server_port}/")
                        return page.evaluate("""async () => {
                            const worker = new Worker('./js/pyodide-worker.js');
                            let freeze = null;
                            let status = 'loading worker';
                            try {
                                return await new Promise((resolve, reject) => {
                                    const timeout = setTimeout(() => reject(new Error('timed out: ' + status)), 700000);
                                    worker.onerror = e => reject(new Error(e.message));
                                    worker.onmessage = ({data}) => {
                                        if (data.type === 'status') status = data.text;
                                        if (data.type === 'log' && data.text.startsWith('BROWSER_FREEZE=')) {
                                            freeze = JSON.parse(data.text.slice('BROWSER_FREEZE='.length));
                                        }
                                        if (data.type === 'error') reject(new Error(data.message));
                                        if (data.type === 'ready') {
                                            clearTimeout(timeout);
                                            if (!freeze) reject(new Error('missing freeze output'));
                                            else resolve(freeze);
                                        }
                                    };
                                    worker.postMessage({type: 'init', baseUrl: new URL('./', document.baseURI).href});
                                });
                            } finally { worker.terminate(); }
                        }""")
                    finally:
                        browser.close()
            finally:
                server.shutdown()
                thread.join()


class BrowserLockIntegrity(unittest.TestCase):
    def test_compatible_wheel_versions_and_hashes(self) -> None:
        packages = json.loads(LOCK.read_text())["packages"]
        expected = {
            "build123d": (
                "0.11.1",
                "fa97b4aa763d72591ea2206cc52bf24314e273de740544abf4aa34a41f4336fa",
            ),
            "cadquery-ocp": (
                "7.9.3.0",
                "f7a293e70133f6faba3826fbfd9c6d00ed775a3255895ad9881b33d05a9825ae",
            ),
            "bd-warehouse": (
                "0.2.0",
                "1fe66a491a81dd131a864677bab15257c9b6e32412cd5a5ab85c2c24b3c3617b",
            ),
            "scipy": (
                "1.14.1",
                "47561d9afac881779309c22d4bec42aea344811c3cbb05a61325495be7c5a800",
            ),
            "scikit-learn": (
                "1.6.1",
                "a4486382b92b93ab43ff9e1ece89a8f851650cf2e0cc37e5785d06e6a9a9c492",
            ),
        }
        self.assertEqual(
            {
                name: (packages[name]["version"], packages[name]["sha256"])
                for name in expected
            },
            expected,
        )

    def test_tampered_wheel_fails_boot_instead_of_installing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            website.stage_browser_runtime(root)
            wheel = root / LOCAL_WHEEL
            wheel.write_bytes(wheel.read_bytes() + b"tampered-but-still-a-valid-zip")
            self.assertTrue(zipfile.is_zipfile(wheel))
            self.assertNotEqual(
                hashlib.sha256(wheel.read_bytes()).hexdigest(),
                json.loads((root / "runtime-lock.json").read_text())["packages"][
                    "build123d"
                ]["sha256"],
            )
            (root / "index.html").write_text(
                "<!doctype html><title>Integrity check</title>"
            )
            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=directory
            )
            with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(headless=True)
                        try:
                            page = browser.new_page()
                            requests = []
                            page.on(
                                "request", lambda request: requests.append(request.url)
                            )
                            page.goto(f"http://127.0.0.1:{server.server_port}/")
                            result = page.evaluate("""async () => {
                                const worker = new Worker('./js/pyodide-worker.js');
                                try {
                                    return await new Promise((resolve, reject) => {
                                        const timeout = setTimeout(() => reject(new Error('boot timed out')), 120000);
                                        worker.onerror = e => reject(new Error(e.message));
                                        worker.onmessage = ({data}) => {
                                            if (data.type === 'ready' || data.type === 'error') {
                                                clearTimeout(timeout);
                                                resolve({type: data.type, message: data.message});
                                            }
                                        };
                                        worker.postMessage({type: 'init',
                                            baseUrl: new URL('./', document.baseURI).href});
                                    });
                                } finally { worker.terminate(); }
                            }""")
                            self.assertEqual(result["type"], "error", result)
                            self.assertIn("build123d", result["message"], result)
                            self.assertTrue(
                                any(url.endswith(WHEEL) for url in requests), requests
                            )
                            self.assertIn("Failed to fetch", result["message"], result)
                        finally:
                            browser.close()
                finally:
                    server.shutdown()
                    thread.join()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    resolved = normalize(resolve_in_browser())
    if args.update:
        LOCK.write_text(json.dumps(resolved, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {LOCK}: {len(resolved['packages'])} packages")
    elif resolved != json.loads(LOCK.read_text()):
        raise SystemExit("browser dependency graph differs from pinned runtime lock")
    else:
        print(f"Lock matches browser resolve: {len(resolved['packages'])} packages")


if __name__ == "__main__":
    main()
