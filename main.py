from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd

app = FastAPI()

pwd = "/home/exdragine/UMD-Client"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def read_data():
    df = pd.read_csv(f"{pwd}/data/latest_3h.csv")
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Assuming time is in Unix timestamp format
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
    df = pd.read_csv(f"{pwd}/data/latest_3h.csv")
    response = {
        "time": str(df["time"].to_list()[-1]),
        "temperature": float(df["temperature"].to_list()[-1]),
        "humidity": float(df["humidity"].to_list()[-1]),
        "wind_speed": float(df["wind_speed"].to_list()[-1]),
        "wind_angle": float(df["wind_angle"].to_list()[-1]),
        "noise": float(df["noise"].to_list()[-1]),
        "pm2.5": float(df["pm2dot5"].to_list()[-1]),
        "pm10": float(df["pm10"].to_list()[-1]),
        "pressure": float(df["pressure"].to_list()[-1]),
        "rain": float(df["rain"].to_list()[-1])
    }
    return response

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)
