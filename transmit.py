import os
import json
import time
import uuid
import requests
import pandas as pd


class Transmit:
    """传输数据"""

    def __init__(self) -> None:
        self.key = "114514"
        self.station_name = "lihua"
        self.sensor_data = r"D:\UMD-Client\data\latest_mean.csv"
        self.transmit_data = ""
        self.initial_check()

    def initial_check(self):
        """检查输入参数的合规性

        Raises:
            TypeError: 输入有毛病
            e: 文件不存在
        """
        checklist = {"key": self.key, "station_name": self.station_name}
        for name, obj in checklist.items():
            if obj == "" or not isinstance(obj, str):
                raise TypeError(f"{name} incorrect, please input your {name} or check again.")
        try:
            _, ext = os.path.splitext(self.sensor_data)
            if ext == ".csv":
                self.data = pd.read_csv(self.sensor_data).tail(1).to_dict(orient="records")[0]
        except FileExistsError as e:
            raise e

    def transform_data(self):
        """发送数据"""

        # 创建字典
        if isinstance(self.data, dict):
            p = {
                "id": str(uuid.uuid5(namespace=uuid.NAMESPACE_DNS, name=self.station_name)),  # 气象站的标识符
                "timestamp": int(time.time()),  # 确保 timestamp 是整数
                "key": self.key,
                "data": self.data,
            }
            # 添加三个空的占位符
            p["data"]["hold1"] = 0.0
            p["data"]["hold2"] = 0.0
            p["data"]["hold3"] = 0.0

            self.transmit_data = json.dumps(p, ensure_ascii=True, allow_nan=True, indent=4)

    def send_data(self):
        """Send data to UMD platform

        Raises:
            e: ERROR
        """
        # 发送结果
        for i in range(3):
            try:
                post = requests.post("http://39.105.29.158:8088/api/api/sync", data=self.transmit_data, timeout=5)
                print(post.status_code)
                match post.status_code:
                    case 200 | 201:
                        break
                    case 202:
                        time.sleep(5)
                        break
                    case _:
                        pass
            except requests.exceptions.ConnectionError as e:
                if i < 2:
                    pass
                else:
                    raise e


while True:
    t = Transmit()
    t.transform_data()
    t.send_data()
    time.sleep(30)