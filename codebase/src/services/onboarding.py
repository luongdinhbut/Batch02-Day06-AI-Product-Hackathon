from __future__ import annotations

from core.schemas import (
    Budget, ExperienceStyle, FoodStyle, OnboardingStep, PlaceType, UserPreference,
)
from utils.date_utils import parse_day_of_week, parse_num_days

_AMBIGUOUS_KEYWORDS = [
    "ăn gì cũng được", "ăn gì cũng ok", "cái gì cũng thích",
    "cái gì cũng được", "tùy bạn", "tùy mình", "không quan trọng",
    "bất kỳ", "không biết", "không có ý kiến", "miễn là được",
]


def _is_ambiguous(text: str) -> bool:
    t = text.lower().strip()
    return any(kw in t for kw in _AMBIGUOUS_KEYWORDS)


GREETING = (
    "Xin chào! Mình là **HaNoi Guide**\n\n"
    "Mình sẽ tạo lịch trình Hà Nội cá nhân hóa cho bạn trong vài phút — "
    "đầy đủ tham quan + ăn uống + nightlife theo đúng sở thích của bạn.\n\n"
    "Mình sẽ hỏi bạn **5 câu nhanh** để hiểu bạn muốn gì nhé!"
)

QUESTIONS = {
    OnboardingStep.food_style: (
        "**Câu 1/5:** Bạn thích ăn uống theo phong cách nào khi đi du lịch?\n\n"
        "_(Ví dụ: thích ăn bún phở vỉa hè, hoặc ngồi nhà hàng thoải mái, hoặc tìm quán local ít người biết...)_"
    ),
    OnboardingStep.place_type: (
        "**Câu 2/5:** Bạn muốn tham quan loại địa điểm nào ở Hà Nội?\n\n"
        "_(Ví dụ: đền chùa bảo tàng, phố cổ mua sắm, hay chỉ muốn chill cafe ngắm hồ...)_"
    ),
    OnboardingStep.experience: (
        "**Câu 3/5:** Bạn muốn trải nghiệm theo hướng nào?\n\n"
        "_(Ví dụ: muốn khám phá như người địa phương, hoặc đi những chỗ tourist-friendly dễ tìm, "
        "hoặc có bar pub buổi tối, hoặc đi cùng gia đình trẻ em...)_"
    ),
    OnboardingStep.budget: (
        "**Câu 4/5:** Ngân sách mỗi ngày của bạn khoảng bao nhiêu (bao gồm vé tham quan + ăn uống)?\n\n"
        "_(Ví dụ: khoảng 300k, hoặc tầm 700k, hoặc trên 1 triệu cũng được...)_"
    ),
    OnboardingStep.arrival_date: (
        "**Câu 5/5 (câu cuối!):** Bạn đến Hà Nội ngày nào và đi mấy ngày?\n\n"
        "_(Ví dụ: thứ 4 ngày 11/6, hoặc thứ 2 ngày 9/6 đi 2 ngày — "
        "mình cần ngày cụ thể để tránh địa điểm đóng cửa nhé!)_"
    ),
}


def get_question(step: OnboardingStep) -> str:
    return QUESTIONS.get(step, "")


def parse_food_style(text: str) -> FoodStyle | None:
    t = text.lower()
    if any(k in t for k in ["đường phố", "vỉa hè", "via he", "bún", "phở", "bánh mì", "street"]):
        return FoodStyle.street_food
    if any(k in t for k in ["nhà hàng", "nha hang", "restaurant", "máy lạnh", "thoải mái"]):
        return FoodStyle.restaurant
    if any(k in t for k in ["hidden", "gem", "ít người", "local", "ít biết", "quán nhỏ", "ngon mà ít"]):
        return FoodStyle.hidden_gem
    if any(k in t for k in ["kết hợp", "cả hai", "mix", "tùy bữa", "vừa", "sáng phở tối nhà hàng"]):
        return FoodStyle.mixed
    return None


def parse_place_type(text: str) -> PlaceType | None:
    t = text.lower()
    if any(k in t for k in ["văn hóa", "lịch sử", "bảo tàng", "đền", "chùa", "di tích", "museum"]):
        return PlaceType.culture_history
    if any(k in t for k in ["mua sắm", "phố cổ", "chợ", "shopping", "vui chơi"]):
        return PlaceType.shopping_entertainment
    if any(k in t for k in ["chill", "cafe", "cà phê", "hồ", "công viên", "ngắm", "view"]):
        return PlaceType.chill_cafe
    if any(k in t for k in ["tất cả", "hết", "mix", "cả 3", "đều được", "nhiều loại"]):
        return PlaceType.mixed
    return None


def parse_experience(text: str) -> tuple[ExperienceStyle, bool] | None:
    t = text.lower()
    if any(k in t for k in ["bar", "pub", "bia", "nightlife", "đêm", "uống"]):
        return ExperienceStyle.local, True
    if any(k in t for k in ["gia đình", "trẻ em", "con nhỏ", "bé"]):
        return ExperienceStyle.family, False
    if any(k in t for k in ["tourist", "tiện nghi", "dễ đi", "dễ tìm", "an toàn"]):
        return ExperienceStyle.tourist, False
    if any(k in t for k in ["local", "địa phương", "người", "tránh tourist", "thật sự", "bản địa", "ngóc ngách"]):
        return ExperienceStyle.local, False
    return None


def parse_budget(text: str) -> Budget | None:
    t = text.lower()
    # Tìm số tiền trong text
    import re
    numbers = re.findall(r"(\d+)", t.replace(".", "").replace(",", ""))
    for n in numbers:
        amount = int(n)
        if amount < 1000:
            amount *= 1000  # "300" → 300k
        if amount < 500000:
            return Budget.low
        if amount <= 1000000:
            return Budget.medium
        return Budget.high
    # Fallback keyword
    if any(k in t for k in ["tiết kiệm", "rẻ", "ít tiền", "sinh viên", "thấp"]):
        return Budget.low
    if any(k in t for k in ["vừa", "trung bình", "bình thường", "tầm tầm"]):
        return Budget.medium
    if any(k in t for k in ["thoải mái", "cao", "không quan trọng tiền", "sang"]):
        return Budget.high
    return None


def process_answer(preference: UserPreference, user_text: str) -> tuple[UserPreference, str | None]:
    step = preference.onboarding_step
    ambiguous = _is_ambiguous(user_text)

    if step == OnboardingStep.food_style:
        parsed = parse_food_style(user_text)
        if parsed is None or ambiguous:
            return preference, (
                "Mình chưa hiểu rõ lắm. Bạn thích kiểu nào hơn — "
                "**ăn vỉa hè bình dân** hay **ngồi nhà hàng có menu**?"
            )
        preference = preference.model_copy(update={
            "food_style": parsed,
            "onboarding_step": OnboardingStep.place_type,
        })

    elif step == OnboardingStep.place_type:
        parsed = parse_place_type(user_text)
        if parsed is None or ambiguous:
            return preference, (
                "Bạn có thể nói rõ hơn không? Ví dụ: thích **đi chùa bảo tàng** "
                "hay **ngồi cafe ngắm hồ**?"
            )
        preference = preference.model_copy(update={
            "place_type": parsed,
            "onboarding_step": OnboardingStep.experience,
        })

    elif step == OnboardingStep.experience:
        parsed = parse_experience(user_text)
        if parsed is None or ambiguous:
            return preference, (
                "Bạn có thể nói rõ hơn chút không? Ví dụ bạn muốn trải nghiệm kiểu **local (bản địa)**, "
                "**tourist-friendly (tiện nghi)**, hay **đi cùng gia đình trẻ em**?"
            )
        exp, nightlife = parsed
        preference = preference.model_copy(update={
            "experience": exp,
            "nightlife": nightlife,
            "onboarding_step": OnboardingStep.budget,
        })

    elif step == OnboardingStep.budget:
        parsed = parse_budget(user_text)
        if parsed is None or ambiguous:
            return preference, (
                "Bạn cho mình biết khoảng bao nhiêu tiền mỗi ngày được không? "
                "Ví dụ: **300k**, **700k**, hay **hơn 1 triệu**?"
            )
        preference = preference.model_copy(update={
            "budget": parsed,
            "onboarding_step": OnboardingStep.arrival_date,
        })

    elif step == OnboardingStep.arrival_date:
        day_of_week = parse_day_of_week(user_text)
        num_days = parse_num_days(user_text)
        if day_of_week is None:
            return preference, (
                "Mình chưa nhận ra ngày bạn đến. "
                "Bạn ghi rõ hơn được không? Ví dụ: **thứ 4, 11/06** hoặc **thứ 2 ngày 9/6**"
            )
        preference = preference.model_copy(update={
            "arrival_date_str": user_text,
            "arrival_day_of_week": day_of_week,
            "num_days": num_days,
            "onboarding_step": OnboardingStep.done,
        })

    return preference, None
