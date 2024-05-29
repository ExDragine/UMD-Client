from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def read_data():
    df = pd.read_csv("./data.csv")
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Assuming time is in Unix timestamp format
    return df  # 仅获取最新的60个数据点


def create_chart(df, key, title):
    x_data = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    y_data = df[key].tolist()
    yaxis_min = min(y_data)
    yaxis_max = max(y_data)

    line = (
        Line(init_opts=opts.InitOpts(width="100%", height="100%"))
        .add_xaxis(x_data)
        .add_yaxis(title, y_data, is_smooth=True)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(type_="value", min_=yaxis_min, max_=yaxis_max),
            datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],
        )
    )
    return line, y_data[-1]  # 返回图表和最新值


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    df = read_data()
    temperature_chart, latest_temperature = create_chart(df, "temperature", "Temperature")
    humidity_chart, latest_humidity = create_chart(df, "humidity", "Humidity")
    wind_speed_chart, latest_wind_speed = create_chart(df, "wind_speed", "Wind Speed")
    wind_scale_chart, latest_wind_scale = create_chart(df, "wind_scale", "Wind Scale")
    wind_angle_chart, latest_wind_angle = create_chart(df, "wind_angle", "Wind Angle")
    wind_direction_chart, latest_wind_direction = create_chart(df, "wind_direction", "Wind Direction")
    noise_chart, latest_noise = create_chart(df, "noise", "Noise")
    pm2dot5_chart, latest_pm2dot5 = create_chart(df, "pm2dot5", "PM2.5")
    pm10_chart, latest_pm10 = create_chart(df, "pm10", "PM10")
    pressure_chart, latest_pressure = create_chart(df, "pressure", "Pressure")
    rain_chart, latest_rain = create_chart(df, "rain", "Rain")

    context = {
        "request": request,
        "latest_temperature": latest_temperature,
        "latest_humidity": latest_humidity,
        "latest_wind_speed": latest_wind_speed,
        "latest_wind_scale": latest_wind_scale,
        "latest_wind_angle": latest_wind_angle,
        "latest_wind_direction": latest_wind_direction,
        "latest_noise": latest_noise,
        "latest_pm2dot5": latest_pm2dot5,
        "latest_pm10": latest_pm10,
        "latest_pressure": latest_pressure,
        "latest_rain": latest_rain,
        "temperature_chart": temperature_chart.render_embed(),
        "humidity_chart": humidity_chart.render_embed(),
        "wind_speed_chart": wind_speed_chart.render_embed(),
        "wind_scale_chart": wind_scale_chart.render_embed(),
        "wind_angle_chart": wind_angle_chart.render_embed(),
        "wind_direction_chart": wind_direction_chart.render_embed(),
        "noise_chart": noise_chart.render_embed(),
        "pm2dot5_chart": pm2dot5_chart.render_embed(),
        "pm10_chart": pm10_chart.render_embed(),
        "pressure_chart": pressure_chart.render_embed(),
        "rain_chart": rain_chart.render_embed(),
    }
    return templates.TemplateResponse("index.html", context)

@app.get("/status")
async def api():
    data = pd.read_csv("./data.csv").tail(1)
    response = {
        "time":str(data.iloc[0,0]),
        "temperature":float(data.iloc[0,1]),
        "humidity":float(data.iloc[0,2]),
        "wind_speed":float(data.iloc[0,3]),
        "wind_angle":float(data.iloc[0,6]),
        "noise":float(data.iloc[0,7]),
        "pm2.5":float(data.iloc[0,8]),
        "pm10":float(data.iloc[0,9]),
        "pressure":float(data.iloc[0,10]),
        "rain":float(data.iloc[0,11])
    }
    return response

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
