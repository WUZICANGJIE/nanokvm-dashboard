"""Exercise the real web UI without probing or changing any NanoKVM devices."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def create_test_app():
    from nanokvm_dashboard.app import create_app
    from nanokvm_dashboard.config import Settings
    from nanokvm_dashboard.service import DashboardService

    class BrowserService(DashboardService):
        async def start(self):
            pass

        def request_refresh(self):
            pass

    return create_app(Settings.from_env(), BrowserService)


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    screenshots = Path("test-results")
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as data_dir:
        environment = {**os.environ, "DATA_DIR": data_dir, "MDNS_ENABLED": "false"}
        environment.pop("DASHBOARD_USERNAME", None)
        environment.pop("DASHBOARD_PASSWORD", None)
        with tempfile.TemporaryFile(mode="w+") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn",
                 "scripts.browser_smoke:create_test_app", "--factory",
                 "--host", "127.0.0.1", "--port", str(port)],
                env=environment, stdout=log, stderr=subprocess.STDOUT,
            )
            try:
                for _ in range(100):
                    try:
                        urllib.request.urlopen(base + "/healthz", timeout=1).close()
                        break
                    except OSError:
                        if process.poll() is not None:
                            raise RuntimeError("Server exited before becoming ready.") from None
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Server did not become ready.")
                with sync_playwright() as playwright:
                    options = {"headless": True}
                    if executable := os.getenv("CHROMIUM_EXECUTABLE"):
                        options["executable_path"] = executable
                    browser = playwright.chromium.launch(**options)
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1000}, locale="zh-CN",
                    )
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base)
                    expect(page.locator("h1")).to_be_visible()
                    expect(page.locator("#scan")).to_be_disabled()
                    page.locator("#add-open").click()
                    page.locator("#device-name").fill("NAS 控制台 <script>")
                    page.locator("#device-url").fill("192.168.254.254")
                    page.locator("#device-notes").fill("Browser test; not a real device")
                    page.locator("#device-save").click()
                    expect(page.locator(".device-card")).to_have_count(1)
                    expect(page.locator(".device-name")).to_have_text("NAS 控制台 <script>")
                    page.locator(".favorite-button").click()
                    expect(page.locator(".favorite-button")).to_have_attribute(
                        "aria-pressed", "true",
                    )
                    page.reload()
                    expect(page.locator(".device-name")).to_have_text("NAS 控制台 <script>")
                    page.locator("#search").fill("not-present")
                    expect(page.locator(".device-card")).to_have_count(0)
                    page.locator("#search").fill("")
                    expect(page.locator(".device-card")).to_have_count(1)
                    page.screenshot(path=str(screenshots / "desktop.png"), full_page=True)
                    page.locator("#settings-open").click()
                    page.locator("#theme-toggle").click()
                    expect(page.locator("html")).to_have_attribute("data-theme", "light")
                    with page.expect_download() as event:
                        page.locator("#export").click()
                    exported = json.loads(Path(event.value.path()).read_text())
                    assert exported["devices"][0]["favorite"] is True
                    page.locator("#settings-dialog .dialog-close").click()
                    page.locator("#language").click()
                    expect(page.locator("html")).to_have_attribute("lang", "en")
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    page.locator(".edit-button").click()
                    page.locator("#device-name").fill("Renamed console")
                    page.locator("#device-save").click()
                    expect(page.locator(".device-name")).to_have_text("Renamed console")
                    page.locator(".edit-button").click()
                    page.locator("#device-delete").click()
                    page.locator("#confirm-delete").click()
                    expect(page.locator(".device-card")).to_have_count(0)
                    assert not errors, errors
                    browser.close()
                print(
                    "Browser smoke test passed: CRUD, escaping, persistence, "
                    "favorite, search, export, theme, mobile."
                )
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                log.seek(0)
                print(log.read())


if __name__ == "__main__":
    main()
