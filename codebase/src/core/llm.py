from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv()


DEFAULT_FIREWORKS_MODEL = "accounts/fireworks/models/deepseek-v4-pro"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_CUSTOM_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    model: str
    url: str
    headers: dict[str, str]


def _provider_name(provider: str | None = None) -> str:
    raw = provider or os.getenv("LLM_PROVIDER", "fireworks")
    name = raw.split(",")[0].strip().lower()
    if name == "google":
        return "gemini"
    return name or "fireworks"


def _chat_completions_url(base_url: str) -> str:
    url = base_url.rstrip("/")
    return url if url.endswith("/chat/completions") else f"{url}/chat/completions"


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing {name}. Add it to .env before running AI features.")
    return value


# LLM switcher: dựng cấu hình đúng cho provider đang chọn từ env.
def get_llm_config(provider: str | None = None) -> LLMConfig:
    selected = _provider_name(provider)

    if selected == "fireworks":
        api_key = _required_env("FIREWORKS_API_KEY")
        return LLMConfig(
            provider="fireworks",
            api_key=api_key,
            model=os.getenv("FIREWORKS_MODEL", DEFAULT_FIREWORKS_MODEL),
            url="https://api.fireworks.ai/inference/v1/chat/completions",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

    if selected == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("Missing GEMINI_API_KEY. Add it to .env before running AI features.")
        model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        return LLMConfig(
            provider="gemini",
            api_key=api_key,
            model=model,
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
        )

    if selected == "custom":
        api_key = _required_env("CUSTOM_API_KEY")
        base_url = os.getenv("CUSTOM_BASE_URL") or os.getenv("CUSTOM_API_BASE_URL")
        if not base_url:
            raise EnvironmentError("Missing CUSTOM_BASE_URL. Add it to .env before running AI features.")
        return LLMConfig(
            provider="custom",
            api_key=api_key,
            model=os.getenv("CUSTOM_MODEL", DEFAULT_CUSTOM_MODEL),
            url=_chat_completions_url(base_url),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

    raise EnvironmentError(f"Unsupported LLM_PROVIDER '{selected}'. Use fireworks, gemini, or custom.")


def get_fireworks_config() -> dict[str, Any]:
    config = get_llm_config("fireworks")
    return {"url": config.url, "headers": config.headers, "model": config.model}


# Cho phép demo cấu hình nhiều provider theo thứ tự ưu tiên, ví dụ fireworks,gemini.
def _provider_order() -> list[str]:
    raw = os.getenv("LLM_PROVIDER", "fireworks")
    names = []
    for item in raw.split(","):
        name = _provider_name(item)
        if name and name not in names:
            names.append(name)
    return names or ["fireworks"]


def _normalize_content(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        text = raw.get("text") or raw.get("content")
        return str(text).strip() if text is not None else str(raw).strip()
    if isinstance(raw, list):
        parts = [_normalize_content(item) for item in raw]
        return "\n".join(part for part in parts if part).strip()
    return str(raw).strip()


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    return "\n\n".join(f"{msg['role'].upper()}:\n{msg['content']}" for msg in messages)


def _extract_chat_completion(payload: dict[str, Any]) -> str:
    return _normalize_content(payload["choices"][0]["message"].get("content", ""))


def _extract_gemini(payload: dict[str, Any]) -> str:
    return _normalize_content(payload["candidates"][0]["content"]["parts"])


# Chuẩn hóa cách gọi provider: Gemini dùng prompt text, Fireworks/custom dùng chat completions.
def _call_provider(config: LLMConfig, messages: list[dict[str, str]]) -> str:
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.6"))

    if config.provider == "gemini":
        body = {
            "contents": [{"parts": [{"text": _messages_to_prompt(messages)}]}],
            "generationConfig": {"temperature": temperature},
        }
        response = requests.post(
            config.url,
            headers=config.headers,
            data=json.dumps(body),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return _extract_gemini(response.json())

    body = {
        "model": config.model,
        "temperature": temperature,
        "messages": messages,
    }
    if config.provider == "fireworks":
        body.update(
            {
                "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "8192")),
                "top_p": 1,
                "top_k": 40,
                "presence_penalty": 0,
                "frequency_penalty": 0,
            }
        )

    response = requests.post(
        config.url,
        headers=config.headers,
        data=json.dumps(body),
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return _extract_chat_completion(response.json())


# Thử lần lượt từng provider; lỗi được gom lại để app fallback thay vì crash.
def call_llm(messages: list[dict[str, str]]) -> tuple[str, str]:
    errors: list[str] = []

    for provider in _provider_order():
        try:
            config = get_llm_config(provider)
            text = _call_provider(config, messages)
            if text:
                return text, f"AI itinerary generated with {config.provider}."
            errors.append(f"{provider}: empty response")
        except (
            EnvironmentError,
            requests.RequestException,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(f"{provider}: {exc}")

    detail = " | ".join(errors) if errors else "no providers configured"
    return "", f"LLM unavailable. {detail}"
