import sqlite3

from nanokvm_dashboard.models import DeviceInput
from nanokvm_dashboard.store import Store


def test_discovery_address_change_preserves_identity_and_customization(tmp_path):
    store = Store(tmp_path)
    device = store.upsert_discovery("KVM-NAS.local.", ["192.168.1.10"], "http://192.168.1.10")
    store.update(device["id"], DeviceInput(
        name="My NAS", url=device["url"], notes="Rack 1", favorite=True,
    ))
    refreshed = store.upsert_discovery(
        "kvm-nas.local", ["192.168.1.20", "192.168.1.21"], "http://192.168.1.20",
    )
    assert refreshed["id"] == device["id"]
    assert refreshed["name"] == "My NAS"
    assert refreshed["favorite"] is True
    assert refreshed["notes"] == "Rack 1"
    assert refreshed["url"] == "http://192.168.1.20"
    assert len(store.list()) == 1
    store.record_probe(device["id"], True, 12)
    store.close()
    reopened = Store(tmp_path)
    assert reopened.get(device["id"])["status"] == "unknown"
    assert reopened.get(device["id"])["last_seen"]
    assert reopened.get(device["id"])["name"] == "My NAS"
    reopened.close()


def test_manual_device_is_associated_and_custom_url_is_kept(tmp_path):
    store = Store(tmp_path)
    manual = store.add(DeviceInput(name="Desk", url="https://192.168.1.10:8443"))
    discovered = store.upsert_discovery("desk.local", ["192.168.1.10"], "http://192.168.1.10")
    assert manual["id"] == discovered["id"]
    assert discovered["url"] == manual["url"]
    assert discovered["name"] == "Desk"
    assert discovered["source"] == "mdns"
    store.close()


def test_removed_discovery_does_not_immediately_return(tmp_path):
    store = Store(tmp_path)
    device = store.upsert_discovery("kvm.local", ["192.168.1.10"], "http://192.168.1.10")
    assert store.delete(device["id"])
    assert store.upsert_discovery("kvm.local", ["192.168.1.20"], "http://192.168.1.20") is None
    store.restore_discovery()
    assert store.upsert_discovery("kvm.local", ["192.168.1.20"], "http://192.168.1.20")
    store.close()


def test_import_merge_retains_devices_and_exports_only_portable_fields(tmp_path):
    store = Store(tmp_path)
    one = store.add(DeviceInput(name="Old", url="192.168.1.10"))
    store.add(DeviceInput(name="Keep", url="192.168.1.11"))
    store.import_devices([
        DeviceInput(name="Renamed", url="192.168.1.10", favorite=True),
        DeviceInput(name="New", url="192.168.1.12"),
    ])
    assert len(store.list()) == 3
    assert store.get(one["id"])["name"] == "Renamed"
    assert set(store.export()["devices"][0]) == {"name", "url", "notes", "favorite"}
    store.close()


def test_mac_metadata_updates_and_survives_edit_import_and_restart(tmp_path):
    store = Store(tmp_path)
    manual = store.add(DeviceInput(name="Desk", url="192.168.1.10"))
    assert manual["mac_addresses"] == []
    macs = ["02:ab:cd:12:34:57", "02:ab:cd:12:34:56", "02:ab:cd:12:34:56"]
    device = store.upsert_discovery("desk.local", ["192.168.1.10"], manual["url"], macs)
    assert device["id"] == manual["id"]
    assert device["mac_addresses"] == sorted(set(macs))
    store.update(device["id"], DeviceInput(
        name="Edited", url=device["url"], notes="Keep", favorite=True,
    ))
    store.import_devices([DeviceInput(name="Imported", url=device["url"], favorite=True)])
    assert store.get(device["id"])["mac_addresses"] == sorted(set(macs))
    assert "mac_addresses" not in store.export()["devices"][0]
    # Missing metadata must not erase a previously received value.
    device = store.upsert_discovery("desk.local", ["192.168.1.20"], "http://192.168.1.20")
    assert device["mac_addresses"] == sorted(set(macs))
    # A new nonempty snapshot replaces old values instead of accumulating forever.
    replacement = ["02:ab:cd:12:34:58"]
    store.upsert_discovery("desk.local", ["192.168.1.20"], "http://192.168.1.20", replacement)
    store.close()
    reopened = Store(tmp_path)
    saved = reopened.get(device["id"])
    assert saved["mac_addresses"] == replacement
    assert saved["name"] == "Imported"
    assert saved["favorite"] is True
    assert saved["url"] == manual["url"]
    reopened.close()


def test_existing_database_is_migrated_without_losing_devices_or_ignored_hosts(tmp_path):
    # Schema from 0.1.0, before MAC metadata existed.
    with sqlite3.connect(tmp_path / "dashboard.db") as connection:
        connection.executescript("""
            CREATE TABLE devices (
                id TEXT PRIMARY KEY, identity TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, custom_name INTEGER NOT NULL DEFAULT 0,
                url TEXT NOT NULL, custom_url INTEGER NOT NULL DEFAULT 0,
                hostname TEXT NOT NULL DEFAULT '', addresses TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
                favorite INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
                last_seen TEXT, last_checked TEXT, status TEXT NOT NULL DEFAULT 'unknown',
                latency_ms INTEGER, error TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE ignored (identity TEXT PRIMARY KEY);
            INSERT INTO devices (id,identity,name,url,source,notes,favorite,created_at)
                VALUES ('old','mdns:desk.local','Desk','http://192.168.1.10',
                        'mdns','Keep notes',1,'2026-01-01');
            INSERT INTO ignored VALUES ('mdns:ignored.local');
        """)
    for _ in range(2):
        store = Store(tmp_path)
        old = store.get("old")
        assert old["mac_addresses"] == []
        assert old["notes"] == "Keep notes"
        assert old["favorite"] is True
        assert store.is_ignored("ignored.local")
        store.close()
