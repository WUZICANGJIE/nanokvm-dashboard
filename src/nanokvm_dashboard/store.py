from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from .models import DeviceInput


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(directory / "dashboard.db")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY, identity TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, custom_name INTEGER NOT NULL DEFAULT 0,
                url TEXT NOT NULL, custom_url INTEGER NOT NULL DEFAULT 0,
                hostname TEXT NOT NULL DEFAULT '', addresses TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
                favorite INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
                last_seen TEXT, last_checked TEXT, status TEXT NOT NULL DEFAULT 'unknown',
                latency_ms INTEGER, error TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS ignored (identity TEXT PRIMARY KEY);
        """)
        # A stored successful check is not evidence that a device is online after a restart.
        with self.connection:
            self.connection.execute(
                "UPDATE devices SET status='unknown', latency_ms=NULL, error=''"
            )

    def close(self):
        self.connection.close()

    @staticmethod
    def decode(row):
        if row is None:
            return None
        result = dict(row)
        result["addresses"] = json.loads(result["addresses"])
        for key in ("favorite", "custom_name", "custom_url"):
            result[key] = bool(result[key])
        return result

    def list(self):
        return [
            self.decode(row)
            for row in self.connection.execute(
                "SELECT * FROM devices ORDER BY favorite DESC, name COLLATE NOCASE"
            )
        ]

    def get(self, device_id):
        return self.decode(
            self.connection.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
        )

    def add(self, data: DeviceInput):
        for device in self.list():
            if device["url"] == data.url:
                raise ValueError("This device URL is already saved.")
        device_id = str(uuid.uuid4())
        with self.connection:
            self.connection.execute(
                """INSERT INTO devices
                (id,identity,name,custom_name,url,custom_url,source,notes,favorite,created_at)
                VALUES (?,?,?,1,?,1,'manual',?,?,?)""",
                (device_id, "manual:" + data.url, data.name, data.url,
                 data.notes, data.favorite, now()),
            )
        return self.get(device_id)

    def update(self, device_id, data: DeviceInput):
        device = self.get(device_id)
        if device is None:
            return None
        if any(d["id"] != device_id and d["url"] == data.url for d in self.list()):
            raise ValueError("This device URL is already saved.")
        with self.connection:
            self.connection.execute(
                """UPDATE devices SET name=?, custom_name=?, url=?, custom_url=?, notes=?,
                favorite=?, status=CASE WHEN url!=? THEN 'unknown' ELSE status END WHERE id=?""",
                (data.name, device["custom_name"] or data.name != device["name"],
                 data.url, device["custom_url"] or data.url != device["url"], data.notes,
                 data.favorite, data.url, device_id),
            )
        return self.get(device_id)

    def delete(self, device_id):
        device = self.get(device_id)
        if device is None:
            return False
        with self.connection:
            if device["source"] == "mdns":
                self.connection.execute(
                    "INSERT OR IGNORE INTO ignored VALUES (?)", (device["identity"],)
                )
            self.connection.execute("DELETE FROM devices WHERE id=?", (device_id,))
        return True

    def restore_discovery(self):
        with self.connection:
            self.connection.execute("DELETE FROM ignored")

    def is_ignored(self, hostname):
        return self.connection.execute(
            "SELECT 1 FROM ignored WHERE identity=?", ("mdns:" + hostname.lower().rstrip("."),)
        ).fetchone() is not None

    def upsert_discovery(self, hostname, addresses, url):
        hostname = hostname.lower().rstrip(".")
        identity = "mdns:" + hostname
        if self.is_ignored(hostname):
            return None
        device = self.decode(
            self.connection.execute(
                "SELECT * FROM devices WHERE identity=?", (identity,),
            ).fetchone()
        )
        if device is None:
            # Associate a manually added endpoint with its later mDNS advertisement.
            for saved in self.list():
                if (
                    saved["source"] == "manual"
                    and urlsplit(saved["url"]).hostname in {hostname, *addresses}
                ):
                    device = saved
                    break
        with self.connection:
            if device:
                self.connection.execute(
                    """UPDATE devices SET identity=?,hostname=?,addresses=?,source='mdns',
                    url=CASE WHEN custom_url=0 THEN ? ELSE url END WHERE id=?""",
                    (identity, hostname, json.dumps(addresses), url, device["id"]),
                )
                device_id = device["id"]
            else:
                device_id = str(uuid.uuid4())
                self.connection.execute(
                    """INSERT INTO devices
                    (id,identity,name,url,hostname,addresses,source,created_at)
                    VALUES (?,?,?,?,?,?,'mdns',?)""",
                    (device_id, identity, hostname.removesuffix(".local"), url,
                     hostname, json.dumps(addresses), now()),
                )
        return self.get(device_id)

    def record_probe(self, device_id, online, latency_ms, error="", working_url=None):
        checked = now()
        with self.connection:
            self.connection.execute(
                """UPDATE devices SET status=?,latency_ms=?,error=?,last_checked=?,
                last_seen=CASE WHEN ? THEN ? ELSE last_seen END,
                url=CASE WHEN custom_url=0 AND ? IS NOT NULL THEN ? ELSE url END WHERE id=?""",
                ("online" if online else "offline", latency_ms, error, checked, online, checked,
                 working_url, working_url, device_id),
            )

    def export(self):
        return {"version": 1, "devices": [
            {key: device[key] for key in ("name", "url", "notes", "favorite")}
            for device in self.list()
        ]}

    def import_devices(self, devices: list[DeviceInput]):
        if len({device.url for device in devices}) != len(devices):
            raise ValueError("Import contains duplicate device URLs.")
        existing = {device["url"]: device for device in self.list()}
        if len(set(existing) | {device.url for device in devices}) > 256:
            raise ValueError("A maximum of 256 devices is supported.")
        # Models are validated before this transaction; merge without erasing existing devices.
        with self.connection:
            for data in devices:
                if data.url in existing:
                    self.connection.execute(
                        "UPDATE devices SET name=?,custom_name=1,notes=?,favorite=? WHERE id=?",
                        (data.name, data.notes, data.favorite, existing[data.url]["id"]),
                    )
                else:
                    self.connection.execute(
                        """INSERT INTO devices
                        (id,identity,name,custom_name,url,custom_url,source,notes,favorite,created_at)
                        VALUES (?,?,?,1,?,1,'manual',?,?,?)""",
                        (str(uuid.uuid4()), "manual:" + data.url, data.name, data.url,
                         data.notes, data.favorite, now()),
                    )
        return len(devices)
