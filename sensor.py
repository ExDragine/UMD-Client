#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/
from collections import deque
import time
import os
import datetime
import serial

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

pwd = "/home/exdragine/UMD-Client/data"
names = [
    "time",
    "temperature",
    "humidity",
    "wind_speed",
    "wind_scale",
    "wind_direction",
    "wind_angle",
    "noise",
    "pm2dot5",
    "pm10",
    "pressure",
    "rain",
]
funcs = ["wind_speed", "wind_scale", "wind_direction", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
code = {
    "wind_speed": [0x01, 0x03, 0x01, 0xF4, 0x00, 0x01, 0xC4, 0x04],
    "wind_scale": [0x01, 0x03, 0x01, 0xF5, 0x00, 0x01, 0x95, 0xC4],
    "wind_direction": [0x01, 0x03, 0x01, 0xF6, 0x00, 0x01, 0x65, 0xC4],
    "wind_angle": [0x01, 0x03, 0x01, 0xF7, 0x00, 0x01, 0x34, 0x04],
    "T&h": [0x01, 0x03, 0x01, 0xF8, 0x00, 0x02, 0x44, 0x06],
    "temperature": [0x01, 0x03, 0x01, 0xF9, 0x00, 0x01, 0x55, 0xC7],
    "noise": [0x01, 0x03, 0x01, 0xFA, 0x00, 0x01, 0xA5, 0xC7],
    "pm2dot5": [0x01, 0x03, 0x01, 0xFB, 0x00, 0x01, 0xF4, 0x07],
    "pm10": [0x01, 0x03, 0x01, 0xFC, 0x00, 0x01, 0x45, 0xC6],
    "pressure": [0x01, 0x03, 0x01, 0xFD, 0x00, 0x01, 0x14, 0x06],
    "lux_high_hex": [0x01, 0x03, 0x01, 0xFE, 0x00, 0x01, 0xE4, 0x06],
    "lux_low_hex": [0x01, 0x03, 0x01, 0xFF, 0x00, 0x01, 0xB5, 0xC6],
    "lux": [0x01, 0x03, 0x01, 0x00, 0x00, 0x01, 0x85, 0xF6],
    "rain": [0x01, 0x03, 0x01, 0x01, 0x00, 0x01, 0xD4, 0x36],
    "compass": [0x01, 0x03, 0x01, 0x02, 0x00, 0x01, 0x24, 0x34],
}

port = serial.Serial("/dev/ttyS0", 4800, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=0.1)
mem_data = deque(maxlen=60)


def get_data(func) -> float:
    port.write(bytes(code[func]))
    time.sleep(0.01)
    response = port.read(7)
    if len(response) == 7:
        data = int.from_bytes(response[3:5], byteorder='big')
        match func:
            case "noise" | "rain":
                return float(data / 10)
            case "wind_speed" | "compass":
                return float(data / 100)
            case _:
                return float(data)
    else:
        return 0.0


def get_th() -> tuple[float, float]:
    """Get Temperature and Humidity

    Returns:
        tuple[float, float]: _description_
    """
    port.write(bytes(code["T&h"]))
    time.sleep(0.01)
    response = port.read(9)
    if len(response) == 9:
        h = int.from_bytes(response[3:5], byteorder='big') / 10
        t = int.from_bytes(response[5:7], byteorder='big') / 10
        return t, h
    else:
        return 0.0, 0.0


def get_rain() -> float:
    port.write(bytes(code["rain"]))
    time.sleep(0.01)
    response = port.read(7)
    if len(response) == 7:
        r = int.from_bytes(response[3:5], byteorder='big') / 10
        return r
    else:
        return 0.0


def update_mem():
    sensor_data = [0.0] * (len(funcs) + 3)
    sensor_data[0] = int(time.time())
    t, h = get_th()
    if t is not None and h is not None:
        sensor_data[1], sensor_data[2] = t, h
        time.sleep(0.01)
    for i in range(len(funcs)):
        data = get_data(funcs[i])
        if data is not None:
            sensor_data[i + 3] = data
        time.sleep(0.01)
    mem_data.append(sensor_data)


def main():
    now = datetime.datetime.now()
    year, month, day = str(now.year), str(now.month), str(now.day)
    timestamp = int(time.time())
    mem_data_T = list(zip(*list(mem_data)))
    del mem_data_T[0]
    max_result = [max(map(float, obj)) for obj in mem_data_T]
    mean_result = [sum(map(float, obj)) / len(obj) for obj in mem_data_T]
    sensor_rain = get_rain()
    max_result[-1] = sensor_rain
    mean_result[-1] = sensor_rain
    max_result.insert(0, timestamp)
    mean_result.insert(0, timestamp)

    everyday = f"{pwd}/{year}/{month}/{day}.csv"
    latest_max = f"{pwd}/latest_max.csv"
    latest_mean = f"{pwd}/latest_mean.csv"

    os.makedirs(f"{pwd}/{year}/{month}", exist_ok=True)

    if not os.path.exists(everyday):
        with open(everyday, "w", encoding='utf-8') as f:
            f.write(",".join(names) + "\n")
    if not os.path.exists(latest_max):
        with open(latest_max, "w", encoding='utf-8') as f:
            f.write(",".join(names) + "\n")
    if not os.path.exists(latest_mean):
        with open(latest_mean, "w", encoding='utf-8') as f:
            f.write(",".join(names) + "\n")

    with open(everyday, "a", encoding='utf-8') as f:
        for data in list(mem_data):
            f.write(",".join(map(str, data)) + "\n")

    with open(latest_max, "r+", encoding='utf-8') as f:
        f.seek(0)
        data = f.readlines()
        titles = [data[0]]
        if len(data) > 4321:
            data = titles + data[-4320:] + [",".join(map(str, max_result)) + "\n"]
        else:
            data = data + [",".join(map(str, max_result)) + "\n"]
        f.seek(0)
        f.truncate()
        f.writelines(data)
    with open(latest_mean, "r+", encoding='utf-8') as f:
        f.seek(0)
        data = f.readlines()
        titles = [data[0]]
        if len(data) > 4321:
            data = titles + data[-4320:] + [",".join(map(str, mean_result)) + "\n"]
        else:
            data = data + [",".join(map(str, mean_result)) + "\n"]
        f.seek(0)
        f.truncate()
        f.writelines(data)


if __name__ == "__main__":
    sensor_scheduler = BackgroundScheduler()
    sensor_scheduler.add_job(update_mem, 'interval', seconds=1)
    sensor_scheduler.start()
    io_scheduler = BlockingScheduler()
    io_scheduler.add_job(main, 'interval', seconds=60)
    io_scheduler.start()
