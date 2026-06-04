from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FoodStyle(str, Enum):
    street_food = "street_food"
    restaurant = "restaurant"
    hidden_gem = "hidden_gem"
    mixed = "mixed"


class PlaceType(str, Enum):
    culture_history = "culture_history"
    shopping_entertainment = "shopping_entertainment"
    chill_cafe = "chill_cafe"
    mixed = "mixed"


class ExperienceStyle(str, Enum):
    local = "local"
    tourist = "tourist"
    family = "family"


class Budget(str, Enum):
    low = "low"        # < 500k
    medium = "medium"  # 500k–1tr
    high = "high"      # > 1tr


class OnboardingStep(int, Enum):
    food_style = 1
    place_type = 2
    experience = 3
    budget = 4
    arrival_date = 5
    done = 6


class UserPreference(BaseModel):
    food_style: Optional[FoodStyle] = None
    place_type: Optional[PlaceType] = None
    experience: Optional[ExperienceStyle] = None
    nightlife: bool = False
    budget: Optional[Budget] = None
    arrival_date_str: Optional[str] = None
    arrival_day_of_week: Optional[str] = None  # "Monday"..."Sunday"
    num_days: int = 1
    onboarding_step: OnboardingStep = OnboardingStep.food_style

    def is_complete(self) -> bool:
        return (
            self.food_style is not None
            and self.place_type is not None
            and self.experience is not None
            and self.budget is not None
            and self.arrival_day_of_week is not None
        )


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'model'")
    content: str


class SessionState(BaseModel):
    preference: UserPreference = Field(default_factory=UserPreference)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    itinerary_generated: bool = False
