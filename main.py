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


app = FastAPI()

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
    """主页rount

    Args:
        request (Request): 响应请求

    Returns:
        _type_: 网页
    """

    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/status")
async def api():
    """返回实时信息

    Returns:
        _type_: _description_
    """
    response = pd.read_csv(f"{pwd}/data/latest_mean.csv").tail(1).to_dict(orient="records")[0]
    return response


@app.get("/api/download")
async def download(value="mean", year=0, month=0, day=0):
    """下载数据

    Args:
        value (str, optional): _description_. Defaults to "mean".
        year (int, optional): _description_. Defaults to 0.
        month (int, optional): _description_. Defaults to 0.
        day (int, optional): _description_. Defaults to 0.

    Returns:
        _type_: File
    """
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


class Types(enum.Enum):
    """返回类型枚举

    Args:
        enum (_type_): 图表类型
    """

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
async def get_charts(type: Types):
    """表格API

    Args:
        type (types): 表格类型

    Returns:
        _type_: Json
    """
    df = pd.read_csv(f"{pwd}/data/latest_mean.csv")
    # Assuming time is in Unix timestamp format
    df["time"] = pd.to_datetime(df["time"], unit="s", origin="1970-01-01 08:00:00").astype(str)
    response = {}
    response["time"] = df["time"].to_list()
    if type.value in ["wind_scale", "wind_direction"]:
        response[type.name] = df[type.name].round(0).to_list()
    else:
        response[type.name] = df[type.name].to_list()
    return response


@app.get("/update")
async def update():
    """更新服务端

    Returns:
        _type_: Json
    """
    try:
        os.system(f"bash {pwd}/update.sh")
        return "finish"
    except OSError as e:
        return str(e)


@app.get("/photo")
async def photo(test=False):
    """拍照

    Returns:
        File,str: _description_
    """
    try:
        if not os.path.exists("./data/photo"):
            return "No photo right now."
        file_list = os.listdir("./data/photo")
        file_list.sort(key=lambda x: os.path.getmtime(os.path.join("./data/photo", x)))
        latest_file = os.path.join("./data/photo", file_list[-1])
        if os.path.exists(latest_file):
            return FileResponse(latest_file)
        else:
            return "Something wrong."
    except Exception as e:
        return str(e)


if __name__ == "__main__":

    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
