import os
import datetime

from astral import LocationInfo
from astral.sun import sun


def photo():
    path = "./data/photo"
    os.makedirs(path, exist_ok=True)
    file_name = datetime.datetime.now().strftime("%H-%M-%S")
    today = datetime.datetime.today()
    city = LocationInfo("guangzhou", "China", "Asia/Harbin", 23.109866, 113.2683)
    s = sun(city.observer, date=datetime.date(today.year, today.month, today.day), tzinfo=city.timezone)

    sunrise = int((s["sunrise"] + datetime.timedelta(minutes=-20)).timestamp())
    sunset = int((s["sunset"] + datetime.timedelta(minutes=20)).timestamp())
    if int(datetime.datetime.now().timestamp()) > sunset or int(datetime.datetime.now().timestamp()) < sunrise:
        os.system(f"rpicam-still --nopreview --rotation 180 --metering centre --awb daylight --shutter 6000000 --ev 0.5 -o {path}/{file_name}.jpg")
    else:
        os.system(f"rpicam-still --nopreview --rotation 180 --metering centre --awb daylight -o ./data/photo/{file_name}.jpg")
    if len(os.listdir(path)) > 1:
        file_list = os.listdir(path)
        file_list.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)))
        os.remove(os.path.join(path, file_list[0]))
