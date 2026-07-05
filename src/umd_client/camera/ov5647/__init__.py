import datetime
import subprocess
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from umd_client.config import LocationConfig


@dataclass(frozen=True)
class CaptureConfig:
    data_path: Path

    @property
    def photo_dir(self) -> Path:
        return self.data_path / "photo"


def build_capture_command(
    output_path: str | Path,
    location: LocationConfig,
    timestamp: int | None = None,
) -> list[str]:
    output_path = Path(output_path)
    base_command = [
        "rpicam-still",
        "--nopreview",
        "--rotation",
        "180",
        "--metering",
        "centre",
        "--awb",
        "daylight",
    ]
    if _is_night(location, timestamp):
        base_command.extend(["--shutter", "6000000", "--ev", "0.5"])
    base_command.extend(["-o", str(output_path)])
    return base_command


def capture_photo(
    data_path: str | Path,
    location: LocationConfig,
    timestamp: int | None = None,
    runner=subprocess.run,
) -> Path:
    config = CaptureConfig(data_path=Path(data_path))
    config.photo_dir.mkdir(parents=True, exist_ok=True)
    now = _datetime_from_timestamp(timestamp, location)
    output_path = config.photo_dir / f"{now.strftime('%H-%M-%S')}.jpg"
    runner(build_capture_command(output_path, location=location, timestamp=timestamp), check=True)
    prune_old_photos(config.photo_dir, keep=1)
    return output_path


def prune_old_photos(photo_dir: str | Path, keep: int = 1) -> None:
    files = [path for path in Path(photo_dir).iterdir() if path.is_file()]
    files.sort(key=lambda path: (path.stat().st_mtime, path.name))
    for old_file in files[:-keep]:
        old_file.unlink()


def photo() -> Path:
    return capture_photo(Path("./data"), LocationConfig())


def _is_night(location: LocationConfig, timestamp: int | None) -> bool:
    from astral import LocationInfo
    from astral.sun import sun

    now = _datetime_from_timestamp(timestamp, location)
    city = LocationInfo(location.city, location.country, location.timezone, location.latitude, location.longitude)
    sun_info = sun(city.observer, date=now.date(), tzinfo=city.timezone)
    sunrise = int((sun_info["sunrise"] + datetime.timedelta(minutes=-20)).timestamp())
    sunset = int((sun_info["sunset"] + datetime.timedelta(minutes=20)).timestamp())
    current = int(now.timestamp())
    return current > sunset or current < sunrise


def _datetime_from_timestamp(timestamp: int | None, location: LocationConfig) -> datetime.datetime:
    timezone = ZoneInfo(location.timezone)
    if timestamp is None:
        return datetime.datetime.now(timezone)
    return datetime.datetime.fromtimestamp(timestamp, timezone)
