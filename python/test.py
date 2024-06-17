#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import ICM20948 #Gyroscope/Acceleration/Magnetometer
import BME280   #Atmospheric Pressure/Temperature and humidity
import LTR390   #UV
import TSL2591  #LIGHT
import SGP40
from PIL import Image,ImageDraw,ImageFont
import math


bme280 = BME280.BME280()
bme280.get_calib_param()
light = TSL2591.TSL2591()
uv = LTR390.LTR390()
sgp = SGP40.SGP40()
icm20948 = ICM20948.ICM20948()

print("TSL2591 Light I2C address:0X29")
print("LTR390 UV I2C address:0X53")
print("SGP40 VOC I2C address:0X59")
print("icm20948 9-DOF I2C address:0X68")
print("bme280 T&H I2C address:0X76")

try:
	while True:
		#time.sleep(1)
		bme = []
		bme = bme280.readData()
		pressure = round(bme[0], 2) 
		temp = round(bme[1], 2) 
		hum = round(bme[2], 2)
		
		lux = round(light.Lux(), 2)
		
		UVS = uv.UVS()
		
		gas = round(sgp.raw(), 2)
		
		icm = []
		icm = icm20948.getdata()
		
		print("==================================================")
		print("pressure : %7.2f hPa" %pressure)
		print("temp : %-6.2f ℃" %temp)
		print("hum : %6.2f ％" %hum)
		print("lux : %d " %lux)
		print("uv : %d " %UVS)
		print("gas : %6.2f " %gas)
		print("Roll = %.2f , Pitch = %.2f , Yaw = %.2f" %(icm[0],icm[1],icm[2]))
		print("Acceleration: X = %d, Y = %d, Z = %d" %(icm[3],icm[4],icm[5]))
		print("Gyroscope:     X = %d , Y = %d , Z = %d" %(icm[6],icm[7],icm[8]))
		print("Magnetic:      X = %d , Y = %d , Z = %d" %(icm[9],icm[10],icm[11]))


except KeyboardInterrupt:
	exit()	



