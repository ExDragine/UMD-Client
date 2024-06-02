#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

import serial
import time
import os
import datetime
from apscheduler.schedulers.background import BlockingScheduler

pwd = "/home/exdragine/UMD-Client/data"
names = ["time", "temperature", "humidity", "wind_speed", "wind_scale", "wind_direction", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
funcs = ["wind_speed", "wind_scale", "wind_direction", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
code = {
    "wind_speed":       [0x01,0x03,0x01,0xF4,0x00,0x01,0xC4,0x04],
    "wind_scale":       [0x01,0x03,0x01,0xF5,0x00,0x01,0x95,0xC4],
    "wind_direction":   [0x01,0x03,0x01,0xF6,0x00,0x01,0x65,0xC4],
    "wind_angle":       [0x01,0x03,0x01,0xF7,0x00,0x01,0x34,0x04],
    "T&h":              [0x01,0x03,0x01,0xF8,0x00,0x02,0x44,0x06],
    "temperature":      [0x01,0x03,0x01,0xF9,0x00,0x01,0x55,0xC7],
    "noise":            [0x01,0x03,0x01,0xFA,0x00,0x01,0xA5,0xC7],
    "pm2dot5":          [0x01,0x03,0x01,0xFB,0x00,0x01,0xF4,0x07],
    "pm10":             [0x01,0x03,0x01,0xFC,0x00,0x01,0x45,0xC6],
    "pressure":         [0x01,0x03,0x01,0xFD,0x00,0x01,0x14,0x06],
    "lux_high_hex":     [0x01,0x03,0x01,0xFE,0x00,0x01,0xE4,0x06],
    "lux_low_hex":      [0x01,0x03,0x01,0xFF,0x00,0x01,0xB5,0xC6],
    "lux":              [0x01,0x03,0x01,0x00,0x00,0x01,0x85,0xF6],
    "rain":             [0x01,0x03,0x01,0x01,0x00,0x01,0xD4,0x36],
    "compass":          [0x01,0x03,0x01,0x02,0x00,0x01,0x24,0x34]
}

class AirSerial():
    def __init__(self):
        self.port = serial.Serial("/dev/ttyS0", 4800, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=0.1)

    def get_data(self, func):
        self.port.write(bytes(code[func]))
        time.sleep(0.01)
        response = self.port.read(7)
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
            return None

    def get_RHaT(self):
        self.port.write(bytes(code["T&h"]))
        time.sleep(0.01)
        response = self.port.read(9)
        if len(response) == 9:
            rh = int.from_bytes(response[3:5], byteorder='big') / 10
            temp = int.from_bytes(response[5:7], byteorder='big') / 10
            return rh, temp
        else:
            return None, None

def main():
    airserial = AirSerial()
    now = datetime.datetime.now()
    year, month, day = str(now.year), str(now.month), str(now.day)

    os.makedirs(f"{pwd}/{year}/{month}", exist_ok=True)

    if not os.path.exists(f"{pwd}/{year}/{month}/{day}.csv"):
        with open(f"{pwd}/{year}/{month}/{day}.csv", "w") as f:
            f.write(",".join(names) + "\n")

    if not os.path.exists(f"{pwd}/latest_3h.csv"):
        with open(f"{pwd}/latest_1d.csv", "w") as f:
            f.write(",".join(names) + "\n")

    number = [0.0] * len(funcs)
    timestamp = int(time.time())
    for i in range(len(funcs)):
        result = airserial.get_data(funcs[i])
        if result is not None:
            number[i] = result
        time.sleep(0.01)

    rh, t = airserial.get_RHaT()
    if rh is not None and t is not None:
        with open(f"{pwd}/{year}/{month}/{day}.csv", "a") as f:
            f.write(f"{timestamp},{t},{rh},{','.join([str(x) for x in number])}\n")

        with open(f"{pwd}/latest_3h.csv", "r+") as f:
            f.seek(0)
            data = f.readlines()
            titles = data[0]
            if len(data) > 10801:
                data = data[-10800:]
                data = [titles] + data + [f"{timestamp},{t},{rh},{','.join([str(x) for x in number])}\n"]
            else:
                data = data + [f"{timestamp},{t},{rh},{','.join([str(x) for x in number])}\n"]
            f.seek(0)
            f.truncate()
            f.writelines(data)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'interval', seconds=1)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
