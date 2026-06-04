import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from core.schemas import (  # noqa: E402
    Budget,
    ExperienceStyle,
    FoodStyle,
    PlaceType,
    UserPreference,
)
from services.data_loader import load_hanoi_data  # noqa: E402


def complete_preference(**overrides):
    data = {
        "food_style": FoodStyle.street_food,
        "place_type": PlaceType.culture_history,
        "experience": ExperienceStyle.local,
        "nightlife": False,
        "budget": Budget.low,
        "arrival_day_of_week": "Monday",
        "arrival_date_str": "2026-06-08",
    }
    data.update(overrides)
    return UserPreference(**data)


class BrokenEngine:
    def refresh(self):
        pass

    def send_raw(self, message):
        raise RuntimeError("provider down")


class ItineraryServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_hanoi_data()

    def test_provider_config_defaults_to_fireworks(self):
        import core.llm as llm

        with patch.dict(os.environ, {"FIREWORKS_API_KEY": "fw-key"}, clear=True):
            config = llm.get_llm_config()

        self.assertEqual(config.provider, "fireworks")
        self.assertIn("fireworks.ai", config.url)
        self.assertEqual(config.api_key, "fw-key")

    def test_provider_config_supports_custom_base_url(self):
        import core.llm as llm

        env = {
            "LLM_PROVIDER": "custom",
            "CUSTOM_API_KEY": "custom-key",
            "CUSTOM_BASE_URL": "https://example.test/v1",
            "CUSTOM_MODEL": "demo-model",
        }
        with patch.dict(os.environ, env, clear=True):
            config = llm.get_llm_config()

        self.assertEqual(config.provider, "custom")
        self.assertEqual(config.url, "https://example.test/v1/chat/completions")
        self.assertEqual(config.model, "demo-model")

    def test_agent_uses_fallback_when_llm_fails(self):
        from agent.itinerary_agent import generate_itinerary_from_preference

        result = generate_itinerary_from_preference(
            self.data,
            complete_preference(),
            BrokenEngine(),
        )

        self.assertEqual(result["mode"], "fallback")
        self.assertIn("AI provider is unavailable", result["rendered_itinerary"])
        self.assertTrue(result["itinerary"]["blocks"])

    def test_fallback_avoids_closed_places_on_travel_day(self):
        from services.fallback_builder import build_fallback_itinerary
        from services.preference_mapper import to_fallback_planner_preferences

        preference = complete_preference(arrival_day_of_week="Monday")
        itinerary = build_fallback_itinerary(
            self.data,
            to_fallback_planner_preferences(preference),
        )
        names = {
            item["name"]
            for block in itinerary["blocks"]
            for item in block["items"]
        }
        monday_closed = {
            place["name"]
            for place in self.data["places"]
            if "Monday" in place.get("closed_on", [])
        }

        self.assertTrue(itinerary["warnings"])
        self.assertTrue(names.isdisjoint(monday_closed))

    def test_validator_accepts_labeled_itinerary_with_known_places(self):
        from services.itinerary_validator import validate_itinerary_text

        preference = complete_preference(arrival_day_of_week="Thursday", arrival_date_str="2026-06-04")
        itinerary = """
LỊCH TRÌNH HÀ NỘI - THỨ NĂM
Phong cách: street_food · culture_history · local · Budget low

SÁNG (7:00-12:00)
- Cafe/ăn sáng gần đó: 61 Cafe - Bát Sứ
- Điểm tham quan: Hồ Hoàn Kiếm & Đền Ngọc Sơn

TRƯA (12:00-13:30)
- Quán ăn: Bà Nga - Bún Mọc Cổ Truyền

CHIỀU (13:30-17:00)
- Điểm tham quan: Nhà hát Lớn Hà Nội

TỐI (18:00-20:00)
- Quán ăn tối: Bún Chả Đắc Kim
"""

        result = validate_itinerary_text(itinerary, self.data, preference)

        self.assertTrue(result.is_valid, result.model_dump())

    def test_validator_accepts_bold_markdown_labels_with_known_places(self):
        from services.itinerary_validator import validate_itinerary_text

        preference = complete_preference(arrival_day_of_week="Thursday", arrival_date_str="2026-06-04")
        breakfast = self.data["restaurants"][0]["name"]
        morning_place = self.data["places"][0]["name"]
        lunch = self.data["restaurants"][1]["name"]
        afternoon_place = self.data["places"][1]["name"]
        dinner = self.data["restaurants"][2]["name"]
        itinerary = f"""
Hanoi itinerary
Morning
- **Cafe/breakfast:** {breakfast}
- **Sightseeing:** {morning_place}
Lunch
- **Restaurant:** {lunch}
Afternoon
- **Sightseeing:** {afternoon_place}
Dinner
- **Dinner restaurant:** {dinner}
"""

        result = validate_itinerary_text(itinerary, self.data, preference)

        self.assertTrue(result.is_valid, result.model_dump())
        self.assertNotIn("low_dataset_coverage", {issue.code for issue in result.issues})

    def test_validator_allows_no_nightlife_safety_note(self):
        from services.itinerary_validator import validate_itinerary_text

        preference = complete_preference(arrival_day_of_week="Thursday", arrival_date_str="2026-06-04")
        breakfast = self.data["restaurants"][0]["name"]
        morning_place = self.data["places"][0]["name"]
        lunch = self.data["restaurants"][1]["name"]
        afternoon_place = self.data["places"][1]["name"]
        dinner = self.data["restaurants"][2]["name"]
        itinerary = f"""
Hanoi itinerary
Morning
- Cafe/breakfast: {breakfast}
- Sightseeing: {morning_place}
Lunch
- Restaurant: {lunch}
Afternoon
- Sightseeing: {afternoon_place}
Dinner
- Dinner restaurant: {dinner}

Note: No night/ĐÊM block because nightlife was not requested. Do not add bar/pub stops.
"""

        result = validate_itinerary_text(itinerary, self.data, preference)

        self.assertTrue(result.is_valid, result.model_dump())
        self.assertNotIn("invalid_evening_block", {issue.code for issue in result.issues})

    def test_validator_allows_warning_about_avoided_closed_place(self):
        from services.itinerary_validator import validate_itinerary_text

        preference = complete_preference(
            arrival_day_of_week="Monday",
            arrival_date_str="2026-06-08",
            budget=Budget.high,
        )
        closed_place = next(place for place in self.data["places"] if "Monday" in place.get("closed_on", []))
        open_places = [place for place in self.data["places"] if "Monday" not in place.get("closed_on", [])]
        breakfast = self.data["restaurants"][0]["name"]
        lunch = self.data["restaurants"][1]["name"]
        dinner = self.data["restaurants"][2]["name"]
        itinerary = f"""
Hanoi itinerary
Morning
- Cafe/breakfast: {breakfast}
- Sightseeing: {open_places[0]["name"]}
Lunch
- Restaurant: {lunch}
Afternoon
- Sightseeing: {open_places[1]["name"]}
Dinner
- Dinner restaurant: {dinner}

Warning: I avoided {closed_place["name"]} because it is closed on Monday.
"""

        result = validate_itinerary_text(itinerary, self.data, preference)

        self.assertTrue(result.is_valid, result.model_dump())
        self.assertNotIn("closed_place", {issue.code for issue in result.issues})

    def test_validator_still_rejects_closed_place(self):
        from services.itinerary_validator import validate_itinerary_text

        preference = complete_preference(arrival_day_of_week="Thursday", arrival_date_str="2026-06-04")
        itinerary = """
Morning
- Phố đi bộ Hồ Hoàn Kiếm
Lunch
- Bún Chả Đắc Kim
Afternoon
- Hồ Hoàn Kiếm & Đền Ngọc Sơn
Dinner
- Bà Nga - Bún Mọc Cổ Truyền
"""

        result = validate_itinerary_text(itinerary, self.data, preference)

        self.assertFalse(result.is_valid)
        self.assertIn("closed_place", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
