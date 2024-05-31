#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

#   _______     _
#  |_  / _ \   /_\
#   / / (_) | / _ \
#  /___\__\_\/_/ \_\

import os
import datetime
import enum
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

app = FastAPI()

pwd = "/home/exdragine/UMD-Client"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def read_data():
    df = pd.read_csv(f"{pwd}/data/latest_1d.csv")
    df['time'] = pd.to_datetime(df['time'], unit='s', origin="1970-01-01 08:00:00")  # Assuming time is in Unix timestamp format
    return df


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/status")
async def api():
    df = pd.read_csv(f"{pwd}/data/latest_1d.csv")
    response = {
        "time": str(df["time"].iloc[-1]),
        "temperature": float(df["temperature"].iloc[-1]),
        "humidity": float(df["humidity"].iloc[-1]),
        "wind_speed": float(df["wind_speed"].iloc[-1]),
        "wind_scale": float(df["wind_scale"].iloc[-1]),
        "wind_direction": float(df["wind_direction"].iloc[-1]),
        "wind_angle": float(df["wind_angle"].iloc[-1]),
        "noise": float(df["noise"].iloc[-1]),
        "pm2.5": float(df["pm2dot5"].iloc[-1]),
        "pm10": float(df["pm10"].iloc[-1]),
        "pressure": float(df["pressure"].iloc[-1]),
        "rain": float(df["rain"].iloc[-1]),
    }
    return response


@app.get("/api/download")
async def download(year=0, month=0, day=0):
    if year == 0 or month == 0 or day == 0:
        return FileResponse(f"{pwd}/data/latest_1d.csv")
    if year and month and day:
        try:
            datetime.datetime(year, month, day)
            return FileResponse(f"{pwd}/data/{str(year)}/{str(month)}/{str(day)}.csv")
        except:
            return "format illeged"


class types(enum.Enum):
    temperature = "temperature"
    humidity = "humidity"
    wind_speed = "wind_speed"
    wind_angle = "wind_angle"
    noise = "noise"
    pm2dot5 = "pm2dot5"
    pm10 = "pm10"
    pressure = "pressure"
    rain = "rain"


@app.post("/api/charts")
async def get_charts(type: types):
    df = read_data()
    df['time'] = df['time'].astype(str)  # 将Timestamp类型转换为字符串
    response = {}
    response["time"] = df["time"].to_list()
    response[type.name] = df[type.name].to_list()
    return response


@app.get("/update")
async def update():
    try:
        os.system(f"bash {pwd}/update.sh")
        return "finish"
    except:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)
