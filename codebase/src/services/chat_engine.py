from __future__ import annotations

from core.llm import call_llm
from core.schemas import ChatMessage, SessionState
from services.prompt_builder import build_system_instruction


class ChatEngine:
    def __init__(self, state: SessionState) -> None:
        self._state = state
        self._system_instruction = ""
        self.last_note = ""

    def refresh(self) -> None:
        """Rebuild system instruction after preferences change."""
        self._system_instruction = ""

    def _ensure_system_instruction(self) -> None:
        if not self._system_instruction:
            self._system_instruction = build_system_instruction(self._state.preference)

    def _messages(self, new_user_message: str) -> list[dict[str, str]]:
        self._ensure_system_instruction()
        messages = [{"role": "system", "content": self._system_instruction}]
        for msg in self._state.chat_history:
            if msg.role in {"user", "model", "assistant"}:
                role = "assistant" if msg.role in {"model", "assistant"} else "user"
                messages.append({"role": role, "content": msg.content})
        messages.append({"role": "user", "content": new_user_message})
        return messages

    def _send(self, user_message: str, save_user_message: bool) -> str:
        reply, note = call_llm(self._messages(user_message))
        self.last_note = note
        if not reply:
            raise RuntimeError(note)

        if save_user_message:
            self._state.chat_history.append(ChatMessage(role="user", content=user_message))
        self._state.chat_history.append(ChatMessage(role="model", content=reply))
        return reply

    def send(self, user_message: str) -> str:
        return self._send(user_message, save_user_message=True)

    def send_raw(self, message: str) -> str:
        """Send hidden generation trigger without rendering it as a normal user turn."""
        return self._send(message, save_user_message=True)
