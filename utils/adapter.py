import time


def umd(data: dict):
    n = ["time", "temperature", "humidity", "wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"]
    p = {}
    for i, key in enumerate(n):
        if key == "time" and isinstance(data.get(key), int):
            p[n[i]] = data.get(key)
        else:
            p[n[i]] = data.get(key, None)
            if key == "time":
                p[n[i]] = int(time.time())

    return p
