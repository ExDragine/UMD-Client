#  __  __     __    __     _____
# /\ \/\ \   /\ "-./  \   /\  __-.
# \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
#  \ \_____\  \ \_\ \ \_\  \ \____-
#   \/_____/   \/_/  \/_/   \/____/


import os
import tomllib

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore

from modules.sensor_hat import Sensor_HAT
from modules.epd2in13b_V4 import display
from utils.adapter import umd
from utils.init import init
from utils.send import send_to
from utils.sql import Database

# Log
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s:%(funcName)s] - %(levelname)s - %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)
logger = logging.getLogger("job")

if not os.path.exists(".env.toml"):
    logger.info("Initializing")
    init()

with open(".env.toml", "rb") as f:
    env = tomllib.load(f)


name = env.get("station_name")
key = env.get("station_key")
server = env.get("server")
record_frequency = int(env.get("record_frequency", 30))
storage_size = int(env.get("storage_size", 86400/record_frequency)) # One day
path = env.get("data_path", f"{os.getcwd()}/data")


# sn3003 = SN3003FSXCSN01()
sensor_hat = Sensor_HAT()

database_name = "./data/record.db"
database = Database(database_name)
if not os.path.exists(database_name):
    database.init()


def main():
    """
    A sample Raspberry Pi sensor board based on the Raspberry Pi sensor board, implementing the most basic data acquisition and sending functions.
    """
    hat_data = sensor_hat.read()
    packed_data = umd(sensor_hat.packed_data())
    send_to(
        key=key,
        name=name,
        server=server,
        value_name=packed_data.keys(),
        value=packed_data.values(),
    )
    database.insert(hat_data)

def update_display():
    """
    Optional extension functions, you can form your own extension functions
    """
    hat_data = sensor_hat.read()
    display(hat_data)

if __name__ == "__main__":
    background_scheduler = BackgroundScheduler()
    block_scheduler = BlockingScheduler()

    background_scheduler.add_job(update_display, "interval", seconds=300,jitter=1)
    block_scheduler.add_job(main, "interval", seconds=record_frequency)

    background_scheduler.start()
    block_scheduler.start()
