from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from agents.base import AgentResult, BaseAgent


LOCATION_MAP = {
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "country": "India"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "country": "India"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "country": "India"},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "country": "India"},
    "bhubaneswar": {"lat": 20.2961, "lon": 85.8245, "country": "India"},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "country": "India"},
}


@dataclass
class WeatherSnapshot:
    temperature_c: Optional[float]
    wind_speed_kmh: Optional[float]
    precipitation_mm: Optional[float]
    weather_code: Optional[int]
    source: str


class DataScoutAgent(BaseAgent):
    name = "Data Scout"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        crisis_text = context["crisis_text"]
        location_key = self._infer_location(crisis_text)
        location = LOCATION_MAP.get(location_key)

        weather = self._get_weather(location) if location else None
        extracted = self._extract_inputs(crisis_text)
        headlines = self._build_headlines(crisis_text, location_key)

        confidence = 0.84 if weather else 0.68
        summary = (
            f"Identified primary area as {location_key.title() if location_key else 'unspecified location'} "
            f"and collected situational signals from weather and crisis text."
        )

        return AgentResult(
            agent_name=self.name,
            summary=summary,
            details={
                "location": location_key.title() if location_key else "Unspecified",
                "coordinates": location,
                "weather": weather.__dict__ if weather else None,
                "headlines": headlines,
                "extracted_inputs": extracted,
            },
            confidence=confidence,
        )

    def _infer_location(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for key in LOCATION_MAP:
            if key in text_lower:
                return key
        return None

    def _extract_inputs(self, text: str) -> Dict[str, Any]:
        lowered = text.lower()
        severity = 0.55
        if any(term in lowered for term in ["cyclone", "storm surge", "landfall"]):
            severity += 0.2
        if any(term in lowered for term in ["severe", "catastrophic", "extreme"]):
            severity += 0.15
        if "flood" in lowered:
            severity += 0.1

        population = 1000
        tokens = lowered.replace(",", " ").split()
        for idx, token in enumerate(tokens):
            if token.isdigit():
                if idx + 1 < len(tokens) and tokens[idx + 1].startswith("people"):
                    population = int(token)
                    break
                if idx + 1 < len(tokens) and tokens[idx + 1].startswith("famil"):
                    population = int(token) * 4
                    break

        resources = {
            "boats": 8 if "boat" in lowered else 4,
            "medical_teams": 5 if "hospital" in lowered or "injur" in lowered else 3,
            "shelter_capacity": int(population * 0.55),
        }
        return {
            "estimated_population": population,
            "severity": min(severity, 0.98),
            "resources": resources,
        }

    def _get_weather(self, location: Dict[str, Any]) -> Optional[WeatherSnapshot]:
        try:
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location["lat"],
                    "longitude": location["lon"],
                    "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
                    "forecast_days": 1,
                },
                timeout=8,
            )
            response.raise_for_status()
            current = response.json().get("current", {})
            return WeatherSnapshot(
                temperature_c=current.get("temperature_2m"),
                wind_speed_kmh=current.get("wind_speed_10m"),
                precipitation_mm=current.get("precipitation"),
                weather_code=current.get("weather_code"),
                source="Open-Meteo",
            )
        except Exception:
            return None

    def _build_headlines(self, crisis_text: str, location_key: Optional[str]) -> List[str]:
        location_label = location_key.title() if location_key else "the affected area"
        return [
            f"Field update: access routes around {location_label} may degrade over the next 6 hours.",
            "Emergency resources should prioritize evacuation, shelter staging, and medical triage.",
            f"Crisis brief generated from user scenario: {crisis_text[:110].strip()}",
        ]
