import requests
import json
import time

# response.raise_for_status() if needed 

def fetchLocation():
    result = {}
    try:
        response = requests.get('https://api.ipify.org?format=json')
        data = response.json()
        ip = data['ip']
        result['ip_address'] = ip

        response = requests.get(f'https://freegeoip.app/json/{ip}')
        data = response.json()
        city = data.get('city', 'Unknown')
        latitude = data.get('latitude', None)
        longitude = data.get('longitude', None)
        result['location'] = city
        result['latitude'] = latitude
        result['longitude'] = longitude

        if latitude is not None and longitude is not None:
            url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true'
            response = requests.get(url)
            data = response.json()
            current = data['current_weather']
            temperature = current.get('temperature', 'error')
            weather_code = current.get('weathercode', 'error')
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                51: "Light drizzle",
                61: "Light rain",
                63: "Moderate rain",
                80: "Rain showers",
                95: "Thunderstorm"
            }
            result['current_weather'] = weather_codes.get(weather_code, "error getting weather ;-;")
            result['temperature_celsius'] = temperature
        else:
            result['error'] = "Cannot fetch weather: Invalid latitude or longitude"
        return json.dumps(result)
    except requests.RequestException as e:
        return json.dumps({"error": f"Request failed: {e}"})

if __name__ == "__main__":
    print(fetchLocation())