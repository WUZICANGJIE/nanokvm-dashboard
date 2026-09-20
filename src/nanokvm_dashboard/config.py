import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    mdns_enabled: bool = True
    mdns_interfaces: tuple[str, ...] = ()
    discovery_interval: float = 60
    discovery_seconds: float = 5
    probe_interval: float = 30
    probe_timeout: float = 3
    allow_control: bool = True
    username: str = ""
    password: str = ""

    @classmethod
    def from_env(cls):
        settings = cls(
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            mdns_enabled=os.getenv("MDNS_ENABLED", "true").lower() not in {"0", "false", "no"},
            mdns_interfaces=tuple(
                value.strip()
                for value in os.getenv("MDNS_INTERFACES", "").split(",")
                if value.strip()
            ),
            discovery_interval=max(15, float(os.getenv("DISCOVERY_INTERVAL", "60"))),
            discovery_seconds=min(30, max(2, float(os.getenv("DISCOVERY_SECONDS", "5")))),
            probe_interval=max(10, float(os.getenv("PROBE_INTERVAL", "30"))),
            probe_timeout=min(15, max(1, float(os.getenv("PROBE_TIMEOUT", "3")))),
            allow_control=os.getenv("ALLOW_CONTROL", "true").lower() not in {"0", "false", "no"},
            username=os.getenv("DASHBOARD_USERNAME", ""),
            password=os.getenv("DASHBOARD_PASSWORD", ""),
        )
        if bool(settings.username) != bool(settings.password):
            raise ValueError("Set both DASHBOARD_USERNAME and DASHBOARD_PASSWORD, or neither.")
        return settings
