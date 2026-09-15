from types import SimpleNamespace

from nanokvm_dashboard.config import Settings
from nanokvm_dashboard.discovery import Candidate, Discovery, merge_service
from nanokvm_dashboard.probe import ProbeResult
from nanokvm_dashboard.service import DashboardService
from nanokvm_dashboard.store import Store


def test_workstation_and_http_services_group_wired_and_wireless():
    candidates = {}
    wired = SimpleNamespace(server="Desk.local.", port=9,
                            parsed_addresses=lambda: ["192.168.1.10", "fe80::1"])
    wireless = SimpleNamespace(server="desk.local.", port=8443,
                               parsed_addresses=lambda: ["192.168.1.11"])
    merge_service(candidates, wired, "_workstation._tcp.local.")
    merge_service(candidates, wireless, "_https._tcp.local.")
    assert len(candidates) == 1
    device = candidates["desk.local"]
    assert device.addresses == {"192.168.1.10", "192.168.1.11"}
    assert "http://192.168.1.10" in device.urls
    assert "https://192.168.1.11:8443" in device.urls
    assert not any(":9" in url for url in device.urls)


async def test_only_verified_kvm_pages_become_devices(tmp_path):
    class FakeDiscovery:
        async def scan(self, duration):
            return [
                Candidate("custom-name.local", {"192.168.1.10"}, ["http://192.168.1.10"]),
                Candidate("printer.local", {"192.168.1.11"}, ["http://192.168.1.11"]),
            ]

        async def close(self):
            pass

    class FakeProber:
        async def probe(self, url, known_addresses=()):
            return ProbeResult(True, url.endswith(".10"), 5, url=url)

        async def close(self):
            pass

    store = Store(tmp_path)
    service = DashboardService(Settings(data_dir=tmp_path), store, FakeDiscovery(), FakeProber())
    await service._scan()
    assert service.candidate_count == 2
    assert service.verified_count == 1
    assert store.list()[0]["hostname"] == "custom-name.local"
    assert len(store.list()) == 1
    await service.close()
    store.close()


async def test_browser_lifecycle_and_multiple_scans(monkeypatch):
    from zeroconf import ServiceStateChange

    from nanokvm_dashboard import discovery as module

    browsers = []

    class FakeZeroconf:
        def __init__(self, **kwargs):
            self.zeroconf = self

        async def async_get_service_info(self, service_type, name, timeout):
            return SimpleNamespace(
                server="kvm.local.", port=9, parsed_addresses=lambda: ["192.168.1.10"],
            )

        async def async_close(self):
            pass

    class FakeBrowser:
        def __init__(self, zeroconf, types, handlers):
            self.cancellations = 0
            browsers.append(self)
            handlers[0](zeroconf, types[0], "kvm._workstation._tcp.local.",
                        ServiceStateChange.Added)

        async def async_cancel(self):
            self.cancellations += 1
            if self.cancellations > 1:
                raise KeyError("zeroconf listeners must be removed exactly once")

    monkeypatch.setattr(module, "AsyncZeroconf", FakeZeroconf)
    monkeypatch.setattr(module, "AsyncServiceBrowser", FakeBrowser)
    discovery = Discovery()
    for _ in range(2):
        candidates = await discovery.scan(0)
        assert candidates[0].hostname == "kvm.local"
    assert all(browser.cancellations == 1 for browser in browsers)
    await discovery.close()
