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
    match = re.search(r"(\d+)\s*ngày", normalized)
    if match:
        return max(1, min(int(match.group(1)), 7))
    if "hai ngày" in normalized or "2 ngày" in normalized:
        return 2
    return 1


def to_vn_day(day_of_week: str) -> str:
    return _WEEKDAY_TO_VN.get(day_of_week, day_of_week)
