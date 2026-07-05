from umd_client.config import LocationConfig
from umd_client.display.epd2in13b_v4 import render_images
from umd_client.sensors.types import Reading


class FakeEPD:
    height = 250
    width = 122


def test_render_images_accepts_reading_and_returns_display_buffers():
    reading = Reading(
        timestamp=123,
        data={
            "time": 123,
            "temperature": 22.5,
            "humidity": 60.0,
            "pressure": 1013.25,
            "lux": 1200.5,
            "uv": 4,
            "shake": 5.0,
        },
    )

    black, red = render_images(reading, epd=FakeEPD(), location=LocationConfig(), timestamp=12 * 60 * 60)

    assert black.size == (250, 122)
    assert red.size == (250, 122)
