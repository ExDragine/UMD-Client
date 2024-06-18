#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

import os
from interface.ICM20948 import ICM20948  # Gyroscope/Acceleration/Magnetometer
from interface.BME280 import BME280  # Atmospheric Pressure/Temperature and humidity
from interface.LTR390 import LTR390  # UV
from interface.TSL2591 import TSL2591  # LIGHT
from interface.SGP40 import SGP40  # Gas


class OnBoardSensor:
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

    def _(self):
        bme = self.bme.readData()
        pressure = round(bme[0], 2)
        temp = round(bme[1], 2)
        hum = round(bme[2], 2)
        lux = round(self.light.Lux(), 2)
        UVS = self.uv.UVS()
        gas = round(self.sgp.raw(), 2)
        icm = self.icm.getdata()
        print("==================================================")
        print("pressure : %7.2f hPa" % pressure)
        print("temp : %-6.2f ℃" % temp)
        print("hum : %6.2f ％" % hum)
        print("lux : %d " % lux)
        print("uv : %d " % UVS)
        print("gas : %6.2f " % gas)
        print("Roll = %.2f , Pitch = %.2f , Yaw = %.2f" % (icm[0], icm[1], icm[2]))
        print("Acceleration: X = %d, Y = %d, Z = %d" % (icm[3], icm[4], icm[5]))
        print("Gyroscope:     X = %d , Y = %d , Z = %d" % (icm[6], icm[7], icm[8]))
        print("Magnetic:      X = %d , Y = %d , Z = %d" % (icm[9], icm[10], icm[11]))
        os.system("clear")
