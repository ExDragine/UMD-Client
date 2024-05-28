from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd

app = FastAPI()

def read_data():
    df = pd.read_csv("/home/exdragine/UMD/data.csv")
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Assuming time is in Unix timestamp format
    return df  # 仅获取最新的60个数据点

def create_chart(df, key, title):
    x_data = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    y_data = df[key].tolist()
    
    line = (
        Line()
        .add_xaxis(x_data)
        .add_yaxis(title, y_data, is_smooth=True)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],
        )
    )
    return line, y_data[-1]  # 返回图表和最新值

@app.get("/", response_class=HTMLResponse)
async def index():
    df = read_data()
    temperature_chart, latest_temperature = create_chart(df, "temperature", "Temperature")
    humidity_chart, latest_humidity = create_chart(df, "humidity", "Humidity")
    wind_speed_chart, latest_wind_speed = create_chart(df, "wind_speed", "Wind Speed")
    wind_scale_chart, latest_wind_scale = create_chart(df, "wind_scale", "Wind Scale")
    wind_angle_chart, latest_wind_angle = create_chart(df, "wind_angle", "Wind Angle")
    noise_chart, latest_noise = create_chart(df, "noise", "Noise")
    pm2dot5_chart, latest_pm2dot5 = create_chart(df, "pm2dot5", "PM2.5")
    pm10_chart, latest_pm10 = create_chart(df, "pm10", "PM10")
    pressure_chart, latest_pressure = create_chart(df, "pressure", "Pressure")
    rain_chart, latest_rain = create_chart(df, "rain", "Rain")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sensor Data</title>
        <style>
            .chart-container {{
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
            }}
            .chart {{
                width: 45%;
                min-width: 300px;
                margin: 20px 0;
            }}
            .latest-values {{
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
                margin-bottom: 20px;
            }}
            .value-box {{
                width: 30%;
                min-width: 200px;
                margin: 10px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-size: 1.2em;
            }}
        </style>
    </head>
    <body>
        <h1>广州市李华气象站</h1>
        <div class="latest-values">
            <div class="value-box">温度: {latest_temperature}°C</div>
            <div class="value-box">湿度: {latest_humidity}%</div>
            <div class="value-box">风速: {latest_wind_speed} m/s</div>
            <div class="value-box">风级: {latest_wind_scale}</div>
            <div class="value-box">风向: {latest_wind_angle}°</div>
            <div class="value-box">噪声: {latest_noise} dB</div>
            <div class="value-box">PM2.5: {latest_pm2dot5} µg/m³</div>
            <div class="value-box">PM10: {latest_pm10} µg/m³</div>
            <div class="value-box">压力: {latest_pressure} hPa</div>
            <div class="value-box">雨量: {latest_rain} mm</div>
        </div>
        <div class="chart-container">
            <div class="chart">{temperature_chart.render_embed()}</div>
            <div class="chart">{humidity_chart.render_embed()}</div>
            <div class="chart">{wind_speed_chart.render_embed()}</div>
            <div class="chart">{wind_scale_chart.render_embed()}</div>
            <div class="chart">{wind_angle_chart.render_embed()}</div>
            <div class="chart">{noise_chart.render_embed()}</div>
            <div class="chart">{pm2dot5_chart.render_embed()}</div>
            <div class="chart">{pm10_chart.render_embed()}</div>
            <div class="chart">{pressure_chart.render_embed()}</div>
            <div class="chart">{rain_chart.render_embed()}</div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
