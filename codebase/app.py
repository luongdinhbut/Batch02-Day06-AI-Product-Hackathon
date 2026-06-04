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
    page_icon="🧭",
    layout="wide",
)

# ─────────────────────────────────────────────
# Custom CSS — premium light theme & HTML chats
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean layout & typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    body, .stApp {
        background-color: #f8fafc !important;
        color: #1e293b !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    /* Custom Chat Container */
    .chat-container {
        display: flex;
        margin-bottom: 20px;
        gap: 12px;
        align-items: flex-start;
    }
    .chat-container.assistant {
        justify-content: flex-start;
    }
    .chat-container.user {
        justify-content: flex-end;
    }
    
    /* Avatars */
    .chat-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 13px;
        flex-shrink: 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .chat-avatar.assistant-avatar {
        background-color: #0f172a;
        color: #ffffff;
    }
    .chat-avatar.user-avatar {
        background-color: #e2e8f0;
        color: #334155;
        border: 1px solid #cbd5e1;
    }
    
    /* Bubbles */
    .chat-bubble {
        max-width: 80%;
        padding: 12px 18px;
        border-radius: 16px;
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.04);
    }
    .chat-bubble-assistant {
        background-color: #ffffff;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        border-top-left-radius: 4px;
    }
    .chat-bubble-user {
        background-color: #f1f5f9;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        border-top-right-radius: 4px;
    }
    
    /* Format markdown inside custom bubbles */
    .chat-bubble p {
        margin: 0 0 10px 0 !important;
        color: #1e293b !important;
    }
    .chat-bubble p:last-child {
        margin-bottom: 0 !important;
    }
    .chat-bubble ul, .chat-bubble ol {
        margin: 4px 0 10px 20px !important;
    }
    .chat-bubble li {
        margin-bottom: 4px !important;
        color: #1e293b !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h4 {
        color: #1e293b !important;
    }
    
    /* Title styling */
    h1 {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.025em;
    }
    
    /* Chat input styling */
    .stChatInput > div {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    .stChatInput textarea {
        color: #1e293b !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 6px 16px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    .stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
    }
    
    /* Image inside sidebar rounded corners */
    section[data-testid="stSidebar"] img {
        border-radius: 8px !important;
    }

    /* Badges in sidebar */
    .pref-badge {
        display: block;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.85em;
        margin: 6px 0;
        font-weight: 500;
    }
    .pref-done {
        background-color: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .pref-pending {
        background-color: #f8fafc;
        color: #64748b;
        border: 1px solid #e2e8f0;
    }

    /* Warning box */
    .closure-warn {
        background-color: #fffbeb;
        border-left: 4px solid #d97706;
        color: #92400e;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 8px 0;
        font-size: 0.9em;
        border-top: 1px solid #fef3c7;
        border-right: 1px solid #fef3c7;
        border-bottom: 1px solid #fef3c7;
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
# Helper: convert basic markdown to HTML
# ─────────────────────────────────────────────
def markdown_to_html(text: str) -> str:
    import re
    # Convert links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" style="color: #0f172a; text-decoration: underline; font-weight: 500;">\1</a>', text)
    # Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Convert italics
    text = re.sub(r'_\((.*?)\)_', r'<em>\1</em>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    
    # Handle list items
    lines = text.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('•') or stripped.startswith('- ') or stripped.startswith('* '):
            content_part = stripped[1:].strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                content_part = stripped[2:].strip()
            
            if not in_list:
                new_lines.append('<ul style="margin: 4px 0 8px 20px; padding-left: 0; list-style-type: disc;">')
                in_list = True
            new_lines.append(f'<li style="margin-bottom: 4px; color: #1e293b;">{content_part}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    
    text = '\n'.join(new_lines)
    text = text.replace('\n', '<br>')
    
    # Clean spacing around list items
    text = text.replace('</ul><br>', '</ul>')
    text = text.replace('<br><ul>', '<ul>')
    text = text.replace('<br><li>', '<li>')
    text = text.replace('</li><br>', '</li>')
    text = text.replace('<ul><br>', '<ul>')
    
    return text


# ─────────────────────────────────────────────
# Helper: render message as HTML bubble
# ─────────────────────────────────────────────
def render_html_message(role: str, content: str):
    html_content = markdown_to_html(content)
    if role == "assistant":
        avatar_html = '<div class="chat-avatar assistant-avatar">H</div>'
        bubble_html = f'<div class="chat-bubble chat-bubble-assistant">{html_content}</div>'
        msg_html = f'<div class="chat-container assistant">{avatar_html}{bubble_html}</div>'
    else:
        avatar_html = '<div class="chat-avatar user-avatar">U</div>'
        bubble_html = f'<div class="chat-bubble chat-bubble-user">{html_content}</div>'
        msg_html = f'<div class="chat-container user">{bubble_html}{avatar_html}</div>'
    st.markdown(msg_html, unsafe_allow_html=True)


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
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Hanoi_Hoan_Kiem_Lake.jpg/640px-Hanoi_Hoan_Kiem_Lake.jpg", use_column_width=True)
    st.markdown("## HaNoi Guide")
    st.caption("AI Travel Agent · 179 địa điểm thực")
    st.divider()

    pref = session.preference

    def _badge(label, value, done):
        cls = "pref-done" if done else "pref-pending"
        val = value if done else "chưa chọn"
        return f'<span class="pref-badge {cls}">{label}: {val}</span>'

    st.markdown("#### Sở thích của bạn", unsafe_allow_html=True)
    st.markdown(
        _badge("Ăn uống", str(pref.food_style.value).replace("_", " ") if pref.food_style else "", pref.food_style is not None) + "<br>" +
        _badge("Tham quan", str(pref.place_type.value).replace("_", " ") if pref.place_type else "", pref.place_type is not None) + "<br>" +
        _badge("Phong cách", str(pref.experience.value) if pref.experience else "", pref.experience is not None) + "<br>" +
        _badge("Ngân sách", str(pref.budget.value) if pref.budget else "", pref.budget is not None) + "<br>" +
        _badge("Ngày đến", to_vn_day(pref.arrival_day_of_week) if pref.arrival_day_of_week else "", pref.arrival_day_of_week is not None),
        unsafe_allow_html=True,
    )

    # Closure warnings
    if pref.arrival_day_of_week:
        closed = get_closed_places(pref.arrival_day_of_week)
        if closed:
            st.divider()
            st.markdown("#### Địa điểm đóng cửa")
            for p in closed:
                st.markdown(
                    f'<div class="closure-warn"><b>{p["name"]}</b><br>'
                    f'<small>{p.get("district", "")} - đóng cửa {to_vn_day(pref.arrival_day_of_week)}</small></div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    if st.button("Bắt đầu lại", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────
# Main: Title
# ─────────────────────────────────────────────
st.title("HaNoi Guide")
st.caption("Chatbot AI tạo lịch trình du lịch Hà Nội cá nhân hóa — tham quan + ăn uống + nightlife")


# ─────────────────────────────────────────────
# Render chat history
# ─────────────────────────────────────────────
for msg in st.session_state.ui_messages:
    render_html_message(msg["role"], msg["content"])


# ─────────────────────────────────────────────
# Chat input handler
# ─────────────────────────────────────────────
if prompt := st.chat_input("Nhắn tin cho HaNoi Guide..."):
    # Show user message
    render_html_message("user", prompt)
    add_msg("user", prompt)

    step = session.preference.onboarding_step

    # ── CASE 1: Still onboarding (steps 1-5) ──
    if step != OnboardingStep.done:
        new_pref, retry_msg = process_answer(session.preference, prompt)
        session.preference = new_pref
        st.session_state.session = session

        if retry_msg:
            # Ambiguous answer → ask again
            render_html_message("assistant", retry_msg)
            add_msg("assistant", retry_msg)

        elif new_pref.onboarding_step == OnboardingStep.done:
            # All 5 answered → show confirmation → generate itinerary
            confirmation = build_confirmation_message(new_pref)
            render_html_message("assistant", confirmation)
            add_msg("assistant", confirmation)

            # Generate itinerary
            with st.spinner("AI đang tạo lịch trình tối ưu cho bạn..."):
                try:
                    engine = ChatEngine(session)
                    itinerary_request = build_itinerary_request(new_pref)
                    reply = engine.send_raw(itinerary_request)
                    st.session_state.engine = engine
                    session.itinerary_generated = True
                    render_html_message("assistant", reply)
                    add_msg("assistant", reply)
                except Exception as e:
                    err = f"Lỗi kết nối AI: {e}\n\nHãy kiểm tra `FIREWORKS_API_KEY` trong file `.env`."
                    st.error(err)
                    add_msg("assistant", err)

        else:
            # Move to next question
            next_q = get_question(new_pref.onboarding_step)
            render_html_message("assistant", next_q)
            add_msg("assistant", next_q)

        st.rerun()

    # ── CASE 2: Itinerary done → correction path ──
    else:
        engine = st.session_state.engine
        if engine is None:
            # Edge case: engine lost, rebuild
            engine = ChatEngine(session)
            st.session_state.engine = engine

        with st.spinner("Đang cập nhật lịch trình..."):
            try:
                reply = engine.send(prompt)
                render_html_message("assistant", reply)
                add_msg("assistant", reply)
            except Exception as e:
                err = f"Lỗi: {e}"
                st.error(err)
                add_msg("assistant", err)

        st.rerun()
