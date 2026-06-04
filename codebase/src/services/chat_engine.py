from __future__ import annotations

import json
import requests
from core.llm import get_fireworks_config
from core.schemas import ChatMessage, SessionState
from services.prompt_builder import build_system_instruction


class ChatEngine:
    def __init__(self, state: SessionState) -> None:
        self._state = state
        self._config = None
        self._system_instruction = None

    def _ensure_config(self) -> None:
        if not self._config:
            self._config = get_fireworks_config()
            self._system_instruction = build_system_instruction(self._state.preference)

    def refresh(self) -> None:
        """Gọi sau khi preference thay đổi để rebuild system_instruction."""
        self._config = None

    def _call_fireworks_api(self, new_user_message: str | None = None) -> str:
        self._ensure_config()
        
        # Build messages payload
        messages = [{"role": "system", "content": self._system_instruction}]
        
        # Add history
        for msg in self._state.chat_history:
            # We don't include system messages in history again, just user/assistant
            if msg.role in ["user", "model", "assistant"]:
                role = "assistant" if msg.role == "model" else "user"
                messages.append({"role": role, "content": msg.content})
                
        # Add new message if any (for `send` method)
        if new_user_message:
            messages.append({"role": "user", "content": new_user_message})
            self._state.chat_history.append(ChatMessage(role="user", content=new_user_message))

        payload = {
            "model": self._config["model"],
            "max_tokens": 8192,  # A reasonable output length
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": 0.6,
            "messages": messages
        }
        
        response = requests.post(
            self._config["url"], 
            headers=self._config["headers"], 
            data=json.dumps(payload)
        )
        
        if response.status_code != 200:
            raise Exception(f"Fireworks API Error {response.status_code}: {response.text}")
            
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
        
        # Save assistant reply to history
        self._state.chat_history.append(ChatMessage(role="model", content=reply))
        
        return reply

    def send(self, user_message: str) -> str:
        return self._call_fireworks_api(new_user_message=user_message)

    def send_raw(self, message: str) -> str:
        """Gửi message trigger generate (không hiển thị user message trong UI lúc đầu)."""
        # Tricking the history to add the user message internally
        return self._call_fireworks_api(new_user_message=message)
