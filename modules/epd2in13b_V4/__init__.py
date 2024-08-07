import datetime
from astral import LocationInfo
from astral.sun import sun
from astral.moon import moonrise, moonset, phase
from PIL import Image, ImageFont, ImageDraw

from modules.epd2in13b_V4 import epd2in13b_V4

icon_font_huge = ImageFont.truetype("./font/FluentSystemIcons-Resizable.ttf", size=96)


def draw_moon_phase(drawblack, height, width, moon_phase, moon_rise, moon_set, timestamp, icon_font_huge):
    def draw_icon(text):
        drawblack.text((int(height / 4 - 96 / 2), int((width - 96) / 2)), text=text, font=icon_font_huge, fill=0)

    if 9 <= moon_phase < 21:
        if moon_rise and moon_set:
            if int(moon_rise.timestamp()) < timestamp or timestamp < int(moon_set.timestamp()):
                draw_icon("\uF339")
            else:
                draw_icon("\uF33B")
        elif moon_rise and int(moon_rise.timestamp()) < timestamp:
            draw_icon("\uF339")
        elif moon_set and timestamp < int(moon_set.timestamp()):
            draw_icon("\uF339")
        else:
            draw_icon("\uF33B")
    else:
        if moon_rise and moon_set:
            if int(moon_rise.timestamp()) < timestamp or timestamp < int(moon_set.timestamp()):
                draw_icon("\uF338")
            else:
                draw_icon("\uF33A")
        elif moon_rise and int(moon_rise.timestamp()) < timestamp:
            draw_icon("\uF338")
        elif moon_set and timestamp < int(moon_set.timestamp()):
            draw_icon("\uF338")
        else:
            draw_icon("\uF33A")


def display(data):
    today = datetime.datetime.today()
    city = LocationInfo("Guangzhou", "China", "Asia/Harbin", 23.109866, 113.2683)
    s = sun(city.observer, date=datetime.date(today.year, today.month, today.day), tzinfo=city.timezone)
    sunrise_start = int((s["sunrise"] + datetime.timedelta(minutes=-15)).timestamp())
    sunrise_finish = int((s["sunrise"] + datetime.timedelta(minutes=15)).timestamp())
    sunset_start = int((s["sunset"] + datetime.timedelta(minutes=-15)).timestamp())
    sunset_finish = int((s["sunset"] + datetime.timedelta(minutes=15)).timestamp())
    moon_phase = phase(datetime.date(today.year, today.month, today.day))
    try:
        moon_rise = moonrise(city.observer, date=datetime.date(today.year, today.month, today.day), tzinfo=city.timezone)
    except ValueError as e:
        moon_rise = None
    try:
        moon_set = moonset(city.observer, date=datetime.date(today.year, today.month, today.day), tzinfo=city.timezone)
    except ValueError as e:
        moon_set = None
    timestamp = int(datetime.datetime.now().timestamp())

    epd = epd2in13b_V4.EPD()
    font = ImageFont.truetype("./font/Minecraft.ttf", 16)
    HBlackimage = Image.new("1", (epd.height, epd.width), color=255)  # 250*122
    RedImage = Image.new("1", (epd.height, epd.width), color=255)  # 250*122
    drawblack = ImageDraw.Draw(HBlackimage)
    drawred = ImageDraw.Draw(RedImage)
    try:
        drawblack.text((125, 13), text=f"T: {data[0]}℃", font=font, fill=0)
        drawblack.text((125, 33), text=f"H: {data[1]}%", font=font, fill=0)
        drawblack.text((125, 53), text=f"P: {int(data[2])}hPa", font=font, fill=0)
        drawblack.text((125, 73), text=f"L: {int(data[3])}", font=font, fill=0)
        drawblack.text((125, 93), text=f"U: {data[4]}", font=font, fill=0)
        if sunrise_start < timestamp < sunrise_finish:
            drawblack.text((int(epd.height / 4 - 96 / 2), int((122 - 96) / 2)), text="\uF357", font=icon_font_huge, fill=0)
        elif sunset_start < timestamp < sunset_finish:
            drawblack.text((int(epd.height / 4 - 96 / 2), int((122 - 96) / 2)), text="\uF356", font=icon_font_huge, fill=0)
        elif sunrise_finish < timestamp < sunset_start:
            if data[3] > 2000.0:
                drawblack.text((int(epd.height / 4 - 96 / 2), int((122 - 96) / 2)), text="\uF355", font=icon_font_huge, fill=0)
            elif data[3] > 1500.0:
                drawblack.text((int(epd.height / 4 - 96 / 2), int((122 - 96) / 2)), text="\uF33D", font=icon_font_huge, fill=0)
            elif data[3] > 800.0:
                drawblack.text((int(epd.height / 4 - 96 / 2), int((122 - 96) / 2)), text="\uF32B", font=icon_font_huge, fill=0)
            else:
                drawblack.text((int(epd.height / 4 - 96 / 2), int((122 - 96) / 2)), text="\uF330", font=icon_font_huge, fill=0)
        elif sunset_finish < timestamp or timestamp < sunrise_start:
            draw_moon_phase(drawblack, epd.height, epd.width, moon_phase, moon_rise, moon_set, timestamp, icon_font_huge)

        drawred.line((108, 0, 108, 0), fill=0)
        drawred.line((109, 0, 109, 0), fill=0)

    except:
        drawblack.text(
            (int((epd.height - 64) / 2), int(13)),
            text="\uF322",
            font=ImageFont.truetype("./font/FluentSystemIcons-Resizable.ttf", size=64),
            fill=0,
        )
        text = "SYSTEM FAILED"
        drawblack.text((int((epd.height - len(text.replace(" ", "")) * 12) / 2), 93), text=text, font=font, fill=0)
    HBlackimage = HBlackimage.rotate(180)
    RedImage = RedImage.rotate(180)
    try:
        epd.init()
        epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(RedImage))
        epd.sleep()
    except KeyboardInterrupt:
        epd.sleep()
