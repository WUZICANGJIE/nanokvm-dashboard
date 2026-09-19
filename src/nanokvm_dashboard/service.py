import asyncio
import logging
from urllib.parse import urlsplit

from .config import Settings
from .discovery import Discovery, address_url
from .probe import Prober
from .store import Store, now

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(self, settings: Settings, store: Store, discovery=None, prober=None):
        self.settings = settings
        self.store = store
        self.discovery = discovery or Discovery(settings.mdns_interfaces)
        self.prober = prober or Prober(settings.probe_timeout)
        self.scan_task = None
        self.refresh_task = None
        self.periodic_task = None
        self.last_scan = None
        self.scan_error = ""
        self.candidate_count = 0
        self.verified_count = 0

    async def start(self):
        self.periodic_task = asyncio.create_task(self._periodic())

    async def close(self):
        tasks = [task for task in (self.periodic_task, self.scan_task, self.refresh_task) if task]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.discovery.close()
        await self.prober.close()

    def status(self):
        return {
            "enabled": self.settings.mdns_enabled,
            "scanning": bool(self.scan_task and not self.scan_task.done()),
            "refreshing": bool(self.refresh_task and not self.refresh_task.done()),
            "last_scan": self.last_scan,
            "error": self.scan_error,
            "candidates": self.candidate_count,
            "verified": self.verified_count,
            "interval": self.settings.discovery_interval,
            "interfaces": list(self.settings.mdns_interfaces),
        }

    def request_scan(self):
        if not self.settings.mdns_enabled:
            return False
        if not self.scan_task or self.scan_task.done():
            self.scan_task = asyncio.create_task(self._scan())
        return True

    def request_refresh(self):
        if not self.refresh_task or self.refresh_task.done():
            self.refresh_task = asyncio.create_task(self._refresh())

    async def _periodic(self):
        next_scan = next_probe = 0
        loop = asyncio.get_running_loop()
        while True:
            current = loop.time()
            if current >= next_scan:
                self.request_scan()
                next_scan = current + self.settings.discovery_interval
            if current >= next_probe:
                self.request_refresh()
                next_probe = current + self.settings.probe_interval
            await asyncio.sleep(2)

    async def _scan(self):
        self.scan_error = ""
        self.verified_count = 0
        try:
            candidates = await self.discovery.scan(self.settings.discovery_seconds)
            self.candidate_count = len(candidates)
            known = {
                device["hostname"]: device for device in self.store.list() if device["hostname"]
            }
            limiter = asyncio.Semaphore(8)

            async def identify(candidate):
                if self.store.is_ignored(candidate.hostname):
                    return
                async with limiter:
                    for url in candidate.urls[:4]:
                        result = await self.prober.probe(url)
                        if result.online and (result.nanokvm or candidate.hostname in known):
                            if len(self.store.list()) >= 256 and candidate.hostname not in known:
                                return
                            device = self.store.upsert_discovery(
                                candidate.hostname, sorted(candidate.addresses), result.url or url,
                                sorted(candidate.mac_addresses),
                            )
                            if device:
                                # Discovery checks the advertised address. A user's custom URL is
                                # checked separately and must not be incorrectly marked online here.
                                if not device["custom_url"]:
                                    self.store.record_probe(device["id"], True, result.latency_ms)
                                self.verified_count += 1
                            return

            await asyncio.gather(*(identify(candidate) for candidate in candidates))
        except Exception as error:
            logger.exception("Discovery failed")
            self.scan_error = str(error)[:200] or type(error).__name__
        finally:
            self.last_scan = now()
            self.request_refresh()

    async def _refresh(self):
        async def check(device):
            urls = [device["url"]]
            if device["source"] == "mdns" and not device["custom_url"]:
                parsed = urlsplit(device["url"])
                urls.extend(
                    address_url(address, parsed.scheme, parsed.port)
                    for address in device["addresses"]
                )
            hints = (
                device["addresses"]
                if urlsplit(device["url"]).hostname == device["hostname"] else ()
            )
            result = None
            for url in list(dict.fromkeys(urls))[:3]:
                result = await self.prober.probe(url, hints)
                if result.online:
                    break
            if result:
                # Editing while a check is in progress must not apply an old result to a new URL.
                latest = self.store.get(device["id"])
                if latest and latest["url"] == device["url"]:
                    self.store.record_probe(
                        device["id"], result.online, result.latency_ms, result.error,
                        result.url if result.online else None,
                    )
        try:
            await asyncio.gather(*(check(device) for device in self.store.list()))
        except Exception:
            logger.exception("Device status refresh failed")
