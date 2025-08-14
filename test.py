from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import requests

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

def fetch_weather(lat, lon):
    weather_api_key = '433318bae28b4767920164042250708'
    url = f"https://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={lat},{lon}"
    response = requests.get(url)
    return response.json()

def fetch_altitude(lat, lon):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    response = requests.get(url)
    return response.json()

@app.post("/getdata")
async def get_weather_endpoint(request: Request):
    try:
        data = await request.json()
        lat = str(data.get("latitude"))
        lon = str(data.get("longitude"))

        with ThreadPoolExecutor() as executor:
            weather_future = executor.submit(fetch_weather, lat, lon)
            altitude_future = executor.submit(fetch_altitude, lat, lon)

            weather_data = weather_future.result()
            elevation_data = altitude_future.result()

        altitude = elevation_data['results'][0]['elevation']
        location_name = f"{weather_data['location']['name']} {weather_data['location']['country']}"
        temperature = weather_data['current']['temp_c']
        condition = weather_data['current']['condition']['text']

        return JSONResponse(content={
            "location": {
                "name": location_name,
                "latitude": lat,
                "longitude": lon,
                "altitude_meters": altitude
            },
            "temperature_celsius": temperature,
            "weather": condition
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2070)
