"""Optional NanoKVM control: stored credentials, device login, power pulses and paste.

The dashboard reads device pages and nothing else until the user saves NanoKVM credentials
for a specific device. With credentials stored, the service polls that device's power LED
state and can send an ATX-button pulse or type clipboard text into the attached machine -
both only from an explicit dashboard request. Stored passwords are encrypted with a key
file beside the database, so a copy of `dashboard.db` alone is not enough to log in.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .probe import resolve_addresses

logger = logging.getLogger(__name__)

# The device decrypts the login password with a key baked into its own web client, so the
# dashboard has to reproduce that layer rather than send the password in the clear.
FIRMWARE_PASSPHRASE = b"nanokvm-sipeed-2024"
COOKIE_NAME = "nano-kvm-token"
MAX_PASTE_LENGTH = 1024  # The KVM rejects longer clipboard payloads itself.
DEFAULT_PULSE_MS = 800  # Firmware default when a pulse length is not sent.
LONG_PULSE_MS = 5000  # Long enough to force a power-off on most ATX boards.
LOGIN_TIMEOUT = 20.0  # A rejected login makes the device sleep for 2-3 seconds first.


class ControlError(RuntimeError):
    """A control request was refused, failed, or the device could not be reached."""


class Unauthorized(ControlError):
    """The cached session is no longer accepted; log in again before retrying."""


def evp_bytes_to_key(passphrase: bytes, salt: bytes, key_length=32, iv_length=16):
    """OpenSSL EVP_BytesToKey with MD5, one iteration: what CryptoJS derives from a passphrase."""
    derived = b""
    block = b""
    while len(derived) < key_length + iv_length:
        block = hashlib.md5(block + passphrase + salt).digest()
        derived += block
    return derived[:key_length], derived[key_length:key_length + iv_length]


def encrypt_password(password: str) -> str:
    """AES-256-CBC in OpenSSL `Salted__` form, percent-encoded, exactly as the web UI sends it."""
    salt = secrets.token_bytes(8)
    key, iv = evp_bytes_to_key(FIRMWARE_PASSPHRASE, salt)
    payload = password.encode()
    padding = 16 - len(payload) % 16
    padded = payload + bytes([padding]) * padding
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    body = encryptor.update(padded) + encryptor.finalize()
    return quote(base64.b64encode(b"Salted__" + salt + body).decode(), safe="")


class CredentialVault:
    """Encrypt stored device passwords with a key file in the data directory."""

    def __init__(self, directory: Path):
        self.key_file = Path(directory) / "credentials.key"
        self.fernet: Fernet | None = None

    def _cipher(self) -> Fernet:
        # The key file is created on first use, so a read-only dashboard never leaves one.
        if self.fernet is None:
            self.fernet = Fernet(self._load_key())
        return self.fernet

    def _load_key(self) -> bytes:
        try:
            key = self.key_file.read_bytes().strip()
        except FileNotFoundError:
            pass
        else:
            if key:
                return key
        key = Fernet.generate_key()
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        # Create with 0600 before writing: the key must never be briefly world-readable.
        descriptor = os.open(self.key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(key)
        return key

    def encrypt(self, value: str) -> str:
        return self._cipher().encrypt(value.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Return the password, or an empty string when the key no longer matches."""
        try:
            return self._cipher().decrypt(token.encode()).decode()
        except (InvalidToken, ValueError):
            return ""


@dataclass(frozen=True)
class DeviceState:
    """What a NanoKVM reports about the machine it is wired to."""

    power: bool
    hdd: bool
    application: str
    image: str
    mdns: str

    @property
    def power_state(self) -> str:
        # The power LED is active-low on the device's GPIO, and the firmware already
        # inverts it: `pwr` is true when the attached machine is powered on.
        return "on" if self.power else "off"


class ControlClient:
    """Talk to a NanoKVM's own API with stored credentials, never with the browser's session."""

    def __init__(self, timeout: float, client: httpx.AsyncClient | None = None):
        self.timeout = timeout
        self.client = client or httpx.AsyncClient(
            verify=False, follow_redirects=False, trust_env=False, timeout=timeout,
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
        )
        self.tokens: dict[tuple[str, str], str] = {}
        # One lock for every login: the device locks an IP out after repeated failures, so
        # concurrent logins are serialised instead of being raced.
        self.login_lock = asyncio.Lock()

    async def close(self):
        await self.client.aclose()

    def forget(self, url: str, username: str = ""):
        """Drop cached sessions for a device, so the next call logs in again."""
        for key in [
            key for key in self.tokens
            if key[0] == url and (not username or key[1] == username)
        ]:
            self.tokens.pop(key, None)

    async def verify(self, url: str, username: str, password: str, addresses=()) -> None:
        """Prove the credentials work before they are stored."""
        await self._login(url, username, password, addresses)

    async def state(self, url: str, username: str, password: str, addresses=()) -> DeviceState:
        info = await self._call(url, username, password, "GET", "/api/vm/info", addresses=addresses)
        gpio = await self._call(url, username, password, "GET", "/api/vm/gpio", addresses=addresses)
        data = info or {}
        return DeviceState(
            power=bool((gpio or {}).get("pwr")),
            hdd=bool((gpio or {}).get("hdd")),
            application=str(data.get("application") or ""),
            image=str(data.get("image") or ""),
            mdns=str(data.get("mdns") or ""),
        )

    async def press(
        self, url: str, username: str, password: str, action: str,
        duration: int | None = None, addresses=(),
    ) -> None:
        """Pulse the ATX power or reset button through the KVM's GPIO."""
        if action not in {"power", "reset"}:
            raise ControlError("Unsupported power action.")
        body: dict[str, object] = {"type": action}
        if duration:
            body["duration"] = int(duration)
        await self._call(url, username, password, "POST", "/api/vm/gpio", body, addresses)

    async def paste(self, url: str, username: str, password: str, text: str, addresses=()) -> None:
        """Type text on the attached machine as USB keyboard input."""
        if not text:
            raise ControlError("Nothing to paste.")
        if len(text) > MAX_PASTE_LENGTH:
            raise ControlError(f"Paste is limited to {MAX_PASTE_LENGTH} characters.")
        await self._call(
            url, username, password, "POST", "/api/hid/paste", {"content": text}, addresses,
        )

    async def _call(
        self, url: str, username: str, password: str, method: str, path: str,
        body=None, addresses=(), retry=True,
    ):
        token = await self._token(url, username, password, addresses)
        try:
            return await self._request(
                url, method, path, token=token, body=body, addresses=addresses,
            )
        except Unauthorized:
            # Sessions are signed JWTs that expire, and a logout on the device rotates the
            # key and invalidates every token. Log in again once, then give up.
            if not retry:
                raise
            self.forget(url, username)
            token = await self._token(url, username, password, addresses)
            return await self._request(
                url, method, path, token=token, body=body, addresses=addresses,
            )

    async def _token(self, url: str, username: str, password: str, addresses=()) -> str:
        key = (url, username)
        token = self.tokens.get(key)
        if token:
            return token
        return await self._login(url, username, password, addresses)

    async def _login(self, url: str, username: str, password: str, addresses=()) -> str:
        async with self.login_lock:
            key = (url, username)
            if token := self.tokens.get(key):
                return token
            data = await self._request(
                url, "POST", "/api/auth/login",
                body={"username": username, "password": encrypt_password(password)},
                addresses=addresses, timeout=LOGIN_TIMEOUT,
            )
            token = str((data or {}).get("token") or "")
            if not token:
                raise ControlError("The device returned no session token.")
            self.tokens[key] = token
            return token

    async def _request(
        self, url: str, method: str, path: str, token=None, body=None, addresses=(),
        timeout: float | None = None,
    ):
        parsed = urlsplit(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not parsed.hostname:
            raise ControlError("This device URL has no host.")
        try:
            resolved = await resolve_addresses(parsed.hostname, port, addresses)
        except ValueError as error:
            raise ControlError(str(error)) from error
        headers = {"User-Agent": "NanoKVM-Dashboard/0.1"}
        if token:
            headers["Cookie"] = f"{COOKIE_NAME}={token}"
        last_error: Exception | None = None
        for address in resolved:
            host = f"[{address}]" if ":" in address else address
            endpoint = urlunsplit((parsed.scheme, f"{host}:{port}", path, "", ""))
            try:
                # Connect to the address already validated as local, not a second resolution.
                response = await self.client.request(
                    method, endpoint, headers={**headers, "Host": parsed.netloc}, json=body,
                    extensions={"sni_hostname": parsed.hostname},
                    timeout=timeout or self.timeout,
                )
            except httpx.HTTPError as error:
                last_error = error
                continue
            return self._unwrap(response)
        raise ControlError(str(last_error) or "The device is not reachable.")

    @staticmethod
    def _unwrap(response: httpx.Response):
        if response.status_code == 401:
            raise Unauthorized("The device rejected the dashboard session.")
        if response.status_code >= 400:
            raise ControlError(f"The device answered HTTP {response.status_code}.")
        try:
            payload = response.json()
        except ValueError as error:
            raise ControlError("The device sent a response that is not JSON.") from error
        if not isinstance(payload, dict):
            raise ControlError("The device sent an unexpected response.")
        if payload.get("code") != 0:
            # Failures arrive as HTTP 200 with a non-zero code. Codes are the firmware's own;
            # -2 on login means the username or password is wrong (or the IP is locked out).
            raise ControlError(str(payload.get("msg") or "The device refused the request."))
        return payload.get("data")
