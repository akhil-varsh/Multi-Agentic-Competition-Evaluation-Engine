import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# We will use the new genai Client. The API key is picked up from environment variables.
def get_client() -> genai.Client:
    return genai.Client()

def get_text_model() -> str:
    # Use Flash-Lite to avoid strict quota limits on Pro
    return "gemini-3.1-flash-lite-preview"

def get_multimodal_model() -> str:
    # Use Flash to avoid strict quota limits on Pro and support images well
    return "gemini-3.1-flash-image-preview"
