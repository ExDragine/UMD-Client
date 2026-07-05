from pathlib import Path

import pytest

from umd_client.config import ConfigError, load_config


def test_load_config_applies_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".env.toml"
    config_path.write_text(
        "\n".join(
            [
                "station_name = 'station-a'",
                "station_key = 'secret'",
                "server = 'https://example.test/upload'",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.station_name == "station-a"
    assert config.station_key == "secret"
    assert config.server == "https://example.test/upload"
    assert config.record_frequency == 30
    assert config.storage_size == 2880
    assert config.data_path == Path(tmp_path / "data")
    assert config.sensor_type == "sensor_hat"
    assert config.sn3003_port == "/dev/ttyS0"
    assert config.display_enabled is False
    assert config.display_frequency == 300
    assert config.camera_enabled is False
    assert config.camera_frequency == 1800
    assert config.location.city == "Guangzhou"
    assert config.location.country == "China"
    assert config.location.timezone == "Asia/Harbin"
    assert config.location.latitude == 23.109866
    assert config.location.longitude == 113.2683


def test_load_config_rejects_missing_required_fields(tmp_path):
    config_path = tmp_path / ".env.toml"
    config_path.write_text("station_name = 'station-a'\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="station_key"):
        load_config(config_path)
