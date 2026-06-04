import os
import unittest
from pathlib import Path

from itinerary import (
    apply_correction,
    build_fallback_itinerary,
    build_llm_prompt,
    build_preferences,
    call_gemini,
    day_name,
    is_closed,
    load_data,
)


ROOT = Path(__file__).resolve().parents[1]


class ItineraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data(ROOT / "data" / "hanoi_places.json")
        cls.prefs = build_preferences({
            "food_style": "Street food",
            "sightseeing": "Culture/history",
            "local_style": "Local",
            "budget": "Under 500k",
            "travel_date": "2026-06-08",
            "nightlife": True,
        })

    def test_day_name(self):
        self.assertEqual(day_name("2026-06-08"), "Monday")

    def test_closed_place_detection(self):
        van_mieu = self.data["places"][0]
        self.assertTrue(is_closed(van_mieu, "Monday"))

    def test_itinerary_warns_and_avoids_monday_closed_places(self):
        itinerary = build_fallback_itinerary(self.data, self.prefs)
        names = [item["name"] for block in itinerary["blocks"] for item in block["items"]]
        self.assertTrue(itinerary["warnings"])
        self.assertNotIn(self.data["places"][0]["name"], names)

    def test_remove_bar_correction(self):
        itinerary = build_fallback_itinerary(self.data, self.prefs)
        updated = apply_correction(self.data, self.prefs, itinerary, "remove bar")
        self.assertNotIn("Evening", [b["name"] for b in updated["blocks"]])

    def test_add_cafe_correction(self):
        itinerary = build_fallback_itinerary(self.data, self.prefs)
        updated = apply_correction(self.data, self.prefs, itinerary, "add a cafe")
        self.assertIn("Cafe break", [b["name"] for b in updated["blocks"]])

    def test_change_district_correction(self):
        itinerary = build_fallback_itinerary(self.data, self.prefs)
        updated = apply_correction(self.data, self.prefs, itinerary, "change to Tay Ho")
        districts = [item.get("district") for b in updated["blocks"][:3] for item in b["items"]]
        self.assertTrue(any(d in {"Tây Hồ", "TÃ¢y Há»“"} for d in districts))

    def test_make_cheaper_correction(self):
        expensive = dict(self.prefs)
        expensive["budget"] = "Over 1tr"
        itinerary = build_fallback_itinerary(self.data, expensive)
        updated = apply_correction(self.data, expensive, itinerary, "make it cheaper")
        self.assertEqual(updated["preferences"]["budget"], "Under 500k")

    def test_llm_prompt_uses_local_guardrail_itinerary(self):
        itinerary = build_fallback_itinerary(self.data, self.prefs)
        prompt = build_llm_prompt(self.data, self.prefs, itinerary)
        self.assertIn("Guardrail itinerary", prompt)
        self.assertIn("Street food", prompt)

    def test_llm_missing_keys_returns_local_fallback_note(self):
        old_env = {k: os.environ.get(k) for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "CUSTOM_API_KEY", "CUSTOM_API_BASE_URL", "LLM_PROVIDER"]}
        try:
            for key in old_env:
                os.environ.pop(key, None)
            os.environ["LLM_PROVIDER"] = "google,custom"
            itinerary = build_fallback_itinerary(self.data, self.prefs)
            text, note = call_gemini(self.data, self.prefs, itinerary)
            self.assertEqual(text, "")
            self.assertIn("LLM unavailable", note)
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
