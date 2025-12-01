"""Transparent OCP CAD Viewer using pywebview."""

import socket
import subprocess
import sys
import time

import webview

PORT = 3939


def is_server_running(host: str = "127.0.0.1", port: int = PORT) -> bool:
    """Check if the OCP server is already running."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


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


def start_ocp_server(port: int = PORT) -> subprocess.Popen:
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


def ensure_server(port: int = PORT) -> subprocess.Popen | None:
    """Ensure OCP server is running with viewer window. Returns process if started, None if already running."""
    if is_server_running(port=port):
        return None
    # Spawn the full viewer (server + window) as a background process
    proc = subprocess.Popen(
        [sys.executable, "-m", "viewer"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for server to be ready
    if not wait_for_server("127.0.0.1", port):
        proc.terminate()
        raise RuntimeError(f"Viewer failed to start on port {port}")
    return proc


def main() -> None:
    """Launch transparent OCP CAD Viewer."""
    print("Starting OCP server...")
    server_proc = start_ocp_server(PORT)
    print(f"Server ready at http://127.0.0.1:{PORT}")

    try:
        # Create transparent window
        window = webview.create_window(
            title="OCP CAD Viewer",
            url=f"http://127.0.0.1:{PORT}/viewer",
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
