from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional

import requests

from agents.base import AgentResult, BaseAgent


LOCATION_MAP = {
    "mumbai": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "India"},
    "kolkata": {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "country": "India"},
    "chennai": {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "country": "India"},
    "visakhapatnam": {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185, "country": "India"},
    "bhubaneswar": {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245, "country": "India"},
    "delhi": {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "country": "India"},
}

REGION_PREFIXES = {
    "coastal",
    "greater",
    "upper",
    "lower",
}

LOCATION_STOPWORDS = {
    "heavy",
    "severe",
    "critical",
    "cyclone",
    "flash",
    "flood",
    "flooding",
    "heatwave",
    "earthquake",
    "wildfire",
    "storm",
    "threat",
    "incoming",
    "emergency",
    "hazard",
}

HAZARD_KEYWORDS = {
    "flood": ["flood", "flash flood", "flooding", "inundation"],
    "cyclone": ["cyclone", "storm surge", "landfall", "typhoon", "hurricane"],
    "heatwave": ["heatwave", "extreme heat", "heat stroke", "high temperature"],
    "earthquake": ["earthquake", "aftershock", "seismic"],
    "landslide": ["landslide", "slope failure", "mudslide"],
    "wildfire": ["wildfire", "forest fire", "smoke", "fire line"],
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
        extracted = self._extract_inputs(crisis_text)
        location = self._resolve_location(crisis_text)
        weather = self._get_weather_for_location(location) if location else None
        headlines = self._build_headlines(crisis_text, extracted, location, weather)

        summary = (
            f"Resolved the crisis area to {location['name'] if location else 'an unspecified region'}, "
            f"identified {extracted['hazard_type']} as the primary hazard, and extracted operational constraints "
            f"from the scenario description."
        )

        return AgentResult(
            agent_name=self.name,
            summary=summary,
            details={
                "location": location["name"] if location else "Unspecified",
                "coordinates": location,
                "weather": weather.__dict__ if weather else None,
                "headlines": headlines,
                "extracted_inputs": extracted,
            },
            confidence=0.9 if location and weather else 0.82 if location else 0.72,
        )

    def _extract_inputs(self, text: str) -> Dict[str, Any]:
        lowered = text.lower()
        hazard_type = self._infer_hazard_type(lowered)
        severity = self._infer_severity(lowered, hazard_type)
        population = self._extract_population(text)
        urgency_hours = self._extract_urgency_hours(lowered)
        resources = self._extract_resources(lowered, population)
        constraints = self._extract_constraints(text, lowered)

        return {
            "hazard_type": hazard_type,
            "estimated_population": population,
            "severity": severity,
            "urgency_hours": urgency_hours,
            "resources": resources,
            "constraints": constraints,
        }

    def _infer_hazard_type(self, lowered: str) -> str:
        for hazard_type, keywords in HAZARD_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return hazard_type
        return "multi-hazard emergency"

    def _infer_severity(self, lowered: str, hazard_type: str) -> float:
        severity = 0.45
        severity += 0.18 if any(term in lowered for term in ["severe", "critical", "catastrophic", "extreme"]) else 0
        severity += 0.14 if any(term in lowered for term in ["limited", "constrained", "shortage", "overwhelmed"]) else 0
        severity += 0.12 if any(term in lowered for term in ["incoming", "within", "imminent", "landfall"]) else 0

        hazard_bonus = {
            "flood": 0.12,
            "cyclone": 0.16,
            "heatwave": 0.1,
            "earthquake": 0.18,
            "landslide": 0.13,
            "wildfire": 0.14,
        }
        severity += hazard_bonus.get(hazard_type, 0.08)

        if any(term in lowered for term in ["power outage", "submerged roads", "hospital access", "communications down"]):
            severity += 0.08
        return min(severity, 0.98)

    def _extract_population(self, text: str) -> int:
        normalized = text.lower().replace(",", "")
        patterns = [
            (r"(\d+(?:\.\d+)?)\s*(k|thousand)\s+(?:people|residents|citizens|families)", self._scale_population),
            (r"(\d+(?:\.\d+)?)\s*(lakh|lakhs)\s+(?:people|residents|citizens|families)", self._scale_population),
            (r"(\d+(?:\.\d+)?)\s*(million)\s+(?:people|residents|citizens|families)", self._scale_population),
            (r"(\d+)\s+(?:people|residents|citizens)", lambda m: int(m.group(1))),
            (r"(\d+)\s+famil(?:y|ies)", lambda m: int(m.group(1)) * 4),
        ]
        for pattern, parser in patterns:
            match = re.search(pattern, normalized)
            if match:
                return parser(match)
        return 1000

    def _scale_population(self, match: re.Match[str]) -> int:
        value = float(match.group(1))
        unit = match.group(2)
        multiplier = {
            "k": 1000,
            "thousand": 1000,
            "lakh": 100000,
            "lakhs": 100000,
            "million": 1000000,
        }[unit]
        return int(value * multiplier)

    def _extract_urgency_hours(self, lowered: str) -> Optional[int]:
        patterns = [
            r"within\s+(\d+)\s+hours?",
            r"in\s+(\d+)\s+hours?",
            r"next\s+(\d+)\s+hours?",
        ]
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                return int(match.group(1))
        if any(term in lowered for term in ["immediate", "imminent", "right now"]):
            return 2
        return None

    def _extract_resources(self, lowered: str, population: int) -> Dict[str, int]:
        boats = self._extract_resource_count(lowered, ["boat", "boats"], default=8 if "boat" in lowered else 4)
        medical_teams = self._extract_resource_count(
            lowered,
            ["medical team", "medical teams", "ambulance", "ambulances"],
            default=5 if "hospital" in lowered or "injur" in lowered else 3,
        )
        shelter_capacity = self._extract_resource_count(
            lowered,
            ["shelter", "shelters", "beds"],
            default=int(population * 0.55),
        )
        return {
            "boats": boats,
            "medical_teams": medical_teams,
            "shelter_capacity": shelter_capacity,
        }

    def _extract_resource_count(self, lowered: str, nouns: List[str], default: int) -> int:
        for noun in nouns:
            pattern_before = rf"(\d+)\s+{re.escape(noun)}"
            pattern_after = rf"{re.escape(noun)}\s+(?:available|ready|deployed|remaining)?\s*(\d+)"
            for pattern in [pattern_before, pattern_after]:
                match = re.search(pattern, lowered)
                if match:
                    return int(match.group(1))
        if any(f"limited {noun}" in lowered for noun in nouns):
            return max(1, int(default * 0.6))
        return default

    def _extract_constraints(self, text: str, lowered: str) -> List[str]:
        constraints: List[str] = []
        phrase_rules = [
            ("submerged roads", "Road access is degraded by flooding."),
            ("limited rescue boats", "Rescue fleet capacity is constrained."),
            ("limited boats", "Boat-based evacuation capacity is constrained."),
            ("hospital access", "Hospital access is constrained."),
            ("power outage", "Power outages are affecting critical services."),
            ("incoming cyclone", "A secondary weather threat is approaching."),
            ("shelters are partially full", "Existing shelters are already under pressure."),
        ]
        for needle, description in phrase_rules:
            if needle in lowered:
                constraints.append(description)

        for sentence in re.split(r"[.!?]\s*", text):
            stripped = sentence.strip()
            if stripped and any(word in stripped.lower() for word in ["limited", "blocked", "overwhelmed", "constrained"]):
                constraints.append(stripped)

        deduped: List[str] = []
        for item in constraints:
            if item not in deduped:
                deduped.append(item)
        return deduped[:6]

    def _resolve_location(self, text: str) -> Optional[Dict[str, Any]]:
        direct = self._match_known_location(text)
        if direct:
            return direct

        fallback_candidate: Optional[str] = None
        for candidate in self._location_candidates(text):
            fallback_candidate = fallback_candidate or candidate
            for query in self._location_query_variants(candidate):
                geocoded = self._geocode_location(query)
                if geocoded:
                    return geocoded
        if fallback_candidate:
            return {
                "name": fallback_candidate,
                "lat": None,
                "lon": None,
                "country": None,
                "source": "Scenario Text Fallback",
            }
        return None

    def _match_known_location(self, text: str) -> Optional[Dict[str, Any]]:
        text_lower = text.lower()
        for key, location in LOCATION_MAP.items():
            if key in text_lower:
                return dict(location)
        return None

    def _location_candidates(self, text: str) -> List[str]:
        candidates: List[str] = []
        original = re.sub(r"\s+", " ", text).strip()
        patterns = [
            r"(?:in|near|around|across|at|for)\s+([A-Za-z0-9][A-Za-z0-9\s-]{2,50})",
            r"(?:affecting|impacting)\s+[A-Za-z0-9,\s]+\s+in\s+([A-Za-z0-9][A-Za-z0-9\s-]{2,50})",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, original, re.IGNORECASE):
                cleaned = self._clean_location_phrase(match.group(1))
                if cleaned:
                    candidates.append(cleaned)

        title_case_chunks = re.findall(r"\b(?:[A-Z][A-Za-z0-9]+(?:\s+[A-Z0-9][A-Za-z0-9]+){0,3})\b", original)
        for chunk in title_case_chunks:
            cleaned = self._clean_location_phrase(chunk)
            if cleaned:
                candidates.append(cleaned)

        deduped: List[str] = []
        for item in candidates:
            if item not in deduped:
                deduped.append(item)
        return deduped[:8]

    def _clean_location_phrase(self, phrase: str) -> Optional[str]:
        cleaned = phrase.strip(" ,.-")
        cleaned = re.split(
            r"\b(?:affecting|with|where|and|limited|incoming|within|using|because|causing)\b",
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" ,.-")
        words = cleaned.split()
        while words and words[0].lower() in REGION_PREFIXES:
            words = words[1:]
        while words and words[0].lower() in LOCATION_STOPWORDS:
            words = words[1:]
        if words and words[-1].lower() in {"region", "district", "area", "zone", "state"}:
            words = words[:-1]
        if not words:
            return None
        if len(words) == 1 and words[0].lower() in LOCATION_STOPWORDS:
            return None
        return " ".join(words[:4])

    def _location_query_variants(self, candidate: str) -> List[str]:
        variants = [candidate]
        words = candidate.split()
        if len(words) > 1:
            variants.append(" ".join(words[-2:]))
            variants.append(words[-1])
        deduped: List[str] = []
        for item in variants:
            cleaned = item.strip()
            if cleaned and cleaned.lower() not in LOCATION_STOPWORDS and cleaned not in deduped:
                deduped.append(cleaned)
        return deduped

    @lru_cache(maxsize=32)
    def _geocode_location(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": query,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
                timeout=8,
            )
            response.raise_for_status()
            results = response.json().get("results") or []
            if not results:
                return None
            best = results[0]
            return {
                "name": best.get("name", query),
                "lat": best.get("latitude"),
                "lon": best.get("longitude"),
                "country": best.get("country"),
                "admin1": best.get("admin1"),
                "admin2": best.get("admin2"),
                "source": "Open-Meteo Geocoding",
            }
        except Exception:
            return None

    def _get_weather_for_location(self, location: Dict[str, Any]) -> Optional[WeatherSnapshot]:
        lat = location.get("lat")
        lon = location.get("lon")
        if lat is None or lon is None:
            return None
        return self._get_weather(lat, lon)

    @lru_cache(maxsize=32)
    def _get_weather(self, lat: float, lon: float) -> Optional[WeatherSnapshot]:
        try:
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
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

    def _build_headlines(
        self,
        crisis_text: str,
        extracted: Dict[str, Any],
        location: Optional[Dict[str, Any]],
        weather: Optional[WeatherSnapshot],
    ) -> List[str]:
        location_label = location["name"] if location else "the affected area"
        weather_line = (
            f"Live weather near {location_label}: {weather.wind_speed_kmh} km/h wind and {weather.precipitation_mm} mm precipitation."
            if weather
            else f"Live weather unavailable for {location_label}; recommendations rely on scenario text and inferred risk."
        )
        urgency_line = (
            f"Escalation window appears to be within {extracted['urgency_hours']} hours."
            if extracted["urgency_hours"]
            else "No explicit response window was identified in the description."
        )
        constraint_line = (
            extracted["constraints"][0]
            if extracted["constraints"]
            else "No explicit infrastructure constraint was extracted from the scenario."
        )
        return [
            f"Primary hazard identified as {extracted['hazard_type']} in {location_label}.",
            weather_line,
            urgency_line,
            constraint_line,
            f"Scenario basis: {crisis_text[:140].strip()}",
        ]
