import asyncio
import logging
import re
from dataclasses import dataclass, field

from zeroconf import InterfaceChoice, IPVersion, ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf

from .models import is_local_address

logger = logging.getLogger(__name__)

# The official Cube/PCIe image enables Avahi publish-workstation. Browsing only
# _http._tcp misses those devices, even though their .local hostname resolves.
SERVICE_TYPES = (
    "_workstation._tcp.local.",
    "_http._tcp.local.",
    "_https._tcp.local.",
    "_nanokvm._tcp.local.",
    "_ssh._tcp.local.",
)


def workstation_mac(name: str, service_type: str) -> str | None:
    """Read the interface MAC from Avahi's 'hostname [MAC]' service instance.

    This is advertised metadata, not device identity or an IP-to-MAC mapping.
    https://github.com/avahi/avahi/blob/master/avahi-core/iface.c
    """
    if service_type != "_workstation._tcp.local.":
        return None
    suffix = "." + service_type
    if not name.lower().endswith(suffix):
        return None
    match = re.search(r" \[([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})\]$", name[:-len(suffix)])
    if not match:
        return None
    mac = match[1].lower()
    # Ignore unspecified, multicast, and broadcast addresses; locally administered is valid.
    if mac == "00:00:00:00:00:00" or int(mac[:2], 16) & 1:
        return None
    return mac


def address_url(address, scheme="http", port=None):
    host = f"[{address}]" if ":" in address else address
    suffix = f":{port}" if port and port != (443 if scheme == "https" else 80) else ""
    return f"{scheme}://{host}{suffix}"


@dataclass
class Candidate:
    hostname: str
    addresses: set[str] = field(default_factory=set)
    urls: list[str] = field(default_factory=list)
    mac_addresses: set[str] = field(default_factory=set)


def merge_service(candidates: dict[str, Candidate], info, service_type):
    hostname = (info.server or "").lower().rstrip(".")
    addresses = [address for address in info.parsed_addresses() if is_local_address(address)]
    if not hostname or not addresses:
        return
    candidate = candidates.setdefault(hostname, Candidate(hostname))
    candidate.addresses.update(addresses)
    if mac := workstation_mac(getattr(info, "name", ""), service_type):
        candidate.mac_addresses.add(mac)
    for address in addresses:
        if service_type in {"_http._tcp.local.", "_https._tcp.local."}:
            scheme = "https" if service_type.startswith("_https") else "http"
            urls = [address_url(address, scheme, info.port)]
        else:
            urls = [address_url(address), address_url(address, "https")]
        for url in urls:
            if url not in candidate.urls:
                candidate.urls.append(url)


class Discovery:
    def __init__(self, interfaces=()):
        self.interfaces = interfaces
        self.zeroconf: AsyncZeroconf | None = None

    async def close(self):
        if self.zeroconf:
            await self.zeroconf.async_close()
            self.zeroconf = None

    async def scan(self, duration: float) -> list[Candidate]:
        if self.zeroconf is None:
            self.zeroconf = AsyncZeroconf(
                interfaces=list(self.interfaces) if self.interfaces else InterfaceChoice.All,
                ip_version=IPVersion.V4Only,
            )
        candidates: dict[str, Candidate] = {}
        seen: set[tuple[str, str]] = set()
        tasks: set[asyncio.Task] = set()
        limiter = asyncio.Semaphore(16)

        async def resolve(service_type, name):
            async with limiter:
                info = await self.zeroconf.async_get_service_info(service_type, name, timeout=1500)
                if info:
                    merge_service(candidates, info, service_type)

        def changed(zeroconf, service_type, name, state_change):
            key = (service_type, name)
            if state_change == ServiceStateChange.Removed or key in seen or len(seen) >= 256:
                return
            seen.add(key)
            task = asyncio.create_task(resolve(service_type, name))
            tasks.add(task)

        browser = AsyncServiceBrowser(
            self.zeroconf.zeroconf, list(SERVICE_TYPES), handlers=[changed],
        )
        browser_cancelled = False
        try:
            await asyncio.sleep(duration)
            await browser.async_cancel()
            browser_cancelled = True
            if tasks:
                done, pending = await asyncio.wait(tasks, timeout=4)
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                for task in done:
                    if not task.cancelled() and task.exception():
                        logger.warning("mDNS service resolution failed: %s", task.exception())
            return list(candidates.values())
        finally:
            if not browser_cancelled:
                await browser.async_cancel()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
