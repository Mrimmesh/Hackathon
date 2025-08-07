import requests
import json

def get_weather_data(lat, lon):
    try:
        api_key = '433318bae28b4767920164042250708'  
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={lat},{lon}"
        response = requests.get(url)
        data = response.json()

        location_name = f"{data['location']['name']} {data['location']['country']}"
        temperature = data['current']['temp_c']
        condition = data['current']['condition']['text']

        weather_json = {
            "location": {
                "name": location_name,
                "latitude": lat,
                "longitude": lon
            },
            "temperature_celsius": temperature,
            "weather": condition
        }

        return weather_json

    except Exception as e:
        return {"error": str(e)}

latitude = input("Enter latitude: ")
longitude = input("Enter longitude: ")

result = get_weather_data(latitude, longitude)
print(json.dumps(result, indent=2))
