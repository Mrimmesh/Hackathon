import pandas as pd
import numpy as np


try:
    df = pd.read_csv('Datasets/crop_ecology_data.csv')
except FileNotFoundError:
    print("File not found")
    df = pd.DataFrame()

df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

def recommend_crops(temp, rainfall, ph, latitude, altitude, month, df=df):
    "Best fit crops based on temperature, rainfall, and soil pH."
    scores = []

    for crop in df.itertuples():
        score = 0

        # Temperature scoring
        if crop.Ecology_Temp_Optimal_Min <= temp <= crop.Ecology_Temp_Optimal_Max:
            score += 3
        elif crop.Ecology_Temp_Absolute_Min <= temp <= crop.Ecology_Temp_Absolute_Max:
            score += 1
        else:
            score -= 100

        # Rainfall scoring
        if crop.Ecology_Rainfall_Annual_Optimal_Min <= rainfall <= crop.Ecology_Rainfall_Annual_Optimal_Max:
            score += 3
        elif crop.Ecology_Rainfall_Annual_Absolute_Min <= rainfall <= crop.Ecology_Rainfall_Annual_Absolute_Max:
            score += 1
        else:
            score -= 100
        
        # Soil pH scoring
        if crop.Ecology_Soil_PH_Optimal_Min <= ph <= crop.Ecology_Soil_PH_Optimal_Max:
            score += 3
        elif crop.Ecology_Soil_PH_Absolute_Min <= ph <= crop.Ecology_Soil_PH_Absolute_Max:
            score += 1
        else:
            score -= 100
        
        # Latitude scoring
        if crop.Ecology_Latitude_Optimal_Min <= latitude <= crop.Ecology_Latitude_Optimal_Max:
            score += 3
        elif crop.Ecology_Latitude_Absolute_Min <= latitude <= crop.Ecology_Latitude_Absolute_Max:
            score += 1
        else:
            score -= 100
        
        # Altitude scoring
        if crop.Ecology_Altitude_Optimal_Min <= altitude <= crop.Ecology_Altitude_Optimal_Max:
            score += 3
        elif crop.Ecology_Altitude_Absolute_Min <= altitude <= crop.Ecology_Altitude_Absolute_Max:
            score += 1
        else:
            score -= 100

        # Month-based scoring for planting
        is_planting_season = False
        if crop.Planting_Start_Month <= crop.Planting_End_Month:
            if crop.Planting_Start_Month <= month <= crop.Planting_End_Month:
                is_planting_season = True
        else:  # Handles planting seasons that wrap around the new year
            if month >= crop.Planting_Start_Month or month <= crop.Planting_End_Month:
                is_planting_season = True
        
        if is_planting_season:
            score += 15

        # Month-based scoring for harvesting
        is_harvesting_season = False
        if crop.Harvesting_Start_Month <= crop.Harvesting_End_Month:
            if crop.Harvesting_Start_Month <= month <= crop.Harvesting_End_Month:
                is_harvesting_season = True
        else:  # Handles harvesting seasons that wrap around the new year
            if month >= crop.Harvesting_Start_Month or month <= crop.Harvesting_End_Month:
                is_harvesting_season = True

        if is_harvesting_season:
            score += 15
        
        if score > 0:
            scores.append({'Crop': crop.Crop, 'Score': score})

    if not scores:
        return pd.DataFrame(columns=['Crop', 'Score'])

    results_df = pd.DataFrame(scores)
    ranked_results = results_df.sort_values(by='Score', ascending=False)
    return ranked_results


