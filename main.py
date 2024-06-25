#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

from collections import deque
import time
import os
import datetime
import json
import requests
import serial

from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler


# logging.basicConfig(
#     level=logging.WARNING, format="%(asctime)s - [%(name)s:%(funcName)s] - %(levelname)s - %(message)s", datefmt="[%X]", handlers=[RichHandler()]
# )
# logger = logging.getLogger("job")


load_dotenv()
name = os.getenv("station_name")
key = os.getenv("station_key")
server = os.getenv("server")
record_frequency = int(os.getenv("record_frequency", 30))
storage_size = int(os.getenv("storage_size", 2880))

if os.getenv("data_path"):
    path = os.getenv("data_path")
else:
    path = os.getcwd() + "/data"


class SN3003FSXCSN01:
    def __init__(self) -> None:
        self.code = {
            "wind_speed": [0x01, 0x03, 0x01, 0xF4, 0x00, 0x01, 0xC4, 0x04],
            "wind_scale": [0x01, 0x03, 0x01, 0xF5, 0x00, 0x01, 0x95, 0xC4],
            "wind_direction": [0x01, 0x03, 0x01, 0xF6, 0x00, 0x01, 0x65, 0xC4],
            "wind_angle": [0x01, 0x03, 0x01, 0xF7, 0x00, 0x01, 0x34, 0x04],
            "T&h": [0x01, 0x03, 0x01, 0xF8, 0x00, 0x02, 0x44, 0x06],
            # "temperature": [0x01, 0x03, 0x01, 0xF9, 0x00, 0x01, 0x55, 0xC7],
            "noise": [0x01, 0x03, 0x01, 0xFA, 0x00, 0x01, 0xA5, 0xC7],
            "pm2dot5": [0x01, 0x03, 0x01, 0xFB, 0x00, 0x01, 0xF4, 0x07],
            "pm10": [0x01, 0x03, 0x01, 0xFC, 0x00, 0x01, 0x45, 0xC6],
            "pressure": [0x01, 0x03, 0x01, 0xFD, 0x00, 0x01, 0x14, 0x06],
            # "lux_high_hex": [0x01, 0x03, 0x01, 0xFE, 0x00, 0x01, 0xE4, 0x06],
            # "lux_low_hex": [0x01, 0x03, 0x01, 0xFF, 0x00, 0x01, 0xB5, 0xC6],
            # "lux": [0x01, 0x03, 0x01, 0x00, 0x00, 0x01, 0x85, 0xF6],
            "rain": [0x01, 0x03, 0x01, 0x01, 0x00, 0x01, 0xD4, 0x36],
            # "compass": [0x01, 0x03, 0x01, 0x02, 0x00, 0x01, 0x24, 0x34],
        }
        # 初始化端口与临时存储变量

        self.port = serial.Serial("/dev/ttyS0", 4800, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=0.1)

    # 定义轮询方法
    def get_data(self, func) -> float:
        """轮询传感器数值并返回

        Args:
            func (string): 查询内容, 对应code变量中的16进制指令

        Returns:
            float: 返回浮点型的数值
        """
        self.port.write(bytes(self.code[func]))
        time.sleep(0.01)
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
        self.port.write(bytes(self.code["T&h"]))
        time.sleep(0.01)
        response = self.port.read(9)
        if len(response) == 9:
            h = int.from_bytes(response[3:5], byteorder="big") / 10
            t = int.from_bytes(response[5:7], byteorder="big") / 10
            return t, h
        else:
            return 0.0, 0.0


class DataTransfer:
    """传输数据"""

    def __init__(self, key, name) -> None:
        self.station_key = key
        self.station_name = name
        self.transmit_data = ""
        self.initial_check()

    def initial_check(self):
        """检查输入参数的合规性

        Raises:
            TypeError: 输入有毛病
            e: 文件不存在
        """
        checklist = {"key": self.station_key, "station_name": self.station_name}
        for name, obj in checklist.items():
            if obj == "" or not isinstance(obj, str):
                raise ValueError(f"{name} incorrect, please input your {name} or check again.")

    def transform_data(self, value_name, value):
        """发送数据"""
        # 创建字典
        data = dict(zip(value_name, value))
        p = {
            "id": self.station_name,  # 气象站的标识符
            "timestamp": int(time.time()),  # 确保 timestamp 是整数
            "key": self.station_key,
            "data": data,
        }
        # 添加三个空的占位符
        p["data"]["hold1"] = 0.0
        p["data"]["hold2"] = 0.0
        p["data"]["hold3"] = 0.0

        transmit_data = json.dumps(p, ensure_ascii=True, allow_nan=True, indent=4)
        return transmit_data

    def send_data(self, server, value_name, value):
        """Send data to UMD platform

        Raises:
            e: ERROR
        """
        data = self.transform_data(value_name, value)
        # 发送结果
        for i in range(3):
            try:
                if server:
                    post = requests.post(server, data, timeout=10)
                    match post.status_code:
                        case 200 | 201:
                            break
                        case 202:
                            time.sleep(5)
                            break
                        case _:
                            print(post.status_code)
                            pass
            except requests.exceptions.ConnectionError as e:
                if i < 2:
                    pass
                print(str(e))


class SensorHub:
    def __init__(self) -> None:
        self.pwd = path
        self.names = ["time", "temperature", "humidity", "wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
        self.new_names = ["UVS", "Lux", "Gas"]
        self.funcs = ["wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
        self.mem_data = deque(maxlen=record_frequency)  # 定义一个长度为保存频率的双向列表, 临时存储数据
        self.sn3003 = SN3003FSXCSN01()

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
        # year, month, day = str(now.year), str(now.month), str(now.day)
        year, month = str(now.year), str(now.month)
        timestamp = int(time.time())  # 秒级timestamp
        data_transposition = list(zip(*list(self.mem_data)))  # 将mem_data转置,每一行对应一个变量
        del data_transposition[0]  # 删除timestamp
        del data_transposition[-1]  # 使用最新读取的雨量数据替换平均后的雨量
        mean_result = [round(sum(map(float, obj)) / len(list(obj)), 2) for obj in data_transposition]  # 对每个分类的变量取平均值
        mean_result.append(self.mem_data[-1][-1] - self.mem_data[0][-1])
        mean_result.insert(0, timestamp)

        # everyday存储原始数据,latest_mean存储平均后的数据
        # everyday = f"{self.pwd}/{year}/{month}/{day}.csv"
        latest_mean = f"{self.pwd}/latest_mean.csv"

        # os.makedirs(f"{self.pwd}/{year}/{month}", exist_ok=True)

        # if not os.path.exists(everyday):
        #     with open(everyday, "w", encoding="utf-8") as f:
        #         f.write(",".join(self.names) + "\n")
        if not os.path.exists(latest_mean):
            with open(latest_mean, "w", encoding="utf-8") as f:
                f.write(",".join(self.names) + "\n")

        # with open(everyday, "a", encoding="utf-8") as f:
        #     for data in list(self.mem_data):
        #         f.write(",".join(map(str, data)) + "\n")

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
        transfer = DataTransfer(key, name)
        transfer.send_data(server, self.names, mean_result)


if __name__ == "__main__":
    sensor_pobe = SensorHub()
    background_scheduler = BackgroundScheduler()
    background_scheduler.add_job(sensor_pobe.update_mem, "interval", seconds=1)
    block_scheduler = BlockingScheduler()
    block_scheduler.add_job(sensor_pobe.local_storage, "interval", seconds=record_frequency)
    background_scheduler.start()
    block_scheduler.start()
