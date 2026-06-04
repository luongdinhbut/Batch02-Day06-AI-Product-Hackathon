# Hanoi Travel Itinerary Chatbot

Streamlit prototype for first-time Hanoi visitors.

## Run

```bash
cd codebase
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Optional AI setup:

```bash
$env:LLM_PROVIDER="fireworks"
$env:FIREWORKS_API_KEY="your_key_here"
$env:FIREWORKS_MODEL="accounts/fireworks/models/deepseek-v4-pro"
```

Without an API key, the app still runs and generates a safe local fallback itinerary.

Other providers:

```bash
$env:LLM_PROVIDER="gemini"
$env:GEMINI_API_KEY="your_key_here"
$env:GEMINI_MODEL="gemini-2.0-flash"

$env:LLM_PROVIDER="custom"
$env:CUSTOM_API_KEY="your_key_here"
$env:CUSTOM_BASE_URL="https://your-provider.example.com/v1"
$env:CUSTOM_MODEL="your_model_name"
```

## What it supports

- 5 preference questions
- Local Hanoi data from `data/hanoi_places.json`
- 1-day itinerary with morning, lunch, afternoon, dinner, evening
- Monday / closed-place guardrail in Python
- Warning plus alternatives for closed places
- Correction flow after itinerary generation
- Fireworks, Gemini, or custom OpenAI-compatible AI call with local fallback

## Test

```bash
cd codebase
python -m unittest discover -s tests
```
