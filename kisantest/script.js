function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`)
                    .then(response => response.json())
                    .then(data => {
                        const weather = data.current_weather;
                        const temperature = weather.temperature;
                        const weatherCode = weather.weathercode;
                        const weatherDescriptions = {
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
                        };
                        const description = weatherDescriptions[weatherCode] || "Unknown weather";

                        document.getElementById('weather').innerText = 
                            `Location: (latitude: ${latitude.toFixed(2)}, longitude: ${longitude.toFixed(2)})\n` +
                            `Temperature: ${temperature}°C\n` +
                            `Weather: ${description}`;

                        const weatherData = {
                            location: {
                                latitude: latitude.toFixed(2),
                                longitude: longitude.toFixed(2)
                            },
                            temperature_celsius: temperature,
                            weather: description
                        };
                        console.log('weatherdata:', weatherData);

                        const jsonString = JSON.stringify(weatherData, null, 2);
                        const blob = new Blob([jsonString], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = 'weather_data.json';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                    })
                    .catch(error => {
                        console.error("Error fetching weather:", error);
                        document.getElementById('weather').innerText = "Error fetching weather data.";
                    });
            },
            (error) => {
                console.error("Geolocation error:", error);
                document.getElementById('weather').innerText = "Unable to retrieve location. Please allow location access.";
            }
        );
    } else {
        document.getElementById('weather').innerText = "Geolocation is not supported by this browser.";
    }
}