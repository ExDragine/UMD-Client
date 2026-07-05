from umd_client.camera.ov5647 import CaptureConfig, build_capture_command, prune_old_photos
from umd_client.config import LocationConfig


def test_build_capture_command_uses_daytime_exposure(tmp_path):
    output = tmp_path / "photo.jpg"
    location = LocationConfig(latitude=0.0, longitude=0.0, timezone="UTC")

    command = build_capture_command(output, location=location, timestamp=12 * 60 * 60)

    assert command == [
        "rpicam-still",
        "--nopreview",
        "--rotation",
        "180",
        "--metering",
        "centre",
        "--awb",
        "daylight",
        "-o",
        str(output),
    ]


def test_build_capture_command_uses_night_exposure(tmp_path):
    output = tmp_path / "photo.jpg"
    location = LocationConfig(latitude=0.0, longitude=0.0, timezone="UTC")

    command = build_capture_command(output, location=location, timestamp=0)

    assert "--shutter" in command
    assert "6000000" in command
    assert command[-2:] == ["-o", str(output)]


def test_prune_old_photos_keeps_newest_file(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_text("old", encoding="utf-8")
    second.write_text("new", encoding="utf-8")

    prune_old_photos(tmp_path, keep=1)

    assert not first.exists()
    assert second.exists()


def test_capture_config_uses_data_path_photo_directory(tmp_path):
    config = CaptureConfig(data_path=tmp_path)

    assert config.photo_dir == tmp_path / "photo"
