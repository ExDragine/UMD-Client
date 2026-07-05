<!--
  __  __     __    __     _____
 /\ \/\ \   /\ "-./  \   /\  __-.
 \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
  \ \_____\  \ \_\ \ \_\  \ \____-
   \/_____/   \/_/  \/_/   \/____/
-->

# UMD-Client

UMD-Client 是一个用于 UMD Weather Platform 的树莓派气象站客户端。
默认运行路径会读取 Raspberry Pi Sensor HAT，将当前读数发送到配置的服务器，
把最近一次 JSON 上报内容写入 `latest_data.json`，并且可以按独立频率刷新
Waveshare 墨水屏或用 OV5647 相机拍照。

## 项目结构

| 路径 | 作用 |
| --- | --- |
| `src/umd_client/app.py` | 运行时调度和单次采集流程 |
| `src/umd_client/config.py` | TOML 配置读取与校验 |
| `src/umd_client/transport.py` | 上报 payload 构建和 HTTP 上传 |
| `src/umd_client/sensors/sensor_hat/` | 默认 Sensor HAT 传感器集成 |
| `src/umd_client/sensors/sn3003/` | 可选 SN3003 串口传感器集成 |
| `src/umd_client/display/epd2in13b_v4/` | 可选 Waveshare e-Paper 墨水屏集成 |
| `src/umd_client/camera/ov5647/` | 可选 OV5647 相机辅助模块 |

## 安装

先安装 `uv`，然后创建开发环境：

```sh
uv sync --extra dev
```

创建本地配置文件：

```sh
cp .env.toml.example .env.toml
```

编辑 `.env.toml`，填入你的站点名称、密钥、上传地址，以及需要启用的运行选项。

## 运行

```sh
uv run umd-client run --config .env.toml
```

硬件调试命令可以用于单次检查：

```sh
uv run umd-client sample --config .env.toml
uv run umd-client display-once --config .env.toml
uv run umd-client photo-once --config .env.toml
```

兼容脚本执行的是同一件事：

```sh
./run.sh
```

如果 `.env.toml` 不存在，客户端会保留之前的行为，交互式提示输入必需配置。

## 树莓派说明

默认 Sensor HAT 路径依赖树莓派 I2C 栈和 `smbus`。当前上传字段为：
`time`、`temperature`、`humidity`、`pressure`、`lux`、`uv`、`shake`。

可选模块保留了旧项目的能力，但不属于默认运行路径：

- SN3003 需要串口访问和 `pyserial`，使用 `uv sync --extra sn3003` 安装。
- e-Paper 墨水屏需要 Pillow、Astral、SPI/GPIO 库以及 Waveshare 屏幕接线，
  Python 依赖使用 `uv sync --extra display` 安装。
- OV5647 相机使用 `rpicam-still`，并通过 Astral 计算昼夜曝光。

显示屏和相机调度由 `.env.toml` 控制：

```toml
display_enabled = true
display_frequency = 300
camera_enabled = true
camera_frequency = 1800
```

## 开发

运行 CI 使用的检查：

```sh
uv run ruff check .
uv run pytest
python3 -m compileall -q .
```
