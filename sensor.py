#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

from collections import deque
import time
import os
import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from interface import ICM20948  # Gyroscope/Acceleration/Magnetometer
from interface import BME280    # Atmospheric Pressure/Temperature and humidity
from interface import LTR390    # UV
from interface import TSL2591   # LIGHT
from interface import SGP40     # Gas
from interface import SN3003


class SensorHub:
    def __init__(self) -> None:
        self.pwd = "/home/exdragine/UMD-Client/data"
        self.names = ["time", "temperature", "humidity", "wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
        self.new_names = ["UVS","Lux","Gas"]
        self.funcs = ["wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
        self.mem_data = deque(maxlen=60)  # 定义一个长度为60的双向列表, 临时存储每分钟的数据
        self.icm20948 = ICM20948.ICM20948()
        self.bme280 = BME280.BME280()
        self.ltr390 = LTR390.LTR390()
        self.tsl2591 = TSL2591.TSL2591()
        self.sgp40 = SGP40.SGP40()
        self.sn3003 = SN3003.SN3003FSXCSN01()

    def update_mem(self):
        """使用查询返回的值更新mem_data"""
        sensor_data = [0.0] * (len(self.funcs) + 3)
        sensor_data[0] = int(time.time())
        t, h = self.sn3003.get_th()
        if t is not None and h is not None:
            sensor_data[1], sensor_data[2] = t, h
            time.sleep(0.01)
        for i, f in enumerate(self.funcs):
            data = self.sn3003.get_data(f)
            if data is not None:
                sensor_data[i + 3] = data
            time.sleep(0.01)
        self.mem_data.append(sensor_data)

    def local_storage(self):
        """处理数据,存储数据"""
        now = datetime.datetime.now()
        year, month, day = str(now.year), str(now.month), str(now.day)
        timestamp = int(time.time())  # 秒级timestamp
        data_transposition = list(zip(*list(self.mem_data)))  # 将mem_data转置,每一行对应一个变量
        del data_transposition[0]  # 删除timestamp
        del data_transposition[-1]  # 使用最新读取的雨量数据替换平均后的雨量
        mean_result = [round(sum(map(float, obj)) / len(list(obj)), 2) for obj in data_transposition]  # 对每个分类的变量取平均值
        mean_result.append(self.mem_data[-1][-1] - self.mem_data[0][-1])
        mean_result.insert(0, timestamp)

        # everyday存储原始数据,latest_mean存储平均后的数据
        everyday = f"{self.pwd}/{year}/{month}/{day}.csv"
        latest_mean = f"{self.pwd}/latest_mean.csv"

        os.makedirs(f"{self.pwd}/{year}/{month}", exist_ok=True)

        if not os.path.exists(everyday):
            with open(everyday, "w", encoding="utf-8") as f:
                f.write(",".join(self.names) + "\n")
        if not os.path.exists(latest_mean):
            with open(latest_mean, "w", encoding="utf-8") as f:
                f.write(",".join(self.names) + "\n")

        with open(everyday, "a", encoding="utf-8") as f:
            for data in list(self.mem_data):
                f.write(",".join(map(str, data)) + "\n")

        with open(latest_mean, "r+", encoding="utf-8") as f:
            f.seek(0)
            data = f.readlines()
            titles = [data[0]]
            if len(data) > 1441:
                data = titles + data[-1440:] + [",".join(map(str, mean_result)) + "\n"]
            else:
                data = data + [",".join(map(str, mean_result)) + "\n"]
            f.seek(0)
            f.truncate()
            f.writelines(data)


if __name__ == "__main__":
    sensor_pobe = SensorHub()
    bg_scheduler = BackgroundScheduler()
    bl_scheduler = BlockingScheduler()
    bg_scheduler.add_job(sensor_pobe.update_mem, "interval", seconds=1)
    bl_scheduler.add_job(sensor_pobe.local_storage, "interval", seconds=60)
    bg_scheduler.start()
    bl_scheduler.start()
