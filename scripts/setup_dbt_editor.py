"""One-time dbt editor setup for this project's .venv; no credentials are stored."""
from pathlib import Path
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise SystemExit("Run this script with the project's .venv Python interpreter")
    target = Path(sysconfig.get_path("purelib")) / "news_dwh_editor.pth"
    target.write_text(str(ROOT) + "\nimport src.modeling.editor_env; src.modeling.editor_env.configure()\n", encoding="utf-8")
    print("Configured project .venv to load dbt settings automatically from config.py.")


if __name__ == "__main__":
    main()
