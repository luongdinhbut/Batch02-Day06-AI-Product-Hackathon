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


DATASET_COVERAGE_THRESHOLD = 0.70


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


def _looks_like_metadata(text: str) -> bool:
    lowered = _normalize(text)
    return any(
        marker in lowered
        for marker in [
            "phong cách:",
            "style:",
            "budget",
            "ngân sách",
            "tổng chi phí",
            "estimated budget",
            "rating:",
            "giá:",
            "giá vé:",
            "món nổi bật:",
            "vibe:",
            "tip:",
        ]
    )


def _strip_item_label(text: str) -> str:
    if ":" not in text:
        return text

    label, value = text.split(":", 1)
    label = _normalize(label)
    item_labels = [
        "cafe",
        "cà phê",
        "ăn sáng",
        "điểm tham quan",
        "tham quan",
        "quán ăn",
        "restaurant",
        "breakfast",
        "sightseeing",
        "dinner restaurant",
        "bar",
        "pub",
    ]
    if any(item_label in label for item_label in item_labels):
        return value.strip()
    return ""


def _strip_markdown_emphasis(text: str) -> str:
    return re.sub(r"\*\*([^*]{1,120})\*\*", r"\1", text)


def _add_recommendation_candidate(raw_text: str, candidates: set[str]) -> None:
    cleaned = raw_text.strip()
    if not cleaned or _looks_like_section(cleaned) or _looks_like_metadata(cleaned):
        return

    cleaned = _strip_item_label(cleaned)
    if not cleaned:
        return

    name = re.split(r"\s[-–—]\s|\s\(|,|·", cleaned, maxsplit=1)[0].strip()
    if 3 <= len(name) <= 80 and not _looks_like_section(name) and not _looks_like_metadata(name):
        candidates.add(name)


def _likely_recommended_names(text: str) -> set[str]:
    candidates: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        bold_matches = re.findall(r"\*\*([^*]{3,80})\*\*", stripped)
        for match in bold_matches:
            _add_recommendation_candidate(match, candidates)

        cleaned = re.sub(r"^[\-•\d\.\s]+", "", _strip_markdown_emphasis(stripped))
        cleaned = re.sub(r"^[^\wÀ-ỹ]+", "", cleaned)
        if not cleaned:
            continue
        _add_recommendation_candidate(cleaned, candidates)
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


def _matches_known_name(name: str, known_names: set[str]) -> bool:
    normalized_name = _normalize(name)
    if normalized_name in known_names:
        return True
    # The AI often shortens a dataset item, e.g. "Bà Nga" for "Bà Nga - Bún Mọc Cổ Truyền".
    return len(normalized_name) >= 6 and any(
        normalized_name in known_name or known_name in normalized_name
        for known_name in known_names
    )


def _find_known_item(name: str, items: list[dict]) -> dict | None:
    normalized_name = _normalize(name)
    if len(normalized_name) < 3:
        return None

    for item in items:
        known_name = _normalize(item.get("name", ""))
        if normalized_name == known_name:
            return item

    if len(normalized_name) < 6:
        return None

    for item in items:
        known_name = _normalize(item.get("name", ""))
        if normalized_name in known_name or known_name in normalized_name:
            return item
    return None


def _has_nightlife_section(text: str) -> bool:
    for line in text.splitlines():
        cleaned = _strip_markdown_emphasis(line).strip()
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned).strip()
        if re.match(r"^(đêm|dem|night)(?:\s*\(|\s+\d|$)", _normalize(cleaned)):
            return True
    return False


def validate_itinerary_text(text: str, data: dict, preference: UserPreference) -> ValidationResult:
    normalized = _normalize(text)
    issues: list[ValidationIssue] = []
    all_items = _all_items(data)
    known_names = {_normalize(item.get("name", "")) for item in all_items}

    required_blocks = {
        "morning": ["morning", "sáng"],
        "lunch": ["lunch", "trưa"],
        "afternoon": ["afternoon", "chiều"],
        "dinner": ["dinner", "tối"],
    }
    present_blocks = {
        block: any(marker in normalized for marker in markers)
        for block, markers in required_blocks.items()
    }
    present_count = sum(1 for present in present_blocks.values() if present)
    for block, present in present_blocks.items():
        if not present:
            issues.append(
                ValidationIssue(
                    code="missing_required_block",
                    message=f"Missing required {block} block.",
                    severity="error" if present_count < 3 else "warning",
                )
            )

    recommended_names = _likely_recommended_names(text)
    matched_names = [name for name in recommended_names if _matches_known_name(name, known_names)]
    recommended_items = [
        item
        for item in (_find_known_item(name, all_items) for name in recommended_names)
        if item is not None
    ]
    unknown_names = [
        name
        for name in recommended_names
        if not _matches_known_name(name, known_names) and not _looks_like_section(name)
    ]
    total_recommendations = len(matched_names) + len(unknown_names)
    dataset_coverage = len(matched_names) / total_recommendations if total_recommendations else 1.0
    for name in unknown_names:
        issues.append(
            ValidationIssue(
                code="unknown_place",
                message="Recommendation does not match any dataset item.",
                severity="warning",
                item_name=name,
            )
        )
    if total_recommendations and dataset_coverage < DATASET_COVERAGE_THRESHOLD:
        issues.append(
            ValidationIssue(
                code="low_dataset_coverage",
                message=(
                    f"Only {dataset_coverage:.0%} of detected recommendations match the dataset; "
                    f"minimum is {DATASET_COVERAGE_THRESHOLD:.0%}."
                ),
                severity="error",
            )
        )

    day = preference.arrival_day_of_week or ""
    if day:
        for item in recommended_items:
            if day in item.get("closed_on", []):
                issues.append(
                    ValidationIssue(
                        code="closed_place",
                        message=f"Item is closed on {day}.",
                        severity="error",
                        item_name=item.get("name"),
                    )
                )

    mentioned_bars = [item for item in recommended_items if item in data.get("bars", [])]
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

    if _has_nightlife_section(text):
        if not preference.nightlife or preference.experience == ExperienceStyle.family:
            issues.append(
                ValidationIssue(
                    code="invalid_evening_block",
                    message="Nightlife block is not allowed for this preference.",
                    severity="error",
                )
            )

    limit = _budget_limit(preference)
    for item in recommended_items:
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
