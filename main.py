from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from collections import defaultdict
from datetime import datetime, timedelta
import google.generativeai as genai



app = FastAPI()

def LLM_rating(startup_name: str, ratings: List[dict]) -> float:
    """
    Calculate the LLM rating for a startup based on its name and ratings.
    """
    # Prepare the prompt for the LLM
    prompt = f"Rate the startup '{startup_name}' based on the following ratings:\n"
    for rating in ratings:
        prompt += f"{rating['type']}: {rating['value']}\n"
    
    # Call the LLM to get the rating
    response = genai.generate_text(prompt=prompt)
    return float(response.text.strip())



weights = {"views": 3, "likes": 7, "comment": 10}

client = AsyncIOMotorClient("mongodb+srv://shitalgautam34:XunxpPQTCbNePuUK@cluster0.e7fkuyl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["rate_my_startup"]



@app.route("/api/startups/rate", methods=["GET"])
async def rate_startups():
    # Get the startup ratings from the database
    ratings = await db["ratings"].find().to_list(100)

