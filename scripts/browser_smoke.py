"""Exercise the real web UI without probing or changing any NanoKVM devices."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from nanokvm_dashboard import __version__


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


def check_table_layout(browser, base, screenshots):
    """Exercise table states with synthetic responses; never contact real devices."""
    context = browser.new_context(viewport={"width": 1200, "height": 800}, locale="zh-CN")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    now = datetime.now(UTC)
    devices = [
        {
            "id": str(index), "name": name, "url": f"http://192.168.50.{101 + index}",
            "hostname": f"kvm-0{index + 1}.local", "addresses": [f"192.168.50.{101 + index}"],
            "mac_addresses": ["02:ab:cd:12:34:56", "02:ab:cd:12:34:57"] if index == 0 else [],
            "notes": note, "source": "mdns", "favorite": index == 0,
            "status": status, "latency_ms": 12 if status == "online" else None,
            "last_seen": (now - timedelta(hours=2)).isoformat() if status == "offline" else None,
            "last_checked": now.isoformat(), "error": "" if status != "offline" else "Timeout",
            "control": False, "kvm_username": "", "power_state": "", "app_version": "",
            "control_error": "",
        }
        for index, (name, note, status) in enumerate([
            ("工作站", "主力电脑", "online"),
            ("家庭服务器", "实验环境", "online"),
            ("备用主机", "备用设备", "offline"),
        ])
    ]
    discovery = {
        "enabled": True, "scanning": False, "refreshing": False, "error": "",
        "last_scan": now.isoformat(), "candidates": 3, "verified": 3,
        "interval": 60, "interfaces": [],
    }
    page.route("**/api/devices", lambda route: route.fulfill(json={
        "devices": devices, "discovery": discovery, "version": __version__,
        "control_available": True, "dashboard_auth": False,
    }))

    def save_credentials(route):
        # The dashboard stores the credentials; the device list then reports control enabled.
        devices[0].update(control=True, kvm_username="admin", power_state="on", app_version="2.4.3")
        route.fulfill(json=dict(devices[0]))

    def clear_credentials(route):
        devices[0].update(control=False, kvm_username="", power_state="", app_version="")
        route.fulfill(json=dict(devices[0]))

    def accept_command(route):
        route.fulfill(json={"ok": True})

    page.route("**/api/devices/*/control", lambda route: (
        clear_credentials(route) if route.request.method == "DELETE" else save_credentials(route)
    ))
    page.route("**/api/devices/*/power", accept_command)
    page.route("**/api/devices/*/paste", accept_command)
    page.goto(base)
    expect(page.locator(".device-row")).to_have_count(3)
    expect(page.locator("#count-online")).to_have_text("2")
    expect(page.locator("#count-offline")).to_have_text("1")
    expect(page.locator(".open-console").first).to_have_attribute("href", devices[0]["url"])
    expect(page.locator(".open-console").first).to_have_attribute("target", "_blank")
    expect(page.locator(".device-macs").first).to_have_text(
        "02:ab:cd:12:34:56\n02:ab:cd:12:34:57"
    )
    expect(page.locator(".device-macs").nth(1)).to_have_text("—")
    page.screenshot(path=str(screenshots / "table-dark.png"), full_page=True)
    for selection, count in [("online", 2), ("offline", 1), ("favorites", 1), ("all", 3)]:
        button = page.locator(f'[data-filter="{selection}"]')
        button.click()
        expect(button).to_have_attribute("aria-pressed", "true")
        expect(page.locator(".device-row")).to_have_count(count)
    page.locator("#search").fill("kvm-02")
    expect(page.locator(".device-name")).to_have_text("家庭服务器")
    page.locator("#search").fill("AB:CD:12:34:57")
    expect(page.locator(".device-name")).to_have_text("工作站")
    page.locator("#search").fill("missing-device")
    expect(page.locator(".device-table")).to_be_hidden()
    expect(page.locator("#empty-title")).to_have_text("没有符合条件的设备")
    page.locator("#search").fill("")
    page.locator("#settings-open").click()
    page.locator("#theme-toggle").click()
    page.locator("#settings-dialog .dialog-close").click()
    page.screenshot(path=str(screenshots / "table-light.png"), full_page=True)
    page.reload()
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    page.locator("#settings-open").click()
    page.locator("#theme-toggle").click()
    page.locator("#settings-dialog .dialog-close").click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(screenshots / "table-mobile.png"), full_page=True)

    # Control: shut until credentials are saved, then power, reset and paste reach the device.
    expect(page.locator(".device-power").first).to_be_hidden()
    page.locator(".control-button").first.click()
    expect(page.locator("#control-dialog")).to_be_visible()
    expect(page.locator("#control-device")).to_contain_text("工作站")
    expect(page.locator("#control-credentials-info")).to_contain_text("尚未保存凭据")
    expect(page.locator("#power-press")).to_be_disabled()
    expect(page.locator("#paste-send")).to_be_disabled()
    page.screenshot(path=str(screenshots / "control-empty.png"), full_page=True)
    page.locator("#control-username").fill("admin")
    page.locator("#control-password").fill("secret")
    page.locator("#control-save").click()
    expect(page.locator("#toast")).to_contain_text("凭据已保存")
    expect(page.locator("#control-power")).to_have_text("已开机")
    expect(page.locator("#control-detail")).to_contain_text("app 2.4.3")
    expect(page.locator("#power-press")).to_be_enabled()
    expect(page.locator("#paste-send")).to_be_enabled()
    page.locator("#power-press").click()
    expect(page.locator("#confirm-title")).to_have_text("发送电源键脉冲")
    page.locator("#confirm-accept").click()
    expect(page.locator("#toast")).to_contain_text("已发送电源键脉冲")
    page.locator("#control-paste").fill("uname -a")
    page.locator("#paste-send").click()
    expect(page.locator("#toast")).to_contain_text("文本已发送")
    page.screenshot(path=str(screenshots / "control-enabled.png"), full_page=True)
    page.locator("#control-dialog .dialog-close").click()
    expect(page.locator(".device-power").first).to_have_text("主机 已开机")
    expect(page.locator(".device-version").first).to_have_text("app 2.4.3")
    # Control is configured and this deployment has no dashboard login: say so.
    page.locator("#settings-open").click()
    expect(page.locator("#control-warning")).to_be_visible()
    page.locator("#settings-dialog .dialog-close").click()
    page.locator(".control-button").first.click()
    page.locator("#control-clear").click()
    page.locator("#confirm-accept").click()
    expect(page.locator("#toast")).to_contain_text("已清除凭据")
    expect(page.locator("#power-press")).to_be_disabled()
    page.locator("#control-dialog .dialog-close").click()
    expect(page.locator(".device-power").first).to_be_hidden()

    # Long user content must not push controls off screen, in either language.
    devices[0].update(name="Long-device-name-" * 6, notes="Long note " * 100,
                      url="https://kvm-01.local/" + "path" * 80, status="unknown")
    page.reload()
    expect(page.locator("#count-online")).to_have_text("1")
    expect(page.locator("#count-offline")).to_have_text("1")
    expect(page.locator(".status-label").first).to_have_text("待检查")
    for language in ["zh-CN", "en"]:
        if language == "en":
            page.locator("#language").click()
        expect(page.locator("html")).to_have_attribute("lang", language)
        for width in [320, 390, 768, 1024, 1440]:
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ), (language, width, "page overflow")
            assert page.locator(".device-actions").evaluate_all(
                "elements => elements.every(el => el.scrollWidth <= el.clientWidth)"
            ), (language, width, "action overflow")
            expect(page.locator(".edit-button").first).to_be_visible()
            expect(page.locator(".device-macs").first).to_contain_text("02:ab:cd:12:34:57")
            assert page.locator(".device-macs").evaluate_all(
                "elements => elements.every(el => el.scrollWidth <= el.clientWidth)"
            ), (language, width, "MAC overflow")
        expect(page.locator(".device-macs").nth(1)).to_have_text("—")

    # Scan controls and errors still belong to the real discovery workflow.
    discovery["scanning"] = True
    page.reload()
    expect(page.locator("#scan")).to_be_disabled()
    expect(page.locator("#scan")).to_have_text("Scanning…")
    discovery.update(scanning=False, error="Test discovery error")
    page.reload()
    expect(page.locator("#scan")).to_be_enabled()
    expect(page.locator("#discovery-message")).to_contain_text("Test discovery error")
    assert not errors, errors
    context.close()


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
                    expect(page.locator(".device-row")).to_have_count(1)
                    expect(page.locator(".device-name")).to_have_text("NAS 控制台 <script>")
                    page.locator(".favorite-button").click()
                    expect(page.locator(".favorite-button")).to_have_attribute(
                        "aria-pressed", "true",
                    )
                    page.reload()
                    expect(page.locator(".device-name")).to_have_text("NAS 控制台 <script>")
                    page.locator("#search").fill("not-present")
                    expect(page.locator(".device-row")).to_have_count(0)
                    page.locator("#search").fill("")
                    expect(page.locator(".device-row")).to_have_count(1)
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
                    page.locator("#confirm-accept").click()
                    expect(page.locator(".device-row")).to_have_count(0)
                    assert not errors, errors
                    check_table_layout(browser, base, screenshots)
                    browser.close()
                print(
                    "Browser smoke test passed: CRUD, escaping, persistence, "
                    "favorite, search, MAC metadata, export, theme, table filters, "
                    "discovery states, long content, responsive layouts in Chinese and English."
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
