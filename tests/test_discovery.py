from types import SimpleNamespace

import pytest

from nanokvm_dashboard.config import Settings
from nanokvm_dashboard.discovery import Candidate, Discovery, merge_service, workstation_mac
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


@pytest.mark.parametrize(("instance", "expected"), [
    ("Desk [02:AB:CD:12:34:56]", "02:ab:cd:12:34:56"),
    ("Desk [00:11:22:33:44:55]", "00:11:22:33:44:55"),
    ("Desk", None),
    ("Desk [00:00:00:00:00:00]", None),
    ("Desk [ff:ff:ff:ff:ff:ff]", None),
    ("Desk [01:11:22:33:44:55]", None),
    ("Desk [02:ab:cd:12:34]", None),
    ("Desk [02:ab:cd:12:34:zz]", None),
    ("Desk [02:ab:cd:12:34:56:78]", None),
    ("Desk [02:ab:cd:12:34:56] trailing", None),
])
def test_workstation_mac_validation(instance, expected):
    kind = "_workstation._tcp.local."
    assert workstation_mac(f"{instance}.{kind}", kind) == expected
    assert workstation_mac(f"{instance}._http._tcp.local.", "_http._tcp.local.") is None
    assert workstation_mac(f"{instance}._http._tcp.local.", kind) is None


def test_mac_metadata_deduplicates_without_merging_different_hostnames():
    candidates = {}
    kind = "_workstation._tcp.local."
    for hostname, mac in [
        ("desk.local.", "02:AB:CD:12:34:56"),
        ("desk.local.", "02:ab:cd:12:34:56"),
        ("desk.local.", "02:ab:cd:12:34:57"),
        ("other.local.", "02:ab:cd:12:34:56"),
    ]:
        info = SimpleNamespace(
            server=hostname, name=f"Desk [{mac}].{kind}", port=9,
            parsed_addresses=lambda: ["192.168.1.10"],
        )
        merge_service(candidates, info, kind)
    assert len(candidates) == 2
    assert candidates["desk.local"].mac_addresses == {
        "02:ab:cd:12:34:56", "02:ab:cd:12:34:57",
    }
    assert candidates["other.local"].mac_addresses == {"02:ab:cd:12:34:56"}


async def test_only_verified_kvm_pages_become_devices(tmp_path):
    class FakeDiscovery:
        async def scan(self, duration):
            return [
                Candidate("custom-name.local", {"192.168.1.10"}, ["http://192.168.1.10"],
                          {"02:ab:cd:12:34:56"}),
                Candidate("printer.local", {"192.168.1.11"}, ["http://192.168.1.11"],
                          {"02:ab:cd:12:34:57"}),
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
    assert store.list()[0]["mac_addresses"] == ["02:ab:cd:12:34:56"]
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
