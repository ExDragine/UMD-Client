#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

import os
import json
import time
import requests
import pandas as pd
import logging

from rich.logging import RichHandler


FORMAT = "%(asctime)s - [%(name)s:%(funcName)s] - %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger("sensor")


class DataTransfer:
    """传输数据"""

    def __init__(self) -> None:
        self.key = "2wmfz09l8rhe"
        self.station_name = "9dpu2k5x1zco"
        self.sensor_data = "/home/exdragine/UMD-Client/data/latest_mean.csv"
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

    def transform_data(self):
        """发送数据"""
        data = None
        try:
            _, ext = os.path.splitext(self.sensor_data)
            if ext == ".csv":
                data = pd.read_csv(self.sensor_data).tail(1).to_dict(orient="records")[0]
        except FileExistsError as e:
            print(str(e))
        # 创建字典
        if isinstance(data, dict):
            p = {
                "id": self.station_name,  # 气象站的标识符
                "timestamp": int(time.time()),  # 确保 timestamp 是整数
                "key": self.key,
                "data": data,
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
        self.transform_data()
        # 发送结果
        for i in range(3):
            try:
                post = requests.post("http://39.105.29.158:8088/api/api/sync", data=self.transmit_data, timeout=10)
                match post.status_code:
                    case 200 | 201:
                        logger.info("数据传输成功")
                        break
                    case 202:
                        time.sleep(5)
                        break
                    case _:
                        logger.warning("貌似出了点问题")
                        pass
            except requests.exceptions.ConnectionError as e:
                if i < 2:
                    pass
                else:
                    logger.error(e)


# if __name__ == "__main__":
#     transfer = DataTransfer()
#     scheduler = BlockingScheduler()
#     scheduler.add_job(transfer.send_data, "interval", seconds=30)
#     scheduler.start()
