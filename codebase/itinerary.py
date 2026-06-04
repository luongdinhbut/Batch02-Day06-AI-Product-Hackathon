import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_BLOCKS = ["Morning", "Lunch", "Afternoon", "Dinner", "Evening"]
GENERIC_WORDS = {"anything", "balanced", "mixed", "toi an duoc het", "cai gi cung thich"}
GEMINI_MODEL = "gemini-3.1-flash-lite"
CUSTOM_MODEL = "gpt-4o-mini"
DISTRICT_ALIASES = {
    "hoan kiem": ["Hoàn Kiếm", "HoÃ n Kiáº¿m"],
    "hoàn kiếm": ["Hoàn Kiếm", "HoÃ n Kiáº¿m"],
    "tay ho": ["Tây Hồ", "TÃ¢y Há»“"],
    "tây hồ": ["Tây Hồ", "TÃ¢y Há»“"],
    "ba dinh": ["Ba Đình", "Ba ÄÃ¬nh"],
    "ba đình": ["Ba Đình", "Ba ÄÃ¬nh"],
    "dong da": ["Đống Đa", "Äá»‘ng Äa"],
    "đống đa": ["Đống Đa", "Äá»‘ng Äa"],
    "cau giay": ["Cầu Giấy", "Cáº§u Giáº¥y"],
    "cầu giấy": ["Cầu Giấy", "Cáº§u Giáº¥y"],
}


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "places": data.get("places", []),
        "restaurants": data.get("restaurants", []),
        "bars": data.get("bars", []),
    }


def build_preferences(answers):
    travel_date = answers["travel_date"]
    if isinstance(travel_date, date):
        travel_date = travel_date.isoformat()
    return {
        "food_style": answers["food_style"],
        "sightseeing": answers["sightseeing"],
        "local_style": answers["local_style"],
        "budget": answers["budget"],
        "travel_date": travel_date,
        "nightlife": bool(answers.get("nightlife")),
    }


def day_name(date_text):
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
        score += 2 if any(w in text for w in ["lịch", "history", "văn", "bảo tàng"]) else 0
    if "cafe" in prefs["sightseeing"].lower() or "chill" in prefs["sightseeing"].lower():
        score += 2 if any(w in text for w in ["cafe", "chill", "thiên nhiên", "hồ"]) else 0
    if "local" in prefs["local_style"].lower():
        score += 1 if any(w in text for w in ["local", "authentic", "phố cổ"]) else 0
    return score


def score_food(item, prefs, district=None):
    text = " ".join(str(item.get(k, "")) for k in ["category", "popular_dish", "name", "district"]).lower()
    score = float(item.get("rating", 0))
    if district and item.get("district") == district:
        score += 3
    if "street" in prefs["food_style"].lower():
        score += 2 if any(w in text for w in ["bún", "phở", "street", "chè", "bánh"]) else 0
    if "hidden" in prefs["food_style"].lower() or "local" in prefs["food_style"].lower():
        score += 1.5 if any(w in text for w in ["local", "quán", "bún", "phở"]) else 0
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
    return sorted(candidates, key=lambda x: x.get("rating", 0), reverse=True)[:limit]


def pick_restaurant(restaurants, prefs, district, used):
    choices = [r for r in restaurants if r.get("id") not in used]
    picked = sorted(choices, key=lambda r: score_food(r, prefs, district), reverse=True)[0]
    used.add(picked.get("id"))
    return picked


def build_fallback_itinerary(data, prefs):
    day = day_name(prefs["travel_date"])
    places = sorted(data["places"], key=lambda p: score_place(p, prefs), reverse=True)
    warnings = []
    selected_places = []

    # Guardrail: make Monday/closed-place risk visible even when fallback avoids it.
    for place in places:
        if len(warnings) >= 3:
            break
        if is_closed(place, day):
            alts = alternatives(data["places"], place, day)
            names = ", ".join(a["name"] for a in alts) or "choose another open place nearby"
            warnings.append(f"{place['name']} is closed on {day}. Suggested alternatives: {names}.")

    for place in places:
        if len(selected_places) >= 4:
            break
        if is_closed(place, day):
            continue
        selected_places.append(place)

    selected_places = selected_places[:4]
    district = selected_places[0].get("district") if selected_places else None
    used_food = set()
    lunch = pick_restaurant(data["restaurants"], prefs, district, used_food)
    dinner = pick_restaurant(data["restaurants"], prefs, district, used_food)
    bar = None
    if prefs.get("nightlife") and data["bars"]:
        bars = sorted(data["bars"], key=lambda b: score_food(b, prefs, district), reverse=True)
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


def block(name, time, items):
    return {"name": name, "time": time, "items": items}


def estimate_budget(blocks):
    mins, maxs = 0, 0
    for b in blocks:
        for item in b["items"]:
            mins += int(item.get("price_min") or 0)
            maxs += int(item.get("price_max") or item.get("price_min") or 0)
    return f"{mins:,}-{maxs:,} VND".replace(",", ".")


def detect_uncertain_preferences(prefs):
    values = [str(v).strip().lower() for k, v in prefs.items() if k != "travel_date"]
    generic_count = sum(1 for v in values if v in GENERIC_WORDS or "anything" in v or "balanced" in v)
    return generic_count >= 2


def render_itinerary(itinerary):
    lines = [f"## {itinerary['title']}", f"**Estimated budget:** {itinerary['estimate']}"]
    for b in itinerary["blocks"]:
        lines.append(f"\n### {b['name']} ({b['time']})")
        for item in b["items"]:
            reason = item.get("description") or item.get("popular_dish") or item.get("local_tip") or ""
            price = item.get("price_note") or f"{item.get('price_min', 0):,}-{item.get('price_max', 0):,} VND".replace(",", ".")
            lines.append(
                f"- **{item.get('name')}** - {item.get('district', 'Hanoi')} - rating {item.get('rating', 'n/a')} - {price}\n"
                f"  {reason[:180]}"
            )
    return "\n".join(lines)


def compact_context(data):
    sample = {
        "places": data["places"][:18],
        "restaurants": data["restaurants"][:18],
        "bars": data["bars"][:12],
    }
    return json.dumps(sample, ensure_ascii=False)


def google_api_key_from_env():
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")


def build_llm_prompt(data, prefs, itinerary):
    return f"""
You are a Hanoi itinerary assistant. Use only the supplied local data. Do not invent opening hours.
Preferences: {json.dumps(prefs, ensure_ascii=False)}
Local data sample: {compact_context(data)}
Guardrail itinerary already checked for closed places: {json.dumps(itinerary, ensure_ascii=False)}
Return a concise Vietnamese 1-day itinerary with morning, lunch, afternoon, dinner, evening, reasons, warnings, and budget.
"""


def call_google_llm(prompt):
    api_key = google_api_key_from_env()
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY or GOOGLE_API_KEY.")
    model = os.getenv("GEMINI_MODEL") or os.getenv("LLM_MODEL") or GEMINI_MODEL
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as res:
        payload = json.loads(res.read().decode("utf-8"))
    return payload["candidates"][0]["content"]["parts"][0]["text"], f"AI enrichment generated with google/{model}."


def call_custom_llm(prompt):
    api_key = os.getenv("CUSTOM_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("CUSTOM_API_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    if not api_key or not base_url:
        raise ValueError("Missing CUSTOM_API_KEY and CUSTOM_API_BASE_URL.")
    model = os.getenv("CUSTOM_MODEL") or os.getenv("LLM_MODEL") or CUSTOM_MODEL
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"
    body = json.dumps({
        "model": model,
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0")),
        "messages": [
            {"role": "system", "content": "You are a Hanoi itinerary assistant."},
            {"role": "user", "content": prompt},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        payload = json.loads(res.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"], f"AI enrichment generated with custom/{model}."


def call_gemini(data, prefs, itinerary):
    prompt = build_llm_prompt(data, prefs, itinerary)
    providers = [p.strip().lower() for p in os.getenv("LLM_PROVIDER", "google,custom").split(",") if p.strip()]
    errors = []
    for provider in providers:
        try:
            if provider == "google":
                return call_google_llm(prompt)
            if provider == "custom":
                return call_custom_llm(prompt)
            errors.append(f"{provider}: unsupported provider")
        except (urllib.error.URLError, ValueError, KeyError, IndexError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{provider}: {exc}")
    return "", "LLM unavailable, showing local fallback. " + " | ".join(errors)


def requested_district(text):
    for key, values in DISTRICT_ALIASES.items():
        if key in text:
            return values
    return []


def apply_correction(data, prefs, itinerary, text):
    text_l = text.lower()
    updated = json.loads(json.dumps(itinerary, ensure_ascii=False))
    blocks = updated["blocks"]

    districts = requested_district(text_l)
    if districts:
        district_places = [
            p for p in data["places"]
            if p.get("district") in districts and not is_closed(p, day_name(prefs["travel_date"]))
        ]
        if district_places:
            updated["blocks"][0]["items"] = district_places[:2]
            updated["blocks"][2]["items"] = district_places[2:4]

    if "remove bar" in text_l or "bỏ bar" in text_l:
        updated["blocks"] = [b for b in blocks if b["name"] != "Evening"]
        updated["estimate"] = estimate_budget(updated["blocks"])
        updated["ai_text"] = ""
        return updated

    if "cafe" in text_l or "cà phê" in text_l:
        cafes = [r for r in data["restaurants"] if "cafe" in str(r.get("category", "")).lower() or "cà" in str(r.get("name", "")).lower()]
        if cafes:
            blocks.insert(3, block("Cafe break", "16:30-17:30", [cafes[0]]))

    if "hoan kiem" in text_l or "hoàn kiếm" in text_l:
        prefs = dict(prefs)
        target = "Hoàn Kiếm"
        places = [p for p in data["places"] if p.get("district") == target and not is_closed(p, day_name(prefs["travel_date"]))]
        if places:
            updated["blocks"][0]["items"] = places[:2]
            updated["blocks"][2]["items"] = places[2:4]

    if "cheaper" in text_l or "rẻ" in text_l:
        prefs = dict(prefs)
        prefs["budget"] = "Under 500k"
        return build_fallback_itinerary(data, prefs)

    updated["estimate"] = estimate_budget(updated["blocks"])
    updated["ai_text"] = ""
    return updated
