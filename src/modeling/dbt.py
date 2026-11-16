"""Run dbt with connection settings read exclusively through config.py."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .connection import settings


def dbt_environment():
    """Connection variables for dbt and editor child processes only."""
    config = settings()
    environment = os.environ.copy()
    environment["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    environment.update({"DBT_HOST": str(config["host"]), "DBT_PORT": str(config["port"]),
                        "DBT_DATABASE": config["dbname"], "DBT_USER": config["user"],
                        "DBT_PASSWORD": config["password"]})
    return environment


def main():
    environment = dbt_environment()
    local_executable = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    executable = str(local_executable) if local_executable.exists() else shutil.which("dbt")
    if not executable:
        raise RuntimeError("Install the warehouse dependency group first")
    project = Path(__file__).resolve().parent
    return subprocess.call([executable, *sys.argv[1:], "--project-dir", str(project),
                            "--profiles-dir", str(project)], env=environment)


if __name__ == "__main__":
    raise SystemExit(main())
