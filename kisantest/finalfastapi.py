from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta, timezone
import logging
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocationInput(BaseModel):
    latitude: float
    longitude: float

def get_annual_rainfall(lat, lon):
    today = datetime.now(timezone.utc).date()
    one_year_ago = today - timedelta(days=365)
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={one_year_ago}&end_date={today}"
        "&daily=precipitation_sum&timezone=UTC"
    )
    response = requests.get(url, timeout=10)    #for annual rainfall
    response.raise_for_status()
    data = response.json()
    if "daily" in data and "precipitation_sum" in data["daily"]:
        total_rainfall = sum(p for p in data["daily"]["precipitation_sum"] if p is not None)
        return round(total_rainfall, 2)
    raise ValueError("No precipitation data found.")

def fetch_altitude(lat, lon):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"#for altitude
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["elevation"]
    raise ValueError("No elevation data found.")

def fetch_current_weather(lat, lon):
    weather_api_key = "433318bae28b4767920164042250708"
    url = f"https://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={lat},{lon}"#for location temperature and weather
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise ValueError(f"Weather API error: {data['error']['message']}")
    return data

@app.post("/getdata")
async def get_weather_endpoint(request: Request):
    try:
        data = await request.json()
        input_data = LocationInput(**data)
        lat = input_data.latitude
        lon = input_data.longitude
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude")
        current_month = datetime.utcnow().month
        with ThreadPoolExecutor() as executor:
            rainfall_future = executor.submit(get_annual_rainfall, lat, lon)
            altitude_future = executor.submit(fetch_altitude, lat, lon)
            current_weather_future = executor.submit(fetch_current_weather, lat, lon)
            annual_rainfall = rainfall_future.result()
            altitude = altitude_future.result()
            current_weather_data = current_weather_future.result()
        location_name = current_weather_data["location"]["name"]
        country = current_weather_data["location"]["country"]
        temperature = current_weather_data["current"]["temp_c"]
        condition = current_weather_data["current"]["condition"]["text"]
        response_data = {
            "location": {
                "name": location_name,
                "country": country
            },
            "latitude": lat,
            "longitude": lon,
            "altitude": altitude,
            "temp": temperature,
            "weather": condition,
            "rainfall": annual_rainfall,
            "month": current_month
        }
        logger.info("Response data for lat=%s, lon=%s: %s", lat, lon, response_data)
    except ValueError as ve:
        logger.error("Validation error: %s", str(ve))
        return JSONResponse(content={"error": str(ve)}, status_code=400)
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2070)