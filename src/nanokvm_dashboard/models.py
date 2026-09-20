import ipaddress
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

LOCAL_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10", "fc00::/7")
)


def is_local_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(
        address.version == network.version and address in network for network in LOCAL_NETWORKS
    )


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value or any(ord(character) < 33 for character in value) or "\\" in value:
        raise ValueError("Enter a valid device URL or IP address.")
    if "://" not in value:
        value = "http://" + value
    try:
        parsed = urlsplit(value)
        host, port = parsed.hostname, parsed.port
    except ValueError as error:
        raise ValueError("Invalid host or port.") from error
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("Only http:// and https:// device URLs are supported.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Do not include login credentials in a device URL.")
    if parsed.query or parsed.fragment:
        raise ValueError("Use the device base URL without a query string or fragment.")
    host = host.lower().rstrip(".")
    if "%" in host or host in {"localhost", "localhost.localdomain"}:
        raise ValueError("Use a LAN IP or hostname, not localhost or a scoped address.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if len(host) > 253 or any(
            not label or len(label) > 63
            or not all(c.isascii() and (c.isalnum() or c == "-") for c in label)
            or label.startswith("-") or label.endswith("-")
            for label in host.split(".")
        ):
            raise ValueError("Invalid device hostname.") from None
    else:
        if not is_local_address(host):
            raise ValueError(
                "Device addresses must be on a private LAN, ULA, or Tailscale network."
            )
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")
    authority = f"[{host}]" if ":" in host else host
    if port is not None:
        authority += f":{port}"
    return urlunsplit((parsed.scheme, authority, parsed.path.rstrip("/"), "", ""))


class DeviceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    notes: str = Field(default="", max_length=1000)
    favorite: bool = False

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("A device name is required.")
        return value

    @field_validator("url")
    @classmethod
    def clean_url(cls, value):
        return normalize_url(value)


class ControlCredentials(BaseModel):
    """NanoKVM login used by the dashboard to control this device."""

    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class PowerAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["power", "reset"]
    duration: int | None = Field(default=None, ge=100, le=10000)


class PasteText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=1024)


class ImportData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(default=1, ge=1, le=1)
    devices: list[DeviceInput] = Field(max_length=256)
