import asyncio
import ipaddress
import re
import socket
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from .models import is_local_address, normalize_url


@dataclass(frozen=True)
class ProbeResult:
    online: bool
    nanokvm: bool = False
    latency_ms: int | None = None
    error: str = ""
    url: str = ""


def is_nanokvm_page(body: str, headers: httpx.Headers) -> bool:
    if headers.get("x-nanokvm-dashboard"):
        return False
    return bool(re.search(r"nano[\s_-]*kvm", body, re.IGNORECASE))


async def resolve_addresses(host: str, port: int, known_addresses=()) -> list[str]:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if known_addresses:
            addresses = list(known_addresses)
        else:
            records = await asyncio.wait_for(
                asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM),
                timeout=3,
            )
            addresses = [record[4][0] for record in records]
    else:
        addresses = [host]
    addresses = list(dict.fromkeys(addresses))
    if not addresses or any(not is_local_address(address) for address in addresses):
        raise ValueError("Target does not resolve exclusively to a supported local network.")
    return sorted(addresses, key=lambda address: (":" in address, address))[:4]


class Prober:
    def __init__(self, timeout: float, client: httpx.AsyncClient | None = None):
        self.timeout = timeout
        # NanoKVM's default HTTPS certificate is self-signed. Only local targets are allowed.
        self.client = client or httpx.AsyncClient(
            verify=False, follow_redirects=False, trust_env=False, timeout=timeout,
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=8),
        )
        self.semaphore = asyncio.Semaphore(8)

    async def close(self):
        await self.client.aclose()

    async def probe(self, url: str, known_addresses=()) -> ProbeResult:
        async with self.semaphore:
            started = time.monotonic()
            try:
                async with asyncio.timeout(self.timeout * 3 + 3):
                    current = normalize_url(url)
                    for _ in range(3):
                        parsed = urlsplit(current)
                        port = parsed.port or (443 if parsed.scheme == "https" else 80)
                        hints = known_addresses if parsed.hostname == urlsplit(url).hostname else ()
                        addresses = await resolve_addresses(parsed.hostname, port, hints)
                        last_error = None
                        for address in addresses:
                            host = f"[{address}]" if ":" in address else address
                            endpoint = urlunsplit(
                                (parsed.scheme, f"{host}:{port}", parsed.path or "/", "", "")
                            )
                            try:
                                # Connect to the address we validated, not a second DNS resolution.
                                async with self.client.stream(
                                    "GET", endpoint,
                                    headers={
                                        "Host": parsed.netloc,
                                        "User-Agent": "NanoKVM-Dashboard/0.1",
                                    },
                                    extensions={"sni_hostname": parsed.hostname},
                                ) as response:
                                    if response.status_code in {301, 302, 303, 307, 308}:
                                        location = response.headers.get("location")
                                        if not location:
                                            raise ValueError("Redirect destination is missing.")
                                        current = normalize_url(urljoin(current + "/", location))
                                        break
                                    content = bytearray()
                                    async for chunk in response.aiter_bytes():
                                        content.extend(chunk[: max(0, 65536 - len(content))])
                                        if len(content) >= 65536:
                                            break
                                    online = (
                                        200 <= response.status_code < 400
                                        or response.status_code in {401, 403}
                                    )
                                    return ProbeResult(
                                        online=online,
                                        nanokvm=is_nanokvm_page(
                                            content.decode(errors="replace"), response.headers,
                                        ),
                                        latency_ms=round((time.monotonic() - started) * 1000),
                                        error="" if online else f"HTTP {response.status_code}",
                                        url=current,
                                    )
                            except httpx.HTTPError as error:
                                last_error = error
                        else:
                            if last_error is not None:
                                raise last_error
                            raise ValueError("No reachable local address.")
                    raise ValueError("Too many redirects.")
            except (httpx.HTTPError, TimeoutError, OSError, ValueError) as error:
                message = str(error) or type(error).__name__
                return ProbeResult(False, error=message[:200], url=url)
