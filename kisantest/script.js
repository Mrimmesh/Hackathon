function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                try {
                    const apiKey = '433318bae28b4767920164042250708';  
                    const weatherResponse = await fetch(`https://api.weatherapi.com/v1/current.json?key=${apiKey}&q=${latitude},${longitude}`);
                    const weatherData = await weatherResponse.json();

                    const temperature = weatherData.current.temp_c;
                    const condition = weatherData.current.condition.text;
                    const placeName = weatherData.location.name + ', ' + weatherData.location.country;

                    const weatherPayload = {
                        location: {
                            name: placeName,
                            latitude: latitude.toFixed(2),
                            longitude: longitude.toFixed(2)
                        },
                        temperature_celsius: temperature,
                        weather: condition
                    };

                    console.log(weatherPayload);

                } catch (error) {
                    console.error("Error fetching weather:", error);
                }
            },
            (error) => {
                console.error("Geolocation error:", error);
            }
        );
    } else {
        console.error("Geolocation is not supported by this browser.");
    }
}
