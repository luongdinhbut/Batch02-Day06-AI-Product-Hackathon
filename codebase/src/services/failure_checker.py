from __future__ import annotations

from services.data_loader import get_places
from utils.date_utils import to_vn_day


def get_closed_places(day_of_week: str) -> list[dict]:
    return [p for p in get_places() if day_of_week in p.get("closed_on", [])]


def find_alternatives(closed_place: dict, day_of_week: str, max_results: int = 2) -> list[dict]:
    all_places = get_places()
    category = closed_place.get("category", "")
    district = closed_place.get("district", "")
    area = closed_place.get("area", "")
    closed_id = closed_place.get("id")

    candidates = [
        p for p in all_places
        if p.get("id") != closed_id and day_of_week not in p.get("closed_on", [])
    ]

    tier1 = [p for p in candidates if p.get("category") == category and p.get("district") == district]
    if len(tier1) >= max_results:
        return sorted(tier1, key=lambda x: -x.get("rating", 0))[:max_results]

    tier2 = [p for p in candidates if p.get("category") == category and p.get("area") == area]
    combined = tier1 + [p for p in tier2 if p not in tier1]
    if len(combined) >= max_results:
        return sorted(combined, key=lambda x: -x.get("rating", 0))[:max_results]

    tier3 = [p for p in candidates if p.get("district") == district and p not in combined]
    return sorted(combined + tier3, key=lambda x: -x.get("rating", 0))[:max_results]


def build_closure_warning(day_of_week: str) -> str:
    closed = get_closed_places(day_of_week)
    if not closed:
        return ""

    vn_day = to_vn_day(day_of_week)
    lines = [f"⚠️ CẢNH BÁO: Các địa điểm sau đóng cửa vào {vn_day}:"]
    for place in closed:
        alts = find_alternatives(place, day_of_week)
        alt_names = " / ".join(a["name"] for a in alts) if alts else "không có thay thế cùng loại"
        lines.append(f"  - {place['name']} ({place['district']}) → Thay thế: {alt_names}")
    lines.append(
        "Hãy LOẠI BỎ các địa điểm trên khỏi lịch trình và chỉ gợi ý những địa điểm thay thế đã liệt kê."
    )
    return "\n".join(lines)
