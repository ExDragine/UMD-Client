import os
import subprocess
import sys
from pathlib import Path


def test_cli_help_imports_without_hardware_dependencies():
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")

    result = subprocess.run(
        [sys.executable, "-m", "umd_client", "--help"],
        check=False,
        cwd=project_root,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "umd-client" in result.stdout


def test_debug_command_help_imports_without_hardware_dependencies():
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")

    for command in ["sample", "display-once", "photo-once"]:
        result = subprocess.run(
            [sys.executable, "-m", "umd_client", command, "--help"],
            check=False,
            cwd=project_root,
            env=env,
            text=True,
            capture_output=True,
        )

        assert result.returncode == 0
        assert "--config" in result.stdout
