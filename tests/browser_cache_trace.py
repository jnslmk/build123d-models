#!/usr/bin/env python3
"""Trace a cold and warm *new worker* CAD rebuild in isolated Chromium.

Run: uv run --with playwright==1.58.0 python tests/browser_cache_trace.py
Chromium must be installed and the Pyodide/OCP package hosts reachable. Output is
JSON with CDP encoded transfer bytes, cache indicators, response headers, and worker
phase timings. The temporary HTTP site and browser profile are discarded on exit.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import math
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402

import website  # noqa: E402

HEADERS = (
    "cache-control",
    "etag",
    "last-modified",
    "content-length",
    "content-encoding",
    "content-range",
    "age",
    "date",
    "vary",
    "accept-ranges",
    "x-cache",
    "cf-cache-status",
)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def safe_url(url: str) -> str:
    """Exclude query strings (which can contain credentials) from reported URLs."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def selected_headers(headers: dict) -> dict:
    lower = {key.lower(): value for key, value in headers.items()}
    return {key: lower[key] for key in HEADERS if key in lower}


def wheel_family(url: str) -> str | None:
    name = urlsplit(url).path.rsplit("/", 1)[-1].lower()
    if not name.endswith(".whl"):
        return None
    if name.startswith(("cadquery_ocp-", "cadquery-ocp-")):
        return "OCP"
    if name.startswith("scipy-"):
        return "SciPy"
    return "other-wheel"


class NetworkTrace:
    """Record Chromium Network events from the page AND its dedicated workers.

    A page CDP session with nested, non-flattened worker attachment captures
    importScripts and micropip requests made inside workers; page.on('response')
    and response.body length alone cannot distinguish network from HTTP cache.
    """

    def __init__(self, page):
        self.cdp = page.context.new_cdp_session(page)
        self.requests: dict[tuple[str, str], dict] = {}
        self.phase = "setup"
        self.workers: set[str] = set()
        self.cdp.on("Target.attachedToTarget", self.attached)
        self.cdp.on("Target.receivedMessageFromTarget", self.worker_event)
        self.cdp.on(
            "Network.requestWillBeSent",
            lambda p: self.record("page", "requestWillBeSent", p),
        )
        self.cdp.on(
            "Network.responseReceived",
            lambda p: self.record("page", "responseReceived", p),
        )
        self.cdp.on(
            "Network.responseReceivedExtraInfo",
            lambda p: self.record("page", "responseReceivedExtraInfo", p),
        )
        self.cdp.on(
            "Network.requestServedFromCache",
            lambda p: self.record("page", "requestServedFromCache", p),
        )
        self.cdp.on(
            "Network.loadingFinished",
            lambda p: self.record("page", "loadingFinished", p),
        )
        self.cdp.on(
            "Network.loadingFailed", lambda p: self.record("page", "loadingFailed", p)
        )
        self.cdp.send("Network.enable")
        # Pause a newly created worker until Network.enable, so its initial
        # importScripts fetch is also visible, rather than racing attachment.
        self.cdp.send(
            "Target.setAutoAttach",
            {
                "autoAttach": True,
                "waitForDebuggerOnStart": True,
                "flatten": False,
            },
        )

    def attached(self, event: dict) -> None:
        if event["targetInfo"]["type"] != "worker":
            return
        session = event["sessionId"]
        self.workers.add(session)
        for index, method in enumerate(
            ("Network.enable", "Runtime.runIfWaitingForDebugger"), 1
        ):
            self.cdp.send(
                "Target.sendMessageToTarget",
                {
                    "sessionId": session,
                    "message": json.dumps({"id": index, "method": method}),
                },
            )

    def worker_event(self, event: dict) -> None:
        if event["sessionId"] not in self.workers:
            return
        message = json.loads(event["message"])
        if "method" in message and message["method"].startswith("Network."):
            self.record(
                event["sessionId"],
                message["method"].removeprefix("Network."),
                message["params"],
            )

    def record(self, target: str, kind: str, event: dict) -> None:
        key = (target, event["requestId"])
        if kind == "requestWillBeSent" and event.get("redirectResponse"):
            # Redirects reuse requestId; keep the old hop and start a fresh row.
            previous = self.requests.pop(key, None)
            if previous:
                previous["redirectedTo"] = safe_url(event["request"]["url"])
                previous["status"] = event["redirectResponse"]["status"]
                previous["responseHeaders"] = selected_headers(
                    event["redirectResponse"].get("headers", {})
                )
                hop = 1
                while (target, f"{event['requestId']}:redirect:{hop}") in self.requests:
                    hop += 1
                self.requests[(target, f"{event['requestId']}:redirect:{hop}")] = (
                    previous
                )
        row = self.requests.setdefault(
            key,
            {"phase": self.phase, "target": "worker" if target != "page" else "page"},
        )
        if kind == "requestWillBeSent":
            row["url"] = safe_url(event["request"]["url"])
            row["startedUnixMs"] = round(event["wallTime"] * 1000)
            row["startMonotonicSeconds"] = event["timestamp"]
        elif kind == "responseReceived":
            response = event["response"]
            row.update(
                {
                    "status": response["status"],
                    "mimeType": response.get("mimeType"),
                    "fromDiskCache": response.get("fromDiskCache", False),
                    "fromPrefetchCache": response.get("fromPrefetchCache", False),
                    "fromServiceWorker": response.get("fromServiceWorker", False),
                    "responseHeaders": selected_headers(response.get("headers", {})),
                }
            )
        elif kind == "responseReceivedExtraInfo":
            row["wireStatus"] = event["statusCode"]
            row["wireHeaders"] = selected_headers(event.get("headers", {}))
        elif kind == "requestServedFromCache":
            row["servedFromCache"] = True
        elif kind == "loadingFinished":
            row["transferBytes"] = event["encodedDataLength"]
            row["endMonotonicSeconds"] = event["timestamp"]
        elif kind == "loadingFailed":
            row["failure"] = event.get("errorText")

    def phase_rows(self, phase: str) -> list[dict]:
        return [
            row
            for row in self.requests.values()
            if row.get("phase") == phase and "url" in row
        ]


RUN_WORKER = """async ({diameter, sources, editSources, timeoutMs}) => {
    const started = Date.now();
    const worker = new Worker('./js/pyodide-worker.js');
    const events = [{atUnixMs: started, phase: 'worker-created'}];
    let status = 'loading worker script';
    let timer;
    try {
        return await new Promise((resolve, reject) => {
            const fail = reason => { clearTimeout(timer); reject(new Error(reason)); };
            timer = setTimeout(() => fail('timed out at: ' + status), timeoutMs);
            worker.onerror = event => fail('worker crashed: ' + event.message);
            worker.onmessageerror = () => fail('worker message could not be decoded');
            worker.onmessage = ({data}) => {
                if (data.type === 'status') {
                    status = data.text;
                    events.push({atUnixMs: Date.now(), phase: 'status', text: status});
                } else if (data.type === 'error') {
                    fail('worker error: ' + data.message);
                } else if (data.type === 'ready') {
                    events.push({atUnixMs: Date.now(), phase: 'ready'});
                    worker.postMessage({type: 'generate', id: 1,
                        model: 'lens_cap', sourcePath: 'models/lens_cap/__init__.py',
                        sourcesUrl: new URL(sources, document.baseURI).href,
                        editSourcesUrl: new URL(editSources, document.baseURI).href,
                        params: {inner_dia: diameter}});
                } else if (data.type === 'result') {
                    if (data.id !== 1 || data.model !== 'lens_cap' || data.cached ||
                        !(data.stl instanceof ArrayBuffer)) {
                        fail('expected uncached lens_cap STL for the requested parameter');
                        return;
                    }
                    const view = new DataView(data.stl);
                    if (view.byteLength < 134) { fail('binary STL too short'); return; }
                    const triangles = view.getUint32(80, true);
                    if (!triangles || view.byteLength !== 84 + triangles * 50) {
                        fail('invalid binary STL triangle table'); return;
                    }
                    let lo = Infinity, hi = -Infinity;
                    for (let i = 0; i < triangles; i++) {
                        for (const offset of [12, 24, 36]) {
                            const x = view.getFloat32(84 + 50 * i + offset, true);
                            if (!Number.isFinite(x)) { fail('nonfinite STL coordinate'); return; }
                            lo = Math.min(lo, x); hi = Math.max(hi, x);
                        }
                    }
                    const finished = Date.now();
                    events.push({atUnixMs: finished, phase: 'result'});
                    clearTimeout(timer);
                    resolve({diameter, triangles, stlBytes: view.byteLength, widthMm: hi - lo,
                        cadMs: data.cadMs, workerBuildMs: data.wallMs,
                        bootMs: events.find(e => e.phase === 'ready').atUnixMs - started,
                        buildMs: finished - events.find(e => e.phase === 'ready').atUnixMs,
                        totalMs: finished - started, events});
                }
            };
            worker.postMessage({type: 'init',
                baseUrl: new URL('./', document.baseURI).href});
        });
    } finally {
        clearTimeout(timer);
        worker.terminate();
    }
}"""


def summarize(phase: str, result: dict, rows: list[dict]) -> dict:
    families = ("OCP", "SciPy")
    wheels = [row for row in rows if wheel_family(row["url"]) is not None]
    focus = [row for row in wheels if wheel_family(row["url"]) in families]
    for family in families:
        if not any(
            wheel_family(row["url"]) == family
            and row["target"] == "worker"
            and "transferBytes" in row
            and "responseHeaders" in row
            for row in focus
        ):
            raise RuntimeError(
                f"{phase}: missing complete worker CDP trace for {family} wheel"
            )
    for row in focus:
        if "endMonotonicSeconds" in row and "startMonotonicSeconds" in row:
            row["fetchMs"] = round(
                1000
                * (row.pop("endMonotonicSeconds") - row.pop("startMonotonicSeconds"))
            )
            row["finishedUnixMs"] = row["startedUnixMs"] + row["fetchMs"]
    return {
        "phase": phase,
        "build": result,
        "network": {
            "requestCount": len(rows),
            "totalTransferBytes": sum(row.get("transferBytes", 0) for row in rows),
            "wheelTransferBytes": sum(row.get("transferBytes", 0) for row in wheels),
            "wheelBytesByFamily": {
                family: sum(
                    row.get("transferBytes", 0)
                    for row in focus
                    if wheel_family(row["url"]) == family
                )
                for family in families
            },
            "requests": focus,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-ms", type=int, default=720_000)
    args = parser.parse_args()
    if args.timeout_ms <= 0:
        parser.error("timeout must be positive")
    with tempfile.TemporaryDirectory(prefix="browser-cache-trace-") as directory:
        root = Path(directory)
        site = root / "site"
        (site / "js").mkdir(parents=True)
        (site / "js" / "pyodide-worker.js").write_bytes(
            (website.WEBSITE_DIR / "js" / "pyodide-worker.js").read_bytes()
        )
        (site / "browser-wheels").mkdir()
        wheel = "build123d-0.11.1-py3-none-any.whl"
        (site / "browser-wheels" / wheel).write_bytes(
            (website.WEBSITE_DIR / "browser-wheels" / wheel).read_bytes()
        )
        assets = {
            "models": [{"name": "lens_cap", "source": "models/lens_cap/__init__.py"}]
        }
        website._write_source_assets(assets, site)
        (site / "index.html").write_text(
            "<!doctype html><title>Browser cache trace</title>"
        )
        handler = functools.partial(QuietHandler, directory=str(site))
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as playwright:
                    context = playwright.chromium.launch_persistent_context(
                        str(root / "chromium-profile"), headless=True
                    )
                    try:
                        page = context.new_page()
                        page.set_default_timeout(args.timeout_ms + 60_000)
                        trace = NetworkTrace(page)
                        page.goto(
                            f"http://127.0.0.1:{server.server_port}/",
                            wait_until="networkidle",
                        )
                        phases = []
                        for phase, diameter in (("cold", 70), ("warm", 71)):
                            trace.phase = phase
                            result = page.evaluate(
                                RUN_WORKER,
                                {
                                    "diameter": diameter,
                                    "timeoutMs": args.timeout_ms,
                                    "sources": assets["models"][0]["sources"],
                                    "editSources": assets["editSources"],
                                },
                            )
                            if not math.isclose(
                                result["widthMm"], diameter + 2.4, abs_tol=0.2
                            ):
                                raise RuntimeError(
                                    f"incorrect STL for {phase} parameters: {result}"
                                )
                            phases.append(
                                summarize(phase, result, trace.phase_rows(phase))
                            )
                        print(json.dumps({"trace": phases}, indent=2), flush=True)
                    finally:
                        context.close()
            finally:
                server.shutdown()
                thread.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
