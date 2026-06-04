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


if __name__ == "__main__":
    unittest.main()
