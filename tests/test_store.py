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
