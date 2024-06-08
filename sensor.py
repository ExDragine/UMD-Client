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

# import requests

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler


pwd = "/home/exdragine/UMD-Client/data"
names = ["time", "temperature", "humidity", "wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
funcs = ["wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
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

# 初始化端口与临时存储变量
port = serial.Serial("/dev/ttyS0", 4800, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=0.1)
mem_data = deque(maxlen=60)  # 定义一个长度为60的双向列表, 临时存储每分钟的数据


# 定义轮询方法
def get_data(func) -> float:
    """轮询传感器数值并返回

    Args:
        func (string): 查询内容, 对应code变量中的16进制指令

    Returns:
        float: 返回浮点型的数值
    """
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


# 定义温度与湿度查询方法
def get_th() -> tuple[float, float]:
    """查询传感器湿度与温度

    Returns:
        tuple[float, float]: 返回传感器湿度与温度
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


def update_mem():
    """使用查询返回的值更新mem_data"""
    sensor_data = [0.0] * (len(funcs) + 3)
    sensor_data[0] = int(time.time())
    t, h = get_th()
    if t is not None and h is not None:
        sensor_data[1], sensor_data[2] = t, h
        time.sleep(0.01)
    for i, f in enumerate(funcs):
        data = get_data(f)
        if data is not None:
            sensor_data[i + 3] = data
        time.sleep(0.01)
    mem_data.append(sensor_data)


def main():
    """处理数据,存储数据"""
    now = datetime.datetime.now()
    year, month, day = str(now.year), str(now.month), str(now.day)
    timestamp = int(time.time())  # 秒级timestamp
    data_transposition = list(zip(*list(mem_data)))  # 将mem_data转置,每一行对应一个变量
    del data_transposition[0]  # 删除timestamp
    del data_transposition[-1]  # 使用最新读取的雨量数据替换平均后的雨量
    mean_result = [round(sum(map(float, obj)) / len(list(obj)), 2) for obj in data_transposition]  # 对每个分类的变量取平均值
    mean_result.append(mem_data[-1][-1]-mem_data[0][-1])
    mean_result.insert(0, timestamp)

    # everyday存储原始数据,latest_mean存储平均后的数据
    everyday = f"{pwd}/{year}/{month}/{day}.csv"
    latest_mean = f"{pwd}/latest_mean.csv"

    os.makedirs(f"{pwd}/{year}/{month}", exist_ok=True)

    if not os.path.exists(everyday):
        with open(everyday, "w", encoding='utf-8') as f:
            f.write(",".join(names) + "\n")
    if not os.path.exists(latest_mean):
        with open(latest_mean, "w", encoding='utf-8') as f:
            f.write(",".join(names) + "\n")

    with open(everyday, "a", encoding='utf-8') as f:
        for data in list(mem_data):
            f.write(",".join(map(str, data)) + "\n")

    with open(latest_mean, "r+", encoding='utf-8') as f:
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


# 入口
if __name__ == "__main__":
    sensor_scheduler = BackgroundScheduler()
    sensor_scheduler.add_job(update_mem, 'interval', seconds=1)
    sensor_scheduler.start()
    io_scheduler = BlockingScheduler()
    io_scheduler.add_job(main, 'interval', seconds=60)
    io_scheduler.start()
