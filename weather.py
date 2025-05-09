from typing import Any
import os
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise RuntimeError("API-ключ не задан в .env")

OWM_API_BASE = "https://api.openweathermap.org/data/2.5"
mcp = FastMCP("weather")

async def owm_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any] | None:
    url = f"{OWM_API_BASE}/{endpoint}"
    params.update({"appid": API_KEY, "units": "metric", "lang": "en"})
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=15.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return None


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    Возвращает текущую погоду в городе.
    Пример: city="Belgrade,RS" или "Paris,FR"
    """
    data = await owm_request("weather", {"q": city})
    if not data:
        return "Не удалось получить данные."
    main = data["main"]
    weather = data["weather"][0]
    return (
        f"Погода в {data['name']}:\n"
        f"{weather['description'].capitalize()}\n"
        f"Температура: {main['temp']}°C (ощущается как {main['feels_like']}°C)\n"
        f"Влажность: {main['humidity']}%\n"
        f"Давление: {main['pressure']} hPa"
    )

@mcp.tool()
async def get_forecast(lat: float, lon: float) -> str:
    """
    Возвращает краткий 5-дневный прогноз для координат.
    """
    data = await owm_request("forecast", {"lat": lat, "lon": lon})
    if not data:
        return "Не удалось получить прогноз."
    # Выбираем первые 5 записей (через 3 часа)
    periods = data["list"][:5]
    lines = []
    for p in periods:
        dt = p["dt_txt"]
        desc = p["weather"][0]["description"].capitalize()
        temp = p["main"]["temp"]
        lines.append(f"{dt} — {desc}, {temp}°C")
    return "\n".join(lines)

if __name__ == "__main__":
    # Initialize and run the server
    print("MCP was start STDIO…")
    mcp.run(transport='stdio')