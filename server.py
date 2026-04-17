#!/usr/bin/env python3
"""
Weather Forecast MCP Server
Uses Open-Meteo API — free, no API key required.
"""

import json
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather Forecast", host="0.0.0.0", port=8000)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def _geocode(city: str) -> tuple[float, float, str]:
    params = urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
    data = _fetch(f"https://geocoding-api.open-meteo.com/v1/search?{params}")
    if not data.get("results"):
        raise ValueError(f"City not found: {city!r}")
    r = data["results"][0]
    name = f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}".strip(", ")
    return r["latitude"], r["longitude"], name


WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}


# ──────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────

@mcp.tool()
def get_current_weather(city: str) -> str:
    """
    Get the current weather conditions for any city in the world.

    Args:
        city: City name (e.g. "Paris", "Tokyo", "New York")
    """
    lat, lon, resolved = _geocode(city)
    params = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "weather_code,wind_speed_10m,wind_direction_10m,precipitation",
        "wind_speed_unit": "kmh",
        "temperature_unit": "celsius",
        "timezone": "auto",
    })
    data = _fetch(f"https://api.open-meteo.com/v1/forecast?{params}")
    c = data["current"]

    condition = WMO_CODES.get(c["weather_code"], "Unknown")
    wind_dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    wind_label = wind_dirs[round(c["wind_direction_10m"] / 45) % 8]

    return (
        f"Current weather in {resolved}\n"
        f"{'─'*40}\n"
        f"Condition    : {condition}\n"
        f"Temperature  : {c['temperature_2m']}°C  (feels like {c['apparent_temperature']}°C)\n"
        f"Humidity     : {c['relative_humidity_2m']}%\n"
        f"Wind         : {c['wind_speed_10m']} km/h {wind_label}\n"
        f"Precipitation: {c['precipitation']} mm\n"
    )


@mcp.tool()
def get_forecast(city: str, days: int = 7) -> str:
    """
    Get a multi-day weather forecast for any city.

    Args:
        city: City name (e.g. "London", "Sydney", "Toronto")
        days: Number of days to forecast — 1 to 16 (default 7)
    """
    days = max(1, min(days, 16))
    lat, lon, resolved = _geocode(city)
    params = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,wind_speed_10m_max",
        "wind_speed_unit": "kmh",
        "temperature_unit": "celsius",
        "timezone": "auto",
        "forecast_days": days,
    })
    data = _fetch(f"https://api.open-meteo.com/v1/forecast?{params}")
    d = data["daily"]

    lines = [
        f"{days}-day forecast for {resolved}",
        "─" * 52,
        f"{'Date':<12}{'Condition':<22}{'Min':>5}{'Max':>5}  {'Rain':>6}  {'Wind':>8}",
    ]
    for i in range(len(d["time"])):
        cond = WMO_CODES.get(d["weather_code"][i], "?")[:20]
        lines.append(
            f"{d['time'][i]:<12}{cond:<22}"
            f"{d['temperature_2m_min'][i]:>4}°  {d['temperature_2m_max'][i]:>4}°"
            f"  {d['precipitation_sum'][i]:>5}mm  {d['wind_speed_10m_max'][i]:>6}km/h"
        )
    return "\n".join(lines)


@mcp.tool()
def compare_weather(city1: str, city2: str) -> str:
    """
    Compare current weather between two cities side by side.

    Args:
        city1: First city name
        city2: Second city name
    """
    results = []
    for city in (city1, city2):
        lat, lon, resolved = _geocode(city)
        params = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,"
                       "relative_humidity_2m,wind_speed_10m,precipitation",
            "wind_speed_unit": "kmh",
            "temperature_unit": "celsius",
            "timezone": "auto",
        })
        data = _fetch(f"https://api.open-meteo.com/v1/forecast?{params}")
        results.append((resolved, data["current"]))

    (n1, c1), (n2, c2) = results
    col = 26
    lines = [
        f"{'':>{col}}  {n1[:col]:<{col}}  {n2[:col]:<{col}}",
        "─" * (col * 3 + 6),
        f"{'Condition':<{col}}  {WMO_CODES.get(c1['weather_code'], '?'):<{col}}  {WMO_CODES.get(c2['weather_code'], '?'):<{col}}",
        f"{'Temperature':<{col}}  {c1['temperature_2m']:>{col-2}}°C  {c2['temperature_2m']:>{col-2}}°C",
        f"{'Feels like':<{col}}  {c1['apparent_temperature']:>{col-2}}°C  {c2['apparent_temperature']:>{col-2}}°C",
        f"{'Humidity':<{col}}  {c1['relative_humidity_2m']:>{col-2}}%   {c2['relative_humidity_2m']:>{col-2}}%",
        f"{'Wind':<{col}}  {c1['wind_speed_10m']:>{col-2}} km/h  {c2['wind_speed_10m']:>{col-2}} km/h",
        f"{'Precipitation':<{col}}  {c1['precipitation']:>{col-2}} mm   {c2['precipitation']:>{col-2}} mm",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse")
