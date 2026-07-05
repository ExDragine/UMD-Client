import json
import urllib.error

from umd_client.transport import build_payload, send_payload


def test_build_payload_preserves_current_wire_shape():
    payload = build_payload(
        station_name="station-a",
        station_key="secret",
        value_names=["time", "temperature", "humidity"],
        values=[111, 22.5, 60.0],
        timestamp=123,
    )

    assert payload == {
        "id": "station-a",
        "timestamp": 123,
        "key": "secret",
        "data": {
            "time": 111,
            "temperature": 22.5,
            "humidity": 60.0,
            "hold1": None,
            "hold2": None,
            "hold3": None,
        },
    }


def test_send_payload_posts_json_and_writes_latest_file(tmp_path):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["data"] = request.data
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout

    payload = {"id": "station-a", "timestamp": 123, "key": "secret", "data": {"temperature": 22.5}}
    latest_path = tmp_path / "latest_data.json"

    sent = send_payload(
        server="https://example.test/upload",
        payload=payload,
        latest_path=latest_path,
        opener=fake_urlopen,
    )

    assert sent is True
    assert captured["url"] == "https://example.test/upload"
    assert captured["timeout"] == 5
    assert captured["headers"]["Content-type"] == "application/json"
    assert json.loads(captured["data"].decode("utf-8")) == payload
    assert json.loads(latest_path.read_text(encoding="utf-8")) == payload


def test_send_payload_still_writes_latest_file_when_request_fails(tmp_path):
    def failing_urlopen(request, timeout):
        raise urllib.error.URLError("offline")

    payload = {"id": "station-a", "timestamp": 123, "key": "secret", "data": {}}
    latest_path = tmp_path / "latest_data.json"

    sent = send_payload(
        server="https://example.test/upload",
        payload=payload,
        latest_path=latest_path,
        opener=failing_urlopen,
    )

    assert sent is False
    assert json.loads(latest_path.read_text(encoding="utf-8")) == payload
