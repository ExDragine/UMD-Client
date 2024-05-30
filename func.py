import serial
import time
import os
import datetime

class AirSerial():
    def __init__(self):
        self.code = {
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
        self.port = serial.Serial("/dev/ttyS0", 4800, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=0.1)
        if self.port.is_open:
            print("欢迎使用李华广州气象站")

    def get_data(self, func):
        self.port.write(bytes(self.code[func]))
        time.sleep(0.01)
        address = self.port.read(1)
        func_code = self.port.read(1)
        data_length = self.port.read(1)
        hex_data = self.port.read(2)
        crc_l = self.port.read(1)
        crc_h = self.port.read(1)
        data = int.from_bytes(hex_data, byteorder='big')
        match func:
            case "noise" | "rain" | "pressure":
                return float(data / 10)
            case "wind_speed" | "compass":
                return float(data / 100)
            case _:
                return float(data)

    def get_RHaT(self):
        self.port.write(bytes(self.code["T&h"]))
        time.sleep(0.1)
        address = self.port.read(1)
        func_code = self.port.read(1)
        data_length = self.port.read(1)
        h_rh = self.port.read(2)
        h_temp = self.port.read(2)
        crc_l = self.port.read(1)
        crc_h = self.port.read(1)
        rh = int.from_bytes(h_rh, byteorder='big') / 10
        temp = int.from_bytes(h_temp, byteorder='big') / 10
        return rh, temp

def get_data():
    airserial = AirSerial()
    pwd = "/home/exdragine/UMD/data"

    now = datetime.datetime.now()
    year,month,day = str(now.year),str(now.month),str(now.day)

    os.mkdir(pwd) if not os.path.exists(pwd) else None
    os.mkdir(f"{pwd}/{year}") if not os.path.exists(f"{pwd}/{year}") else None
    os.mkdir(f"{pwd}/{year}/{month}") if not os.path.exists(f"{pwd}/{year}/{month}") else None


    ls = ["time", "temperature", "humidity", "wind_speed", "wind_scale", "wind_direction", "wind_angle", "noise", "pm2dot5", "pm10", "pressure","rain"]
    if not os.path.exists(f"{pwd}/{year}/{month}/{day}.csv"):
        with open(f"{pwd}/{year}/{month}/{day}.csv", "w") as f:
            f.write(",".join(ls) + "\n")
    ls = ["wind_speed", "wind_scale", "wind_direction", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
    number = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    now = str(time.time())[:10]
    for i in range(len(ls)):
        number[i] = airserial.get_data(ls[i])
        time.sleep(0.01)

    rh, t = airserial.get_RHaT()

    with open(f"{pwd}/{year}/{month}/{day}.csv", "a") as f:
        f.write(f"{now},{t},{rh},{','.join([str(x) for x in number])}\n")

if __name__ == "__main__":
    while True:
        get_data()