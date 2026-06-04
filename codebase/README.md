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
$env:GEMINI_API_KEY="your_key_here"
$env:GEMINI_MODEL="gemini-3.1-flash-lite"
$env:LLM_PROVIDER="google,custom"
```

Without `GEMINI_API_KEY`, the app still runs with local fallback logic and shows a setup warning. The app also accepts `GOOGLE_API_KEY` or `GOOGLE_AI_API_KEY`.

Optional custom OpenAI-compatible fallback:

```bash
$env:CUSTOM_API_KEY="your_key_here"
$env:CUSTOM_API_BASE_URL="https://your-provider.example.com/v1"
$env:CUSTOM_MODEL="your_model_name"
```

## What it supports

- 5 preference questions
- Local Hanoi data from `data/hanoi_places.json`
- 1-day itinerary with morning, lunch, afternoon, dinner, evening
- Monday / closed-place guardrail in Python
- Warning plus alternatives for closed places
- Correction flow: add cafe, remove bar, change to Hoan Kiem, make cheaper
- Gemini or custom OpenAI-compatible call for AI enrichment when API key is present

## Test

```bash
cd codebase
python -m unittest discover -s tests
```
