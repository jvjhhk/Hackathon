"""AgriShield AI demo API. Live weather and PostgreSQL are enabled by environment variables."""
from __future__ import annotations

import os
import random
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

app = FastAPI(title="AgriShield AI", version="1.0.0", description="Farm dashboard, climate, irrigation, and assistant API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DEMO = {
    "location": "Wayanad, Kerala",
    "crop": "Cardamom",
    "temperature_c": 28,
    "humidity_pct": 76,
    "rainfall_mm": 2.4,
    "soil_moisture_pct": 38,
    "field_size_acres": 2.4,
    "source": "simulated",
}
soil_moisture = DEMO["soil_moisture_pct"]
_profile_engine = None


def profile_engine():
    """Create the PostgreSQL profile table on demand; return None in local demo mode."""
    global _profile_engine
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    if _profile_engine is None:
        try:
            _profile_engine = create_engine(url, pool_pre_ping=True)
            with _profile_engine.begin() as conn:
                conn.execute(text("""CREATE TABLE IF NOT EXISTS farmer_profile (
                    id INTEGER PRIMARY KEY, name VARCHAR(160) NOT NULL, farm_name VARCHAR(160) NOT NULL,
                    location VARCHAR(240) NOT NULL, crop VARCHAR(100) NOT NULL,
                    field_size_acres FLOAT NOT NULL DEFAULT 2.4, language VARCHAR(30) NOT NULL DEFAULT 'English'
                )"""))
        except Exception as exc:
            _profile_engine = None
            raise HTTPException(status_code=503, detail=f"PostgreSQL profile storage is unavailable: {exc}") from exc
    return _profile_engine


class MoistureUpdate(BaseModel):
    moisture_pct: int = Field(ge=0, le=100)
    source: Literal["simulated", "sensor"] = "simulated"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Literal["English", "Malayalam"] = "English"
    moisture_pct: int = Field(default=soil_moisture, ge=0, le=100)


class CropRequest(BaseModel):
    soil_type: Literal["Loamy", "Sandy", "Clay"] = "Loamy"
    location: str = "Wayanad, Kerala"


def moisture_state(value: int) -> str:
    if value < 30:
        return "dry"
    if value > 68:
        return "wet"
    return "optimal"


@app.get("/api/health")
def health():
    return {"status": "ok", "weather": "live" if os.getenv("OPENWEATHER_API_KEY") else "simulated", "database": "configured" if os.getenv("DATABASE_URL") else "demo mode"}


@app.get("/api/dashboard")
async def dashboard(location: str | None = None):
    result = {**DEMO, "location": location or DEMO["location"], "soil_moisture_pct": soil_moisture}
    key = os.getenv("OPENWEATHER_API_KEY")
    if key:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get("https://api.openweathermap.org/data/2.5/weather", params={"q": result["location"], "appid": key, "units": "metric"})
                response.raise_for_status()
                weather = response.json()
            result.update({"temperature_c": round(weather["main"]["temp"]), "humidity_pct": weather["main"]["humidity"], "rainfall_mm": weather.get("rain", {}).get("1h", 0), "source": "weather_api"})
        except (httpx.HTTPError, KeyError, ValueError):
            result["weather_error"] = "Live weather is temporarily unavailable; showing clearly labelled demo values."
    return {**result, "moisture_state": moisture_state(soil_moisture), "updated_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/climate")
async def climate(location: str = DEMO["location"]):
    key = os.getenv("OPENWEATHER_API_KEY")
    if key:
        try:
            async with httpx.AsyncClient(timeout=7) as client:
                response = await client.get("https://api.openweathermap.org/data/2.5/forecast", params={"q": location, "appid": key, "units": "metric"})
                response.raise_for_status()
                entries = response.json()["list"]
            by_day = {}
            for entry in entries:
                day = datetime.fromtimestamp(entry["dt"], timezone.utc).strftime("%a")
                row = by_day.setdefault(day, {"day": day, "high_c": -50, "low_c": 60, "rain_chance_pct": 0, "rain_mm": 0})
                row["high_c"] = max(row["high_c"], round(entry["main"]["temp_max"]))
                row["low_c"] = min(row["low_c"], round(entry["main"]["temp_min"]))
                row["rain_chance_pct"] = max(row["rain_chance_pct"], round(entry.get("pop", 0) * 100))
                row["rain_mm"] += entry.get("rain", {}).get("3h", 0)
            days = list(by_day.values())[:6]
            rain_total = sum(day["rain_mm"] for day in days)
            max_temp = max((day["high_c"] for day in days), default=30)
            rain_level = "high" if rain_total >= 50 else "moderate" if rain_total >= 15 or any(day["rain_chance_pct"] >= 60 for day in days) else "low"
            heat_level = "high" if max_temp >= 38 else "moderate" if max_temp >= 34 else "low"
            dry_level = "moderate" if rain_total < 2 and len(days) >= 4 else "low"
            risks = [
                {"type": "heavy_rainfall", "level": rain_level, "chance_pct": max((d["rain_chance_pct"] for d in days), default=0), "message": f"Forecast rainfall totals about {rain_total:.1f} mm. Clear field drains if heavy showers are expected."},
                {"type": "heat_stress", "level": heat_level, "temperature_c": max_temp, "message": f"Forecast highs reach {max_temp}°C. Provide shade and check soil moisture during warm afternoons."},
                {"type": "dry_spell", "level": dry_level, "duration_days": len(days), "message": "Little rainfall is forecast. Check soil moisture regularly and irrigate only when needed." if dry_level != "low" else "Rainfall is expected during the forecast period."},
            ]
            ranks = {"low": 0, "moderate": 1, "high": 2}
            overall = max((risk["level"] for risk in risks), key=lambda level: ranks[level])
            return {"source": "weather_api", "risk_level": overall, "risks": risks, "forecast": days}
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            pass
    return {"source": "simulated", "risk_level": "low", "risks": [
        {"type": "heavy_rainfall", "level": "moderate", "chance_pct": 60, "message": "Showers likely over the weekend. Clear field drains to prevent waterlogging."},
        {"type": "heat_stress", "level": "low", "temperature_c": 31, "message": "Temperatures stay comfortable for cardamom."},
        {"type": "dry_spell", "level": "low", "duration_days": 2, "message": "No extended dry period expected."},
    ], "forecast": [{"day": "Today", "high_c": 31, "low_c": 24, "rain_chance_pct": 10}, {"day": "Friday", "high_c": 30, "low_c": 24, "rain_chance_pct": 20}, {"day": "Saturday", "high_c": 28, "low_c": 23, "rain_chance_pct": 60}, {"day": "Sunday", "high_c": 27, "low_c": 22, "rain_chance_pct": 80}, {"day": "Monday", "high_c": 29, "low_c": 23, "rain_chance_pct": 30}, {"day": "Tuesday", "high_c": 31, "low_c": 24, "rain_chance_pct": 10}]}


@app.get("/api/irrigation")
def get_irrigation():
    state = moisture_state(soil_moisture)
    return {"moisture_pct": soil_moisture, "state": state, "irrigation_needed": state == "dry", "source": "simulated", "last_synced": datetime.now(timezone.utc).isoformat(), "recommendation": "Water gently in the early morning." if state == "dry" else "Hold irrigation and check again tomorrow."}


@app.post("/api/irrigation")
def update_irrigation(update: MoistureUpdate):
    global soil_moisture
    soil_moisture = update.moisture_pct
    return {"moisture_pct": soil_moisture, "state": moisture_state(soil_moisture), "irrigation_needed": moisture_state(soil_moisture) == "dry", "source": update.source, "last_synced": datetime.now(timezone.utc).isoformat()}


@app.post("/api/crops/recommend")
def crop_recommend(request: CropRequest):
    options = {
        "Loamy": [("Cardamom", "Suits Wayanad’s cool, shaded slopes", "Mulch with leaf litter; compost before monsoon", 92), ("Black pepper", "Climbs well in humid conditions", "Apply neem cake at the base", 84)],
        "Sandy": [("Groundnut", "Thrives in well-drained soil", "Apply gypsum at flowering", 90), ("Millet", "Tolerates dry conditions", "Split nitrogen after sowing", 85)],
        "Clay": [("Rice", "Retains water for paddy", "Apply compost before transplanting", 92), ("Banana", "Benefits from nutrient-rich soil", "Use potassium-rich organic manure", 82)],
    }
    return {"source": "rule_based_demo", "location": request.location, "recommendations": [dict(name=n, reason=r, care_tip=c, match_pct=m) for n, r, c, m in options[request.soil_type]]}


@app.post("/api/assistant")
def assistant(request: ChatRequest):
    q = request.message.lower()
    value = request.moisture_pct
    if request.language == "Malayalam":
        answer = f"നിങ്ങളുടെ കൃഷിയിടത്തിലെ വിവരങ്ങൾ പരിശോധിച്ച് തീരുമാനിക്കാം. മണ്ണിലെ ഈർപ്പം ഇപ്പോൾ {value}% ആണ്. മഴ പ്രതീക്ഷിക്കുന്നതിനാൽ വെള്ളം നൽകുന്നതിന് മുമ്പ് മണ്ണ് പരിശോധിക്കുക. കൂടുതൽ സഹായത്തിന് അടുത്തുള്ള കൃഷിഭവനുമായി ബന്ധപ്പെടുക."
    elif any(word in q for word in ("rain", "weather")):
        answer = "Light showers are expected this weekend in Wayanad. Clear field drains, hold off on irrigation, and avoid applying fertilizer just before the rain."
    elif any(word in q for word in ("cardamom", "crop")):
        answer = f"Cardamom does best with dappled shade, moist but well-drained soil, and leaf mulch. Your current soil moisture is {value}%, which is {moisture_state(value)}."
    elif any(word in q for word in ("moisture", "water", "irrigat")):
        advice = "That is getting dry. A slow watering early in the morning would help." if value < 30 else "That is quite wet. Hold off on watering and check drainage." if value > 68 else "That is in a good range for cardamom, so you can hold off on watering today."
        answer = f"Your soil moisture is {value}%. {advice} Check again tomorrow morning."
    else:
        answer = f"For your farm in Wayanad, keep checking the soil before watering and maintain a light mulch around your plants. Your current moisture is {value}%. Share the crop or concern for more specific guidance."
    return {"answer": answer, "source": "rule_based_demo", "language": request.language}


@app.get("/api/market")
def market(crop: Literal["Cardamom", "Pepper", "Coffee"] = "Cardamom"):
    prices = {"Cardamom": [("Vandanmedu Auction", 2240, 5.2), ("Puttady Spices Market", 2180, 4.1), ("Kumily Regulated Market", 2132, 3.4)], "Pepper": [("Vandanmedu Auction", 710, 2.9), ("Puttady Spices Market", 680, 1.8), ("Kumily Regulated Market", 662, 1.4)], "Coffee": [("Mananthavady Market", 256, 2.2), ("Kalpetta Market", 248, 1.6), ("Sultan Bathery Market", 239, 1.0)]}
    rows = prices[crop]
    return {"crop": crop, "unit": "INR/kg", "source": "simulated", "markets": [{"name": name, "price": price, "weekly_change_pct": change} for name, price, change in rows]}


@app.get("/api/profile")
def get_profile():
    """Read a stored farmer profile when PostgreSQL is configured, otherwise return demo data."""
    engine = profile_engine()
    if engine is None:
        return {"name": "Anjali K.", "farm_name": "Anjali’s farm", "location": DEMO["location"], "crop": DEMO["crop"], "field_size_acres": DEMO["field_size_acres"], "language": "English", "storage": "demo"}
    try:
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO farmer_profile (id, name, farm_name, location, crop, field_size_acres, language)
                VALUES (1, 'Anjali K.', 'Anjali’s farm', :location, :crop, 2.4, 'English') ON CONFLICT (id) DO NOTHING"""), {"location": DEMO["location"], "crop": DEMO["crop"]})
            row = conn.execute(text("SELECT name, farm_name, location, crop, field_size_acres, language FROM farmer_profile WHERE id=1")).mappings().one()
        return {**dict(row), "storage": "postgresql"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"PostgreSQL profile storage is unavailable: {exc}") from exc


@app.put("/api/profile")
def save_profile(profile: dict):
    required = {"location", "crop", "language"}
    if not required.issubset(profile):
        raise HTTPException(status_code=422, detail="Profile requires location, crop, and language.")
    engine = profile_engine()
    if engine is None:
        return {"saved": True, "storage": "demo", "profile": profile, "message": "Profile is held in demo mode. Configure DATABASE_URL to persist it."}
    try:
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO farmer_profile (id, name, farm_name, location, crop, field_size_acres, language)
                VALUES (1, :name, :farm_name, :location, :crop, :field_size_acres, :language)
                ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, farm_name=EXCLUDED.farm_name,
                location=EXCLUDED.location, crop=EXCLUDED.crop, field_size_acres=EXCLUDED.field_size_acres, language=EXCLUDED.language"""), {
                "name": profile.get("name", "Anjali K."), "farm_name": profile.get("farm_name", "Anjali’s farm"),
                "location": profile["location"], "crop": profile["crop"],
                "field_size_acres": profile.get("field_size_acres", 2.4), "language": profile["language"],
            })
        return {"saved": True, "storage": "postgresql", "profile": profile}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not save profile to PostgreSQL: {exc}") from exc
