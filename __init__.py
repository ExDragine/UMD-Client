import logging
import os
import threading
import time
import tomllib

from modules.sn3003 import SN3003FSXCSN01
from utils.init import init
from utils.send import send_to

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s:%(funcName)s] - %(levelname)s - %(message)s",
    datefmt="[%X]",
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
storage_size = int(env.get("storage_size", 86400 / record_frequency))  # One day
path = env.get("data_path", f"{os.getcwd()}/data")

sn3003 = SN3003FSXCSN01()


def main():
    try:
        """
        A sample Raspberry Pi sensor board based on the Raspberry Pi sensor board, implementing the most basic data acquisition and sending functions.
        """
        sn3003.update_mem()
        send_to(key=key, name=name, server=server, value_name=sn3003.names, value=list(sn3003.mem_data[-1]))
    except Exception as e:
        logger.error(f"Error occurred in main: {e}")


def scheduler():
    """
    Schedule the main function to run at fixed intervals.
    """
    main()  # Call the main function
    threading.Timer(record_frequency, scheduler).start()  # Schedule the next execution


if __name__ == "__main__":
    try:
        scheduler()  # Start the scheduler
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
