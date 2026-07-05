from umd_client.sensors.sensor_hat import build_reading


def test_build_reading_maps_sensor_hat_core_fields():
    raw = [
        22.5,
        60.0,
        1013.25,
        1200.5,
        4,
        123.0,
        1.0,
        2.0,
        3.0,
        0,
        0,
        0,
        3,
        4,
        0,
        10,
        20,
        30,
    ]

    reading = build_reading(raw, timestamp=123456)

    assert reading.timestamp == 123456
    assert reading.data == {
        "time": 123456,
        "temperature": 22.5,
        "humidity": 60.0,
        "pressure": 1013.25,
        "lux": 1200.5,
        "uv": 4,
        "shake": 5.0,
    }
    assert reading.value_names == ["time", "temperature", "humidity", "pressure", "lux", "uv", "shake"]
    assert reading.values == [123456, 22.5, 60.0, 1013.25, 1200.5, 4, 5.0]
    assert reading.display_values == [22.5, 60.0, 1013.25, 1200.5, 4]
