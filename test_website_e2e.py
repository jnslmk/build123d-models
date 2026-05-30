from playwright.sync_api import sync_playwright
import subprocess
import sys
import time

errors = []
warnings = []

server_proc = None

try:
    server_proc = subprocess.Popen(
        ["uv", "run", "website", "9876"],
        cwd="/home/jonas/git-projects/build123d/build123d-models",
    )
    time.sleep(4)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_console(msg):
            if msg.type == "error":
                errors.append(f"[{msg.type}] {msg.text}")

        page.on("console", handle_console)

        page.goto("http://localhost:9876/", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        print("Page title:", page.title())

        list_heading = page.locator(".model-list-panel h2").inner_text()
        print("List heading:", list_heading)

        model_buttons = page.locator(".model-item").all()
        print(f"Model buttons: {len(model_buttons)}")

        if model_buttons:
            model_buttons[0].click()
            page.wait_for_timeout(3000)

            container_visible = (
                page.locator("#model-viewer-container:not(.hidden)").count() > 0
            )
            print("3D viewer container visible:", container_visible)

        print("\n--- Errors ---")
        for e in errors:
            print(" ", e)
        if not errors:
            print("  (none)")

        browser.close()

        if errors:
            print("\nRESULT: FAILED")
            sys.exit(1)
        else:
            print("\nRESULT: PASSED")
            sys.exit(0)

finally:
    if server_proc:
        server_proc.terminate()
        server_proc.wait()
