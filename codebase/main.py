import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src/ to path so existing modules work with their relative imports
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from agent.itinerary_agent import generate_itinerary_from_preference
from core.schemas import SessionState, OnboardingStep, ChatMessage
from services.onboarding import GREETING, get_question, process_answer
from services.data_loader import load_hanoi_data
from services.prompt_builder import build_confirmation_message
from services.chat_engine import ChatEngine
from services.failure_checker import get_closed_places
from utils.date_utils import to_vn_day

app = FastAPI(title="HaNoi Guide API")
DATA = load_hanoi_data()

# Enable CORS for Next.js (usually on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    session: SessionState

def get_llm_session_state(session: SessionState) -> SessionState:
    """Keep recent visible context for itinerary correction without exposing hidden prompts."""
    llm_session = session.model_copy(deep=True)
    llm_session.chat_history = [
        ChatMessage(role="model" if msg.role == "assistant" else msg.role, content=msg.content)
        for msg in session.chat_history[-12:]
        if msg.role in {"user", "assistant", "model"}
    ]
    return llm_session

@app.post("/api/start")
async def start_session():
    session = SessionState()
    # Thêm tin chào mừng và câu hỏi đầu tiên vào lịch sử
    session.chat_history.append(ChatMessage(role="assistant", content=GREETING))
    session.chat_history.append(ChatMessage(role="assistant", content=get_question(OnboardingStep.food_style)))
    return {"session": session}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    prompt = req.prompt.strip()
    session = req.session
    step = session.preference.onboarding_step
    
    # ── CASE 1: Đang thực hiện onboarding (câu 1-5) ──
    if step != OnboardingStep.done:
        # Ghi nhận tin nhắn người dùng vào UI history
        session.chat_history.append(ChatMessage(role="user", content=prompt))
        
        new_pref, retry_msg = process_answer(session.preference, prompt)
        session.preference = new_pref
        
        if retry_msg:
            # Nhập mơ hồ -> hỏi lại câu đó
            session.chat_history.append(ChatMessage(role="assistant", content=retry_msg))
        elif new_pref.onboarding_step == OnboardingStep.done:
            # Hoàn thành 5 câu -> hiện xác nhận -> tạo lịch trình
            confirmation = build_confirmation_message(new_pref)
            session.chat_history.append(ChatMessage(role="assistant", content=confirmation))
            
            # AI-first flow with deterministic fallback when provider output is unavailable.
            try:
                llm_session = get_llm_session_state(session)
                engine = ChatEngine(llm_session)
                result = generate_itinerary_from_preference(DATA, new_pref, engine)
                reply = result["rendered_itinerary"]
                session.itinerary_generated = True
                session.chat_history.append(ChatMessage(role="assistant", content=reply))
            except Exception:
                err = "Mình chưa thể tạo lịch trình lúc này. Hãy kiểm tra dữ liệu địa điểm và thử lại."
                session.chat_history.append(ChatMessage(role="assistant", content=err))
        else:
            # Chuyển sang câu hỏi tiếp theo
            next_q = get_question(new_pref.onboarding_step)
            session.chat_history.append(ChatMessage(role="assistant", content=next_q))
            
        return {"session": session}
        
    # ── CASE 2: Đã có lịch trình -> Chế độ chỉnh sửa (Correction) ──
    else:
        # Lọc session state dành riêng cho LLM (không có tin nhắn chỉnh sửa hiện tại)
        llm_session = get_llm_session_state(session)
        engine = ChatEngine(llm_session)
        
        # Ghi nhận tin nhắn người dùng vào UI history
        session.chat_history.append(ChatMessage(role="user", content=prompt))
        
        try:
            reply = engine.send(prompt)
            session.chat_history.append(ChatMessage(role="assistant", content=reply))
        except Exception as e:
            err = f"Lỗi: {e}"
            session.chat_history.append(ChatMessage(role="assistant", content=err))
            
        return {"session": session}

@app.get("/api/closed-places")
async def closed_places(day: str):
    """Trả về danh sách các địa điểm đóng cửa theo thứ."""
    places = get_closed_places(day)
    return {"places": places}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
