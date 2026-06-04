from __future__ import annotations

from core.schemas import UserPreference
from services.chat_engine import ChatEngine
from services.fallback_builder import build_fallback_itinerary
from services.itinerary_validator import ValidationResult, validate_itinerary_text
from services.preference_mapper import to_fallback_planner_preferences
from services.prompt_builder import build_itinerary_request


PROVIDER_FALLBACK_NOTE = "AI provider is unavailable, so I generated a safe local fallback itinerary."
UNSAFE_AI_FALLBACK_NOTE = "AI response was not safe enough, so I generated a safe local fallback itinerary."


def format_itinerary_for_chat(itinerary: dict) -> str:
    lines = [f"## {itinerary['title']}", f"**Estimated budget:** {itinerary['estimate']}"]
    for itinerary_block in itinerary["blocks"]:
        lines.append(f"\n### {itinerary_block['name']} ({itinerary_block['time']})")
        for item in itinerary_block["items"]:
            reason = item.get("description") or item.get("popular_dish") or item.get("local_tip") or ""
            price = item.get("price_note") or f"{item.get('price_min', 0):,}-{item.get('price_max', 0):,} VND".replace(",", ".")
            lines.append(
                f"- **{item.get('name')}** - {item.get('district', 'Hanoi')} - rating {item.get('rating', 'n/a')} - {price}\n"
                f"  {reason[:180]}"
            )
    return "\n".join(lines)


def _render_fallback_itinerary(itinerary: dict, safety_warnings: list[str], note: str) -> str:
    lines = [note]
    if safety_warnings:
        lines.extend(["", "**Warnings:**"])
        lines.extend(f"- {warning}" for warning in safety_warnings)
    lines.extend(["", format_itinerary_for_chat(itinerary)])
    return "\n".join(lines)


def _build_fallback_result(
    data: dict,
    preference: UserPreference,
    note: str,
    internal_warnings: list[str],
    validation: ValidationResult | None,
) -> dict:
    planner_preferences = to_fallback_planner_preferences(preference)
    fallback = build_fallback_itinerary(data, planner_preferences)
    return {
        "mode": "fallback",
        "itinerary": fallback,
        "rendered_itinerary": _render_fallback_itinerary(fallback, fallback.get("warnings", []), note),
        "ai_text": "",
        "warnings": internal_warnings + fallback.get("warnings", []),
        "validation": validation.model_dump() if validation else None,
    }


def _send_ai_request(engine: ChatEngine, message: str) -> str:
    engine.refresh()
    return engine.send_raw(message)


def generate_itinerary_from_preference(
    data: dict,
    preference: UserPreference,
    engine: ChatEngine | None = None,
) -> dict:
    if engine is None:
        return _build_fallback_result(data, preference, PROVIDER_FALLBACK_NOTE, ["AI engine is not available."], None)

    request = build_itinerary_request(preference)
    try:
        ai_text = _send_ai_request(engine, request)
    except Exception as exc:
        return _build_fallback_result(data, preference, PROVIDER_FALLBACK_NOTE, [f"AI unavailable: {exc}"], None)

    validation = validate_itinerary_text(ai_text, data, preference)
    if validation.is_valid:
        return {
            "mode": "ai",
            "itinerary": None,
            "rendered_itinerary": ai_text,
            "ai_text": ai_text,
            "warnings": [issue.message for issue in validation.issues],
            "validation": validation.model_dump(),
        }

    retry_request = request + "\n\n" + validation.retry_feedback
    try:
        retry_text = _send_ai_request(engine, retry_request)
    except Exception as exc:
        return _build_fallback_result(
            data,
            preference,
            PROVIDER_FALLBACK_NOTE,
            [f"AI retry unavailable: {exc}"],
            validation,
        )

    retry_validation = validate_itinerary_text(retry_text, data, preference)
    if retry_validation.is_valid:
        return {
            "mode": "ai_retry",
            "itinerary": None,
            "rendered_itinerary": retry_text,
            "ai_text": retry_text,
            "warnings": [issue.message for issue in retry_validation.issues],
            "validation": retry_validation.model_dump(),
        }

    return _build_fallback_result(
        data,
        preference,
        UNSAFE_AI_FALLBACK_NOTE,
        [issue.message for issue in retry_validation.issues],
        retry_validation,
    )
