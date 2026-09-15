import httpx
import pytest

from nanokvm_dashboard.models import normalize_url
from nanokvm_dashboard.probe import Prober, resolve_addresses


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "http://user:password@192.168.1.1", "http://127.0.0.1",
    "http://169.254.169.254", "http://8.8.8.8", "http://[::1]", "http://localhost",
    "http://192.168.1.1:0", "http://192.168.1.1:70000", "http://192.168.1.1/?token=secret",
    "http://192.168.1.1/#token", "http://192.168.1.1\\@8.8.8.8", " ",
])
def test_reject_unsupported_urls(url):
    with pytest.raises(ValueError):
        normalize_url(url)


def test_normalize_lan_urls():
    assert normalize_url(" 192.168.1.10/ ") == "http://192.168.1.10"
    assert normalize_url("https://KVM.local.:8443/") == "https://kvm.local:8443"
    assert normalize_url("http://[fd7a:115c:a1e0::1]") == "http://[fd7a:115c:a1e0::1]"


async def test_reject_dns_answers_outside_supported_networks():
    with pytest.raises(ValueError):
        await resolve_addresses("kvm.local", 80, ["192.168.1.10", "8.8.8.8"])


async def test_http_redirect_and_self_signed_https_path_is_identified():
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.scheme == "http":
            return httpx.Response(302, headers={"Location": "https://kvm.local/"})
        return httpx.Response(200, text="<html><title>NanoKVM Pro</title></html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    prober = Prober(1, client)
    result = await prober.probe("http://kvm.local", ["192.168.1.10"])
    assert result.online and result.nanokvm
    assert result.url == "https://kvm.local"
    assert requests[-1].url.host == "192.168.1.10"
    assert requests[-1].headers["host"] == "kvm.local"
    await prober.close()


async def test_redirect_cannot_escape_to_public_address():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "http://8.8.8.8/"})

    prober = Prober(1, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    result = await prober.probe("http://192.168.1.10")
    assert not result.online
    assert len(calls) == 1
    await prober.close()


async def test_other_web_services_and_dashboard_are_not_kvms():
    for body, headers in [
        ("<title>Printer</title>", {}),
        ("<title>NanoKVM Dashboard</title>", {"X-NanoKVM-Dashboard": "0.1.0"}),
    ]:
        def handle(request, body=body, headers=headers):
            return httpx.Response(200, text=body, headers=headers)
        prober = Prober(1, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        result = await prober.probe("http://192.168.1.10")
        assert result.online and not result.nanokvm
        await prober.close()
