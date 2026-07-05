from pathlib import Path


def init(path: str | Path = ".env.toml") -> None:
    station_name = _input_required("Please input station name: ")
    station_key = _input_required("Please input your key: ")
    server = _input_required("Please input endpoint(server): ")
    record_frequency = _input_int("Reflesh frequency: ")
    storage_size = _input_int("Log size: ")

    config_path = Path(path)
    config_path.write_text(
        "\n".join(
            [
                f"station_name = '{station_name}'",
                f"station_key = '{station_key}'",
                f"server = '{server}'",
                f"record_frequency = {record_frequency}",
                f"storage_size = {storage_size}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _input_required(prompt: str) -> str:
    while True:
        value = input(prompt)
        if value:
            return value
        print("Nothing input")


def _input_int(prompt: str) -> int:
    while True:
        value = input(prompt)
        try:
            return int(value)
        except ValueError:
            print("Error format\n")
