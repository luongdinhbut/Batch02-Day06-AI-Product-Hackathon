import streamlit as st
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Add src/ to path so existing modules work with their relative imports
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.schemas import SessionState, OnboardingStep, ChatMessage
from services.onboarding import (
    GREETING, get_question, process_answer,
)
from services.prompt_builder import build_confirmation_message, build_itinerary_request
from services.chat_engine import ChatEngine
from services.failure_checker import get_closed_places, build_closure_warning
from utils.date_utils import to_vn_day

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="HaNoi Guide — AI Travel Agent",
    page_icon="🗺️",
    layout="wide",
)

# ─────────────────────────────────────────────
# Custom CSS — premium look
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    /* Chat messages */
    .stChatMessage {
        border-radius: 16px !important;
        margin-bottom: 12px !important;
        backdrop-filter: blur(10px);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #e0e0e0;
    }

    /* Chat input */
    .stChatInput > div {
        border-radius: 24px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }

    /* Title glow */
    h1 {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #f7971e, #ffd200) !important;
        color: #1a1a2e !important;
        border: none !important;
        border-radius: 24px !important;
        font-weight: 700 !important;
    }

    /* Status badges in sidebar */
    .pref-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        margin: 2px 0;
    }
    .pref-done { background: rgba(76,175,80,0.25); color: #66bb6a; }
    .pref-pending { background: rgba(255,255,255,0.08); color: #888; }

    /* Warning box */
    .closure-warn {
        background: rgba(255,152,0,0.15);
        border-left: 4px solid #ff9800;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────
if "session" not in st.session_state:
    st.session_state.session = SessionState()
if "ui_messages" not in st.session_state:
    # UI messages = what the user SEES (greeting + Q&A + itinerary)
    st.session_state.ui_messages = []
if "engine" not in st.session_state:
    st.session_state.engine = None
if "booted" not in st.session_state:
    st.session_state.booted = False
if "generating" not in st.session_state:
    st.session_state.generating = False

session: SessionState = st.session_state.session


# ─────────────────────────────────────────────
# Helper: append message to UI
# ─────────────────────────────────────────────
def add_msg(role: str, content: str):
    st.session_state.ui_messages.append({"role": role, "content": content})


# ─────────────────────────────────────────────
# Boot: greeting + first question
# ─────────────────────────────────────────────
if not st.session_state.booted:
    add_msg("assistant", GREETING)
    add_msg("assistant", get_question(OnboardingStep.food_style))
    st.session_state.booted = True


# ─────────────────────────────────────────────
# Sidebar: live preference summary
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Hanoi_Hoan_Kiem_Lake.jpg/640px-Hanoi_Hoan_Kiem_Lake.jpg", use_container_width=True)
    st.markdown("## 🗺️ HaNoi Guide")
    st.caption("AI Travel Agent · 179 địa điểm thực")
    st.divider()

    pref = session.preference

    def _badge(label, value, done):
        cls = "pref-done" if done else "pref-pending"
        val = value if done else "chưa chọn"
        return f'<span class="pref-badge {cls}">{label}: {val}</span>'

    st.markdown("#### 📋 Sở thích của bạn", unsafe_allow_html=True)
    st.markdown(
        _badge("🍜 Ăn uống", str(pref.food_style.value).replace("_", " ") if pref.food_style else "", pref.food_style is not None) + "<br>" +
        _badge("🏛️ Tham quan", str(pref.place_type.value).replace("_", " ") if pref.place_type else "", pref.place_type is not None) + "<br>" +
        _badge("🎯 Phong cách", str(pref.experience.value) if pref.experience else "", pref.experience is not None) + "<br>" +
        _badge("💰 Ngân sách", str(pref.budget.value) if pref.budget else "", pref.budget is not None) + "<br>" +
        _badge("📅 Ngày đến", to_vn_day(pref.arrival_day_of_week) if pref.arrival_day_of_week else "", pref.arrival_day_of_week is not None),
        unsafe_allow_html=True,
    )

    # Closure warnings
    if pref.arrival_day_of_week:
        closed = get_closed_places(pref.arrival_day_of_week)
        if closed:
            st.divider()
            st.markdown("#### ⚠️ Địa điểm đóng cửa")
            for p in closed:
                st.markdown(
                    f'<div class="closure-warn">🚫 <b>{p["name"]}</b><br>'
                    f'<small>{p.get("district", "")} — đóng cửa {to_vn_day(pref.arrival_day_of_week)}</small></div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    if st.button("🔄 Bắt đầu lại", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────
# Main: Title
# ─────────────────────────────────────────────
st.title("🗺️ HaNoi Guide")
st.caption("Chatbot AI tạo lịch trình du lịch Hà Nội cá nhân hóa — tham quan + ăn uống + nightlife")


# ─────────────────────────────────────────────
# Render chat history
# ─────────────────────────────────────────────
for msg in st.session_state.ui_messages:
    avatar = "🗺️" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# ─────────────────────────────────────────────
# Chat input handler
# ─────────────────────────────────────────────
if prompt := st.chat_input("Nhắn tin cho HaNoi Guide..."):
    # Show user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    add_msg("user", prompt)

    step = session.preference.onboarding_step

    # ── CASE 1: Still onboarding (steps 1-5) ──
    if step != OnboardingStep.done:
        new_pref, retry_msg = process_answer(session.preference, prompt)
        session.preference = new_pref
        st.session_state.session = session

        if retry_msg:
            # Ambiguous answer → ask again
            with st.chat_message("assistant", avatar="🗺️"):
                st.markdown(retry_msg)
            add_msg("assistant", retry_msg)

        elif new_pref.onboarding_step == OnboardingStep.done:
            # All 5 answered → show confirmation → generate itinerary
            confirmation = build_confirmation_message(new_pref)
            with st.chat_message("assistant", avatar="🗺️"):
                st.markdown(confirmation)
            add_msg("assistant", confirmation)

            # Generate itinerary
            with st.chat_message("assistant", avatar="🗺️"):
                with st.spinner("🧠 AI đang tạo lịch trình tối ưu cho bạn..."):
                    try:
                        engine = ChatEngine(session)
                        itinerary_request = build_itinerary_request(new_pref)
                        reply = engine.send_raw(itinerary_request)
                        st.session_state.engine = engine
                        session.itinerary_generated = True
                        st.markdown(reply)
                        add_msg("assistant", reply)
                    except Exception as e:
                        err = f"❌ Lỗi kết nối AI: {e}\n\nHãy kiểm tra `FIREWORKS_API_KEY` trong file `.env`."
                        st.error(err)
                        add_msg("assistant", err)

        else:
            # Move to next question
            next_q = get_question(new_pref.onboarding_step)
            with st.chat_message("assistant", avatar="🗺️"):
                st.markdown(next_q)
            add_msg("assistant", next_q)

        st.rerun()

    # ── CASE 2: Itinerary done → correction path ──
    else:
        engine = st.session_state.engine
        if engine is None:
            # Edge case: engine lost, rebuild
            engine = ChatEngine(session)
            st.session_state.engine = engine

        with st.chat_message("assistant", avatar="🗺️"):
            with st.spinner("Đang cập nhật lịch trình..."):
                try:
                    reply = engine.send(prompt)
                    st.markdown(reply)
                    add_msg("assistant", reply)
                except Exception as e:
                    err = f"❌ Lỗi: {e}"
                    st.error(err)
                    add_msg("assistant", err)

        st.rerun()
