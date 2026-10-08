"""Load settings from the environment, reading a local .env file if present.

Tokens are never printed or logged; error messages list variable names only.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path=ROOT / ".env"):
    """Set variables from a .env file without overriding the real environment."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require(*names):
    """Return the named variables, or exit listing every missing one."""
    load_dotenv()
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit(
            "Missing required settings: " + ", ".join(missing)
            + "\nCopy .env.example to .env and fill them in."
        )
    return {n: os.environ[n] for n in names}
