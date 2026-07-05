import argparse
import json
from pathlib import Path

from umd_client.app import capture_camera, refresh_display, run
from umd_client.config import load_config
from umd_client.sensors.factory import create_sensor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="umd-client")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the weather station client.")
    run_parser.add_argument(
        "--config",
        default=".env.toml",
        type=Path,
        help="Path to the TOML configuration file.",
    )
    for command, help_text in [
        ("sample", "Read the configured sensor once and print JSON."),
        ("display-once", "Read the configured sensor once and refresh the display."),
        ("photo-once", "Capture one OV5647 photo."),
    ]:
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument(
            "--config",
            default=".env.toml",
            type=Path,
            help="Path to the TOML configuration file.",
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        run(args.config)
        return 0
    if args.command == "sample":
        config = load_config(args.config)
        reading = create_sensor(config).read()
        print(json.dumps(reading.data, ensure_ascii=True, indent=4))
        return 0
    if args.command == "display-once":
        config = load_config(args.config)
        reading = create_sensor(config).read()
        refresh_display(reading, config)
        return 0
    if args.command == "photo-once":
        config = load_config(args.config)
        capture_camera(config)
        return 0

    parser.print_help()
    return 0
