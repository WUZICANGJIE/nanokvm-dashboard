"""Control layer tests: credential handling, the device protocol, and the API surface.

Nothing here talks to a real NanoKVM. The device side is a fake HTTP transport that
implements the same envelope, cookie check and routes the firmware exposes, and the
password encryption is checked against the OpenSSL command line as an independent
implementation of what the device's web client sends.
"""

import base64
import hashlib
import json
import os
import shutil
import subprocess
from urllib.parse import unquote

import httpx
import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi.testclient import TestClient

from nanokvm_dashboard.app import create_app
from nanokvm_dashboard.config import Settings
from nanokvm_dashboard.control import (
    ControlClient,
    ControlError,
    CredentialVault,
    encrypt_password,
)
from nanokvm_dashboard.models import DeviceInput
from nanokvm_dashboard.service import DashboardService
from nanokvm_dashboard.store import Store

DEVICE_URL = "http://10.9.9.9"
PASSPHRASE = b"nanokvm-sipeed-2024"


def decrypt_password(encrypted: str) -> str:
    """Decrypt what the dashboard sends the way a NanoKVM does (url-decode, then AES)."""
    payload = base64.b64decode(unquote(encrypted))
    assert payload[:8] == b"Salted__"
    salt, body = payload[8:16], payload[16:]
    derived = b""
    block = b""
    while len(derived) < 48:
        block = hashlib.md5(block + PASSPHRASE + salt).digest()
        derived += block
    key, iv = derived[:32], derived[32:48]
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(body) + decryptor.finalize()
    return padded[:-padded[-1]].decode()


def test_password_encryption_round_trips_through_openssl():
    """The firmware key, MD5 key derivation and salted format must match OpenSSL/CryptoJS."""
    if shutil.which("openssl") is None:
        pytest.skip("openssl is required for an independent check")
    encrypted = encrypt_password("hunter2")
    payload = base64.b64decode(unquote(encrypted))
    assert (len(payload) - 16) % 16 == 0
    decrypted = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-md", "md5", "-pass", "pass:nanokvm-sipeed-2024"],
        input=payload, capture_output=True, check=True,
    ).stdout
    assert decrypted == b"hunter2"
    # A fresh random salt every time: identical passwords must not produce identical payloads.
    assert encrypt_password("hunter2") != encrypted


def test_credential_vault_encrypts_at_rest_and_fails_closed_without_its_key(tmp_path):
    vault = CredentialVault(tmp_path / "data")
    token = vault.encrypt("s3cret-value")
    assert "s3cret-value" not in token
    assert vault.decrypt(token) == "s3cret-value"
    assert os.stat(vault.key_file).st_mode & 0o777 == 0o600
    # A restored database without its key file must not turn into a wildcard credential.
    assert CredentialVault(tmp_path / "elsewhere").decrypt(token) == ""


class FakeDevice:
    """A NanoKVM's API surface: login envelope, cookie check, and the routes we use."""

    def __init__(self, username="admin", password="secret"):
        self.username = username
        self.password = password
        self.token = ""
        self.logins = []
        self.pulses = []
        self.pastes = []
        self.reject_once = False

    def transport(self):
        return httpx.MockTransport(self.handle)

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/auth/login":
            body = json.loads(request.content)
            self.logins.append(body["username"])
            matches = (
                body["username"] == self.username
                and decrypt_password(body["password"]) == self.password
            )
            if matches:
                self.token = f"token-{len(self.logins)}"
                return httpx.Response(
                    200, json={"code": 0, "msg": "success", "data": {"token": self.token}},
                )
            return httpx.Response(200, json={"code": -2, "msg": "invalid username or password"})
        if self.reject_once:
            # A logout on the device rotates the signing key and invalidates every session.
            self.reject_once = False
            return httpx.Response(401, json="unauthorized")
        if request.headers.get("cookie") != f"nano-kvm-token={self.token}":
            return httpx.Response(401, json="unauthorized")
        if path == "/api/vm/info":
            return httpx.Response(200, json={
                "code": 0, "msg": "success",
                "data": {"ips": [], "mdns": "kvm-dionysus.local", "image": "v1.4.2",
                         "application": "2.4.3", "deviceKey": "device-key"},
            })
        if path == "/api/vm/gpio" and request.method == "GET":
            return httpx.Response(200, json={
                "code": 0, "msg": "success", "data": {"pwr": True, "hdd": False},
            })
        if path == "/api/vm/gpio" and request.method == "POST":
            self.pulses.append(json.loads(request.content))
            return httpx.Response(200, json={"code": 0, "msg": "success", "data": None})
        if path == "/api/hid/paste":
            self.pastes.append(json.loads(request.content))
            return httpx.Response(200, json={"code": 0, "msg": "success", "data": None})
        return httpx.Response(404)


def client_for(fake: FakeDevice) -> ControlClient:
    return ControlClient(3.0, client=httpx.AsyncClient(transport=fake.transport(), timeout=3.0))


async def test_client_logs_in_once_then_reuses_its_session():
    fake = FakeDevice()
    client = client_for(fake)
    state = await client.state(DEVICE_URL, "admin", "secret")
    assert state.power_state == "on"
    assert state.power is True
    assert state.application == "2.4.3"
    assert state.image == "v1.4.2"
    await client.press(DEVICE_URL, "admin", "secret", "reset")
    await client.press(DEVICE_URL, "admin", "secret", "power", 5000)
    await client.paste(DEVICE_URL, "admin", "secret", "hello")
    assert fake.pulses == [{"type": "reset"}, {"type": "power", "duration": 5000}]
    assert fake.pastes == [{"content": "hello"}]
    assert len(fake.logins) == 1
    await client.close()


async def test_client_logs_in_again_when_the_device_rejects_its_session():
    fake = FakeDevice()
    fake.reject_once = True
    client = client_for(fake)
    state = await client.state(DEVICE_URL, "admin", "secret")
    assert state.power is True
    assert len(fake.logins) == 2
    await client.close()


async def test_client_surfaces_device_errors_without_echoing_the_password():
    fake = FakeDevice()
    client = client_for(fake)
    with pytest.raises(ControlError) as error:
        await client.verify(DEVICE_URL, "admin", "hunter2")
    assert "invalid username or password" in str(error.value)
    assert "hunter2" not in str(error.value)
    await client.close()


async def test_client_refuses_unsupported_actions_and_oversized_paste_before_sending():
    fake = FakeDevice()
    client = client_for(fake)
    with pytest.raises(ControlError):
        await client.press(DEVICE_URL, "admin", "secret", "suspend")
    with pytest.raises(ControlError):
        await client.paste(DEVICE_URL, "admin", "secret", "x" * 1025)
    assert fake.pulses == [] and fake.pastes == []
    await client.close()


class FakeControl:
    """Records what the service asks for; it never opens a socket."""

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.verified = []
        self.pulses = []
        self.pastes = []
        self.forgotten = []
        self.online = True

    async def verify(self, url, username, password, addresses=()):
        if self.error:
            raise self.error
        self.verified.append((url, username, password))

    async def state(self, url, username, password, addresses=()):
        if not self.online:
            raise ControlError("The device is not reachable.")
        return FakeState()

    async def press(self, url, username, password, action, duration=None, addresses=()):
        if self.error:
            raise self.error
        self.pulses.append((action, duration))

    async def paste(self, url, username, password, text, addresses=()):
        if self.error:
            raise self.error
        self.pastes.append(text)

    def forget(self, url, username=""):
        self.forgotten.append(url)

    async def close(self):
        pass


class FakeState:
    power = True
    hdd = False
    application = "2.4.3"
    image = "v1.4.2"
    mdns = "kvm-dionysus.local"

    @property
    def power_state(self):
        return "on"


def app_for(tmp_path, control, **kwargs):
    """An app whose service uses a fake control client and never probes or scans."""

    class Service(DashboardService):
        def __init__(self, settings, store):
            super().__init__(settings, store, control=control)

        async def start(self):
            pass

        def request_refresh(self):
            pass

    return create_app(Settings(data_dir=tmp_path, mdns_enabled=False, **kwargs), Service)


def add_device(client):
    return client.post("/api/devices", json={"name": "工作站", "url": DEVICE_URL}).json()


def post(client, device, path, payload):
    return client.post(f"/api/devices/{device['id']}/{path}", json=payload)


def test_credentials_are_stored_encrypted_and_never_returned(tmp_path):
    control = FakeControl()
    with TestClient(app_for(tmp_path, control)) as client:
        device = add_device(client)
        assert device["control"] is False
        assert post(client, device, "power", {"action": "power"}).status_code == 502
        saved = post(client, device, "control", {"username": "admin", "password": "secret"})
        assert saved.status_code == 200
        assert saved.json()["control"] is True
        assert saved.json()["kvm_username"] == "admin"
        assert control.verified == [(DEVICE_URL, "admin", "secret")]
        listed = client.get("/api/devices")
        assert "secret" not in listed.text
        assert "kvm_password" not in listed.text
        assert listed.json()["devices"][0]["control"] is True
        # The reading the device reported right after the credentials were saved.
        assert listed.json()["devices"][0]["power_state"] == "on"
        assert listed.json()["devices"][0]["app_version"] == "2.4.3"
        assert client.delete(f"/api/devices/{device['id']}/control").status_code == 200
        cleared = client.get("/api/devices").json()["devices"][0]
        assert cleared["control"] is False and cleared["kvm_username"] == ""
        assert control.forgotten == [DEVICE_URL]


def test_rejected_credentials_are_not_stored(tmp_path):
    control = FakeControl(ControlError("invalid username or password"))
    with TestClient(app_for(tmp_path, control)) as client:
        device = add_device(client)
        response = post(client, device, "control", {"username": "admin", "password": "wrong"})
        assert response.status_code == 400
        assert "invalid username or password" in response.json()["detail"]
        assert client.get("/api/devices").json()["devices"][0]["control"] is False


def test_power_and_paste_reach_the_device_only_through_the_client(tmp_path):
    control = FakeControl()
    with TestClient(app_for(tmp_path, control)) as client:
        device = add_device(client)
        post(client, device, "control", {"username": "admin", "password": "secret"})
        assert post(client, device, "power", {"action": "reset"}).status_code == 200
        assert post(client, device, "power",
                    {"action": "power", "duration": 5000}).status_code == 200
        assert post(client, device, "paste", {"text": "echo hi"}).status_code == 200
        assert control.pulses == [("reset", None), ("power", 5000)]
        assert control.pastes == ["echo hi"]
        # Validation happens before anything is sent to a device.
        assert post(client, device, "power", {"action": "suspend"}).status_code == 422
        assert post(client, device, "paste", {"text": "x" * 1025}).status_code == 422
        assert control.pulses == [("reset", None), ("power", 5000)]


def test_control_is_refused_when_disabled_in_the_deployment(tmp_path):
    with TestClient(app_for(tmp_path, None, allow_control=False)) as client:
        device = add_device(client)
        assert client.get("/api/devices").json()["control_available"] is False
        response = post(client, device, "control", {"username": "admin", "password": "secret"})
        assert response.status_code == 403


def test_cross_origin_control_requests_are_rejected(tmp_path):
    control = FakeControl()
    with TestClient(app_for(tmp_path, control)) as client:
        device = add_device(client)
        response = client.post(
            f"/api/devices/{device['id']}/power", json={"action": "power"},
            headers={"Origin": "https://another-site.example"},
        )
        assert response.status_code == 403
        assert control.pulses == []


def test_control_endpoints_sit_behind_the_dashboard_login(tmp_path):
    control = FakeControl()
    settings = {"username": "admin", "password": "panel-password"}
    with TestClient(app_for(tmp_path, control, **settings)) as client:
        blocked = client.post("/api/devices/anything/power", json={"action": "power"})
        assert blocked.status_code == 401
        credentials = base64.b64encode(b"admin:panel-password").decode()
        headers = {"Authorization": f"Basic {credentials}"}
        listed = client.get("/api/devices", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["dashboard_auth"] is True


async def test_state_poll_records_the_power_led_and_reports_failures(tmp_path):
    store = Store(tmp_path)
    device = store.add(DeviceInput(name="工作站", url=DEVICE_URL))
    control = FakeControl()
    service = DashboardService(
        Settings(data_dir=tmp_path, mdns_enabled=False), store, control=control,
    )
    store.set_credentials(device["id"], "admin", service.vault.encrypt("secret"))
    await service._poll_control(store.get(device["id"]))
    saved = store.get(device["id"])
    assert saved["power_state"] == "on"
    assert saved["app_version"] == "2.4.3"
    assert saved["control_error"] == ""
    # A failed poll withdraws the reading instead of leaving a stale claim behind.
    control.online = False
    await service._poll_control(store.get(device["id"]))
    assert store.get(device["id"])["power_state"] == ""
    assert "not reachable" in store.get(device["id"])["control_error"]
    await service.close()
    store.close()
