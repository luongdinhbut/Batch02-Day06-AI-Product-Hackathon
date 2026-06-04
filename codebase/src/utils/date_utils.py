from __future__ import annotations

import re
from datetime import datetime, date

_VN_DAY_MAP: dict[str, str] = {
    "thứ 2": "Monday", "thu 2": "Monday", "thứ hai": "Monday", "thu hai": "Monday",
    "thứ 3": "Tuesday", "thu 3": "Tuesday", "thứ ba": "Tuesday", "thu ba": "Tuesday",
    "thứ 4": "Wednesday", "thu 4": "Wednesday", "thứ tư": "Wednesday", "thu tu": "Wednesday",
    "thứ 5": "Thursday", "thu 5": "Thursday", "thứ năm": "Thursday", "thu nam": "Thursday",
    "thứ 6": "Friday", "thu 6": "Friday", "thứ sáu": "Friday", "thu sau": "Friday",
    "thứ 7": "Saturday", "thu 7": "Saturday", "thứ bảy": "Saturday", "thu bay": "Saturday",
    "chủ nhật": "Sunday", "chu nhat": "Sunday", "cn": "Sunday",
}

_WEEKDAY_TO_VN: dict[str, str] = {
    "Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4",
    "Thursday": "Thứ 5", "Friday": "Thứ 6", "Saturday": "Thứ 7", "Sunday": "Chủ nhật",
}

_PYTHON_WEEKDAY: dict[int, str] = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday",
    3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday",
}


def parse_day_of_week(text: str) -> str | None:
    normalized = text.lower().strip()
    for vn_key, en_day in _VN_DAY_MAP.items():
        if vn_key in normalized:
            return en_day
    match = re.search(r"(\d{1,2})[/\-\.](\d{1,2})(?:[/\-\.](\d{2,4}))?", normalized)
    if match:
        day_num, month_num = int(match.group(1)), int(match.group(2))
        year_str = match.group(3)
        year = int(year_str) if year_str else datetime.now().year
        if len(str(year)) == 2:
            year += 2000
        try:
            return _PYTHON_WEEKDAY[date(year, month_num, day_num).weekday()]
        except ValueError:
            pass
    return None


def parse_num_days(text: str) -> int:
    normalized = text.lower()
    # Check for explicit "X ngày" pattern
    match = re.search(r"(\d+)\s*ngày", normalized)
    if match:
        return max(1, min(int(match.group(1)), 7))
    # Check for "hai ngày"
    if "hai ngày" in normalized or "2 ngày" in normalized:
        return 2
    # Map thứ X to X days (thứ 4 → 4 days, etc.)
    vn_days = ["thứ 2", "thu 2", "thứ ba", "thu ba", "thứ 3", "thu 3",
               "thứ tư", "thu tu", "thứ 4", "thu 4",
               "thứ năm", "thu nam", "thứ 5", "thu 5",
               "thứ sáu", "thu sau", "thứ 6", "thu 6",
               "thứ bảy", "thu bay", "thứ 7", "chu nhat", "chủ nhật"]
    day_number_map = {
        "thứ 2": 2, "thu 2": 2, "thứ ba": 2, "thu ba": 2, "thứ 3": 3, "thu 3": 3,
        "thứ tư": 4, "thu tu": 4, "thứ 4": 4, "thu 4": 4,
        "thứ năm": 5, "thu nam": 5, "thứ 5": 5, "thu 5": 5,
        "thứ sáu": 6, "thu sau": 6, "thứ 6": 6, "thu 6": 6,
        "thứ bảy": 7, "thu bay": 7, "thứ 7": 7,
        "chu nhat": 1, "chủ nhật": 1
    }
    for vn_day, num_days in day_number_map.items():
        if vn_day in normalized:
            return min(num_days, 7)
    return 1


def to_vn_day(day_of_week: str) -> str:
    return _WEEKDAY_TO_VN.get(day_of_week, day_of_week)
