from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from core.schemas import Budget, ExperienceStyle, UserPreference


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"]
    item_name: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    issues: list[ValidationIssue]
    retry_feedback: str


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _all_items(data: dict) -> list[dict]:
    return data.get("places", []) + data.get("restaurants", []) + data.get("bars", [])


def _known_mentions(text: str, data: dict) -> list[dict]:
    normalized = _normalize(text)
    mentions = []
    for item in _all_items(data):
        name = item.get("name")
        if name and _normalize(name) in normalized:
            mentions.append(item)
    return mentions


def _likely_recommended_names(text: str) -> set[str]:
    candidates: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        bold_matches = re.findall(r"\*\*([^*]{3,80})\*\*", stripped)
        for match in bold_matches:
            candidates.add(match.strip())
        if bold_matches:
            continue

        cleaned = re.sub(r"^[\-•\d\.\s]+", "", stripped)
        cleaned = re.sub(r"^[^\wÀ-ỹ]+", "", cleaned)
        if not cleaned:
            continue
        name = re.split(r"\s[-–—]\s|\s\(|,|·", cleaned, maxsplit=1)[0].strip()
        if 3 <= len(name) <= 80 and not _looks_like_section(name):
            candidates.add(name)
    return candidates


def _looks_like_section(text: str) -> bool:
    lowered = _normalize(text)
    return any(
        keyword in lowered
        for keyword in [
            "sáng",
            "trưa",
            "chiều",
            "tối",
            "đêm",
            "morning",
            "lunch",
            "afternoon",
            "dinner",
            "evening",
            "itinerary",
            "lịch trình",
            "estimated budget",
        ]
    )


def _budget_limit(preference: UserPreference) -> int:
    if preference.budget == Budget.low:
        return 120_000
    if preference.budget == Budget.medium:
        return 300_000
    return 1_000_000


def _build_feedback(issues: list[ValidationIssue]) -> str:
    if not issues:
        return ""
    lines = ["Please revise the itinerary. Keep the same output format and fix these validation issues:"]
    for issue in issues:
        item = f" ({issue.item_name})" if issue.item_name else ""
        lines.append(f"- {issue.code}{item}: {issue.message}")
    return "\n".join(lines)


def validate_itinerary_text(text: str, data: dict, preference: UserPreference) -> ValidationResult:
    normalized = _normalize(text)
    issues: list[ValidationIssue] = []
    mentions = _known_mentions(text, data)
    known_names = {_normalize(item.get("name", "")) for item in _all_items(data)}

    required_blocks = {
        "morning": ["morning", "sáng"],
        "lunch": ["lunch", "trưa"],
        "afternoon": ["afternoon", "chiều"],
        "dinner": ["dinner", "tối"],
    }
    for block, markers in required_blocks.items():
        if not any(marker in normalized for marker in markers):
            issues.append(
                ValidationIssue(
                    code="missing_required_block",
                    message=f"Missing required {block} block.",
                    severity="error",
                )
            )

    for name in _likely_recommended_names(text):
        normalized_name = _normalize(name)
        if normalized_name not in known_names and not _looks_like_section(name):
            issues.append(
                ValidationIssue(
                    code="unknown_place",
                    message="Recommendation does not match any dataset item.",
                    severity="error",
                    item_name=name,
                )
            )

    day = preference.arrival_day_of_week or ""
    if day:
        for item in mentions:
            if day in item.get("closed_on", []):
                issues.append(
                    ValidationIssue(
                        code="closed_place",
                        message=f"Item is closed on {day}.",
                        severity="error",
                        item_name=item.get("name"),
                    )
                )

    mentioned_bars = [item for item in mentions if item in data.get("bars", [])]
    if mentioned_bars and not preference.nightlife:
        for bar in mentioned_bars:
            issues.append(
                ValidationIssue(
                    code="nightlife_not_requested",
                    message="Bar/pub was recommended even though nightlife is false.",
                    severity="error",
                    item_name=bar.get("name"),
                )
            )

    if mentioned_bars and preference.experience == ExperienceStyle.family:
        for bar in mentioned_bars:
            issues.append(
                ValidationIssue(
                    code="family_bar",
                    message="Bar/pub was recommended for a family itinerary.",
                    severity="error",
                    item_name=bar.get("name"),
                )
            )

    if "evening" in normalized or "night" in normalized or "đêm" in normalized:
        if not preference.nightlife or preference.experience == ExperienceStyle.family:
            issues.append(
                ValidationIssue(
                    code="invalid_evening_block",
                    message="Evening/night block is not allowed for this preference.",
                    severity="error",
                )
            )

    limit = _budget_limit(preference)
    for item in mentions:
        price_max = int(item.get("price_max") or item.get("price_min") or 0)
        if price_max > limit:
            issues.append(
                ValidationIssue(
                    code="budget_mismatch",
                    message=f"Item price max {price_max} exceeds budget sanity limit {limit}.",
                    severity="warning",
                    item_name=item.get("name"),
                )
            )

    errors = [issue for issue in issues if issue.severity == "error"]
    return ValidationResult(
        is_valid=not errors,
        issues=issues,
        retry_feedback=_build_feedback(issues),
    )
