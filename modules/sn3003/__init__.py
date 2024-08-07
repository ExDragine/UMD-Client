import os
import serial
import tomllib
import time
import datetime
from collections import deque


class SN3003FSXCSN01:
    def __init__(self) -> None:
        if not os.path.exists("./modules/sn3003/sn3003fsxcsn01.toml"):
            print("亲，你没有传感器配置文件呢")
            exit(2)
        with open(f"{os.getcwd()}/modules/sn3003/sn3003fsxcsn01.toml", "rb") as f:
            self.config = tomllib.load(f)
        self.code = self.config["SN3003FSXCSN01"]
        # 初始化端口与临时存储变量
        self.names = ["time"] + list(self.config["SN3003FSXCSN01"]["names"])
        self.funcs = ["wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
        self.mem_data = deque(maxlen=60)  # 定义一个长度为保存频率的双向列表, 临时存储数据
        self.trans_data = 0.0

        self.port = serial.Serial(
            "/dev/ttyS0",
            4800,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        )

    # 定义轮询方法
    def get_data(self, func) -> float:
        """轮询传感器数值并返回

        Args:
            func (string): 查询内容, 对应code变量中的16进制指令

        Returns:
            float: 返回浮点型的数值
        """
        time.sleep(0.05)
        self.port.write(bytes(self.code[func]))
        time.sleep(0.05)
        self.port.flush()
        response = self.port.read(7)
        if len(response) == 7:
            data = int.from_bytes(response[3:5], byteorder="big")
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
    def get_th(self) -> tuple[float, float]:
        """查询传感器湿度与温度

        Returns:
            tuple[float, float]: 返回传感器湿度与温度
        """
        time.sleep(0.05)
        self.port.write(bytes(self.code["T&h"]))
        time.sleep(0.05)
        self.port.flush()
        response = self.port.read(9)
        if len(response) == 9:
            h = int.from_bytes(response[3:5], byteorder="big") / 10
            t = int.from_bytes(response[5:7], byteorder="big") / 10
            return t, h
        else:
            return 0.0, 0.0

    def update_mem(self):
        """使用查询返回的值更新mem_data"""
        sensor_data = [0.0] * (len(self.funcs) + 3)
        sensor_data[0] = int(time.time())
        t, h = self.get_th()
        if t is not None and h is not None:
            sensor_data[1], sensor_data[2] = t, h
        for i, f in enumerate(self.funcs):
            data = self.get_data(f)
            if data is not None:
                sensor_data[i + 3] = data
        self.mem_data.append(sensor_data)

    def save(self, path, storage_size):
        """处理数据,存储数据"""
        now = datetime.datetime.now()
        year, month, day = str(now.year), str(now.month), str(now.day)
        timestamp = int(time.time())  # 秒级timestamp
        data_transposition = list(zip(*list(self.mem_data)))  # 将mem_data转置,每一行对应一个变量
        del data_transposition[0]  # 删除timestamp
        del data_transposition[-1]  # 使用最新读取的雨量数据替换平均后的雨量
        mean_result = [
            round(sum(map(float, obj)) / len(list(obj)), 2) for obj in data_transposition
        ]  # 对每个分类的变量取平均值
        mean_result.append(self.mem_data[-1][-1] - self.mem_data[0][-1])
        mean_result.insert(0, timestamp)
        self.trans_data = mean_result

        # everyday存储原始数据,latest_mean存储平均后的数据
        everyday = f"{path}/{year}/{month}/{day}.csv"
        latest_mean = f"{path}/latest_mean.csv"

        os.makedirs(f"{path}/{year}/{month}", exist_ok=True)

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
            if len(data) > storage_size + 1:
                data = titles + data[-storage_size:] + [",".join(map(str, mean_result)) + "\n"]
            else:
                data = data + [",".join(map(str, mean_result)) + "\n"]
            f.seek(0)
            f.truncate()
            f.writelines(data)
