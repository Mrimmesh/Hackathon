from fastapi import FastAPI
from recom import recommend_crops
import pandas as pd
from callai import msg
from Bestcrop import get_crop_recommendations


app = FastAPI()

# Load data (not used here directly, but assuming needed)
df = pd.read_csv('Datasets/crop_ecology_data.csv')

@app.get("/recommend-crops/")
async def get_crop_recommendations(
    temp: float,
    rainfall: float,
    ph: float,
    latitude: float,
    altitude: float,
    month: int
):
    # Call the function to get recommendations
    final_message = get_crop_recommendations(temp, rainfall, ph, latitude, altitude, month)
    
    return {"message": final_message}



