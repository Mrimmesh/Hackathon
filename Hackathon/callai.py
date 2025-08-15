import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
Gemini_API_KEY = os.getenv("Gemini_API_KEY")
if not Gemini_API_KEY:
    raise Exception("Missing Gemini_API_KEY in environment variables")

genai.configure(api_key=Gemini_API_KEY)

def msg(text: str) -> str:
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(text)
    return response.text.strip()
