
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        try {
            const response = await fetch("http://127.0.0.1:2070/get_weather", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    latitude: latitude,
                    longitude: longitude
                })
            });

            const data = await response.json();
            console.log("Weather + Altitude Data:", data);
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, (error) => {
        console.error("Geolocation error:", error);
    });
} else {
    console.error("Geolocation not supported by this browser.");
}
