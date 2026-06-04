from __future__ import annotations

import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_MODEL = "gemini-2.0-flash"


def build_model_with_system(system_instruction: str) -> genai.GenerativeModel:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is not set. Check your .env file.")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
    )
