import base64

from fastapi.testclient import TestClient

from nanokvm_dashboard.app import create_app
from nanokvm_dashboard.config import Settings
from nanokvm_dashboard.service import DashboardService


class QuietService(DashboardService):
    async def start(self):
        pass

    def request_refresh(self):
        pass


def client_for(tmp_path, **kwargs):
    return TestClient(create_app(
        Settings(data_dir=tmp_path, mdns_enabled=False, **kwargs), QuietService,
    ))


def test_device_crud_import_validation_and_static_assets(tmp_path):
    with client_for(tmp_path) as client:
        assert client.get("/").status_code == 200
        assert "default-src 'self'" in client.get("/").headers["content-security-policy"]
        assert client.get("/static/app.js").status_code == 200
        data = {"name": "Desk", "url": "192.168.1.10"}
        created = client.post("/api/devices", json=data)
        assert created.status_code == 201
        device = created.json()
        assert device["url"] == "http://192.168.1.10"
        assert client.post("/api/devices", json=data).status_code == 409
        assert client.post("/api/discovery").status_code == 409
        bad_import = {"version": 1, "devices": [data, {"name": "Bad", "url": "file:///etc/passwd"}]}
        assert client.post("/api/import", json=bad_import).status_code == 422
        assert len(client.get("/api/devices").json()["devices"]) == 1
        export = client.get("/api/export").json()
        assert export["devices"][0]["name"] == "Desk"
        data.update(name="Renamed", favorite=True)
        assert client.put(f"/api/devices/{device['id']}", json=data).status_code == 200
        assert client.delete(f"/api/devices/{device['id']}").status_code == 200
        assert client.get("/api/devices").json()["devices"] == []


def test_cross_origin_changes_are_rejected(tmp_path):
    with client_for(tmp_path) as client:
        response = client.post("/api/devices", json={"name": "x", "url": "192.168.1.10"},
                               headers={"Origin": "https://another-site.example"})
        assert response.status_code == 403
        assert client.post("/api/refresh", headers={"Origin": "null"}).status_code == 403


def test_optional_auth_and_health_check(tmp_path):
    with client_for(tmp_path, username="admin", password="test-only-password") as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/api/devices").status_code == 401
        assert client.get("/").status_code == 401
        credentials = base64.b64encode(b"admin:test-only-password").decode()
        response = client.get("/api/devices", headers={"Authorization": f"Basic {credentials}"})
        assert response.status_code == 200
