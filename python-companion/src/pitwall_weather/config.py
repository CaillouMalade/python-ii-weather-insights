"""Load only the configured local env file; never serialize key values."""
import os
from pathlib import Path


def load_config(env_path="variables.env"):
    try:
        from dotenv import load_dotenv
    except ImportError:
        raise RuntimeError("Install the package first: python -m pip install -e .") from None
    load_dotenv(Path(env_path), override=False)
    return {"openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),
            "database": os.getenv("PITWALL_DATABASE", "data/weather.sqlite3")}
