from __future__ import annotations

from datetime import datetime


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def day_name(date_text):
    if str(date_text) in DAY_NAMES:
        return str(date_text)
    try:
        return DAY_NAMES[datetime.fromisoformat(str(date_text)).weekday()]
    except ValueError:
        return ""


def is_closed(item, day):
    return day in item.get("closed_on", [])


def budget_limit(prefs):
    budget = prefs.get("budget", "").lower()
    if "under" in budget or "500" in budget and "1tr" not in budget:
        return 100000
    if "500k-1tr" in budget:
        return 250000
    return 600000


def score_place(place, prefs):
    text = " ".join(
        str(place.get(k, "")) for k in ["category", "vibe", "district", "area", "description"]
    ).lower()
    score = float(place.get("rating", 0))
    if "culture" in prefs["sightseeing"].lower() or "history" in prefs["sightseeing"].lower():
        score += 2 if any(w in text for w in ["lich", "history", "van", "bao tang", "lịch", "văn", "bảo tàng"]) else 0
    if "cafe" in prefs["sightseeing"].lower() or "chill" in prefs["sightseeing"].lower():
        score += 2 if any(w in text for w in ["cafe", "chill", "thien nhien", "ho", "thiên nhiên", "hồ"]) else 0
    if "local" in prefs["local_style"].lower():
        score += 1 if any(w in text for w in ["local", "authentic", "pho co", "phố cổ"]) else 0
    return score


def score_food(item, prefs, district=None):
    text = " ".join(str(item.get(k, "")) for k in ["category", "popular_dish", "name", "district"]).lower()
    score = float(item.get("rating", 0))
    if district and item.get("district") == district:
        score += 3
    if "street" in prefs["food_style"].lower():
        score += 2 if any(w in text for w in ["bun", "pho", "street", "che", "banh", "bún", "phở", "chè", "bánh"]) else 0
    if "hidden" in prefs["food_style"].lower() or "local" in prefs["food_style"].lower():
        score += 1.5 if any(w in text for w in ["local", "quan", "bun", "pho", "quán", "bún", "phở"]) else 0
    if item.get("price_max", 999999) <= budget_limit(prefs):
        score += 2
    return score


def open_items(items, day):
    return [item for item in items if not is_closed(item, day)]


def alternatives(items, closed_item, day, limit=2):
    candidates = [
        item for item in open_items(items, day)
        if item.get("id") != closed_item.get("id")
        and (item.get("district") == closed_item.get("district") or item.get("category") == closed_item.get("category"))
    ]
    return sorted(candidates, key=lambda item: item.get("rating", 0), reverse=True)[:limit]


def pick_restaurant(restaurants, prefs, district, used):
    choices = [restaurant for restaurant in restaurants if restaurant.get("id") not in used]
    picked = sorted(choices, key=lambda restaurant: score_food(restaurant, prefs, district), reverse=True)[0]
    used.add(picked.get("id"))
    return picked


def block(name, time, items):
    return {"name": name, "time": time, "items": items}


def estimate_budget(blocks):
    mins, maxs = 0, 0
    for itinerary_block in blocks:
        for item in itinerary_block["items"]:
            mins += int(item.get("price_min") or 0)
            maxs += int(item.get("price_max") or item.get("price_min") or 0)
    return f"{mins:,}-{maxs:,} VND".replace(",", ".")


def build_fallback_itinerary(data, prefs):
    day = day_name(prefs["travel_date"])
    places = sorted(data["places"], key=lambda place: score_place(place, prefs), reverse=True)
    warnings = []
    selected_places = []

    # Guardrail: expose closure risk while selecting only open places.
    for place in places:
        if len(warnings) >= 3:
            break
        if is_closed(place, day):
            alts = alternatives(data["places"], place, day)
            names = ", ".join(alt["name"] for alt in alts) or "choose another open place nearby"
            warnings.append(f"{place['name']} is closed on {day}. Suggested alternatives: {names}.")

    for place in places:
        if len(selected_places) >= 4:
            break
        if not is_closed(place, day):
            selected_places.append(place)

    district = selected_places[0].get("district") if selected_places else None
    used_food = set()
    lunch = pick_restaurant(data["restaurants"], prefs, district, used_food)
    dinner = pick_restaurant(data["restaurants"], prefs, district, used_food)
    bar = None
    if prefs.get("nightlife") and data.get("bars"):
        bars = sorted(data["bars"], key=lambda item: score_food(item, prefs, district), reverse=True)
        bar = bars[0]

    blocks = [
        block("Morning", "08:00-11:30", selected_places[:2]),
        block("Lunch", "11:30-13:00", [lunch]),
        block("Afternoon", "13:30-17:00", selected_places[2:]),
        block("Dinner", "18:00-20:00", [dinner]),
    ]
    if bar:
        blocks.append(block("Evening", "20:30-23:00", [bar]))

    return {
        "title": f"Hanoi itinerary - {day or prefs['travel_date']}",
        "preferences": prefs,
        "warnings": warnings,
        "blocks": blocks,
        "estimate": estimate_budget(blocks),
    }
