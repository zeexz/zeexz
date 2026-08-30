#!/usr/bin/env python3
"""
Updates two auto-generated blocks in README.md:

1. <!--STATUS_START--> ... <!--STATUS_END-->
   Live local time + weather (Open-Meteo, no API key required).

2. <!--BUILDING_START--> ... <!--BUILDING_END-->
   Your most recently pushed-to public repo, pulled from the
   GitHub REST API (no auth token required for public data,
   but GITHUB_TOKEN is used automatically in Actions to raise
   the rate limit).
"""

import re
import sys
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import urllib.request
import json

# ---- Configuration ----
LOCATION_NAME = "Colombo, Sri Lanka"
LATITUDE = 6.9271
LONGITUDE = 79.8612
TIMEZONE = "Asia/Colombo"
GITHUB_USERNAME = "zeexz"
README_PATH = "README.md"

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


# ---------------------------------------------------------------------
# Weather + time
# ---------------------------------------------------------------------

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


def build_status_block():
    weather = fetch_weather()
    local_time = get_local_time()
    return (
        "```text\n"
        f"📍 Location   : {LOCATION_NAME}\n"
        f"🕒 Local Time : {local_time}\n"
        f"🌤️ Weather    : {weather}\n"
        "```"
    )


# ---------------------------------------------------------------------
# Currently building
# ---------------------------------------------------------------------

def time_ago(iso_timestamp: str) -> str:
    """Convert an ISO 8601 UTC timestamp to a short 'X ago' string."""
    pushed = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - pushed

    seconds = int(delta.total_seconds())
    if seconds < 3600:
        minutes = max(seconds // 60, 1)
        return f"{minutes}m ago"
    hours = seconds // 3600
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    return f"{months}mo ago"


def fetch_currently_building():
    """
    Finds the public, non-fork repo with the most recent push,
    via the GitHub REST API.
    """
    url = (
        f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
        "?sort=pushed&direction=desc&per_page=10&type=owner"
    )
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos = json.loads(resp.read().decode())

        for repo in repos:
            if repo.get("fork"):
                continue
            name = repo["name"]
            description = repo.get("description") or "No description provided."
            language = repo.get("language") or "—"
            pushed_at = repo["pushed_at"]
            url_html = repo["html_url"]
            return {
                "name": name,
                "description": description,
                "language": language,
                "updated": time_ago(pushed_at),
                "url": url_html,
            }
        return None
    except Exception as e:
        print(f"Currently-building fetch failed: {e}", file=sys.stderr)
        return None


def build_building_block():
    repo = fetch_currently_building()
    if repo is None:
        return "```text\nUnavailable right now — check back later.\n```"

    return (
        "```text\n"
        f"📦 Repo     : {repo['name']}\n"
        f"📝 About    : {repo['description']}\n"
        f"💻 Language : {repo['language']}\n"
        f"🕓 Updated  : {repo['updated']}\n"
        "```\n"
        f"**[View Repo →]({repo['url']})**"
    )


# ---------------------------------------------------------------------
# README writer
# ---------------------------------------------------------------------

def replace_block(content: str, marker: str, new_inner: str) -> str:
    start = f"<!--{marker}_START-->"
    end = f"<!--{marker}_END-->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)

    if not pattern.search(content):
        print(f"{marker} markers not found in README.md", file=sys.stderr)
        sys.exit(1)

    replacement = f"{start}\n{new_inner}\n{end}"
    return pattern.sub(replacement, content)


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = replace_block(content, "STATUS", build_status_block())
    content = replace_block(content, "BUILDING", build_building_block())

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated: STATUS + BUILDING blocks.")


if __name__ == "__main__":
    update_readme()
