from __future__ import annotations

from core.llm import build_model_with_system
from core.schemas import ChatMessage, SessionState
from services.prompt_builder import build_system_instruction


class ChatEngine:
    def __init__(self, state: SessionState) -> None:
        self._state = state
        self._chat = None

    def _ensure_chat(self) -> None:
        system_instruction = build_system_instruction(self._state.preference)
        model = build_model_with_system(system_instruction)
        history = [
            {"role": msg.role, "parts": [msg.content]}
            for msg in self._state.chat_history
        ]
        self._chat = model.start_chat(history=history)

    def refresh(self) -> None:
        """Gọi sau khi preference thay đổi để rebuild system_instruction."""
        self._chat = None

    def send(self, user_message: str) -> str:
        if self._chat is None:
            self._ensure_chat()
        self._state.chat_history.append(ChatMessage(role="user", content=user_message))
        response = self._chat.send_message(user_message)
        reply = response.text.strip()
        self._state.chat_history.append(ChatMessage(role="model", content=reply))
        return reply

    def send_raw(self, message: str) -> str:
        """Gửi message trigger generate (không hiển thị trong UI chat)."""
        if self._chat is None:
            self._ensure_chat()
        response = self._chat.send_message(message)
        reply = response.text.strip()
        self._state.chat_history.append(ChatMessage(role="user", content=message))
        self._state.chat_history.append(ChatMessage(role="model", content=reply))
        return reply
