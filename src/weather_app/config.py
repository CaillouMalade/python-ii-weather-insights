"""Environment configuration: reads the API key without crashing when it is missing."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "variables.env")

# API_KEY is None when no key is configured. The app checks this and shows
# SETUP_MESSAGE, so Analytics keeps working on the saved log without a key.
API_KEY = os.getenv("OPENWEATHER_API_KEY")

SETUP_MESSAGE = (
    "Live weather needs an OpenWeatherMap API key. Copy variables.env.example to "
    "variables.env, fill in your own key, then restart the app."
)
