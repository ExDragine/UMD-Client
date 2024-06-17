import serial
import time

class SN3003FSXCSN01:
    def __init__(self) -> None:
        self.code = {
            "wind_speed":       [0x01, 0x03, 0x01, 0xF4, 0x00, 0x01, 0xC4, 0x04],
            "wind_scale":       [0x01, 0x03, 0x01, 0xF5, 0x00, 0x01, 0x95, 0xC4],
            "wind_direction":   [0x01, 0x03, 0x01, 0xF6, 0x00, 0x01, 0x65, 0xC4],
            "wind_angle":       [0x01, 0x03, 0x01, 0xF7, 0x00, 0x01, 0x34, 0x04],
            "T&h":              [0x01, 0x03, 0x01, 0xF8, 0x00, 0x02, 0x44, 0x06],
            "temperature":      [0x01, 0x03, 0x01, 0xF9, 0x00, 0x01, 0x55, 0xC7],
            "noise":            [0x01, 0x03, 0x01, 0xFA, 0x00, 0x01, 0xA5, 0xC7],
            "pm2dot5":          [0x01, 0x03, 0x01, 0xFB, 0x00, 0x01, 0xF4, 0x07],
            "pm10":             [0x01, 0x03, 0x01, 0xFC, 0x00, 0x01, 0x45, 0xC6],
            "pressure":         [0x01, 0x03, 0x01, 0xFD, 0x00, 0x01, 0x14, 0x06],
            "lux_high_hex":     [0x01, 0x03, 0x01, 0xFE, 0x00, 0x01, 0xE4, 0x06],
            "lux_low_hex":      [0x01, 0x03, 0x01, 0xFF, 0x00, 0x01, 0xB5, 0xC6],
            "lux":              [0x01, 0x03, 0x01, 0x00, 0x00, 0x01, 0x85, 0xF6],
            "rain":             [0x01, 0x03, 0x01, 0x01, 0x00, 0x01, 0xD4, 0x36],
            "compass":          [0x01, 0x03, 0x01, 0x02, 0x00, 0x01, 0x24, 0x34],
        }
        # 初始化端口与临时存储变量

        self.port = serial.Serial(
            "/dev/ttyS0", 4800, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, timeout=0.1
        )

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

