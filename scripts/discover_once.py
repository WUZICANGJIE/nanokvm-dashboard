"""Run one mDNS discovery and HTTP identity check; keep all state in a temporary directory."""

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from nanokvm_dashboard.config import Settings
from nanokvm_dashboard.service import DashboardService
from nanokvm_dashboard.store import Store


async def run(args):
    with tempfile.TemporaryDirectory() as directory:
        settings = Settings(
            data_dir=Path(directory), mdns_interfaces=tuple(args.interface),
            discovery_seconds=args.seconds,
        )
        store = Store(settings.data_dir)
        service = DashboardService(settings, store)
        try:
            await service._scan()
            if service.refresh_task:
                await service.refresh_task
            print(json.dumps({
                "discovery": service.status(),
                "devices": [
                    {key: device[key] for key in (
                        "name", "hostname", "url", "addresses", "mac_addresses", "status",
                    )}
                    for device in store.list()
                ],
            }, ensure_ascii=False, indent=2))
        finally:
            await service.close()
            store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", action="append", default=[], help="This host's LAN IPv4")
    parser.add_argument("--seconds", type=float, default=5)
    asyncio.run(run(parser.parse_args()))
