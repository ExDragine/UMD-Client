import json
import time
import ssl
import asyncio
import aiohttp

context = ssl._create_unverified_context()


async def send_to(key, name, server, value_name, value):
    """Send data to UMD platform

    Raises:
        e: ERROR
    """
    station_key = key
    station_name = name
    transmit_data = ""
    checklist = {"key": station_key, "station_name": station_name}
    for name, obj in checklist.items():
        if obj == "" or not isinstance(obj, str):
            raise ValueError(f"{name} incorrect, please input your {name} or check again.")

    data = dict(zip(value_name, value))
    p = {
        "id": station_name,
        "timestamp": int(time.time()),
        "key": station_key,
        "data": data,
    }
    # Hold
    p["data"]["hold1"] = None
    p["data"]["hold2"] = None
    p["data"]["hold3"] = None

    transmit_data = json.dumps(p, ensure_ascii=True, allow_nan=True, indent=4).encode("utf-8")
    with open("./data/send_data.json", "wb") as f:
        f.write(transmit_data)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url=server,
                json=transmit_data,
                headers={"Content-Type": "application/json"},
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=1),
            ) as response:
                response.raise_for_status()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            pass
