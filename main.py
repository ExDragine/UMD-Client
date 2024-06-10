#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

import os
import datetime
import enum
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from apscheduler.schedulers.background import BackgroundScheduler

from sensor import update_mem, main
from transmit import Transmit

app = FastAPI()
t = Transmit()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd = "/home/exdragine/UMD-Client"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/status")
async def api():
    response = (
        pd.read_csv(f"{pwd}/data/latest_mean.csv").tail(1).to_dict(orient="records")[0]
    )
    return response


@app.get("/api/download")
async def download(value="mean", year=0, month=0, day=0):
    if year == 0 or month == 0 or day == 0:
        try:
            return FileResponse(f"{pwd}/data/latest_{value}.csv")
        except FileNotFoundError as e:
            return "Unable to get value.\n" + str(e)
    if year and month and day:
        try:
            datetime.datetime(year, month, day)
            return FileResponse(f"{pwd}/data/{str(year)}/{str(month)}/{str(day)}.csv")
        except FileNotFoundError as e:
            return "format illeged\n" + str(object=e)


class types(enum.Enum):
    temperature = "temperature"
    humidity = "humidity"
    wind_speed = "wind_speed"
    wind_scale = "wind_scale"
    wind_direction = "wind_direction"
    wind_angle = "wind_angle"
    noise = "noise"
    pm2dot5 = "pm2dot5"
    pm10 = "pm10"
    pressure = "pressure"
    rain = "rain"


@app.get("/api/charts")
async def get_charts(type: types):
    df = pd.read_csv(f"{pwd}/data/latest_mean.csv")
    # Assuming time is in Unix timestamp format
    df["time"] = pd.to_datetime(df["time"], unit="s", origin="1970-01-01 08:00:00")
    df["time"] = df["time"].astype(str)  # 将Timestamp类型转换为字符串
    response = {}
    response["time"] = df["time"].to_list()
    if type.value == "wind_scale" or type.value == "wind_direction":
        response[type.name] = df[type.name].round(0).to_list()
    else:
        response[type.name] = df[type.name].to_list()
    return response


@app.get("/update")
async def update():
    try:
        os.system(f"bash {pwd}/update.sh")
        return "finish"
    except OSError as e:
        return str(e)


def active_transfer():
    t.transform_data()
    t.send_data()


if __name__ == "__main__":
    sensor_scheduler = BackgroundScheduler()
    sensor_scheduler.add_job(update_mem, "interval", seconds=1)
    sensor_scheduler.add_job(active_transfer, "interval", seconds=30)
    sensor_scheduler.add_job(main, "interval", seconds=60)
    sensor_scheduler.start()

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80, reload=True)
