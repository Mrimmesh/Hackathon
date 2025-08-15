from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime, timedelta, timezone
import logging
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np

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

try:
    df = pd.read_csv('Datasets/crop_ecology_data.csv')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
except FileNotFoundError:
    logger.error("Crop ecology CSV file not found")
    df = pd.DataFrame()

class LocationInput(BaseModel):
    latitude: float
    longitude: float
    soil_ph: Optional[float] = None  

def get_annual_rainfall(lat, lon):
    today = datetime.now(timezone.utc).date()
    one_year_ago = today - timedelta(days=365)
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={one_year_ago}&end_date={today}"
        "&daily=precipitation_sum&timezone=UTC"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "daily" in data and "precipitation_sum" in data["daily"]:
        total_rainfall = sum(p for p in data["daily"]["precipitation_sum"] if p is not None)
        return round(total_rainfall, 2)
    raise ValueError("No precipitation data found.")

def fetch_altitude(lat, lon):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["elevation"]
    raise ValueError("No elevation data found.")

def fetch_current_weather(lat, lon):
    weather_api_key = "433318bae28b4767920164042250708"
    url = f"https://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={lat},{lon}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise ValueError(f"Weather API error: {data['error']['message']}")
    return data

def recommend_crops(temp, rainfall, ph, latitude, altitude, month, df=df):
    scores = []
    for crop in df.itertuples():
        score = 0
        if crop.Ecology_Temp_Optimal_Min <= temp <= crop.Ecology_Temp_Optimal_Max:
            score += 3
        elif crop.Ecology_Temp_Absolute_Min <= temp <= crop.Ecology_Temp_Absolute_Max:
            score += 1
        else:
            score -= 100
        if crop.Ecology_Rainfall_Annual_Optimal_Min <= rainfall <= crop.Ecology_Rainfall_Annual_Optimal_Max:
            score += 3
        elif crop.Ecology_Rainfall_Annual_Absolute_Min <= rainfall <= crop.Ecology_Rainfall_Annual_Absolute_Max:
            score += 1
        else:
            score -= 100
        if ph is not None: 
            if crop.Ecology_Soil_PH_Optimal_Min <= ph <= crop.Ecology_Soil_PH_Optimal_Max:
                score += 3
            elif crop.Ecology_Soil_PH_Absolute_Min <= ph <= crop.Ecology_Soil_PH_Absolute_Max:
                score += 1
            else:
                score -= 100
        if crop.Ecology_Latitude_Optimal_Min <= latitude <= crop.Ecology_Latitude_Optimal_Max:
            score += 3
        elif crop.Ecology_Latitude_Absolute_Min <= latitude <= crop.Ecology_Latitude_Absolute_Max:
            score += 1
        else:
            score -= 100
        if crop.Ecology_Altitude_Optimal_Min <= altitude <= crop.Ecology_Altitude_Optimal_Max:
            score += 3
        elif crop.Ecology_Altitude_Absolute_Min <= altitude <= crop.Ecology_Altitude_Absolute_Max:
            score += 1
        else:
            score -= 100
        is_planting_season = False
        if crop.Planting_Start_Month <= crop.Planting_End_Month:
            if crop.Planting_Start_Month <= month <= crop.Planting_End_Month:
                is_planting_season = True
        else:
            if month >= crop.Planting_Start_Month or month <= crop.Planting_End_Month:
                is_planting_season = True
        if is_planting_season:
            score += 15
        is_harvesting_season = False
        if crop.Harvesting_Start_Month <= crop.Harvesting_End_Month:
            if crop.Harvesting_Start_Month <= month <= crop.Harvesting_End_Month:
                is_harvesting_season = True
        else:
            if month >= crop.Harvesting_Start_Month or month <= crop.Harvesting_End_Month:
                is_harvesting_season = True
        if is_harvesting_season:
            score += 15
        if score > 0:
            scores.append({'Crop': crop.Crop, 'Score': score})
    if not scores:
        return pd.DataFrame(columns=['Crop', 'Score'])
    results_df = pd.DataFrame(scores)
    return results_df.sort_values(by='Score', ascending=False)

@app.post("/getdata")
async def get_weather_endpoint(request: Request):
    try:
        data = await request.json()
        input_data = LocationInput(**data)
        lat = input_data.latitude
        lon = input_data.longitude
        soil_ph = input_data.soil_ph
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude")
        if soil_ph is not None and not (0 <= soil_ph <= 14):
            raise ValueError("Soil pH must be between 0 and 14")
        current_month = datetime.now(timezone.utc).month
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
        crop_recommendations = recommend_crops(
            temp=temperature,
            rainfall=annual_rainfall,
            ph=soil_ph,
            latitude=lat,
            altitude=altitude,
            month=current_month
        )
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
            "month": current_month,
            "soil_ph": soil_ph,
            "crop_recommendations": crop_recommendations.to_dict(orient="records")
        }
        logger.info( response_data)
        return JSONResponse(content=response_data)
    except ValueError as ve:
        logger.error("Validation error: %s", str(ve))
        return JSONResponse(content={"error": str(ve)}, status_code=400)
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2070)