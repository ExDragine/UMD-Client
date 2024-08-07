import time
import math

from modules.sensor_hat.ICM20948 import ICM20948  # Gyroscope/Acceleration/Magnetometer
from modules.sensor_hat.BME280 import BME280  # Atmospheric Pressure/Temperature and humidity
from modules.sensor_hat.LTR390 import LTR390  # UV
from modules.sensor_hat.TSL2591 import TSL2591  # LIGHT
from modules.sensor_hat.SGP40 import SGP40  # Gas


class Sensor_HAT:
    def __init__(self) -> None:
        self.icm = ICM20948()
        self.bme = BME280()
        self.bme.get_calib_param()
        self.uv = LTR390()
        self.light = TSL2591()
        self.sgp = SGP40()

    def information(self):
        print("TSL2591 Light I2C address:0X29")
        print("LTR390 UV I2C address:0X53")
        print("SGP40 VOC I2C address:0X59")
        print("icm20948 9-DOF I2C address:0X68")
        print("bme280 T&H I2C address:0X76")

    def read(self):
        bme = self.bme.readData()
        icm = self.icm.getdata()
        bme = self.bme.readData()
        icm = self.icm.getdata()
        self.pressure = round(bme[0], 2)
        self.temp = round(bme[1], 2)
        self.hum = round(bme[2], 2)
        self.lux = round(self.light.Lux(), 2)
        self.uvs = self.uv.UVS()
        self.gas = round(self.sgp.measureRaw(int(self.temp), int(self.hum)), 2)
        self.roll, self.pitch, self.yaw = round(icm[0], 2), round(icm[1], 2), round(icm[2], 2)
        self.acceleration = (round(icm[3]), round(icm[4]), round(icm[5]))
        self.gyroscope = (round(icm[6]), round(icm[7]), round(icm[8]))
        self.magnetic = (round(icm[9]), round(icm[10]), round(icm[11]))
        data = (
            [self.temp, self.hum, self.pressure, self.lux, self.uvs, self.gas, self.roll, self.pitch, self.yaw]
            + list(self.acceleration)
            + list(self.gyroscope)
            + list(self.magnetic)
        )
        return data

    def packed_data(self):
        data = {
            "time": int(time.time()),
            "temperature": self.temp,
            "humidity": self.hum,
            "pressure": self.pressure,
            "lux": self.lux,
            "uv": self.uvs,
            "shake":math.sqrt(pow(self.gyroscope[0],2)+pow(self.gyroscope[1],2)+pow(self.gyroscope[2],2))
        }
        return data
