#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/

#   _______     _
#  |_  / _ \   /_\
#   / / (_) | / _ \
#  /___\__\_\/_/ \_\

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

app = FastAPI()

pwd = "/home/exdragine/UMD-Client"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def read_data():
    df = pd.read_csv(f"{pwd}/data/latest_1d.csv")
    df['time'] = pd.to_datetime(df['time'], unit='s',origin = "1970-01-01 08:00:00")  # Assuming time is in Unix timestamp format
    return df


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    df = read_data()
    df['time'] = df['time'].astype(str)  # 将Timestamp类型转换为字符串

    latest_data = {
        "temperature": float(df["temperature"].iloc[-1]),
        "humidity": float(df["humidity"].iloc[-1]),
        "wind_speed": float(df["wind_speed"].iloc[-1]),
        "wind_scale": float(df["wind_scale"].iloc[-1]),
        "wind_angle": float(df["wind_angle"].iloc[-1]),
        "wind_direction": float(df["wind_direction"].iloc[-1]),
        "noise": float(df["noise"].iloc[-1]),
        "pm2dot5": float(df["pm2dot5"].iloc[-1]),
        "pm10": float(df["pm10"].iloc[-1]),
        "pressure": float(df["pressure"].iloc[-1]),
        "rain": float(df["rain"].iloc[-1])
    }

    context = {
        "request": request,
        "data": df.to_dict(orient="list"),
        "latest_data": latest_data
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/status")
async def api():
    df = pd.read_csv(f"{pwd}/data/latest_1d.csv")
    response = {
        "time": str(df["time"].iloc[-1]),
        "temperature": float(df["temperature"].iloc[-1]),
        "humidity": float(df["humidity"].iloc[-1]),
        "wind_speed": float(df["wind_speed"].iloc[-1]),
        "wind_angle": float(df["wind_angle"].iloc[-1]),
        "noise": float(df["noise"].iloc[-1]),
        "pm2.5": float(df["pm2dot5"].iloc[-1]),
        "pm10": float(df["pm10"].iloc[-1]),
        "pressure": float(df["pressure"].iloc[-1]),
        "rain": float(df["rain"].iloc[-1])
    }
    return response


@app.get("/download")
async def download():
    return FileResponse(f"{pwd}/data/latest_3h.csv")
    # TODO: 日后再写正则表达式吧
    # (([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]{1}|[0-9]{1}[1-9][0-9]{2}|[1-9][0-9]{3})__sep__(((0[13578]|1[02])__sep__(0[1-9]|[12][0-9]|3[01]))|((0[469]|11)__sep__(0[1-9]|[12][0-9]|30))|(02__sep__(0[1-9]|[1][0-9]|2[0-8]))))|((([0-9]{2})(0[48]|[2468][048]|[13579][26])__sep__02__sep__29)|((0[48]|[2468][048]|[13579][26])00__sep__02__sep__29))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)

