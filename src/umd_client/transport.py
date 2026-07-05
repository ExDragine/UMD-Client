import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

Payload = dict[str, Any]
UrlOpen = Callable[[urllib.request.Request, int], Any]


def build_payload(
    station_name: str,
    station_key: str,
    value_names: list[str],
    values: list[Any],
    timestamp: int | None = None,
) -> Payload:
    _check_required_string("station_name", station_name)
    _check_required_string("key", station_key)

    data = dict(zip(value_names, values, strict=False))
    data["hold1"] = None
    data["hold2"] = None
    data["hold3"] = None

    return {
        "id": station_name,
        "timestamp": int(time.time()) if timestamp is None else timestamp,
        "key": station_key,
        "data": data,
    }


def send_payload(
    server: str,
    payload: Payload,
    latest_path: str | Path = "latest_data.json",
    timeout: int = 5,
    opener: UrlOpen = urllib.request.urlopen,
) -> bool:
    transmit_data = encode_payload(payload)
    sent = True

    try:
        request = urllib.request.Request(
            url=server,
            data=transmit_data,
            headers={"Content-Type": "application/json"},
        )
        opener(request, timeout)
    except urllib.error.URLError as e:
        sent = False
        print(f"Request failed: {e.reason}")

    latest = Path(latest_path)
    if latest.parent != Path("."):
        latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(transmit_data)
    return sent


def send_to(key: str, name: str, server: str, value_name: list[str], value: list[Any]) -> bool:
    payload = build_payload(station_name=name, station_key=key, value_names=value_name, values=value)
    return send_payload(server=server, payload=payload)


def encode_payload(payload: Payload) -> bytes:
    return json.dumps(payload, ensure_ascii=True, allow_nan=True, indent=4).encode("utf-8")


def _check_required_string(name: str, value: str) -> None:
    if value == "" or not isinstance(value, str):
        raise ValueError(f"{name} incorrect, please input your {name} or check again.")
