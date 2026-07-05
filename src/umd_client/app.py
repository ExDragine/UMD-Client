import logging
import time
from pathlib import Path

from umd_client.config import ClientConfig, load_config
from umd_client.init_config import init
from umd_client.scheduler import ScheduledTask, due_tasks
from umd_client.sensors.factory import Sensor, create_sensor
from umd_client.sensors.types import Reading
from umd_client.transport import build_payload, send_payload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s:%(funcName)s] - %(levelname)s - %(message)s",
    datefmt="[%X]",
)
logger = logging.getLogger("umd_client")


def run(config_path: str | Path = ".env.toml") -> None:
    config_path = Path(config_path)
    if not config_path.exists():
        logger.info("Initializing")
        init(config_path)

    config = load_config(config_path)

    sensor = create_sensor(config)
    tasks = build_tasks(config)
    latest_reading = None
    logger.info("Starting scheduler with %s second collection interval", config.record_frequency)

    try:
        while True:
            latest_reading = run_due_tasks(config, sensor, tasks, latest_reading)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


def build_tasks(config: ClientConfig) -> list[ScheduledTask]:
    tasks = [ScheduledTask("upload", config.record_frequency)]
    if config.display_enabled:
        tasks.append(ScheduledTask("display", config.display_frequency))
    if config.camera_enabled:
        tasks.append(ScheduledTask("camera", config.camera_frequency))
    return tasks


def run_due_tasks(
    config: ClientConfig,
    sensor: Sensor,
    tasks: list[ScheduledTask],
    latest_reading: Reading | None = None,
    now: int | None = None,
) -> Reading | None:
    now = int(time.time()) if now is None else now
    for task in due_tasks(tasks, now):
        if task.name == "upload":
            latest_reading = collect_and_upload(config, sensor)
        elif task.name == "display" and latest_reading is not None:
            refresh_display(latest_reading, config)
        elif task.name == "camera":
            capture_camera(config)
        task.mark_run(now)
    return latest_reading


def collect_and_upload(config: ClientConfig, sensor: Sensor) -> Reading | None:
    try:
        reading = sensor.read()
        payload = build_payload(
            station_name=config.station_name,
            station_key=config.station_key,
            value_names=reading.value_names,
            values=reading.values,
        )
        send_payload(server=config.server, payload=payload)
        return reading
    except Exception:
        logger.exception("Error occurred while collecting or sending data")
        return None


def run_once(config: ClientConfig, sensor: Sensor) -> bool:
    return collect_and_upload(config, sensor) is not None


def refresh_display(reading: Reading, config: ClientConfig) -> None:
    try:
        from umd_client.display.epd2in13b_v4 import display_reading

        display_reading(reading, location=config.location)
    except Exception:
        logger.exception("Error occurred while refreshing display")


def capture_camera(config: ClientConfig) -> None:
    try:
        from umd_client.camera.ov5647 import capture_photo

        capture_photo(config.data_path, location=config.location)
    except Exception:
        logger.exception("Error occurred while capturing photo")
