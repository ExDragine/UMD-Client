import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when the client configuration is missing or invalid."""


@dataclass(frozen=True)
class LocationConfig:
    city: str = "Guangzhou"
    country: str = "China"
    timezone: str = "Asia/Harbin"
    latitude: float = 23.109866
    longitude: float = 113.2683


@dataclass(frozen=True)
class ClientConfig:
    station_name: str
    station_key: str
    server: str
    sensor_type: str = "sensor_hat"
    record_frequency: int = 30
    storage_size: int = 2880
    data_path: Path = Path("data")
    sn3003_port: str = "/dev/ttyS0"
    display_enabled: bool = False
    display_frequency: int = 300
    camera_enabled: bool = False
    camera_frequency: int = 1800
    location: LocationConfig = LocationConfig()


def load_config(path: str | Path = ".env.toml") -> ClientConfig:
    config_path = Path(path)
    with config_path.open("rb") as f:
        raw = tomllib.load(f)

    record_frequency = _positive_int(raw.get("record_frequency", 30), "record_frequency")
    storage_size = _positive_int(raw.get("storage_size", int(86400 / record_frequency)), "storage_size")
    data_path = Path(raw.get("data_path", Path.cwd() / "data"))

    return ClientConfig(
        station_name=_required_string(raw, "station_name"),
        station_key=_required_string(raw, "station_key"),
        server=_required_string(raw, "server"),
        sensor_type=_sensor_type(raw.get("sensor_type", "sensor_hat")),
        record_frequency=record_frequency,
        storage_size=storage_size,
        data_path=data_path,
        sn3003_port=_optional_string(raw, "sn3003_port", "/dev/ttyS0"),
        display_enabled=_bool(raw.get("display_enabled", False), "display_enabled"),
        display_frequency=_positive_int(raw.get("display_frequency", 300), "display_frequency"),
        camera_enabled=_bool(raw.get("camera_enabled", False), "camera_enabled"),
        camera_frequency=_positive_int(raw.get("camera_frequency", 1800), "camera_frequency"),
        location=LocationConfig(
            city=_optional_string(raw, "city", "Guangzhou"),
            country=_optional_string(raw, "country", "China"),
            timezone=_optional_string(raw, "timezone", "Asia/Harbin"),
            latitude=_float(raw.get("latitude", 23.109866), "latitude"),
            longitude=_float(raw.get("longitude", 113.2683), "longitude"),
        ),
    )


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} is required and must be a non-empty string")
    return value


def _optional_string(raw: dict[str, Any], key: str, default: str) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value


def _positive_int(value: Any, key: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{key} must be a positive integer") from exc
    if parsed <= 0:
        raise ConfigError(f"{key} must be a positive integer")
    return parsed


def _bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{key} must be a boolean")


def _float(value: Any, key: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{key} must be a number") from exc


def _sensor_type(value: Any) -> str:
    if value not in {"sensor_hat", "sn3003"}:
        raise ConfigError("sensor_type must be 'sensor_hat' or 'sn3003'")
    return value
