from __future__ import annotations

from core.schemas import Budget, ExperienceStyle, FoodStyle, PlaceType, UserPreference


# Các token này được fallback_builder dùng để chấm điểm; chỉ đổi khi sửa scorer.
FALLBACK_FOOD_STYLE = {
    FoodStyle.street_food: "Street food",
    FoodStyle.restaurant: "Restaurant",
    FoodStyle.hidden_gem: "Local hidden gem",
    FoodStyle.mixed: "Anything",
}

FALLBACK_PLACE_TYPE = {
    PlaceType.culture_history: "Culture/history",
    PlaceType.shopping_entertainment: "Shopping/fun",
    PlaceType.chill_cafe: "Chill cafe",
    PlaceType.mixed: "Balanced",
}

FALLBACK_EXPERIENCE = {
    ExperienceStyle.local: "Local",
    ExperienceStyle.tourist: "Tourist-friendly",
    ExperienceStyle.family: "Family",
}

FALLBACK_BUDGET = {
    Budget.low: "Under 500k",
    Budget.medium: "500k-1tr",
    Budget.high: "Over 1tr",
}


# Chuyển enum từ onboarding sang dict đơn giản cho fallback_builder.
def to_fallback_planner_preferences(preference: UserPreference) -> dict:
    return {
        "food_style": FALLBACK_FOOD_STYLE.get(preference.food_style, "Anything"),
        "sightseeing": FALLBACK_PLACE_TYPE.get(preference.place_type, "Balanced"),
        "local_style": FALLBACK_EXPERIENCE.get(preference.experience, "Local"),
        "budget": FALLBACK_BUDGET.get(preference.budget, "500k-1tr"),
        "travel_date": preference.arrival_day_of_week or preference.arrival_date_str or "",
        "nightlife": bool(preference.nightlife),
    }
