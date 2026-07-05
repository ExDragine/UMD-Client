<!--
  __  __     __    __     _____
 /\ \/\ \   /\ "-./  \   /\  __-.
 \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
  \ \_____\  \ \_\ \ \_\  \ \____-
   \/_____/   \/_/  \/_/   \/____/
-->

# UMD-Client

UMD-Client is a Raspberry Pi weather station client for the UMD Weather Platform.
The default runtime path reads the Raspberry Pi Sensor HAT, sends the current
reading to a configured server, writes the latest JSON payload to
`latest_data.json`, and can optionally refresh a Waveshare e-Paper display or
capture one OV5647 camera photo on separate schedules.

## Project Layout

| Path | Purpose |
| --- | --- |
| `src/umd_client/app.py` | Runtime scheduler and one-shot collection flow |
| `src/umd_client/config.py` | TOML configuration loading and validation |
| `src/umd_client/transport.py` | Payload construction and HTTP upload |
| `src/umd_client/sensors/sensor_hat/` | Default Sensor HAT integration |
| `src/umd_client/sensors/sn3003/` | Optional SN3003 serial sensor integration |
| `src/umd_client/display/epd2in13b_v4/` | Optional Waveshare e-Paper display integration |
| `src/umd_client/camera/ov5647/` | Optional OV5647 camera helper |

## Setup

Install `uv`, then create the environment:

```sh
uv sync --extra dev
```

Create local configuration:

```sh
cp .env.toml.example .env.toml
```

Edit `.env.toml` with your station name, key, upload endpoint, and optional
runtime settings.

## Run

```sh
uv run umd-client run --config .env.toml
```

Hardware debug commands are available for one-shot checks:

```sh
uv run umd-client sample --config .env.toml
uv run umd-client display-once --config .env.toml
uv run umd-client photo-once --config .env.toml
```

The compatibility script does the same thing:

```sh
./run.sh
```

If `.env.toml` is missing, the client keeps the previous behavior and prompts for
the required values interactively.

## Raspberry Pi Notes

The default Sensor HAT path depends on the Raspberry Pi I2C stack and `smbus`.
The uploaded data fields are `time`, `temperature`, `humidity`, `pressure`,
`lux`, `uv`, and `shake`.

Optional modules keep the old project capabilities but are not part of the
default runtime:

- SN3003 requires serial access and `pyserial`; install with `uv sync --extra sn3003`.
- e-Paper display requires Pillow, Astral, SPI/GPIO libraries, and the Waveshare
  display wiring; install Python dependencies with `uv sync --extra display`.
- OV5647 camera uses `rpicam-still` and Astral for day/night exposure selection.

Display and camera schedules are controlled by `.env.toml`:

```toml
display_enabled = true
display_frequency = 300
camera_enabled = true
camera_frequency = 1800
```

## Development

Run the checks used by CI:

```sh
uv run ruff check .
uv run pytest
python3 -m compileall -q .
```
