from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_MODEL = "accounts/fireworks/models/deepseek-v4-pro"

def get_fireworks_config() -> dict:
    """Returns the API URL, headers, and model name for Fireworks AI."""
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise EnvironmentError("FIREWORKS_API_KEY is not set. Check your .env file.")
        
    model_name = os.getenv("FIREWORKS_MODEL", _DEFAULT_MODEL)
    
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    return {
        "url": url,
        "headers": headers,
        "model": model_name
    }
