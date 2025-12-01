"""Transparent OCP CAD Viewer using pywebview."""

import socket
import subprocess
import sys
import time

import webview


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Wait for server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def start_ocp_server(port: int = 3939) -> subprocess.Popen:
    """Start the OCP viewer server in the background."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "ocp_vscode", "--port", str(port), "--theme", "dark"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to actually be ready
    if not wait_for_server("127.0.0.1", port):
        proc.terminate()
        raise RuntimeError(f"Server failed to start on port {port}")
    return proc


def main() -> None:
    """Launch transparent OCP CAD Viewer."""
    port = 3939

    print("Starting OCP server...")
    server_proc = start_ocp_server(port)
    print(f"Server ready at http://127.0.0.1:{port}")

    try:
        # Create transparent window
        window = webview.create_window(
            title="OCP CAD Viewer",
            url=f"http://127.0.0.1:{port}/viewer",
            width=1200,
            height=800,
            resizable=True,
            frameless=False,
            transparent=True,
        )

        # Start the webview (blocking)
        webview.start(gui="gtk")

    finally:
        # Clean up server on exit
        server_proc.terminate()
        server_proc.wait()


if __name__ == "__main__":
    main()
