#!/usr/bin/env python3
"""
Fetches current local time + live weather for a fixed location and
rewrites the block between <!--STATUS_START--> and <!--STATUS_END-->
in README.md.

Weather API: Open-Meteo (https://open-meteo.com) — free, no API key required.
Timezone:    zoneinfo (Python 3.9+, stdlib) — no API key required.
"""

import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.request
import json

# ---- Configuration: edit these for your own location ----
LOCATION_NAME = "Colombo, Sri Lanka"
LATITUDE = 6.9271
LONGITUDE = 79.8612
TIMEZONE = "Asia/Colombo"
README_PATH = "README.md"

# WMO weather codes -> human-readable + emoji
WEATHER_CODES = {
    0: ("Clear Sky", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "🌤️"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing Rime Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Moderate Drizzle", "🌦️"),
    55: ("Dense Drizzle", "🌦️"),
    61: ("Slight Rain", "🌧️"),
    63: ("Moderate Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    71: ("Slight Snow", "🌨️"),
    73: ("Moderate Snow", "🌨️"),
    75: ("Heavy Snow", "🌨️"),
    80: ("Rain Showers", "🌦️"),
    81: ("Moderate Rain Showers", "🌦️"),
    82: ("Violent Rain Showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm w/ Hail", "⛈️"),
    99: ("Thunderstorm w/ Heavy Hail", "⛈️"),
}


def fetch_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        "&current=temperature_2m,weather_code"
        f"&timezone={TIMEZONE}"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        current = data["current"]
        temp = current["temperature_2m"]
        code = current["weather_code"]
        desc, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))
        return f"{emoji} {desc}, {round(temp)}°C"
    except Exception as e:
        print(f"Weather fetch failed: {e}", file=sys.stderr)
        return "Unavailable"


def get_local_time():
    now = datetime.now(ZoneInfo(TIMEZONE))
    return now.strftime("%H:%M, %A %d %B %Y")


def build_block():
    weather = fetch_weather()
    local_time = get_local_time()
    return (
        "```text\n"
        f"📍 Location   : {LOCATION_NAME}\n"
        f"🕒 Local Time : {local_time}\n"
        f"🌤️ Weather    : {weather}\n"
        "```"
    )


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_block = build_block()
    pattern = re.compile(
        r"<!--STATUS_START-->.*?<!--STATUS_END-->", re.DOTALL
    )
    replacement = f"<!--STATUS_START-->\n{new_block}\n<!--STATUS_END-->"

    if not pattern.search(content):
        print("STATUS markers not found in README.md", file=sys.stderr)
        sys.exit(1)

    updated = pattern.sub(replacement, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print("README.md status block updated.")


if __name__ == "__main__":
    update_readme()
