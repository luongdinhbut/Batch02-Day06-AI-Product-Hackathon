import os
from pathlib import Path

import streamlit as st

from itinerary import (
    apply_correction,
    build_fallback_itinerary,
    build_preferences,
    call_gemini,
    detect_uncertain_preferences,
    load_data,
    render_itinerary,
)


BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "hanoi_places.json"
ENV_PATHS = [BASE_DIR / ".env", BASE_DIR.parent / ".env"]

QUESTIONS = [
    ("food_style", "Food style", ["Street food", "Restaurant", "Local hidden gem", "Anything"]),
    ("sightseeing", "Sightseeing", ["Culture/history", "Shopping/fun", "Chill cafe", "Balanced"]),
    ("local_style", "Travel style", ["Local", "Tourist-friendly", "Mixed"]),
    ("budget", "Budget/day", ["Under 500k", "500k-1tr", "Over 1tr"]),
    ("travel_date", "Travel date", None),
]


def load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


for env_path in ENV_PATHS:
    load_env_file(env_path)

st.set_page_config(page_title="Hanoi 1-Day AI Itinerary", layout="wide")
st.title("Hanoi 1-Day AI Itinerary Chatbot")
st.caption("For first-time Hanoi visitors. Uses local place data and a closed-place guardrail.")

data = load_data(DATA_PATH)

with st.sidebar:
    st.header("5 preference questions")
    answers = {}
    for key, label, options in QUESTIONS:
        if options:
            answers[key] = st.selectbox(label, options)
        else:
            answers[key] = st.date_input(label)
    answers["nightlife"] = st.checkbox("Add evening bar/pub", value=True)
    generate = st.button("Generate itinerary", type="primary")

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None
if "preferences" not in st.session_state:
    st.session_state.preferences = None
if "ai_note" not in st.session_state:
    st.session_state.ai_note = ""

if generate:
    prefs = build_preferences(answers)
    st.session_state.preferences = prefs
    itinerary = build_fallback_itinerary(data, prefs)

    # Critical demo flow: real AI call enriches at least one generated itinerary.
    ai_text, ai_note = call_gemini(data, prefs, itinerary)
    itinerary["ai_text"] = ai_text
    st.session_state.ai_note = ai_note
    st.session_state.itinerary = itinerary

if st.session_state.itinerary:
    itinerary = st.session_state.itinerary
    prefs = st.session_state.preferences

    if st.session_state.ai_note:
        st.info(st.session_state.ai_note)
    if detect_uncertain_preferences(prefs):
        st.warning("Input is broad, so this is a balanced itinerary. For a sharper plan, say what you want to change.")
    for warning in itinerary["warnings"]:
        st.warning(warning)

    st.markdown(render_itinerary(itinerary), unsafe_allow_html=False)

    if itinerary.get("ai_text"):
        with st.expander("AI draft / enrichment"):
            st.write(itinerary["ai_text"])

    st.subheader("Correction without restarting")
    correction = st.chat_input("Try: add a cafe, remove bar, change to Hoan Kiem, make it cheaper")
    if correction:
        st.session_state.itinerary = apply_correction(data, prefs, itinerary, correction)
        st.rerun()
else:
    st.info("Answer the 5 questions, then generate a demo-ready 1-day itinerary.")
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")):
        st.warning("Missing GEMINI_API_KEY. App still runs with local fallback; add it to .env, codebase/.env, or your shell for AI enrichment.")
