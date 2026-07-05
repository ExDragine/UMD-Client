from typing import Protocol

from umd_client.config import ClientConfig
from umd_client.sensors.types import Reading


class Sensor(Protocol):
    def read(self) -> Reading:
        ...


def create_sensor(config: ClientConfig) -> Sensor:
    if config.sensor_type == "sensor_hat":
        from umd_client.sensors.sensor_hat import SensorHatSensor

        return SensorHatSensor()
    if config.sensor_type == "sn3003":
        from umd_client.sensors.sn3003 import SN3003Sensor

        return SN3003Sensor(port=config.sn3003_port)
    raise ValueError(f"Unsupported sensor_type: {config.sensor_type}")
