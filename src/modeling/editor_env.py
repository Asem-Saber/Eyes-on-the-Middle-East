"""Project-venv startup support for dbt Core editor integrations."""
import os
from pathlib import Path


def configure():
    if os.environ.get("DBT_CONFIG_AUTOLOAD") == "0":
        return
    from .dbt import dbt_environment
    environment = dbt_environment()
    for name in ("DBT_HOST", "DBT_PORT", "DBT_DATABASE", "DBT_USER", "DBT_PASSWORD",
                 "DBT_SEND_ANONYMOUS_USAGE_STATS"):
        os.environ.setdefault(name, environment[name])
    os.environ.setdefault("DBT_PROFILES_DIR", str(Path(__file__).resolve().parent))
