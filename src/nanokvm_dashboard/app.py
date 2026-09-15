import base64
import binascii
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings
from .models import DeviceInput, ImportData
from .service import DashboardService
from .store import Store


def create_app(settings: Settings | None = None, service_factory=DashboardService):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        store = Store(settings.data_dir)
        service = service_factory(settings, store)
        app.state.service = service
        try:
            await service.start()
            yield
        finally:
            await service.close()
            store.close()

    app = FastAPI(
        title="NanoKVM Dashboard", version=__version__, lifespan=lifespan,
        docs_url=None, redoc_url=None,
    )

    @app.middleware("http")
    async def access_control(request: Request, call_next):
        # Liveness does not disclose devices and remains usable by Docker HEALTHCHECK.
        if settings.username and request.url.path != "/healthz":
            valid = False
            authorization = request.headers.get("authorization", "")
            if authorization.lower().startswith("basic "):
                try:
                    value = base64.b64decode(authorization.split(" ", 1)[1], validate=True).decode()
                    username, password = value.split(":", 1)
                    valid = (
                        secrets.compare_digest(username.encode(), settings.username.encode())
                        & secrets.compare_digest(password.encode(), settings.password.encode())
                    )
                except (ValueError, UnicodeError, binascii.Error):
                    pass
            if not valid:
                return JSONResponse(
                    {"detail": "Authentication required"}, status_code=401,
                    headers={
                        "WWW-Authenticate": 'Basic realm="NanoKVM Dashboard", charset="UTF-8"',
                    },
                )
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and (
                origin == "null" or urlsplit(origin).netloc != request.headers.get("host")
            ):
                return JSONResponse(
                    {"detail": "Cross-origin changes are not allowed"}, status_code=403,
                )
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse(
                    {"detail": "Cross-site changes are not allowed"}, status_code=403,
                )
        response = await call_next(request)
        response.headers["X-NanoKVM-Dashboard"] = __version__
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    async def health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/devices")
    async def devices(request: Request):
        service = request.app.state.service
        return {
            "devices": service.store.list(), "discovery": service.status(), "version": __version__,
        }

    @app.post("/api/devices", status_code=201)
    async def add_device(data: DeviceInput, request: Request):
        service = request.app.state.service
        if len(service.store.list()) >= 256:
            raise HTTPException(409, "A maximum of 256 devices is supported.")
        try:
            device = service.store.add(data)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        service.request_refresh()
        return device

    @app.put("/api/devices/{device_id}")
    async def update_device(device_id: str, data: DeviceInput, request: Request):
        service = request.app.state.service
        try:
            device = service.store.update(device_id, data)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        if device is None:
            raise HTTPException(404, "Device not found")
        service.request_refresh()
        return device

    @app.delete("/api/devices/{device_id}")
    async def delete_device(device_id: str, request: Request):
        if not request.app.state.service.store.delete(device_id):
            raise HTTPException(404, "Device not found")
        return {"ok": True}

    @app.post("/api/discovery", status_code=202)
    async def discover(request: Request):
        if not request.app.state.service.request_scan():
            raise HTTPException(409, "mDNS discovery is disabled in this deployment.")
        return {"ok": True}

    @app.post("/api/discovery/restore", status_code=202)
    async def restore_discovery(request: Request):
        service = request.app.state.service
        service.store.restore_discovery()
        service.request_scan()
        return {"ok": True}

    @app.post("/api/refresh", status_code=202)
    async def refresh(request: Request):
        request.app.state.service.request_refresh()
        return {"ok": True}

    @app.get("/api/export")
    async def export(request: Request):
        return JSONResponse(request.app.state.service.store.export(), headers={
            "Content-Disposition": 'attachment; filename="nanokvm-devices.json"',
        })

    @app.post("/api/import")
    async def import_devices(data: ImportData, request: Request):
        service = request.app.state.service
        try:
            count = service.store.import_devices(data.devices)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        service.request_refresh()
        return {"imported": count}

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def index():
        return FileResponse(static_dir / "index.html")

    return app


app = create_app()
