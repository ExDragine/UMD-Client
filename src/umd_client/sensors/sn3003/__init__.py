import datetime
import os
import time
import tomllib
from collections import deque
from importlib import resources
from pathlib import Path
from typing import Any

from umd_client.sensors.types import Reading


class SN3003FSXCSN01:
    def __init__(
        self,
        port: str = "/dev/ttyS0",
        baudrate: int = 4800,
        config_path: str | Path | None = None,
    ) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("SN3003 support requires the pyserial package.") from exc

        if config_path is None:
            config_file = resources.files(__package__).joinpath("sn3003fsxcsn01.toml")
            with config_file.open("rb") as f:
                self.config = tomllib.load(f)
        else:
            with Path(config_path).open("rb") as f:
                self.config = tomllib.load(f)

        self.code: dict[str, Any] = self.config["SN3003FSXCSN01"]
        self.names = ["time"] + list(self.config["SN3003FSXCSN01"]["names"])
        self.funcs = ["wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
        self.mem_data = deque(maxlen=60)
        self.trans_data = 0.0

        self.port = serial.Serial(
            port,
            baudrate,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        )

    def get_data(self, func: str) -> float:
        """Poll one sensor value."""
        time.sleep(0.05)
        self.port.write(bytes(self.code[func]))
        time.sleep(0.05)
        self.port.flush()
        response = self.port.read(7)
        if len(response) != 7:
            return 0.0

        data = int.from_bytes(response[3:5], byteorder="big")
        match func:
            case "noise" | "rain":
                return float(data / 10)
            case "wind_speed" | "compass":
                return float(data / 100)
            case _:
                return float(data)

    def get_th(self) -> tuple[float, float]:
        """Poll humidity and temperature."""
        time.sleep(0.05)
        self.port.write(bytes(self.code["T&h"]))
        time.sleep(0.05)
        self.port.flush()
        response = self.port.read(9)
        if len(response) == 9:
            humidity = int.from_bytes(response[3:5], byteorder="big") / 10
            temperature = int.from_bytes(response[5:7], byteorder="big") / 10
            return temperature, humidity
        return 0.0, 0.0

    def update_mem(self) -> None:
        sensor_data = [0.0] * (len(self.funcs) + 3)
        sensor_data[0] = int(time.time())
        temperature, humidity = self.get_th()
        sensor_data[1], sensor_data[2] = temperature, humidity
        for index, func in enumerate(self.funcs):
            sensor_data[index + 3] = self.get_data(func)
        self.mem_data.append(sensor_data)

    def save(self, path: str | Path, storage_size: int) -> None:
        """Save raw readings and rolling mean CSV files."""
        now = datetime.datetime.now()
        year, month, day = str(now.year), str(now.month), str(now.day)
        timestamp = int(time.time())
        data_transposition = list(zip(*list(self.mem_data), strict=False))
        del data_transposition[0]
        del data_transposition[-1]
        mean_result = [round(sum(map(float, obj)) / len(list(obj)), 2) for obj in data_transposition]
        mean_result.append(self.mem_data[-1][-1] - self.mem_data[0][-1])
        mean_result.insert(0, timestamp)
        self.trans_data = mean_result

        base_path = Path(path)
        everyday = base_path / year / month / f"{day}.csv"
        latest_mean = base_path / "latest_mean.csv"

        os.makedirs(base_path / year / month, exist_ok=True)

        if not everyday.exists():
            everyday.write_text(",".join(self.names) + "\n", encoding="utf-8")
        if not latest_mean.exists():
            latest_mean.write_text(",".join(self.names) + "\n", encoding="utf-8")

        with everyday.open("a", encoding="utf-8") as f:
            for data in list(self.mem_data):
                f.write(",".join(map(str, data)) + "\n")

        with latest_mean.open("r+", encoding="utf-8") as f:
            f.seek(0)
            rows = f.readlines()
            titles = [rows[0]]
            if len(rows) > storage_size + 1:
                rows = titles + rows[-storage_size:] + [",".join(map(str, mean_result)) + "\n"]
            else:
                rows = rows + [",".join(map(str, mean_result)) + "\n"]
            f.seek(0)
            f.truncate()
            f.writelines(rows)


class SN3003Sensor:
    def __init__(self, port: str = "/dev/ttyS0") -> None:
        self.sensor = SN3003FSXCSN01(port=port)

    def read(self) -> Reading:
        self.sensor.update_mem()
        values = list(self.sensor.mem_data[-1])
        return Reading(timestamp=values[0], data=dict(zip(self.sensor.names, values, strict=False)))
