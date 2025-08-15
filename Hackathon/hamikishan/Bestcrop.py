from callai import msg
from recom import recommend_crops

def get_crop_recommendations(
    temp: float,
    rainfall: float,
    ph: float,
    latitude: float,
    altitude: float,
    month: int
):
    # Get recommendations DataFrame
    recommendations = recommend_crops(temp, rainfall, ph, latitude, altitude, month)

    # Extract crop names as a comma-separated string
    crop_list = recommendations['Crop'].tolist()
    crop_string = ", ".join(crop_list)

    # Create prompt using f-string
    messagetoai = f"""
    You are an expert in agriculture and crop recommendations.
    Based on the following conditions, suggest the best crops to plant:
    Temperature: {temp}°C , Rainfall: {rainfall}mm, Soil pH: {ph}, Latitude: {latitude}°N, Altitude: {altitude}m, Month: {month}
    Our system has identified the following crops as suitable: {crop_string}.
    Now your job is to provide a detailed explanation of why these crops are suitable for the given conditions.
    You don't need to mention the scores but you can just mention which crops to grow — in descending order of suitability.
    """

    # Generate model response (make sure `msg()` is your generative AI call)
    final = msg(messagetoai)
    return final


# Example call
message = get_crop_recommendations(
    temp=25,
    rainfall=1000,
    ph=6.5,
    latitude=10,
    altitude=500,
    month=6
)

print(message)
